"""More of Marisol's life, for freeze 3: python3 make_life_3.py [--check]

Writes `life-more/`, beside `life/` and never inside it, so the folder runs 1
and 2 read is the same bytes it was: four kinds of file her work leaves that
`life/` doesn't have, each for the willow reader that reads it.

    calendar/escuela-2022-23.ics      the district's school-year calendar   calendar
    phone/sms-backup.xml              her texts with Tomás (Android backup)  sms
    budget/presupuesto-laboratorio.xlsx  the lab's budget, one sheet          office
    sensors/history.json              the lab's battery bank (Home Assistant) home-sensors
    grants/draft-3.md                 the draft's new paragraph: never boxed

The same bytes every run (no clock, no randomness: the zip's dates are fixed).
`--check` reads them back and holds them to PLANTED.md's freeze-3 section.

Fiction throughout, as make_life.py's is. The Spanish was written by a model,
not by an islander: a Puerto Rican reader must read it for what rings false
before this goes beyond its author.
"""

from __future__ import annotations

import json
import sys
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MORE = HERE / "life-more"
FICTION_ES = "FICCIÓN. Inventado para una demostración; no describe a ninguna persona, escuela ni empresa reales."
FICTION_EN = (
    "FICTION. Invented for a demo; no real person, school or company is described."
)

# --- what is planted (PLANTED.md's freeze-3 section says the same) -----------
CLOSURES = [  # school days closed for an outage, 2022-23 (invented): seven
    date(2022, 9, 19), date(2022, 9, 20), date(2022, 9, 21),  # Fiona
    date(2022, 11, 14), date(2023, 2, 6), date(2023, 3, 27), date(2023, 4, 24),
]  # fmt: skip
CLOSED = "Cierre por apagón"
OTHER_EVENTS = [  # the year's calendar is more than its closures
    (date(2022, 8, 15), "Inicio de clases", "Primer día del año escolar 2022-2023."),
    (date(2022, 11, 18), "Feria científica", "Proyectos de robótica en la cancha."),
    (date(2023, 5, 26), "Graduación", "Clase de 2023."),
]
CLAIMED_DAYS = 9  # what the draft says: 9 days lost (it's 7)

ARRIVED = "Ya llegaron los $6,000"
BUDGET = [  # line, units, price (each written with its $, as amounts reads it)
    ("Chromebooks para el laboratorio", 12, 28900),
    ("Router y punto de acceso", 1, 18500),
    ("Kits de robótica", 6, 6450),
]  # fmt: skip
BUDGET_TOTAL_CENTS = sum(n * c for _, n, c in BUDGET)  # $4,040.00
CHROMEBOOK_LINE_CENTS = 12 * 28900  # $3,468.00
DRAFT_ASK = "$18,000"  # 30 laptops at $600: the draft's figure, nowhere in the budget

SCHOOL_DAY_HOURS = 6.5  # the bell schedule's day (invented)
OUTAGE_RUNTIMES = {  # hours the bank ran the lab on an outage day (invented)
    date(2026, 9, 3): 4.5, date(2026, 9, 9): 4.0, date(2026, 9, 10): 5.0,
}  # fmt: skip
SENSOR_DAYS = [date(2026, 9, 1) + timedelta(days=i) for i in range(14)]
CHARGE = "Lab battery bank charge"
RUNTIME = "Lab backup runtime"


def put(rel: str, data: bytes) -> None:
    path = MORE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def money(cents: int) -> str:
    return f"${cents // 100:,}.{cents % 100:02d}"


# --- the calendar -------------------------------------------------------------
def make_calendar() -> None:
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Distrito Escolar de Ponce//ficcion//ES",
           f"X-WR-CALDESC:{FICTION_ES}"]  # fmt: skip
    events = [(d, f"{CLOSED}: no hay clases", "Aviso del distrito: la escuela cierra por falta de servicio eléctrico.")
              for d in CLOSURES] + OTHER_EVENTS  # fmt: skip
    for i, (d, summary, notes) in enumerate(sorted(events), 1):
        out += [
            "BEGIN:VEVENT",
            f"UID:la-ceiba-2022-23-{i:02d}@example.org",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{summary}",
            "LOCATION:Escuela Superior La Ceiba\\, Ponce",
            f"DESCRIPTION:{notes}",
            "END:VEVENT",
        ]
    out.append("END:VCALENDAR")
    put("calendar/escuela-2022-23.ics", ("\r\n".join(out) + "\r\n").encode("utf-8"))


# --- her texts with Tomás (an Android SMS backup) -----------------------------
def ms(y, mo, d, h, mi) -> int:
    return int(
        datetime(y, mo, d, h, mi, tzinfo=timezone(timedelta(hours=-4))).timestamp()
        * 1000
    )


def make_sms() -> None:
    texts = [  # (when, type: 1 received, 2 sent, body)
        (ms(2018, 2, 9, 21, 20), 1, "Te acabo de mandar el email con lo de la transferencia para las baterías."),
        (ms(2018, 2, 9, 21, 31), 2, "Gracias, Tomás. Te aviso cuando lleguen."),
        (ms(2018, 2, 12, 9, 30), 2, f"{ARRIVED}. Gracias, hermano. El banco de baterías se instala el martes."),
        (ms(2018, 2, 12, 9, 41), 1, "Qué bueno. Mándame foto cuando esté puesto."),
        (ms(2018, 2, 20, 16, 5), 2, "Ya está puesto. El laboratorio prendió con el banco por primera vez."),
    ]  # fmt: skip
    rows = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            f"<!-- {FICTION_ES} -->",
            f'<smses count="{len(texts)}">']  # fmt: skip
    for when, kind, body in texts:
        body = body.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        rows.append(f'  <sms protocol="0" address="787-555-0121" date="{when}" type="{kind}" '
                    f'body="{body}" read="1" status="-1" contact_name="Tomás Beltrán" />')  # fmt: skip
    rows.append("</smses>")
    put("phone/sms-backup.xml", ("\n".join(rows) + "\n").encode("utf-8"))


