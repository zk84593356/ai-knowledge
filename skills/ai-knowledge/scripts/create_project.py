"""Set up a content workspace, its brand folders, and dated projects inside it.

Optional helper: everything here can be done by hand. It copies files from
templates/内容工作台/ and templates/品牌/, creates missing folders, and never
overwrites an existing file.

  python create_project.py init --workspace DIR [--no-remember] [--set-default]
  python create_project.py brand <brand-id> [--name 显示名] [--workspace DIR]
  python create_project.py new <topic-slug> [--workspace DIR] [--date YYYYMMDD]

Workspace lookup for brand/new: --workspace, then AI_KNOWLEDGE_WORKSPACE, then
"workspace" in ~/.ai-knowledge/settings.json. `init` records its workspace there
unless --no-remember; an existing different value is kept unless --set-default.
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
SEED = TEMPLATES / "内容工作台"
BRAND_TEMPLATE = TEMPLATES / "品牌"
ENV_VAR = "AI_KNOWLEDGE_WORKSPACE"
PROJECT_DIRS = ("_briefs", "_knowledge_base", "_协作文档", "公众号写作", "推文写作", "短视频逐字稿",
                "历史存档/公众号写作", "历史存档/推文写作", "历史存档/短视频逐字稿")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
            *(f"lpt{i}" for i in range(1, 10))}


def settings_file():
    return Path.home() / ".ai-knowledge" / "settings.json"


def read_settings():
    path = settings_file()
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        raise SystemExit(f"cannot read {path}: {type(exc).__name__}")
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must hold a JSON object")
    return value


def resolve_workspace(explicit=None):
    """Return (path, source). A configured location that is unusable is an error, not a fallback."""
    if explicit:
        return Path(explicit), "argument"
    env = os.environ.get(ENV_VAR, "").strip()
    if env:
        return Path(env), ENV_VAR
    value = read_settings().get("workspace")
    if isinstance(value, str) and value.strip():
        return Path(value).expanduser(), "settings.json"
    raise SystemExit("no workspace: pass --workspace, set AI_KNOWLEDGE_WORKSPACE, "
                     "or run `init --workspace DIR` once to record it in ~/.ai-knowledge/settings.json")


def copy_tree(source, target, created, skipped):
    for path in sorted(source.rglob("*")):
        dest = target / path.relative_to(source)
        if path.is_dir():
            if not dest.exists():
                dest.mkdir(parents=True)
                created.append(dest)
        elif dest.exists():
            skipped.append(dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            created.append(dest)


def ensure_layout(workspace):
    """Copy the bundled starter workspace and create the project folders; returns (created, skipped)."""
    created, skipped = [], []
    workspace.mkdir(parents=True, exist_ok=True)
    copy_tree(SEED, workspace, created, skipped)
    for name in PROJECT_DIRS:
        path = workspace / "我的项目" / name
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)
    brands = workspace / "品牌资产"
    if not brands.exists():
        brands.mkdir()
        created.append(brands)
    return created, skipped


def remember(workspace, replace):
    """Record the workspace in ~/.ai-knowledge/settings.json; returns a message."""
    path = settings_file()
    settings = read_settings()
    current = settings.get("workspace")
    if isinstance(current, str) and current.strip():
        if Path(current).expanduser().resolve() == workspace:
            return f"default workspace already set in {path}"
        if not replace:
            return (f"kept existing default workspace {current} in {path}; "
                    "rerun with --set-default to switch")
    settings["workspace"] = workspace.as_posix()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f"default workspace recorded in {path}"


def new_brand(workspace, brand_id, name):
    if not SLUG.fullmatch(brand_id) or len(brand_id) > 40 or brand_id in RESERVED:
        raise SystemExit("brand-id must be lowercase letters, digits and hyphens (max 40), e.g. blue-cat")
    root = workspace / "品牌资产" / brand_id
    if root.exists():
        raise SystemExit(f"品牌资产/{brand_id} already exists; nothing changed")
    created = []
    for sub in ("assets/canonical", "assets/scenes", "candidates"):
        (root / sub).mkdir(parents=True)
        created.append(root / sub)
    display = name or brand_id
    for path in sorted(BRAND_TEMPLATE.iterdir()):
        text = path.read_text(encoding="utf-8").replace("{{brand-id}}", brand_id).replace("{{显示名}}", display)
        (root / path.name).write_text(text, encoding="utf-8")
        created.append(root / path.name)
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
    projects = workspace / "我的项目"
    created = []
    for sub in PROJECT_DIRS:
        if not (projects / sub).exists():
            (projects / sub).mkdir(parents=True)
            created.append(projects / sub)
    name = free_name(f"{day}-{slug}", projects / "公众号写作", projects / "_briefs",
                     projects / "历史存档" / "公众号写作")
    folder = projects / "公众号写作" / name
    (folder / "assets").mkdir(parents=True)
    brief = projects / "_briefs" / f"{name}.md"
    shutil.copyfile(TEMPLATES / "文章" / "brief-template.md", brief)
    created += [folder, folder / "assets", brief]
    return name, created


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="copy the starter workspace and record it as the default")
    init.add_argument("--workspace")
    init.add_argument("--no-remember", action="store_true", help="do not write ~/.ai-knowledge/settings.json")
    init.add_argument("--set-default", action="store_true", help="replace a different recorded workspace")
    brand = sub.add_parser("brand", help="create 品牌资产/<brand-id>/ from the brand skeleton")
    brand.add_argument("brand_id")
    brand.add_argument("--name")
    brand.add_argument("--workspace")
    new = sub.add_parser("new", help="create a dated project folder and its brief")
    new.add_argument("slug")
    new.add_argument("--workspace")
    new.add_argument("--date", default=date.today().strftime("%Y%m%d"))
    args = parser.parse_args(argv)
    workspace, source = resolve_workspace(args.workspace)
    workspace = workspace.resolve()
    if workspace.exists() and not workspace.is_dir():
        raise SystemExit("workspace path exists and is not a directory")
    if args.command != "init" and not workspace.is_dir():
        raise SystemExit(f"workspace {workspace} does not exist; run init first")
    print(f"workspace ({source}): {workspace}")
    skipped = []
    if args.command == "init":
        created, skipped = ensure_layout(workspace)
    elif args.command == "brand":
        created = new_brand(workspace, args.brand_id, args.name)
    else:
        name, created = new_project(workspace, args.slug, args.date)
        print(f"project: {name}")
    for path in created:
        print(f"created: {path.relative_to(workspace).as_posix()}")
    for path in skipped:
        print(f"kept existing: {path.relative_to(workspace).as_posix()}")
    if not created:
        print("nothing to create")
    if args.command == "init" and not args.no_remember:
        print(remember(workspace, args.set_default))
    return 0


if __name__ == "__main__":
    sys.exit(main())
