"""Code finds and ranks; a small model only phrases. A "this week" note.

    python ranked.py URL MODEL PERSON NOW OUT.json

Rules about kinds of fact, not about any one person:

1. Owed to you. A CSV ledger with a `client` column lists invoices you
   issued. A row with no paid date, past its due date, is unpaid unless the
   bank (read by the bank add-on) shows a credit of the same amount, from a
   payee sharing a name word with the client, on or after the invoice date.
   Summed per client; the newest email naming those invoices is the last
   chaser.
2. Renewing. A yearly payment (subscriptions add-on) due within 14 days.
3. Dated. Anything coming-up lists within 14 days.

Each fact is one line saying plainly who owes whom, with its sources, and
the facts are numbered in that order. The model writes 3 to 6 points from
them, citing [n]; a point with no words, citing nothing, or whose cited
facts hold under half its words, is struck.
"""

import csv
import json
import re
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402
from assemble import ask, parse  # noqa: E402

AHEAD = 14
LEDGER = {}  # invoice id -> {client, amount, paid}, filled by owed_to_you
SYSTEM = (
    "You write short, plain notes for a person from facts about their own files."
    " Use only the numbered facts, keep who owes whom exactly as each fact says,"
    " and reply with JSON only."
)
WRITE = (
    "Today is {today}. Write {who} a note: what needs her attention this week,"
    " in the order the facts are given (most urgent first), 3 to 6 points, each one"
    " short sentence that says what to do. End every point with the facts it rests"
    " on, like [1] or [2, 3].\n\nFacts:\n{facts}\n\n"
    'Reply as JSON: {{"points": ["... [n]", ...]}}'
)


def name_words(s):
    return {w for w in kernel.words(s) if len(w) > 2} - {"ltd", "and", "the", "limited"}


def bank_credits(life, tmp):
    out = tmp / "bank"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters/stdlib/bank/bank.py"),
            "mirror",
            "--from",
            str(life),
            "--to",
            str(out),
        ],
        capture_output=True,
    )
    credits = []
    for f in sorted(out.rglob("*.txt")) if out.exists() else []:
        for ln in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"(\d{4}-\d{2}-\d{2})\s+(-?\d+\.\d\d)\s+(.+)", ln)
            if m and float(m.group(2)) > 0:
                credits.append((m.group(1), float(m.group(2)), m.group(3)))
    return credits


def owed_to_you(life, today, tmp):
    credits = bank_credits(life, tmp)
    facts = []
    for ledger in sorted(life.rglob("*.csv")):
        with ledger.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows or not {"client", "due"} <= {k.lower() for k in rows[0]}:
            continue
        col = {k.lower(): k for k in rows[0]}
        amount_col = next((col[k] for k in col if k.startswith("amount")), None)
        paid_col = next((col[k] for k in col if k.startswith("paid")), None)
        unpaid = {}
        for i, r in enumerate(rows, 2):
            if col.get("invoice"):
                LEDGER[r[col["invoice"]]] = {
                    "client": r[col["client"]],
                    "amount": r[amount_col] if amount_col else "",
                    "paid": bool(paid_col and r[paid_col].strip()),
                }
            due = r[col["due"]]
            if (
                (paid_col and r[paid_col].strip())
                or not due
                or due >= today.isoformat()
            ):
                continue
            amt = float(r[amount_col])
            issued = r.get(col.get("date", ""), "") or ""
            who = name_words(r[col["client"]])
            if any(
                abs(a - amt) < 0.005 and d >= issued and who & name_words(p)
                for d, a, p in credits
            ):
                continue  # the bank shows it paid, by name and amount
            limit = (
                (date.fromisoformat(issued) + timedelta(60)).isoformat()
                if issued
                else "9999"
            )
            maybe = [
                (d, p)
                for d, a, p in credits
                if abs(a - amt) < 0.005 and issued <= d <= limit
            ]
            inv = r.get(col.get("invoice", ""), "")
            unpaid.setdefault(r[col["client"]], []).append((inv, amt, due, i, maybe))
        rel = ledger.relative_to(life)
        for client, all_items in unpaid.items():
            for inv, amt, due, i, maybe in all_items:
                if maybe:
                    d, p = maybe[0]
                    facts.append(
                        (
                            0,
                            0,
                            f"POSSIBLY PAID: your invoice {inv} to {client} (£{amt:,.2f},"
                            f" due {due}) has no paid date, but a credit of £{amt:,.2f} from"
                            f" {p} arrived on {d}. Check before chasing it."
                            f" Source: {rel} row {i}; your bank statements.",
                        )
                    )
            items = [x for x in all_items if not x[4]]
            if not items:
                continue
            total = sum(a for _, a, *_ in items)
            oldest = min(d for _, _, d, *_ in items)
            days = (today - date.fromisoformat(oldest)).days
            ids = [inv for inv, *_ in items if inv]
            chasers = sorted(
                p
                for p in life.rglob("*")
                if p.is_file()
                and p.suffix != ".csv"
                and not any(i.lower() in p.name.lower() for i in ids)
                and any(
                    i in p.read_text(encoding="utf-8", errors="replace") for i in ids
                )
            )
            last = chasers[-1].relative_to(life) if chasers else None
            detail = ", ".join(f"{inv} £{a:,.2f} due {d}" for inv, a, d, *_ in items)
            facts.append(
                (
                    0,
                    -total,
                    f"OWED TO YOU: {client} owes you £{total:,.2f} on {len(items)} invoice(s)"
                    f" you sent ({detail}); the oldest is {days} days overdue."
                    + (
                        f" Your last reminder: {last}."
                        if last
                        else " You have not chased it."
                    )
                    + f" Source: {rel} rows {', '.join(str(x[3]) for x in items)}.",
                )
            )
    return facts


