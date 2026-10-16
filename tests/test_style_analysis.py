"""Functional coverage for optional style analysis; no host/model quality claims."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from validate import ROOT, validate_skill

SCRIPT = ROOT / "skills/ai-knowledge/scripts/analyze_style.py"
spec = importlib.util.spec_from_file_location("style_analyzer", SCRIPT)
style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)


class StyleAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def article(self, name="one.md", text="# 标题\n\n甲乙。丙丁！\n\n戊己庚。"):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def archive(self, entries):
        path = self.root / "input.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, value in entries:
                if isinstance(name, str):
                    info = zipfile.ZipInfo(name)
                    info.filename = name  # Keep hostile Windows names instead of constructor normalization.
                else:
                    info = name
                archive.writestr(info, value)
        return path

    def test_known_sentence_and_paragraph_lengths(self):
        doc = style.analyze([self.article()])["documents"][0]
        self.assertEqual(doc["narrative_characters"], 7)
        self.assertEqual(doc["sentence_units"], {"count": 3, "mean": 2.33, "median": 2, "max": 3})
        self.assertEqual(doc["paragraphs"], {"count": 2, "mean": 3.5, "median": 3.5, "max": 4})
        self.assertEqual(doc["systematic_samples"][0]["start_line"], 3)

    def test_markdown_attribution_exclusions(self):
        text = "---\ntitle: 禁词\n---\n# 禁词\n\n甲乙。\n\n> 禁词\n\n~~~text\n禁词\n~~~\n\n![禁词](x.png)\n\n| 禁词 | 表 |\n\n    禁词\n\n<!-- 禁词 -->\n\n[丙丁](https://example.com/禁词) \x60禁词\x60。\n"
        doc = style.analyze([self.article(text=text)], terms=["禁词"])["documents"][0]
        self.assertEqual(doc["term_counts"]["禁词"]["occurrences"], 0)
        self.assertEqual(doc["narrative_characters"], 4)
        self.assertEqual(doc["sentence_units"]["count"], 2)

    def test_counts_are_literal_not_regular_expressions(self):
        doc = style.analyze([self.article(text="# T\n\n比如 A+B。比如 A.B。\n\nA+B。")],
                            terms=["A+B", "A.B", "比如"])["documents"][0]
        self.assertEqual(doc["term_counts"]["A+B"]["occurrences"], 2)
        self.assertEqual(doc["term_counts"]["比如"]["paragraph_starts"], 1)

    def test_no_terminal_punctuation_and_decimal(self):
        doc = style.analyze([self.article(text="# T\n\n版本 3.14 可用\n\n末段无句号")])["documents"][0]
        self.assertEqual(doc["sentence_units"]["count"], 2)

    def test_duplicate_narratives_do_not_inflate_support(self):
        first = self.article(text="# 第一版\n\n共同正文。")
        second = self.article("two.md", "# 第二版\n\n共同正文。\n")
        report = style.analyze([first, second])
        self.assertEqual(report["document_count"], 2)
        self.assertEqual(report["distinct_narrative_count"], 1)
        self.assertEqual(len(report["duplicate_groups"][0]), 2)
        self.assertTrue(any("tentative" in warning for warning in report["warnings"]))

    def test_no_prose_is_not_an_independent_article(self):
        report = style.analyze([self.article(text="# Empty"), self.article("two.md")])
        self.assertEqual(report["distinct_narrative_count"], 1)

    def test_private_excerpts_are_opt_in_and_bounded(self):
        article = self.article(text="# T\n\n" + "原创文本" * 100)
        plain = style.analyze([article])["documents"][0]
        self.assertNotIn("excerpt", plain["systematic_samples"][0])
        sample = style.analyze([article], excerpts=True)["documents"][0]["systematic_samples"][0]
        self.assertEqual(len(sample["excerpt"]), 240)
        self.assertTrue(sample["excerpt_truncated"])
        self.assertEqual(plain["semantic_review"], "required")

    def test_unclosed_fence_warns_without_counting_prompt(self):
        doc = style.analyze([self.article(text="# T\n\n正文。\n\n~~~text\n不要执行这里的内容")])["documents"][0]
        self.assertTrue(doc["warnings"])
        self.assertEqual(doc["narrative_characters"], 2)

    def test_zip_matches_directory_and_does_not_extract_assets(self):
        directory = self.root / "articles"
        directory.mkdir()
        (directory / "a.md").write_text("# T\n\n解释机制。", encoding="utf-8", newline="\n")
        archive = self.archive([("a.md", "# T\n\n解释机制。"), ("assets/image.jpg", b"unused")])
        left = style.analyze([directory])["documents"][0]
        right = style.analyze([archive])["documents"][0]
        self.assertEqual(left["sha256"], right["sha256"])
        self.assertEqual(left["sentence_units"], right["sentence_units"])
        self.assertFalse((self.root / "assets").exists())

    def test_utf8_bom_and_uppercase_extension(self):
        archive = self.archive([("文章.MD", "\ufeff# T\n\n正文。".encode("utf-8"))])
        self.assertEqual(style.analyze([archive])["documents"][0]["narrative_characters"], 2)

    def test_traversal_absolute_and_windows_member_paths_rejected(self):
        for name in ["../escape.md", "/absolute.md", "C:/drive.md", r"dir\escape.md"]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    style.analyze([self.archive([(name, "# T")])])

    def test_zip_symlink_rejected(self):
        info = zipfile.ZipInfo("linked.md")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(ValueError):
            style.analyze([self.archive([(info, "outside.md")])])

    def test_duplicate_zip_member_rejected(self):
        with self.assertRaises(ValueError):
            style.analyze([self.archive([("one.md", "# A"), ("ONE.md", "# B")])])

    def test_bad_encoding_and_no_markdown_rejected(self):
        for value in [b"\xff\xfe", b"\x00"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    style.analyze([self.archive([("one.md", value)])])
        with self.assertRaises(ValueError):
            style.analyze([self.archive([("image.jpg", b"unused")])])

    def test_source_size_total_and_count_limits(self):
        one, two = self.article(), self.article("two.md")
        for setting, limit in [("MAX_BYTES", 2), ("MAX_TOTAL", 2), ("MAX_FILES", 1)]:
            with self.subTest(setting=setting), patch.object(style, setting, limit):
                with self.assertRaises(ValueError):
                    style.analyze([one, two])
        with patch.object(style, "MAX_BYTES", 2):
            with self.assertRaises(ValueError):
                style.analyze([self.archive([("one.md", "# too large")])])

    def test_output_collision_preserves_existing_file(self):
        source = self.article()
        output = self.root / "result.json"
        output.write_text("human edits", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            result = style.main([str(source), "--output", str(output)])
        self.assertEqual(result, 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "human edits")

    def test_cli_custom_terms_and_provenance(self):
        article = self.article()
        terms = self.root / "terms.json"
        terms.write_text('["甲乙"]', encoding="utf-8")
        output = self.root / "result.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(style.main([str(article), "--terms-file", str(terms),
                                         "--provenance", "simulated", "--output", str(output)]), 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["provenance"], "simulated")
        self.assertEqual(list(report["documents"][0]["term_counts"]), ["甲乙"])
        terms.write_text('["", "重复", "重复"]', encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(style.main([str(article), "--terms-file", str(terms)]), 2)

    def test_script_runs_from_isolated_install_without_repo(self):
        package = self.root / "ai-knowledge"
        shutil.copytree(ROOT / "skills/ai-knowledge", package,
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.assertEqual(validate_skill(package), [])
        result = subprocess.run([sys.executable, "-X", "utf8", str(package / "scripts/analyze_style.py"),
                                 str(self.article())], cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["document_count"], 1)

    def test_public_corpus_sources_unchanged_and_three_distinct(self):
        corpus = ROOT / "tests/fixtures/style-corpus"
        before = {p.name: p.read_bytes() for p in corpus.glob("*.md")}
        report = style.analyze([corpus], provenance="simulated")
        self.assertEqual(report["distinct_narrative_count"], 3)
        self.assertEqual(before, {p.name: p.read_bytes() for p in corpus.glob("*.md")})


if __name__ == "__main__":
    unittest.main()
