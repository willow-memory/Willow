"""boxes_here.py: the boxes already in a folder, how much waits on each, and a list kept of the ones you choose. Python 3.9+.

    python adapters/stdlib/boxes-here/boxes_here.py --in FOLDER [--deep N] [--json]
    python adapters/stdlib/boxes-here/boxes_here.py --kept FILE [--json]
    python adapters/stdlib/boxes-here/boxes_here.py keep --to FILE BOX [BOX ...]
    python adapters/stdlib/boxes-here/boxes_here.py drop --to FILE BOX [BOX ...]

    boxes-here: populated, 2 boxes under /home/you/papers; 4 suggestions wait on you
    ## boxes already here
      taxes/box        30 rows: 12 asked, 9 approved, 3 waiting
      letters          8 rows: 2 asked, 0 approved, 1 waiting
    ## not looked in
      scans/2019/q1    it is 3 folders down, and holds folders of its own

A box is a folder that holds a kernel.json: a record was started there.
Before one is made over a folder, this says whether one is there already,
so it is opened and not made twice. --in looks through FOLDER and the
folders under it, --deep folders down (3, unless told). It looks for the
one file and counts the record's rows; it opens nothing else of yours. A
folder whose name starts with a dot, a link to a folder, and the inside of
a box are not looked in. Where it stopped short is said, folder by folder,
so "none here" is never said of a place it didn't look.

keep adds boxes to a list, FILE, by where they are: nothing is copied or
moved, and a box stays where you keep it. drop takes them off. --kept
reads the list back the way --in reads a folder, and says which are gone.

Keeping a box says where it is, and nothing about who may read it: this
sends a box nowhere, and what may leave the machine is not its to decide.

It writes FILE, under --to, and nothing else: no row on a record, and your
key is never read. FILE's folder must be there already. It prints a report
(ci/README.md, "The report contract"); --json gives the same as one object.
Exit codes, the kernel's: 0 said, or done (no box is an empty report); 42 a
suggestion waits on you in one, a record's chain is broken, or a kept box
is gone; 2 refused.
"""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    "usage: boxes_here.py --in FOLDER [--deep N] [--json]\n"
    "       boxes_here.py --kept FILE [--json]\n"
    "       boxes_here.py keep|drop --to FILE BOX [BOX ...]"
)
NAME = "boxes-here"
STDLIB = Path(__file__).resolve().parents[1]
#: how many folders down --in looks, unless told
DEEP = 3
#: the most a list is read at
MAX_LIST = 1 << 20


def projects_addon():
    """The projects add-on's module, from its source beside this one."""
    path = STDLIB / "projects" / "projects.py"
    mod = types.ModuleType("boxes_here_projects")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def boxes_said(n: int) -> str:
    return f"{n} box{'es' * (n != 1)}"


def is_box(folder: Path) -> bool:
    return (folder / "kernel.json").is_file()


def find(folder: Path, deep: int = DEEP) -> tuple[list[Path], list[tuple[Path, str]]]:
    """(the boxes in `folder` and up to `deep` folders under it, the folders
    not looked in and why). A box's own inside is not looked in, nor a
    folder named with a dot, nor a link."""
    boxes: list[Path] = []
    skipped: list[tuple[Path, str]] = []
    level = [folder]
    for depth in range(deep + 1):
        below: list[Path] = []
        for d in level:
            if is_box(d):
                boxes.append(d)
                continue
            try:
                with os.scandir(d) as it:
                    kids = sorted(
                        Path(e.path)
                        for e in it
                        if not e.name.startswith(".")
                        and e.is_dir(follow_symlinks=False)
                    )
            except OSError as e:
                skipped.append((d, f"it couldn't be opened: {type(e).__name__}"))
                continue
            if depth == deep and kids:
                n = f"{deep} folder{'' if deep == 1 else 's'} down"
                skipped.append((d, f"it is {n}, and holds folders of its own"))
            below += kids
        level = below
    return sorted(boxes), sorted(skipped)


def waits(box: Path, pr) -> tuple[str, int, bool]:
    """(what to say of a box's record, the suggestions waiting, it is broken)."""
    try:
        t = pr.tally(box)
    except (OSError, ValueError, KeyError, TypeError) as e:
        return f"its record couldn't be read: {type(e).__name__}", 0, True
    if "broken" in t:
        return f"its chain is broken: {t['broken']}", 0, True
    said = (
        f"{pr.count(t['rows'], 'row')}: {t['asked']} asked, "
        f"{t['approved']} approved, {t['waiting']} waiting"
    )
    return said, t["waiting"], False


def kept(file: Path) -> tuple[list[dict] | None, str]:
    """(the list in `file`, "") or (None, why it isn't one). A file that
    isn't there yet is an empty list."""
    if not file.exists():
        return [], ""
    try:
        if file.stat().st_size > MAX_LIST:
            return None, "it is too long to be a list of boxes"
        doc = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, f"it could not be read: {type(e).__name__}"
    ok = isinstance(doc, list) and all(
        isinstance(b, dict) and isinstance(b.get("box"), str) and b["box"] for b in doc
    )
    if not ok:
        return None, 'it is not a list of {"box": where it is}'
    return doc, ""


