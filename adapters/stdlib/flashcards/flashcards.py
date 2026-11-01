"""flashcards.py: your approved answers as cards, scheduled by spaced repetition.

    python adapters/stdlib/flashcards/flashcards.py --box DIR due [--all] [--now TS]
    python adapters/stdlib/flashcards/flashcards.py --box DIR show ID [--now TS]
    python adapters/stdlib/flashcards/flashcards.py --box DIR review ID GRADE [--now TS]
    python adapters/stdlib/flashcards/flashcards.py --box DIR check

A card is an approval you sealed: the front is the words of its file name, the
back is the answer you approved. `due` lists the cards to study now; `show`
prints one; `review` writes your grade (1 again, 2 hard, 3 good, 4 easy, or
the word) as one `review` row through the kernel's own append, and says when
the card is next due:

    4f0c2a91d3  why runs a and b diverged  new
    reviewed 4f0c2a91d3 good: next in 3 days, 2026-11-04T09:00:00Z

Nothing is stored but your grade and its day: every card's schedule is
replayed from the review rows, in order, so `--now` fixes "today" for a test
and the same record gives the same schedule on every machine. Each row also
holds the interval and due date it produced; `check` replays them all and
names the first that doesn't match, or a review of a card that was never
sealed.

The algorithm is FSRS-5 (Free Spaced Repetition Scheduler, Open Spaced
Repetition, MIT licence, as in py-fsrs), written out here from its published
formulas; the card says which parameters. Cards come only from sealed
approvals whose proposal file is still the bytes that were sealed; a broken
one is counted, never studied.

Exit codes, the kernel's: 0 listed, shown, reviewed, or every review holds;
42 nothing is due; 2 refused: a record that doesn't verify, a card or grade
it can't use, or a review that doesn't hold.
"""

from __future__ import annotations

import math
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "review"
WHO = "flashcards"
ALGO = "fsrs-5"
# FSRS-5's published defaults, not fitted to anyone's reviews.
W = (0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046, 1.54575,
     0.1192, 1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898, 0.51655,
     0.6621)  # fmt: skip
RETENTION = 0.9
MAX_DAYS = 36500
MIN_STABILITY = 0.1
DECAY = -0.5
FACTOR = 0.9 ** (1 / DECAY) - 1  # 19/81
GRADES = {"again": 1, "hard": 2, "good": 3, "easy": 4}
FMT = "%Y-%m-%dT%H:%M:%SZ"


def parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, FMT).replace(tzinfo=timezone.utc)


def initial_difficulty(g: int) -> float:
    return min(max(W[4] - math.exp(W[5] * (g - 1)) + 1, 1), 10)


def next_difficulty(d: float, g: int) -> float:
    damped = d + (10 - d) * -(W[6] * (g - 3)) / 9
    return min(max(W[7] * initial_difficulty(4) + (1 - W[7]) * damped, 1), 10)


def step(card: tuple[float, float] | None, g: int, days: int) -> tuple[float, float]:
    """(stability, difficulty) after grade g, `days` whole days since the last."""
    if card is None:
        return max(W[g - 1], MIN_STABILITY), initial_difficulty(g)
    s, d = card
    if days < 1:  # the same day: the short-term formula
        new = s * math.exp(W[17] * (g - 3 + W[18]))
    else:
        r = (1 + FACTOR * days / s) ** DECAY
        if g == 1:
            new = min(
                W[11]
                * d ** -W[12]
                * ((s + 1) ** W[13] - 1)
                * math.exp((1 - r) * W[14]),
                s / math.exp(W[17] * W[18]),
            )
        else:
            bonus = (W[15] if g == 2 else 1) * (W[16] if g == 4 else 1)
            new = s * (1 + math.exp(W[8]) * (11 - d) * s ** -W[9]
                       * (math.exp((1 - r) * W[10]) - 1) * bonus)  # fmt: skip
    return max(new, MIN_STABILITY), next_difficulty(d, g)


def interval(s: float) -> int:
    """Whole days until recall falls to RETENTION, at least 1."""
    days = round(s / FACTOR * (RETENTION ** (1 / DECAY) - 1))
    return min(max(days, 1), MAX_DAYS)


