"""car: jobs by the first kind a line names, a cost per currency sign, a due
date only from what is written (a date after "due", or the last day plus an
interval), measured from --now."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("car", HERE / "car.py")
car = importlib.util.module_from_spec(spec)
spec.loader.exec_module(car)
NOW = ["--now", "2026-10-29T00:00:00Z"]
SCRIPT = str(HERE / "car.py")


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def test_months_clamp_to_the_end_of_the_month():
    assert car.add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert car.add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert car.add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)
    assert car.add_months(date(2026, 12, 31), 12) == date(2027, 12, 31)
    assert car.add_months(date(2026, 3, 31), 12) == date(2027, 3, 31)
    assert car.add_months(date(2026, 1, 15), 0) == date(2026, 1, 15)
    assert car.add_months(date(2026, 10, 30), 4) == date(2027, 2, 28)


def test_an_interval_is_only_what_the_line_says():
    iv = car.interval_of
    assert iv("service every 12 months") == (12, "month")
    assert iv("every 2 years") == (24, "month")
    assert iv("every year") == (12, "month")
    assert iv("every six months") == (6, "month")
    assert iv("every 6 weeks") == (6, "week")
    assert iv("every 6-weeks") == (6, "week")
    assert iv("MOT yearly") == (12, "month")
    assert iv("annual service") == (12, "month")
    assert iv("annually") == (12, "month")
    assert iv("six-monthly check") == (6, "month")
    assert iv("six monthly check") == (6, "month")
    assert iv("monthly wash") == (1, "month")
    assert iv("weekly check") == (1, "week")
    assert iv("every 0 months") is None
    assert iv("service done") is None
    assert iv("every 12 months, now every 6 months") == (6, "month"), "the last wins"
    assert iv("yearly, then every 3 months") == (3, "month")


def test_a_kind_is_the_first_a_line_names_and_a_day_is_needed():
    kinds = car.CAR
    pile = [{"path": "log.md", "line": 1, "text": (
        "2026-01-15 Full service £420.50\n"
        "2025-11-10 MOT passed, £54.85\n"
        "2025-06-02 two new tyres $310 and a repair 12\n"
        "2024-03-01 washed the car\n"
    )}]  # fmt: skip
    pile.append({"path": "undated.md", "line": 1, "text": "replaced the battery\n"})
    got = car.register(pile, kinds)
    assert set(got) == {("", "service"), ("", "mot"), ("", "tyres")}
    assert got[("", "service")]["cost"] == {"£": 420.5}
    assert got[("", "tyres")]["cost"] == {"$": 310.0}
    assert got[("", "mot")]["days"] == ["20251110"]


def test_a_job_is_the_cars_only_when_the_line_or_its_path_says_a_vehicle():
    pile = [
        {"path": "work/tuning.csv", "line": 1, "text": "2021-03-05 service visit 135\n"},
        {"path": "van/service_history.txt", "line": 1, "text": "2022-01-04 service 220\n"},
        {"path": "house/cal.ics", "line": 1, "text": "2026-05-01 roof inspection\n"},
        {"path": "mail/a.eml", "line": 1, "text": "2025-10-07 vehicle registration renewed\n"},
        {"path": "mail/b.eml", "line": 1, "text": "2025-10-08 service of the car\n"},
    ]  # fmt: skip
    got = car.register(pile, car.CAR, context=car.CAR_CONTEXT)
    assert {k: v["days"] for k, v in got.items()} == {
        ("", "service"): ["20220104", "20251008"],
        ("", "mot"): ["20251007"],
    }
    both = car.register(pile, car.CAR)
    assert len(both[("", "service")]["days"]) == 3 and ("", "mot") in both
    assert car.CAR_CONTEXT.search("garage") and not car.CAR_CONTEXT.search("carpet")
    assert not car.CAR_CONTEXT.search("service")


def test_a_garages_oil_and_filter_is_a_service():
    pile = [{"path": "van/history.txt", "line": 1, "text": "2021-06-14 odo 92,034 $ 89.40 Oil + filter, rotate tires\n2021-11-29 Oil and filter\n2021-12-01 Oil change\n"}]  # fmt: skip
    got = car.register(pile, car.CAR, context=car.CAR_CONTEXT)
    assert got[("", "tyres")]["cost"] == {"$": 89.4}, "spaces after the sign are fine"
    assert ("", "tyres") in got, (
        "rotate tires is the tyres', the first kind a line names"
    )
    assert got[("", "tyres")]["days"] == ["20210614"]
    assert got[("", "service")]["days"] == ["20211129", "20211201"]


def test_costs_total_per_sign_and_never_convert():
    pile = [{"path": "log.md", "line": 1, "text": (
        "2026-01-15 service £1,200.50 and $20\n"
        "2026-02-15 service €5 and £0.25\n"
    )}]  # fmt: skip
    rec = car.register(pile, car.CAR)[("", "service")]
    assert rec["cost"] == {"£": 1200.75, "$": 20.0, "€": 5.0}
    assert car.money(rec["cost"]) == "$20.00 + £1,200.75 + €5.00"
    assert car.money({}) == "-"


def test_due_is_what_is_written_and_a_due_date_is_not_the_day_of_the_job():
    pile = [{"path": "log.md", "line": 1, "text": (
        "2026-01-15 service, next service due 2027-03-01\n"
        "2025-11-10 MOT, every 12 months\n"
        "2025-06-02 tyres\n"
    )}]  # fmt: skip
    got = car.register(pile, car.CAR)
    assert got[("", "service")]["days"] == ["20260115"]
    assert car.due_date(got[("", "service")]) == date(2027, 3, 1)
    assert car.due_date(got[("", "mot")]) == date(2026, 11, 10)
    assert car.due_date(got[("", "tyres")]) is None
    weeks = {"days": ["20260101"], "interval": (6, "week"), "due": ""}
    assert car.due_date(weeks) == date(2026, 2, 12)


def test_a_later_line_replaces_the_interval_and_an_earlier_one_does_not():
    pile = [{"path": "log.md", "line": 1, "text": (
        "2026-06-01 service every 6 months\n"
        "2026-01-01 service every 12 months\n"
    )}]  # fmt: skip
    rec = car.register(pile, car.CAR)[("", "service")]
    assert rec["interval"] == (6, "month")
    assert rec["at"] == "log.md:1"


def test_when_counts_the_days():
    t = date(2026, 10, 29)
    assert car.when(date(2026, 10, 29), t) == "due today"
    assert car.when(date(2026, 10, 30), t) == "in 1 day"
    assert car.when(date(2026, 11, 10), t) == "in 12 days"
    assert car.when(date(2026, 10, 28), t) == "overdue 1 day"
    assert car.when(date(2026, 10, 19), t) == "overdue 10 days"


def test_the_listing_soonest_due_first(tmp_path):
    b = box(tmp_path, {"car/log.md": (
        "2025-11-10 MOT £54, yearly\n"
        "2026-11-10 MOT £54.00\n"
        "2026-01-15 service £420.50, next service due 2027-01-15\n"
        "2024-06-02 tyres £310\n"
        "2026-01-20 brakes every 12 months\n")})  # fmt: skip
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "service  last 2026-01-15  1 time    £420.50     due 2027-01-15 (in 78 days)",
        "brakes   last 2026-01-20  1 time    -           due 2027-01-20 (in 83 days)",
        "mot      last 2026-11-10  2 times   £108.00     due 2027-11-10 (in 377 days)",
        "tyres    last 2024-06-02  1 time    £310.00     no due date written",
        "4 kinds of job, 5 entries",
    ]
    assert run(SCRIPT, "--box", str(b), *NOW).stdout == got.stdout


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 42 and "job done to the car" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--now", "soon"],
        ["--box", str(b), "--now", "2026-13-45"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "car.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