def change(file: Path, boxes: list[Path], drop: bool) -> tuple[list[dict], int]:
    """(the list after `boxes` are added, or dropped; how many it changed).
    A box is named by where it is, in full."""
    doc, why = kept(file)
    if doc is None:
        raise ValueError(why)
    names = [str(b.resolve()) for b in boxes]
    before = len(doc)
    if drop:
        doc = [b for b in doc if b["box"] not in names]
        return doc, before - len(doc)
    have = {b["box"] for b in doc}
    doc += [{"box": n} for n in dict.fromkeys(names) if n not in have]
    return sorted(doc, key=lambda b: b["box"]), len(doc) - before


def report(state: str, said: str, groups: list[tuple[str, list[tuple[str, str]]]]):
    return {
        "addon": NAME,
        "state": state,
        "said": said,
        "groups": [
            {"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
            for g, rows in groups
            if rows
        ],
    }


def show(doc: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(doc, ensure_ascii=False))
        return
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    print(f"{NAME}: {doc['state']}, {doc['said']}")
    for g in doc["groups"]:
        print(f"## {g['name']}")
        for r in g["rows"]:
            print(f"  {r['where']:<{w}}  {r['what']}".rstrip())


def looked(folder: Path, deep: int) -> tuple[dict, bool]:
    """(the report of the boxes in a folder, whether something waits or is
    broken)."""
    pr = projects_addon()
    boxes, skipped = find(folder, deep)
    rows, waiting, flagged = [], 0, False
    for b in boxes:
        said, n, broken = waits(b, pr)
        rows.append((str(b.relative_to(folder)), said))
        waiting, flagged = waiting + n, flagged or broken
    short = [(str(d.relative_to(folder)), why) for d, why in skipped]
    down = f"{deep} folder{'' if deep == 1 else 's'}"
    if boxes:
        said = f"{boxes_said(len(boxes))} under {folder}"
        if waiting:
            said += f"; {pr.count(waiting, 'suggestion')} wait{'s' * (waiting == 1)} on you"  # fmt: skip
    else:
        said = f"no box in {folder} or {down} under it"
    if short:
        said += f"; {pr.count(len(short), 'folder')} not looked in"
    doc = report(
        "populated" if boxes else "empty",
        said,
        [("boxes already here", rows), ("not looked in", short)],
    )
    return doc, bool(waiting) or flagged


def listed(file: Path) -> tuple[dict | None, str, bool]:
    """(the report of a kept list, why it isn't a list, whether something
    waits, is broken or is gone)."""
    doc, why = kept(file)
    if doc is None:
        return None, why, False
    pr = projects_addon()
    rows, waiting, flagged = [], 0, False
    for b in doc:
        box = Path(b["box"])
        if not is_box(box):
            rows.append((b["box"], "no box is there now"))
            flagged = True
            continue
        said, n, broken = waits(box, pr)
        rows.append((b["box"], said))
        waiting, flagged = waiting + n, flagged or broken
    if doc:
        said = f"{boxes_said(len(doc))} kept in {file}"
        if waiting:
            said += f"; {pr.count(waiting, 'suggestion')} wait{'s' * (waiting == 1)} on you"  # fmt: skip
    else:
        said = f"no box is kept in {file}"
    out = report(
        "populated" if doc else "empty",
        said,
        [("kept boxes", rows)],
    )
    return out, "", bool(waiting) or flagged


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if argv[:1] in (["keep"], ["drop"]):
        if len(argv) < 4 or argv[1] != "--to" or not argv[2] or as_json:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
        file, boxes = Path(argv[2]).expanduser(), [Path(a).expanduser() for a in argv[3:]]  # fmt: skip
        if not file.parent.is_dir():
            print(f"refused: {file.parent} isn't a folder that's there; make it first", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        if file.is_dir():
            print(f"refused: {file} is a folder, not a list", file=sys.stderr)
            return kernel.REFUSED
        if argv[0] == "keep":
            for b in boxes:
                if not is_box(b):
                    print(f"refused: {b} is not a box: it holds no kernel.json", file=sys.stderr)  # fmt: skip
                    return kernel.REFUSED
        try:
            doc, n = change(file, boxes, argv[0] == "drop")
        except ValueError as e:
            print(f"refused: {file}: {e}", file=sys.stderr)
            return kernel.REFUSED
        try:
            file.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")  # fmt: skip
        except OSError as e:
            print(f"refused: {file} could not be written: {type(e).__name__}", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        did = "kept" if argv[0] == "keep" else "dropped"
        print(f"{did} {n} of {len(boxes)}; {len(doc)} in {file}")
        return kernel.ALIVE
    opts: dict[str, str] = {}
    it = iter(argv)
    for a in it:
        if a in ("--in", "--deep", "--kept") and a not in opts:
            opts[a] = next(it, "")
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
    if "--kept" in opts:
        if len(opts) != 1 or not opts["--kept"]:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
        doc, why, flagged = listed(Path(opts["--kept"]).expanduser())
        if doc is None:
            print(f"refused: {opts['--kept']}: {why}", file=sys.stderr)
            return kernel.REFUSED
        show(doc, as_json)
        return kernel.ESCALATE if flagged else kernel.ALIVE
    deep = opts.get("--deep", str(DEEP))
    if not opts.get("--in") or not deep.isdigit() or int(deep) > 9:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    folder = Path(opts["--in"]).expanduser()
    if not folder.is_dir():
        print(f"refused: {folder} isn't a folder", file=sys.stderr)
        return kernel.REFUSED
    doc, flagged = looked(folder.resolve(), int(deep))
    show(doc, as_json)
    return kernel.ESCALATE if flagged else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
