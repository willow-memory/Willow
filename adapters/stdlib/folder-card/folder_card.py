"""folder_card.py: a card for your folder itself, written to a file, to hand a
model as context. Python 3.9+.

    python adapters/stdlib/folder-card/folder_card.py --box DIR --to FILE [--notes FILE] [--now TS]

The card says what the files in the pile are (size, first and last date, whether
the file labels itself fiction), which files it could not read, and where the
dated logs stop, using the `gaps` add-on's rule and not a second one. With
--notes it adds the gaps you know of, from your own notes:

    gap 2026-03-04 to 2026-03-11 flu, no writing
    Everything before 2025 was typed up from paper.

A line that starts with `gap` and two dates is a gap you know of, with your
reason. Every other line is kept word for word under "Your notes". Each gap the
files show is marked as told (you named it) or untold; each gap you named is
marked as seen in the files or not, with the number of dated entries the files
hold inside it, so a note that the files contradict is said, not smoothed over.

A gap is days with no entry written, never days when nothing happened. FILE is
written once, readable only by you, never over a file that exists, and the same
pile and notes give the same bytes. The card is a claim made from your files,
not a signature; it says so. Nothing is sent anywhere.

Exit codes, the kernel's: 0 written; 2 refused (a bad command line, a box that
isn't one, notes that can't be read, a FILE that exists or can't be made).
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_gaps_for_card", HERE.parent / "gaps" / "gaps.py"
)
gaps = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gaps)

KNOWN = re.compile(
    r"^[ \t#*>-]*gap[ \t]+(\d{4}-\d\d-\d\d)[ \t]*(?:to|-|–)?[ \t]*(\d{4}-\d\d-\d\d)\b[ \t]*(.*)$",
    re.I,
)
FICTION = ("fiction", "fictional")  # a first line that starts with one of these
FOLD = 5  # files named by a date in one folder are said as one line from this many
SHOWN = 10  # the longest gaps a log lists; the ones you named are always listed


def iso(text: str) -> date | None:
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def read_notes(text: str) -> dict:
    """Your notes as three kinds of line: gaps you know of, lines that start
    with `gap` but did not read as one, and everything else, kept as written."""
    out = {"known": [], "unread": [], "notes": []}
    for ln in text.splitlines():
        if not ln.strip():
            continue
        m = KNOWN.match(ln)
        if m and (a := iso(m[1])) and (b := iso(m[2])) and a <= b:
            out["known"].append((a, b, m[3].strip()))
        elif re.match(r"^[ \t#*>-]*gap\b", ln, re.I):
            out["unread"].append(ln.strip())
        else:
            out["notes"].append(ln.rstrip())
    return out


def files(pile: Path, chunks: list[dict]) -> list[dict]:
    """Every file under the pile (hidden folders aside, as the kernel leaves
    them): its size, its first and last date, its fiction label; or, when the
    kernel does not read it, that it was not read."""
    by_path: dict[str, list[dict]] = {}
    for c in chunks:
        by_path.setdefault(c["path"], []).append(c)
    out = []
    for p in sorted(pile.rglob("*")):
        rel = p.relative_to(pile)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        row = {
            "path": rel.as_posix(),
            "bytes": p.stat().st_size,
            "read": str(rel) in by_path,
        }
        if row["read"]:
            cs = by_path[str(rel)]
            days = {
                d
                for c in cs
                for ln in c["text"].splitlines()
                if (d := gaps.starts_with_date(ln))
            }
            named = gaps.day(kernel.newest(p.name))
            row["named"] = named
            row["days"] = days
            first = min(cs, key=lambda c: c["line"])["text"].lstrip().lower()
            row["fiction"] = first.startswith(FICTION)
        out.append(row)
    return out


def span(f: dict) -> str:
    if f["named"]:
        return f"named for {f['named']}"
    d = sorted(f["days"])
    if not d:
        return "no dated line"
    if len(d) == 1:
        return f"one dated line, {d[0]}"
    return f"{len(d)} dated days, {d[0]} to {d[-1]}"


def overlap(a: date, b: date, x: date, y: date) -> bool:
    return a <= y and x <= b


def card(pile: Path, notes: dict | None, now: date | None) -> str:
    chunks = kernel.chunks(pile)
    fs = files(pile, chunks)
    logs = gaps.logs(chunks)
    every = set()
    for log in logs:
        every |= log["days"]
    known = notes["known"] if notes else []
    n_read = sum(1 for f in fs if f["read"])
    L = [f"# Card for {pile.name}", "",
         "Compiled from the files in this folder"
         + (" and the person's own notes" if notes is not None else "")
         + ". It is a claim made from those files, not a signature. A gap is days with "
         "no entry written, never days when nothing happened.", "",
         f"## Files ({len(fs)}: {n_read} read, {len(fs) - n_read} not)", ""]  # fmt: skip
    folds: dict[str, list[dict]] = {}
    for f in fs:
        if f["read"] and f["named"]:
            folds.setdefault(str(Path(f["path"]).parent), []).append(f)
    folds = {k: v for k, v in folds.items() if len(v) >= FOLD}
    said = set()
    for f in fs:
        k = str(Path(f["path"]).parent)
        if f["read"] and f["named"] and k in folds:
            if k not in said:
                said.add(k)
                g = folds[k]
                ds = sorted(x["named"] for x in g)
                L.append(f"- `{k}/`: {len(g)} files named by a date, {ds[0]} to {ds[-1]}, "
                         f"{sum(x['bytes'] for x in g):,} bytes")  # fmt: skip
            continue
        if not f["read"]:
            L.append(
                f"- `{f['path']}`: {f['bytes']:,} bytes, not read (binary, too large or not UTF-8)"
            )
        else:
            fic = "; labels itself fiction" if f["fiction"] else ""
            L.append(f"- `{f['path']}`: {f['bytes']:,} bytes, {span(f)}{fic}")
    L += ["", "## Dates and gaps", ""]
    seen: list[
        tuple[date, date]
    ] = []  # (first empty day, last empty day) of each gap found
    if not logs:
        L.append(
            "Nothing dated: no file named by a date, and no line that starts with one."
        )
    for log in logs:
        seq = sorted(log["days"])
        entries = "1 entry" if len(seq) == 1 else f"{len(seq)} entries"
        head = f"- `{log['name']}`, {log['how']}, {entries}"
        if len(seq) < gaps.FEWEST:
            L.append(f"{head}: too few for a rhythm (it needs {gaps.FEWEST})")
            continue
        typical, found = gaps.gaps(log["days"], now)
        L.append(
            f"{head}, {seq[0]} to {seq[-1]}, typical spacing {gaps.plural(typical, 'day')}"
        )
        if not found:
            L.append("  - no gap")
        marks = []
        for a, b, empty, open_ in found:
            lo, hi = (
                date.fromordinal(a.toordinal() + 1),
                date.fromordinal(b.toordinal() - 1),
            )
            seen.append((lo, hi))
            told = [why for x, y, why in known if overlap(lo, hi, x, y)]
            how = "told: " + (told[0] or "no reason given") if told else "untold"
            what = "SINCE" if open_ else "GAP"
            row = f"  - {what} {a} to {b}, {gaps.plural(empty, 'day')} with no entry; {how}"
            marks.append((empty, bool(told), row))
        top = sorted(marks, key=lambda m: (not m[1], -m[0]))[
            : max(SHOWN, sum(m[1] for m in marks))
        ]
        L += [m[2] for m in marks if m in top]
        if len(top) < len(marks):
            L.append(f"  - {len(marks) - len(top)} shorter gaps not listed")
        for p in log["undated"]:
            L.append(f"  - UNDATED `{p}`, not counted")
    if notes is not None:
        L += ["", "## Gaps you know of", ""]
        if not known:
            L.append("None named.")
        for x, y, why in known:
            inside = sum(1 for d in every if x <= d <= y)
            if inside:
                state = f"the files hold {f'{inside} dated ' + ('entry' if inside == 1 else 'entries')} inside it"
            elif any(overlap(x, y, lo, hi) for lo, hi in seen):
                state = "the files show it too"
            else:
                state = "the files show no gap there"
            L.append(f"- {x} to {y}: {why or 'no reason given'} ({state})")
        if notes["unread"]:
            L += ["", "Lines that start with `gap` but could not be read as one:", ""]
            L += [f"- {ln}" for ln in notes["unread"]]
        L += ["", "## Your notes", ""]
        L += notes["notes"] or ["None."]
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--notes", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    now = gaps.day(kernel.newest(opts["--now"])) if "--now" in opts else None
    if not opts.get("--box") or not opts.get("--to") or args or ("--now" in opts and now is None) \
            or ("--notes" in opts and not opts["--notes"]):  # fmt: skip
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box, to = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    notes = None
    if "--notes" in opts:
        try:
            notes = read_notes(Path(opts["--notes"]).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as e:
            print(
                f"refused: could not read the notes: {type(e).__name__}",
                file=sys.stderr,
            )
            return kernel.REFUSED
    text = card(Path(kernel.config(box)["pile"]), notes, now)
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as out:
        out.write(text)
    print(f"wrote {to}: {text.count(chr(10))} lines")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
