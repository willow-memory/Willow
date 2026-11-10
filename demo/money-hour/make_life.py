"""The money hour's four folders, as the files they leave: python make_life.py [--mirror MIRROR] [--check]

Four people from willow's other demos at one table: Teo Marinescu (teodora)
hosts a video call about money on a Sunday each month, and Bernie Halloran
(bernadette), Hollis Varga (hollis) and Marisol Archuleta (ofrenda) come.
Their files are fiction and say so on their first line. Every line in them
that names a real figure, rate, official or company is a frozen line from
questions.json, word for word; nothing else in them states anything about
the world.

One file is not theirs: Hollis's copy of the 10-K paragraph his newsletter
summarised, read from MIRROR (the markets demo's mirror) word for word, and
labelled as a copy. It is how pair-drift has a full text to hold the summary
to, and it is written only with --mirror: without it (as CI runs every
demo's make_life.py, offline) every other file is written and checked.
Written to `life/`, the same bytes every run; `--check` reads them back and
holds them to questions.json, and the copy to the mirror when one is named.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"
Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
TODAY = Q["today"]
TENK = "web/sec/10-k/AAPL-2026-11-03.htm.txt"
TENK_START = "In April 2026, the Company announced a new share repurchase program"

#: Words that name the real world. A line holding one must be a frozen line,
#: or in the copied source, which is held to the mirror instead.
REAL = re.compile(r"\b(Fed|FOMC|Treasury|ECB|SP500|S&P|unemployment|Warsh|Powell|Apple|"
                  r"10-K|Cook|Hammack|repurchased|deposit facility|target range)\b")  # fmt: skip
COPY = "hollis/newsletter/apple/10-k-paragraph.md"


def frozen() -> dict[str, list[str]]:
    """Each person's frozen lines, in the order the files use them."""
    by: dict[str, list[str]] = {}
    for x in Q["facts"] + [Q["quote"]] + Q["traps"] + Q["calls"]:
        if "line" in x:
            by.setdefault(x["who"], []).append(x["line"])
    by["teodora"] += [ln for ln in Q["letter"]["draft"] + Q["letter"]["final"]
                      if ln not in by["teodora"]]  # fmt: skip
    return by


def line(id_: str) -> str:
    for x in Q["facts"] + [Q["quote"]] + Q["traps"]:
        if x["id"] == id_:
            return x["line"]
    raise KeyError(id_)


def call(who: str) -> str:
    return next(c["line"] for c in Q["calls"] if c["who"] == who)


def fiction(who: str) -> str:
    return (f"Fiction: {who} is no one, from willow's demos. Real figures here are frozen "
            "lines, checked against the markets pile.\n\n")  # fmt: skip


