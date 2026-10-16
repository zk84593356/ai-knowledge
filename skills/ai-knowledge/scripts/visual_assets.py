"""Read-only visual routing and local PNG/JPEG/SVG checks; Python 3.10+ stdlib.

Topic bundles: article.md embeds only registered PNG/JPEG from ./assets/; SVG may be
registered in assets/manifest.json as an editable source. A topic with no assets/
directory and no embedded image passes, because images are optional.
Does not generate images, infer facts, approve aesthetics, or establish rights.

No personal brand kit is bundled. Lookup order: --brand <kit-dir>, then --brand-id <id>
(<personal>/brands/<id>), then the default <personal>/visual, where <personal> is
$AI_KNOWLEDGE_PERSONAL or ~/.ai-knowledge/personal. A kit root holds brand-kit.json
(schemaVersion 2) plus character.md, style.md, provenance.md and assets/.
Missing or invalid kits fall back to generic visuals. A draft kit is used only when the
user selects it explicitly; the default location never auto-loads a draft.

`list` shows the kits in the personal directory; `inspect` prints the size and SHA-256
of every image under a kit's assets/ so the Agent can register them. No command writes.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
from urllib.parse import unquote
import xml.etree.ElementTree as ET

ENV_VAR = "AI_KNOWLEDGE_PERSONAL"
LIMIT = 64 * 1024 * 1024
TYPES = {"cover", "infographic", "chart", "illustration", "banner", "profile-card"}
PUBLISHABLE = {".png", ".jpg", ".jpeg"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg"}
BRAND_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
HEX = re.compile(r"#[0-9A-Fa-f]{6}\Z")
KIT_STATUS = {"draft", "confirmed"}
LICENSE = {"local-only", "pending", "public"}
USAGE = {"article", "video"}
PALETTE_STATUS = {"proposed", "confirmed"}
ASSET_ROLES = {"canonical", "scene", "layout"}
ASSET_STATUS = {"proposed", "confirmed"}
IDENTITY_KEYS = ("original", "turnaround", "detail")
GUIDELINES = ("character", "style", "provenance")


def read(path):
    path = Path(path)
    if path.stat().st_size > LIMIT:
        raise ValueError("file exceeds 64 MiB")
    return path.read_bytes()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load(path):
    value = json.loads(read(path).decode("utf-8-sig"), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def contained(root, relative):
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("missing relative path")
    decoded = unquote(relative)
    if "\\" in decoded or ":" in decoded or "?" in decoded or "#" in decoded:
        raise ValueError("unsupported path syntax")
    path = Path(decoded)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("absolute or parent path")
    dest = (Path(root) / path).resolve()
    if not dest.is_relative_to(Path(root).resolve()):
        raise ValueError("path escapes root")
    return dest


def dimensions(path):
    raw = read(path)
    suffix = Path(path).suffix.lower()
    if suffix == ".png":
        if len(raw) < 33 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
            raise ValueError("invalid PNG header")
        size = struct.unpack(">II", raw[16:24])
    elif suffix in {".jpg", ".jpeg"}:
        if raw[:2] != b"\xff\xd8":
            raise ValueError("invalid JPEG header")
        i, size = 2, None
        while i + 4 <= len(raw):
            if raw[i] != 255:
                break
            while i < len(raw) and raw[i] == 255:
                i += 1
            if i >= len(raw):
                break
            marker = raw[i]
            i += 1
            if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
                continue
            length = int.from_bytes(raw[i:i + 2], "big")
            if length < 2 or i + length > len(raw):
                break
            if marker in {0xC0, 0xC1, 0xC2} and length >= 8:
                height, width = struct.unpack(">HH", raw[i + 3:i + 7])
                size = (width, height)
                break
            i += length
        if size is None:
            raise ValueError("unsupported or truncated JPEG")
    elif suffix == ".svg":
        text = raw.decode("utf-8")
        if re.search(r"<!DOCTYPE|<!ENTITY|<\?xml-stylesheet", text, re.I):
            raise ValueError("active XML declaration")
        tree = ET.fromstring(text)
        if tree.tag.split("}")[-1] != "svg":
            raise ValueError("not SVG")
        for node in tree.iter():
            tag = node.tag.split("}")[-1].lower()
            if tag in {"script", "foreignobject", "style", "animate", "animatetransform", "set"}:
                raise ValueError("active or unsupported SVG element")
            for key, value in node.attrib.items():
                key = key.split("}")[-1].lower()
                if key.startswith("on") or key in {"base", "style"}:
                    raise ValueError("active or unsupported SVG attribute")
                if key == "href" and not value.startswith("#"):
                    match = re.fullmatch(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/=]+)", value)
                    if not match:
                        raise ValueError("SVG external resource")
                    embedded = base64.b64decode(match[2], validate=True)
                    if not (embedded.startswith(b"\x89PNG\r\n\x1a\n") if match[1] == "png"
                            else embedded.startswith(b"\xff\xd8")):
                        raise ValueError("invalid embedded image")
                if re.search(r"url\s*\(", value, re.I) and not re.fullmatch(r"url\(#[\w-]+\)", value):
                    raise ValueError("SVG external resource")
            if node.text and re.search(r"@import|url\s*\(", node.text, re.I):
                raise ValueError("SVG external CSS")
        def number(value):
            if not re.fullmatch(r"\d+(?:\.\d+)?(?:px)?", value):
                raise ValueError("explicit SVG pixel dimensions required")
            return float(value.removesuffix("px"))
        size = (number(tree.get("width", "")), number(tree.get("height", "")))
    else:
        raise ValueError("unsupported image format; use PNG/JPEG/SVG")
    if not all(0 < n <= 32768 for n in size):
        raise ValueError("invalid dimensions")
    return size


def verify_image(root, record):
    path = contained(root, record["path"])
    size = dimensions(path)
    if size != (record.get("width"), record.get("height")):
        raise ValueError("image dimensions differ from manifest")
    if hashlib.sha256(read(path)).hexdigest() != record.get("sha256"):
        raise ValueError("image hash differs from manifest")
    return path


def text_field(kit, field, errors):
    if not isinstance(kit.get(field), str) or not kit[field].strip():
        errors.append("missing kit " + field)


def validate_kit(root):
    """Check a schemaVersion 2 kit: fields, states, registered images, identity, documents."""
    errors = []
    try:
        kit = load(contained(root, "brand-kit.json"))
        if kit.get("schemaVersion") != "2":
            raise ValueError("brand-kit.json schemaVersion must be \"2\"")
        for field in ("brandId", "name", "kitVersion"):
            text_field(kit, field, errors)
        brand_id = kit.get("brandId")
        if isinstance(brand_id, str) and (len(brand_id) > 40 or not BRAND_ID.fullmatch(brand_id)):
            errors.append("brandId must be lowercase letters, digits and hyphens (max 40)")
        if kit.get("status") not in KIT_STATUS:
            errors.append("kit status must be draft or confirmed")
        if kit.get("licenseStatus") not in LICENSE:
            errors.append("licenseStatus must be local-only, pending or public")
        usage = kit.get("usage")
        if not isinstance(usage, list) or not usage or not set(usage) <= USAGE or len(set(usage)) != len(usage):
            errors.append("usage must list article and/or video")
        approval = kit.get("approval")
        if not isinstance(approval, dict) or approval.get("brandPalette") not in PALETTE_STATUS:
            errors.append("approval.brandPalette must be proposed or confirmed")
        palette = kit.get("palette")
        if not isinstance(palette, dict) or not palette or any(
                not isinstance(v, str) or not HEX.fullmatch(v) for v in palette.values()):
            errors.append("palette must map names to #RRGGBB colors")
        assets = kit.get("assets")
        if not isinstance(assets, list) or not assets:
            raise ValueError("nonempty assets list required")
        ids, by_path = set(), {}
        for index, asset in enumerate(assets):
            try:
                asset_id = asset.get("id")
                if not isinstance(asset_id, str) or not BRAND_ID.fullmatch(asset_id) or asset_id in ids:
                    raise ValueError("missing, malformed or duplicate asset id")
                if asset.get("role") not in ASSET_ROLES:
                    raise ValueError("role must be canonical, scene or layout")
                if asset.get("status") not in ASSET_STATUS:
                    raise ValueError("asset status must be proposed or confirmed")
                path = verify_image(root, asset)
                if path in by_path:
                    raise ValueError("duplicate asset path")
                ids.add(asset_id)
                by_path[path] = asset
            except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
                errors.append(f"asset {index}: {exc}")
        identity = kit.get("identity")
        if not isinstance(identity, dict) or "original" not in identity:
            errors.append("identity.original required")
            identity = {}
        for key, value in identity.items():
            if key not in IDENTITY_KEYS:
                errors.append(f"unknown identity.{key}")
                continue
            asset = by_path.get(contained(root, value))
            if asset is None:
                errors.append(f"unverified identity.{key}")
            elif asset["role"] != "canonical":
                errors.append(f"identity.{key} must be a canonical asset")
            elif kit.get("status") == "confirmed" and asset["status"] != "confirmed":
                errors.append(f"confirmed kit needs confirmed identity.{key}")
        guidelines = kit.get("contentGuidelines")
        if not isinstance(guidelines, dict):
            guidelines = {}
        for key in GUIDELINES:
            try:
                if not contained(root, guidelines.get(key)).is_file():
                    errors.append(f"missing contentGuidelines.{key}")
            except ValueError as exc:
                errors.append(f"contentGuidelines.{key}: {exc}")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
        errors.append(str(exc))
    return errors


def inspect_kit(root):
    """Describe every image under <kit>/assets/ against the registered records; read-only."""
    root = Path(root)
    registered = {}
    try:
        kit = load(contained(root, "brand-kit.json"))
        for asset in kit.get("assets") or []:
            if isinstance(asset, dict) and isinstance(asset.get("path"), str):
                registered[asset["path"]] = asset
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    images, seen = [], set()
    base = root / "assets"
    for path in sorted(base.rglob("*")) if base.is_dir() else []:
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        seen.add(relative)
        entry = {"path": relative, "registered": relative in registered}
        try:
            contained(root, relative)
            width, height = dimensions(path)
            entry.update(width=width, height=height, sha256=hashlib.sha256(read(path)).hexdigest())
            if entry["registered"]:
                record = registered[relative]
                entry["matches"] = (record.get("width"), record.get("height"), record.get("sha256")) == (
                    width, height, entry["sha256"])
        except (OSError, ValueError, ET.ParseError) as exc:
            entry["error"] = str(exc)
        images.append(entry)
    missing = sorted(p for p in registered if p not in seen)
    return {"kit": str(root.resolve()), "images": images, "registered_missing": missing}


def personal_root():
    """Return (source, path) for the implicit personal root; path is None if unresolvable."""
    value = os.environ.get(ENV_VAR, "").strip()
    if value:
        path = Path(value).expanduser()
        return "env", path if path.is_absolute() else None
    try:
        return "home", Path.home() / ".ai-knowledge" / "personal"
    except (RuntimeError, KeyError):
        return "home", None


def kit_summary(root):
    kit = load(root / "brand-kit.json")
    return {"brandId": kit["brandId"], "name": kit["name"], "status": kit["status"],
            "kitVersion": kit["kitVersion"], "usage": kit["usage"], "approval": kit["approval"],
            "licenseStatus": kit["licenseStatus"]}


def select_context(visual=False, no_brand=False, brand=None, brand_id=None):
    if not visual:
        return {"route": "text-only", "source": None, "source_path": None, "brand": None,
                "reason": "visual resources not loaded"}
    result = {"route": "generic", "source": None, "source_path": None, "brand": None,
              "reason": "personal visual disabled"}
    if no_brand:
        return result
    if brand is not None:
        source, base = "explicit", Path(brand)
        root = base
    else:
        source, base = personal_root()
        result["source"] = "named" if brand_id is not None else source
        if base is None:
            result["reason"] = (ENV_VAR + " is not an absolute path; generic visuals" if source == "env"
                                else "home directory unavailable; generic visuals")
            return result
        if brand_id is not None:
            if not isinstance(brand_id, str) or not BRAND_ID.fullmatch(brand_id):
                result["reason"] = "invalid brand id; generic visuals, do not substitute another kit"
                return result
            root = base / "brands" / brand_id
        else:
            root = base / "visual"
    selected = source == "explicit" or brand_id is not None
    result.update(source="named" if brand_id is not None and source != "explicit" else source,
                  source_path=str(base.resolve()))
    if not selected and not base.is_dir():
        # A broken env setting must not silently fall through to the home directory.
        result["reason"] = (ENV_VAR + " directory missing; generic visuals, home not substituted"
                            if source == "env" else "no personal config directory; generic visuals")
        return result
    errors = validate_kit(root)
    if errors:
        result.update(reason=("selected kit unavailable or invalid; generic visuals, do not substitute another kit"
                              if selected else "personal kit missing or invalid; generic visuals"),
                      issues=errors)
        return result
    summary = kit_summary(root)
    if not selected and summary["status"] != "confirmed":
        result.update(reason="default kit is a draft; confirm it or select it by name before use",
                      draft=str(root.resolve()))
        return result
    route = "explicit" if source == "explicit" else ("named" if brand_id is not None else "personal")
    return {"route": route, "source": result["source"], "source_path": result["source_path"],
            "brand": str(root.resolve()), **summary}


def list_kits():
    """List the default kit and brands/<id> kits in the personal directory; read-only."""
    source, base = personal_root()
    result = {"source": source, "source_path": str(base.resolve()) if base else None, "kits": []}
    if base is None or not base.is_dir():
        return result
    candidates = [("default", base / "visual")]
    brands = base / "brands"
    if brands.is_dir():
        candidates += [("brands/" + p.name, p) for p in sorted(brands.iterdir()) if p.is_dir()]
    for location, root in candidates:
        if not (root / "brand-kit.json").is_file():
            continue
        errors = validate_kit(root)
        entry = {"location": location, "path": str(root.resolve()), "ok": not errors}
        if errors:
            entry["issues"] = errors
        else:
            entry.update(kit_summary(root))
            if location != "default" and entry["brandId"] != root.name:
                entry["ok"] = False
                entry["issues"] = ["directory name differs from brandId"]
        result["kits"].append(entry)
    return result


def image_links(text):
    # Strip fenced and inline code examples. Not a general Markdown parser.
    lines, fence = [], None
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(\x60{3,}|~{3,})(.*)$", line)
        if match:
            token, tail = match.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not tail.strip():
                fence = None
            continue
        if fence is None:
            lines.append(line)
    text = re.sub(r"(\x60+).*?\1", "", "\n".join(lines))
    if re.search(r"<img\b|!\[\[", text, re.I):
        raise ValueError("convert HTML/wiki images to standard Markdown")
    definitions = {m[1].strip().casefold(): m[2] or m[3] for m in re.finditer(
        r'(?m)^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))', text)}
    targets = []
    for match in re.finditer(r'!\[([^\]\n]*)\](?:\(([^)\n]*)\)|\[([^\]\n]*)\])?', text):
        alt, inline, label = match.groups()
        if not alt.strip():
            raise ValueError("image alt is empty")
        if inline is not None:
            parsed = re.fullmatch(r'\s*(?:<([^>]+)>|([^\s]+?))(?:\s+"[^"]*")?\s*', inline)
            if not parsed:
                raise ValueError("unsupported Markdown image target")
            targets.append(parsed[1] or parsed[2])
        else:
            key = (label or alt).strip().casefold()
            if key not in definitions:
                raise ValueError("undefined image reference")
            targets.append(definitions[key])
    return targets


def validate_bundle(root, brand=None):
    root = Path(root).resolve()
    errors, entries, documents = [], {}, {}
    for doc in sorted(root.glob("*.md")):
        try:
            contained(root, doc.name)
            documents[doc] = image_links(read(doc).decode("utf-8-sig"))
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"{doc.name}: {exc}")
    # Images are optional: a topic with no assets/ and no embedded image needs no manifest.
    if not (root / "assets").exists() and not any(documents.values()):
        return errors
    try:
        if not (root / "assets/manifest.json").is_file():
            raise ValueError("missing assets/manifest.json")
        manifest = load(contained(root, "assets/manifest.json"))
        if manifest.get("schemaVersion") != "1" or manifest.get("status") not in {"draft", "approved"}:
            errors.append("invalid manifest schema/status")
        for key in ("brandId", "kitVersion", "paletteStatus", "batch"):
            if not isinstance(manifest.get(key), str) or not manifest[key].strip():
                errors.append("missing manifest " + key)
        assets = manifest.get("assets")
        if not isinstance(assets, list):
            raise ValueError("assets must be a list")
        reference_ids = None
        if brand is not None:
            kit_errors = validate_kit(brand)
            errors.extend("selected kit: " + e for e in kit_errors)
            if not kit_errors:
                kit = load(contained(brand, "brand-kit.json"))
                reference_ids = {a["id"] for a in kit["assets"]}
                for key in ("brandId", "kitVersion"):
                    if manifest.get(key) != kit[key]:
                        errors.append("selected kit mismatch: " + key)
                if manifest.get("paletteStatus") != kit["approval"].get("brandPalette"):
                    errors.append("selected kit mismatch: paletteStatus")
        ids = set()
        for index, asset in enumerate(assets):
            try:
                if not isinstance(asset.get("id"), str) or not asset["id"] or asset["id"] in ids:
                    raise ValueError("missing or duplicate id")
                ids.add(asset["id"])
                if asset.get("type") not in TYPES or asset.get("status") not in {
                        "planned", "generated", "approved", "rejected"}:
                    raise ValueError("invalid type/status")
                relative = asset["path"]
                if not relative.startswith("./assets/"):
                    raise ValueError("asset path must start ./assets/")
                path = contained(root / "assets", relative[len("./assets/"):])
                if path in entries:
                    raise ValueError("duplicate asset path")
                for key in ("source", "method"):
                    if not isinstance(asset.get(key), str) or not asset[key].strip():
                        raise ValueError("missing " + key)
                if not isinstance(asset.get("references"), list):
                    raise ValueError("references must be a list")
                if reference_ids is not None and any(r not in reference_ids for r in asset["references"]):
                    raise ValueError("unknown brand reference id")
                entries[path] = asset
                if asset["status"] == "planned":
                    if not asset.get("reason"):
                        raise ValueError("planned asset needs reason")
                else:
                    verify_image(root, asset)
                    review = asset.get("review", {})
                    for key in ("identity", "knowledge", "readability"):
                        if review.get(key) not in {"pass", "fail", "pending", "na"}:
                            raise ValueError("invalid review " + key)
                    if review.get("rights") not in {"local-only", "pending", "public"}:
                        raise ValueError("invalid rights")
                    if review.get("aesthetic") not in {"pending", "pass", "fail"}:
                        raise ValueError("invalid aesthetic review")
                    if asset["status"] == "approved":
                        if not asset.get("approval") or review["aesthetic"] != "pass" or any(
                                review[k] not in {"pass", "na"} for k in ("identity", "knowledge", "readability")):
                            raise ValueError("approved without acceptance evidence")
                if manifest["status"] == "approved" and asset["status"] != "approved":
                    raise ValueError("approved bundle has unapproved asset")
            except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
                errors.append(f"asset {index}: {exc}")
        for doc, targets in documents.items():
            try:
                for target in targets:
                    if not target.startswith("./assets/"):
                        raise ValueError("image must use ./assets/ relative path")
                    path = contained(root / "assets", target[len("./assets/"):])
                    if doc.name == "article.md" and path.suffix.lower() not in PUBLISHABLE:
                        raise ValueError("article.md may embed only PNG/JPEG; keep SVG as editable source")
                    if not path.is_file() or path not in entries:
                        raise ValueError("missing or unregistered image")
                    asset = entries[path]
                    if asset["status"] not in {"generated", "approved"}:
                        raise ValueError("unready image embedded")
                    if any(asset.get("review", {}).get(k) not in {"pass", "na"}
                           for k in ("identity", "knowledge", "readability")):
                        raise ValueError("image basic review incomplete")
            except (OSError, ValueError, TypeError) as exc:
                errors.append(f"{doc.name}: {exc}")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(str(exc))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    context = sub.add_parser("context")
    context.add_argument("--visual", action="store_true")
    context.add_argument("--no-brand", action="store_true")
    choice = context.add_mutually_exclusive_group()
    choice.add_argument("--brand", type=Path)
    choice.add_argument("--brand-id")
    sub.add_parser("list")
    for name in ("kit", "bundle", "inspect"):
        command = sub.add_parser(name)
        command.add_argument("directory", type=Path)
        if name == "bundle":
            command.add_argument("--brand", type=Path)
    args = parser.parse_args(argv)
    failed = False
    if args.command == "context":
        result = select_context(visual=args.visual, no_brand=args.no_brand, brand=args.brand,
                                brand_id=args.brand_id)
    elif args.command == "list":
        result = list_kits()
    elif args.command == "inspect":
        result = inspect_kit(args.directory)
    else:
        errors = (validate_kit(args.directory) if args.command == "kit"
                  else validate_bundle(args.directory, args.brand))
        result = {"ok": not errors, "errors": errors,
                  "not_checked": "full raster decoding, facts, identity, aesthetics, rights"}
        failed = bool(errors)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