# --- the lab's budget (.xlsx, one sheet, inline strings) -----------------------
NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
RNS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def cell(ref: str, value: str | int) -> str:
    if isinstance(value, int):
        return f'<c r="{ref}"><v>{value}</v></c>'
    v = value.replace("&", "&amp;").replace("<", "&lt;")
    return f'<c r="{ref}" t="inlineStr"><is><t>{v}</t></is></c>'


def make_budget() -> None:
    rows = [["Partida", "Cantidad", "Precio", "Total"]]
    rows += [[name, n, money(c), money(n * c)] for name, n, c in BUDGET]
    rows += [["Total del presupuesto", "", "", money(BUDGET_TOTAL_CENTS)], [FICTION_ES]]
    xml_rows = []
    for i, row in enumerate(rows, 1):
        cells = "".join(
            cell(f"{'ABCD'[j]}{i}", v) for j, v in enumerate(row) if v != ""
        )
        xml_rows.append(f'<row r="{i}">{cells}</row>')
    parts = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>",
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>",
        "xl/workbook.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook {NS} {RNS}>'
        '<sheets><sheet name="Presupuesto" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>",
        "xl/worksheets/sheet1.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet {NS}>'
        f"<sheetData>{''.join(xml_rows)}</sheetData></worksheet>",
    }
    path = MORE / "budget/presupuesto-laboratorio.xlsx"
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for (
            name,
            text,
        ) in parts.items():  # fixed dates and modes: the same bytes every run
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, text.encode("utf-8"))


# --- the battery bank (Home Assistant history) ---------------------------------
def make_sensors() -> None:
    charge, runtime = [], []
    for d in SENSOR_DAYS:
        out = d in OUTAGE_RUNTIMES
        for hour, pct in ((8, 98), (11, 71 if out else 97), (14, 22 if out else 96)):
            charge.append({"entity_id": "sensor.lab_battery_bank_charge", "state": str(pct),
                           "attributes": {"friendly_name": CHARGE, "unit_of_measurement": "%"},
                           "last_changed": f"{d}T{hour:02d}:00:00-04:00"})  # fmt: skip
        runtime.append({"entity_id": "sensor.lab_backup_runtime", "state": str(OUTAGE_RUNTIMES.get(d, 0.0)),
                        "attributes": {"friendly_name": RUNTIME, "unit_of_measurement": "h"},
                        "last_changed": f"{d}T15:00:00-04:00"})  # fmt: skip
    put(
        "sensors/history.json",
        (json.dumps([charge, runtime], indent=1) + "\n").encode("utf-8"),
    )


# --- the draft's new paragraph (never boxed: its claims are what is checked) --
def make_draft() -> None:
    put(
        "grants/draft-3.md",
        (
            f"# Grant draft, a new paragraph\n\n_{FICTION_EN}_\n\n"
            f"Outages closed the school for {CLAIMED_DAYS} class days in 2022-23 (C7). "
            "My brother's $6,000 for the battery bank arrived in February 2018 (C8). "
            f"We need 30 laptops at $600 each, {DRAFT_ASK} in all (C9). "
            "The lab's battery bank runs the lab through a full school day (C10).\n"
        ).encode("utf-8"),
    )


def make() -> None:
    make_calendar()
    make_sms()
    make_budget()
    make_sensors()
    make_draft()


def check() -> list[str]:
    """What PLANTED.md's freeze-3 section says, read back from the files."""
    bad = []
    ics = (MORE / "calendar/escuela-2022-23.ics").read_text(encoding="utf-8")
    if ics.count(f"SUMMARY:{CLOSED}") != len(CLOSURES) or len(CLOSURES) != 7:
        bad.append("the calendar holds seven closures")
    if f"{CLAIMED_DAYS} class days" not in (MORE / "grants/draft-3.md").read_text(
        encoding="utf-8"
    ):
        bad.append("the draft says nine days")
    if ARRIVED not in (MORE / "phone/sms-backup.xml").read_text(encoding="utf-8"):
        bad.append("the texts say the money arrived")
    with zipfile.ZipFile(MORE / "budget/presupuesto-laboratorio.xlsx") as zf:
        sheet = zf.read("xl/worksheets/sheet1.xml").decode("utf-8")
    for want in (money(CHROMEBOOK_LINE_CENTS), money(BUDGET_TOTAL_CENTS)):
        if want not in sheet:
            bad.append(f"the budget holds {want}")
    if DRAFT_ASK in sheet:
        bad.append("the budget never says the draft's $18,000")
    doc = json.loads((MORE / "sensors/history.json").read_text(encoding="utf-8"))
    hours = [float(s["state"]) for s in doc[1]]
    if not (
        max(hours) < SCHOOL_DAY_HOURS
        and sum(h > 0 for h in hours) == len(OUTAGE_RUNTIMES)
    ):
        bad.append("the bank never ran a full school day, on three outage days")
    return bad


def main(argv: list[str]) -> int:
    if argv not in ([], ["--check"]):
        print(__doc__.splitlines()[0], file=sys.stderr)
        return 2
    if argv == ["--check"]:
        bad = check()
        print("\n".join(bad) or "life-more holds what was planted")
        return 1 if bad else 0
    make()
    print(f"wrote {MORE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