def files(mirror: Path | None) -> dict[str, str]:
    t = "Teo Marinescu"
    f: dict[str, str] = {}

    # --- Teo: the host. Leeds, bookkeeper, keeps the minutes -------------------
    f["teodora/money-hour/README.md"] = (
        fiction(t)
        + """# Money hour

Last Sunday of the month, 7pm my time, on video. Started it after Bernie's
comment on my bookkeeping blog asking about her super. Rules I made us agree:

1. Nobody gives anybody advice. We say what we read and where.
2. If you repeat a number, say where it came from. "Someone said" is not a where.
3. Write your wagers down before, with how sure you are, and keep the losers.

Who comes: Bernie (Ballarat, so it's Monday morning for her), Hollis (piano
tuner, Larkfield), Marisol (Española, her gran's savings).
"""
    )
    f["teodora/money-hour/2026-09-27.md"] = (
        fiction(t)
        + f"""# Money hour, 2026-09-27

Present: Bernie, Hollis, Marisol, me. Sam made tea and hid.

Marisol: "My cousin Lupe keeps telling me what the bank will do. I don't know who to believe."
Bernie: "Gerry reads the paper at the Men's Shed and comes home with numbers."
Hollis said he'd rather tune a hundred spinets than read a statement.

Agreed: next time everyone brings one number and where it came from.
Me: dug out the quote I keep for this, from the transcript, not the radio.
{line("V1")}
"""
    )
    f["teodora/money-hour/2026-10-25.md"] = (
        fiction(t)
        + """# Money hour, 2026-10-25

Present: all four. Maisie drew everyone's cats on the whiteboard behind me.

Marisol brought Lupe's version and her own. Bernie brought Gerry's figure and mine.
Hollis brought a newsletter and a thing off the van radio, and admitted he
hadn't checked either.

Bernie: "So the trick is the where, not the what."
Hollis: "I'll bring the paragraph next time, not the newsletter."
Marisol said she would write a wager even though she has no idea.

Actions: everyone puts their wager in calls.md before the day, with a p.
"""
    )
    f["teodora/money-hour/2026-11-01.md"] = (
        fiction(t)
        + f"""# Notes for the November call (2026-11-01)

{line("R2")}
{line("R5")}

To ask: did everyone write their wager before the day? Hollis says yes.
"""
    )
    head = (f"# Fiction: {t} is no one, from willow's demos. A letter to the money hour, "
            "one sentence a line, so thesis can put each to the sources.\n\n")  # fmt: skip
    f["teodora/letter/2026-11-draft.md"] = head + "\n".join(Q["letter"]["draft"]) + "\n"
    f["teodora/letter/2026-11.md"] = head + "\n".join(Q["letter"]["final"]) + "\n"
    f["teodora/calls.md"] = (
        fiction(t)
        + f"""# My wagers

{call("teodora")}
"""
    )
    f["teodora/clients/bramble-and-bean.md"] = (
        fiction(t)
        + """# Bramble & Bean (Kirsty)

Monthly: bank rec, VAT quarter, payroll for three.
Coffee supplier in Antwerp invoices in euros; Kirsty asks every month whether
to pay now or at 30 days. I say: I don't predict, I write down what happened.
Last supplier invoice €3,480.00, paid 2026-10-21. October payroll £6,912.40.
Next VAT return due 2026-11-07.
"""
    )
    f["teodora/todo.md"] = (
        fiction(t)
        + """# To do

- [ ] chase Hannah's receipts for September
- [ ] AAT Level 4: open the book. Any page.
- [ ] wrist: actually book the physio
- [x] send money hour link for November
"""
    )

    # --- Bernie: Ballarat. Super, Gerry, the roof --------------------------------
    b = "Bernie Halloran"
    f["bernadette/money/super-notes.md"] = (
        fiction(b)
        + f"""# AusPrime Super, our notes

Both pensions account-based. Statement came 2026-10-14. I don't understand
half of it but the balance went down and then up.

{line("T3")}
{line("R4")}

Kieran says I should stop reading the comments under articles. He's right.
"""
    )
    f["bernadette/money/calls.md"] = (
        fiction(b)
        + f"""# Wagers (Teo's rule: write it before, keep it after)

{call("bernadette")}
"""
    )
    f["bernadette/house/roof.md"] = (
        fiction(b)
        + """# The roof

Leak over the back bedroom again after the rain on 2026-10-30.
Gerry wants to go up the ladder. He is not going up the ladder.
Quote from the roofer: $2,140, can come 2026-11-12.
"""
    )
    f["bernadette/family/aoife-21st.md"] = (
        fiction(b)
        + """# Aoife's 21st, 12 December

Siobhán is doing the party in Brunswick West. We'll drive down the day before.
Gift: the pearl earrings from Mam, and a card with money in it.
"""
    )

    # --- Hollis: Larkfield. Pianos, his father, a newsletter ------------------------
    h = "Hollis Varga"
    f["hollis/notes/2026-10.md"] = (
        fiction(h)
        + f"""# October notes

{line("T2")}
{line("T4")}
Teo says check it against the transcript before I repeat it at the money hour.

{line("R7")}
"""
    )
    f["hollis/notes/2026-11.md"] = (
        fiction(h)
        + f"""# November notes

Went back to the source like Teo said. The newsletter was wrong by ten billion.
{line("R6")}
"""
    )
    f["hollis/calls.md"] = (
        fiction(h)
        + f"""# Wagers

{call("hollis")}
"""
    )
    f["hollis/newsletter/apple/summary.md"] = (
        fiction(h) + next(x["summary"] for x in Q["traps"] if x["id"] == "T5") + "\n"
    )
    f["hollis/schedule.md"] = (
        fiction(h)
        + """# Week of 2026-11-02

Mon: Coldbrook church, the Kimball. Tue: Civic Hall Steinway D for the concert.
Wed: Pine Hatch, three uprights. Sun: Dad in Brookhollow.
Van due for service 2026-11-20.
"""
    )
    f["hollis/dad.md"] = (
        fiction(h)
        + """# Imre

Ruth next door says he's eating. Bring the good bread Sunday.
He asked again about Mom's Weiler upright in the garage. Tell him: soundboard next.
"""
    )
    # the copied source, word for word from the mirror, when there is one
    if mirror is not None:
        text = (mirror / TENK).read_text(encoding="utf-8")
        para = next(ln for ln in text.splitlines() if ln.startswith(TENK_START))
        f[COPY] = (
            "Copied word for word from the issuer's annual report on SEC EDGAR, filed "
            "2026-11-03, so the summary beside it can be held to it. Not Hollis's words.\n\n"
            + para
            + "\n"
        )  # fmt: skip

    # --- Marisol: Española. Her grandmother's savings ---------------------------------
    m = "Marisol Archuleta"
    f["marisol/savings/grandma-bonds.md"] = (
        fiction(m)
        + f"""# Grandma's bonds

Femia's savings bonds matured in the spring. The envelope was in the Dell's
drawer, next to the recipe printouts. Joaquín helped me cash them.

{line("R3")}
"""
    )
    f["marisol/savings/lupe.md"] = (
        fiction(m)
        + f"""# What Lupe says

Lupe called from Alamosa on 2026-10-04.
{line("T1")}
I asked her where she read it. She said everybody knows.

{line("R1")}
"""
    )
    f["marisol/calls.md"] = (
        fiction(m)
        + f"""# Wagers

{call("marisol")}
"""
    )
    f["marisol/ofrenda.md"] = (
        fiction(m)
        + """# The ofrenda, November

Marigolds from the yard are done for the year. Fresh veladora on 2026-11-01.
Biscochitos for Día de los Muertos, Rosa's recipe this time, don't tell anyone.
"""
    )
    return f


