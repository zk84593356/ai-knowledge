"""Read-only visual routing and local PNG/JPEG/SVG checks; Python 3.10+ stdlib.

Topic bundles: article.md embeds only registered PNG/JPEG from ./assets/; SVG may be
registered in assets/manifest.json as an editable source. A topic with no assets/
directory and no embedded image passes, because images are optional.
Does not generate images, infer facts, approve aesthetics, or establish rights.

No personal brand kit is bundled. Lookup order: --brand <kit-dir>, then
$AI_KNOWLEDGE_PERSONAL/visual, then ~/.ai-knowledge/personal/visual; the kit root holds
brand-kit.json. Missing or invalid kits fall back to generic visuals.
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


def validate_kit(root):
    errors = []
    try:
        kit = load(contained(root, "brand-kit.json"))
        for field in ("brandId", "kitVersion", "licenseStatus"):
            if not isinstance(kit.get(field), str) or not kit[field].strip():
                errors.append("missing kit " + field)
        if not isinstance(kit.get("approval"), dict):
            errors.append("missing approval states")
        assets = kit.get("assets")
        if not isinstance(assets, list) or not assets:
            raise ValueError("nonempty assets list required")
        ids, paths = set(), set()
        for index, asset in enumerate(assets):
            try:
                if not isinstance(asset.get("id"), str) or not asset["id"] or asset["id"] in ids:
                    raise ValueError("missing or duplicate asset id")
                path = verify_image(root, asset)
                if path in paths:
                    raise ValueError("duplicate asset path")
                ids.add(asset["id"])
                paths.add(path)
            except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
                errors.append(f"asset {index}: {exc}")
        for group, required in (
            ("identity", ("turnaround", "detail", "original")),
            ("contentGuidelines", ("brandPositioning", "character", "styleDNA", "visualGuidelines",
                                   "scenes", "provenance", "quality")),
            ("templates", ("visualPlan", "characterPrompt", "knowledgeVisualPrompt")),
        ):
            values = kit.get(group, {})
            for key in required:
                path = contained(root, values.get(key))
                if not path.is_file():
                    errors.append(f"missing {group}.{key}")
                if group == "identity" and path not in paths:
                    errors.append(f"unverified identity.{key}")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
        errors.append(str(exc))
    return errors


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


def select_context(visual=False, no_brand=False, brand=None):
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
        result["source"] = source
        if base is None:
            result["reason"] = (ENV_VAR + " is not an absolute path; generic visuals" if source == "env"
                                else "home directory unavailable; generic visuals")
            return result
        root = base / "visual"
    result.update(source=source, source_path=str(base.resolve()))
    if source != "explicit" and not base.is_dir():
        # A broken env setting must not silently fall through to the home directory.
        result["reason"] = (ENV_VAR + " directory missing; generic visuals, home not substituted"
                            if source == "env" else "no personal config directory; generic visuals")
        return result
    errors = validate_kit(root)
    if errors:
        result.update(reason=("explicit kit unavailable or invalid; generic visuals, do not substitute another kit"
                              if source == "explicit" else "personal kit missing or invalid; generic visuals"),
                      issues=errors)
        return result
    kit = load(root / "brand-kit.json")
    return {"route": "explicit" if source == "explicit" else "personal", "source": source,
            "source_path": result["source_path"], "brand": str(root.resolve()), "brandId": kit["brandId"],
            "kitVersion": kit["kitVersion"], "approval": kit["approval"],
            "licenseStatus": kit["licenseStatus"]}


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
    context.add_argument("--brand", type=Path)
    for name in ("kit", "bundle"):
        command = sub.add_parser(name)
        command.add_argument("directory", type=Path)
        if name == "bundle":
            command.add_argument("--brand", type=Path)
    args = parser.parse_args(argv)
    if args.command == "context":
        result = select_context(visual=args.visual, no_brand=args.no_brand, brand=args.brand)
        failed = False
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
