"""game_canon.py: what a game's table holds true, and what a new word meets of it. Python 3.9+.

    python adapters/stdlib/game-canon/game_canon.py --box DIR holds [--json]
    python adapters/stdlib/game-canon/game_canon.py --box DIR tonight [--json]
    python adapters/stdlib/game-canon/game_canon.py --box DIR meets FACT [--subject SUBJECT] [--json]
    python adapters/stdlib/game-canon/game_canon.py --box DIR replace --old SUBJECT --new SUBJECT --fact FACT [--now TS]
    python adapters/stdlib/game-canon/game_canon.py --box DIR take-back --old SUBJECT [--now TS]
    python adapters/stdlib/game-canon/game_canon.py --box DIR both --old SUBJECT --new SUBJECT --fact FACT [--now TS]

What the table holds true is every call and every offer of game-master's, in
every game on the record, that the person sealed, unless a sealed replacement
stands over it. `holds` lists them, `tonight` those since the last session
ended.

`meets` is the heads-up before the game master decides: what the table holds
true that FACT is about the same thing as, by contradictions' own rule (the
two share at least two of their own words, and at least half the shorter
one's). It can't tell whether they disagree and never picks a side: it only
says, and the person decides. Not raised: FACT itself, the same words made
true again, and a pair the person said are both true.

What the person chooses is kept, and nothing here chooses. The rows are
[table](../table/)'s own, `table-replaces` and `table-both` in its shape, read
by its rule, so one record holds a game's calls and a table's words and one
replacement or one "both" reads the same at either:

- **Mine stands now:** `replace` hands in, through the kernel's own bite and
  propose, a proposal that the new word stands in place of the old, and
  writes a `table-replaces` row naming it. Then it waits, exit 42: the old one
  stops standing only when the person seals that proposal with
  `kernel.py seal`. The old one stays on the record.
- **A yes taken back:** `take-back` is a replacement whose new word is
  nothing, waiting on the person's seal the same way; nothing takes a seal
  back, this stands over it.
- **Both are true:** `both` writes a `table-both` row, so the pair isn't
  raised again. It changes no truth, so it is a row and no seal.

Exit codes, the kernel's: 0 done; 42 waiting on your seal; 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(STDLIB / "game-master"))
sys.path.insert(0, str(STDLIB / "table"))
import game_master as gm  # noqa: E402
import kernel  # noqa: E402
import table  # noqa: E402  the rows are the table's, read by its rule

REPLACES, BOTH, SLIP = table.REPLACES, table.BOTH, table.SLIP
WHO = "game-canon"
USAGE = __doc__.split("\n\n")[1]


def refuse(why: str) -> int:
    print(f"game-canon: {why}", file=sys.stderr)
    return kernel.REFUSED


def replaced(box: Path, rows: list[dict]) -> dict:
    """{the old subject: the replacing row} for every replacement the person
    sealed: the table's own reading of its `table-replaces` rows."""
    return table.replaced(box, rows)


def standing(box: Path, rows: list[dict]) -> list[dict]:
    """Everything the table holds true now, in every game: each sealed call
    and each sealed offer, unless a sealed replacement says it was replaced.
    {subject, fact, n (the seal's row), day}, oldest first."""
    gone = set(replaced(box, rows))
    out = []
    for g in gm.games(rows):
        for a in g["asks"] + g["offers"]:
            what, got = gm.ruling(box, rows, a["subject"])
            if what == "sealed" and a["subject"] not in gone:
                out.append({"subject": a["subject"], "fact": a["fact"], "n": got["n"], "day": got["ts"][:10]})  # fmt: skip
    return sorted(out, key=lambda t: t["n"])


def both(rows: list[dict]) -> set:
    """The pairs of words the person said are both true, by their words: the
    same two said again (a story played again) aren't raised again."""
    return {frozenset(r["facts"]) for r in rows if r["kind"] == BOTH}


def meets(box: Path, fact: str, subject: str = "") -> list[dict]:
    """What the table holds true that FACT is about the same thing as, by the
    table's own heads-up over a game's calls and offers: not itself, not the
    same words made true again, and not a pair the person already said are
    both true."""
    rows, _ = kernel.read(box / "record.jsonl")
    return table.meets(box, rows, fact, subject, among=standing(box, rows))


def tonight(box: Path, rows: list[dict]) -> list[dict]:
    """What the table made true since the last session ended, still standing,
    oldest first."""
    after = table.last_end(rows)
    return [t for t in standing(box, rows) if t["n"] > after]


