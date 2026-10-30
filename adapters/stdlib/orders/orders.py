r"""orders.py: Amazon's order history and other shops' CSV exports: what you bought, when, and for how much. Python 3.9+.

    python adapters/stdlib/orders/orders.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .csv files that are an order history (hidden folders and files
skipped; any other CSV skipped and counted) and writes each item, oldest first,
as a dated line:

    2024-03-02  Basil seeds, 3 packets  GBP 4.50  (order 026-1234567-8901234)
    2024-03-09  Garden twine  GBP 6.99  (order 026-7654321-0987654)

A file is an order history when its header has a date column (`Order Date` or
`Date`), a column that names the item (`Product Name`, `Title`, `Item` or
`Description`) and a column for what it cost (`Total Owed`, `Item Total`,
`Total`, `Amount` or `Price`), which covers Amazon's current Retail.OrderHistory
export, its older Order History Report, and the order exports of many other
shops. The first of each kind of column is used. The order number follows when
there is an `Order ID` column; the currency when there is a `Currency` column
(else the amount stands alone). The date is read as the kernel reads one, so a
date that reads either way round (03/04/24) is never guessed: that row is
written without a day. Addresses, payment cards, email addresses and the rest
are not copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

DATES = ("Order Date", "Date")
NAMES = ("Product Name", "Title", "Item", "Description")
TOTALS = ("Total Owed", "Item Total", "Total", "Amount", "Price")


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def first(head: list[str], wanted: tuple[str, ...]) -> str:
    return next((w for w in wanted if w in head), "")


def money(v: object) -> str:
    s = words(v).replace(",", "") if isinstance(v, str) else ""
    try:
        x = float(s.lstrip("$£€"))
    except ValueError:
        return ""
    return f"{x:.2f}" if x == x else ""


def convert(data: bytes) -> str | None:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    head = reader.fieldnames or []
    date_col, name_col, total_col = (
        first(head, DATES),
        first(head, NAMES),
        first(head, TOTALS),
    )
    if not (date_col and name_col and total_col):
        return None
    rows = []
    for r in reader:
        name = words(r.get(name_col))
        if not name:
            continue
        stamp = kernel.newest(words(r.get(date_col))[:10])
        when = f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:]}" if stamp else ""
        amount = money(r.get(total_col))
        cost = (
            " ".join(x for x in (words(r.get("Currency")), amount) if x)
            if amount
            else ""
        )
        order = f"(order {words(r['Order ID'])})" if words(r.get("Order ID")) else ""
        line = "  ".join(x for x in ([when] if when else []) + [name, cost, order] if x)
        rows.append((when, line))
    return (
        "\n".join(t for _w, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".csv",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, csv.Error)

USAGE = "usage: orders.py mirror --from FOLDER --to MIRROR"


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
