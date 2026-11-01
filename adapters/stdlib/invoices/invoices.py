"""invoices.py: the invoices you sent, matched to payments by their number, never guessed.

    python adapters/stdlib/invoices/invoices.py --box DIR --id PATTERN [--now TS]

PATTERN is how your invoice numbers are written, as a regular expression
(`INV-\\d+`, say). An invoice is known by its number, from either:

- a CSV ledger row that holds it, read by its columns in any case: an
  amount (`amount`, `amount_gbp`, `total`), `due`, `client` or `customer`,
  and a paid date (`paid`, `paid_on`) or a `status` of paid; or
- a file whose name holds it (`INV-0427_bramble.txt`), read by its lines:
  `Total` with a sum, `Payment due` or `Due` with a date, and `Bill to`.

It is paid only when a line that names its number says so: a paid date or
status in its ledger row, or any other line with the number and a word of
payment (paid, received, remittance, settled) and none of not paid
(unpaid, outstanding, overdue, owed, chase). No amount, payee or date ever
matches a payment to an invoice. The rest are listed, overdue first:

    overdue  INV-0427  Bramble & Bean Ltd  £680.00  due 2026-07-30, 84 days ago
             invoice   work/invoices/invoice_ledger.csv:228
             last said email/2026-10-06_outstanding-invoices.eml:11
    not due  INV-0440  Fernside Dog Grooming  £173.25  due 2026-10-30, in 8 days

Then, for an unpaid one, any bank credit (through the bank add-on) or line
of a file that speaks of payment, with the same sum, on or after the
invoice's date, that names no invoice at all, under a heading that says to
check it by hand: a client who pays without quoting your number is shown,
never counted as paid.

    114 invoices: 108 paid, 4 overdue (£2,660.00), 2 not due (£731.00).

An unpaid invoice due before the first bank statement in your folder can't
be shown paid either way, so it isn't called overdue: it is named on one line
of its own, and no payments are listed for it.

A date is read as the kernel reads one, so a due date that reads either way
round (09/11/2026) is not guessed: that invoice says "due date unread".

It only reads. Exit codes, the kernel's: 0 invoices found; 42 none named by
PATTERN; 2 refused.
"""

from __future__ import annotations

import csv
import io
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "bank"))
sys.path.insert(0, str(HERE.parent / "amounts"))
import amounts  # noqa: E402
import bank  # noqa: E402
import kernel  # noqa: E402

USAGE = "usage: invoices.py --box DIR --id PATTERN [--now TS]"
PAID = re.compile(r"\b(paid|received|remittance|settled)\b", re.I)
UNPAID = re.compile(r"\b(unpaid|not paid|outstanding|overdue|owed|owing|chase)\b", re.I)
AMOUNT_COLS = ("amount", "total")
PAID_COLS = ("paid", "paid_on", "paid on", "date paid")
WHO_COLS = ("client", "customer", "bill to")


def day(text: str) -> str:
    """YYYY-MM-DD for the date a text says, or "" (the kernel's reading)."""
    d = kernel.newest(text or "")
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else ""


SYMBOL = re.compile(r"([$£€¥₹])\s+(?=\d)")
CODES = {"gbp": "£", "usd": "$", "eur": "€"}


def currency(text: str) -> str:
    """The symbol a sum or a column name is written in, or ""."""
    m = re.search(r"[$£€¥₹]", text or "")
    if m:
        return m.group()
    low = (text or "").lower()
    return next((s for code, s in CODES.items() if code in low), "")


def money(text: str) -> float | None:
    """The last sum a text writes (a symbol may stand apart from its number,
    as in an invoice's right-aligned column), or a bare number written alone."""
    text = SYMBOL.sub(r"\1", text or "")
    found = amounts.sums(text)
    if found:
        return bank.amount(found[-1])
    return (
        bank.amount(text)
        if text and re.fullmatch(r"[£$€]?\s*[\d,]+(\.\d\d)?", text.strip())
        else None
    )


def sum_of(rec: dict) -> str:
    return f"{rec.get('cur', '')}{rec['amount']:,.2f}"


def total(recs: list[dict]) -> str:
    """The sums added up, one figure for each currency they are written in."""
    by: dict[str, float] = {}
    for r in recs:
        if "amount" in r:
            by[r.get("cur", "")] = by.get(r.get("cur", ""), 0) + r["amount"]
    return " + ".join(f"{c}{v:,.2f}" for c, v in sorted(by.items())) or "0.00"


