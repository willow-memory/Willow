"""market_calls.py: market calls kept as wagers on the record, settled by your
seal, losers and all. Python 3.9+.

    python adapters/stdlib/market-calls/market_calls.py call  --box DIR --p P [--now TS] SYMBOL up|above:PRICE DATE
    python adapters/stdlib/market-calls/market_calls.py close --box DIR [--now TS] SYMBOL DATE CLOSE PREV_CLOSE
    python adapters/stdlib/market-calls/market_calls.py score --box DIR

`call` writes a `wager` row, forecasts' own, that also names the market:
"SPY up 2026-11-06" is P that SPY closes above the close before it on that
day; "SPY above:580 2026-11-06" is P that it closes above 580. One call per
question: a second one on the same symbol, kind and day is refused, so you
can't hold both sides. It must be made before 13:00 UTC on the close date, by
the record's own time; that is as honest as the clock --now gives it, so keep
a tip-pin from before the market opens if the timing must be shown.

`close` writes the day's closes, as you read them, in a `close` row, then
proposes each open call's outcome on that symbol and day through forecasts'
`settle`: the kernel's own door, waiting on your seal. Code never settles a
call. A second close for the same symbol and day must say the same prices.

`score` lists every call, settled, waiting or open, and whether it was right,
the losers kept; then the Brier score over the settled ones. It writes
nothing. Paper only: nothing here trades or fetches a price.

Exit codes, the kernel's: `call` 0; `close` 42 when an outcome waits on your
seal, 0 when no call was open; `score` 0, or 42 when a call waits on your seal
or nothing is settled yet; 2 refused.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "forecasts"))
import forecasts  # noqa: E402
import kernel  # noqa: E402

WHO = "market-calls"
DEADLINE = "T13:00:00Z"  # a call is made before this on its close date
_SYMBOL = re.compile(r"[A-Z0-9^][A-Z0-9.^=-]{0,14}")


def day(text: str) -> str | None:
    try:
        return date.fromisoformat(text).isoformat() if len(text) == 10 else None
    except ValueError:
        return None


def price(text: str) -> str | None:
    """A positive finite price as a decimal string, so a comparison is exact."""
    try:
        d = Decimal(text)
    except InvalidOperation:
        return None
    return str(d) if d.is_finite() and d > 0 else None


def market_of(symbol: str, kind: str, close_date: str) -> dict | None:
    if not _SYMBOL.fullmatch(symbol) or day(close_date) is None:
        return None
    if kind == "up":
        return {"symbol": symbol, "kind": "up", "close_date": close_date}
    if kind.startswith("above:") and price(kind[6:]):
        return {"symbol": symbol, "kind": "above", "threshold": price(kind[6:]),
                "close_date": close_date}  # fmt: skip
    return None


def claim_of(m: dict) -> str:
    kind = "up" if m["kind"] == "up" else f"above:{m['threshold']}"
    return f"{m['symbol']} {kind} {m['close_date']}"


def answer(m: dict, close: str, prev_close: str) -> bool:
    if m["kind"] == "up":
        return Decimal(close) > Decimal(prev_close)
    return Decimal(close) > Decimal(m["threshold"])


def calls(rows: list[dict]) -> list[dict]:
    return [
        r for r in rows if r["kind"] == "wager" and isinstance(r.get("market"), dict)
    ]


def closes(rows: list[dict], symbol: str, close_date: str) -> list[dict]:
    return [r for r in rows if r["kind"] == "close" and r.get("symbol") == symbol
            and r.get("close_date") == close_date]  # fmt: skip


def verdict(p: float, happened: bool) -> str:
    """A call over even odds was right when it happened, one under when it
    didn't; a call at even odds called nothing."""
    if p == 0.5:
        return "even"
    return "right" if (p > 0.5) == happened else "wrong"


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


# ── the verbs ───────────────────────────────────────────────────────────────
def call(box: Path, rows: list[dict], p: float, m: dict, ts: str) -> int:
    if ts >= m["close_date"] + DEADLINE:
        return refuse(f"a call on {m['close_date']} is made before 13:00 UTC that "
                      "day; this is after, and the market may be known")  # fmt: skip
    if closes(rows, m["symbol"], m["close_date"]):
        return refuse(f"{m['symbol']} on {m['close_date']} has closed on the record")
    if any(r["market"] == m for r in calls(rows)):
        return refuse(f"{claim_of(m)} is called already; one call per question")
    claim = claim_of(m)
    row = kernel.append(box, ts, "wager", who=WHO, p=p, claim=kernel.h256(claim),
                        market=m)  # fmt: skip
    print(f"call row {row['n']}: {claim}, p {p:g}")
    print(f"  close it:  market_calls.py close --box {box} {m['symbol']} "
          f"{m['close_date']} CLOSE PREV_CLOSE")  # fmt: skip
    return kernel.ALIVE


