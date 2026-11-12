"""land.py: the files sort placed, copied (never moved) into a folder per
category, each copy logged with where it came from and its hash.
Python 3.9+.

    python adapters/stdlib/land/land.py --of SORT.json --from FOLDER --to DIR [--skip PREFIX ...] [--dry-run] [--json]

SORT.json is sort's report as JSON (`sort.py ... --json`, or the copy a
stack keeps, `{NN.json}`). FOLDER is the folder of originals the box's pile
was made from; DIR is where the categories' folders go. Each file sort put
in a category is copied from FOLDER to DIR/<category>/files/<its path>, and
the copy is logged in DIR/<category>/landed.jsonl: its path, where it came
from, and its sha256.

**From a pile path to its original.** A reader writes FOLDER's file
`a/b.pdf` as `a/b.pdf.txt`, a long one as `a/b.pdf.part2.txt` too, and a
pile made by several readers puts each under its own folder first
(`pdf/a/b.pdf.txt`). So a pile path names, in this order, the file at that
path in FOLDER, the file it is a mirror of, then those two with the first
folder taken off, the mirror first; the first of these that is a file in FOLDER is the original. The
same original reached by two readers is landed once; reached in two
categories, it is said and copied nowhere.

**What waits on you.** sort's "more than one" and "unsorted" are never
copied: they wait for your phrase or your seal. A copy that would replace a
different file already in DIR is left undone and said; the same bytes
already there are "already there". A path under a --skip PREFIX (a code
checkout inside the folder, say) is passed over and counted. --dry-run says
the same and writes nothing.

It prints a report (the shape every report add-on shares), and --json the
same report as one JSON object.

Exit codes, the kernel's: 0 every placed file landed or already there
(populated), or nothing placed (empty); 42 something waits on you (a tie,
an unsorted file, one in two categories, one with no original, a copy that
would replace a different file); 2 refused (a bad command line, SORT.json
not sort's report, FOLDER not a folder that's there, DIR a file, one
inside the other). DIR is made on the first copy if it isn't there.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    "usage: land.py --of SORT.json --from FOLDER --to DIR "
    "[--skip PREFIX ...] [--dry-run] [--json]"
)
WAITS = ("more than one", "unsorted")  # sort's own groups, never a category
MIRROR = re.compile(r"(\.part\d+)?\.txt$")


def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def candidates(rel: str) -> list[str]:
    """The paths in FOLDER a pile path may be the words of, in the order
    they're tried: itself, what it mirrors, then what it mirrors and itself
    without their first folder (a reader's own folder)."""
    bare = MIRROR.sub("", rel)
    out = [rel, bare]
    for p in (bare, rel):
        parts = PurePosixPath(p).parts
        if len(parts) > 1:
            out.append(str(PurePosixPath(*parts[1:])))
    seen: list[str] = []
    for c in out:
        if c and c not in seen:
            seen.append(c)
    return seen


def original(src: Path, rel: str) -> str | None:
    """The original in `src` that pile path `rel` was read from, or None."""
    for c in candidates(rel):
        parts = PurePosixPath(c).parts
        if ".." in parts or PurePosixPath(c).is_absolute():
            continue
        if (src / c).is_file():
            return c
    return None


def safe_name(name: str) -> bool:
    """A category's name as one folder: no separator, nothing hidden."""
    return (
        bool(name) and "/" not in name and "\\" not in name and not name.startswith(".")
    )


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def placed(doc: dict) -> tuple[dict, list]:
    """({category: [(pile path, why)]}, [(pile path, what)] waiting on you)
    from sort's report."""
    by: dict = {}
    waiting: list = []
    for g in doc["groups"]:
        name = g.get("name")
        rows = [(r["where"], r["what"]) for r in g.get("rows", [])]
        if name in WAITS:
            waiting += [(w, f"{name}: {x}") for w, x in rows]
        elif name is not None:
            by.setdefault(name, []).extend(rows)
    return by, waiting


def land(doc: dict, src: Path, dst: Path, skip: list[str], dry: bool) -> dict:
    by, waiting = placed(doc)
    homes: dict = {}  # original -> {category: why}
    no_original: list = []
    bad_names: list = []
    skipped = 0
    for cat, rows in by.items():
        if not safe_name(cat):
            bad_names += [(w, f"{cat!r} isn't a folder name") for w, _ in rows]
            continue
        for rel, why in rows:
            orig = original(src, rel)
            if orig is None:
                no_original.append((rel, f"{cat}: no original in the folder"))
                continue
            if any(
                orig == s.rstrip("/") or orig.startswith(s.rstrip("/") + "/")
                for s in skip
            ):
                skipped += 1
                continue
            homes.setdefault(orig, {}).setdefault(cat, why)
    twice = [
        (o, "in " + ", ".join(sorted(c)))
        for o, c in sorted(homes.items())
        if len(c) > 1
    ]
    landed: dict = {}
    differs: list = []
    copied = there = 0
    for orig, cats in sorted(homes.items()):
        if len(cats) > 1:
            continue
        ((cat, why),) = cats.items()
        target = dst / cat / "files" / orig
        source = src / orig
        if target.exists():
            if target.is_file() and sha(target) == sha(source):
                there += 1
                landed.setdefault(cat, []).append((orig, "already there"))
            else:
                differs.append(
                    (orig, f"{cat}: a different file is already there, left as it was")
                )
            continue
        copied += 1
        landed.setdefault(cat, []).append((orig, "would copy" if dry else "copied"))
        if dry:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        line = {"path": orig, "from": str(source), "sha256": sha(target), "sorted": why}
        with open(dst / cat / "landed.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")
    waits = waiting + twice + no_original + bad_names + differs
    groups = [(cat, rows) for cat, rows in sorted(landed.items())]
    groups += [
        ("waiting on you", waiting),
        ("in two categories", twice),
        ("no original", no_original + bad_names),
        ("left as it was", differs),
    ]
    verb = "would copy" if dry else "copied"
    said = (
        f"{verb} {copied} files into {len(landed)} categories, {there} already there, "
        f"{len(waits)} waiting on you, {skipped} skipped"
    )
    state = "populated" if (landed or waits) else "empty"
    return report("land", state, said, groups)


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    dry = "--dry-run" in argv
    argv = [a for a in argv if a not in ("--json", "--dry-run")]
    if len(argv) % 2:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    pairs = list(zip(argv[::2], argv[1::2]))
    opts = {k: v for k, v in pairs if k != "--skip"}
    skip = [v for k, v in pairs if k == "--skip"]
    if sorted(opts) != ["--from", "--of", "--to"] or len(opts) + len(skip) != len(
        pairs
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    src, dst = Path(opts["--from"]), Path(opts["--to"])
    if not src.is_dir():
        print(f"refused: not a folder that's there: {src}", file=sys.stderr)
        return kernel.REFUSED
    if dst.exists() and not dst.is_dir():
        print(f"refused: not a folder: {dst}", file=sys.stderr)
        return kernel.REFUSED
    if within(dst.resolve(), src.resolve()) or within(src.resolve(), dst.resolve()):
        print("refused: FOLDER and DIR must not be inside one another", file=sys.stderr)
        return kernel.REFUSED
    try:
        doc = json.loads(Path(opts["--of"]).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        print(f"refused: can't read {opts['--of']} as JSON", file=sys.stderr)
        return kernel.REFUSED
    if (
        not isinstance(doc, dict)
        or doc.get("addon") != "sort"
        or not isinstance(doc.get("groups"), list)
    ):
        print(
            f"refused: {opts['--of']} isn't sort's report (sort.py --json)",
            file=sys.stderr,
        )
        return kernel.REFUSED
    out = land(doc, src, dst, skip, dry)
    say(out, as_json)
    waits = any(g["name"] in ("waiting on you", "in two categories", "no original", "left as it was")
                for g in out["groups"])  # fmt: skip
    return kernel.ESCALATE if waits else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