def texts(pile: Path) -> list[tuple[str, list[str]]]:
    """(relative path, lines) for each readable text file, hidden ones left out."""
    out = []
    for p in sorted(pile.rglob("*")):
        rel = p.relative_to(pile)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        try:
            raw = p.read_bytes()
            if b"\0" in raw[: kernel.SNIFF]:
                continue
            out.append((rel.as_posix(), raw.decode("utf-8-sig").splitlines()))
        except (OSError, UnicodeDecodeError):
            continue
    return out


def column(header: dict[str, str], names: tuple[str, ...]) -> str | None:
    """The header as written for the first name it has, in any case; for an
    amount, a column that starts with the name (amount_gbp) counts too."""
    for n in names:
        if n in header:
            return header[n]
    for n in names:
        for low, real in header.items():
            if names is AMOUNT_COLS and low.startswith(n):
                return real
    return None


def ledgers(files, pattern) -> dict[str, dict]:
    """Invoices from CSV rows that hold a number."""
    found: dict[str, dict] = {}
    for path, lines in files:
        if not path.lower().endswith(".csv"):
            continue
        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        header = {h.strip().lower(): h for h in reader.fieldnames or [] if h}
        amt, who = column(header, AMOUNT_COLS), column(header, WHO_COLS)
        due, paid, status = (
            header.get("due"),
            column(header, PAID_COLS),
            header.get("status"),
        )
        issued = header.get("invoice date") or header.get("date")
        statement = bool(bank.from_csv("\n".join(lines)))
        for row in reader:
            ids = {
                m.group()
                for v in row.values()
                if isinstance(v, str)
                for m in pattern.finditer(v)
            }
            if len(ids) != 1:
                continue
            (inv,) = ids
            rec = found.setdefault(inv, {"id": inv})
            if statement:  # a bank statement: money in that names it pays it
                value = money(row.get(amt)) if amt else None
                if value is not None and value > 0:
                    rec.setdefault(
                        "paid",
                        (day(row.get(issued) or ""), f"{path}:{reader.line_num}"),
                    )
                continue
            rec["where"] = f"{path}:{reader.line_num}"
            if amt and money(row.get(amt)) is not None:
                rec["amount"] = money(row.get(amt))
                rec["cur"] = currency(row.get(amt)) or currency(amt)
            if who and (row.get(who) or "").strip():
                rec["who"] = row[who].strip()
            if due and day(row.get(due)):
                rec["due"] = day(row.get(due))
            if issued and day(row.get(issued)):
                rec["issued"] = day(row.get(issued))
            when = day(row.get(paid)) if paid else ""
            if when or (status and (row.get(status) or "").strip().lower() == "paid"):
                rec["paid"] = (when or "date not written", f"{path}:{reader.line_num}")
    return found


def from_files(files, pattern, found) -> None:
    """Invoices from files named for their number, by their own lines."""
    for path, lines in files:
        ids = {m.group() for m in pattern.finditer(Path(path).name)}
        if len(ids) != 1 or path.lower().endswith(".csv"):
            continue
        (inv,) = ids
        rec = found.setdefault(inv, {"id": inv})
        rec.setdefault("where", path)
        net = None
        for n, line in enumerate(lines):
            low = line.lower()
            terms = re.search(
                r"\bnet ?(\d{1,3})\b|\b(?:due|payable) within (\d{1,3}) days\b", low
            )
            if terms:
                net = int(terms.group(1) or terms.group(2))
            if "total" in low and "amount" not in rec and money(line) is not None:
                rec["amount"] = money(line)
                rec["cur"] = currency(line)
            elif re.search(r"\bdue\b", low) and "due" not in rec and day(line):
                rec["due"] = day(line)
            elif (re.search(r"\b(invoice date|date of issue|issued)\b", low)
                  or low.strip().startswith("date:")) and day(line):  # fmt: skip
                rec.setdefault("issued", day(line))
            elif low.strip().startswith("bill to") and "who" not in rec:
                said = line.split(":", 1)[-1].strip()
                after = next((x.strip() for x in lines[n + 1 :] if x.strip()), "")
                rec["who"] = said or after
        if "due" not in rec and net is not None and rec.get("issued"):
            rec["due"] = (
                date.fromisoformat(rec["issued"]) + timedelta(days=net)
            ).isoformat()
            rec["terms"] = f"net {net}"


def mentions(files, pattern, found) -> None:
    """Other lines naming one number: a payment if they say so, else the latest
    word on it."""
    for path, lines in files:
        if path.lower().endswith(".csv"):
            continue
        own = {m.group() for m in pattern.finditer(Path(path).name)}
        for n, line in enumerate(lines, 1):
            ids = {m.group() for m in pattern.finditer(line)} - own
            for inv in ids & set(found):
                rec, where = found[inv], f"{path}:{n}"
                if len(ids) == 1 and PAID.search(line) and not UNPAID.search(line):
                    rec.setdefault(
                        "paid", (day(line) or day(path) or "date not written", where)
                    )
                when = day(line) or day(path) or ""
                if when >= rec.get("said", ("", ""))[0]:
                    rec["said"] = (when, where)


