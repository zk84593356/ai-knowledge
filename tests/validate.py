"""Read-only checks for this repository, standalone skill, or topic bundle.

A topic bundle is article.md (the one publishable article) plus review.md
(the private pre-publication record) and optional assets/.
Not a fact checker, full Markdown parser, or complete secret scanner.
"""
import argparse
import importlib.util
from datetime import date
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
ARTICLE, REVIEW = "article.md", "review.md"
ARTICLE_KEYS = ("title", "topic", "type", "mode", "summary", "tags", "created", "updated", "language")
REVIEW_KEYS = ("title", "topic", "type", "mode", "status", "created", "updated", "language")
REVIEW_SUFFIX = "｜发布前核验"
REVIEW_SECTIONS = ("发布状态", "事实核验", "公开安全过滤", "可补充的个人经历", "配图", "标题与摘要备选")
EVIDENCE_HEADER = ["ID", "结论", "类型", "依据", "核验"]
EVIDENCE_TYPES = {"项目事实", "框架行为", "协议原理", "通用知识", "推测", "建议"}
EVIDENCE_CHECKS = {"未核验", "已核验", "推翻", "存疑", "不适用"}
# "draft" is matched as a standalone word so identifiers such as draft-ietf-* stay allowed.
STATUS_WORDING = re.compile(r"未核验|已核验|发布前核验|核验日期|草稿|待审批|未批准|工作区"
                            r"|(?<![\w-])draft(?![\w-])", re.I)
SUMMARY_LIMIT = 60
MODES = {"feature", "concept", "problem"}
REFERENCES = (
    "publishing", "writing-craft", "editing", "feature-analysis", "concept-explanation",
    "problem-review", "visual-planning", "visual-brand-loading", "visual-brand-setup", "personal-experience",
    "style-loading", "style-application", "style-analysis", "style-reflection", "style-source-update",
)
TEMPLATES = ("article", "review", "personal-experience", "style-reflection",
             "writing-profile", "writing-rules")
BRAND_TEMPLATES = ("brand-kit.json", "character.md", "style.md", "provenance.md")
SCRIPTS = ("scripts/analyze_style.py", "scripts/style_learning.py", "scripts/visual_assets.py")
EXAMPLE_BUNDLES = ("concept-sso", "feature-oidc-demo")
DEMO_KIT = "tests/fixtures/personal-demo/visual"
DEMO_DRAFT_KIT = "tests/fixtures/personal-demo/brands/demo-draft"
# Personal config lives outside the repository; these trees must never carry it again.
PRIVATE_MARKER = "anyues"
PRIVATE_SCAN = ("skills", "examples")
SKIP_PARTS = {".tmp", "node_modules", "__pycache__"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
            *(f"lpt{i}" for i in range(1, 10))}


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    pairs = loader.construct_pairs(node, deep=deep)
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = value
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def frontmatter(text):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not match:
        raise ValueError("missing or unclosed frontmatter")
    data = yaml.load(match.group(1), Loader=UniqueLoader)
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    return data, text[match.end():]


def prose_and_fences(text):
    """Extract prose for simple inline-link checks; track backtick/tilde fences."""
    prose, fence, length = [], None, 0
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            mark, tail = match.groups()
            if fence is None:
                fence, length = mark[0], len(mark)
            elif mark[0] == fence and len(mark) >= length and not tail.strip():
                fence = None
            continue
        if fence is None:
            prose.append(line)
    return "\n".join(prose), fence is not None


def markdown_errors(text, single_h1=True):
    errors = []
    prose, unclosed = prose_and_fences(text)
    if unclosed:
        errors.append("unclosed code fence")
    if single_h1 and len(re.findall(r"^# \S", prose, re.M)) != 1:
        errors.append("expected exactly one H1 outside code fences")
    if re.search(r"\{\{[^\n}]+\}\}|\[TODO:", text):
        errors.append("unresolved template placeholder")
    return errors


