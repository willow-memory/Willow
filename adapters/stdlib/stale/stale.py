"""stale.py: approved answers whose cited passage has changed or gone.

    python adapters/stdlib/stale/stale.py --box DIR [--json]

An approved answer cites passages by id, and a passage's id is the SHA-256 of
its text. So when the cited words change, or their file goes, that id is no
longer anywhere in your folder, and this says so exactly; no guess, no date
compared. It counts the approvals and the stale ones, and for each that
doesn't hold, which cited passage is missing and where it was:

    stale: populated, 2 approved; 1 stale
    ## proposal:0a6fde95fa41…  'Reply by 2026-09-16: …'
      mail/2026-03-20-county.txt:12  cited 0e4ba2dfb524: no longer in your folder

It prints a report, as every report add-on does (adapters/stdlib/ci/README.md,
the report contract), and `--json` gives the same report as one JSON object.
An approval whose proposal file isn't what was sealed is a row of its own,
first, marked broken, and is never read for its cites.

The kernel keeps giving an approved answer for its question whatever its
sources do; this is how a person finds out the ground moved under one.

Exit codes, the kernel's: 0 every approval holds, or there are none (empty);
42 an approval's cited passage has changed or gone, or its proposal file is
broken, and waits on you (populated); 2 refused (a record that doesn't
verify).

It only reads: the record, the approved suggestions, your folder. It writes
nothing, and it doesn't take an approval back; that stays the person's.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "stale"


def pieces():
    """The pieces add-on, which reads a pile a folder at a time, or None
    when it isn't beside this one."""
    path = Path(__file__).resolve().parents[1] / "pieces" / "pieces.py"
    if not path.is_file():
        return None
    mod = types.ModuleType("stale_pieces")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def present(pile: Path, ids: set[str]) -> set[str]:
    """Which of these ids are passages of the pile now. With pieces beside,
    the pile is read a folder at a time and only these ids are kept."""
    if not ids:
        return set()
    pc = pieces()
    found = set()
    for c in pc.passages(pile) if pc else kernel.chunks(pile):
        if c["id"] in ids:
            found.add(c["id"])
            if len(found) == len(ids):
                break
    return found


def check(box: Path) -> tuple[int, list[dict]]:
    """(exit code, one entry per approval, in the order they were sealed)."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return kernel.REFUSED, [{"refused": b} for b in breaks]
    places = {}  # where each served id was, from the bites that served it
    for r in rows:
        for s in r.get("served", []):
            places.setdefault(s["id"], s["where"])
    standing = [
        (subj, row, *kernel.standing(box, rows, subj, row))
        for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"])
    ]  # fmt: skip
    cited = {c for _, _, prop, _, why in standing if why is None for c in prop["cites"]}
    here = present(Path(kernel.config(box)["pile"]), cited)
    out = []
    for subj, row, prop, _, why in standing:
        if (
            why is not None
        ):  # its cites can't be read from a file that isn't what was sealed
            out.append({"subject": subj, "broken": why, "gone": [], "row": row["n"]})
            continue
        gone = [
            {"id": c, "was": places.get(c, "?")} for c in prop["cites"] if c not in here
        ]
        out.append(
            {"subject": subj, "data": prop["data"], "gone": gone, "row": row["n"]}
        )
    stale = any(e["gone"] or e.get("broken") for e in out)
    return (kernel.ESCALATE if stale else kernel.ALIVE), out


def groups_of(entries: list[dict]) -> list[tuple[str | None, list]]:
    """The broken approvals first, with no heading; then a group per stale
    approval, its rows each cited passage gone, where it was, then its id."""
    broken = [(f"{e['subject'][:21]}…", f"broken: its proposal file {e['broken']}")
              for e in entries if "broken" in e]  # fmt: skip
    groups: list[tuple[str | None, list]] = [(None, broken)]
    for e in entries:
        if e.get("gone"):
            quote = e["data"] if len(e["data"]) <= 60 else e["data"][:57] + "..."
            groups.append((f"{e['subject'][:21]}…  {quote!r}", [
                (g["was"], f"cited {g['id'][:12]}: no longer in your folder")
                for g in e["gone"]]))  # fmt: skip
    return groups


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
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


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    code, entries = check(box)
    if code == kernel.REFUSED:
        for e in entries:
            print(f"refused: {e['refused']}", file=sys.stderr)
        return code
    n = sum(bool(e["gone"]) for e in entries)
    bad = sum("broken" in e for e in entries)
    said = f"{len(entries)} approved; {n} stale" + (f"; {bad} broken" if bad else "")
    state = "populated" if n or bad else "empty"
    say(report(NAME, state, said, groups_of(entries)), as_json)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