def close(box: Path, rows: list[dict], symbol: str, close_date: str, c: str,
          prev: str, ts: str) -> int:  # fmt: skip
    seen = closes(rows, symbol, close_date)
    same = (Decimal(c), Decimal(prev))
    if any((Decimal(r["close"]), Decimal(r["prev_close"])) != same for r in seen):
        return refuse(f"{symbol} on {close_date} closed at {seen[0]['close']} "
                      f"(before: {seen[0]['prev_close']}) by row {seen[0]['n']}; "
                      "two closes for one day")  # fmt: skip
    if not seen:
        kernel.append(box, ts, "close", who=WHO, symbol=symbol,
                      close_date=close_date, close=c, prev_close=prev)  # fmt: skip
    print(f"{symbol} closed {c} on {close_date} (before: {prev})")
    told = forecasts.outcomes(box, kernel.read(box / "record.jsonl")[0])
    code = kernel.ALIVE
    for w in calls(rows):
        m = w["market"]
        if (m["symbol"], m["close_date"]) != (symbol, close_date):
            continue
        if told[w["n"]]["state"] != "open":
            print(f"  row {w['n']} {claim_of(m)}: {told[w['n']]['state']}")
            continue
        happened = answer(m, c, prev)
        now, _ = kernel.read(box / "record.jsonl")
        got, said = forecasts.quiet(forecasts.settle, box, now, w["n"], happened, ts)
        if got != kernel.ESCALATE:
            print(said.strip(), file=sys.stderr)
            return kernel.REFUSED
        print(f"  row {w['n']} {claim_of(m)}: " + said.strip().replace("\n", "\n  "))
        code = kernel.ESCALATE
    return code


def score(box: Path, rows: list[dict]) -> int:
    mine = calls(rows)
    if not mine:
        print("no market calls yet: call first, close after")
        return kernel.ESCALATE
    told = forecasts.outcomes(box, rows)
    pairs, waiting = [], 0
    for w in mine:
        t = told[w["n"]]
        if t["state"] == "settled":
            pairs.append((w["p"], t["happened"]))
            said = verdict(w["p"], t["happened"])
        else:
            said = t["state"]
            waiting += t["state"] == "waiting"
        print(f"{said:<11} row {w['n']}  {claim_of(w['market'])}  p {w['p']:g}")
    if any(told[w["n"]]["state"] in ("broken", "conflicting") for w in mine):
        return kernel.REFUSED
    if not pairs:
        print("nothing settled yet: a call counts once you seal its outcome")
        return kernel.ESCALATE
    b = sum(forecasts.brier(p, o) for p, o in pairs) / len(pairs)
    right = sum(verdict(p, o) == "right" for p, o in pairs)
    print(f"{right} of {len(pairs)} settled calls right, Brier {b:.3f}")
    return kernel.ESCALATE if waiting else kernel.ALIVE


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("call", "close", "score"):
        return usage()
    verb, opts, words = argv[0], {}, []
    it = iter(argv[1:])
    for a in it:
        if a in ("--box", "--now", "--p"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            return usage()
        else:
            words.append(a)
    if not opts.get("--box") or any(not v for v in opts.values()):
        return usage()
    want = {"call": 3, "close": 4, "score": 0}[verb]
    if len(words) != want or ("--p" in opts) != (verb == "call"):
        return usage()
    if verb == "score" and "--now" in opts:
        return usage()
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        return refuse("not a kernel box; init first")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse(f"the record doesn't verify ({breaks[0]}); a person looks first")
    ts = opts.get("--now") or kernel.now()
    if verb == "score":
        return score(box, rows)
    if verb == "close":
        symbol, close_date, c, prev = words
        if (not _SYMBOL.fullmatch(symbol) or day(close_date) is None
                or price(c) is None or price(prev) is None):  # fmt: skip
            return usage()
        return close(box, rows, symbol, close_date, price(c), price(prev), ts)
    try:
        p = float(opts["--p"])
    except ValueError:
        return usage()
    m = market_of(*words)
    if m is None or not forecasts.LOW <= p <= forecasts.HIGH:
        return usage()
    return call(box, rows, p, m, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
