"""Marisol Ortiz Beltran's folder, as the files her work leaves: python3 make_life.py [--check]

Seeded, so the same bytes every run. Writes `life/` (the folder her box is
built from) and `names.txt` (the people in it, for `--names`; kept outside
`life/`). `--check` reads the written files back and holds them to PLANTED.md:
each claim's evidence is there, and each trap is too.

Fiction throughout. The people, the school and the companies are invented; the
real facts the story stands on are kept by address and SHA-256 in sources.json,
never as text. Phones are 787-555-01xx and mail is at example.org/.com. Every
file says it is fiction, and every invented number is marked invented.

The Spanish was written by a model, not by an islander. A Puerto Rican reader
must read it for what rings false before this goes beyond its author.
"""

from __future__ import annotations

import csv
import io
import random
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIFE = HERE / "life"
R = random.Random(2017)

MARIA = date(2017, 9, 20)
POWER_BACK = date(2017, 12, 4)  # the school's grid power: 76 days, inclusive
TODAY = date(2026, 11, 12)
TOTAL_CENTS = 1_487_350  # the receipts total: $14,873.50 (invented)
CLAIMED = "$40,000"
LESSON_LINE = "Whoever keeps the log alone decides what counts as evidence."
DRAFT_QUOTE = "Whoever keeps the log decides what counts as evidence."

FICTION_EN = (
    "FICTION. Invented for a demo; no real person, school or company is described."
)
FICTION_ES = "FICCIÓN. Inventado para una demostración; no describe a ninguna persona, escuela ni empresa reales."

CAST = [
    "Marisol Ortiz Beltrán", "Ernesto Beltrán", "Camila Rosario",
    "Héctor Delgado", "Inés Quiñones", "Tomás Beltrán",
    "Escuela Superior La Ceiba", "Puente Digital", "Laboratorios Caribe del Sur",
]  # fmt: skip


def phone(n: int) -> str:
    return f"787-555-01{n:02d}"


def put(rel: str, text: str) -> None:
    path = LIFE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


# --- the outage log (Spanish) -------------------------------------------------

AFTER_MARIA = [
    "Clase con linternas en el salón de computación.",
    "Se llenó el tanque del generador; se apagó a las 8 de la noche para ahorrar.",
    "Los estudiantes de robótica revisaron las baterías del carrito de prueba.",
    "El generador de la escuela alimenta la cafetería primero.",
    "Cargamos teléfonos en la oficina del director por turnos.",
    "Hoy no hubo clases en el laboratorio; el calor era mucho.",
    "Camila llevó su cuaderno de apuntes y anotó la hora de cada cambio de turno.",
]
LATER = [
    "avería en el alimentador, sin aviso previo",
    "mantenimiento anunciado por la compañía",
    "tormenta tropical; se cayó un poste en la carretera",
    "sobrecarga de la red en la tarde",
    "sin explicación; llamé al número de averías y no contestaron",
]


