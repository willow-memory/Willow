"""Femia Archuleta's computer and Marisol's ofrenda: python3 make_life.py [--check]

Seeded, so the same bytes every run. Writes `life/`, the folder Marisol's box
is built from: Femia's old Dell (her terminal history, recipes, notes and
letters, 2010 to 2021) and Marisol's own diary and ofrenda list, 2022 to 2026.
`--check` reads it back: every planted line of questions.json is in it word
for word, every file says on its first line that it is fiction, and no file
holds a word the silent questions are frozen to find nowhere.

Fictional throughout: Femia, Marisol, Joaquín, Rosa and Lupe are no one, and
mail is at example.org. Truchas, Española and the Santuario de Chimayó are
real places, and the customs are real customs; the people are made up.
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"
Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
LABEL = "Fiction: Femia and Marisol Archuleta are made up, for the ofrenda demo; no real person behind them."
DELL = "computadora-de-femia"
PLANT = Q["planted"]


def epoch(stamp: str) -> int:
    """Seconds since 1970 for a UTC 'YYYY-MM-DD HH:MM'."""
    t = datetime.strptime(stamp, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return int(t.timestamp())


# Femia's sessions at the terminal, as bash kept them: the ones that matter,
# then a seeded scatter of the everyday ones around them.
SESSIONS = [
    ("2010-10-16 21:05", ["ls", "pwd", "cd Documents", "ls", "cd", "echo hola"]),
    (
        "2010-10-17 20:40",
        [
            "mkdir recetas",
            "cd recetas",
            "nano biscochitos.txt",
            "ls",
            "cat biscochitos.txt",
        ],
    ),
    (
        "2010-10-23 19:55",
        ["cd recetas", "nano chile-colorado.txt", "nano posole.txt", "ls -l"],
    ),
    (
        "2010-10-30 23:10",
        [
            "nano notas/computadora.txt",
            "nano vela.sh",
            "sh vela.sh",
            PLANT["cron"],
            "crontab -l",
        ],
    ),
    (
        "2011-03-12 18:20",
        [
            "cd cartas",
            "nano lupe-2011-03.txt",
            "mail -s 'saludos' lupe@example.org < lupe-2011-03.txt",
        ],
    ),
    ("2013-12-14 17:30", ["cd recetas", "cat biscochitos.txt", "nano natillas.txt"]),
    ("2016-11-02 06:15", ["cat vela.sh", "crontab -l", "echo 'still here'"]),
    (
        "2019-12-21 16:45",
        [
            "cd recetas",
            "cat biscochitos.txt",
            PLANT["secret"],
            "cat secreto.txt",
            "rm secreto.txt",
            "ls",
        ],
    ),
    ("2021-04-03 15:10", ["cd cartas", "nano lupe-2021-04.txt", "ls"]),
]
EVERYDAY = [
    "ls", "cd", "cd recetas", "ls recetas", "sol", "clear", "date", "cal",
    "cat recetas/posole.txt", "cat recetas/chile-colorado.txt",
    "ping -c 3 example.org", "firefox", "sudo apt update", "exit",
    "espeak 'buenos dias'", "cd cartas", "ls cartas", "cat notas/computadora.txt",
]  # fmt: skip


def history() -> str:
    """Her terminal, oldest first: `#EPOCH` over each command, as bash writes
    it with HISTTIMEFORMAT set (Joaquín set it, "so we know when, Grandma")."""
    R = random.Random(1938)
    sessions = list(SESSIONS)
    for year in range(2011, 2022):
        for _ in range(R.randrange(3, 7)):
            day = f"{year}-{R.randrange(1, 13):02d}-{R.randrange(1, 29):02d}"
            when = f"{day} {R.randrange(14, 24):02d}:{R.randrange(60):02d}"
            sessions.append((when, R.sample(EVERYDAY, R.randrange(2, 5))))
    out = [f"# {LABEL}"]
    for when, commands in sorted(sessions):
        t = epoch(when)
        for i, cmd in enumerate(commands):
            out += [f"#{t + 20 * i}", cmd]
    return "\n".join(out) + "\n"


BISCOCHITOS = f"""{LABEL}
BISCOCHITOS (Femia's) -- for the bake sale, 6 dozen

1 lb lard (not butter, not Crisco. LARD.)
1 1/2 cups sugar
2 eggs
2 tsp anise seed, crushed a little
6 cups flour
3 tsp baking powder
1 tsp salt

Cream the lard and sugar a long time, until it is like a cloud.
Eggs, anise. Flour, baking powder and salt together, then into the lard.
{PLANT["card"]}
Roll thin, 1/4 inch. Cut with the fleur de lis or the star.
Dip the tops in sugar and cinnamon. 350, 10 or 12 minutes, just golden.
"""

CHILE = f"""{LABEL}
CHILE COLORADO

12 dried red chiles from Chimayó, stems and seeds out
4 cups water, 2 cloves garlic, salt, a pinch of oregano

Toast the chiles a little, not black. Soak in hot water 20 minutes.
Blend with the garlic and the water. Strain it.
Brown 2 tbsp flour in a little lard, add the chile, simmer 20 minutes.
For enchiladas, posole, carne adovada. Everything.
"""

POSOLE = f"""{LABEL}
POSOLE for New Year

2 lb frozen posole (the white corn, not the can)
2 lb pork shoulder in pieces
1 onion, 3 cloves garlic, oregano, salt
Cook the posole alone first until it pops open, 3 hours.
Add the pork, onion, garlic. 2 more hours. Chile colorado on the side.
"""

NATILLAS = f"""{LABEL}
NATILLAS

4 cups milk, 4 eggs separated, 3/4 cup sugar, 1/4 cup flour, salt, nutmeg.
Scald the milk. Yolks, sugar and flour into a paste, then into the milk.
Stir, stir, stir until thick. Beat the whites stiff and fold them in.
Nutmeg and cinnamon on top. Mamá made them for the velorio of Papá.
"""

NOTES = f"""{LABEL}
COMPUTADORA -- lo que aprendí

2010-10-16  Joaquín came from Denver and put Ubuntu on Rudy's old Dell.
It is all typing. ls is the list. cd is go inside. Not so hard.

2010-10-17  Made a folder for the recetas. Typed the biscochitos.

{PLANT["notes"]}

2011-03-12  Wrote to Lupe by mail. She wrote back the same day!
"""

VELA = f"""#!/bin/sh
# {LABEL}
printf '\\a'
echo 'Prendan la vela. Aquí estoy.'
"""

LETTERS = {
    "lupe-2011-03.txt": f"""{LABEL}
Querida Lupe,

Look at me, writing on the computer. Joaquín says I am a hacker now.
The apricot tree is blooming early again and the frost will get it again.
Rosa is already talking about the bake sale and it is March.

Tu prima,
Femia
""",
    "lupe-2021-04.txt": f"""{LABEL}
Querida Lupe,

Marisol drove me to Chimayó for Holy Week, I walked the last part.
I brought back a little tierra bendita for you, I will mail it.
I am tired more these days. Bueno, I am 82.

Tu prima,
Femia
""",
}

OFRENDA = f"""{LABEL}
What's on Grandma's ofrenda (it stays up all year)

Her photo from the church directory, the good one, and the one at the beach.
Veladora of the Virgen de Guadalupe. I change it on the 2nd of every month.
Her rosary, the black one from Chimayó.
A little bag of tierra bendita.
The small ristra from the porch.
A plate of biscochitos, made from her card. Never quite right.
Coffee with canela in her blue cup, fresh every morning.
Marigolds from the yard, October to the first frost.
{PLANT["ada"]}
The old Dell, on the table beside it. Still plugged in.
"""

DIARY = [
    (
        "2022-02-11",
        "The funeral was at Sacred Heart. Tía Rosa cried harder than anyone.",
    ),
    ("2022-02-20", "Moved into the house. Didn't touch the Dell."),
    ("2022-03-02", "Started the ofrenda in the sala. Lit the first veladora."),
    ("2022-10-30", "Picked marigolds. Joaquín says he will come for the 2nd."),
    ("2022-11-02", PLANT["beep"]),
    (
        "2022-11-03",
        "Joaquín laughed and then he didn't. He said he'd look at it next time.",
    ),
    ("2022-12-17", PLANT["rosa"]),
    ("2023-06-14", "Hot. The coffee in her cup goes bad by noon now."),
    (
        "2023-11-02",
        "It did it again at midnight. I was waiting this time. I lit the candle.",
    ),
    ("2024-11-02", "Midnight. Third year. Joaquín was here and he cried."),
    (
        "2025-12-20",
        "Biscochitos from her card again. Rosa ate three and said not quite.",
    ),
    ("2026-10-31", "Tomorrow the marigolds. I want to ask her files, not a guess."),
]


def diary() -> str:
    lines = [LABEL, "Marisol's diary", ""]
    for day, text in DIARY:
        lines += [f"{day}  {text}", ""]
    return "\n".join(lines)


def files() -> dict[str, str]:
    out = {
        f"{DELL}/bash_history": history(),
        f"{DELL}/recetas/biscochitos.txt": BISCOCHITOS,
        f"{DELL}/recetas/chile-colorado.txt": CHILE,
        f"{DELL}/recetas/posole.txt": POSOLE,
        f"{DELL}/recetas/natillas.txt": NATILLAS,
        f"{DELL}/notas/computadora.txt": NOTES,
        f"{DELL}/vela.sh": VELA,
        "marisol/ofrenda.txt": OFRENDA,
        "marisol/diario.txt": diary(),
    }
    out.update({f"{DELL}/cartas/{k}": v for k, v in LETTERS.items()})
    return out


def check() -> list[str]:
    import re

    wrong = []
    text = {}
    for p in files():
        try:
            text[p] = (LIFE / p).read_text(encoding="utf-8")
        except OSError:
            wrong.append(f"missing: {p}")
    every = "\n".join(text.values())
    wrong += [f"not planted: {k}" for k, line in PLANT.items() if line not in every]
    for p, t in text.items():
        first = t.splitlines()[1 if p.endswith(".sh") else 0]
        if "Fiction" not in first:
            wrong.append(f"{p}: no fiction label first")
    said = set(re.findall(r"[^\W_]+", every.lower()))
    said |= set(re.findall(r"[^\W_]+", " ".join(files()).lower()))
    for word in Q["never_said"]:
        if word in said:
            wrong.append(
                f"says {word!r}, which a silent question is frozen to find nowhere"
            )
    if text and files() != text:
        wrong.append("life/ is not what make_life.py makes: run it again")
    return wrong


def main(argv: list[str]) -> int:
    if argv == ["--check"]:
        wrong = check()
        print(
            "\n".join(wrong)
            or "ok: every planted line, every label, no silent word said"
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
