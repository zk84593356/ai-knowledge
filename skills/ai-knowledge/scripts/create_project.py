"""Create the content workspace layout and one dated project inside it.

Optional helper: everything here can be done by hand. It only creates missing
folders and copies blank templates; it never overwrites an existing file.

  python create_project.py init [--workspace DIR]
  python create_project.py new <topic-slug> [--workspace DIR] [--date YYYYMMDD]
"""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import shutil
import sys

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "templates"
ROOT_DIRS = ("风格参考", "写作技巧", "规范指南")
PROJECT_DIRS = ("_briefs", "_knowledge_base", "_协作文档", "公众号写作", "推文写作", "短视频逐字稿",
                "历史存档/公众号写作", "历史存档/推文写作", "历史存档/短视频逐字稿")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
            *(f"lpt{i}" for i in range(1, 10))}


def personal_dir():
    env = os.environ.get("AI_KNOWLEDGE_PERSONAL")
    return Path(env) if env else Path.home() / ".ai-knowledge" / "personal"


def resolve_workspace(explicit=None):
    """Return (path, source). An explicit or configured location that is unusable is an error, not a fallback."""
    if explicit:
        return Path(explicit), "argument"
    env = os.environ.get("AI_KNOWLEDGE_WORKSPACE")
    if env:
        return Path(env), "AI_KNOWLEDGE_WORKSPACE"
    settings = personal_dir() / "settings.json"
    if settings.is_file():
        try:
            value = json.loads(settings.read_text(encoding="utf-8")).get("workspace")
        except (ValueError, AttributeError) as exc:
            raise SystemExit(f"cannot read {settings.name}: {type(exc).__name__}")
        if isinstance(value, str) and value.strip():
            return Path(value).expanduser(), "settings.json"
    raise SystemExit("no workspace: pass --workspace, set AI_KNOWLEDGE_WORKSPACE, "
                     "or add \"workspace\" to settings.json in the personal config directory")


def ensure_layout(workspace):
    created = []
    workspace.mkdir(parents=True, exist_ok=True)
    for name in ROOT_DIRS:
        path = workspace / name
        if not path.exists():
            path.mkdir()
            created.append(path)
    for name in PROJECT_DIRS:
        path = workspace / "我的项目" / name
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)
    persona = workspace / "用户人设.md"
    if not persona.exists():
        shutil.copyfile(TEMPLATES / "用户人设-template.md", persona)
        created.append(persona)
    return created


def free_name(base, *parents):
    """First name not used under any parent: base, base-02, base-03 ..."""
    name, n = base, 1
    while any((p / name).exists() or (p / f"{name}.md").exists() for p in parents):
        n += 1
        name = f"{base}-{n:02d}"
    return name


def new_project(workspace, slug, day):
    if not SLUG.fullmatch(slug) or slug in RESERVED:
        raise SystemExit("topic-slug must be short lowercase words joined by hyphens")
    if not re.fullmatch(r"\d{8}", day):
        raise SystemExit("--date must be YYYYMMDD")
    created = ensure_layout(workspace)
    projects = workspace / "我的项目"
    name = free_name(f"{day}-{slug}", projects / "公众号写作", projects / "_briefs",
                     projects / "历史存档" / "公众号写作")
    folder = projects / "公众号写作" / name
    (folder / "assets").mkdir(parents=True)
    brief = projects / "_briefs" / f"{name}.md"
    shutil.copyfile(TEMPLATES / "brief-template.md", brief)
    created += [folder, folder / "assets", brief]
    return name, created


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create the workspace folders and a blank 用户人设.md")
    init.add_argument("--workspace")
    new = sub.add_parser("new", help="create a dated project folder and its brief")
    new.add_argument("slug")
    new.add_argument("--workspace")
    new.add_argument("--date", default=date.today().strftime("%Y%m%d"))
    args = parser.parse_args(argv)
    workspace, source = resolve_workspace(args.workspace)
    workspace = workspace.resolve()
    if workspace.exists() and not workspace.is_dir():
        raise SystemExit("workspace path exists and is not a directory")
    print(f"workspace ({source}): {workspace}")
    if args.command == "init":
        created = ensure_layout(workspace)
    else:
        name, created = new_project(workspace, args.slug, args.date)
        print(f"project: {name}")
    for path in created:
        print(f"created: {path.relative_to(workspace).as_posix()}")
    if not created:
        print("nothing to create")
    return 0


if __name__ == "__main__":
    sys.exit(main())