def renewing(box, today):
    out = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters/stdlib/subscriptions/subscriptions.py"),
            "--box",
            str(box),
        ],
        capture_output=True,
        text=True,
    ).stdout
    facts = []
    for ln in out.splitlines():
        m = re.match(
            r"(.+?)\s+([\d,]+\.\d\d)\s+yearly\s+last (\S+)\s+next about (\S+)", ln
        )
        if (
            m
            and today.isoformat()
            <= m.group(4)
            <= (today + timedelta(AHEAD)).isoformat()
        ):
            facts.append(
                (
                    1,
                    m.group(4),
                    f"RENEWS: a yearly payment of £{m.group(2)} to {m.group(1).strip().upper()}"
                    f" is due about {m.group(4)} (last paid {m.group(3)}); check it will go through."
                    f" Source: your bank statements, via subscriptions.",
                )
            )
    return facts


def dated(box, now, today):
    out = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters/stdlib/coming-up/coming_up.py"),
            "--box",
            str(box),
            "--now",
            now,
        ],
        capture_output=True,
        text=True,
    ).stdout
    facts, seen = [], set()
    for ln in out.splitlines():
        m = re.match(r"(\d{4}-\d{2}-\d{2})\s+(\S+?:\d+)\s+(.*)", ln.strip())
        if not m or not m.group(1) <= (today + timedelta(AHEAD)).isoformat():
            continue
        what = (
            re.sub(r"\b(DTSTART|DTEND)\S*\s*", "", m.group(3))
            .replace("SUMMARY:", "")
            .strip()
        )
        src = m.group(2).split(":")[0]
        if src.endswith(".csv") and "invoice" in src.lower():
            continue  # a ledger row: the invoice's own file says it better
        inv = re.search(r"INV-\d+", src)
        if inv:
            row = LEDGER.get(inv.group(0))
            if row and row["paid"]:
                continue
            facts.append(
                (
                    2,
                    m.group(1),
                    f"AN INVOICE YOU SENT FALLS DUE: {inv.group(0)} to"
                    f" {row['client'] if row else 'a client'}"
                    + (f" (£{row['amount']})" if row else "")
                    + f" is due to be paid to you on {m.group(1)}. Source: {m.group(2)}.",
                )
            )
            continue
        key = (what, src)
        if key in seen:
            continue
        seen.add(key)
        facts.append(
            (2, m.group(1), f"DATE: {m.group(1)}: {what}. Source: {m.group(2)}.")
        )
    return facts


def main(url, model, person, now, outp):
    today = date.fromisoformat(now[:10])
    life = ROOT / "demo" / person / "life"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        box = tmp / "box"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "kernel.py"),
                "init",
                "--box",
                str(box),
                "--pile",
                str(life),
                "--key",
                str(tmp / "key"),
                "--now",
                now,
            ],
            capture_output=True,
            check=True,
        )
        found = (
            owed_to_you(life, today, tmp)
            + renewing(box, today)
            + dated(box, now, today)
        )
    facts = [f for *_, f in sorted(found, key=lambda x: (x[0], x[1]))]
    print("[facts]")
    for i, f in enumerate(facts, 1):
        print(f"  [{i}] {f}")
    who = {"teodora": "Teo"}.get(person, person)
    body = "\n".join(f"[{i}] {f}" for i, f in enumerate(facts, 1))
    text, secs = ask(
        url, model, SYSTEM, WRITE.format(today=now[:10], who=who, facts=body), 700
    )
    points = [
        p for p in ((parse(text) or {}).get("points") or []) if isinstance(p, str)
    ]
    note, struck = [], []
    for p in points:
        cites = [
            int(x)
            for m in re.findall(r"\[([\d,\s]+)\]", p)
            for x in re.split(r"[,\s]+", m)
            if x
        ]
        want = set(kernel.words(re.sub(r"\[[\d,\s]+\]", "", p))) - kernel.FUNCTION
        have = set(
            kernel.words(" ".join(facts[c - 1] for c in cites if 1 <= c <= len(facts)))
        )
        if not cites:
            struck.append((p, "cites nothing"))
        elif not want:
            struck.append((p, "says nothing but its citation"))
        elif any(not 1 <= c <= len(facts) for c in cites):
            struck.append((p, "cites a fact that isn't there"))
        elif len(want & have) < len(want) / 2:
            struck.append(
                (p, f"its facts hold {len(want & have)} of its {len(want)} words")
            )
        else:
            note.append(p)
    print(f"\n[write] {secs}s: {len(note)} points kept, {len(struck)} struck\n")
    for p in note:
        print("•", p)
    for p, why in struck:
        print("✗ struck:", p, "—", why)
    Path(outp).write_text(
        json.dumps(
            {
                "model": model,
                "person": person,
                "now": now,
                "facts": facts,
                "raw": text,
                "note": note,
                "struck": struck,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n"
    )


if __name__ == "__main__":
    main(*sys.argv[1:6])
