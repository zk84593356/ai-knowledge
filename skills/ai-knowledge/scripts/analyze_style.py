"""Local UTF-8 Markdown/ZIP statistics. Python 3.10+, standard library only.
No extraction, network, source edits, or automatic inference of personal identity.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import statistics
import sys
import zipfile

MAX_FILES = 100
MAX_BYTES = 2 * 1024 * 1024
MAX_TOTAL = 20 * 1024 * 1024
DEFAULT_TERMS = ["其实", "比如", "比方说", "也就是说", "但是", "不过", "所以", "因此",
                 "接下来", "回到", "我觉得", "可能", "通常", "必须", "你", "我们"]


def safe_member(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or "\\" in name or ":" in name
            or ".." in path.parts or "\x00" in name):
        raise ValueError("unsafe ZIP member path")


def read_sources(inputs):
    """Bounded reads with relative labels; reject the corpus as a whole on error."""
    docs, total = [], 0

    def add(label, raw):
        nonlocal total
        total += len(raw)
        if len(raw) > MAX_BYTES or total > MAX_TOTAL or len(docs) >= MAX_FILES:
            raise ValueError("corpus limit exceeded")
        text = raw.decode("utf-8-sig", errors="strict")
        if "\x00" in text:
            raise ValueError("NUL in Markdown")
        docs.append((label, raw, text))

    def read_file(path):
        with path.open("rb") as stream:
            return stream.read(MAX_BYTES + 1)

    for number, source in enumerate(inputs, 1):
        path = Path(source)
        if path.is_symlink():
            raise ValueError("symbolic source link")
        if path.is_dir():
            root = path.resolve()
            for item in sorted(path.rglob("*")):
                relative = item.relative_to(path)
                if any(part.startswith(".") for part in relative.parts):
                    continue
                if item.is_symlink() or not item.resolve().is_relative_to(root):
                    raise ValueError("escaping or symbolic directory entry")
                if item.is_file() and item.suffix.lower() == ".md":
                    add(f"input-{number}/{relative.as_posix()}", read_file(item))
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                if len(entries) > 10000:
                    raise ValueError("ZIP inventory limit")
                seen = set()
                for info in sorted(entries, key=lambda i: i.filename):
                    safe_member(info.orig_filename)  # Windows ZipInfo normalizes filename on read.
                    safe_member(info.filename)
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise ValueError("ZIP symbolic link")
                    if info.is_dir() or PurePosixPath(info.filename).suffix.lower() != ".md":
                        continue
                    if info.filename.casefold() in seen:
                        raise ValueError("duplicate Markdown member")
                    seen.add(info.filename.casefold())
                    if info.file_size > MAX_BYTES or info.flag_bits & 1:
                        raise ValueError("oversized or encrypted Markdown")
                    with archive.open(info) as stream:
                        add(f"input-{number}/{info.filename}", stream.read(MAX_BYTES + 1))
        elif path.is_file() and path.suffix.lower() == ".md":
            add(f"input-{number}/{path.name}", read_file(path))
        else:
            raise ValueError("input must be Markdown, directory, or ZIP")
    if not docs:
        raise ValueError("no Markdown documents")
    return docs


def narrative_paragraphs(text):
    """Conservative Markdown heuristic, not a complete Markdown parser."""
    lines = text.splitlines()
    excluded = Counter()
    paragraphs, pending, warnings = [], [], []
    fence, comment, front = None, False, bool(lines and lines[0].strip() == "---")

    def flush():
        if pending:
            paragraphs.append({"start_line": pending[0][0], "end_line": pending[-1][0],
                               "text": " ".join(value for _, value in pending)})
            pending.clear()

    for index, line in enumerate(lines, 1):
        if front:
            excluded["frontmatter"] += 1
            if index > 1 and line.strip() == "---":
                front = False
            continue
        mark = re.match(r"^\s{0,3}(" + r"\x60{3,}|~{3,})(.*)$", line)
        if fence:
            excluded["fence"] += 1
            if mark and mark[1][0] == fence[0] and len(mark[1]) >= fence[1] and not mark[2].strip():
                fence = None
            continue
        if mark:
            flush()
            fence = (mark[1][0], len(mark[1]))
            excluded["fence"] += 1
            continue
        if comment or "<!--" in line:
            flush()
            excluded["comment"] += 1
            comment = "-->" not in line
            continue
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        category = None
        if re.match(r"^\s{0,3}>", line):
            category = "blockquote"
        elif re.match(r"^\s{0,3}#{1,6}\s", line) or re.fullmatch(r"\s*(?:[-*_]\s*){3,}", line):
            category = "heading_or_rule"
        elif re.match(r"^\s*(?:!\[.*\]\(|\[.*\]:\s*\S|<[^>]+>)", line):
            category = "image_reference_or_html"
        elif "|" in stripped and (stripped.startswith("|") or re.match(r"^:?-{3,}", stripped)):
            category = "table"
        elif line.startswith("    ") or line.startswith("\t"):
            category = "indented_block"
        if category:
            flush()
            excluded[category] += 1
            continue
        value = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", line)
        value = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", value)
        value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
        value = re.sub(r"\x60+[^\x60]*\x60+", "", value)
        value = re.sub(r"https?://\S+", "", value)
        value = re.sub(r"[*_~]", "", value).strip()
        if value:
            pending.append((index, value))
    flush()
    if front or fence or comment:
        warnings.append("unclosed frontmatter, fenced block, or HTML comment; inspect source")
    return paragraphs, dict(sorted(excluded.items())), warnings


def char_count(text):
    return sum(c.isalnum() for c in text)


def distribution(values):
    return {"count": len(values), "mean": round(statistics.mean(values), 2) if values else None,
            "median": statistics.median(values) if values else None, "max": max(values) if values else None}


def analyze_document(label, raw, text, terms, excerpts=False):
    paragraphs, excluded, warnings = narrative_paragraphs(text)
    body = "\n".join(p["text"] for p in paragraphs)
    sentences = [s for p in paragraphs for s in re.split(r"[。！？!?]+|\.(?=\s|$)", p["text"]) if char_count(s)]
    starts = [p["text"] for p in paragraphs]
    counts = {term: {"occurrences": body.count(term),
                     "paragraphs": sum(term in s for s in starts),
                     "paragraph_starts": sum(s.startswith(term) for s in starts)} for term in terms}
    candidates = Counter()
    for span in re.findall(r"[\u4e00-\u9fff]+", body):
        candidates.update(span[i:i + 2] for i in range(len(span) - 1))
    words = Counter(w.lower() for w in re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", body))
    samples = []
    positions = sorted({0, len(paragraphs) // 2, len(paragraphs) - 1}) if paragraphs else []
    for index in positions:
        paragraph = paragraphs[index]
        item = {"paragraph": index + 1, "start_line": paragraph["start_line"], "end_line": paragraph["end_line"]}
        if excerpts:
            item["excerpt"] = paragraph["text"][:240]
            item["excerpt_truncated"] = len(paragraph["text"]) > 240
        samples.append(item)
    return {"source": label, "sha256": hashlib.sha256(raw).hexdigest(),
            "narrative_sha256": hashlib.sha256(re.sub(r"\s+", "", body).encode("utf-8")).hexdigest(),
            "bytes": len(raw), "lines": len(text.splitlines()), "decoded_full_text": True,
            "semantic_review": "required", "narrative_characters": char_count(body),
            "sentence_units": distribution([char_count(s) for s in sentences]),
            "paragraphs": distribution([char_count(p["text"]) for p in paragraphs]),
            "excluded_lines": excluded, "term_counts": counts,
            "chinese_bigram_candidates": candidates.most_common(15), "english_word_candidates": words.most_common(15),
            "systematic_samples": samples, "warnings": warnings}


def analyze(inputs, terms=None, excerpts=False, provenance="external"):
    terms = DEFAULT_TERMS if terms is None else terms
    documents = [analyze_document(*doc, terms, excerpts) for doc in read_sources(inputs)]
    groups = {}
    for doc in documents:
        if doc["narrative_characters"]:
            groups.setdefault(doc["narrative_sha256"], []).append(doc["source"])
    warnings = ["Heuristics only: full reading, authorship, quotations and rule evidence need Agent review."]
    if len(groups) < 2:
        warnings.append("Fewer than two distinct narrative texts: tentative observations only.")
    return {"schema_version": 1, "provenance": provenance, "method": {
        "character_unit": "Unicode alphanumeric characters; excludes punctuation/whitespace, not word count",
        "sentence_unit": "terminal punctuation splits; trailing fragments count as units, commas do not",
        "paragraph_unit": "narrative lines separated by blanks or excluded blocks",
        "excluded": "frontmatter, fences, blockquotes, headings, images, tables, indented blocks, HTML comments",
        "terms": "explicit substring inventory, not Chinese word segmentation; overlapping terms independent",
        "candidates": "Chinese bigrams and English words are hints, not inferred habits",
        "sampling": "first, middle, last narrative paragraphs; original 1-based line locators",
        "limitations": "heuristic Markdown; inline quotes, lazy blockquotes, captions and prompts need manual attribution",
    }, "document_count": len(documents), "distinct_narrative_count": len(groups),
        "duplicate_groups": [g for g in groups.values() if len(g) > 1], "documents": documents, "warnings": warnings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="explicit Markdown files, directories or ZIPs")
    parser.add_argument("--output", type=Path, help="new JSON path; never overwrite")
    parser.add_argument("--include-excerpts", action="store_true", help="include private 240-character samples")
    parser.add_argument("--provenance", choices=["external", "user", "simulated"], default="external")
    parser.add_argument("--terms-file", type=Path, help="UTF-8 JSON array of 1-100 literal terms")
    args = parser.parse_args(argv)
    try:
        terms = None
        if args.terms_file:
            terms = json.loads(args.terms_file.read_text(encoding="utf-8-sig"))
            if (not isinstance(terms, list) or not 1 <= len(terms) <= 100
                    or any(not isinstance(t, str) or not t.strip() or len(t) > 40 for t in terms)
                    or len(set(terms)) != len(terms)):
                raise ValueError("invalid term inventory")
        report = analyze(args.inputs, terms, args.include_excerpts, args.provenance)
        data = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(data)
            print("PASS: statistics written; semantic analysis still requires full reading.")
        else:
            print(data, end="")
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, NotImplementedError):
        print("ERROR: rejected input/output; check UTF-8, ZIP paths, limits, terms and output nonexistence.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
