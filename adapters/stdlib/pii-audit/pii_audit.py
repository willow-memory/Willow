"""pii_audit.py: the personal numbers sitting in your files, by file and line.

    python adapters/stdlib/pii-audit/pii_audit.py --box DIR
    python adapters/stdlib/pii-audit/pii_audit.py --from FOLDER

Before a folder is shared, backed up somewhere new, or handed to a tool,
what identifying numbers are in it, each by file and line, shown masked:

    a card number        ···· 4242   money/orders.csv:17
    an NHS number        ··· 6789    health/letter.txt:3
    a National Insurance number  ····· 45C  work/p60.txt:9
    3 personal numbers in 3 of 254 files

**Every number is checked, not guessed.** A card number must pass the Luhn
check (13 to 19 digits, spaces or dashes between groups); a US Social
Security number and a UK National Insurance number their strict written
shapes, which carry no checksum, so their rows say shape, not check. An NHS
number, an Australian Medicare number and a tax file number pass their own
weighted checks AND their line must say what it holds (nhs, medicare, tfn or
tax file): one ten-digit run in ten passes such a check by luck — a chat's
timestamp, a phone — and an audit doesn't flip coins. A run that passes
nothing is nobody's number and is never listed; one that passes two checks
says both, since the digits can't say which it is. What has no checkable
shape at all — a diagnosis, an address, a name — this cannot find, and that
silence is said here so it isn't mistaken for a clean bill.

**The audit never repeats the number.** Each row shows the kind, the last
few digits, and where it sits: enough to go and deal with it, nothing worth
stealing from the audit itself.

It only reads, through the kernel's own `chunks`, so what the kernel
searches is exactly what is audited. Exit codes, the kernel's, as the
audits use them: 0 nothing found; 42 personal numbers found, or nothing
there to check; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: digit runs with optional group separators, 8 to 23 characters about
RUN = re.compile(r"(?<![\d.\w-])\d(?:[\d -]{6,21})\d(?![\d.\w-])")
SSN = re.compile(r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")
NI = re.compile(
    r"\b(?![DFIQUV])[A-Z](?![DFIQUVO])[A-Z]\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b"
)


def luhn(digits: str) -> bool:
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


#: a weighted check one run in ten passes by luck: its line must say its name
NAMED = {"an NHS number": ("nhs",), "a Medicare number": ("medicare",),
         "a tax file number": ("tfn", "tax file")}  # fmt: skip


def kinds_of(run: str, line: str = "") -> list[str]:
    """What the digit run checks out as; [] for a run that passes nothing.
    The separators are set aside, the checks are run on the digits, and a
    kind whose check is a one-in-ten coin needs its name on the line."""
    digits = re.sub(r"[ -]", "", run)
    said = line.lower()
    out = []
    if 13 <= len(digits) <= 19 and digits[0] in "23456" and luhn(digits):
        out.append("a card number")
    if len(digits) == 10 and digits[0] != "0":
        total = sum(int(d) * w for d, w in zip(digits[:9], range(10, 1, -1)))
        check = 11 - total % 11
        if check == 11:
            check = 0
        if check != 10 and check == int(digits[9]):
            out.append("an NHS number")
        weights = (1, 3, 7, 9, 1, 3, 7, 9)
        if digits[0] in "23456" and (
            sum(int(d) * w for d, w in zip(digits[:8], weights)) % 10 == int(digits[8])
        ):
            out.append("a Medicare number")
    if len(digits) == 9:
        weights = (1, 4, 3, 7, 5, 8, 6, 9, 10)
        if sum(int(d) * w for d, w in zip(digits, weights)) % 11 == 0:
            out.append("a tax file number")
    return [k for k in out
            if k not in NAMED or any(w in said for w in NAMED[k])]  # fmt: skip


def masked(run: str) -> str:
    digits = re.sub(r"[ -]", "", run)
    return "···· " + digits[-4:]


def audit(pile: list[dict]) -> list[tuple[str, str, str, int]]:
    """(kind, masked, path, line) for every checked number, in file order."""
    out = []
    for c in pile:
        for i, line in enumerate(c["text"].splitlines()):
            n = c["line"] + i
            for m in RUN.finditer(line):
                kinds = kinds_of(m.group(), line)
                if kinds:
                    out.append((" or ".join(kinds), masked(m.group()), c["path"], n))
            for m in SSN.finditer(line):
                out.append(("a Social Security number, by shape",
                            "···· " + m.group()[-4:], c["path"], n))  # fmt: skip
            for m in NI.finditer(line):
                out.append(("a National Insurance number, by shape",
                            "···· " + m.group().replace(" ", "")[-3:],
                            c["path"], n))  # fmt: skip
    return sorted(out, key=lambda r: (r[2], r[3], r[0]))


def show(found: list[tuple[str, str, str, int]], files: int) -> list[str]:
    wk = max(len(k) for k, *_ in found)
    wm = max(len(m) for _, m, *_ in found)
    out = [f"{kind:<{wk}}  {mask:<{wm}}  {path}:{n}" for kind, mask, path, n in found]
    hit = len({p for *_, p, _ in found})
    out.append(f"{len(found)} personal number{'s' if len(found) != 1 else ''}"
               f" in {hit} of {files} files")  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    given = [k for k in ("--box", "--from") if opts.get(k)]
    if len(given) != 1 or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if given == ["--box"]:
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        folder = Path(kernel.config(box)["pile"])
    else:
        folder = Path(opts["--from"])
        if not folder.is_dir():
            print(f"refused: {folder} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    pile = kernel.chunks(folder)
    files = len({c["path"] for c in pile})
    if not files:
        print("Nothing there to check.")
        return kernel.ESCALATE
    found = audit(pile)
    if not found:
        print(f"No checked number in {files} file{'s' if files != 1 else ''};"
              " what has no checkable shape, this cannot see.")  # fmt: skip
        return kernel.ALIVE
    for line in show(found, files):
        print(line)
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
