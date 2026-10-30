"""pair_drift.py: figures a summary says that its full text doesn't.

    python adapters/stdlib/pair-drift/pair_drift.py --box DIR [--full NAME] [--summary NAME]

A pair is two files in one folder: the full text (DRAFT.md unless --full
names another) and its summary (README.md unless --summary does). Every
figure in the summary is looked for in the full text. A figure the summary
says and the full text never does is drift: a number changed in one and not
the other, or a number the summary brought in on its own.

    research/sovereignty    summary 4 figures, full 61, 1 only in the summary
      README.md:31  $195-$205B   Google guides $195-$205B for 2026
    research/postwar        summary 4 figures, full 5, 0 only in the summary
    2 pairs read, 1 with drift

A figure is a number with what makes it one: a currency sign, a percent, a
scale word (thousand, million, billion, trillion, or k, M, B, T after a
number), a unit of power (MW, GW), or three or more digits. A range is one
figure, its two ends kept, so "$180 to $190 billion" and "$180-190B" are the
same figure and "$195-205B" is a different one. Bare numbers under 100,
years from 1900 to 2099, and a year with its month (2026-03) are left out: a count of chapters and a date are not
the figures a reader checks. "$5 billion" is never read as "$5".

It only reads. Exit codes, the kernel's: 0 a summary carries a figure its
full text doesn't; 42 every pair agrees, or no pair was found; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

SCALE = {"thousand": "K", "k": "K", "million": "M", "m": "M", "mn": "M",
         "billion": "B", "b": "B", "bn": "B", "trillion": "T", "t": "T"}  # fmt: skip
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
FIG = re.compile(
    rf"(?<![\w.])(?P<cur>[$€£])?(?P<a>{NUM})"
    rf"(?:\s*(?P<sa>thousand|million|billion|trillion|bn|mn|[kmbt])\b)?"
    rf"(?:\s*(?:-|–|—|to)\s*(?P<cur2>[$€£])?(?P<b>{NUM}))?"
    rf"(?:\s*(?P<sb>thousand|million|billion|trillion|bn|mn|[kmbt])\b)?"
    rf"(?:\s*(?P<unit>%|percent\b|MW\b|GW\b))?",
    re.I,
)


def figure(m: re.Match) -> str | None:
    """One figure's plain form, or None when the number isn't one by the
    card's reading (a bare small number, or a year)."""
    a, b = m["a"].replace(",", ""), (m["b"] or "").replace(",", "")
    scale = SCALE.get((m["sb"] or m["sa"] or "").lower(), "")
    unit = (m["unit"] or "").replace("percent", "%").upper().replace("PERCENT", "%")
    cur = m["cur"] or m["cur2"] or ""
    if b and re.fullmatch(r"(19|20)\d\d", a) and re.fullmatch(r"(0?[1-9]|1[0-2])", b):
        return None  # a year and month, as 2026-03
    marked = bool(cur or scale or unit)
    if not marked:
        if not b and (float(a) < 100 or re.fullmatch(r"(19|20)\d\d", a)):
            return None
        if b and all(re.fullmatch(r"(19|20)\d\d", x) for x in (a, b)):
            return None
        if b and float(a) < 100 and float(b) < 100:
            return None
    value = f"{a}-{b}" if b else a
    return f"{cur}{value}{scale}{unit}"


def figures(text: str) -> list[str]:
    return [f for m in FIG.finditer(text) if (f := figure(m))]


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def pairs(files: dict, full: str, summary: str) -> list[tuple[str, str, str]]:
    out = []
    for path in sorted(files):
        p = Path(path)
        if p.name == summary:
            twin = str(p.with_name(full))
            if twin in files:
                out.append((str(p.parent) if str(p.parent) != "." else ".", twin, path))
    return out


def drift(files: dict, full_path: str, summary_path: str) -> dict:
    in_full = {f for _, ln in files[full_path] for f in figures(ln)}
    seen, only = set(), []
    for n, line in files[summary_path]:
        for f in figures(line):
            seen.add(f)
            if f not in in_full:
                only.append((n, f, line.strip()))
    return {"summary": len(seen), "full": len(in_full), "only": only}


def main(argv: list[str]) -> int:
    opts, it = {"--full": "DRAFT.md", "--summary": "README.md"}, iter(argv)
    for a in it:
        if a in ("--box", "--full", "--summary"):
            opts[a] = next(it, "")
        else:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return kernel.REFUSED
    if not opts.get("--box") or not opts["--full"] or not opts["--summary"]:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if opts["--full"] == opts["--summary"]:
        print("refused: --full and --summary name the same file", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    files = file_lines(kernel.chunks(Path(kernel.config(box)["pile"])))
    found = pairs(files, opts["--full"], opts["--summary"])
    if not found:
        print(f"No folder holds both {opts['--full']} and {opts['--summary']}.")
        return kernel.ESCALATE
    w = max(len(d) for d, _, _ in found)
    lines, drifted = [], 0
    for folder, full_path, summary_path in found:
        d = drift(files, full_path, summary_path)
        drifted += bool(d["only"])
        lines.append(
            f"{folder:<{w}}  summary {d['summary']} figures, full {d['full']}, "
            f"{len(d['only'])} only in the summary"
        )
        name = Path(summary_path).name
        for n, f, text in d["only"]:
            lines.append(f"  {name}:{n}  {f:<12} {text[:100]}")
    lines.append(
        f"{len(found)} pair{'s' if len(found) != 1 else ''} read, {drifted} with drift"
    )
    print("\n".join(lines))
    return kernel.ALIVE if drifted else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
