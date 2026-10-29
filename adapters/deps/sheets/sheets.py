"""sheets.py: spreadsheets with formulas, number formats and notes kept.

    python adapters/deps/sheets/sheets.py mirror --from FOLDER --to MIRROR

Needs openpyxl (MIT), pinned in requirements.txt beside this file:

    pip install -r adapters/deps/sheets/requirements.txt

The office add-on reads a spreadsheet's stored values. This reads what a
person sees and what made it: for each .xlsx or .xlsm under FOLDER it writes
`MIRROR/<same relative path>.txt`, one passage a sheet, headed `== sheet
NAME` (`== sheet NAME (hidden)` for one hidden), one line a row, each cell
named by its address and shown as its number format shows it:

    == sheet Budget
    A1 Item | B1 Cost | C1 Due
    A2 Rent | B2 £1,200.00 | C2 2026-03-01
    A4 Total | B4 £1,450.50 =SUM(B2:B3)
    note B4 (Ana): check the deposit

A formula follows the value it last gave (the file's own cached result; a
file saved by a program that doesn't keep one shows the formula alone). A
date is written YYYY-MM-DD, whatever its format, so the kernel reads it as a
date. Notes on cells come after the rows. Macros are never run: openpyxl
doesn't run them, and this reads the file only.

The contract every file reader shares: FOLDER is walked in sorted order,
skipping hidden files and folders; nothing is written inside FOLDER and no
original is changed; MIRROR inside FOLDER, or FOLDER inside MIRROR, is
refused; the same file always gives the same bytes; a file that can't be
read (corrupt, or encrypted) is skipped and counted, never a crash.

If openpyxl isn't installed it refuses and names the install; it never skips
quietly. Exit codes, the kernel's: 0 wrote at least one file; 42 nothing
readable; 2 refused.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import sys
import warnings
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/sheets/requirements.txt"
KINDS = (".xlsx", ".xlsm")
#: a bracket in a number format: a currency [$€-407] keeps its symbol; a
#: colour, a condition or a locale ([Red], [>=100], [$-409]) shows nothing
BRACKET = re.compile(r"\[\$([^\]-]*)[^\]]*\]|\[[^\]]*\]")
QUOTED = re.compile(r'"([^"]*)"')


def plain(v: float) -> str:
    """A number as Excel's General shows it: 3, not 3.0; 0.1, not 0.1000001."""
    if float(v).is_integer() and abs(v) < 1e15:
        return str(int(v))
    return f"{v:.15g}"


def number(v: float, fmt: str) -> str:
    """`v` as the first section of number format `fmt` shows it: decimals,
    thousands, percent, a currency or other text around it, scientific. A
    negative number takes a minus whatever the format's own negative section
    says; one it can't read (fractions, a lone `@`) shows as General."""
    section = fmt.split(";")[0]
    section = BRACKET.sub(lambda m: m.group(1) or "", section)
    section = QUOTED.sub(lambda m: m.group(1).replace("0", "\0"), section)
    section = re.sub(r"_.|\*.", "", section).replace("\\", "")
    digits = re.search(r"[0#?][0#?,.]*(?:E[+-][0#]+)?%?", section)
    if not digits or "?" in digits.group(0) or "/" in section:
        return plain(v)
    pat = digits.group(0)
    head = section[: digits.start()].replace("\0", "0")
    tail = section[digits.end() :].replace("\0", "0")
    if pat.endswith("%") or "%" in tail:
        v, pat = v * 100, pat.rstrip("%")
    places = len(pat.split(".")[1].split("E")[0]) if "." in pat else 0
    if "E" in pat:
        shown = f"{abs(v):.{places}E}"
    else:  # half away from zero, as Excel rounds: 2.5 shows as 3, not 2
        d = Decimal(repr(abs(v))).quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP)
        shown = f"{d:{',' if ',' in pat.split('.')[0] else ''}.{places}f}"
    sign = "-" if v < 0 and float(shown.replace(",", "").split("E")[0]) else ""
    return f"{sign}{head}{shown}{'%' if digits.group(0).endswith('%') else ''}{tail}".strip()


def shown(v, fmt: str) -> str:
    """A cell's value as a person reads it; "" for an empty one."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, dt.datetime):
        if (v.hour, v.minute, v.second) == (0, 0, 0):
            return v.date().isoformat()
        return v.isoformat(sep=" ", timespec="seconds")
    if isinstance(v, (dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, dt.timedelta):
        return str(v)
    if isinstance(v, (int, float)):
        return plain(v) if fmt in ("General", "@", "") else number(v, fmt)
    return " ".join(str(v).split())


def formula(c) -> str:
    """The cell's formula, from `=`, or ""."""
    v = getattr(c.value, "text", c.value)  # an array formula keeps it in .text
    if c.data_type != "f" or not isinstance(v, str) or not v.strip("= "):
        return ""
    return v if v.startswith("=") else "=" + v


def as_text(path: Path) -> str:
    """Every sheet's passage, or raises: corrupt, or not a workbook."""
    import openpyxl

    with warnings.catch_warnings():  # an unknown extension is noise, not news
        warnings.simplefilter("ignore")
        made = openpyxl.load_workbook(path, data_only=False)
        gave = openpyxl.load_workbook(path, data_only=True)
    out = []
    for ws in made.worksheets:
        values = gave[ws.title]
        head = f"== sheet {ws.title}"
        if ws.sheet_state != "visible":
            head += " (hidden)"
        lines, notes = [head], []
        for row in ws.iter_rows():
            cells = []
            for c in row:
                f = formula(c)
                value = values[c.coordinate].value if f else c.value
                text = " ".join(x for x in (shown(value, c.number_format), f) if x)
                if text:
                    cells.append(f"{c.coordinate} {text}")
                if c.comment is not None and c.comment.text.strip():
                    who = f" ({c.comment.author.strip()})" if c.comment.author else ""
                    body = " ".join(c.comment.text.split())
                    notes.append(f"note {c.coordinate}{who}: {body}")
            if cells:
                lines.append(" | ".join(cells))
        out.append("\n".join(lines + notes))
    return "\n\n".join(out) + "\n"


def inside(a: Path, b: Path) -> bool:
    return a == b or b in a.parents


def mirror(src: Path, dst: Path) -> int:
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print(f"refused: sheets needs openpyxl: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = src.resolve(), dst.resolve()
    if not src.is_dir():
        print(f"refused: {src} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if inside(dst, src) or inside(src, dst):
        print(
            "refused: the mirror and the folder can't be inside each other",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote = skipped = 0
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if not p.is_file() or p.suffix.lower() not in KINDS:
            continue
        if any(part.startswith((".", "~$")) for part in rel.parts):
            continue  # ~$budget.xlsx is Excel's lock file while it's open
        try:
            text = as_text(p)
        except Exception:  # openpyxl raises many kinds for a damaged file
            skipped += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        wrote += 1
    print(f"wrote {wrote} files to {dst}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    if (
        len(argv) == 5
        and argv[0] == "mirror"
        and argv[1] == "--from"
        and argv[3] == "--to"
    ):
        return mirror(Path(argv[2]), Path(argv[4]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    os.environ.setdefault("PYTHONHASHSEED", "0")
    raise SystemExit(main(sys.argv[1:]))
