"""budget: a monthly budget written in your own words, statement lines matched
to its categories by the markers you gave, months held against it by plain
arithmetic."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "budget.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("budget", SCRIPT)
bg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bg)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
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


def chunk(text: str, path: str = "money.md") -> list[dict]:
    return [{"path": path, "line": 1, "text": text}]


PLAN = (
    "2026-01-01 Budget: groceries £400 a month (tesco, aldi, coles)\n"
    "2026-01-01 Budget: transport 120 per month\n"
    "2026-01-01 Budget for eating out $200 monthly (cafe, restaurant, pizza hut)\n"
)
STATEMENT = (
    "2026-02-03,TESCO STORES 3241,-45.20\n2026-02-10,ALDI,-267.20\n2026-03-04,Tesco Express,-55.10\n"
    "2026-03-12,COLES ONLINE,-400.00\n2026-03-15,TRANSPORT FOR LONDON,-96.00\n2026-03-20,PIZZA HUT,-30.00\n"
    "2026-03-21,Pizza Hut Express,-12.50\n2026-03-22,SOMETHING ELSE,-99.00\n"
)


def test_a_budget_line_names_a_category_an_amount_a_month_and_markers():
    got = bg.budgets(chunk(PLAN))
    assert got == {
        "groceries": {
            "amount": 400.0,
            "markers": ["tesco", "aldi", "coles"],
            "day": "20260101",
        },
        "transport": {"amount": 120.0, "markers": ["transport"], "day": "20260101"},
        "eating out": {
            "amount": 200.0,
            "markers": ["cafe", "restaurant", "pizza hut"],
            "day": "20260101",
        },
    }
    assert bg.budgets(chunk("2026-01-01 Budget: groceries £400\n")) == {}, (
        "a budget says it is monthly"
    )
    assert (
        bg.budgets(chunk("2026-01-01 Budget: groceries 1,200.50/month\n"))["groceries"][
            "amount"
        ]
        == 1200.5
    )
    assert bg.budgets(chunk("2026-01-01 Budget groceries 400 each month ()\n"))[
        "groceries"
    ]["markers"] == ["groceries"]
    assert bg.budgets(chunk("groceries budget 400 a month\n")) == {}, (
        "the line needs its own date"
    )


def test_a_later_budget_replaces_an_earlier_one():
    text = "2026-06-01 Budget: groceries 500 a month\n2026-01-01 Budget: groceries 400 a month\n"
    assert bg.budgets(chunk(text))["groceries"]["amount"] == 500.0


def test_an_amount_is_a_sum_with_a_sign_or_cents_and_dates_are_not():
    a = bg.amount_of
    assert a("2026-02-03,TESCO,-45.20") == 45.2
    assert a("paid £1,240.50 rent") == 1240.5
    assert a("paid $9 for lunch") == 9.0
    assert a("TESCO 3241 on 03/02/2026") is None, (
        "a bare number is an id, a date is a date"
    )
    assert a("3.5 hours") is None
    assert a("2026-02-03 refund 12.00 then 3.00") == 12.0
    assert a("") is None


def test_spending_is_matched_by_whole_word_markers_and_counted_once():
    plan = bg.budgets(chunk(PLAN))
    got = bg.spending(chunk(STATEMENT), plan)
    assert got["groceries"] == {"202602": 312.4, "202603": 455.1}
    assert got["transport"] == {"202603": 96.0}
    assert got["eating out"] == {"202603": 42.5}
    twice = bg.spending(
        chunk("2026-02-03,TESCO,-10.00\n", "a.csv")
        + chunk("2026-02-03,TESCO,-10.00\n", "b.csv"),
        plan,
    )
    assert twice["groceries"] == {"202602": 10.0}, (
        "the same payment in two files is one"
    )
    part = bg.spending(
        chunk("2026-02-03,TESCOS,-10.00\n2026-02-03,tesco,-5.00\n"), plan
    )
    assert part["groceries"] == {"202602": 5.0}, "a marker is a whole word"
    first = bg.spending(chunk("2026-02-03,ALDI TRANSPORT,-10.00\n"), plan)
    assert "transport" not in first and first["groceries"] == {"202602": 10.0}, (
        "the first budget written"
    )


def test_the_listing(tmp_path):
    b = box(tmp_path, {"money.md": PLAN, "bank.csv": STATEMENT})
    got = run("--box", str(b))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "groceries  budget 400.00 a month",
        "  2026-02    312.40 of 400.00   78%  under by 87.60",
        "  2026-03    455.10 of 400.00  114%  over by 55.10",
        "transport  budget 120.00 a month",
        "  2026-03     96.00 of 120.00   80%  under by 24.00",
        "eating out  budget 200.00 a month",
        "  2026-03     42.50 of 200.00   21%  under by 157.50",
        "3 categories, 1 month over budget",
    ]
    assert run("--box", str(b)).stdout == got.stdout


def test_exactly_on_budget_is_under_by_nothing_and_one_category_is_singular(tmp_path):
    b = box(
        tmp_path,
        {
            "money.md": "2026-01-01 Budget: groceries 100 a month\n2026-03-04 groceries -100.00\n"
        },
    )
    assert run("--box", str(b)).stdout.splitlines() == [
        "groceries  budget 100.00 a month",
        "  2026-03    100.00 of 100.00  100%  under by 0.00",
        "1 category, 0 months over budget",
    ]


def test_no_budget_is_42_and_a_bad_command_line_is_refused(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run("--box", str(b))
    assert got.returncode == 42 and "is a budget" in got.stdout
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for argv in ([], ["--box"], ["--box", str(b), "stray"], ["--box", str(tmp_path)]):
        assert run(*argv).returncode == 2, argv
    assert "budget.py" in run().stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'budget.py')!r})\n"
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
