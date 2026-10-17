"""Content workspace scripts and the four content types; temporary directories only."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bundle_fixtures import write_bundle
from validate import ROOT, validate_bundle

SCRIPTS = ROOT / "skills/ai-knowledge/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


create = load("create_project")
save = load("save_article")
CLEAN_ENV = {k: v for k, v in os.environ.items()
             if k != "AI_KNOWLEDGE_WORKSPACE"}


def quiet(func, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ws = self.root / "工作台"
        env = patch.dict(os.environ, CLEAN_ENV, clear=True)
        env.start()
        self.addCleanup(env.stop)
        home = patch.object(Path, "home", return_value=self.root / "home")
        home.start()
        self.addCleanup(home.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def init(self, *extra):
        return quiet(create.main, ["init", "--workspace", str(self.ws), *extra])

    def settings(self):
        path = self.root / "home/.ai-knowledge/settings.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    def test_init_copies_seed_content_and_project_layout(self):
        self.init()
        seed = SCRIPTS.parent / "templates/内容工作台"
        files = [p for p in seed.rglob("*") if p.is_file()]
        self.assertGreaterEqual(len(files), 10)
        for path in files:
            relative = path.relative_to(seed)
            self.assertEqual((self.ws / relative).read_bytes(), path.read_bytes(), relative)
        for relative in ("我的项目/_briefs", "我的项目/_knowledge_base", "我的项目/_协作文档",
                         "我的项目/公众号写作", "我的项目/推文写作", "我的项目/短视频逐字稿",
                         "我的项目/历史存档/公众号写作", "品牌资产"):
            self.assertTrue((self.ws / relative).is_dir(), relative)

    def test_init_never_overwrites_and_reports_kept_files(self):
        self.init()
        persona = self.ws / "用户人设.md"
        persona.write_text("# 我自己的人设\n", encoding="utf-8")
        (self.ws / "规范指南/运营沉淀.md").unlink()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            create.main(["init", "--workspace", str(self.ws)])
        self.assertEqual(persona.read_text(encoding="utf-8"), "# 我自己的人设\n")
        self.assertIn("kept existing: 用户人设.md", out.getvalue())
        self.assertIn("created: 规范指南/运营沉淀.md", out.getvalue())
        self.assertTrue((self.ws / "规范指南/运营沉淀.md").is_file())

    def test_init_records_default_workspace_once(self):
        self.init()
        self.assertEqual(self.settings(), {"workspace": self.ws.resolve().as_posix()})
        other = self.root / "另一个"
        quiet(create.main, ["init", "--workspace", str(other)])
        self.assertEqual(self.settings(), {"workspace": self.ws.resolve().as_posix()})
        quiet(create.main, ["init", "--workspace", str(other), "--set-default"])
        self.assertEqual(self.settings(), {"workspace": other.resolve().as_posix()})

    def test_init_no_remember_leaves_settings_alone(self):
        self.init("--no-remember")
        self.assertIsNone(self.settings())
        self.assertTrue((self.ws / "用户人设.md").is_file())

    def test_brand_creates_skeleton_and_refuses_existing(self):
        self.init()
        quiet(create.main, ["brand", "blue-cat", "--name", "蓝猫", "--workspace", str(self.ws)])
        root = self.ws / "品牌资产/blue-cat"
        kit = json.loads((root / "brand-kit.json").read_text(encoding="utf-8"))
        self.assertEqual((kit["brandId"], kit["name"]), ("blue-cat", "蓝猫"))
        for relative in ("assets/canonical", "assets/scenes", "candidates", "character.md", "style.md",
                         "provenance.md"):
            self.assertTrue((root / relative).exists(), relative)
        for args in (["brand", "blue-cat"], ["brand", "Blue_Cat"], ["brand", "../x"]):
            with self.subTest(args=args), self.assertRaises(SystemExit):
                quiet(create.main, [*args, "--workspace", str(self.ws)])

    def test_commands_other_than_init_need_existing_workspace(self):
        for args in (["new", "oidc-login"], ["brand", "blue-cat"]):
            with self.subTest(args=args), self.assertRaises(SystemExit):
                quiet(create.main, [*args, "--workspace", str(self.ws)])
        self.assertFalse(self.ws.exists())

    def test_new_project_gets_dated_folder_brief_and_suffix(self):
        self.init()
        quiet(create.main, ["new", "oidc-login", "--workspace", str(self.ws), "--date", "20261017"])
        projects = self.ws / "我的项目"
        self.assertTrue((projects / "公众号写作/20261017-oidc-login/assets").is_dir())
        brief = (projects / "_briefs/20261017-oidc-login.md").read_text(encoding="utf-8")
        self.assertIn("需求卡", brief)
        self.assertIn("配图品牌", brief)
        quiet(create.main, ["new", "oidc-login", "--workspace", str(self.ws), "--date", "20261017"])
        self.assertTrue((projects / "公众号写作/20261017-oidc-login-02").is_dir())
        self.assertTrue((projects / "_briefs/20261017-oidc-login-02.md").is_file())

    def test_invalid_slug_or_date_rejected(self):
        self.init()
        for args in (["new", "OIDC", "--workspace", str(self.ws)],
                     ["new", "../x", "--workspace", str(self.ws)],
                     ["new", "con", "--workspace", str(self.ws)],
                     ["new", "ok", "--workspace", str(self.ws), "--date", "2026-10-17"]):
            with self.subTest(args=args), self.assertRaises(SystemExit):
                quiet(create.main, args)
        self.assertEqual(list((self.ws / "我的项目/公众号写作").iterdir()), [])

    def test_workspace_lookup_order(self):
        with self.assertRaises(SystemExit):
            create.resolve_workspace()
        settings = self.root / "home/.ai-knowledge/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({"workspace": str(self.ws)}), encoding="utf-8")
        self.assertEqual(create.resolve_workspace(), (self.ws, "settings.json"))
        os.environ["AI_KNOWLEDGE_WORKSPACE"] = str(self.root / "env-ws")
        self.assertEqual(create.resolve_workspace(), (self.root / "env-ws", "AI_KNOWLEDGE_WORKSPACE"))
        self.assertEqual(create.resolve_workspace(str(self.ws)), (self.ws, "argument"))

    def test_broken_settings_is_an_error(self):
        settings = self.root / "home/.ai-knowledge/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text("{not json", encoding="utf-8")
        with self.assertRaises(SystemExit):
            create.resolve_workspace()
        with self.assertRaises(SystemExit):
            self.init()

    def project(self, name="20261017-oidc-login"):
        quiet(create.main, ["init", "--workspace", str(self.ws)])
        projects = self.ws / "我的项目"
        main = projects / "公众号写作" / name
        main.mkdir(parents=True)
        (main / "review.md").write_text("# r\n", encoding="utf-8")
        (projects / "推文写作" / name).mkdir()
        (projects / "推文写作" / name / "xiaohongshu.md").write_text("短文案\n", encoding="utf-8")
        return projects, name

    def test_save_article_moves_main_and_adaptations(self):
        projects, name = self.project()
        quiet(save.main, [name, "--workspace", str(self.ws), "--dry-run"])
        self.assertTrue((projects / "公众号写作" / name).is_dir())
        quiet(save.main, [name, "--workspace", str(self.ws)])
        self.assertFalse((projects / "公众号写作" / name).exists())
        self.assertEqual((projects / "历史存档/公众号写作" / name / "review.md").read_text(encoding="utf-8"), "# r\n")
        self.assertTrue((projects / "历史存档/推文写作" / name / "xiaohongshu.md").is_file())

    def test_save_article_refuses_existing_target_or_missing_review(self):
        projects, name = self.project()
        (projects / "历史存档/推文写作" / name).mkdir()
        with self.assertRaises(SystemExit):
            quiet(save.main, [name, "--workspace", str(self.ws)])
        self.assertTrue((projects / "公众号写作" / name / "review.md").is_file())
        (projects / "公众号写作/20261017-empty").mkdir()
        for bad in ("20261017-empty", "oidc-login", "20261017-../x"):
            with self.subTest(name=bad), self.assertRaises(SystemExit):
                quiet(save.main, [bad, "--workspace", str(self.ws)])


class ContentTypeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bundle = write_bundle(Path(self.tmp.name) / "topic")

    def tearDown(self):
        self.tmp.cleanup()

    def replace(self, old, new):
        for name in ("article.md", "review.md"):
            path = self.bundle / name
            path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def test_four_content_types_accepted_old_modes_rejected(self):
        current = "explainer"
        for mode in ("retrospective", "evaluation", "opinion", "explainer"):
            self.replace(f'mode: "{current}"', f'mode: "{mode}"')
            current = mode
            with self.subTest(mode=mode):
                self.assertEqual(validate_bundle(self.bundle), [])
        self.replace('mode: "explainer"', 'mode: "concept"')
        self.assertIn("article.md: invalid mode", validate_bundle(self.bundle))

    def test_public_source_and_author_test_evidence_types(self):
        self.replace("| 协议原理 | 示例规范第 3 节 |", "| 公开资料 | 示例页面，访问 2026-10-17 |")
        self.replace("| 通用知识 | 示例教材 |", "| 实测记录 | 协作文档 T1 第 1–3 次 |")
        self.assertEqual(validate_bundle(self.bundle), [])


if __name__ == "__main__":
    unittest.main()
