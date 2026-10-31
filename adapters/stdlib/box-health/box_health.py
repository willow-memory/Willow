"""box_health.py: a box's health in one line. Python 3.9+.

    python adapters/stdlib/box-health/box_health.py --box DIR [--now TS] [--long]

    box ok: 214 rows hold; 3 approved, 2 waiting; every file readable; words list as last used; last out row 2026-10-20 (4 days ago)

What it looks at, each in a few words, in this order:

- the chain: whether every row's hash holds (`kernel.read`). A break is the
  first thing said, and nothing else is, since nothing after it can be trusted;
- approvals: how many hold under your key (the kernel's `sealed`, so the key is
  read there and nowhere here), how many suggestions wait, and any approval
  whose proof fails or whose proposal file is no longer the bytes you approved;
- files it can't read: the files in your folder the bite skips, because they
  are binary, too large, or not UTF-8 text, counted by extension, with the
  add-on that reads that kind of file if this repository has one;
- the words list: whether it is still the one the last question used;
- `out`: when the record last had an `out` row, the kernel's own look at what
  waits on you, and how long ago that was.

Hidden files and folders are not counted, the bite doesn't read them either.
`--long` puts each part on its own line. The line begins `box ok` when
nothing needs you, `box needs you` when something does, and `box broken` for a
chain that doesn't hold.

It only reads, and writes nothing, not even the `out` row it reports on.
Exit codes, the kernel's: 0 ok; 42 something needs you; 2 refused (a chain
that doesn't hold, a bad command line).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

#: what reads a kind of file this repository has no plain-text reader for
READERS = {
    ".pdf": "pdf", ".docx": "office", ".xlsx": "office", ".pptx": "office", ".odt": "office",
    ".ods": "office", ".eml": "mail", ".mbox": "mail", ".epub": "books",
}  # fmt: skip


def reader_for(ext: str) -> str | None:
    name = READERS.get(ext)
    if name and any(
        (STDLIB.parents[1] / "adapters" / kind / name).is_dir()
        for kind in ("stdlib", "deps")
    ):
        return name
    return None


def too_large(pile: Path) -> int:
    """How many files the bite skips for size alone: over `kernel.MAX_FILE`.
    A reader's mirror that big is cut, not converted again."""
    return sum(
        1
        for p in pile.rglob("*")
        if p.is_file()
        and not any(part.startswith(".") for part in p.relative_to(pile).parts)
        and p.stat().st_size > kernel.MAX_FILE
    )


def unreadable(pile: Path) -> dict[str, int]:
    """Files the bite can't read, by extension: not text, too large, not UTF-8."""
    out: dict[str, int] = {}
    for p in sorted(pile.rglob("*")):
        rel = p.relative_to(pile)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        try:
            if p.stat().st_size > kernel.MAX_FILE:
                bad = True
            else:
                raw = p.read_bytes()
                bad = b"\0" in raw[: kernel.SNIFF]
                if not bad:
                    raw.decode("utf-8")
        except UnicodeDecodeError:
            bad = True
        except OSError:
            bad = True
        if bad:
            ext = p.suffix.lower() or "(no extension)"
            out[ext] = out.get(ext, 0) + 1
    return out


def ago(then: str, today: date) -> str:
    try:
        d = date(int(then[:4]), int(then[5:7]), int(then[8:10]))
    except ValueError:
        return then
    n = (today - d).days
    return (
        f"{then[:10]} (today)"
        if n == 0
        else f"{then[:10]} ({n} day{'s' if n != 1 else ''} ago)"
        if n > 0
        else f"{then[:10]} (in the future)"
    )


def health(box: Path, today: date) -> tuple[str, list[str], list[str]]:
    """(ok | needs you | broken, what is fine, what needs you)."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return (
            "broken",
            [],
            [
                f"the chain doesn't hold: {breaks[0]}"
                + (f" (and {len(breaks) - 1} more)" if len(breaks) > 1 else "")
            ],
        )
    fine: list[str] = []
    needs: list[str] = []
    fine.append(
        f"{len(rows)} row{'s' if len(rows) != 1 else ''} hold{'' if len(rows) != 1 else 's'}"
    )
    good, no = kernel.sealed(box, rows), kernel.declined(box, rows)
    forged = [
        r["n"] for r in rows if r["kind"] == "seal" and r.get("subject") not in good
    ]
    drifted = [
        s
        for s, row in good.items()
        if kernel.standing(box, rows, s, row)[2] is not None
    ]
    waiting = (
        {
            r["subject"]
            for r in rows
            if r["kind"] == "proposal" and r.get("verdict") == "pass"
        }
        - set(good)
        - set(no)
    )
    fine.append(f"{len(good) - len(drifted)} approved, {len(waiting)} waiting")
    if forged:
        needs.append(
            f"seal row{'s' if len(forged) != 1 else ''} {forged} don't prove under your key"
        )
    if drifted:
        needs.append(
            f"{len(drifted)} approved answer{'s' if len(drifted) != 1 else ''} whose proposal file is not what you approved"
        )
    if waiting:
        needs.append(
            f"{len(waiting)} suggestion{'s' if len(waiting) != 1 else ''} waiting for you"
        )
    cfg = kernel.config(box)
    skipped = unreadable(Path(cfg["pile"]))
    if skipped:
        parts = []
        for ext, n in sorted(skipped.items(), key=lambda x: (-x[1], x[0])):
            r = reader_for(ext)
            parts.append(f"{n} {ext}" + (f", read by {r}" if r else ""))
        total = sum(skipped.values())
        big = too_large(Path(cfg["pile"]))
        needs.append(
            f"{total} file{'s' if total != 1 else ''} can't be read ({'; '.join(parts)})"
            + (f", {big} of them over {kernel.MAX_FILE // 1_000_000} MB" if big else "")
        )
    else:
        fine.append("every file readable")
    last_bite = next(
        (r for r in reversed(rows) if r["kind"] == "bite" and "words_sha256" in r), None
    )
    if "words" in cfg:
        _, sha, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            needs.append(f"the words list can't be read ({why})")
        elif last_bite and last_bite["words_sha256"] != sha:
            needs.append("the words list changed since the last question")
        else:
            fine.append("words list as last used")
    out = next((r for r in reversed(rows) if r["kind"] == "out"), None)
    (fine if out else needs).append(
        f"last out row {ago(out['ts'], today)}" if out else "no out row yet"
    )
    return ("needs you" if needs else "ok"), fine, needs


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    long = "--long" in args
    args = [a for a in args if a != "--long"]
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    try:
        today = date(int(ts[:4]), int(ts[5:7]), int(ts[8:10]))
    except ValueError:
        print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    state, fine, needs = health(box, today)
    if state == "broken":
        print(f"box broken: {needs[0]}", file=sys.stderr)
        return kernel.REFUSED
    if long:
        print(f"box {state}")
        for line in needs:
            print(f"  needs you: {line}")
        for line in fine:
            print(f"  fine: {line}")
    else:
        print(f"box {state}: " + "; ".join(needs + fine))
    return kernel.ESCALATE if needs else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
