"""spent's tests: money out (a minus, or a money-out column) on lines that hold
all of the question's words, through the words list, in a period, each payment
once, each line cited; money in and an unsigned amount never added; a date
that reads both ways never guessed; currencies never added together."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "spent.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = "2026-10-24T09:00:00Z"
spec = importlib.util.spec_from_file_location("spent", SCRIPT)
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)  # fmt: skip


def box(tmp_path: Path, files: dict, words: str = "") -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    argv = [sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"), "--now", NOW]  # fmt: skip
    if words:
        wl = tmp_path / "words.txt"
        wl.write_text(words)
        wl.chmod(0o600)
        argv += ["--words", str(wl)]
    got = subprocess.run(argv, capture_output=True, text=True)
    assert got.returncode == 0, got.stderr
    return b


def ask(b: Path, q: str, *more: str) -> subprocess.CompletedProcess:
    return run("--box", str(b), "--now", NOW, *more, q)


STATEMENT = (
    "2026-01-25  -446.06  BPAY ORIGIN ENERGY 6631094\n"
    "2026-02-02  -95.00  TELSTRA DIRECT DEBIT\n"
    "2026-04-25  -479.80  BPAY ORIGIN ENERGY 6631094\n"
    "2025-10-25  -608.53  BPAY ORIGIN ENERGY 6631094\n"
    "2026-03-15  +3292.34  AUSPRIME ENERGY PENSION\n"
    "2026-07-25  -728.50  BPAY ORIGIN ENERGY 6631094\n"
)


def test_an_amount_is_written_to_the_cent_and_which_way_it_went_is_its_sign():
    a = sp.amount_of
    assert a("2026-01-25  -446.06  ORIGIN") == ("out", "", 44606)
    assert a('25/01/2026,"-446.06","ORIGIN","+9.99"') == ("out", "", 44606)
    assert a("+3292.34 pension") == ("in", "", 329234)
    assert a("paid 45.20 for it") == ("", "", 4520)  # no sign: it does not say
    assert a("-$9.00 coffee") == ("out", "$", 900)
    assert a("$-9.00 coffee") == ("out", "$", 900)
    assert a("-£1,240.50 rent") == ("out", "£", 124050)
    assert a("−€12.30 shop") == ("out", "€", 1230)  # the minus sign
    assert a("INV-100.00 sent") == ("", "", 10000)  # a hyphen glued to a word
    assert a("2026-10-24-5.00") == ("", "", 500)  # and to a date
    assert a("rent 1200") is None and a("1.5 hours") is None and a("version 1.2.3") is None  # fmt: skip
    assert a("25.01.2026") is None and a("") is None


def test_the_total_is_the_lines_written_as_money_out_each_cited_with_its_file_and_line(
    tmp_path,
):
    b = box(tmp_path, {"bank.txt": STATEMENT})
    got = ask(b, "how much did we spend on origin")
    assert got.returncode == 0, got.stderr
    out = got.stdout.splitlines()
    assert out[0] == "spent: origin" and out[1].startswith("period: every date, up to 2026-10-24")  # fmt: skip
    assert "2026-01-25  446.06  bank.txt:1  2026-01-25  -446.06  BPAY ORIGIN ENERGY 6631094" in out  # fmt: skip
    assert any(ln.startswith("2025-10-25  608.53  bank.txt:4") for ln in out)
    assert (
        out[-1] == "total: 2,262.89 in 4 payments"
    )  # 446.06 + 479.80 + 608.53 + 728.50
    assert (
        "AUSPRIME" not in got.stdout
    )  # a plus is money in: said "energy"? it is not "origin"
    assert "TELSTRA" not in got.stdout  # a line that never said it


def test_a_plus_is_money_in_and_an_unsigned_amount_is_listed_but_never_added(tmp_path):
    b = box(tmp_path, {"bank.txt": "2026-03-01  +500.00  ORIGIN ENERGY REFUND\n2026-03-02  81.10  ORIGIN ENERGY\n2026-03-03  -70.00  ORIGIN ENERGY\n"})  # fmt: skip
    got = ask(b, "origin energy")
    assert (
        got.stdout.splitlines()[-2:]
        == [
            "total: 70.00 in 1 payment",
            "  not added, it is written with no sign (money in, or only a price): bank.txt:2  2026-03-02  81.10  ORIGIN ENERGY",  # fmt: skip
        ]
    )
    assert "REFUND" not in got.stdout  # money in says nothing at all


def test_only_unsigned_lines_found_is_nothing_found_and_says_which_were_left(tmp_path):
    b = box(tmp_path, {"bank.txt": "2026-03-02  81.10  ORIGIN ENERGY\n"})
    got = ask(b, "origin")
    assert got.returncode == 42
    assert "No money-out line in this period holds all of: origin." in got.stdout
    assert "bank.txt:1" in got.stdout


def test_a_money_out_column_is_money_out_and_a_money_in_column_is_not(tmp_path):
    csv = (
        "Date,Description,Debit,Credit,Balance\n"
        "2026-02-01,ORIGIN ENERGY,300.00,,1000.00\n"
        "2026-02-02,ORIGIN ENERGY REFUND,,50.00,1050.00\n"
        "2026-02-03,ORIGIN ENERGY,£20.50,,1030.00\n"
        "2026-02-04,ORIGIN ENERGY,,,900.00\n"
    )
    b = box(tmp_path, {"s.csv": csv})
    got = ask(b, "origin energy")
    assert got.stdout.splitlines()[-3:] == ["total: 300.00 in 1 payment (no currency sign)", "total: £20.50 in 1 payment", "currencies are never added together"]  # fmt: skip
    assert "REFUND" not in got.stdout and "currencies are never added together" in got.stdout  # fmt: skip
    # the same rows in a file with no such header have no column to read: unsigned
    b2 = box(tmp_path / "x", {"s.csv": csv.split("\n", 1)[1]})
    assert ask(b2, "origin energy").returncode == 42


def test_a_money_out_column_with_a_minus_is_still_money_out(tmp_path):
    csv = "Date,Description,Paid out,Paid in\n2026-02-01,ORIGIN ENERGY,-12.00,\n2026-02-02,ORIGIN ENERGY,+9.00,\n2026-02-03,ORIGIN ENERGY,,+9.00\n"  # fmt: skip
    got = ask(box(tmp_path, {"s.csv": csv}), "origin")
    assert got.stdout.splitlines()[-1] == "total: 12.00 in 1 payment"


def test_this_year_and_last_year_are_the_calendar_years_of_now(tmp_path):
    b = box(tmp_path, {"bank.txt": STATEMENT})
    this = ask(b, "how much did we spend on origin this year")
    assert "period: calendar 2026, 2026-01-01 to 2026-10-24 (so far)" in this.stdout
    assert this.stdout.splitlines()[-1] == "total: 1,654.36 in 3 payments"
    assert "2025-10-25" not in this.stdout
    last = ask(b, "how much did we spend on origin last year")
    assert "period: calendar 2025, 2025-01-01 to 2025-12-31\n" in last.stdout
    assert last.stdout.splitlines()[-1] == "total: 608.53 in 1 payment"


def test_a_financial_year_starts_in_july_unless_the_start_month_is_given(tmp_path):
    b = box(tmp_path, {"bank.txt": STATEMENT})
    this = ask(b, "how much did we spend on origin this financial year")
    assert "period: financial year 2026-27, starting 1 July, 2026-07-01 to 2026-10-24 (so far)" in this.stdout  # fmt: skip
    assert this.stdout.splitlines()[-1] == "total: 728.50 in 1 payment"
    last = ask(b, "what did we spend on origin last financial year")
    assert "period: financial year 2025-26, starting 1 July, 2025-07-01 to 2026-06-30\n" in last.stdout  # fmt: skip
    assert last.stdout.splitlines()[-1] == "total: 1,534.39 in 3 payments"  # 608.53 + 446.06 + 479.80  # fmt: skip
    fy = ask(b, "origin this fy")  # the question's own word
    assert "financial year 2026-27" in fy.stdout
    uk = ask(b, "origin", "--year", "financial:4")  # a start month, as a flag: April
    assert "period: financial year 2026-27, starting 1 April, 2026-04-01 to 2026-10-24 (so far)" in uk.stdout  # fmt: skip
    assert (
        uk.stdout.splitlines()[-1] == "total: 1,208.30 in 2 payments"
    )  # 479.80 + 728.50
    cal = ask(b, "origin", "--year", "calendar")
    assert "period: calendar 2026," in cal.stdout
    last_cal = ask(
        b, "origin last year", "--year", "financial:1"
    )  # month 1 is the calendar
    assert "period: calendar 2025," in last_cal.stdout


def test_the_period_function_places_the_year_by_its_start_month():
    p = sp.period
    assert p(date(2026, 6, 30), "this", True, 7)[1:] == (date(2025, 7, 1), date(2026, 6, 30))  # fmt: skip
    assert p(date(2026, 7, 1), "this", True, 7)[1:] == (date(2026, 7, 1), date(2027, 6, 30))  # fmt: skip
    assert p(date(2026, 7, 1), "last", True, 7)[1:] == (date(2025, 7, 1), date(2026, 6, 30))  # fmt: skip
    assert p(date(2026, 3, 31), "last", True, 4)[1:] == (date(2024, 4, 1), date(2025, 3, 31))  # fmt: skip
    assert p(date(2026, 4, 1), "this", True, 4)[1:] == (date(2026, 4, 1), date(2027, 3, 31))  # fmt: skip
    assert p(date(2026, 10, 24), "last", False, 7) == ("calendar 2025", date(2025, 1, 1), date(2025, 12, 31))  # fmt: skip
    assert p(date(2026, 10, 24), "this", True, 1)[0] == "calendar 2026"


def test_a_line_dated_after_now_is_not_spent_yet_and_is_said(tmp_path):
    b = box(tmp_path, {"bank.txt": "2026-10-20  -10.00  ORIGIN\n2026-10-24  -5.00  ORIGIN\n2026-11-25  -99.00  ORIGIN\n"})  # fmt: skip
    got = ask(b, "origin this year")
    assert (
        got.stdout.splitlines()[-2:]
        == [
            "total: 15.00 in 2 payments",
            "  not added, it is dated after 2026-10-24, not spent yet: bank.txt:3  2026-11-25  -99.00  ORIGIN",  # fmt: skip
        ]
    )
    assert "2025" not in ask(b, "origin last year").stdout.split("period:")[0]


def test_a_date_that_reads_both_ways_is_never_guessed_and_is_said(tmp_path):
    b = box(tmp_path, {"bank.csv.txt": "03/04/2026,-45.20,ORIGIN\n13/04/2026,-10.00,ORIGIN\n"})  # fmt: skip
    got = ask(b, "origin")
    assert (
        got.stdout.splitlines()[-2:]
        == [
            "total: 10.00 in 1 payment",
            "  not added, it is money out with no date it can read: bank.csv.txt:1  03/04/2026,-45.20,ORIGIN",  # fmt: skip
        ]
    )
    # a date is the line's own, never one above it
    b2 = box(tmp_path / "y", {"n.txt": "2026-04-01\n-30.00 ORIGIN\n"})
    assert ask(b2, "origin").returncode == 42


def test_the_same_payment_in_two_files_is_one_and_two_in_one_file_are_two(tmp_path):
    b = box(tmp_path, {
        "a.csv": "2026-02-01,-4.50,CAFE NERO\n2026-02-01,-4.50,CAFE NERO\n2026-02-03,-7.00,CAFE NERO\n",
        "b.txt": "2026-02-01  -4.50  CAFE NERO 55\n2026-02-03  -7.00  CAFE NERO DEAN ST\n2026-02-01  -4.50  CAFE NERO\n2026-02-01  -4.50  CAFE NERO\n",  # fmt: skip
    })  # fmt: skip
    got = ask(b, "cafe")
    # the 1st: two in a.csv, three in b.txt: three payments, b.txt's first two
    # being a.csv's; the 3rd: the one payment in both
    assert (
        got.stdout.splitlines()[-1] == "total: 20.50 in 4 payments"
    )  # 3 x 4.50 + 7.00
    assert "(also b.txt:1)" in got.stdout and "(also b.txt:3)" in got.stdout
    assert "(also b.txt:2)" in got.stdout and "b.txt:4  " in got.stdout


def test_two_payments_of_one_amount_on_a_day_to_two_places_are_two(tmp_path):
    two = {
        "a.txt": "2026-02-01  -4.50  CAFE NERO\n",
        "b.txt": "2026-02-01  -4.50  CAFE STARBUCKS\n",
    }
    got = ask(
        box(tmp_path, two), "cafe"
    )  # the word asked for is not what makes them one
    assert got.stdout.splitlines()[-1] == "total: 9.00 in 2 payments"
    # the same words, or a word besides the asked-for ones in common, make them one
    one = {
        "a.txt": "2026-02-01  -4.50  ORIGIN ENERGY\n",
        "b.txt": "2026-02-01  -4.50  BPAY ORIGIN ENERGY\n",
    }
    assert ask(box(tmp_path / "z", one), "origin").stdout.splitlines()[-1] == "total: 4.50 in 1 payment"  # fmt: skip
    same = {
        "a.txt": "2026-02-01  -4.50  ORIGIN\n",
        "b.txt": "2026-02-01,-4.50,ORIGIN\n",
    }
    assert ask(box(tmp_path / "y", same), "origin").stdout.splitlines()[-1] == "total: 4.50 in 1 payment"  # fmt: skip
    # another day, another amount, another currency: another payment
    other = {"a.txt": "2026-02-01  -4.50  ORIGIN ENERGY\n", "b.txt": "2026-02-02  -4.50  ORIGIN ENERGY\n", "c.txt": "2026-02-01  -4.51  ORIGIN ENERGY\n"}  # fmt: skip
    assert ask(box(tmp_path / "x", other), "origin").stdout.splitlines()[-1] == "total: 13.51 in 3 payments"  # fmt: skip
    cur = {
        "a.txt": "2026-02-01  -$4.50  ORIGIN ENERGY\n",
        "b.txt": "2026-02-01  -4.50  ORIGIN ENERGY\n",
    }
    assert (
        "in 1 payment (no currency sign)"
        in ask(box(tmp_path / "w", cur), "origin").stdout
    )


def test_a_line_must_hold_every_word_of_the_question_not_half(tmp_path):
    b = box(tmp_path, {"bank.txt": "2026-02-01  -30.00  ORIGIN ENERGY\n2026-02-02  -20.00  ORIGIN SUPER\n"})  # fmt: skip
    both = ask(b, "origin energy")
    assert both.stdout.splitlines()[-1] == "total: 30.00 in 1 payment"
    assert ask(b, "origin energy gas").returncode == 42  # one the line never said


def test_a_word_is_held_the_way_the_kernel_holds_it_and_a_plural_counts(tmp_path):
    b = box(tmp_path, {"bank.txt": "2026-02-01  -30.00  ENERGY BILL\n"})
    assert ask(b, "how much did we spend on energy bills").stdout.splitlines()[-1] == "total: 30.00 in 1 payment"  # fmt: skip


def test_the_words_list_says_what_the_person_calls_it(tmp_path):
    files = {"bank.txt": STATEMENT}
    plain = ask(box(tmp_path, files), "how much did we spend on electricity this year")
    assert plain.returncode == 42  # her bank says ORIGIN ENERGY
    t2 = tmp_path / "w"
    t2.mkdir()
    b = box(t2, files, "# her own words\nelectricity = energy, origin\n")
    got = ask(b, "how much did we spend on electricity this year")
    assert got.stdout.splitlines()[0] == "spent: electricity (electricity = energy, origin)"  # fmt: skip
    assert got.stdout.splitlines()[-1] == "total: 1,654.36 in 3 payments"


def test_a_words_list_anyone_can_read_is_refused_like_the_kernel_refuses_it(tmp_path):
    b = box(tmp_path, {"bank.txt": STATEMENT}, "electricity = origin\n")
    (tmp_path / "words.txt").chmod(0o644)
    got = ask(b, "electricity")
    assert got.returncode == 2 and "readable beyond its owner" in got.stderr


def test_a_line_is_judged_on_its_own_words_never_its_files_name(tmp_path):
    b = box(tmp_path, {"electricity/bank.txt": "2026-02-01  -30.00  ACME LTD\n"})
    assert ask(b, "electricity").returncode == 42


def test_currencies_are_each_totalled_and_never_added(tmp_path):
    b = box(tmp_path, {"a.txt": "2026-02-01  -£10.00  CAFE\n2026-02-02  -$20.00  CAFE\n2026-02-03  -5.00  CAFE\n2026-02-04  -£2.50  CAFE\n"})  # fmt: skip
    got = ask(b, "cafe")
    assert got.stdout.splitlines()[-4:] == [
        "total: 5.00 in 1 payment (no currency sign)",
        "total: $20.00 in 1 payment",
        "total: £12.50 in 2 payments",
        "currencies are never added together",
    ]


def test_words_that_only_say_it_is_a_sum_or_a_period_name_nothing(tmp_path):
    b = box(tmp_path, {"bank.txt": STATEMENT})
    got = ask(b, "how much did we spend this year")
    assert got.returncode == 2 and "name what it was spent on" in got.stderr
    assert sp.wanted("how much did we spend on electricity this year") == (["electricity"], "this", False)  # fmt: skip
    assert sp.wanted("total paid for the gym last financial year") == (["gym"], "last", True)  # fmt: skip
    assert sp.wanted("what did the rent cost in the fiscal year") == (["rent"], "", True)  # fmt: skip
    assert sp.wanted("tesco tesco tesco") == (["tesco"], "", False)
    assert sp.wanted("what was last month's rent") == (
        ["month", "rent"],
        "",
        False,
    )  # only years


def test_a_year_flag_with_no_this_or_last_means_this_year(tmp_path):
    b = box(tmp_path, {"bank.txt": STATEMENT})
    got = ask(b, "origin", "--year", "calendar")
    assert "period: calendar 2026," in got.stdout
    assert "period: every date" in ask(b, "origin").stdout


def test_it_only_reads(tmp_path):
    b = box(tmp_path, {"bank.txt": STATEMENT})

    def snap() -> dict:
        return {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    before = snap()
    assert ask(b, "origin").returncode == 0
    assert snap() == before


def test_the_same_question_gives_the_same_bytes(tmp_path):
    b = box(tmp_path, {"bank.txt": STATEMENT})
    assert ask(b, "origin energy").stdout == ask(b, "origin energy").stdout


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    got = run()
    assert got.returncode == 2 and "spent.py" in got.stderr
    b = box(tmp_path, {"bank.txt": STATEMENT})
    for argv in (
        ["--box", str(b)],  # no words
        ["--box", str(b), "--year", "weekly", "origin"],
        ["--box", str(b), "--year", "calendar:7", "origin"],
        ["--box", str(b), "--year", "financial:13", "origin"],
        ["--box", str(b), "--year", "financial:x", "origin"],
        ["--box", str(b), "--year", "financial:0", "origin"],
        ["--now", NOW, "origin"],  # no box
    ):
        got = run(*argv)
        assert got.returncode == 2 and "spent.py" in got.stderr, argv
    got = run("--box", str(b), "--now", "yesterday", "origin")
    assert got.returncode == 2 and "--now" in got.stderr
    got = run("--box", str(tmp_path), "origin")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    assert os.path.exists(b / "kernel.json")


def test_it_defaults_to_the_clock_only_when_now_is_not_given(tmp_path):
    b = box(tmp_path, {"bank.txt": "2000-01-01  -1.00  ORIGIN\n"})
    got = run("--box", str(b), "origin")  # no --now: today, which is after 2000
    assert got.returncode == 0 and "total: 1.00 in 1 payment" in got.stdout
