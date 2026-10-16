"""Negative checks prove the validator rejects broken article.md + review.md bundles."""
from pathlib import Path
import shutil
import tempfile
import unittest

from bundle_fixtures import write_bundle
from validate import (ROOT, frontmatter, local_link_errors, markdown_errors, private_config_findings,
                      sensitive_findings, validate_bundle, validate_skill)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bundle = write_bundle(self.root / "topic")

    def tearDown(self):
        self.tmp.cleanup()

    def mutate(self, old, new, filename="article.md"):
        path = self.bundle / filename
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def assertFinding(self, message, **kwargs):
        errors = validate_bundle(self.bundle, **kwargs)
        self.assertIn(message, errors)
        return errors

    def test_valid_bundle(self):
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_valid_bundle_without_images(self):
        bundle = write_bundle(self.root / "plain", images=False)
        self.assertEqual(validate_bundle(bundle), [])

    def test_platform_adaptation_is_ignored(self):
        (self.bundle / "xiaohongshu.md").write_text("没有标题的短文案\n", encoding="utf-8")
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_missing_review(self):
        (self.bundle / "review.md").unlink()
        self.assertEqual(validate_bundle(self.bundle), ["missing output: review.md"])

    def test_missing_article(self):
        (self.bundle / "article.md").unlink()
        self.assertIn("missing output: article.md", validate_bundle(self.bundle))

    def test_duplicate_yaml_key(self):
        with self.assertRaises(ValueError):
            frontmatter('---\ntitle: one\ntitle: two\n---\n')

    def test_bad_yaml(self):
        self.mutate('tags: ["登录", "会话"]', 'tags: [')
        errors = validate_bundle(self.bundle)
        self.assertTrue(any(e.startswith("article.md: invalid YAML (") for e in errors), errors)

    def test_old_aliases_key_rejected(self):
        self.mutate('language: "zh-CN"', 'language: "zh-CN"\naliases: []')
        self.assertFinding("article.md: unexpected frontmatter key: aliases")

    def test_missing_summary_key(self):
        self.mutate('summary: "用两次跳转讲清登录态从哪里来"\n', '')
        errors = self.assertFinding("article.md: missing frontmatter key: summary")
        self.assertIn("article.md: summary must be a non-empty string of at most 60 characters", errors)

    def test_h1_in_article(self):
        self.mutate("## 两个应用各有会话", "# 两个应用各有会话")
        self.assertFinding("article.md: H1 outside code fences not allowed in article body")

    def test_article_needs_h2(self):
        path = self.bundle / "article.md"
        path.write_text(path.read_text(encoding="utf-8").replace("## ", "### "), encoding="utf-8")
        self.assertFinding("article.md: article body needs at least one H2")

    def test_mermaid_fence_in_article(self):
        self.mutate("```text\n", "```mermaid\n")
        self.assertFinding("article.md: Mermaid fence in article body; export the diagram as an image")

    def test_html_comment_in_article(self):
        self.mutate("开头先讲读者遇到的问题。", "开头先讲读者遇到的问题。<!-- 备注 -->")
        self.assertFinding("article.md: HTML comment in article body")

    def test_placeholder_in_article(self):
        for placeholder in ("[TODO: 补开头]", "{" + "{opening}" + "}"):
            with self.subTest(placeholder=placeholder):
                self.mutate("开头先讲读者遇到的问题。", placeholder)
                self.assertFinding("article.md: unresolved template placeholder")
                self.mutate(placeholder, "开头先讲读者遇到的问题。")

    def test_status_wording_in_article(self):
        message = "article.md: production/status wording in article body"
        for word in ("未核验", "已核验", "发布前核验", "核验日期", "草稿", "Draft", "待审批", "未批准", "工作区"):
            with self.subTest(word=word):
                self.mutate("开头先讲读者遇到的问题。", f"开头先讲读者遇到的问题。{word}")
                self.assertFinding(message)
                self.mutate(f"开头先讲读者遇到的问题。{word}", "开头先讲读者遇到的问题。")
        self.mutate("示例规范：", "草案规范 draft-ietf-oauth-example：")
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_status_wording_inside_code_fence_allowed(self):
        self.mutate("# 代码块里的井号不是标题", "status: draft")
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_summary_length(self):
        self.mutate('"用两次跳转讲清登录态从哪里来"', '"' + "长" * 60 + '"')
        self.assertEqual(validate_bundle(self.bundle), [])
        self.mutate('"' + "长" * 60 + '"', '"' + "长" * 61 + '"')
        self.assertFinding("article.md: summary must be a non-empty string of at most 60 characters")

    def test_empty_summary(self):
        self.mutate('"用两次跳转讲清登录态从哪里来"', '"  "')
        self.assertFinding("article.md: summary must be a non-empty string of at most 60 characters")

    def test_tag_count_bounds(self):
        message = "article.md: tags must be a list of 2-5 non-empty strings"
        current = '["登录", "会话"]'
        for tags, valid in (('["登录"]', False), ('["a", "b", "c", "d", "e"]', True),
                            ('["a", "b", "c", "d", "e", "f"]', False), ('["登录", ""]', False),
                            ('"登录"', False)):
            with self.subTest(tags=tags):
                self.mutate("tags: " + current, "tags: " + tags)
                current = tags
                if valid:
                    self.assertEqual(validate_bundle(self.bundle), [])
                else:
                    self.assertFinding(message)

    def test_type_mismatch(self):
        self.mutate('type: "article"', 'type: "review"')
        self.assertFinding('article.md: type must be "article"')
        self.mutate('type: "review"', 'type: "review-card"', "review.md")
        self.assertFinding('review.md: type must be "review"')

    def test_review_status(self):
        self.mutate('status: "draft"', 'status: "ready"', "review.md")
        self.assertEqual(validate_bundle(self.bundle), [])
        self.mutate('status: "ready"', 'status: "published"', "review.md")
        self.assertFinding("review.md: status must be draft or ready")

    def test_review_missing_section(self):
        self.mutate("## 公开安全过滤", "## 安全", "review.md")
        self.assertFinding("review.md: missing section: ## 公开安全过滤")

    def test_review_sections_out_of_order(self):
        path = self.bundle / "review.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("## 配图", "## TMP").replace("## 可补充的个人经历", "## 配图")
        path.write_text(text.replace("## TMP", "## 可补充的个人经历"), encoding="utf-8")
        self.assertFinding("review.md: review sections out of order; expected "
                           "发布状态 > 事实核验 > 公开安全过滤 > 可补充的个人经历 > 配图 > 标题与摘要备选")

    def test_extra_review_section_between_required_ones(self):
        self.mutate("## 配图", "## 平台注意事项\n\n发布前核对平台字数。\n\n## 配图", "review.md")
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_review_needs_one_h1(self):
        self.mutate("# 会话为什么能跨应用｜发布前核验\n", "", "review.md")
        self.assertFinding("review.md: expected exactly one H1 outside code fences")

    def test_bad_evidence_type_and_check(self):
        self.mutate("| 协议原理 |", "| 历史事实 |", "review.md")
        self.mutate("| 已核验 |", "| 已确认 |", "review.md")
        errors = self.assertFinding("review.md: evidence row 1: invalid 类型")
        self.assertIn("review.md: evidence row 2: invalid 核验", errors)

    def test_suggestion_must_not_be_verified(self):
        self.mutate("| 建议 | 无 | 不适用 |", "| 建议 | 无 | 已核验 |", "review.md")
        self.assertFinding("review.md: evidence row 3: 建议 must use 核验 不适用")

    def test_duplicate_or_empty_evidence_id(self):
        self.mutate("| C2 |", "| C1 |", "review.md")
        self.assertFinding("review.md: evidence row 2: empty or duplicate ID")
        self.mutate("| C1 | 应用", "|  | 应用", "review.md")
        self.assertFinding("review.md: evidence row 1: empty or duplicate ID")

    def test_evidence_row_cell_count(self):
        self.mutate("| 示例教材 | 已核验 |", "| 已核验 |", "review.md")
        self.assertFinding("review.md: evidence row 2: expected 5 cells")

    def test_missing_or_empty_evidence_table(self):
        self.mutate("| ID | 结论 | 类型 | 依据 | 核验 |", "| ID | 结论 | 依据 | 核验 |", "review.md")
        self.assertFinding("review.md: missing evidence table | ID | 结论 | 类型 | 依据 | 核验 | in ## 事实核验")
        bundle = write_bundle(self.root / "empty")
        path = bundle / "review.md"
        text = path.read_text(encoding="utf-8")
        start = text.index("| C1 |")
        path.write_text(text[:start] + text[text.index("\n## 公开安全过滤"):], encoding="utf-8")
        self.assertIn("review.md: evidence table has no rows", validate_bundle(bundle))

    def test_evidence_table_must_be_in_its_section(self):
        path = self.bundle / "review.md"
        text = path.read_text(encoding="utf-8")
        start, end = text.index("| ID |"), text.index("\n## 公开安全过滤")
        table = text[start:end]
        text = text[:start] + text[end:]
        path.write_text(text.replace("## 配图\n", "## 配图\n\n" + table + "\n"), encoding="utf-8")
        self.assertFinding("review.md: missing evidence table | ID | 结论 | 类型 | 依据 | 核验 | in ## 事实核验")

    def test_review_title_must_match_article(self):
        self.mutate('title: "会话为什么能跨应用｜发布前核验"', 'title: "会话为什么能跨应用|发布前核验"', "review.md")
        self.assertFinding("review.md: title must be the article title followed by ｜发布前核验")
        self.mutate('title: "会话为什么能跨应用|发布前核验"', 'title: "会话为什么能跨应用｜发布前核验"', "review.md")
        self.mutate('title: "会话为什么能跨应用"', 'title: "另一个标题"')
        self.assertFinding("review.md: title must be the article title followed by ｜发布前核验")

    def test_metadata_mismatch(self):
        for key, old, new in (("mode", 'mode: "concept"', 'mode: "feature"'),
                              ("language", 'language: "zh-CN"', 'language: "en"'),
                              ("created", 'created: "2026-10-14"', 'created: "2026-10-13"'),
                              ("topic", 'topic: "topic"', 'topic: "another"')):
            with self.subTest(key=key):
                self.mutate(old, new, "review.md")
                self.assertFinding(f"bundle metadata mismatch: {key}")
                self.mutate(new, old, "review.md")

    def test_bad_date(self):
        self.mutate('updated: "2026-10-14"', 'updated: "2026-02-30"')
        self.assertFinding("article.md: invalid ISO date strings")

    def test_updated_precedes_created(self):
        self.mutate('updated: "2026-10-14"', 'updated: "2026-10-13"')
        self.assertFinding("article.md: updated precedes created")

    def test_old_generation_date(self):
        errors = self.assertFinding("article.md: updated differs from supplied generation date",
                                    expected_date="2026-10-15")
        self.assertIn("review.md: updated differs from supplied generation date", errors)
        self.assertEqual(validate_bundle(self.bundle, expected_date="2026-10-14"), [])

    def test_reserved_and_invalid_slug(self):
        for slug in ("con", "Topic", "a/b", "../x"):
            with self.subTest(slug=slug):
                self.mutate('topic: "topic"', f'topic: "{slug}"')
                self.assertFinding("article.md: invalid topic slug")
                self.mutate(f'topic: "{slug}"', 'topic: "topic"')

    def test_invalid_mode(self):
        self.mutate('mode: "concept"', 'mode: "tutorial"')
        self.assertFinding("article.md: invalid mode")

    def test_svg_embedded_in_article(self):
        self.mutate("./assets/flow.png", "./assets/cover.svg")
        self.assertFinding("article.md: article image must be ./assets/<name>.png|.jpg|.jpeg")

    def test_remote_or_parent_image_in_article(self):
        for target in ("https://example.com/a.png", "assets/flow.png", "./assets/../flow.png"):
            with self.subTest(target=target):
                self.mutate("./assets/flow.png", target)
                self.assertFinding("article.md: article image must be ./assets/<name>.png|.jpg|.jpeg")
                self.mutate(target, "./assets/flow.png")

    def test_image_needs_alt_and_standard_syntax(self):
        self.mutate("![关系图：浏览器、应用与认证中心]", "![]")
        self.assertFinding("article.md: image without alt text")
        self.mutate("![](./assets/flow.png)", '<img src="./assets/flow.png" alt="x">')
        self.assertFinding("article.md: unsupported image syntax; use ![alt](./assets/<name>.png)")

    def test_missing_image_file(self):
        (self.bundle / "assets/flow.png").unlink()
        self.assertFinding("article.md: missing local link: ./assets/flow.png")

    def test_secret_in_review_reported_without_value(self):
        fake = "gh" + "p_" + "A" * 36
        self.mutate("无真实系统信息", "无真实系统信息 " + fake, "review.md")
        errors = self.assertFinding("review.md: possible credential")
        self.assertNotIn(fake, str(errors))


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "topic").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_path_traversal_link(self):
        msg = local_link_errors(self.root / "topic/note.md", "[out](../../elsewhere.md)", self.root)
        self.assertIn("local link escapes allowed root", msg)

    def test_missing_local_reference(self):
        self.assertTrue(local_link_errors(self.root / "topic/note.md", "[lost](missing.py)", self.root))

    def test_link_inside_inline_code_is_not_checked(self):
        text = "写成 `![有意义的 alt](./assets/<文件名>.png)`。"
        self.assertEqual(local_link_errors(self.root / "topic/note.md", text, self.root), [])

    def test_source_line_out_of_range(self):
        (self.root / "source.txt").write_text("one\ntwo\n", encoding="utf-8")
        self.assertTrue(local_link_errors(self.root / "topic/note.md", "[source](../source.txt#L999)", self.root))

    def test_fence_and_placeholder(self):
        self.assertTrue(markdown_errors("# Title\n```python\npass\n"))
        self.assertTrue(markdown_errors("# Title\n" + "{{" + "title}}"))
        self.assertEqual(markdown_errors("# Title\n```text\n# not a heading\n```\n"), [])
        self.assertEqual(markdown_errors("no heading\n", single_h1=False), [])

    def test_secret_report_does_not_echo_value(self):
        fake = "gh" + "p_" + "A" * 36
        findings = sensitive_findings(fake)
        self.assertTrue(findings)
        self.assertNotIn(fake, str(findings))

    def test_private_url_detected(self):
        self.assertTrue(sensitive_findings("https://" + "service" + ".internal/"))

    def test_jwt_bearer_and_private_ipv4_detected_by_category(self):
        segment = "A" * 12
        jwt = "ey" + "J" + segment + ".ey" + "J" + segment + "." + segment
        bearer = "Authorization: Bear" + "er " + "x" * 24
        cases = {"possible JWT": jwt, "possible bearer token": bearer}
        for prefix in ("10.", "192.168.", "172.16.", "172.31."):
            address = prefix + ".".join(["1"] * (4 - prefix.count(".")))
            cases["private IPv4 address " + prefix] = "内网地址" + address + "。"
        for name, text in cases.items():
            with self.subTest(name=name):
                findings = sensitive_findings(text)
                self.assertEqual(len(findings), 1)
                self.assertTrue(name.startswith(findings[0]))
                self.assertNotIn(text.split()[-1].removeprefix("内网地址").rstrip("。"), str(findings))

    def test_public_addresses_and_versions_not_flagged(self):
        for text in ("8.8.8.8", "172.15.0.1", "172.32.0.1", "版本 10.2", "v1.10.0.1",
                     "Authorization: Bearer <token>", "eyJ only"):
            with self.subTest(text=text):
                self.assertEqual(sensitive_findings(text), [])


class SkillPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_contract_resources_reported(self):
        target = self.root / "ai-knowledge"
        shutil.copytree(ROOT / "skills/ai-knowledge", target, ignore=shutil.ignore_patterns("__pycache__"))
        for relative in ("references/publishing.md", "assets/templates/article.md",
                         "assets/templates/review.md", "scripts/visual_assets.py"):
            path = target / relative
            if path.exists():
                path.unlink()
        errors = validate_skill(target)
        for message in ("missing reference: publishing", "missing template: article",
                        "missing template: review", "missing script: scripts/visual_assets.py"):
            self.assertIn(message, errors)

    def test_real_package_passes_validate_skill(self):
        # Depends on the complete v0.4.0 package (references, templates) being present.
        target = self.root / "ai-knowledge"
        shutil.copytree(ROOT / "skills/ai-knowledge", target, ignore=shutil.ignore_patterns("__pycache__"))
        self.assertEqual(validate_skill(target), [])

    def test_bundled_personal_config_rejected(self):
        target = self.root / "ai-knowledge"
        shutil.copytree(ROOT / "skills/ai-knowledge", target, ignore=shutil.ignore_patterns("__pycache__"))
        (target / "styles/personal/someone").mkdir(parents=True)
        self.assertIn("bundled personal config: styles/personal must not exist in the package",
                      validate_skill(target))

    def test_private_marker_guard_covers_skills_and_examples_only(self):
        marker = "Any" + "ues"
        for relative in ("skills/a.md", "examples/x/manifest.json", "docs/history.md", "tests/RESULTS.md",
                         "skills/.tmp/scratch.md"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("mentions " + marker, encoding="utf-8")
        (self.root / "examples" / (marker.lower() + "-kit")).mkdir()
        (self.root / "skills/clean.md").write_text("clean", encoding="utf-8")
        self.assertEqual(private_config_findings(self.root), [
            "skills/a.md: private config marker in content",
            "examples/" + marker.lower() + "-kit: private config marker in path",
            "examples/x/manifest.json: private config marker in content",
        ])


if __name__ == "__main__":
    unittest.main()
