"""subscriptions: lines with their own date and an amount to the cent, grouped
by what they were for; only a rhythm of a month (three payments) or a year
(two) makes one; the latest amount, the earlier said; nothing cancelled."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "subscriptions.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("subscriptions", SCRIPT)
sb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sb)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).write_text(text)
    b = tmp_path / "box"
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b


def test_an_amount_is_written_to_the_cent_and_a_bare_whole_number_is_not_one():
    p = sb.paid
    assert p("2026-01-05 NETFLIX -15.99 card") == "15.99"
    assert p("paid £1,240.50 rent") == "1240.50"
    assert p("$9.00 coffee") == "9.00"
    assert p("rent 1200") == ""
    assert p("1.5 hours") == ""
    assert p("version 1.2.3") == ""
    assert p("ref 12345.678") == ""
    assert p("") == ""
    assert p("first 3.50 then 4.00") == "3.50"


def test_what_a_line_was_for_is_its_letters_without_dates_numbers_and_stock_words():
    w = sb.what
    assert w("2026-01-05  NETFLIX.COM  -15.99  card purchase") == "netflix"
    assert w("05/01/2026 DD Northern Energy 68.00 debit") == "dd northern energy"
    assert w("2026-01-05 Spotify Premium Family Plan 16.99") == "spotify premium family"
    assert w("2026-01-05 The Gym 29.00") == "gym"
    assert w("2026-01-05 A 15.99") == ""
    assert w("2026-01-05 15.99") == ""


def test_a_rhythm_needs_every_gap_about_a_month_or_a_year():
    r = sb.rhythm
    month = ["20260105", "20260205", "20260305"]
    assert r(month) == "monthly"
    assert r(month[:2]) == "", "two payments a month apart are not yet a rhythm"
    assert r(["20260101", "20260201", "20260305"]) == "monthly"
    assert r(["20260101", "20260127", "20260224"]) == "monthly", "26 days is a month"
    assert r(["20260101", "20260125", "20260224"]) == "", "25 is not"
    assert r(["20260101", "20260205", "20260312"]) == "monthly", "35 is"
    assert r(["20260101", "20260206", "20260312"]) == "", "36 is not"
    assert r(["20260105", "20260205", "20260320"]) == "", "one odd gap spoils it"
    assert r(["20250105", "20260105"]) == "yearly"
    assert r(["20250101", "20251222"]) == "yearly", "355 is a year"
    assert r(["20250101", "20251221"]) == "", "354 is not"
    assert r(["20250101", "20260111"]) == "yearly", "375 is"
    assert r(["20250101", "20260112"]) == "", "376 is not"
    assert r(["20250105"]) == "" and r([]) == ""
    assert r(["20250105", "20260105", "20270105"]) == "yearly"


def chunk(text: str, path: str = "bank.csv") -> list[dict]:
    return [{"path": path, "line": 1, "text": text}]


STATEMENT = (
    "2026-01-05,NETFLIX.COM,-12.99\n2026-02-05,NETFLIX.COM,-12.99\n2026-03-05,NETFLIX.COM,-15.99\n"
    "2026-01-02,GYM,-29.00\n2026-02-01,GYM,-29.00\n2026-03-03,GYM,-29.00\n2026-04-02,GYM,-29.00\n"
    "2025-11-02,DROPBOX,-119.88\n2026-11-02,DROPBOX,-119.88\n"
    "2026-01-09,COFFEE,-4.50\n2026-01-16,COFFEE,-4.50\n2026-01-23,COFFEE,-4.50\n2026-03-20,COFFEE,-4.50\n"
)  # fmt: skip


def test_only_a_payment_on_a_rhythm_is_a_subscription_and_the_latest_amount_counts():
    got = {s["what"]: s for s in sb.found(chunk(STATEMENT))}
    assert set(got) == {"netflix", "gym", "dropbox"}, (
        "a coffee on Fridays and then not is a habit"
    )
    n = got["netflix"]
    assert (n["amount"], n["kind"], n["was"], n["count"]) == (
        "15.99",
        "monthly",
        "12.99",
        3,
    )
    assert n["last"] == date(2026, 3, 5) and n["next"] == date(2026, 4, 4)
    d = got["dropbox"]
    assert (d["kind"], d["next"], d["year"], d["was"]) == (
        "yearly",
        date(2027, 11, 2),
        119.88,
        "",
    )
    assert got["gym"]["year"] == 348.0 and got["gym"]["count"] == 4


def test_was_is_the_latest_different_amount_even_when_only_the_one_before_differs():
    text = "2026-01-05,GYM,-15.99\n2026-02-04,GYM,-12.99\n2026-03-06,GYM,-15.99\n"
    (sub,) = sb.found(chunk(text))
    assert (sub["amount"], sub["was"]) == ("15.99", "12.99")


def test_the_same_day_in_two_files_is_one_payment_and_a_line_needs_its_own_date():
    both = chunk("2026-01-05,GYM,-29.00\n2026-02-04,GYM,-29.00\n", "a.csv") + chunk(
        "2026-01-05,GYM,-29.00\n2026-03-06,GYM,-29.00\n", "b.csv"
    )
    got = sb.found(both)
    assert [s["count"] for s in got] == [3], "Jan 5 is one payment, not two"
    undated = chunk("2026-01-05\nGYM -29.00\nGYM -29.00\nGYM -29.00\n")
    assert sb.found(undated) == [], "a line borrows no date from above"
    assert sb.payments(chunk("Total 5.00 and more\n")) == {}


def test_the_listing_dearest_a_year_first_with_totals(tmp_path):
    b = box(tmp_path, {"bank.csv": STATEMENT})
    got = run("--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "gym         29.00  monthly  last 2026-04-02  next about 2026-05-02  (4 payments)",
        "netflix     15.99  monthly  last 2026-03-05  next about 2026-04-04  (3 payments, was 12.99)",
        "dropbox    119.88  yearly   last 2026-11-02  next about 2027-11-02  (2 payments)",
        "3 subscriptions: about 44.99 a month, 659.76 a year",
    ]
    assert run("--box", str(b)).stdout == got.stdout


def test_one_subscription_is_singular_and_nothing_is_42(tmp_path):
    b = box(
        tmp_path,
        {
            "bank.csv": "2026-01-05,GYM,-29.00\n2026-02-04,GYM,-29.00\n2026-03-06,GYM,-29.00\n"
        },
    )
    assert (
        run("--box", str(b)).stdout.splitlines()[-1]
        == "1 subscription: about 29.00 a month, 348.00 a year"
    )
    b2 = tmp_path / "other"
    b2.mkdir()
    quiet = box(b2, {"garden.md": "Tomatoes want sun.\n"})
    got = run("--box", str(quiet))
    assert got.returncode == 42 and "monthly or yearly rhythm" in got.stdout


def test_a_bad_command_line_is_refused_and_nothing_is_written(tmp_path):
    b = box(tmp_path, {"garden.md": "x\n"})
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for argv in ([], ["--box"], ["--box", str(b), "stray"], ["--box", str(tmp_path)]):
        assert run(*argv).returncode == 2, argv
    assert "subscriptions.py" in run().stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'subscriptions.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "habits"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )
