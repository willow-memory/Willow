"""The life box over the demo lives that aren't Teodora's or Bernadette's.

Of the four others, one is a person's life with questions of her own, asked of
her own files (demo/ofrenda: Marisol's F1 to F3), and is laid. Three are not:
demo/money-hour is four people and holds no question (its facts, traps and
wagers are claims held to a record outside the files), demo/stewart-crossover
holds claims about a real man, and demo/johnson is five people's folders with
no question file. The life box refuses each, and says why.

Ofrenda is made up, has no answer key, and so is run open, week, ask and recap
only: decide refuses. The frozen studies' folders are only read, and the test
holds them byte for byte through the run.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEMO = ROOT / "demo"
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

sys.path.insert(0, str(HERE))
import life_box  # noqa: E402

LB = HERE / "life_box.py"
#: folders the life box may only read: the frozen studies, and Johnson's, which it never lays
UNTOUCHED = ["money-hour", "ofrenda", "stewart-crossover", "johnson"]


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(LB), *map(str, argv)], capture_output=True, text=True, check=False)  # fmt: skip


def hashes() -> dict[str, str]:
    """Every file under those folders, by SHA-256."""
    return {
        str(f.relative_to(DEMO)): hashlib.sha256(f.read_bytes()).hexdigest()
        for name in UNTOUCHED
        for f in sorted((DEMO / name).rglob("*"))
        if f.is_file() and "__pycache__" not in f.parts
    }


@pytest.fixture(scope="module")
def ofrenda(tmp_path_factory):
    before = hashes()
    table = tmp_path_factory.mktemp("life") / "ofrenda"
    opened = run("open", "--who", "ofrenda", "--table", table, "--read")
    assert opened.returncode == 0, opened.stderr
    week = run("week", "--table", table)
    asked = run("ask", "--table", table)
    decided = run("decide", "--table", table)
    recap = run("recap", "--table", table)
    yield {"table": table, "open": opened, "week": week, "ask": asked, "decide": decided, "recap": recap, "before": before}  # fmt: skip
    for key in table.glob(
        "*.key"
    ):  # a key made for a made-up person, gone with the table
        subprocess.run(["shred", "-u", str(key)], check=False)


def test_ofrenda_is_laid_at_her_own_day_read_through_shell_history(ofrenda):
    out = ofrenda["open"].stdout
    assert "11 files" in out and "2026-10-31" in out
    assert "shell-history: wrote 1 files" in out
    assert "copied: 10 files no reader took" in out
    table = ofrenda["table"]
    # the history is read: each command is a dated line, and the deleted secret's is there
    read = table / "ofrenda-read" / "computadora-de-femia"
    history = (read / "bash_history.txt").read_text(encoding="utf-8")
    assert re.search(r"^2019-12-21 16:45:40 UTC  echo \"biscochitos secret: un chorrito de vino dulce", history, re.M)  # fmt: skip
    assert not (read / "bash_history").exists()
    # her own day is the last line of her diary, where she is about to ask her files
    diary = (table / "ofrenda" / "life" / "marisol" / "diario.txt").read_text(encoding="utf-8")  # fmt: skip
    assert "2026-10-31" in diary.splitlines()[-1] and "ask her files" in diary.splitlines()[-1]  # fmt: skip
    assert life_box.today_of("ofrenda") == "2026-10-31T09:00:00Z"
    first = kernel.read(table / "record" / "record.jsonl")[0][0]
    assert "2026-10-31" in json.dumps(first)


def test_her_questions_are_read_verbatim_from_questions_json_in_order(ofrenda):
    listed = json.loads((DEMO / "ofrenda" / "questions.json").read_text(encoding="utf-8"))["questions"]  # fmt: skip
    own = [x["ask"] for x in listed if x["box"] == "ofrenda"]
    assert own == [
        "what was the secret in the biscochitos",
        "why does the old computer beep at midnight on november 2",
        "where did she hide the deed to the land",
    ]
    assert life_box.questions("ofrenda") == own
    asked = re.findall(r"^\s*(\d+)\. (.+?)(?:  \(.*\))?$", ofrenda["ask"].stdout, re.M)
    assert [q for _, q in asked] == own
    # the two books' questions are put to Babbage's and Ada's words, not to her files
    for x in listed:
        if x["box"] != "ofrenda":
            assert x["ask"] not in ofrenda["ask"].stdout


def test_teodoras_and_bernadettes_questions_still_come_from_their_questions_md():
    for who in ("teodora", "bernadette"):
        text = (DEMO / who / "QUESTIONS.md").read_text(encoding="utf-8")
        assert life_box.questions(who) == re.findall(r"^\d+\. (.+)$", text, re.M)
        assert len(life_box.questions(who)) == 20
    assert life_box.today_of("teodora") == "2026-10-22T09:00:00Z"
    assert life_box.today_of("bernadette") == "2026-10-24T09:00:00Z"


def test_a_today_is_read_from_the_demo_and_never_guessed():
    assert (
        life_box.today_of("money-hour") == "2026-11-05T09:00:00Z"
    )  # questions.json's `today`
    assert life_box.today_of("ofrenda") == "2026-10-31T09:00:00Z"  # run.py's NOW
    with pytest.raises(ValueError, match="names no today"):
        life_box.today_of("johnson")  # no TODAY, no questions.json, no run.py NOW


def test_ask_offers_what_the_files_hold_and_nothing_for_the_silent_question(ofrenda):
    out = ofrenda["ask"].stdout
    assert ofrenda["ask"].returncode == kernel.ESCALATE
    assert "5 answers wait on ofrenda's seal" in out
    # the deleted file's command is served first for the secret, dated, from the read history
    assert re.search(r"1\. what was the secret in the biscochitos.*\n\s+3 suggested: computadora-de-femia/bash_history\.txt:\d+; marisol/diario\.txt:24", out)  # fmt: skip
    assert "2. why does the old computer beep" in out
    assert "computadora-de-femia/notas/computadora.txt:9" in out
    # the silent one: nothing holds it, as demo/ofrenda froze it to
    assert re.search(r"3\. where did she hide the deed to the land.*\n\s+nothing in the life holds it", out)  # fmt: skip


def test_nothing_is_sealed_and_decide_refuses_for_want_of_an_answer_key(ofrenda):
    assert not (HERE / "ofrenda.json").exists()
    assert ofrenda["decide"].returncode == kernel.REFUSED
    assert "no answer key" in ofrenda["decide"].stderr
    rows = kernel.read(ofrenda["table"] / "record" / "record.jsonl")[0]
    assert [r for r in rows if r["kind"] in ("seal", "decline")] == []
    proposals = [
        r for r in rows if r["kind"] == "proposal" and r.get("verdict") == "pass"
    ]
    assert len(proposals) == 5  # every one still waits
    recap = ofrenda["recap"].stdout
    assert "0 of 3 questions have an answer ofrenda sealed." in recap
    assert recap.count("waiting   ") == 5
    assert "sealed   " not in recap and "declined" not in recap


def test_her_record_verifies(ofrenda):
    got = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(ofrenda["table"] / "record")], capture_output=True, text=True, check=False)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr


def test_the_week_runs_at_her_day_over_her_files(ofrenda):
    week = ofrenda["week"].stdout
    assert "coming-up -- --box {box} --days 21 --now 2026-10-31T09:00:00Z" in week
    assert "marisol/diario.txt:26  2026-10-31  Tomorrow the marigolds" in week


@pytest.mark.parametrize(
    "who, says",
    [
        ("money-hour", "holds no `questions` list"),
        ("stewart-crossover", "holds no `questions` list"),
        ("johnson", "has no QUESTIONS.md and no questions.json"),
    ],
)
def test_a_study_that_is_not_one_persons_questions_is_not_laid(who, says, tmp_path):
    table = tmp_path / "t"
    got = run("open", "--who", who, "--table", table)
    assert got.returncode == kernel.REFUSED and says in got.stderr, got.stderr
    assert not table.exists()  # nothing was made, no key either


def test_the_frozen_demos_are_unchanged_by_all_of_it(ofrenda):
    # laying a life copies its folder into the table and runs make_life.py there
    assert hashes() == ofrenda["before"]


def test_readings_have_nothing_to_say_beside_her_questions(ofrenda):
    """No dated log or table is served for any of her questions: no hint, none
    kept, and what ask offers is what the kernel serves."""
    assert "see readings" not in ofrenda["ask"].stdout + ofrenda["recap"].stdout
    assert not (ofrenda["table"] / "readings").exists()