def replace(box: Path, ts: str, old: dict, new_subject: str, new_fact: str) -> str:
    """The person's "mine stands now": a replacement handed in, in the table's
    shape, and its subject, waiting on their seal. Unlike the table's own,
    which a host types at its terminal and seals, this seals nothing.
    RuntimeError with the kernel's words if it won't take it."""
    tail = old["subject"].split(":")[-1][:16]
    claim = f"From now on this stands in place of what the table made true on {old['day']}: {old['fact']}"  # fmt: skip
    prop = {"path": f"table/replaces/{ts[:10]}-{tail}.md", "data": new_fact + "\n",
            "cites": [], "claim": claim}  # fmt: skip
    try:
        subject = table.hand_in(box, ts, f"game-canon replaces {old['subject']}", prop)
    except table.Refused as e:
        raise RuntimeError(str(e)) from None
    kernel.append(box, ts, REPLACES, who=WHO, old=old["subject"], new=new_subject, fact=new_fact, subject=subject)  # fmt: skip
    return subject


def take_back(box: Path, ts: str, old: dict) -> str:
    """A yes pressed by mistake: a replacement whose new word is nothing,
    handed in, and its subject, waiting on the person's seal as "mine stands
    now" does. The old truth stays on the record and, once sealed, no longer
    stands. Nothing takes a seal back; this stands over it."""
    return replace(box, ts, old, "", SLIP)


def keep_both(box: Path, ts: str, old: dict, new_subject: str, new_fact: str) -> None:
    """The person's "both are true": a `table-both` row in the table's shape,
    so the pair isn't raised again, here or at the table."""
    kernel.append(box, ts, BOTH, who=WHO, pair=sorted((old["subject"], new_subject)), facts=sorted((old["fact"], new_fact)))  # fmt: skip


def show(items: list[dict], as_json: bool, none: str) -> int:
    if as_json:
        print(json.dumps(items, indent=1, ensure_ascii=False))
    elif not items:
        print(none)
    else:
        for t in items:
            print(f"on {t['day']} (row {t['n']}): {t['fact']}\n   {t['subject']}")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, flags, it = {}, [], set(), iter(argv)
    for a in it:
        if a in ("--box", "--subject", "--old", "--new", "--fact", "--now"):
            opts[a] = next(it, None)
        elif a == "--json":
            flags.add(a)
        else:
            args.append(a)
    need = {
        "holds": ((), 0),
        "tonight": ((), 0),
        "meets": ((), 1),
        "replace": (("--old", "--new", "--fact"), 0),
        "take-back": (("--old",), 0),
        "both": (("--old", "--new", "--fact"), 0),
    }
    verb = args[0] if args else ""
    # --new may be given empty: a replacement with no word of its own to name
    if not opts.get("--box") or verb not in need or len(args) != 1 + need[verb][1] or not all(opts.get(k) or (k == "--new" and k in opts) for k in need[verb][0]) or None in opts.values():  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").is_file():
        return refuse(f"{box} isn't a box: make one with kernel.py init")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse("the record doesn't verify: " + "; ".join(breaks))
    as_json = "--json" in flags
    if verb == "holds":
        return show(
            standing(box, rows), as_json, "nothing is held true at this table yet"
        )
    if verb == "tonight":
        return show(tonight(box, rows), as_json, "nothing has been made true since the last session ended")  # fmt: skip
    if verb == "meets":
        met = meets(box, args[1], opts.get("--subject") or "")
        return show(
            met, as_json, "nothing the table holds true is about the same thing"
        )
    held = {t["subject"]: t for t in standing(box, rows)}
    old = held.get(opts["--old"])
    if old is None:
        return refuse(f"{opts['--old']} isn't something the table holds true now")
    ts = opts.get("--now") or kernel.now()
    if verb == "both":
        keep_both(box, ts, old, opts["--new"], opts["--fact"])
        print(
            f"both stand: {old['fact']} / {opts['--fact']}; the pair isn't raised again"
        )
        return kernel.ALIVE
    try:
        if verb == "take-back":
            subject = take_back(box, ts, old)
        else:
            subject = replace(box, ts, old, opts["--new"], opts["--fact"])
    except RuntimeError as e:
        return refuse(str(e))
    print(f"waiting on your seal: {subject}\n   it stands in place of: {old['fact']}\n   python kernel.py seal --box {box} {subject}")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