def make_log() -> None:
    out = [
        FICTION_ES,
        "Registro de apagones de la Escuela Superior La Ceiba (inventado).",
        "Los números de este registro son inventados.",
        "",
    ]
    d, n = MARIA, 0
    while d < POWER_BACK:
        n = (d - MARIA).days + 1
        line = AFTER_MARIA[(n // 7) % len(AFTER_MARIA)]
        out.append(f"{d.isoformat()} Día {n} sin luz de la red. {line}")
        d += timedelta(days=7)
    out.append(
        f"{POWER_BACK.isoformat()} Día {(POWER_BACK - MARIA).days + 1}: volvió la luz de la red"
        f" a la escuela. Fueron {(POWER_BACK - MARIA).days + 1} días."
    )
    out.append("")
    for year in range(2018, 2027):
        count = R.randint(3, 6)
        days = sorted(R.sample(range(1, 330 if year < 2026 else 300), count))
        for k in days:
            when = date(year, 1, 1) + timedelta(days=k)
            hours = R.choice([2, 3, 4, 6, 9, 14])
            gen = R.choice(
                ["Entró el generador.", "Funcionó la batería del laboratorio."]
            )
            out.append(
                f"{when.isoformat()} Sin luz {hours} horas: {R.choice(LATER)}. {gen}"
            )
        if year == 2019:
            out.append(
                "2019-08-14 Subida de voltaje en la tarde: el técnico habló de una línea de"
                " casi 40 mil voltios (38 kV) en el poste. Se quemaron dos fuentes de poder."
            )
        if year == 2021:
            out.append(
                "2021-06-01 LUMA asumió la operación de la red hoy. El registro sigue."
            )
    put("log/outages.txt", "\n\n".join(sorted_log(out)) + "\n")


def sorted_log(lines: list[str]) -> list[str]:
    head = lines[:3]
    body = sorted(x for x in lines[3:] if x.strip())
    return ["\n".join(head)] + body


# --- receipts (csv, with notes above the header) ------------------------------

VENDORS = ["Gasolinera El Mirador", "Combustibles del Sur", "Estación Las Palmas"]


def make_receipts() -> None:
    fixed = [
        ("2018-03-14", "Banco de baterías, 4 de 12 V ciclo profundo", "Energía Hogar PR", 624000, "baterías"),
        ("2018-03-14", "Inversor 3000 W", "Energía Hogar PR", 138500, "baterías"),
        ("2018-03-20", "Cables, interruptores y soportes", "Ferretería Central", 41275, "baterías"),
        ("2018-06-02", "Computadoras reacondicionadas, 4", "Reciclaje Digital Ponce", 112000, "equipos"),
    ]  # fmt: skip
    fuel_total = TOTAL_CENTS - sum(f[3] for f in fixed)
    n = 22
    w = [R.uniform(0.7, 1.3) for _ in range(n)]
    cents = [round(x / sum(w) * fuel_total) for x in w]
    cents[-1] = fuel_total - sum(cents[:-1])
    dates = sorted(
        [MARIA + timedelta(days=int(R.uniform(8, 120))) for _ in range(n - 4)]
        + [date(2019, 8, 15), date(2021, 6, 3), date(2022, 9, 18), date(2024, 1, 11)]
    )
    rows = [
        (d.isoformat(), "Diésel para el generador", R.choice(VENDORS), c, "combustible")
        for d, c in zip(dates, cents)
    ] + fixed
    rows.sort(key=lambda r: r[0])
    buf = io.StringIO()
    buf.write("# FICCIÓN. Recibos inventados de la Escuela Superior La Ceiba.\n")
    buf.write("# Las cantidades son inventadas.\n")
    w_ = csv.writer(buf, lineterminator="\n")
    w_.writerow(["fecha", "concepto", "comercio", "monto", "categoria"])
    for d, what, shop, c, cat in rows:
        w_.writerow([d, what, shop, f"${c / 100:,.2f}", cat])
    put("receipts/outage-costs.csv", buf.getvalue())


# --- mail (Spanish) -----------------------------------------------------------


def eml(sender: str, to: str, when: str, subject: str, body: str) -> str:
    return (
        f"From: {sender}\nTo: {to}\nDate: {when}\nSubject: {subject}\n"
        "MIME-Version: 1.0\nContent-Type: text/plain; charset=utf-8\n"
        "Content-Transfer-Encoding: 8bit\nX-Demo: ficción\n\n"
        f"{FICTION_ES}\n\n{body}\n"
    )


def make_mail() -> None:
    marisol = "Marisol Ortiz <marisol.ortiz@example.org>"
    put(
        "mail/2018-02-09-tomas.eml",
        eml(
            "Tomás Beltrán <tomas.beltran@example.com>",
            marisol,
            "Fri, 09 Feb 2018 21:14:00 -0400",
            "Transferencia para las baterías",
            "Marisol,\n\nTe mandé $6,000 por transferencia para el banco de baterías de la "
            "escuela. Es lo que pudimos juntar aquí. Dime cuando llegue.\n\nY dime algo: "
            "¿cuándo se va a quedar la luz prendida? Los nenes me preguntan.\n\nTomás\n"
            f"{phone(21)}",
        ),
    )
    put(
        "mail/2018-09-05-hector.eml",
        eml(
            "Héctor Delgado <hector.delgado@example.org>",
            marisol,
            "Wed, 05 Sep 2018 10:02:00 -0400",
            "Prioridad del generador",
            "Profesora Ortiz:\n\nEl generador de la escuela alimenta primero la cafetería y la "
            "oficina. El laboratorio queda con el banco de baterías que usted compró. Le pido que "
            "lleve la cuenta de lo que gasta en diésel, porque el distrito va a preguntar.\n\n"
            "Héctor Delgado\nDirector",
        ),
    )
    put(
        "mail/2026-11-03-ines.eml",
        eml(
            "Inés Quiñones <ines.quinones@example.org>",
            marisol,
            "Tue, 03 Nov 2026 16:40:00 -0400",
            "Su borrador para Puente Digital",
            "Estimada profesora Ortiz:\n\nGracias por el borrador del laboratorio de robótica y "
            "alfabetización en IA. Antes de pasarlo al comité, le pido algo: que cada afirmación "
            "lleve su fuente. Donde no haya fuente, dígamelo y lo escribimos así.\n\n"
            "Una pregunta concreta: ¿la cifra de pérdidas por apagones sale de sus recibos?\n\n"
            "Inés Quiñones\nPuente Digital\n" + phone(44),
        ),
    )


# --- the father's interview (WebVTT, Spanish) ---------------------------------

CUES = [
    ("Marisol", "Papá, cuéntame del cierre de la planta, con calma."),
    (
        "Ernesto",
        "Cerró en el verano de 2004. Yo tenía cincuenta y dos años y llevaba veintiocho en el laboratorio.",
    ),
    ("Marisol", "¿Y por qué cerró?"),
    (
        "Ernesto",
        "Por la ley. Ese crédito federal de la 936 se acabó en el noventa y seis, y de ahí para acá fue cuesta abajo.",
    ),
    ("Marisol", "¿Seguro que fue en el noventa y seis?"),
    (
        "Ernesto",
        "Ay, mija, no me preguntes fechas. Pregúntame qué fabricábamos: tabletas, en tres turnos, con una sala limpia.",
    ),
    (
        "Ernesto",
        "Los fines de semana arreglo radios viejos en el garaje. Eso sí me lo sé de memoria.",
    ),
    ("Marisol", "Es que los domingos me llamas para preguntarme en qué año estamos."),
    ("Ernesto", "Para oírte la voz. El año ya me lo sé."),
]


def stamp(s: int) -> str:
    return f"00:{s // 60:02d}:{s % 60:02d}.000"


def make_interview() -> None:
    out = [
        "WEBVTT",
        "",
        f"NOTE {FICTION_ES}",
        "NOTE Entrevista inventada, 2026-10-18.",
        "",
    ]
    t = 4
    for i, (who, said) in enumerate(CUES, 1):
        out += [str(i), f"{stamp(t)} --> {stamp(t + 9)}", f"<v {who}>{said}", ""]
        t += 11
    put("notes/ernesto-interview.vtt", "\n".join(out))
    put(
        "notes/nota-credito-936.md",
        f"# Nota sobre el crédito de la 936\n\n_{FICTION_ES}_\n\n"
        "2025-03-02. Mi apunte: el crédito de la sección 936 se terminó en 2005. "
        "Revisar el año en el informe del CRS antes de escribirlo en el borrador.\n",
    )


# --- lessons ------------------------------------------------------------------


def make_lessons() -> None:
    put(
        "lessons/01-comprobar-una-fuente.md",
        f"# Comprobar una fuente en tres preguntas\n\n_{FICTION_ES}_\n\n"
        "**Grado:** 10 a 12. **Duración:** 45 minutos.\n\n"
        "## Objetivos\n\n- Preguntar quién escribió una fuente y cuándo.\n"
        "- Separar lo que dice la fuente de lo que dice quien la cita.\n\n"
        "## Actividad\n\nCada grupo recibe un párrafo con una afirmación y su fuente. "
        "Responde: ¿Dónde está la línea que lo dice? ¿Dice lo mismo, o algo parecido? "
        "¿Qué falta para estar seguros?\n\n## Cierre\n\n"
        "Una afirmación sin fuente se escribe como lo que es: una afirmación sin fuente.\n",
    )
    put(
        "lessons/02-robots-and-power-cuts.md",
        f"# What a robot does when the power goes out\n\n_{FICTION_EN}_\n\n"
        "**Grades:** 9 to 12. **Time:** two 50-minute periods.\n\n"
        "## Objectives\n\n- Draw the path of power from the wall to a motor.\n"
        "- Decide what the robot saves to memory before it stops.\n\n"
        "## Activity\n\nTeams add a capacitor and a battery to a test cart and cut the "
        "supply mid-run. Each team records what the cart remembers and what it forgets.\n\n"
        "## Check for understanding\n\nWhy is a log kept on the cart more useful than one "
        "kept in a notebook that was never charged?\n",
    )
    put(
        "lessons/03-open-lesson-who-keeps-the-log.md",
        f'# Who keeps the log\n\n_{FICTION_EN} The "open community lesson" of this demo\'s '
        "plan is a stand-in written for the demo, not a real lesson._\n\n"
        'Adapted from "Who Keeps the Log", a fictional open lesson, shared for reuse with '
        "credit.\n\n## Key idea\n\n"
        f"{LESSON_LINE}\n\n"
        "## Activity\n\nStudents compare two logs of the same afternoon, one kept by the people "
        "it describes and one kept by someone else, and write down what each leaves out.\n",
    )


# --- the grant draft (English) ------------------------------------------------


def make_draft() -> None:
    put(
        "grants/draft.md",
        f"# Escuela Superior La Ceiba: robotics and AI-literacy lab (draft 3)\n\n"
        f"_{FICTION_EN} Numbers marked invented are invented._\n\n"
        "## Need\n\n"
        f"Our school went 76 days without grid power after Hurricane Maria. Outages have cost "
        f"the school about {CLAIMED} since then. A lab that runs on its own batteries lets "
        "students keep working, and keep records, when the grid does not.\n\n"
        "## Background\n\n"
        "The Puerto Rico Science, Technology and Research Trust holds a Type 2 engine award "
        "from the National Science Foundation, and we would like to build on its regional "
        "network. LUMA Energy took over the grid in June 2021, and our log has kept filling "
        "since.\n\n"
        "The island's manufacturing base was shaped by federal tax policy. The credit ended in "
        "2005, after a phase-out that began in 1996, and plants like the one my father worked "
        "at closed in the years after.\n\n"
        "## Why records\n\n"
        f'As the open lesson puts it, "{DRAFT_QUOTE}" We teach students to keep the log '
        "themselves.\n\n"
        "## Sources\n\n"
        "- NBC News, on LUMA taking over the grid: "
        "https://www.nbcnews.com/news/latino/puerto-rico-private-company-takes-power-utility-service-rcna1091\n"
        "- Congressional Research Service report RS20695: "
        "https://www.everycrsreport.com/reports/RS20695.html\n"
        "- Our own outage log, 2017 to 2026 (invented): `log/outages.txt`\n",
    )


def make_names() -> None:
    (HERE / "names.txt").write_text("\n".join(sorted(CAST)) + "\n", encoding="utf-8")


def make() -> None:
    for f in (
        make_log,
        make_receipts,
        make_mail,
        make_interview,
        make_lessons,
        make_draft,
        make_names,
    ):
        f()


# --- the answer key, read back -------------------------------------------------


def check() -> list[str]:
    bad: list[str] = []

    def need(ok: bool, what: str) -> None:
        if not ok:
            bad.append(what)

    def read(rel: str) -> str:
        return (LIFE / rel).read_text(encoding="utf-8")

    draft = read("grants/draft.md")
    need("Type 2 engine award" in draft, "C1: the draft says Type 2")
    need(CLAIMED in draft, "C2: the draft says $40,000")
    lines = read("receipts/outage-costs.csv").splitlines()
    rows = list(csv.DictReader(x for x in lines if not x.startswith("#")))
    cents = sum(
        round(float(r["monto"].lstrip("$").replace(",", "")) * 100) for r in rows
    )
    need(
        cents == TOTAL_CENTS, f"C2: the receipts total {cents / 100:.2f}, not 14873.50"
    )
    need(cents != 40_000 * 100, "C2: the receipts must not total the claim")
    need(
        "June 2021" in draft and "2021-06-01 LUMA" in read("log/outages.txt"),
        "C3: LUMA, June 2021",
    )
    lesson = read("lessons/03-open-lesson-who-keeps-the-log.md")
    need(
        LESSON_LINE in lesson and DRAFT_QUOTE in draft and LESSON_LINE not in draft,
        "C4: the quote",
    )
    need(
        LESSON_LINE.replace(" alone", "") == DRAFT_QUOTE, "C4: exactly one word dropped"
    )
    need("began in 1996" in draft and "ended in 2005" in draft, "C5: the draft's years")
    need(
        "se acabó en el noventa y seis" in read("notes/ernesto-interview.vtt"),
        "C5: the father's year",
    )
    need(
        "se terminó en 2005" in read("notes/nota-credito-936.md"), "C5: her note's year"
    )
    log = read("log/outages.txt")
    need("2017-12-04 Día 76: volvió la luz" in log, "C6: 76 days in the log")
    need(
        (POWER_BACK - MARIA).days + 1 == 76,
        "C6: 76 is the days from Maria to the return",
    )
    need("casi 40 mil voltios" in log, "T3: the voltage line")
    need(
        "$6,000" in read("mail/2018-02-09-tomas.eml")
        and any(r["monto"] == "$6,240.00" for r in rows),
        "T2",
    )
    for p in sorted(LIFE.rglob("*")):
        if p.is_file():
            t = p.read_text(encoding="utf-8")
            need(
                "FICCIÓN" in t or "FICTION" in t,
                f"fiction header: {p.relative_to(LIFE)}",
            )
    allx = "".join(
        p.read_text(encoding="utf-8") for p in LIFE.rglob("*") if p.is_file()
    )
    need("787-555-01" in allx and "@example." in allx, "reserved ranges")
    return bad


def main(argv: list[str]) -> int:
    if argv == ["--check"]:
        bad = check()
        for b in bad:
            print("FAILS:", b)
        print("PLANTED.md holds" if not bad else f"{len(bad)} planted things missing")
        return 1 if bad else 0
    if argv:
        print("usage: make_life.py [--check]", file=sys.stderr)
        return 2
    make()
    print(f"wrote {sum(1 for p in LIFE.rglob('*') if p.is_file())} files to {LIFE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
