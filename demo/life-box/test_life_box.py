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
    opened = run("open", "--who", "teodora", "--table", table)
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
    assert (t / "teodora.key").is_file() and (
        t / "words.txt"
    ).stat().st_mode & 0o077 == 0
    first = kernel.read(t / "record" / "record.jsonl")[0][0]
    assert first["ts"].startswith("2026-10-22")


def test_her_week_finds_what_is_coming_at_her_today(teo):
    out = teo["week"].stdout
    assert teo["week"].returncode in (0, 42), teo["week"].stderr
    for line in (
        "27/10/2026",
        "SUMMARY:Half term",
        "Payment due: 30/10/2026",
        "Month end",
    ):
        assert line in out, line
    week = (teo["table"] / "week" / "001.md").read_text()
    assert week.count("2026-10-22T09:00:00Z") == 3  # its three steps that take a today
    assert "`{today}` is the person's today" in week  # and its prose, as written


def test_her_week_finds_who_owes_her_what_goes_out_and_what_she_meant_to_do(teo):
    run = teo["table"] / "week" / "001"
    invoices = (run / "03-invoices.txt").read_text()
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
    assert "Dev Raman: I can do 600 tonight" in (run / "04-debts.txt").read_text()
    subs = (run / "05-subscriptions.txt").read_text()
    assert "holmwood lettings" in subs and "8 subscriptions" in subs
    todo = (run / "06-todo.txt").read_text()
    assert todo.count("recipes/bunica/index.md") == 19  # the recipes not yet typed up
    assert (
        "Turnover (invoiced):            £24962.00"
        in (run / "07-amounts.txt").read_text()
    )


def test_each_question_is_sent_to_the_steps_whose_job_it_is(teo):
    route = json.loads((teo["table"] / "route.json").read_text())
    assert route["2"]["kind"] == "money owed"
    assert {"step": "invoices", "kept": "week/001/03-invoices.txt"} in route["2"][
        "steps"
    ]
    assert route["17"]["kind"] == "where it stands"
    assert {"step": "todo", "kept": "week/001/06-todo.txt"} in route["17"]["steps"]
    assert (
        "3" not in route or route["3"]["steps"] == []
    )  # the wifi password is a thing she wrote down
    recap = teo["recap"].stdout
    q2 = recap.split(" 2. has kirsty paid me yet")[1].split(" 3. ")[0]
    assert "see       invoices: week/001/03-invoices.txt" in q2


def test_her_week_misses_the_dates_that_could_be_read_two_ways(teo):
    """Her cover ends 03/11/2026 and the MOT 09/11/2026: day first, but each
    could be read month first, and coming-up never guesses. Held here, so the
    day it can be told otherwise this test says so."""
    out = (teo["table"] / "week" / "001" / "01-coming-up.txt").read_text()
    assert "27/10/2026" in out
    assert "03/11/2026" not in out and "09/11/2026" not in out


def test_nothing_is_an_answer_until_she_seals_it(teo):
    assert (
        teo["ask"].returncode == 42
        and "41 answers wait on teodora's seal" in teo["ask"].stdout
    )
    assert teo["before"] == []


def test_she_seals_what_her_answer_key_names_and_declines_the_rest(teo):
    assert "sealed 15 answers and declined 26" in teo["decide"].stdout
    got = answers(teo["recap"].stdout)
    assert "10 of 20 questions have an answer teodora sealed" in teo["recap"].stdout
    assert got[1]["sealed"] == ["car/MOT_2025-11-10.txt:3"] and "car/MOT_2024-11-08.txt:3" in got[1]["declined"]  # fmt: skip
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
    assert v.returncode == 0 and "15 sealed" in v.stdout
    rows = kernel.read(t / "record" / "record.jsonl")[0]
    assert [r["kind"] for r in rows].count("seal") == 15
    assert [r["kind"] for r in rows].count("decline") == 26


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
