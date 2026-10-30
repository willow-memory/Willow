r"""family_tree.py: Family trees from GEDCOM files: who was born where and when. Python 3.9+.

    python adapters/stdlib/family-tree/family_tree.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .ged files (hidden folders and files skipped) and writes each
person as a paragraph that names the record it came from:

    John Smith (@I1@): born 2 Mar 1850 in Leeds; died 1920 in York;
    father Arthur Smith (@I4@); mother Ann Jones (@I5@);
    married Mary Brown (@I2@) 1875 in Hull; note: A weaver.

The name is read from NAME (the slashes round a surname dropped), the facts
from BIRT, DEAT, BURI, CHR and MARR with their DATE and PLAC, parents from the
family the person is a child of (FAMC), and spouses from the families they are
a spouse in (FAMS). A NOTE is kept whole, its CONT and CONC lines joined. The
@I..@ in brackets is the record's own id, so a passage says which record says
so. Dates are kept as the file writes them; none is guessed or reformatted.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no person is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

LINE = re.compile(r"^\s*(\d+)\s+(?:(@[^@]+@)\s+)?([A-Za-z0-9_]+)(?:\s(.*))?$")
EVENTS = {"BIRT": "born", "CHR": "christened", "DEAT": "died", "BURI": "buried"}


def records(text: str) -> list[dict]:
    """The level-0 records as {id, tag, value, kids: [(tag, value, kids)]}."""
    stack: list[tuple[int, dict]] = []
    out = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        m = LINE.match(raw)
        if not m:
            continue
        level, xref, tag, value = (
            int(m.group(1)),
            m.group(2),
            m.group(3).upper(),
            (m.group(4) or "").strip(),
        )
        node = {"id": xref or "", "tag": tag, "value": value, "kids": []}
        while stack and stack[-1][0] >= level:
            stack.pop()
        if level == 0:
            out.append(node)
        elif stack:
            parent = stack[-1][1]
            if tag in ("CONT", "CONC"):
                parent["value"] += ("\n" if tag == "CONT" else "") + (m.group(4) or "")
                continue
            parent["kids"].append(node)
        stack.append((level, node))
    return out


def child(node: dict, tag: str) -> dict | None:
    return next((k for k in node["kids"] if k["tag"] == tag), None)


def clean(name: str) -> str:
    return " ".join(name.replace("/", " ").split())


def named(people: dict[str, dict], ref: str) -> str:
    p = people.get(ref)
    n = child(p, "NAME") if p else None
    return f"{clean(n['value'])} ({ref})" if n else ref


def fact(node: dict) -> str:
    date, place = child(node, "DATE"), child(node, "PLAC")
    return " ".join(
        x
        for x in (
            date["value"] if date else "",
            f"in {place['value']}" if place else "",
        )
        if x
    )


def convert(data: bytes) -> str | None:
    text = (
        data.decode("utf-8-sig", errors="strict")
        if data.isascii()
        else data.decode("utf-8-sig", errors="replace")
    )
    if not text.lstrip().startswith("0 HEAD"):
        raise ValueError("not a GEDCOM file")
    recs = records(text)
    people = {r["id"]: r for r in recs if r["tag"] == "INDI" and r["id"]}
    families = {r["id"]: r for r in recs if r["tag"] == "FAM" and r["id"]}
    blocks = []
    for ref, p in people.items():
        name = child(p, "NAME")
        bits = []
        for tag, word in EVENTS.items():
            for e in (k for k in p["kids"] if k["tag"] == tag):
                bits.append(
                    f"{word} {fact(e)}".strip()
                    if fact(e)
                    else word
                    if e["value"].upper() == "Y"
                    else ""
                )
        for fam in (k["value"] for k in p["kids"] if k["tag"] == "FAMC"):
            f = families.get(fam)
            for tag, word in (("HUSB", "father"), ("WIFE", "mother")):
                parent = child(f, tag) if f else None
                if parent:
                    bits.append(f"{word} {named(people, parent['value'])}")
        for fam in (k["value"] for k in p["kids"] if k["tag"] == "FAMS"):
            f = families.get(fam)
            if not f:
                continue
            for tag in ("HUSB", "WIFE"):
                spouse = child(f, tag)
                if spouse and spouse["value"] != ref:
                    m = child(f, "MARR")
                    bits.append(
                        f"married {named(people, spouse['value'])}"
                        + (f" {fact(m)}" if m and fact(m) else "")
                    )
        for n in (k for k in p["kids"] if k["tag"] == "NOTE"):
            if n["value"].strip():
                bits.append("note: " + " ".join(n["value"].split()))
        who = f"{(clean(name['value']) if name else '') or '(no name)'} ({ref})"
        said = "; ".join(b for b in bits if b)
        blocks.append(
            f"{who}: {said}" + ("" if said.endswith(".") else ".")
            if said
            else f"{who}."
        )
    return "\n\n".join(blocks) + "\n" if blocks else None


EXTS = (".ged",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: family_tree.py mirror --from FOLDER --to MIRROR"


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