def write(mirror: Path | None) -> int:
    for rel, text in files(mirror).items():
        p = LIFE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as out:
            out.write(text)
    print(f"wrote {len(files(mirror))} files to {LIFE}")
    return check(mirror)


def check(mirror: Path | None) -> int:
    """Every real-world line is frozen; every frozen line is there; none is dated after today."""
    want, bad = frozen(), []
    for who, lines in want.items():
        have = "\n".join(
            p.read_text(encoding="utf-8") for p in (LIFE / who).rglob("*.md")
        )
        bad += [f"missing {who}: {ln}" for ln in lines if ln not in have.splitlines()]
    every = {ln for lines in want.values() for ln in lines}
    every |= {x["summary"] for x in Q["traps"] if "summary" in x}
    for p in sorted(LIFE.rglob("*.md")):
        rel = p.relative_to(LIFE).as_posix()
        for n, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if rel == COPY and n > 1:
                continue
            if REAL.search(ln) and ln not in every:
                bad.append(f"unfrozen {rel}:{n}: {ln}")
            for d in re.findall(r"\b20\d\d-\d\d-\d\d\b", ln) if ln in every else []:
                if d > TODAY:  # plans may be ahead of today; what the world did may not
                    bad.append(f"after today {rel}:{n}: {d}")
    if mirror is not None:
        copy = (LIFE / COPY).read_text(encoding="utf-8").splitlines()[2]
        if copy not in (mirror / TENK).read_text(encoding="utf-8").splitlines():
            bad.append("the copied paragraph is not the mirror's, word for word")
    for b in bad:
        print(b)
    print("holds" if not bad else f"{len(bad)} problems")
    return 0 if not bad else 2


def main(argv: list[str]) -> int:
    mirror = None
    if argv[:1] == ["--mirror"] and len(argv) >= 2:
        mirror, argv = Path(argv[1]), argv[2:]
    if argv == ["--check"]:
        return check(mirror)
    if argv == []:
        return write(mirror)
    print(__doc__.split("\n\n")[0], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
