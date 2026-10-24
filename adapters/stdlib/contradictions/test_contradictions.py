"""contradictions: two lines saying the same thing with a different date or
amount, side by side, cited, neither picked; near misses left alone."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def contradictions(
    tmp_path: Path, files: dict[str, str]
) -> subprocess.CompletedProcess:
    pile = tmp_path / "pile"
    pile.mkdir(exist_ok=True)
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    return run(str(HERE / "contradictions.py"), "--box", str(b))


def lines(got: subprocess.CompletedProcess) -> list[str]:
    return got.stdout.splitlines()


def test_two_dates_for_the_same_thing_side_by_side_neither_picked(tmp_path):
    got = contradictions(tmp_path, {
        "plans.md": "Guest list draft.\n\nThe wedding dinner is on 2026-06-12.\n",
        "mail/ana.txt": "Hi all,\nReminder: the wedding dinner is on 19/06/2026.\n",
    })  # fmt: skip
    assert got.returncode == 0
    # in file order, never by which date is later
    assert lines(got) == [
        "DATE    wedding, dinner",
        "        mail/ana.txt:2  2026-06-19  Reminder: the wedding dinner is on 19/06/2026.",
        "        plans.md:3      2026-06-12  The wedding dinner is on 2026-06-12.",
        "1 disagreement, 2 lines with a date or an amount read; neither side is picked.",
    ]


def test_a_near_miss_about_something_else_is_not_reported(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "The plumber came on 2026-03-01.\n",
        "b.md": "The electrician came on 2026-03-09.\nThe plumber visit is booked 2026-03-04.\n",
    })  # fmt: skip
    assert got.returncode == 42
    assert lines(got) == [
        "No two lines saying the same thing disagree; 3 lines with a date or an amount read."
    ]


def test_amounts_of_one_unit_however_written(tmp_path):
    got = contradictions(tmp_path, {
        "lease.md": "Rent for the flat is $1,200 a month.\n",
        "notes.md": "Rent for the flat is 1250 dollars a month now.\nRent for the flat is $1200.00 a month.\n",
    })  # fmt: skip
    assert got.returncode == 0
    # $1,200 and $1200.00 are one amount; 1250 dollars is the same unit as $
    assert lines(got) == [
        "AMOUNT  rent, flat",
        "        lease.md:1  $1,200        Rent for the flat is $1,200 a month.",
        "        notes.md:1  1250 dollars  Rent for the flat is 1250 dollars a month now.",
        "AMOUNT  rent, flat",
        "        notes.md:1  1250 dollars  Rent for the flat is 1250 dollars a month now.",
        "        notes.md:2  $1200.00      Rent for the flat is $1200.00 a month.",
        "2 disagreements, 3 lines with a date or an amount read; neither side is picked.",
    ]


def test_hours_disagree_and_other_units_are_not_compared(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "Tomatoes want 6 hours of sun and 2 kg of compost.\n",
        "b.md": "Tomato wants 8 hours of sun and 2 lb of compost.\n",
    })  # fmt: skip
    assert got.returncode == 0
    assert lines(got)[:3] == [
        "AMOUNT  tomatoes, want, sun, compost",
        "        a.md:1  6 hours  Tomatoes want 6 hours of sun and 2 kg of compost.",
        "        b.md:1  8 hours  Tomato wants 8 hours of sun and 2 lb of compost.",
    ]
    assert len(lines(got)) == 4


def test_every_unit_is_its_own(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "Seed costs 40 euros, weighs 3 kg, takes 5 days, is 12% water.\n",
        "b.md": "Seed costs €45, weighs 4 kilos, takes 6 days, is 15 percent water.\n",
    })  # fmt: skip
    heads = [x for x in lines(got) if not x.startswith(" ")]
    assert heads[:-1] == ["AMOUNT  seed, costs, weighs, takes, water"] * 4
    # units in name order, each pair its own; values as written
    vals = [x.split("  ")[5:7] for x in lines(got) if x.startswith(" ")]
    assert [v[0] for v in vals] == ["12%", "15 percent", "5 days", "6 days", "3 kg",
                                    "4 kilos", "40 euros", "€45"]  # fmt: skip


def test_a_date_that_could_be_either_way_round_is_never_read(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "The wedding dinner is on 03/04/2026.\n",
        "b.md": "The wedding dinner is on 2026-06-19.\n",
    })  # fmt: skip
    assert got.returncode == 42
    assert lines(got) == [
        "No two lines saying the same thing disagree; 1 line with a date or an amount read."
    ]


def test_nothing_there_is_said_as_nothing_there(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "2026-10-01 Watered the tomatoes.\n",
        "b.md": "Costs $5k, or $1.2 million, or 5-10 kg, about 3 m.\n",
    })  # fmt: skip
    assert got.returncode == 42
    assert lines(got) == [
        "Nothing in your folder states a date or an amount this can read."
    ]


def test_log_entries_on_different_days_are_left_alone_and_counted(tmp_path):
    got = contradictions(tmp_path, {
        "stamps.md": "2026-10-01 Paid $40 for gas.\n- 2026-10-03 Paid $55 for gas.\n",
        "heads.md": "# 2026-10-01\nBought 3 kg of flour.\n\n# 2026-10-03\nBought 5 kg of flour.\n",
        "notes/2026-10-01.md": "Gave 2 hours to the garden club.\n",
        "notes/2026-10-02.md": "Gave 3 hours to the garden club.\n",
    })  # fmt: skip
    assert got.returncode == 42
    assert lines(got) == [
        "No two lines saying the same thing disagree; 6 lines with a date or an amount"
        " read, 3 pairs written on different days left alone."
    ]


def test_log_entries_on_one_day_are_compared(tmp_path):
    got = contradictions(tmp_path, {
        "heads.md": "# 2026-10-01\nBought 3 kg of flour.\nBought 5 kg of flour.\n",
        "notes/2026-10-01.md": "2026-10-01 Paid $40 for gas.\nPaid $55 for gas.\n",
    })  # fmt: skip
    assert got.returncode == 0
    assert [x for x in lines(got) if not x.startswith(" ")] == [
        "AMOUNT  bought, flour",
        "AMOUNT  paid, gas",
        "2 disagreements, 4 lines with a date or an amount read; neither side is picked.",
    ]


def test_one_left_alone_is_said_in_the_singular(tmp_path):
    got = contradictions(tmp_path, {
        "2026-10-01.md": "Paid $40 for gas.\n", "2026-10-02.md": "Paid $55 for gas.\n",
        "x.md": "Rent for the flat is $1 a week.\nRent for the flat is $2 a week.\n",
    })  # fmt: skip
    assert lines(got)[-1] == (
        "1 disagreement, 4 lines with a date or an amount read, 1 pair written on"
        " different days left alone; neither side is picked."
    )


def test_a_line_saying_two_of_a_thing_is_not_read_for_it(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "The town fair moved from 2026-05-01 to 2026-05-08.\nThe town fair is on 2026-05-15.\n"
                "The town fair is on 2026-05-16.\n",
        "b.md": "Club fees were $10 then $12.\nClub fees were $11.\nClub fees were $13 and $13.00 again.\n",
    })  # fmt: skip
    assert lines(got) == [
        "DATE    town, fair",
        "        a.md:2  2026-05-15  The town fair is on 2026-05-15.",
        "        a.md:3  2026-05-16  The town fair is on 2026-05-16.",
        "AMOUNT  club, fees",
        "        b.md:2  $11  Club fees were $11.",
        "        b.md:3  $13  Club fees were $13 and $13.00 again.",
        "2 disagreements, 4 lines with a date or an amount read; neither side is picked.",
    ]


def test_the_shorter_must_be_half_the_longer(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "Wedding dinner on 2026-06-12.\n",
        "b.md": "Wedding dinner, cake tasting with Ana on 2026-06-19.\n",
        "c.md": "Wedding dinner party on 2026-06-20.\n",
    })  # fmt: skip
    assert got.returncode == 0
    assert lines(got) == [
        "DATE    wedding, dinner",
        "        a.md:1  2026-06-12  Wedding dinner on 2026-06-12.",
        "        c.md:1  2026-06-20  Wedding dinner party on 2026-06-20.",
        "1 disagreement, 3 lines with a date or an amount read; neither side is picked.",
    ]


def test_the_same_value_twice_is_no_disagreement(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "The wedding dinner is on 2026-06-19.\nRent for the flat is $900.\n",
        "b.md": "The wedding dinner is on 19/06/2026.\nRent for the flat is $900.00.\n",
        # one dated and one not: no date to disagree with
        "c.md": "The dinner costs $90.\nThe dinner costs $90 on 2026-06-12.\n",
    })  # fmt: skip
    assert got.returncode == 42
    assert "6 lines" in got.stdout


def test_a_short_name_is_a_word_of_its_own(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "Ed paid $40 for gas.\n", "b.md": "Jo paid $55 for gas.\n",
    })  # fmt: skip
    assert got.returncode == 42


def test_one_word_is_a_label_not_a_subject(tmp_path):
    got = contradictions(tmp_path, {
        "a.md": "Date: 2026-06-12\nRent is $900.\n", "b.md": "Date: 2026-06-19\nRent is $950.\n",
    })  # fmt: skip
    assert got.returncode == 42
    assert "4 lines" in got.stdout


def test_a_long_line_is_cut_at_a_hundred_characters(tmp_path):
    long_ = "The roof repair quote " + "from the builder " * 8 + "is $4,000."
    got = contradictions(tmp_path, {"a.md": long_ + "\n",
                                    "b.md": long_.replace("4,000", "4,500") + "\n"})  # fmt: skip
    rows = [x for x in lines(got) if x.startswith(" ")]
    assert [r.split("  ", 6)[-1] for r in rows] == [long_[:100], long_[:100]]


def test_the_same_folder_gives_the_same_bytes(tmp_path):
    files = {
        "z.md": "Rent for the flat is $9.\n",
        "a.md": "Rent for the flat is $8.\n",
        "m.md": "Rent for the flat is $7.\n",
    }
    one = contradictions(tmp_path, files).stdout
    assert one == contradictions(tmp_path, files).stdout
    heads = [x.split()[0] for x in one.splitlines() if x.startswith(" ")]
    assert heads == ["a.md:1", "m.md:1", "a.md:1", "z.md:1", "m.md:1", "z.md:1"]


def test_refused_without_a_box_or_with_a_bad_command_line(tmp_path):
    script = str(HERE / "contradictions.py")
    assert run(script, "--box", str(tmp_path)).returncode == 2
    got = run(script, "--bx", str(tmp_path))
    assert got.returncode == 2 and "contradictions.py --box DIR" in got.stderr
