"""Functional tests for routing/diff/merge; semantic decisions require Agent review.

Personal config comes from a temporary copy of tests/fixtures/personal-demo; the real
home directory is replaced by an empty temporary one in every test.
"""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from validate import ROOT, validate_skill

PACKAGE = ROOT / "skills/ai-knowledge"
FIXTURE = ROOT / "tests/fixtures/personal-demo"
spec = importlib.util.spec_from_file_location("learning", PACKAGE / "scripts/style_learning.py")
learning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learning)
ENV = learning.ENV_VAR


def isolated_env(home, personal=None):
    """Subprocess environment whose home is a temporary directory."""
    env = {k: v for k, v in os.environ.items() if k != ENV}
    env.update(HOME=str(home), USERPROFILE=str(home))
    if personal is not None:
        env[ENV] = str(personal)
    return env


class StyleLearningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.package = self.root / "ai-knowledge"
        shutil.copytree(PACKAGE, self.package, ignore=shutil.ignore_patterns("__pycache__"))
        self.personal = self.root / "personal"
        shutil.copytree(FIXTURE, self.personal)
        self.home = self.root / "home"
        self.home.mkdir()
        environ = patch.dict(os.environ, {ENV: str(self.personal)})
        environ.start()
        self.addCleanup(environ.stop)
        home = patch.object(Path, "home", return_value=self.home)
        home.start()
        self.addCleanup(home.stop)

    def unset_env(self):
        os.environ.pop(ENV, None)

    def home_personal(self):
        target = self.home / ".ai-knowledge/personal"
        shutil.copytree(FIXTURE, target)
        return target

    def test_env_combines_public_and_confirmed_rules_only(self):
        result = learning.select_context(self.package)
        self.assertEqual((result["route"], result["source"]), ("personal", "env"))
        self.assertEqual(Path(result["source_path"]), self.personal.resolve())
        self.assertEqual([r["id"] for r in result["rules"]], ["SAMPLE-001"])
        self.assertTrue(Path(result["public"]).is_file())
        self.assertEqual(Path(result["profile"]), self.personal.resolve() / "writing-profile.md")

    def test_package_has_no_bundled_personal_config(self):
        self.assertFalse((PACKAGE / "styles").exists())
        self.assertEqual(validate_skill(self.package), [])

    def test_home_default_used_when_env_unset(self):
        self.unset_env()
        self.assertEqual(learning.select_context(self.package)["route"], "public-only")
        target = self.home_personal()
        result = learning.select_context(self.package)
        self.assertEqual((result["route"], result["source"]), ("personal", "home"))
        self.assertEqual(Path(result["source_path"]), target.resolve())

    def test_precedence_explicit_then_env_then_home(self):
        self.home_personal()
        rules = self.personal / "writing-rules.md"
        rules.write_text(rules.read_text("utf-8").replace("## SAMPLE-001", "## ENVONLY-001"), encoding="utf-8")
        result = learning.select_context(self.package)
        self.assertEqual((result["source"], [r["id"] for r in result["rules"]]), ("env", ["ENVONLY-001"]))
        profile = self.root / "selected.md"
        profile.write_text("# User style\n\nUse concise sentences.", encoding="utf-8")
        result = learning.select_context(self.package, profile=profile)
        self.assertEqual((result["route"], result["source"]), ("explicit", "explicit"))
        self.assertEqual(result["rules"], [])
        self.unset_env()
        self.assertEqual([r["id"] for r in learning.select_context(self.package)["rules"]], ["SAMPLE-001"])

    def test_missing_env_directory_falls_back_without_using_home(self):
        self.home_personal()
        os.environ[ENV] = str(self.root / "absent")
        result = learning.select_context(self.package)
        self.assertEqual((result["route"], result["source"]), ("public-only", "env"))
        self.assertIn("home not substituted", result["reason"])
        self.assertEqual(result["rules"], [])

    def test_relative_env_path_rejected(self):
        os.environ[ENV] = "relative/personal"
        result = learning.select_context(self.package)
        self.assertEqual((result["route"], result["source"], result["source_path"]), ("public-only", "env", None))

    def test_empty_env_value_means_unset(self):
        os.environ[ENV] = "  "
        self.assertEqual(learning.select_context(self.package)["source"], "home")

    def test_empty_personal_directory_falls_back(self):
        for path in self.personal.glob("*.md"):
            path.write_text("", encoding="utf-8")
        result = learning.select_context(self.package)
        self.assertEqual((result["route"], result["rules"]), ("public-only", []))

    def test_rules_without_profile_still_apply(self):
        (self.personal / "writing-profile.md").unlink()
        result = learning.select_context(self.package)
        self.assertEqual(result["route"], "personal")
        self.assertIsNone(result["profile"])

    def test_candidates_and_disabled_rules_do_not_apply(self):
        path = self.personal / "writing-rules.md"
        original = path.read_text(encoding="utf-8")
        for state in ("候选", "已停用"):
            path.write_text(original.replace("状态：已确认", "状态：" + state), encoding="utf-8")
            self.assertEqual(learning.select_context(self.package)["route"], "public-only")

    def test_unconfirmed_and_duplicate_ids_rejected(self):
        path = self.personal / "writing-rules.md"
        original = path.read_text(encoding="utf-8")
        path.write_text(original + "\n" + original, encoding="utf-8")
        self.assertEqual(learning.select_context(self.package)["rules"], [])
        incomplete = "## SAMPLE-001\n\n- 规则：改写\n- 状态：已确认\n"
        path.write_text(incomplete, encoding="utf-8")
        self.assertEqual(learning.select_context(self.package)["route"], "public-only")

    def test_generic_rule_id_prefixes_parsed(self):
        text = (self.personal / "writing-rules.md").read_text(encoding="utf-8")
        for prefix in ("DEMO", "ANY", "AB_C"):
            with self.subTest(prefix=prefix):
                ids = [r["id"] for r in learning.parse_rules(text.replace("SAMPLE-", prefix + "-"))]
                self.assertEqual(ids, [prefix + "-001", prefix + "-002", prefix + "-003"])
        self.assertEqual(learning.parse_rules(text.replace("## SAMPLE-", "## sample-")), [])

    def test_public_only_overrides_env_and_explicit_profile(self):
        result = learning.select_context(self.package, True, self.root / "missing.md")
        self.assertEqual((result["route"], result["source"]), ("public-only", None))
        self.assertIsNone(result["profile"])
        self.assertEqual(result["rules"], [])

    def test_explicit_profile_replaces_default(self):
        profile = self.root / "selected.md"
        profile.write_text("# User style\n\nUse concise sentences.", encoding="utf-8")
        result = learning.select_context(self.package, profile=profile)
        self.assertEqual(result["route"], "explicit")
        self.assertEqual(Path(result["profile"]), profile.resolve())
        self.assertEqual(result["rules"], [])

    def test_missing_explicit_profile_does_not_substitute_personal(self):
        result = learning.select_context(self.package, profile=self.root / "absent.md")
        self.assertEqual((result["route"], result["source"]), ("public-only", "explicit"))
        self.assertIn("do not substitute", result["reason"])
        self.assertEqual(result["rules"], [])

    def test_missing_public_resource_is_error(self):
        (self.package / "references/writing-craft.md").unlink()
        with self.assertRaises(OSError):
            learning.select_context(self.package)

    def test_actual_diff_has_exact_changed_text_and_lines(self):
        draft, final = self.root / "draft.md", self.root / "final.md"
        draft.write_text("# T\n\n效果很好。\n\n保留条件。\n", encoding="utf-8")
        final.write_text("# T\n\n页面显示新价格。\n\n保留条件。\n", encoding="utf-8")
        report = learning.compare_versions(final, draft)
        self.assertEqual(len(report["changes"]), 1)
        change = report["changes"][0]
        self.assertEqual(change["before"], ["效果很好。"])
        self.assertEqual(change["after"], ["页面显示新价格。"])
        self.assertEqual(change["before_lines"], [3, 3])
        self.assertNotEqual(report["draft_sha256"], report["final_sha256"])

    def test_missing_draft_has_no_invented_changes(self):
        final = ROOT / "tests/fixtures/style-reflection/sso-final.md"
        report = learning.compare_versions(final)
        self.assertEqual(report["mode"], "final-only")
        self.assertIsNone(report["draft_sha256"])
        self.assertEqual(report["changes"], [])
        self.assertEqual(report["purpose"], "not inferred")

    def test_unchanged_text_does_not_create_edits(self):
        path = ROOT / "tests/fixtures/style-reflection/sso-final.md"
        self.assertEqual(learning.compare_versions(path, path)["changes"], [])

    def evidence(self, article="demo-sso", version="one"):
        return {"article_id": article, "draft_sha256": "draft-" + version,
                "final_sha256": "final-" + version, "evidence": "原创模拟修改",
                "status": "已确认"}  # Observations cannot promote state.

    def test_single_and_multiple_articles_stay_candidates(self):
        first = learning.add_evidence({"id": "DEMO-001"}, self.evidence())
        second = learning.add_evidence(first, self.evidence("demo-cache", "two"))
        self.assertEqual(first["status"], "候选")
        self.assertEqual(second["status"], "候选")
        self.assertEqual(second["support_count"], 2)

    def test_repeat_and_renamed_copy_are_idempotent(self):
        first = learning.add_evidence({"id": "DEMO-001"}, self.evidence())
        self.assertEqual(learning.add_evidence(first, self.evidence()), first)
        self.assertEqual(learning.add_evidence(first, self.evidence("renamed")), first)

    def test_multiple_revisions_of_one_article_count_once(self):
        first = learning.add_evidence({"id": "DEMO-001"}, self.evidence())
        merged = learning.add_evidence(first, self.evidence(version="revision"))
        self.assertEqual(len(merged["evidence"]), 2)
        self.assertEqual(merged["support_count"], 1)

    def test_existing_disabled_rule_not_reactivated_and_input_immutable(self):
        rule = {"id": "DEMO-001", "status": "已停用"}
        result = learning.add_evidence(rule, self.evidence())
        self.assertEqual(result["status"], "已停用")
        self.assertNotIn("evidence", rule)

    def test_final_only_cannot_be_added_as_change_evidence(self):
        evidence = self.evidence()
        evidence["draft_sha256"] = None
        with self.assertRaises(ValueError):
            learning.add_evidence({"id": "DEMO-001"}, evidence)

    def snapshot(self, *folders):
        return {p: p.read_bytes() for folder in folders for p in folder.rglob("*") if p.is_file()}

    def run_context(self, cwd, env, *args):
        return subprocess.run([sys.executable, "-B", "-X", "utf8",
                               str(self.package / "scripts/style_learning.py"), "context", *args],
                              cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8")

    def test_cross_project_cli_reads_personal_root_without_mutation(self):
        other = self.root / "other-project"
        other.mkdir()
        before = self.snapshot(self.package, self.personal, self.home)
        result = self.run_context(other, isolated_env(self.home, self.personal))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual((data["route"], data["source"]), ("personal", "env"))
        result = self.run_context(other, isolated_env(self.home))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual((data["route"], data["source"]), ("public-only", "home"))
        self.assertEqual(self.snapshot(self.package, self.personal, self.home), before)
        self.assertEqual(list(other.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_cli_home_fallback_and_public_only(self):
        target = self.home_personal()
        result = self.run_context(self.root, isolated_env(self.home))
        data = json.loads(result.stdout)
        self.assertEqual((data["route"], data["source"]), ("personal", "home"))
        self.assertEqual(Path(data["source_path"]), target.resolve())
        data = json.loads(self.run_context(self.root, isolated_env(self.home, self.personal),
                                           "--public-only").stdout)
        self.assertEqual((data["route"], data["rules"]), ("public-only", []))

    def test_private_diffs_never_write_rules_or_learning_log(self):
        # A local synthetic private string must remain only in the in-memory report.
        draft, final = self.root / "private-draft.md", self.root / "private-final.md"
        draft.write_text("# T\n\n私有模拟客户甲的观察。\n", encoding="utf-8")
        final.write_text("# T\n\n私有模拟客户甲的具体观察。\n", encoding="utf-8")
        before = self.snapshot(self.package, self.personal)
        report = learning.compare_versions(final, draft)
        self.assertTrue(report["changes"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(learning.main(["compare", "--draft", str(draft), "--final", str(final)]), 0)
        self.assertEqual(before, self.snapshot(self.package, self.personal))

    def test_fixture_rules_include_scope_and_exceptions(self):
        records = learning.parse_rules((FIXTURE / "writing-rules.md").read_text(encoding="utf-8"))
        self.assertEqual({r["状态"] for r in records}, {"已确认", "候选", "已停用"})
        self.assertTrue(all(all(r[k] for k in learning.FIELDS) for r in records))


if __name__ == "__main__":
    unittest.main()
