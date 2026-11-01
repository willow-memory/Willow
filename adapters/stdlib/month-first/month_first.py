"""month_first.py: dates written month first, mirrored with their ISO form beside them.

    python adapters/stdlib/month-first/month_first.py mirror --from FOLDER --to MIRROR

The kernel reads 10/24/2026, since 24 can't be a month, but never 11/03/2026,
which reads either way, and never `Oct 24, 2026` or a two-digit year. This is
for a folder whose writer you know: an American's letters, a US court's
papers. Each text file (.txt, .md, .html) is written into MIRROR with every
month-first date followed by its ISO form, so the kernel and the add-ons that
read dates (timeline, gaps, coming-up) can place it:

    Hearing moved to 11/03/2026 [2026-11-03]; filed Oct. 2nd, 2026 [2026-10-02].

What it reads: 11/03/2026, 11/03/26, Nov 3, 2026, November 3 2026 and Nov. 3rd,
2026. A two-digit year 70 to 99 is the 1900s, 00 to 69 the 2000s. A date that
isn't one (13/03/2026, Feb 30, 2026), or falls outside 1900 to 2099, is left
as it is. The original text stays; a page's tags are dropped, as the kernel
drops them. A date already followed by its ISO form is not marked again.

Every text file is written, marked or not, so MIRROR is a whole folder to
build a box from. A file that isn't UTF-8 is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

TEXT = (".txt", ".md")
PAGE = (".html", ".htm")
MONTHS = {
    name: number
    for number, names in enumerate(
        [
            ("jan", "january"),
            ("feb", "february"),
            ("mar", "march"),
            ("apr", "april"),
            ("may",),
            ("jun", "june"),
            ("jul", "july"),
            ("aug", "august"),
            ("sep", "sept", "september"),
            ("oct", "october"),
            ("nov", "november"),
            ("dec", "december"),
        ],
        1,
    )
    for name in names
}
MARKED = r"(?! \[\d{4}-\d{2}-\d{2}\])"
# 11/03/2026 or 11/03/26: whole numbers, not part of a path or a longer run
NUMBERS = re.compile(r"(?<![\w/.-])(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})(?![\w/])" + MARKED)
# Nov 3, 2026 / November 3 2026 / Nov. 3rd, 2026
WORDS = re.compile(
    r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?"
    r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b" + MARKED,
    re.IGNORECASE,
)


def iso(year: str, month: int, day: int) -> str | None:
    """The date as YYYY-MM-DD, or None when it isn't one the kernel reads."""
    y = int(year)
    if len(year) == 2:
        y += 1900 if y >= 70 else 2000
    if not 1900 <= y <= 2099:
        return None
    try:
        return dt.date(y, month, day).isoformat()
    except ValueError:
        return None


def mark(text: str) -> tuple[str, int]:
    """`text` with each month-first date's ISO form after it, and how many."""
    count = 0

    def beside(m: re.Match, got: str | None) -> str:
        nonlocal count
        if got is None:
            return m[0]
        count += 1
        return f"{m[0]} [{got}]"

    text = NUMBERS.sub(lambda m: beside(m, iso(m[3], int(m[1]), int(m[2]))), text)
    text = WORDS.sub(
        lambda m: beside(m, iso(m[3], MONTHS[m[1].lower()], int(m[2]))), text
    )
    return text, count


def sources(root: Path) -> list[Path]:
    """Every file under `root`, skipping hidden names, sorted by path."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            full = Path(dirpath, name)
            if not name.startswith(".") and full.is_file():
                found.append(full.relative_to(root))
    return sorted(found, key=lambda p: p.as_posix())


def mirror(folder: Path, to: Path) -> int:
    if not folder.is_dir():
        print(f"refused: {folder} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    src, dst = folder.resolve(), to.resolve()
    if dst == src or src in dst.parents or dst in src.parents:
        print(
            "refused: MIRROR and FOLDER must not be inside each other", file=sys.stderr
        )
        return kernel.REFUSED
    if to.exists() and not to.is_dir():
        print(f"refused: {to} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    written = skipped = dates = 0
    for rel in sources(src):
        suffix = rel.suffix.lower()
        if suffix not in TEXT + PAGE:
            continue
        try:
            text = (src / rel).read_bytes().decode("utf-8-sig")
        except UnicodeDecodeError:
            skipped += 1
            print(f"skipped {rel.as_posix()}: not UTF-8", file=sys.stderr)
            continue
        except OSError as why:
            skipped += 1
            print(f"skipped {rel.as_posix()}: {why}", file=sys.stderr)
            continue
        if suffix in PAGE:
            text = kernel.html_text(text)
        text, n = mark(text)
        dates += n
        out = to / rel
        out = out.with_name(out.name + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))
        written += 1
    print(f"{dates} month-first dates given their ISO form")
    print(f"wrote {written} files to {to}; skipped {skipped}")
    return kernel.ALIVE if written else kernel.ESCALATE


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="month_first.py", description=__doc__.split("\n")[0]
    )
    verbs = ap.add_subparsers(dest="verb", required=True)
    m = verbs.add_parser("mirror", help="write each text file with ISO dates beside")
    m.add_argument("--from", dest="folder", required=True, type=Path)
    m.add_argument("--to", dest="to", required=True, type=Path)
    args = ap.parse_args(argv)
    return mirror(args.folder, args.to)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
