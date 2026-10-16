"""Behavior tests for schemaVersion 2 brand kits: format, draft gate, named brands, list, inspect.

Kits come from tests/fixtures/personal-demo; the real home directory is replaced by an
empty temporary one in every test.
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

from bundle_fixtures import png_bytes
from validate import ROOT

PACKAGE = ROOT / "skills/ai-knowledge"
PERSONAL = ROOT / "tests/fixtures/personal-demo"
KIT = PERSONAL / "visual"
DRAFT = PERSONAL / "brands/demo-draft"
TEMPLATES = PACKAGE / "assets/templates/brand"
spec = importlib.util.spec_from_file_location("visual_brand", PACKAGE / "scripts/visual_assets.py")
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)
ENV = visual.ENV_VAR


def snapshot(root):
    return {p.relative_to(root): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(root).rglob("*") if p.is_file()}


class BrandKitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        environ = patch.dict(os.environ)
        environ.start()
        self.addCleanup(environ.stop)
        os.environ.pop(ENV, None)
        home = patch.object(Path, "home", return_value=self.home)
        home.start()
        self.addCleanup(home.stop)

    def copy(self, source, name):
        target = self.root / name
        shutil.copytree(source, target)
        return target

    def mutate(self, kit, change):
        path = kit / "brand-kit.json"
        data = json.loads(path.read_text("utf-8"))
        change(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def test_fixture_kits_pass(self):
        self.assertEqual(visual.validate_kit(KIT), [])
        self.assertEqual(visual.validate_kit(DRAFT), [])

    def test_only_schema_2_is_accepted(self):
        kit = self.copy(KIT, "kit")
        self.mutate(kit, lambda d: d.update(schemaVersion="1.1"))
        self.assertEqual(visual.validate_kit(kit), ['brand-kit.json schemaVersion must be "2"'])

    def test_three_documents_are_required(self):
        for key in visual.GUIDELINES:
            with self.subTest(key=key):
                kit = self.copy(KIT, "kit-" + key)
                (kit / (key + ".md")).unlink()
                self.assertEqual(visual.validate_kit(kit), ["missing contentGuidelines." + key])

    def test_field_values_are_checked(self):
        cases = (("brandId", "Bad_ID"), ("status", "final"), ("licenseStatus", "unknown"),
                 ("usage", []), ("usage", ["podcast"]), ("usage", ["article", "article"]),
                 ("palette", {"primary": "blue"}), ("palette", {}), ("approval", {}), ("name", " "))
        for index, (field, value) in enumerate(cases):
            with self.subTest(field=field, value=value):
                kit = self.copy(KIT, f"kit-{index}")
                self.mutate(kit, lambda d: d.update({field: value}))
                self.assertTrue(visual.validate_kit(kit))

    def test_identity_must_be_registered_canonical_images(self):
        def no_original(d):
            del d["identity"]["original"]
        changes = ((no_original, "identity.original required"),
                   (lambda d: d["identity"].update(turnaround="assets/scenes/desk.png"),
                    "identity.turnaround must be a canonical asset"),
                   (lambda d: d["identity"].update(extra="assets/canonical/original.png"),
                    "unknown identity.extra"),
                   (lambda d: d["identity"].update(detail="assets/canonical/absent.png"),
                    "unverified identity.detail"))
        for index, (change, message) in enumerate(changes):
            with self.subTest(message=message):
                kit = self.copy(KIT, f"kit-{index}")
                self.mutate(kit, change)
                self.assertIn(message, visual.validate_kit(kit))

    def test_confirmed_kit_needs_confirmed_identity(self):
        kit = self.copy(DRAFT, "draft")
        self.mutate(kit, lambda d: d.update(status="confirmed"))
        self.assertEqual(visual.validate_kit(kit), ["confirmed kit needs confirmed identity.original"])
        self.mutate(kit, lambda d: d["assets"][0].update(status="confirmed"))
        self.assertEqual(visual.validate_kit(kit), [])

    def test_asset_role_status_and_integrity(self):
        for index, (key, value) in enumerate((("role", "photo"), ("status", "approved"), ("id", "Bad ID"))):
            with self.subTest(key=key):
                kit = self.copy(DRAFT, f"draft-{index}")
                self.mutate(kit, lambda d: d["assets"][0].update({key: value}))
                self.assertTrue(visual.validate_kit(kit))
        kit = self.copy(DRAFT, "draft-bytes")
        (kit / "assets/canonical/original.png").write_bytes(png_bytes(6, 8, 10))
        self.assertIn("asset 0: image hash differs from manifest", visual.validate_kit(kit))

    def test_sample_role_is_style_reference_only(self):
        kit = self.copy(KIT, "kit")
        (kit / "assets/samples").mkdir()
        data = png_bytes(16, 9, 200)
        (kit / "assets/samples/cover.png").write_bytes(data)

        def add(d):
            d["assets"].append({"id": "sample-cover", "path": "assets/samples/cover.png", "role": "sample",
                                "status": "proposed", "width": 16, "height": 9,
                                "sha256": hashlib.sha256(data).hexdigest(), "note": "比例不精确"})
        self.mutate(kit, add)
        self.assertEqual(visual.validate_kit(kit), [])
        self.mutate(kit, lambda d: d["identity"].update(detail="assets/samples/cover.png"))
        self.assertEqual(visual.validate_kit(kit), ["identity.detail must be a canonical asset"])

    def test_default_draft_is_not_used_automatically(self):
        personal = self.copy(PERSONAL, "personal")
        shutil.rmtree(personal / "visual")
        shutil.copytree(DRAFT, personal / "visual")
        os.environ[ENV] = str(personal)
        result = visual.select_context(visual=True)
        self.assertEqual((result["route"], result["brand"]), ("generic", None))
        self.assertIn("draft", result["reason"])
        self.assertEqual(Path(result["draft"]), (personal / "visual").resolve())

    def test_named_brand_selects_draft(self):
        os.environ[ENV] = str(self.copy(PERSONAL, "personal"))
        result = visual.select_context(visual=True, brand_id="demo-draft")
        self.assertEqual((result["route"], result["source"], result["brandId"], result["status"]),
                         ("named", "named", "demo-draft", "draft"))
        self.assertEqual(Path(result["brand"]).name, "demo-draft")
        default = visual.select_context(visual=True)
        self.assertEqual((default["route"], default["brandId"]), ("personal", "personal-demo"))

    def test_named_brand_missing_or_invalid_does_not_substitute(self):
        os.environ[ENV] = str(self.copy(PERSONAL, "personal"))
        result = visual.select_context(visual=True, brand_id="absent")
        self.assertEqual((result["route"], result["brand"]), ("generic", None))
        self.assertIn("do not substitute", result["reason"])
        for value in ("../visual", "Demo", "a/b", ""):
            with self.subTest(value=value):
                result = visual.select_context(visual=True, brand_id=value)
                self.assertEqual((result["route"], result["brand"]), ("generic", None))

    def test_named_brand_with_missing_env_dir_does_not_use_home(self):
        shutil.copytree(PERSONAL, self.home / ".ai-knowledge/personal")
        os.environ[ENV] = str(self.root / "absent")
        result = visual.select_context(visual=True, brand_id="demo-draft")
        self.assertEqual((result["route"], result["brand"]), ("generic", None))

    def test_list_kits_reports_default_and_brands(self):
        personal = self.copy(PERSONAL, "personal")
        shutil.copytree(DRAFT, personal / "brands/wrong-name")
        os.environ[ENV] = str(personal)
        kits = {k["location"]: k for k in visual.list_kits()["kits"]}
        self.assertEqual(sorted(kits), ["brands/demo-draft", "brands/wrong-name", "default"])
        self.assertEqual((kits["default"]["status"], kits["default"]["ok"]), ("confirmed", True))
        self.assertEqual((kits["brands/demo-draft"]["status"], kits["brands/demo-draft"]["ok"]), ("draft", True))
        self.assertFalse(kits["brands/wrong-name"]["ok"])
        os.environ[ENV] = str(self.root / "absent")
        self.assertEqual(visual.list_kits()["kits"], [])

    def test_inspect_reports_registration_without_writing(self):
        kit = self.copy(DRAFT, "draft")
        (kit / "assets/scenes").mkdir()
        new = png_bytes(5, 2, 40)
        (kit / "assets/scenes/new.png").write_bytes(new)
        before = snapshot(kit)
        report = visual.inspect_kit(kit)
        self.assertEqual(snapshot(kit), before)
        images = {i["path"]: i for i in report["images"]}
        self.assertTrue(images["assets/canonical/original.png"]["matches"])
        self.assertEqual(images["assets/scenes/new.png"],
                         {"path": "assets/scenes/new.png", "registered": False, "width": 5, "height": 2,
                          "sha256": hashlib.sha256(new).hexdigest()})
        (kit / "assets/canonical/original.png").write_bytes(png_bytes(6, 8, 1))
        report = visual.inspect_kit(kit)
        self.assertFalse({i["path"]: i for i in report["images"]}["assets/canonical/original.png"]["matches"])
        (kit / "assets/canonical/original.png").unlink()
        self.assertEqual(visual.inspect_kit(kit)["registered_missing"], ["assets/canonical/original.png"])

    def test_templates_plus_inspect_build_a_valid_draft(self):
        kit = self.root / "brands/new-brand"
        (kit / "assets/canonical").mkdir(parents=True)
        for name in ("character.md", "style.md", "provenance.md", "brand-kit.json"):
            shutil.copy(TEMPLATES / name, kit / name)
        (kit / "assets/canonical/original.png").write_bytes(png_bytes(7, 9, 120))
        image = visual.inspect_kit(kit)["images"][0]
        self.assertFalse(image["registered"] and image.get("matches"))

        def fill(d):
            d.update(brandId="new-brand", name="新品牌")
            d["palette"] = {k: "#336699" for k in d["palette"]}
            d["assets"][0].update(width=image["width"], height=image["height"], sha256=image["sha256"])
        data = self.mutate(kit, fill)
        self.assertEqual((data["status"], data["assets"][0]["status"], data["approval"]["brandPalette"]),
                         ("draft", "proposed", "proposed"))
        self.assertEqual(visual.validate_kit(kit), [])

    def test_cli_brand_id_list_and_exclusive_options(self):
        personal = self.copy(PERSONAL, "personal")
        env = {k: v for k, v in os.environ.items() if k != ENV}
        env.update(HOME=str(self.home), USERPROFILE=str(self.home), **{ENV: str(personal)})
        script = str(PACKAGE / "scripts/visual_assets.py")
        run = subprocess.run([sys.executable, "-B", script, "context", "--visual", "--brand-id", "demo-draft"],
                             capture_output=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["route"], "named")
        run = subprocess.run([sys.executable, "-B", script, "list"], capture_output=True, env=env)
        self.assertEqual(len(json.loads(run.stdout)["kits"]), 2)
        run = subprocess.run([sys.executable, "-B", script, "context", "--visual", "--brand", str(KIT),
                              "--brand-id", "demo-draft"], capture_output=True, env=env)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
