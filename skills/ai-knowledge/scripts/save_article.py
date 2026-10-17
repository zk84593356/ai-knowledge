"""Archive a published project: move its folders under 我的项目/历史存档/.

Run only after the author says the article has been published. Moves, never
edits or overwrites; stops if any target already exists.

  python save_article.py <YYYYMMDD-topic-slug> [--workspace DIR] [--dry-run]
"""
import argparse
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_project import resolve_workspace  # noqa: E402

KINDS = ("公众号写作", "推文写作", "短视频逐字稿")
NAME = re.compile(r"\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def plan(workspace, name):
    if not NAME.fullmatch(name):
        raise SystemExit("project name must look like YYYYMMDD-topic-slug")
    projects = workspace / "我的项目"
    main_dir = projects / "公众号写作" / name
    if not (main_dir / "review.md").is_file():
        raise SystemExit(f"not a project with review.md: 公众号写作/{name}")
    moves = []
    for kind in KINDS:
        source = projects / kind / name
        if source.exists():
            target = projects / "历史存档" / kind / name
            if target.exists():
                raise SystemExit(f"archive target already exists: 历史存档/{kind}/{name}")
            moves.append((source, target))
    return moves


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", help="project folder name, e.g. 20261017-oidc-login")
    parser.add_argument("--workspace")
    parser.add_argument("--dry-run", action="store_true", help="print the moves without doing them")
    args = parser.parse_args(argv)
    workspace, source = resolve_workspace(args.workspace)
    workspace = workspace.resolve()
    print(f"workspace ({source}): {workspace}")
    moves = plan(workspace, args.name)
    for src, dst in moves:
        print(f"{'would move' if args.dry_run else 'move'}: "
              f"{src.relative_to(workspace).as_posix()} -> {dst.relative_to(workspace).as_posix()}")
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
