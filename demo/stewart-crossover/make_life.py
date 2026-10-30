"""Wren Castellano's files, 2020 to 2023: python3 make_life.py [--check]

Seeded, so the same bytes every run. Writes `life/` (the folder her box is
built from). `--check` reads it back: every frozen line of questions.json is
in it word for word, every file says on its first line that she is fiction,
and no line names him, the show or the memoir unless it is a frozen line.

Fictional throughout: Wren, Kati, Dev and the rest are no one, the town and
its library are made up, mail is at example.org, and the shop is an
example.com one. Patrick Stewart is not fiction, and so nothing here says
anything of him but the lines questions.json froze: facts two publishers
hold, quotes a source holds, the four traps, and four lines of her own.
"""

from __future__ import annotations

import json
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"
Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
R = random.Random(2020)
LABEL = "Fiction: Wren Castellano is made up, for the stewart-crossover demo; no real person behind her."
FACT = {f["id"]: f["sentence"] for f in Q["facts"]}
QUOTE = {q["id"]: q["line"] for q in Q["quotes"]}
TRAP = {t["id"]: t["line"] for t in Q["traps"]}
OWN = Q["fiction_lines"]

SHIFTS = [
    "story time, twenty-two kids and one very loud parrot puppet",
    "weeded the 500s; three carts to the book sale",
    "interlibrary loan backlog, cleared to Thursday",
    "the printer jammed four times; Ruth fixed it with a paper clip",
    "teen advisory board voted for a graphic novel shelf",
    "homework help, mostly long division",
    "inventory of the reference room, two missing atlases found",
    "the boiler again; closed at three",
    "seed library opened for spring",
    "book club picked a doorstop; nobody finished it",
]
GROUP = ["Kati", "Dev", "Ruth", "Mo"]
MERCH = [
    ("bridge mug", "ceramic", "shop.example.com", 18),
    ("combadge pin", "enamel", "shop.example.com", 12),
    ("starship blueprint poster", "paper", "flea market", 5),
    ("tea tin, Earl Grey", "tin", "shop.example.com", 9),
    ("Enterprise-D model, 1:2500", "resin", "shop.example.com", 64),
    ("phaser replica, toy", "plastic", "flea market", 7),
    ("uniform tunic, red", "polyester", "shop.example.com", 45),
    ("tricorder notebook", "paper", "shop.example.com", 14),
]


def days(start: date, end: date, n: int) -> list[date]:
    span = (end - start).days
    return sorted({start + timedelta(days=R.randrange(span)) for _ in range(n)})


def log_year(year: int, extra: list[str]) -> str:
    out = [LABEL, f"Wren's desk log, {year}. Typed up from the notebook.", ""]
    picks = days(date(year, 1, 2), date(year, 12, 30), 40)
    slots = R.sample(range(len(picks)), len(extra))
    for i, day in enumerate(picks):
        out.append(f"{day.isoformat()}  {R.choice(SHIFTS)}")
        if i in slots:
            out.append(f"{day.isoformat()}  {extra[slots.index(i)]}")
    return "\n".join(out) + "\n"


def chat() -> str:
    out = [LABEL, "Watch group chat, exported. Kati, Dev, Ruth, Mo and Wren.", ""]
    small = [
        "who's bringing the kettle",
        "running late, save me the good chair",
        "snacks: someone not me this time",
        "the library lot is plowed, see you at seven",
        "I'm making the tea strong, you've been warned",
        "can we start ten minutes early",
    ]
    planted = {14: TRAP["T2"], 31: TRAP["T4"], 47: OWN[3]}
    when = days(date(2020, 1, 20), date(2023, 4, 30), 60)
    for i, day in enumerate(when):
        who = R.choice(GROUP)
        text = planted.get(i) or f"{who}: {R.choice(small)}"
        out.append(f"[{day.isoformat()} 19:{R.randrange(60):02d}] {text}")
    return "\n".join(out) + "\n"


def fan_facts() -> str:
    return "\n".join([
        LABEL,
        "# Fan facts, checked",
        "",
        "Things I've read and written down.",
        "",
        *(f"- {FACT[k]}" for k in sorted(FACT)),
        "",
        "# Not checked",
        "",
        f"- {TRAP['T1']}",
        "",
    ])  # fmt: skip


def quotes() -> str:
    return "\n".join(
        [
            LABEL,
            "Highlights I keep on the corkboard.",
            "",
            QUOTE["quote1"],
            "",
            QUOTE["quote2"],
            "",
        ]
    )


def collection() -> str:
    rows = [LABEL, "The shelf, for the insurance list: item, where from, price.", ""]
    for item, mat, shop, price in MERCH:
        if item.startswith("Enterprise-D model"):
            rows.append(TRAP["T3"])
        else:
            rows.append(f"{item} ({mat}), {shop}, ${price}")
    return "\n".join(rows) + "\n"


def files() -> dict[str, str]:
    return {
        "log/2020.txt": log_year(2020, [OWN[0], OWN[1]]),
        "log/2021.txt": log_year(2021, []),
        "log/2022.txt": log_year(2022, []),
        "log/2023.txt": log_year(2023, [OWN[2]]),
        "chat/watch-group.txt": chat(),
        "notes/fan-facts.md": fan_facts(),
        "notes/quotes.txt": quotes(),
        "merch/collection.txt": collection(),
    }


def check() -> list[str]:
    wrong, names = [], re.compile(Q["names"])
    known = [*FACT.values(), *QUOTE.values(), *TRAP.values(), *OWN]
    text = {p: (LIFE / p).read_text(encoding="utf-8") for p in files()}
    every = "\n".join(text.values())
    wrong += [f"missing: {k}" for k in known if k not in every]
    for p, t in text.items():
        if "Fiction" not in t.splitlines()[0]:
            wrong.append(f"{p}: no fiction label first")
        for n, line in enumerate(t.splitlines(), 1):
            if names.search(line) and not any(k in line for k in known):
                wrong.append(f"{p}:{n}: names him in a line not frozen")
    return wrong


def main(argv: list[str]) -> int:
    if argv == ["--check"]:
        wrong = check()
        print(
            "\n".join(wrong)
            or "ok: every frozen line, every label, nothing else naming him"
        )
        return 1 if wrong else 0
    if argv:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    for p, t in files().items():
        (LIFE / p).parent.mkdir(parents=True, exist_ok=True)
        (LIFE / p).write_text(t, encoding="utf-8")
    print(f"wrote {len(files())} files to {LIFE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