def reviews(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        if r["kind"] == KIND:
            out.setdefault(str(r.get("subject")), []).append(r)
    return out


def replay(rs: list[dict]) -> list[tuple[int, str, tuple[float, float]]]:
    """For each review row, in order: (days, due, state) as the grades give it.
    A row whose grade or ts can't be read stops the replay with ValueError."""
    card, last, out = None, None, []
    for r in rs:
        g, at = r.get("grade"), parse_ts(r["ts"])
        if isinstance(g, bool) or g not in (1, 2, 3, 4):
            raise ValueError(f"row {r['n']}: grade {g!r} is not 1 to 4")
        if last is not None and at < last:
            raise ValueError(f"row {r['n']}: reviewed before the review row before it")
        card = step(card, g, 0 if last is None else (at - last).days)
        days = interval(card[0])
        out.append((days, (at + timedelta(days=days)).strftime(FMT), card))
        last = at
    return out


def front(prop: dict) -> str:
    stem = Path(prop["path"]).stem
    return " ".join(re.sub(r"[-_.]+", " ", stem).split()) or stem


def cards(box: Path, rows: list[dict]) -> tuple[list[dict], int]:
    """(the cards, in the order they were sealed; how many seals are broken)."""
    out, broken = [], 0
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            broken += 1
            continue
        out.append({"subject": subj, "id": subj[9:19], "front": front(prop),
                    "back": prop["data"], "sealed": row["ts"], "n": row["n"]})  # fmt: skip
    return out, broken


def schedule(cards_: list[dict], rows: list[dict]) -> None:
    """Add to each card its reviews, due date and last review, from the rows."""
    by = reviews(rows)
    for c in cards_:
        rs = by.get(c["subject"], [])
        got = replay(rs)
        c["reviews"] = len(rs)
        c["due"] = got[-1][1] if got else c["sealed"]
        c["last"] = rs[-1]["ts"] if rs else None


def load(argv_box: str) -> tuple[Path, list[dict]] | None:
    box = Path(argv_box)
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return None
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return None
    return box, rows


def pick(cs: list[dict], ident: str) -> dict | None:
    got = [c for c in cs if len(ident) >= 6 and c["id"].startswith(ident.lower())]
    if len(got) != 1:
        print(f"refused: {ident!r} names {len(got)} cards; give 6 or more of its id",
              file=sys.stderr)  # fmt: skip
        return None
    return got[0]


def due_in(c: dict, now: datetime) -> bool:
    return parse_ts(c["due"]) <= now


def check(box: Path, rows: list[dict]) -> list[str]:
    """Every way a review row doesn't hold; empty when all do."""
    sealed = kernel.sealed(box, rows)
    bad = []
    for subj, rs in reviews(rows).items():
        if subj not in sealed or sealed[subj]["n"] > rs[0]["n"]:
            bad.append(
                f"row {rs[0]['n']}: reviews a card that was not sealed before it"
            )
            continue
        try:
            got = replay(rs)
        except (ValueError, KeyError) as e:
            bad.append(str(e))
            continue
        for r, (days, due, _) in zip(rs, got):
            if r.get("algo") != ALGO or r.get("days") != days or r.get("due") != due:
                bad.append(f"row {r['n']}: the grades give {days} days, due {due};"
                           f" the row says {r.get('days')!r}, {r.get('due')!r}"
                           f" ({r.get('algo')!r})")  # fmt: skip
                break
    return sorted(bad, key=lambda s: int(s.split()[1].rstrip(":")))


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        elif a == "--all":
            opts[a] = "1"
        else:
            args.append(a)
    cmd = args[:1]
    shape = {"due": 1, "check": 1, "show": 2, "review": 3}
    if not opts.get("--box") or not cmd or shape.get(cmd[0]) != len(args):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if "--all" in opts and cmd != ["due"]:
        print("refused: --all is for due", file=sys.stderr)
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    try:
        now = parse_ts(ts)
    except ValueError:
        print(
            f"refused: {ts!r} is not a time like 2026-11-01T09:00:00Z", file=sys.stderr
        )
        return kernel.REFUSED
    got = load(opts["--box"])
    if got is None:
        return kernel.REFUSED
    box, rows = got
    if cmd == ["check"]:
        bad = check(box, rows)
        for b in bad:
            print(f"refused: {b}", file=sys.stderr)
        n = sum(len(v) for v in reviews(rows).values())
        print(
            f"{n} reviews; " + (f"{len(bad)} don't hold" if bad else "every one holds")
        )
        return kernel.REFUSED if bad else kernel.ALIVE
    if bad := check(box, rows):
        print("refused: the reviews on this record don't hold; `check` says which:",
              bad[0], sep="\n  ", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    cs, broken = cards(box, rows)
    schedule(cs, rows)
    if cmd == ["due"]:
        shown = [c for c in cs if "--all" in opts or due_in(c, now)]
        for c in sorted(shown, key=lambda c: (c["due"], c["n"])):
            state = "new" if not c["reviews"] else f"due {c['due']}"
            print(f"{c['id']}  {c['front']}  {state}")
        late = sum(due_in(c, now) for c in cs)
        print(f"{len(cs)} cards; {late} due" + (f"; {broken} broken" if broken else ""))
        return kernel.ALIVE if shown else kernel.ESCALATE
    c = pick(cs, args[1])
    if c is None:
        return kernel.REFUSED
    if cmd[0] == "show":
        print(f"{c['id']}  {c['front']}\n{c['back']}")
        print(f"reviewed {c['reviews']} times; "
              + (f"next due {c['due']}" if c["reviews"] else "new"))  # fmt: skip
        return kernel.ALIVE
    word = args[2].lower()
    g = GRADES.get(word) or (int(word) if word in ("1", "2", "3", "4") else None)
    if g is None:
        print("refused: a grade is 1 again, 2 hard, 3 good or 4 easy", file=sys.stderr)
        return kernel.REFUSED
    if now < parse_ts(c["sealed"]) or (c["last"] and now < parse_ts(c["last"])):
        print("refused: that is before the card was sealed or last reviewed",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    by = reviews(rows).get(c["subject"], [])
    days, due, _ = replay([*by, {"n": len(rows), "ts": ts, "grade": g}])[-1]
    kernel.append(box, ts, KIND, who=WHO, subject=c["subject"], grade=g, days=days,
                  due=due, algo=ALGO)  # fmt: skip
    print(f"reviewed {c['id']} {['again', 'hard', 'good', 'easy'][g - 1]}: next in "
          f"{days} day{'s' * (days != 1)}, {due}")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