def same_sum(files, pattern, rec) -> list[str]:
    """Lines and bank credits of the invoice's sum that name no invoice."""
    out, since = [], rec.get("issued", "")
    for path, lines in files:
        if path.lower().endswith(".csv"):
            for when, value, payee in bank.from_csv("\n".join(lines)):
                if (value > 0 and abs(value - rec["amount"]) < 0.005 and when >= since
                        and not pattern.search(payee)):  # fmt: skip
                    out.append(f"{path}  {when}  {value:.2f}  {payee}")
            continue
        if pattern.search(Path(path).name) or not any(PAID.search(ln) for ln in lines):
            continue  # an invoice's own file, or one that speaks of no payment
        if (day(path) or "9999") < since:
            continue
        for n, line in enumerate(lines, 1):
            if pattern.search(line):
                continue
            if any(
                abs((bank.amount(s) or -1) - rec["amount"]) < 0.005
                for s in amounts.sums(line)
            ):
                out.append(f"{path}:{n}  {' '.join(line.split())[:70]}")
    return out


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if len(argv) % 2 or not {"--box", "--id"} <= set(opts) <= {
        "--box",
        "--id",
        "--now",
    }:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        pattern = re.compile(opts["--id"])
    except re.error as e:
        print(f"refused: --id is not a pattern ({e})", file=sys.stderr)
        return kernel.REFUSED
    if pattern.search(""):
        print(
            "refused: --id matches nothing at all; give the shape of a number",
            file=sys.stderr,
        )
        return kernel.REFUSED
    now = day(opts.get("--now", "")) or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    files = texts(Path(kernel.config(box)["pile"]))
    found = ledgers(files, pattern)
    from_files(files, pattern, found)
    mentions(files, pattern, found)
    if not found:
        print(f"no invoice in your folder is numbered like {opts['--id']}")
        return kernel.ESCALATE
    open_, paid = [], 0
    for rec in found.values():
        if "paid" in rec:
            paid += 1
        else:
            open_.append(rec)
    first = min((when for path, lines in files if path.lower().endswith(".csv")
                 for when, *_ in bank.from_csv("\n".join(lines)) if when), default="")  # fmt: skip
    unproven = sorted(
        (r for r in open_ if first and r.get("due") and r["due"] < first),
        key=lambda r: (r["due"], r["id"]),
    )
    open_ = [r for r in open_ if r not in unproven]
    late = sorted(
        (r for r in open_ if r.get("due") and r["due"] < now),
        key=lambda r: (r["due"], r["id"]),
    )
    later = sorted(
        (r for r in open_ if r not in late),
        key=lambda r: (r.get("due") or "9999", r["id"]),
    )
    for rec in late + later:
        state = "overdue" if rec in late else "not due"
        amt = sum_of(rec) if "amount" in rec else "no sum written"
        if rec.get("due"):
            gap = (date.fromisoformat(now) - date.fromisoformat(rec["due"])).days
            when = f"due {rec['due']}, " + (
                f"{gap} days ago"
                if gap > 0
                else f"in {-gap} days"
                if gap < 0
                else "today"
            )
        else:
            when = "due date unread"
        print(
            f"{state:<8} "
            + "  ".join(x for x in (rec["id"], rec.get("who", ""), amt, when) if x)
        )
        print(f"{'':<8} invoice   {rec['where']}")
        if rec.get("said"):
            print(f"{'':<8} last said {rec['said'][1]}")
    checks = [(r, same_sum(files, pattern, r)) for r in late + later if "amount" in r]
    checks = [(r, hits) for r, hits in checks if hits]
    if checks:
        print(
            "\nsame sum, no invoice named: check these by hand, never counted as paid"
        )
        for rec, hits in checks:
            for h in hits[:3]:
                print(f"  {rec['id']}  {sum_of(rec)}  {h}")
    if unproven:
        print(f"\ndue before your first bank statement ({first}), so nothing here can show "
              f"them paid: {len(unproven)} ({total(unproven)}), "
              f"{', '.join(r['id'] for r in unproven)}")  # fmt: skip
    print(f"\n{len(found)} invoices: {paid} paid, {len(late)} overdue ({total(late)}), "
          f"{len(later)} not due ({total(later)})"
          + (f", {len(unproven)} before your statements." if unproven else "."))  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
