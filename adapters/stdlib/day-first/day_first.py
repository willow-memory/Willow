"""day_first.py: dates written day first, mirrored with their ISO form beside them.

    python adapters/stdlib/day-first/day_first.py mirror --from FOLDER --to MIRROR

The kernel reads 24/10/2026, since 24 can't be a month, but never 03/11/2026,
which reads either way, and never `3 Nov 2026`. This is for a folder whose
writer you know writes the day first: an English, Irish, Australian or Indian
hand, most of Europe's. Each file the kernel reads is written into MIRROR
under the same name with every day-first date followed by its ISO form, so
the kernel and the add-ons that read dates (coming-up, renewals, car, gaps,
timeline) can place it:

    Your cover ends on 03/11/2026 [2026-11-03]; MOT due 9 Nov 2026 [2026-11-09].

What it reads: 03/11/2026, 03/11/26, 3.11.2026 (dotted, with all four digits of its year), 3 Nov 2026, Tue 3 Nov 2026,
3rd November 2026 and 3 November, 2026. A two-digit year 70 to 99 is the
1900s, 00 to 69 the 2000s. A date that isn't one (31/02/2026), or falls
outside 1900 to 2099, is left as it is. A date with no year (Mon 26 Oct) is
left: its year is a guess. A date already followed by its ISO form is not
marked again.

The files are the kernel's own: every file it would read, by what it holds,
not its name (UTF-8, no NUL byte in its first 8,192 bytes, under its million
byte cap), so .eml, .ics and .csv come through as well as .txt and .md. Each
keeps its name; a page (.html) gains .txt, its tags dropped as the kernel
drops them. The original text stays. Files the kernel wouldn't read are left
out, so MIRROR is the folder to build the box from.

A file whose own dates say month first (11/24/2026 reads no other way) is
not the folder you said it was: its numbered dates are left as they are and
the file named. Its dates in words (3 Nov 2026) still gain their ISO form, as
they read one way only. It shares month-first's walk, its date check and its
month names; only the order is its own.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "month-first"))
import kernel  # noqa: E402
import month_first as mf  # noqa: E402

# 03/11/2026, 03/11/26, 3.11.2026: whole numbers, not part of a path, a
# version or a longer run. A dotted date needs its four-digit year: 1.1.11 is
# a section or an MOT item's number far more often than a day.
NUMBERS = re.compile(r"(?<![\w/.-])(\d{1,2})(?:(/)(\d{1,2})/(\d{4}|\d{2})|(\.)(\d{1,2})\.(\d{4}))(?![\w/]|\.\d)" + mf.MARKED)  # fmt: skip
# 3 Nov 2026 / Tue 3 Nov 2026 / 3rd November 2026 / 3 November, 2026
WORDS = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+("
    + "|".join(sorted(mf.MONTHS, key=len, reverse=True))
    + r")\.?,?\s+(\d{4})\b"
    + mf.MARKED,  # fmt: skip
    re.IGNORECASE,
)


def parts(m: re.Match) -> tuple[str, str]:
    """A numbered date's second number and its year, slashed or dotted."""
    return (m[3], m[4]) if m[2] else (m[6], m[7])


def month_first(text: str) -> bool:
    """`text`'s own dates say month first: one reads only that way (11/24/2026)."""
    return any(
        int(month) > 12 and mf.iso(year, int(m[1]), int(month))
        for m in NUMBERS.finditer(text)
        for month, year in [parts(m)]
    )


def mark(text: str) -> tuple[str, int, bool]:
    """`text` with each day-first date's ISO form after it, how many, and
    whether its own dates say month first, so its numbered ones are left."""
    count = 0
    mdy = month_first(text)

    def beside(m: re.Match, got: str | None) -> str:
        nonlocal count
        if got is None:
            return m[0]
        count += 1
        return f"{m[0]} [{got}]"

    if not mdy:
        text = NUMBERS.sub(lambda m: beside(m, mf.iso(parts(m)[1], int(parts(m)[0]), int(m[1]))), text)  # fmt: skip
    text = WORDS.sub(lambda m: beside(m, mf.iso(m[3], mf.MONTHS[m[2].lower()], int(m[1]))), text)  # fmt: skip
    return text, count, mdy


def is_kernel_text(rel: Path, path: Path) -> bool:
    """A file the kernel reads: UTF-8 by what it holds, under its cap."""
    try:
        if path.stat().st_size > kernel.MAX_FILE:
            return False
        raw = path.read_bytes()
    except OSError:
        return True  # read again by the walk, which says why it couldn't
    if b"\0" in raw[: kernel.SNIFF]:
        return False
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def mirror(folder: Path, to: Path) -> int:
    return mf.mirror_with(folder, to, mark, is_kernel_text, "day-first", "month first", every_txt=False)  # fmt: skip


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="day_first.py", description=__doc__.split("\n")[0])  # fmt: skip
    verbs = ap.add_subparsers(dest="verb", required=True)
    m = verbs.add_parser("mirror", help="write each file the kernel reads with ISO dates beside")  # fmt: skip
    m.add_argument("--from", dest="folder", required=True, type=Path)
    m.add_argument("--to", dest="to", required=True, type=Path)
    args = ap.parse_args(argv)
    return mirror(args.folder, args.to)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
