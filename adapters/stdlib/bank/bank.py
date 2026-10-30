r"""bank.py: Bank CSV and OFX statements as dated lines, with spending by month. Python 3.9+.

    python adapters/stdlib/bank/bank.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .ofx and .qfx statements and .csv files that are a bank
statement (hidden folders and files skipped; any other CSV skipped and counted)
and writes each transaction, oldest first, as a dated line, then the months:

    2024-03-02  -45.20  TESCO STORES 3241
    2024-03-05  2000.00  ACME PAYROLL

    monthly totals
    2024-03  spent 45.20  received 2000.00  net 1954.80  (2 transactions)

An OFX or QFX statement is read by its `STMTTRN` entries (date posted, amount,
name and memo), in the SGML form banks usually send or in XML. A CSV is a
statement when its header has a date column (`Date`, `Transaction Date`, `Posted
Date` or `Booking Date`), a description (`Description`, `Details`, `Memo`,
`Payee`, `Narrative` or `Name`) and either one signed `Amount` or a pair of money
out and money in columns (`Debit`/`Credit`, `Paid out`/`Paid in`, `Money
out`/`Money in`). A date is read as the kernel reads one, so a date that reads
either way round (03/04/2024) is never guessed: that row is written without a day
and is left out of the months. A negative amount is money spent. Account
numbers, balances and the rest are not copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import csv
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

DATES = ("Date", "Transaction Date", "Posted Date", "Booking Date")
NAMES = ("Description", "Details", "Memo", "Payee", "Narrative", "Name")
OUT_IN = (
    ("Debit", "Credit"),
    ("Paid out", "Paid in"),
    ("Money out", "Money in"),
    ("Withdrawals", "Deposits"),
)
LEAF = re.compile(r"<([A-Z0-9.]+)>([^<\r\n]*)")


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def amount(v: object) -> float | None:
    s = words(v).replace(",", "").replace("£", "").replace("$", "").replace("€", "")
    neg = s.startswith("(") and s.endswith(")")
    try:
        x = float(s.strip("()"))
    except ValueError:
        return None
    return -x if neg else x if x == x else None


def iso(v: object) -> str:
    d = kernel.newest(words(v)[:10])
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else ""


def from_ofx(text: str) -> list[tuple[str, float, str]]:
    out = []
    for block in re.split(r"<STMTTRN>", text)[1:]:
        block = block.split("</STMTTRN>")[0]
        fields = {k: v.strip() for k, v in LEAF.findall(block)}
        posted = re.match(r"(\d{4})(\d{2})(\d{2})", fields.get("DTPOSTED", ""))
        value = amount(fields.get("TRNAMT"))
        label = words(
            " ".join(x for x in (fields.get("NAME", ""), fields.get("MEMO", "")) if x)
        )
        if value is not None:
            out.append(("-".join(posted.groups()) if posted else "", value, label))
    return out


def from_csv(text: str) -> list[tuple[str, float, str]]:
    reader = csv.DictReader(io.StringIO(text))
    head = reader.fieldnames or []
    date_col = next((c for c in DATES if c in head), "")
    name_col = next((c for c in NAMES if c in head), "")
    pair = next((p for p in OUT_IN if p[0] in head and p[1] in head), None)
    if not (date_col and name_col and ("Amount" in head or pair)):
        return []
    out = []
    for r in reader:
        if "Amount" in head and amount(r.get("Amount")) is not None:
            value = amount(r.get("Amount"))
        elif pair:
            spent, got = amount(r.get(pair[0])), amount(r.get(pair[1]))
            value = (
                (got or 0) - abs(spent or 0)
                if spent is not None or got is not None
                else None
            )
        else:
            value = None
        if value is not None and words(r.get(name_col)):
            out.append((iso(r.get(date_col)), value, words(r.get(name_col))))
    return out


def convert(data: bytes) -> str | None:
    text = data.decode(
        "utf-8-sig", errors="replace" if b"<STMTTRN>" in data[:200000] else "strict"
    )
    rows = from_ofx(text) if "<STMTTRN>" in text else from_csv(text)
    if not rows:
        return None
    rows.sort(key=lambda r: r[0])
    lines = [
        f"{d}  {v:.2f}  {name}" if d else f"{v:.2f}  {name}" for d, v, name in rows
    ]
    months: dict[str, list[float]] = {}
    for d, v, _name in rows:
        if d:
            months.setdefault(d[:7], []).append(v)
    if months:
        lines += ["", "monthly totals"]
        for m in sorted(months):
            vs = months[m]
            spent, got = -sum(v for v in vs if v < 0), sum(v for v in vs if v > 0)
            lines.append(
                f"{m}  spent {spent:.2f}  received {got:.2f}  net {got - spent:.2f}  ({len(vs)} transaction{'s' if len(vs) != 1 else ''})"
            )
    return "\n".join(lines) + "\n"


EXTS = (".csv", ".ofx", ".qfx")
ERRORS = (OSError, UnicodeDecodeError, ValueError, csv.Error)

USAGE = "usage: bank.py mirror --from FOLDER --to MIRROR"


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
