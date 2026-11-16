"""The life box: Teodora's made-up life laid as the binder, her week run at
her own today, her own questions asked, and the answers she seals with the
key made for her, held to her answer key. The traps PLANTED.md sets are
declined, and nothing is an answer before the seal."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

LB = HERE / "life_box.py"


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(LB), *map(str, argv)], capture_output=True, text=True, check=False)  # fmt: skip


@pytest.fixture(scope="module")
def teo(tmp_path_factory):
    table = tmp_path_factory.mktemp("life") / "teodora"
    opened = run("open", "--who", "teodora", "--table", table, "--dates", "day-first")
    assert opened.returncode == 0, opened.stderr
    week = run("week", "--table", table)
    asked = run("ask", "--table", table)
    sealed_before = [r for r in kernel.read(table / "record" / "record.jsonl")[0] if r["kind"] == "seal"]  # fmt: skip
    decided = run("decide", "--table", table)
    recap = run("recap", "--table", table)
    return {"table": table, "open": opened, "week": week, "ask": asked, "before": sealed_before, "decide": decided, "recap": recap}  # fmt: skip


def answers(recap: str) -> dict[int, dict[str, list[str]]]:
    out, q = {}, None
    for line in recap.splitlines():
        m = re.match(r"^\s*(\d+)\. ", line)
        if m:
            q = int(m.group(1))
            out[q] = {"sealed": [], "declined": []}
        elif q is not None and line.strip().startswith(("sealed", "declined")):
            verb, where = line.split(None, 1)  # a file name can hold spaces
            out[q][verb].append(where)
    return out


def test_her_life_is_laid_at_her_own_today_with_a_key_made_for_her(teo):
    t = teo["table"]
    assert "308 files" in teo["open"].stdout and "2026-10-22" in teo["open"].stdout
    assert "its dates read day-first" in teo["open"].stdout
    assert (t / "teodora.key").is_file() and (
        t / "words.txt"
    ).stat().st_mode & 0o077 == 0
    first = kernel.read(t / "record" / "record.jsonl")[0][0]
    assert first["ts"].startswith("2026-10-22")


def test_her_week_finds_what_is_coming_at_her_today(teo):
    out = teo["week"].stdout
    assert teo["week"].returncode in (0, 42), teo["week"].stderr
    for line in (
        "27/10/2026 [2026-10-27]",
        "SUMMARY:Half term",
        "Payment due: 30/10/2026 [2026-10-30]",
        "Month end",
    ):
        assert line in out, line
    week = (teo["table"] / "week" / "001.md").read_text()
    assert week.count("2026-10-22T09:00:00Z") == 6  # its six steps that take a today
    assert "`{today}` is the person's today" in week  # and its prose, as written


def test_her_week_finds_who_owes_her_what_goes_out_and_what_she_meant_to_do(teo):
    run = teo["table"] / "week" / "001"
    invoices = (run / "06-invoices.txt").read_text()
    for inv, amount in (
        ("INV-0427", "£680.00"),
        ("INV-0431", "£720.00"),
        ("INV-0435", "£740.00"),
    ):
        line = next(ln for ln in invoices.splitlines() if inv in ln)
        assert (
            line.startswith("overdue") and "Bramble & Bean" in line and amount in line
        ), line
    # T2: Hargreaves' August matches a payment only by sum, so it is never counted as paid
    assert (
        "same sum, no invoice named: check these by hand, never counted as paid"
        in invoices
    )
    assert "HPS LTD BACS" in invoices
    assert "Dev Raman: I can do 600 tonight" in (run / "07-debts.txt").read_text()
    subs = (run / "08-subscriptions.txt").read_text()
    assert "holmwood lettings" in subs and "8 subscriptions" in subs
    todo = (run / "09-todo.txt").read_text()
    assert todo.count("recipes/bunica/index.md") == 19  # the recipes not yet typed up
    assert (
        "Turnover (invoiced):            £24962.00"
        in (run / "10-amounts.txt").read_text()
    )


def test_each_question_is_sent_to_the_steps_whose_job_it_is(teo):
    route = json.loads((teo["table"] / "route.json").read_text())
    assert route["2"]["kind"] == "money owed"
    assert {"step": "invoices", "kept": "week/001/06-invoices.txt"} in route["2"][
        "steps"
    ]
    assert route["17"]["kind"] == "where it stands"
    assert {"step": "todo", "kept": "week/001/09-todo.txt"} in route["17"]["steps"]
    assert (
        "3" not in route or route["3"]["steps"] == []
    )  # the wifi password is a thing she wrote down
    recap = teo["recap"].stdout
    q2 = recap.split(" 2. has kirsty paid me yet")[1].split(" 3. ")[0]
    assert "see       invoices: week/001/06-invoices.txt" in q2


def test_her_week_catches_her_cover_and_her_mot_once_her_dates_are_day_first(teo):
    """Her cover ends 03/11/2026 and the MOT 09/11/2026: each reads two ways,
    so only once the box knows her life is written day first can it place
    them. The day-first mirror gives each its ISO form; coming-up and
    renewals then find both."""
    run_ = teo["table"] / "week" / "001"
    coming = (run_ / "01-coming-up.txt").read_text()
    assert "## 2026-11-03" in coming and "PI_schedule_2025-26.txt:8" in coming
    assert "## 2026-11-09" in coming and "car/MOT_2025-11-10.txt:8" in coming
    renewals = (run_ / "02-renewals.txt").read_text()
    assert "2026-11-04  email/2026-10-06_pi-renewal-2026.eml" in renewals
    assert (
        "2026-11-09  car/MOT_2025-11-10.txt:8" in renewals and "2 to come" in renewals
    )
    car = (run_ / "03-car.txt").read_text()
    assert "mot      last 2025-11-10" in car
    assert "2026-11-09" not in car  # the MOT's expiry is not a day a job was done


def test_without_her_date_order_the_box_leaves_those_dates_unread(tmp_path):
    """The same life without --dates: a date that reads two ways is never guessed."""
    table = tmp_path / "as-written"
    assert run("open", "--who", "teodora", "--table", table).returncode == 0
    assert run("week", "--table", table).returncode in (0, 42)
    coming = (table / "week" / "001" / "01-coming-up.txt").read_text()
    assert "27/10/2026" in coming
    assert "03/11/2026" not in coming and "09/11/2026" not in coming


def test_a_date_order_must_be_one_of_the_two(tmp_path):
    got = run(
        "open", "--who", "teodora", "--table", tmp_path / "t", "--dates", "year-first"
    )
    assert got.returncode == 2 and "--dates is day-first or month-first" in got.stderr


def test_nothing_is_an_answer_until_she_seals_it(teo):
    assert (
        teo["ask"].returncode == 42
        and "41 answers wait on teodora's seal" in teo["ask"].stdout
    )
    assert teo["before"] == []


def test_she_seals_what_her_answer_key_names_and_declines_the_rest(teo):
    assert "sealed 16 answers and declined 25" in teo["decide"].stdout
    got = answers(teo["recap"].stdout)
    assert "10 of 20 questions have an answer teodora sealed" in teo["recap"].stdout
    assert got[1]["sealed"] == [
        "car/MOT_2025-11-10.txt:3",
        "car/MOT_2025-11-10.txt:15",
    ]  # its expiry, then its advisories
    assert "car/MOT_2024-11-08.txt:3" in got[1]["declined"]  # last year's
    assert got[18]["sealed"] == ["email/2026-09-20_your-replacement-debit-card-is-on-its-way.eml:13"]  # fmt: skip
    assert (
        "email/2025-10-06_pi-renewal-2025.eml:15" in got[18]["declined"]
    )  # last year's, the decoy
    for q in (2, 6, 15, 17):  # nothing in her life holds the question's words
        assert got[q] == {"sealed": [], "declined": []}
        assert f"{q:>2}. " in teo["recap"].stdout
    assert teo["recap"].stdout.count("nothing in the life holds it") == 4


def test_the_traps_are_declined(teo):
    got = answers(teo["recap"].stdout)
    # T2: the ledger says Hargreaves' August is unpaid; it was paid
    assert got[11]["sealed"] == [] and "work/invoices/invoice_ledger.csv:236" in got[11]["declined"]  # fmt: skip
    # T1: the "refund" email is phishing; it answers nothing
    assert got[12]["sealed"] == [] and all("tax-refund" in w for w in got[12]["declined"])  # fmt: skip


def test_her_record_holds_every_seal(teo):
    t = teo["table"]
    v = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(t / "record")],
                       capture_output=True, text=True, check=False)  # fmt: skip
    assert v.returncode == 0 and "16 sealed" in v.stdout
    rows = kernel.read(t / "record" / "record.jsonl")[0]
    assert [r["kind"] for r in rows].count("seal") == 16
    assert [r["kind"] for r in rows].count("decline") == 25


def test_only_a_made_up_person_with_an_answer_key_is_decided_for(teo, tmp_path):
    table = tmp_path / "hollis"
    assert run("open", "--who", "hollis", "--table", table).returncode == 0
    got = run("decide", "--table", table)
    assert got.returncode == 2 and "has no answer key" in got.stderr


@pytest.mark.parametrize("argv, says", [
    (("open", "--who", "nobody"), "isn't one of willow's made-up lives"),
    (("open", "--who", "../teodora"), "isn't one of willow's made-up lives"),
    (("week",), "isn't a life box laid by open"),
])  # fmt: skip
def test_what_isnt_a_life_box_is_refused(tmp_path, argv, says):
    got = run(*argv, "--table", tmp_path / "t")
    assert got.returncode == 2 and says in got.stderr


def test_a_command_line_that_isnt_one_is_refused(teo):
    for argv in ((), ("open", "--table", "x"), ("ask",), ("fly", "--table", "x")):
        assert run(*argv).returncode == 2
    assert (
        "is there already"
        in run("open", "--who", "teodora", "--table", teo["table"]).stderr
    )


def test_her_answer_key_is_what_planted_md_names():
    key = json.loads((HERE / "teodora.json").read_text())
    planted = (ROOT / "demo" / "teodora" / "PLANTED.md").read_text()
    files = {a["file"].rstrip("/") for v in key["answers"].values() for a in v}
    named = {f for f in files if f in planted or f.split("/")[-1] in planted}
    assert len(key["answers"]) == 20
    assert {"car/MOT_2025-11-10.txt", "email/2026-10-06_pi-renewal-2026.eml", "work/invoices/invoice_ledger.csv"} <= named  # fmt: skip
