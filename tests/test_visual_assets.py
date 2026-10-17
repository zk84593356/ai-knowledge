"""Behavior tests for visual routing, integrity, publishable formats and approval boundaries.

The brand kit comes from tests/fixtures/workspace-demo/品牌资产/demo-brand; the real home directory is
replaced by an empty temporary one in every test.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from bundle_fixtures import SVG, asset_record, png_bytes, write_bundle
from validate import ROOT, validate_bundle as core_bundle

PACKAGE = ROOT / "skills/ai-knowledge"
PERSONAL = ROOT / "tests/fixtures/workspace-demo"
KIT = PERSONAL / "品牌资产/demo-brand"
spec = importlib.util.spec_from_file_location("visual", PACKAGE / "scripts/visual_assets.py")
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)
ENV = visual.ENV_VAR


def isolated_env(home, personal=None):
    """Subprocess environment whose home is a temporary directory."""
    env = {k: v for k, v in os.environ.items() if k != ENV}
    env.update(HOME=str(home), USERPROFILE=str(home))
    if personal is not None:
        env[ENV] = str(personal)
    return env


class VisualTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.topic = write_bundle(self.root / "topic")
        self.manifest_path = self.topic / "assets/manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text("utf-8"))
        self.home = self.root / "home"
        self.home.mkdir()
        environ = patch.dict(os.environ)
        environ.start()
        self.addCleanup(environ.stop)
        os.environ.pop(ENV, None)
        home = patch.object(Path, "home", return_value=self.home)
        home.start()
        self.addCleanup(home.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def personal_copy(self, target, brand_id=None):
        shutil.copytree(PERSONAL, target)
        if brand_id:
            kit = target / "品牌资产" / brand_id
            (target / "品牌资产/demo-brand").rename(kit)
            path = kit / "brand-kit.json"
            data = json.loads(path.read_text("utf-8"))
            data["brandId"] = brand_id
            path.write_text(json.dumps(data), encoding="utf-8")
        return target

    def remember(self, workspace):
        (self.home / ".ai-knowledge").mkdir(exist_ok=True)
        (self.home / ".ai-knowledge/settings.json").write_text(
            json.dumps({"workspace": str(workspace)}), encoding="utf-8")

    def save(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def record(self, path):
        return next(a for a in self.manifest["assets"] if a["path"] == path)

    def test_synthetic_bundle_passes_both_checkers(self):
        self.assertEqual(visual.validate_bundle(self.topic), [])
        self.assertEqual(core_bundle(self.topic), [])
        self.assertEqual(visual.dimensions(self.topic / "assets/cover.png"), (4, 3))

    def test_no_images_bundle_passes_without_manifest_or_kit(self):
        topic = write_bundle(self.root / "plain", images=False)
        with patch.object(visual, "validate_kit", side_effect=AssertionError("unexpected kit")):
            self.assertEqual(visual.validate_bundle(topic), [])
        self.assertEqual(core_bundle(topic), [])
        self.assertFalse((topic / "assets").exists())

    def test_visual_plan_file_not_required(self):
        self.assertFalse((self.topic / "visual-plan.md").exists())
        self.assertEqual(visual.validate_bundle(self.topic), [])

    def test_manifest_required_once_images_or_assets_exist(self):
        self.manifest_path.unlink()
        self.assertEqual(visual.validate_bundle(self.topic), ["missing assets/manifest.json"])
        topic = write_bundle(self.root / "plain", images=False)
        (topic / "assets").mkdir()
        self.assertEqual(visual.validate_bundle(topic), ["missing assets/manifest.json"])
        shutil.rmtree(topic / "assets")
        path = topic / "article.md"
        path.write_text(path.read_text("utf-8") + "\n![图](./assets/x.png)\n", encoding="utf-8")
        self.assertEqual(visual.validate_bundle(topic), ["missing assets/manifest.json"])

    def test_svg_registered_as_source_but_not_embedded_in_article(self):
        self.assertEqual(self.record("./assets/cover.svg")["type"], "cover")
        path = self.topic / "article.md"
        path.write_text(path.read_text("utf-8").replace("./assets/flow.png", "./assets/cover.svg"),
                        encoding="utf-8")
        self.assertEqual(visual.validate_bundle(self.topic),
                         ["article.md: article.md may embed only PNG/JPEG; keep SVG as editable source"])

    def test_plain_summary_and_no_brand_never_read_personal_kit(self):
        os.environ[ENV] = str(PERSONAL)
        with patch.object(visual, "validate_kit", side_effect=AssertionError("unexpected load")):
            self.assertEqual(visual.select_context(visual=False)["route"], "text-only")
            result = visual.select_context(visual=True, no_brand=True, brand=KIT)
            self.assertEqual((result["route"], result["brand"]), ("generic", None))

    def test_no_workspace_anywhere_is_generic(self):
        self.assertFalse((PACKAGE / "styles").exists())
        result = visual.select_context(visual=True)
        self.assertEqual((result["route"], result["source"], result["source_path"]), ("generic", "settings", None))

    def test_env_kit_loads_by_name_without_promoting_palette(self):
        os.environ[ENV] = str(PERSONAL)
        result = visual.select_context(visual=True, brand_id="demo-brand")
        self.assertEqual((result["route"], result["source"]), ("named", "named"))
        self.assertEqual(Path(result["brand"]), KIT.resolve())
        self.assertEqual(result["brandId"], "demo-brand")
        self.assertEqual(result["approval"]["brandPalette"], "proposed")

    def test_settings_workspace_used_when_env_unset(self):
        target = self.personal_copy(self.root / "ws")
        self.remember(target)
        result = visual.select_context(visual=True, brand_id="demo-brand")
        self.assertEqual(result["route"], "named")
        self.assertEqual(Path(result["brand"]), (target / "品牌资产/demo-brand").resolve())
        self.assertEqual(visual.select_context(visual=True)["available"], ["demo-brand"])

    def test_precedence_explicit_then_env_then_settings(self):
        self.remember(self.personal_copy(self.root / "settings-ws", "settings-kit"))
        env_root = self.personal_copy(self.root / "env-ws", "env-kit")
        explicit = self.personal_copy(self.root / "explicit-ws", "explicit-kit") / "品牌资产/explicit-kit"
        os.environ[ENV] = str(env_root)
        self.assertEqual(visual.select_context(visual=True, brand=explicit)["brandId"], "explicit-kit")
        self.assertEqual(visual.select_context(visual=True)["available"], ["env-kit"])
        os.environ.pop(ENV)
        self.assertEqual(visual.select_context(visual=True)["available"], ["settings-kit"])

    def test_workspace_argument_beats_env(self):
        os.environ[ENV] = str(self.personal_copy(self.root / "env-ws", "env-kit"))
        argument = self.personal_copy(self.root / "arg-ws", "arg-kit")
        self.assertEqual(visual.select_context(visual=True, workspace=argument)["available"], ["arg-kit"])
        result = visual.select_context(visual=True, workspace=argument, brand_id="arg-kit")
        self.assertEqual((result["route"], result["brandId"]), ("named", "arg-kit"))
        self.assertEqual([k["brandId"] for k in visual.list_kits(argument)["kits"]], ["arg-kit", "demo-draft"])

    def test_missing_env_directory_does_not_use_settings(self):
        self.remember(self.personal_copy(self.root / "ws"))
        for value in (str(self.root / "absent"), "relative/personal"):
            with self.subTest(value=value):
                os.environ[ENV] = value
                result = visual.select_context(visual=True, brand_id="demo-brand")
                self.assertEqual((result["route"], result["source"], result["brand"]), ("generic", "env", None))

    def test_broken_workspace_kit_falls_back(self):
        target = self.personal_copy(self.root / "broken")
        (target / "品牌资产/demo-brand/brand-kit.json").write_text("{", encoding="utf-8")
        os.environ[ENV] = str(target)
        self.assertEqual(visual.select_context(visual=True)["available"], [])
        result = visual.select_context(visual=True, brand_id="demo-brand")
        self.assertEqual((result["route"], result["brand"]), ("generic", None))
        self.assertTrue(result["issues"])

    def test_missing_empty_and_malformed_kit_fall_back(self):
        for payload in (None, "", "{}", "[]", "{"):
            with self.subTest(payload=payload):
                path = self.root / "brand-kit.json"
                if payload is not None:
                    path.write_text(payload, encoding="utf-8")
                self.assertEqual(visual.select_context(visual=True, brand=self.root)["route"], "generic")

    def test_explicit_kit_replaces_default_and_missing_does_not_substitute(self):
        os.environ[ENV] = str(PERSONAL)
        kit = self.root / "custom"
        shutil.copytree(KIT, kit)
        path = kit / "brand-kit.json"
        data = json.loads(path.read_text("utf-8")); data["brandId"] = "demo"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = visual.select_context(visual=True, brand=kit)
        self.assertEqual((result["route"], result["source"], result["brandId"]), ("explicit", "explicit", "demo"))
        result = visual.select_context(visual=True, brand=self.root / "missing")
        self.assertEqual((result["route"], result["source"], result["brand"]), ("generic", "explicit", None))
        self.assertIn("do not substitute", result["reason"])

    def test_brand_identity_and_documents_must_be_contained_and_present(self):
        kit = self.root / "kit"; shutil.copytree(KIT, kit)
        path = kit / "brand-kit.json"; data = json.loads(path.read_text("utf-8"))
        data["identity"]["turnaround"] = "../outside.png"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(visual.validate_kit(kit))
        data["identity"]["turnaround"] = "assets/canonical/turnaround.png"
        data["contentGuidelines"]["character"] = "missing.md"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(visual.validate_kit(kit))

    def test_manifest_paths_reject_windows_urls_encoded_traversal(self):
        for target in ("../x", "/x", "C:/x", r"a\b", "https://example.com/x",
                       "%2e%2e/x", "//server/share", "assets/a.svg?x"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                visual.contained(self.root, target)

    def test_symlink_escape_rejected(self):
        outside = self.root / "outside"; outside.mkdir()
        link = self.topic / "assets/link"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest("OS did not permit symlink: " + str(exc))
        with self.assertRaises(ValueError):
            visual.contained(self.topic / "assets", "link/test.svg")

    def test_hash_and_dimensions_detect_asset_change(self):
        self.manifest["assets"][0]["width"] += 1; self.save()
        self.assertTrue(visual.validate_bundle(self.topic))
        self.manifest["assets"][0]["width"] -= 1
        self.manifest["assets"][0]["sha256"] = "0" * 64; self.save()
        self.assertTrue(visual.validate_bundle(self.topic))

    def test_missing_and_unregistered_images_fail(self):
        original = (self.topic / "assets/flow.png").read_bytes()
        (self.topic / "assets/flow.png").unlink()
        self.assertTrue(visual.validate_bundle(self.topic))
        (self.topic / "assets/flow.png").write_bytes(original)
        self.manifest["assets"] = [a for a in self.manifest["assets"] if a["path"] != "./assets/flow.png"]
        self.save()
        self.assertEqual(visual.validate_bundle(self.topic), ["article.md: missing or unregistered image"])

    def test_jpeg_header_is_publishable(self):
        jpeg = (b"\xff\xd8" + b"\xff\xc0" + (17).to_bytes(2, "big") + b"\x08"
                + (3).to_bytes(2, "big") + (4).to_bytes(2, "big") + b"\x03" + b"\x00" * 9 + b"\xff\xd9")
        (self.topic / "assets/photo.jpg").write_bytes(jpeg)
        self.manifest["assets"].append(asset_record(self.topic, "photo", "photo.jpg", "illustration"))
        self.save()
        path = self.topic / "article.md"
        path.write_text(path.read_text("utf-8") + "\n![示意照片](./assets/photo.jpg)\n", encoding="utf-8")
        self.assertEqual(visual.validate_bundle(self.topic), [])

    def test_planned_image_can_be_missing_but_cannot_be_embedded(self):
        self.manifest["assets"].append(dict(id="pending", type="banner", path="./assets/banner.png",
                                           status="planned", reason="no platform selected",
                                           source="user request", method="pending layout", references=[]))
        self.save()
        self.assertEqual(visual.validate_bundle(self.topic), [])
        (self.topic / "pending.md").write_text("![Banner](./assets/banner.png)", encoding="utf-8")
        self.assertTrue(visual.validate_bundle(self.topic))

    def test_unapproved_cannot_be_promoted_by_file_existence(self):
        self.manifest["assets"][0]["status"] = "approved"; self.save()
        self.assertTrue(visual.validate_bundle(self.topic))
        self.manifest["assets"][0]["status"] = "generated"
        self.manifest["status"] = "approved"; self.save()
        self.assertTrue(visual.validate_bundle(self.topic))

    def test_rejected_and_failed_basic_review_not_embedded(self):
        for key, value in (("status", "rejected"), ("identity", "fail"), ("knowledge", "pending")):
            with self.subTest(key=key):
                original = json.loads(self.manifest_path.read_text("utf-8"))
                target = self.record("./assets/cover.png")
                if key == "status":
                    target[key] = value
                else:
                    target["review"][key] = value
                self.save()
                self.assertTrue(visual.validate_bundle(self.topic))
                self.manifest = original; self.save()

    def test_relative_inline_reference_links_and_code_examples(self):
        code = chr(96)
        text = ('![a](./assets/a.svg "title")\n![b][img]\n[img]: ./assets/b.png\n'
                + code + '![fake](https://invalid)' + code + '\n'
                + code * 3 + '\n![example](./absent)\n' + code * 3)
        self.assertEqual(visual.image_links(text), ["./assets/a.svg", "./assets/b.png"])
        for text in ("![[x]]", "<img src='x'>", "![x][undefined]", "![](./assets/x.png)"):
            with self.assertRaises(ValueError):
                visual.image_links(text)

    def test_remote_absolute_and_traversal_images_fail(self):
        path = self.topic / "bad.md"
        for target in ("https://example.com/a.png", "file:///tmp/x", "/x.png",
                       "./assets/../../outside.png", "./assets/%2e%2e/outside.png"):
            with self.subTest(target=target):
                path.write_text("![bad](" + target + ")", encoding="utf-8")
                self.assertTrue(visual.validate_bundle(self.topic))

    def test_active_or_external_svg_rejected(self):
        path = self.root / "bad.svg"
        for body in ('<script>alert(1)</script>', '<image href="https://example.com/x"/>',
                     '<rect onclick="x()"/>', '<style>@import "x";</style>',
                     '<foreignObject/>', '<image href="../x.png"/>'):
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
                            + body + '</svg>', encoding="utf-8")
            with self.assertRaises(ValueError):
                visual.dimensions(path)

    def test_svg_may_embed_exact_png_bytes(self):
        import base64
        data = png_bytes()
        path = self.root / "embed.svg"
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="4" height="3">'
                        '<image href="data:image/png;base64,' + base64.b64encode(data).decode()
                        + '" width="4" height="3"/></svg>', encoding="utf-8")
        self.assertEqual(visual.dimensions(path), (4.0, 3.0))

    def test_truncated_png_and_bad_svg_fail(self):
        path = self.root / "broken.png"; path.write_bytes(b"\x89PNG\r\n\x1a\n")
        with self.assertRaises(ValueError):
            visual.dimensions(path)
        path = self.root / "broken.svg"; path.write_text('<svg width="100%" height="0"/>')
        with self.assertRaises(ValueError):
            visual.dimensions(path)

    def test_duplicate_ids_and_malformed_record_fail_cleanly(self):
        self.manifest["assets"].append(self.manifest["assets"][0]); self.save()
        self.assertTrue(visual.validate_bundle(self.topic))
        for malformed in (None, "bad", [], 5):
            self.manifest["assets"] = [malformed]; self.save()
            self.assertTrue(visual.validate_bundle(self.topic))

    def test_duplicate_json_keys_rejected(self):
        self.manifest_path.write_text('{"assets": [], "assets": []}', encoding="utf-8")
        self.assertEqual(visual.validate_bundle(self.topic), ["duplicate JSON key"])

    def test_brand_version_palette_and_reference_consistency(self):
        kit = json.loads((KIT / "brand-kit.json").read_text("utf-8"))
        self.manifest.update(brandId=kit["brandId"], kitVersion=kit["kitVersion"],
                             paletteStatus=kit["approval"]["brandPalette"])
        self.manifest["assets"][0]["references"] = [kit["assets"][0]["id"]]
        self.save()
        self.assertEqual(visual.validate_bundle(self.topic, KIT), [])
        for field, value in (("kitVersion", "unknown"), ("paletteStatus", "confirmed")):
            original = self.manifest[field]
            self.manifest[field] = value; self.save()
            self.assertIn("selected kit mismatch: " + field, visual.validate_bundle(self.topic, KIT))
            self.manifest[field] = original; self.save()
        self.manifest["assets"][0]["references"] = ["not-in-kit"]; self.save()
        self.assertIn("asset 0: unknown brand reference id", visual.validate_bundle(self.topic, KIT))

    def test_moved_topic_runs_isolated_package_read_only(self):
        package = self.root / "ai-knowledge"
        shutil.copytree(PACKAGE, package, ignore=shutil.ignore_patterns("__pycache__"))
        moved = self.root / "elsewhere/deeper/topic"
        shutil.copytree(self.topic, moved)
        before = {p.relative_to(package): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in package.rglob("*") if p.is_file()}
        for personal, route in ((None, "generic"), (PERSONAL, "named")):
            run = subprocess.run([sys.executable, "-B", str(package / "scripts/visual_assets.py"),
                                  "context", "--visual", "--brand-id", "demo-brand"], cwd=moved,
                                 capture_output=True, env=isolated_env(self.home, personal))
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["route"], route)
        self.assertEqual(list(self.home.iterdir()), [])
        run = subprocess.run([sys.executable, "-B", str(package / "scripts/visual_assets.py"),
                              "bundle", str(moved)], cwd=self.root, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertEqual(core_bundle(moved), [])
        self.assertEqual(before, {p.relative_to(package): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in package.rglob("*") if p.is_file()})

    def test_editable_svg_fixture_is_safe(self):
        path = self.root / "fixture.svg"
        path.write_text(SVG, encoding="utf-8")
        self.assertEqual(visual.dimensions(path), (4.0, 3.0))


if __name__ == "__main__":
    unittest.main()
