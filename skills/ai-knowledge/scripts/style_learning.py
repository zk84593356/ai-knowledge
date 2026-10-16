"""Read-only style routing and textual reflection helpers (Python 3.10+).
These helpers never update rules, run Git, install packages, or call a network API.
Semantic approval, privacy review and actual source edits belong to the Agent workflow.

Personal config is never bundled. Lookup order: --profile <file>, then the directory in
AI_KNOWLEDGE_PERSONAL, then ~/.ai-knowledge/personal. A personal root holds
writing-rules.md, writing-profile.md and learning-log.md.
"""
import argparse
import copy
from difflib import SequenceMatcher
import hashlib
import json
import os
from pathlib import Path
import re
import sys

FIELDS = ("规则", "适用范围", "修改原因", "来源文章", "修改证据", "支持次数", "例外", "状态", "确认依据")
MAX_BYTES = 2 * 1024 * 1024
ENV_VAR = "AI_KNOWLEDGE_PERSONAL"


def read_text(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("document exceeds 2 MiB")
    return raw, raw.decode("utf-8-sig")


def parse_rules(text):
    """Only complete, unambiguous records are eligible; prose is not a rule."""
    # Ignore fenced examples, including headings inside them.
    lines, fence = [], None
    for line in text.splitlines():
        mark = re.match(r"^\s{0,3}(\x60{3,}|~{3,})(.*)$", line)
        if fence:
            if mark and mark[1][0] == fence[0] and len(mark[1]) >= fence[1] and not mark[2].strip():
                fence = None
            continue
        if mark:
            fence = (mark[1][0], len(mark[1]))
        else:
            lines.append(line)
    records, duplicates, seen = [], set(), set()
    for section in re.split(r"(?m)^## ", "\n".join(lines))[1:]:
        head, _, body = section.partition("\n")
        rule_id = head.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_-]*-\d{3,}", rule_id):
            continue
        if rule_id in seen:
            duplicates.add(rule_id)
        seen.add(rule_id)
        fields, valid = {}, True
        for key, value in re.findall(r"(?m)^- ([^：\n]+)：([^\n]*)$", body):
            if key in fields:
                valid = False
            fields[key] = value.strip()
        if (not valid or any(not fields.get(k) for k in FIELDS)
                or fields["状态"] not in {"候选", "已确认", "已停用"}
                or not re.fullmatch(r"\d+", fields["支持次数"])
                or "{{" in body):
            continue
        records.append({"id": rule_id, **fields})
    return [r for r in records if r["id"] not in duplicates]


def contained_file(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("resource escapes package")
    return target


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


def select_context(skill_root, public_only=False, profile=None):
    root = Path(skill_root).resolve()
    public = contained_file(root, "references/writing-craft.md")
    read_text(public)  # Missing public rules are an error, not a silent fallback.
    result = {"public": str(public), "route": "public-only", "source": None, "source_path": None,
              "profile": None, "rules": [], "reason": "personal style disabled",
              "semantic_review_required": True}
    if public_only:
        return result
    if profile is not None:
        path = Path(profile).resolve()
        result.update(source="explicit", source_path=str(path))
        try:
            _, content = read_text(path)
            if not content.strip():
                raise ValueError("empty explicit profile")
        except (OSError, ValueError):
            result["reason"] = "explicit profile unavailable; public rules only, do not substitute another config"
            return result
        result.update(route="explicit", profile=str(path), reason="user-selected profile replaces personal config")
        return result  # Explicit profiles can use legacy/freeform formats; Agent reviews them.
    source, base = personal_root()
    result["source"] = source
    if base is None:
        result["reason"] = (ENV_VAR + " is not an absolute path; public rules only" if source == "env"
                            else "home directory unavailable; public rules only")
        return result
    base = base.resolve()
    result["source_path"] = str(base)
    if not base.is_dir():
        # A broken env setting must not silently fall through to the home directory.
        result["reason"] = (ENV_VAR + " directory missing; public rules only, home not substituted"
                            if source == "env" else "no personal config directory; public rules only")
        return result
    try:
        _, text = read_text(base / "writing-rules.md")
        records = [r for r in parse_rules(text) if r["状态"] == "已确认"
                   and r["确认依据"] not in {"无", "未提供", "待确认", "统计次数"}]
        if not records:
            raise ValueError("no eligible rules")
        profile_path = base / "writing-profile.md"
        # Profile is optional; complete confirmed rules remain usable without it.
        profile_text = read_text(profile_path)[1] if profile_path.is_file() else ""
        result.update(route="personal", rules=records,
                      profile=str(profile_path) if profile_text.strip() else None,
                      reason="confirmed personal rules; Agent must check provenance and conflicts")
    except (OSError, ValueError):
        result["reason"] = "personal rules missing, empty, invalid, or without confirmed entries; public rules only"
    return result


def compare_versions(final, draft=None):
    final_raw, final_text = read_text(final)
    result = {"final_sha256": hashlib.sha256(final_raw).hexdigest(),
              "draft_sha256": None, "mode": "final-only", "changes": [],
              "purpose": "not inferred", "user_confirmation": "not inferred"}
    if draft is None:
        return result
    draft_raw, draft_text = read_text(draft)
    result.update(draft_sha256=hashlib.sha256(draft_raw).hexdigest(), mode="comparison")
    before, after = draft_text.splitlines(), final_text.splitlines()
    for tag, a, b, c, d in SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        result["changes"].append({"kind": tag, "before_lines": [a + 1, b] if a < b else None,
                                  "after_lines": [c + 1, d] if c < d else None,
                                  "before": before[a:b], "after": after[c:d]})
    return result


def add_evidence(rule, observation):
    """Pure merge preview; repeated files/versions do not inflate article support.
    Caller must verify identity, ownership and semantic equivalence before calling.
    No count or supplied observation can promote a rule to confirmed.
    """
    result = copy.deepcopy(rule)
    if result.get("status", "候选") not in {"候选", "已确认", "已停用"}:
        raise ValueError("invalid rule state")
    if any(not isinstance(observation.get(k), str) or not observation[k].strip()
           for k in ("article_id", "draft_sha256", "final_sha256", "evidence")):
        raise ValueError("actual paired evidence required")
    result.setdefault("status", "候选")
    result.setdefault("evidence", [])
    fingerprint = (observation["draft_sha256"], observation["final_sha256"])
    if not any((e["draft_sha256"], e["final_sha256"]) == fingerprint for e in result["evidence"]):
        result["evidence"].append({k: observation[k] for k in
                                   ("article_id", "draft_sha256", "final_sha256", "evidence")})
    result["support_count"] = len({e["article_id"] for e in result["evidence"]})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    context = sub.add_parser("context")
    context.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    context.add_argument("--public-only", action="store_true")
    context.add_argument("--profile", type=Path)
    compare = sub.add_parser("compare")
    compare.add_argument("--draft", type=Path)
    compare.add_argument("--final", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = (select_context(args.skill_root, args.public_only, args.profile) if args.command == "context"
                  else compare_versions(args.final, args.draft))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError):
        print("ERROR: unreadable/invalid input; check explicit files and package resources.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