def article_body_errors(body):
    errors = markdown_errors(body, single_h1=False)
    prose, _ = prose_and_fences(body)
    if re.search(r"^# \S", prose, re.M):
        errors.append("H1 outside code fences not allowed in article body")
    if not re.search(r"^## \S", prose, re.M):
        errors.append("article body needs at least one H2")
    if re.search(r"^ {0,3}(?:`{3,}|~{3,})\s*mermaid\b", body, re.M | re.I):
        errors.append("Mermaid fence in article body; export the diagram as an image")
    if "<!--" in prose:
        errors.append("HTML comment in article body")
    if STATUS_WORDING.search(prose):
        errors.append("production/status wording in article body")
    plain = re.sub(r"(`+).*?\1", "", prose)
    if re.search(r"<img\b|!\[\[|!\[[^\]\n]*\]\[", plain, re.I):
        errors.append("unsupported image syntax; use ![alt](./assets/<name>.png)")
    for alt, target in re.findall(r"!\[([^\]\n]*)\]\(([^)\n]*)\)", plain):
        if not alt.strip():
            errors.append("image without alt text")
        target = target.strip().split()[0].strip("<>") if target.strip() else ""
        if (not re.fullmatch(r"\./assets/[^?#\\]+\.(?:png|jpe?g)", target, re.I)
                or ".." in target.split("/")):
            errors.append("article image must be ./assets/<name>.png|.jpg|.jpeg")
    return errors


def local_link_errors(path, text, boundary):
    errors = []
    prose, _ = prose_and_fences(text)
    prose = re.sub(r"(`+).*?\1", "", prose)
    # Project uses inline links; reference-style links and heading anchors need review.
    for raw in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", prose):
        target = raw.strip().strip("<>")
        parts = urlsplit(target)
        if parts.scheme in {"https", "http", "mailto"} or not parts.path:
            continue
        if parts.scheme or parts.netloc:
            errors.append("unsupported or absolute link target")
            continue
        dest = (path.parent / unquote(parts.path)).resolve()
        if not dest.is_relative_to(boundary.resolve()):
            errors.append("local link escapes allowed root")
        elif not dest.exists():
            errors.append(f"missing local link: {parts.path}")
        elif re.fullmatch(r"L\d+(?:-L?\d+)?", parts.fragment) and dest.is_file():
            numbers = [int(n) for n in re.findall(r"\d+", parts.fragment)]
            if min(numbers) < 1 or max(numbers) > len(dest.read_text(encoding="utf-8").splitlines()):
                errors.append("source line anchor outside file")
    return errors


def sensitive_findings(text):
    # Report categories only, never the matched credential value.
    patterns = {
        "private-key material": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "possible credential": r"\b(?:gh[pousr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16})\b",
        "possible assigned secret": r"""(?i)\b(?:password|api_key|client_secret|access_token)\s*[:=]\s*["'][A-Za-z0-9_+/=-]{16,}["']""",
        "possible JWT": r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        "possible bearer token": r"Bearer\s+[A-Za-z0-9._~+/-]{20,}=*",
        "private IPv4 address": r"(?<![\d.])(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}"
                                r"|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?!\.?\d)",
        "personal Windows path": r"[A-Za-z]:[\\/]Users[\\/][^\s\\/]+",
        "private service URL": r"https?://[^\s/]*(?:\.internal|\.local)(?:[:/\s]|$)",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, text)]


