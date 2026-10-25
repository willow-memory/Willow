"""cal: .ics events and .vcf contacts become dated, readable text the kernel can
serve. Every sample is written out inside the test; example.org and example.net
only, and phone numbers in the 555-01xx range."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
CAL = HERE / "cal.py"
spec = importlib.util.spec_from_file_location("cal", CAL)
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)
NOW = ["--now", "2026-10-23T00:00:00Z"]
CRLF = "\r\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(str(CAL), "mirror", "--from", str(folder), "--to", str(to))


def ics(*lines: str) -> str:
    body = ["BEGIN:VCALENDAR", "VERSION:2.0", *lines, "END:VCALENDAR"]
    return "".join(line + CRLF for line in body)


# A timed event with a location and a folded, escaped description; an all-day
# event written after it; a recurring event whose VALARM has its own DESCRIPTION.
HOME_ICS = ics(
    "BEGIN:VEVENT",
    "DTSTART:20261028T140000Z",
    "SUMMARY:Tune - Ybarra",
    "LOCATION:Studio 2\\, Annex",
    "DESCRIPTION:Ask about the fee\\; bring a\\nspare string and the"
    + CRLF
    + "  setlist",
    "END:VEVENT",
    "BEGIN:VEVENT",
    "DTSTART;VALUE=DATE:20261021",
    "SUMMARY:Pay the water bill",
    "END:VEVENT",
    "BEGIN:VEVENT",
    "DTSTART:20261026T180000Z",
    "RRULE:FREQ=WEEKLY;BYDAY=MO",
    "SUMMARY:Choir practice",
    "BEGIN:VALARM",
    "TRIGGER:-PT15M",
    "ACTION:DISPLAY",
    "DESCRIPTION:Default alarm text",
    "END:VALARM",
    "END:VEVENT",
)

HOME_TXT = (
    "2026-10-21  Pay the water bill\n"
    "\n"
    "2026-10-26 18:00  Choir practice  (weekly, from this date)\n"
    "repeats: FREQ=WEEKLY;BYDAY=MO\n"
    "\n"
    "2026-10-28 14:00  Tune - Ybarra\n"
    "where: Studio 2, Annex\n"
    "notes: Ask about the fee; bring a\n"
    "  spare string and the setlist\n"
)

VCF = "".join(
    line + CRLF
    for line in [
        "BEGIN:VCARD",
        "VERSION:3.0",
        "FN:Ana Example",
        "N:Example;Ana;;;",
        "TEL;TYPE=CELL:+1-555-0142",
        "EMAIL:ana@example.org",
        "ADR;TYPE=HOME:;;12 Oak Lane;Springfield;;;",
        "BDAY:19900315",
        "END:VCARD",
        "BEGIN:VCARD",
        "VERSION:3.0",
        "FN:Zoé Café",
        "END:VCARD",
        "BEGIN:VCARD",
        "VERSION:3.0",
        "N:Vale;Ben;;;",
        "END:VCARD",
    ]
)

CONTACTS_TXT = (
    "contact: Ana Example\n"
    "phone: +1-555-0142\n"
    "email: ana@example.org\n"
    "address: 12 Oak Lane, Springfield\n"
    "birthday: 1990-03-15\n"
    "\n"
    "contact: Zoé Café\n"
    "\n"
    "contact: Ben Vale\n"
)


def tree(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def make_folder(tmp_path: Path) -> Path:
    folder = tmp_path / "folder"
    (folder / "home").mkdir(parents=True)
    (folder / "work").mkdir()
    (folder / "home" / "cal.ics").write_text(HOME_ICS, encoding="utf-8")
    (folder / "work" / "Team.VCF").write_text(VCF, encoding="utf-8")
    return folder


def test_events_sorted_by_date_with_all_day_timed_location_notes_and_one_repeat(
    tmp_path,
):
    folder = make_folder(tmp_path)
    out = tmp_path / "mirror"
    got = mirror(folder, out)
    assert got.returncode == 0, got.stderr
    text = (out / "home" / "cal.ics.txt").read_bytes().decode("utf-8")
    assert text == HOME_TXT
    assert "\r" not in text and text.endswith("\n")
    assert text.count("repeats:") == 1
    assert "Default alarm text" not in text  # a VALARM's DESCRIPTION is not the event's


@pytest.mark.parametrize("rule, said", [
    ("FREQ=YEARLY", "yearly"),
    ("FREQ=WEEKLY;BYDAY=MO", "weekly"),
    ("FREQ=WEEKLY;INTERVAL=2", "every 2 weeks"),
    ("FREQ=MONTHLY;UNTIL=20260601T000000Z", "monthly, until 2026-06-01"),
    ("FREQ=DAILY;COUNT=10", "daily, 10 times"),
    ("FREQ=SECONDLY", "repeating"),
])  # fmt: skip
def test_a_repeat_is_said_in_words_on_its_first_line(rule, said):
    assert cal.in_words(rule) == said


def test_a_repeating_or_cancelled_event_says_so_where_it_is_quoted(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "home.ics").write_text(ics(
        "BEGIN:VEVENT", "DTSTART;VALUE=DATE:20221103", "RRULE:FREQ=YEARLY",
        "SUMMARY:Car rego due", "END:VEVENT",
        "BEGIN:VEVENT", "DTSTART:20260819T103000", "STATUS:CANCELLED",
        "SUMMARY:Skin check", "END:VEVENT",
    ), encoding="utf-8")  # fmt: skip
    assert mirror(folder, tmp_path / "m").returncode == 0
    lines = (tmp_path / "m" / "home.ics.txt").read_text().splitlines()
    assert lines[0] == "2022-11-03  Car rego due  (yearly, from this date)"
    assert lines[1] == "repeats: FREQ=YEARLY"
    assert lines[3] == "2026-08-19 10:30  Skin check  (cancelled)"


def test_folded_lines_unfolded_and_escapes_undone(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "a.ics").write_text(
        ics(
            "BEGIN:VEVENT",
            "DTSTART:20261104",
            "SUMMARY:Lunch with Ybarra\\, Mesa\\; and friends",
            "DESCRIPTION:one\\ntwo and the" + CRLF + "  end\\\\done",
            "END:VEVENT",
        ),
        encoding="utf-8",
    )
    out = tmp_path / "m"
    assert mirror(folder, out).returncode == 0
    text = (out / "a.ics.txt").read_text(encoding="utf-8")
    assert text.startswith("2026-11-04  Lunch with Ybarra, Mesa; and friends\n")
    assert "notes: one\n  two and the end\\done\n" in text
    assert "\\n" not in text and "\\," not in text and "\\;" not in text


def test_contacts_with_phone_email_address_and_birthday(tmp_path):
    folder = make_folder(tmp_path)
    out = tmp_path / "mirror"
    assert mirror(folder, out).returncode == 0
    text = (out / "work" / "Team.VCF.txt").read_bytes().decode("utf-8")
    assert text == CONTACTS_TXT


def test_mirror_names_skips_hidden_and_counts_what_it_cannot_read(tmp_path):
    folder = make_folder(tmp_path)
    (folder / "home" / "broken.ics").write_text("this is not a calendar\n")
    (folder / "work" / "bad.vcf").write_bytes(b"\xff\xfe BEGIN:VCARD\n")
    (folder / ".hidden").mkdir()
    (folder / ".hidden" / "secret.ics").write_text(HOME_ICS, encoding="utf-8")
    (folder / "home" / ".dotted.ics").write_text(HOME_ICS, encoding="utf-8")
    (folder / "notes.txt").write_text("not a calendar\n")
    out = tmp_path / "mirror"
    got = mirror(folder, out)
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 2 files to {out}; skipped 2"
    assert sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()) == [
        "home/cal.ics.txt",
        "work/Team.VCF.txt",
    ]


def test_nothing_readable_exits_42(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "junk.ics").write_text("nothing here\n")
    out = tmp_path / "m"
    got = mirror(folder, out)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {out}; skipped 1"


def test_refuses_mirror_inside_folder_and_folder_inside_mirror(tmp_path):
    folder = make_folder(tmp_path)
    inside = folder / "out"
    got = mirror(folder, inside)
    assert got.returncode == 2 and got.stderr.startswith("refused:")
    assert not inside.exists()

    box = tmp_path / "box"
    nested = box / "folder"
    nested.mkdir(parents=True)
    (nested / "cal.ics").write_text(HOME_ICS, encoding="utf-8")
    got = mirror(nested, box)
    assert got.returncode == 2 and got.stderr.startswith("refused:")
    assert sorted(p.name for p in box.iterdir()) == ["folder"]

    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and got.stderr.startswith("refused:")


def test_originals_are_not_changed_and_nothing_is_added_to_folder(tmp_path):
    folder = make_folder(tmp_path)
    before = tree(folder)
    assert mirror(folder, tmp_path / "mirror").returncode == 0
    assert tree(folder) == before


def test_two_runs_give_identical_bytes(tmp_path):
    folder = make_folder(tmp_path)
    first, second = tmp_path / "one", tmp_path / "two"
    assert mirror(folder, first).returncode == 0
    assert mirror(folder, second).returncode == 0
    assert tree(first) == tree(second)


def test_kernel_serves_the_event_paragraph(tmp_path):
    folder = make_folder(tmp_path)
    pile = tmp_path / "pile"
    assert mirror(folder, pile).returncode == 0
    box = tmp_path / "box"
    key = tmp_path / "k"
    init = run(
        str(KERNEL),
        "init",
        "--box",
        str(box),
        "--pile",
        str(pile),
        "--key",
        str(key),
        *NOW,
    )
    assert init.returncode == 0, init.stderr
    got = run(
        str(KERNEL),
        "bite",
        "--box",
        str(box),
        *NOW,
        "when is the ybarra tuning",
    )
    assert got.returncode == 0, got.stdout + got.stderr
    doc = json.loads(got.stdout)
    assert doc["state"] == "populated"
    assert doc["served"][0]["where"] == "home/cal.ics.txt:6"
    assert doc["served"][0]["text"].startswith(
        "2026-10-28 14:00  Tune - Ybarra\nwhere: Studio 2, Annex\n"
    )
