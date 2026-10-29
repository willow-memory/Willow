r"""gh_json.py: What gh prints with --json, saved to a file: issues, pull requests and runs. Python 3.9+.

    python adapters/stdlib/gh-json/gh_json.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are the output of `gh issue list --json ...`,
`gh pr list --json ...` or `gh run list --json ...` (a list of objects; hidden
folders and files skipped; other JSON skipped and counted) and writes each item,
oldest first, as a dated passage:

    issue #12 (open) 2024-03-02 ana: Tomatoes want more sun [bug, garden]
      The bed by the fence is shaded after noon.
      comment 2024-03-03 ben: Move them to bed 2.
    pull request #14 (merged) 2024-03-04 ben: Move tomatoes to bed 2 (branch bed-2)
    run 1234 (failure) 2024-03-04 ci on main: Move tomatoes to bed 2

An issue or pull request is a list item with a `number` and a `title`; it is a
pull request when it has a `headRefName`, `mergedAt` or `isDraft`. A pull
request that has a merge time is "merged"; otherwise its state is the state gh
gave, in lower case. Body and comments are kept as written, whitespace
collapsed. A run has a `databaseId` and a workflow or conclusion. Fields gh
was not asked for are simply absent; a field it was asked for is used, and the
others are never invented.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def text(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def day(v: object) -> str:
    return v[:10] if isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}", v) else ""


def login(v: object) -> str:
    return text(v.get("login")) if isinstance(v, dict) else ""


def item(i: dict) -> str:
    number, title = i["number"], text(i["title"])
    is_pr = any(k in i for k in ("headRefName", "mergedAt", "isDraft"))
    state = (
        "merged"
        if is_pr and i.get("mergedAt")
        else text(i.get("state")).lower() or "unknown"
    )
    labels = (
        [
            text(lab.get("name"))
            for lab in i.get("labels", [])
            if isinstance(lab, dict) and text(lab.get("name"))
        ]
        if isinstance(i.get("labels"), list)
        else []
    )
    who = login(i.get("author"))
    head = f"{'pull request' if is_pr else 'issue'} #{number} ({state})"
    head += "".join(
        " " + x for x in (day(i.get("createdAt")), f"{who}:" if who else "") if x
    )
    head += " " + title + (f" [{', '.join(labels)}]" if labels else "")
    if is_pr and text(i.get("headRefName")):
        head += f" (branch {text(i['headRefName'])})"
    lines = [head]
    if text(i.get("body")):
        lines.append("  " + text(i["body"]))
    for c in i.get("comments", []) if isinstance(i.get("comments"), list) else []:
        if isinstance(c, dict) and text(c.get("body")):
            lines.append(
                "  comment "
                + " ".join(
                    x
                    for x in (
                        day(c.get("createdAt")),
                        f"{login(c.get('author'))}:" if login(c.get("author")) else "",
                    )
                    if x
                )
                + " "
                + text(c["body"])
            )
    return "\n".join(lines)


def run(r: dict) -> str:
    what = text(r.get("workflowName")) or text(r.get("name"))
    result = text(r.get("conclusion")) or text(r.get("status")) or "unknown"
    where = f" on {text(r['headBranch'])}" if text(r.get("headBranch")) else ""
    line = f"run {r['databaseId']} ({result}) " + " ".join(
        x for x in (day(r.get("createdAt")), (what + where).strip()) if x
    )
    line = line.rstrip()
    return line + (
        f": {text(r.get('displayTitle'))}" if text(r.get("displayTitle")) else ""
    )


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not isinstance(doc, list):
        return None
    rows = []
    for i in doc:
        if not isinstance(i, dict):
            continue
        if (
            "number" in i
            and isinstance(i.get("title"), str)
            and isinstance(i["number"], int)
            and not isinstance(i["number"], bool)
        ):
            rows.append((day(i.get("createdAt")), item(i)))
        elif "databaseId" in i and (
            "conclusion" in i or "workflowName" in i or "status" in i
        ):
            rows.append((day(i.get("createdAt")), run(i)))
    return (
        "\n".join(t for _d, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: gh_json.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