def visual_checker(folder):
    spec = importlib.util.spec_from_file_location("packaged_visual_checks", folder / "scripts/visual_assets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_skill(folder):
    folder = Path(folder).resolve()
    errors = []
    entry = folder / "SKILL.md"
    if not entry.is_file():
        return ["missing SKILL.md"]
    text = entry.read_text(encoding="utf-8")
    try:
        meta, _ = frontmatter(text)
    except (ValueError, yaml.YAMLError, TypeError) as exc:
        return [f"invalid skill YAML: {type(exc).__name__}"]
    name, description = meta.get("name"), meta.get("description")
    if not isinstance(name, str) or not 1 <= len(name) <= 64 or not SLUG.fullmatch(name) or name != folder.name:
        errors.append("invalid skill name or directory mismatch")
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
        errors.append("invalid skill description")
    if len(text.splitlines()) >= 500:
        errors.append("entry exceeds project progressive-loading limit")
    for name in REFERENCES:
        if not (folder / "references" / f"{name}.md").is_file():
            errors.append(f"missing reference: {name}")
    for name in TEMPLATES:
        if not (folder / "assets/templates" / f"{name}.md").is_file():
            errors.append(f"missing template: {name}")
    for name in BRAND_TEMPLATES:
        if not (folder / "assets/templates/brand" / name).is_file():
            errors.append(f"missing brand template: {name}")
    for relative in SCRIPTS:
        if not (folder / relative).is_file():
            errors.append(f"missing script: {relative}")
    if not (folder / "LICENSE").is_file():
        errors.append("missing bundled LICENSE")
    if (folder / "styles/personal").exists():
        errors.append("bundled personal config: styles/personal must not exist in the package")
    # Templates link to future output siblings, so check only executable guidance.
    for path in [entry, *sorted((folder / "references").glob("*.md"))]:
        content = path.read_text(encoding="utf-8")
        for msg in markdown_errors(content) + local_link_errors(path, content, folder):
            errors.append(f"{path.relative_to(folder)}: {msg}")
    return errors


def private_config_findings(root):
    """Flag file names or contents under skills/ and examples/ that mention the private config."""
    findings = []
    for base in PRIVATE_SCAN:
        for path in sorted((Path(root) / base).rglob("*")):
            relative = path.relative_to(root)
            if SKIP_PARTS.intersection(relative.parts):
                continue
            if PRIVATE_MARKER in relative.as_posix().lower():
                findings.append(f"{relative.as_posix()}: private config marker in path")
            elif path.is_file() and PRIVATE_MARKER.encode() in path.read_bytes().lower():
                findings.append(f"{relative.as_posix()}: private config marker in content")
    return findings


def table_cells(line):
    row = line.strip()
    if not row.startswith("|"):
        return None
    row = row[1:-1] if row.endswith("|") and len(row) > 1 else row[1:]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", row)]


def section_lines(prose, heading):
    lines, inside = [], False
    for line in prose.splitlines():
        if re.match(r"^## ", line):
            inside = line[3:].strip().rstrip("#").strip() == heading
            continue
        if inside:
            lines.append(line)
    return lines


def evidence_errors(prose):
    errors, ids, rows, found = [], set(), 0, False
    lines = section_lines(prose, "事实核验")
    i = 0
    while i < len(lines):
        if table_cells(lines[i]) != EVIDENCE_HEADER:
            i += 1
            continue
        found = True
        delimiter = table_cells(lines[i + 1]) if i + 1 < len(lines) else None
        if not delimiter or not all(re.fullmatch(r":?-{3,}:?", c) for c in delimiter):
            errors.append("evidence table header lacks a delimiter row")
            i += 1
            continue
        i += 2
        while i < len(lines) and table_cells(lines[i]) is not None:
            rows += 1
            cells = table_cells(lines[i])
            label = f"evidence row {rows}"
            i += 1
            if len(cells) != len(EVIDENCE_HEADER):
                errors.append(f"{label}: expected 5 cells")
                continue
            claim_id, _, kind, _, check = cells
            if not claim_id or claim_id in ids:
                errors.append(f"{label}: empty or duplicate ID")
            ids.add(claim_id)
            if kind not in EVIDENCE_TYPES:
                errors.append(f"{label}: invalid 类型")
            if check not in EVIDENCE_CHECKS:
                errors.append(f"{label}: invalid 核验")
            elif kind == "建议" and check != "不适用":
                errors.append(f"{label}: 建议 must use 核验 不适用")
    if not found:
        errors.append("missing evidence table | ID | 结论 | 类型 | 依据 | 核验 | in ## 事实核验")
    elif not rows:
        errors.append("evidence table has no rows")
    return errors


def review_body_errors(body):
    errors = markdown_errors(body)
    prose, _ = prose_and_fences(body)
    headings = [h.strip().rstrip("#").strip() for h in re.findall(r"^## (.+)$", prose, re.M)]
    positions = []
    for name in REVIEW_SECTIONS:
        if name in headings:
            positions.append(headings.index(name))
        else:
            errors.append(f"missing section: ## {name}")
    if positions != sorted(positions):
        errors.append("review sections out of order; expected " + " > ".join(REVIEW_SECTIONS))
    if "事实核验" in headings:
        errors.extend(evidence_errors(prose))
    return errors


def metadata_errors(meta, keys, kind, expected_date):
    issues = [f"missing frontmatter key: {k}" for k in keys if k not in meta]
    issues += [f"unexpected frontmatter key: {k}" for k in meta if k not in keys]
    for key in ("title", "topic", "type", "mode", "language", "created", "updated"):
        if key in meta and (not isinstance(meta[key], str) or not meta[key].strip()):
            issues.append(f"invalid string field: {key}")
    slug = meta.get("topic")
    if not isinstance(slug, str) or not SLUG.fullmatch(slug) or slug in RESERVED:
        issues.append("invalid topic slug")
    if meta.get("type") != kind:
        issues.append(f'type must be "{kind}"')
    if meta.get("mode") not in MODES:
        issues.append("invalid mode")
    try:
        dates = [meta[k] for k in ("created", "updated")]
        if not all(isinstance(d, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) for d in dates):
            raise ValueError
        created, updated = map(date.fromisoformat, dates)
        if updated < created:
            issues.append("updated precedes created")
        if expected_date and updated.isoformat() != expected_date:
            issues.append("updated differs from supplied generation date")
    except (ValueError, TypeError, KeyError):
        issues.append("invalid ISO date strings")
    return issues


def validate_bundle(folder, boundary=None, expected_date=None):
    folder = Path(folder).resolve()
    boundary = Path(boundary).resolve() if boundary else folder
    errors, records = [], {}
    for filename, kind, keys in ((ARTICLE, "article", ARTICLE_KEYS), (REVIEW, "review", REVIEW_KEYS)):
        path = folder / filename
        if not path.is_file():
            errors.append(f"missing output: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        try:
            meta, body = frontmatter(text)
        except (ValueError, yaml.YAMLError, TypeError) as exc:
            errors.append(f"{filename}: invalid YAML ({type(exc).__name__})")
            continue
        records[filename] = meta
        issues = metadata_errors(meta, keys, kind, expected_date)
        if kind == "article":
            summary, tags = meta.get("summary"), meta.get("tags")
            if not isinstance(summary, str) or not summary.strip() or len(summary.strip()) > SUMMARY_LIMIT:
                issues.append(f"summary must be a non-empty string of at most {SUMMARY_LIMIT} characters")
            if (not isinstance(tags, list) or not 2 <= len(tags) <= 5
                    or any(not isinstance(t, str) or not t.strip() for t in tags)):
                issues.append("tags must be a list of 2-5 non-empty strings")
            issues += article_body_errors(body)
        else:
            if meta.get("status") not in {"draft", "ready"}:
                issues.append("status must be draft or ready")
            issues += review_body_errors(body)
        issues += local_link_errors(path, body, boundary)
        issues += sensitive_findings(text)
        errors.extend(f"{filename}: {msg}" for msg in issues)
    if len(records) == 2:
        article, review = records[ARTICLE], records[REVIEW]
        for key in ("topic", "mode", "language", "created"):
            if str(article.get(key)) != str(review.get(key)):
                errors.append(f"bundle metadata mismatch: {key}")
        if not isinstance(article.get("title"), str) or review.get("title") != article["title"] + REVIEW_SUFFIX:
            errors.append(f"review.md: title must be the article title followed by {REVIEW_SUFFIX}")
    return errors


def validate_repo(root):
    errors = validate_skill(root / "skills/ai-knowledge")
    required = ["README.md", "LICENSE", "CHANGELOG.md", "AGENTS.md",
                "docs/installation.md", "docs/usage-examples.md", "docs/architecture.md",
                "tests/README.md", "tests/RESULTS.md",
                *[DEMO_KIT.removesuffix("/visual") + "/" + name for name in
                  ("writing-profile.md", "writing-rules.md", "learning-log.md")]]
    for name in required:
        if not (root / name).is_file():
            errors.append(f"missing project file: {name}")
    errors.extend(private_config_findings(root))
    visual = visual_checker(root / "skills/ai-knowledge")
    errors.extend("demo kit: " + e for e in visual.validate_kit(root / DEMO_KIT))
    errors.extend("demo draft kit: " + e for e in visual.validate_kit(root / DEMO_DRAFT_KIT))
    covered = set()
    for topic in EXAMPLE_BUNDLES:
        folder = root / "examples" / topic
        errors.extend(f"examples/{topic}: {msg}" for msg in validate_bundle(folder, root))
        errors.extend(f"examples/{topic}: {msg}" for msg in visual.validate_bundle(folder))
        covered.update(p.resolve() for p in (folder / ARTICLE, folder / REVIEW))
    public_files = [root / n for n in ("README.md", "AGENTS.md", "CHANGELOG.md") if (root / n).exists()]
    for base in ("skills", "docs", "examples", "tests"):
        public_files.extend(p for p in (root / base).rglob("*")
                            if p.is_file() and p.suffix in {".md", ".py", ".mjs"}
                            and not SKIP_PARTS.intersection(p.parts))
    entries = [p for p in public_files if p.name == "SKILL.md"]
    if entries != [root / "skills/ai-knowledge/SKILL.md"]:
        errors.append("expected exactly one source Skill entrypoint")
    if (root / "SKILL.md").exists() or (root / ".agents/skills/ai-knowledge/SKILL.md").exists():
        errors.append("duplicate Skill entrypoint")
    for path in public_files:
        relative = path.relative_to(root)
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            errors.append(f"empty file: {relative}")
        # validate_bundle already reported these two files.
        if path.resolve() in covered:
            continue
        for msg in sensitive_findings(content):
            errors.append(f"{relative}: {msg}")
        if path.suffix != ".md" or "templates" in path.parts:
            continue
        in_bundle = relative.parts[0] == "examples" and (path.parent / ARTICLE).is_file()
        if path.name == ARTICLE:
            try:
                _, body = frontmatter(content)
                issues = article_body_errors(body)
            except (ValueError, yaml.YAMLError, TypeError) as exc:
                body, issues = content, [f"invalid YAML ({type(exc).__name__})"]
            issues += local_link_errors(path, body, root)
        else:
            # Platform adaptations next to an example article.md follow platform layouts, not the H1 rule.
            single_h1 = not (in_bundle and path.name != REVIEW)
            issues = markdown_errors(content, single_h1) + local_link_errors(path, content, root)
        errors.extend(f"{relative}: {msg}" for msg in issues)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, help="validate an isolated Skill folder")
    parser.add_argument("--bundle", type=Path,
                        help="validate one topic folder containing article.md and review.md")
    parser.add_argument("--root", type=Path, default=ROOT, help="allowed local citation root")
    parser.add_argument("--expected-date", help="optional generation date, YYYY-MM-DD")
    args = parser.parse_args()
    if args.skill and args.bundle:
        parser.error("choose --skill or --bundle")
    if args.skill:
        errors = validate_skill(args.skill)
    elif args.bundle:
        errors = validate_bundle(args.bundle, args.root, args.expected_date)
    else:
        errors = validate_repo(args.root.resolve())
    for error in errors:
        print(f"FAIL: {error}")
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} structural/security-pattern findings")
    print("Not checked: factual truth, full Markdown grammar, external URLs, teaching effectiveness.")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
