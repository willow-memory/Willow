r"""trello.py: A Trello board's JSON export: cards, checklists and comments, by list. Python 3.9+.

    python adapters/stdlib/trello/trello.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are a Trello board export, an object with
`lists` and `cards` (hidden folders and files skipped; other JSON skipped and
counted), and writes the board, then each open list with its open cards:

    board: Garden

    list: To do
    - Stake the tomatoes (due 2024-03-09) [urgent, veg]
      Use the long canes.
      checklist Tools: [x] canes, [ ] twine
      comment 2024-03-02 Ana: Borrow Ben's.

    list: Done
    - Order seed

A card keeps its name, due day, label names, description, checklists (each item
ticked or not) and the comments written on it, oldest first, with the day and
who wrote them. Archived lists and cards are left out. Members, attachments,
custom fields and the board's other settings are not copied.

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


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (
        isinstance(doc, dict)
        and isinstance(doc.get("lists"), list)
        and isinstance(doc.get("cards"), list)
    ):
        return None
    checklists = (
        {
            c["id"]: c
            for c in doc.get("checklists", [])
            if isinstance(c, dict) and isinstance(c.get("id"), str)
        }
        if isinstance(doc.get("checklists"), list)
        else {}
    )
    comments: dict[str, list[tuple[str, str, str]]] = {}
    for a in doc.get("actions", []) if isinstance(doc.get("actions"), list) else []:
        data_ = (
            a.get("data")
            if isinstance(a, dict) and isinstance(a.get("data"), dict)
            else {}
        )
        card = data_.get("card") if isinstance(data_.get("card"), dict) else {}
        if (
            isinstance(a, dict)
            and a.get("type") == "commentCard"
            and text(data_.get("text"))
            and isinstance(card.get("id"), str)
        ):
            who = (
                a.get("memberCreator")
                if isinstance(a.get("memberCreator"), dict)
                else {}
            )
            comments.setdefault(card["id"], []).append(
                (
                    day(a.get("date")),
                    text(who.get("fullName")) or "someone",
                    text(data_["text"]),
                )
            )
    out = [f"board: {text(doc.get('name')) or '(unnamed board)'}"]
    shown = 0
    for lst in doc["lists"]:
        if not isinstance(lst, dict) or lst.get("closed") is True:
            continue
        cards = [
            c
            for c in doc["cards"]
            if isinstance(c, dict)
            and c.get("idList") == lst.get("id")
            and c.get("closed") is not True
            and text(c.get("name"))
        ]
        block = ["", f"list: {text(lst.get('name')) or '(unnamed list)'}"]
        for c in cards:
            extras = [f"due {day(c.get('due'))}"] if day(c.get("due")) else []
            labels = (
                [
                    text(lab.get("name"))
                    for lab in c.get("labels", [])
                    if isinstance(lab, dict) and text(lab.get("name"))
                ]
                if isinstance(c.get("labels"), list)
                else []
            )
            head = (
                f"- {text(c['name'])}"
                + (f" ({', '.join(extras)})" if extras else "")
                + (f" [{', '.join(labels)}]" if labels else "")
            )
            block.append(head)
            if text(c.get("desc")):
                block.append("  " + text(c["desc"]))
            for cid in (
                c.get("idChecklists", [])
                if isinstance(c.get("idChecklists"), list)
                else []
            ):
                cl = checklists.get(cid)
                items = (
                    [
                        i
                        for i in cl.get("checkItems", [])
                        if isinstance(i, dict) and text(i.get("name"))
                    ]
                    if cl and isinstance(cl.get("checkItems"), list)
                    else []
                )
                if cl and items:
                    ticks = ", ".join(
                        f"[{'x' if i.get('state') == 'complete' else ' '}] {text(i['name'])}"
                        for i in items
                    )
                    block.append(
                        f"  checklist {text(cl.get('name')) or '(unnamed)'}: {ticks}"
                    )
            for d, who, said in sorted(
                comments.get(c.get("id"), []), key=lambda t: t[0]
            ):
                block.append(
                    f"  comment {d} {who}: {said}".replace("comment  ", "comment ")
                )
        if cards:
            out += block
            shown += len(cards)
    return "\n".join(out) + "\n" if shown else None


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: trello.py mirror --from FOLDER --to MIRROR"


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
