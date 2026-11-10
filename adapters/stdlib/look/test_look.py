"""look: one question is given its kind by route's rules and answered from
what a kept run holds for the steps whose job that kind is, the lines
holding its words first; a thing written down is asked of the box; what
can't be answered yet is left, said, and exits 42; nothing is written."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "look.py"
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE))
import look  # noqa: E402

KINDS = """\
money owed: owe, did * pay -> debts, invoices
a person: phone number -> people, ask
"""
DIARY = "Ruth's phone number is 555 0142.\n\nThe frosts came early last year.\n"


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, argv)], capture_output=True, text=True
    )


def kinds(tmp_path: Path, text: str = KINDS) -> Path:
    k = tmp_path / "kinds.txt"
    k.write_text(text)
    return k


def a_run(tmp_path: Path, **steps: str) -> Path:
    """A kept run: a log, and each step's output in its numbered file."""
    folder = tmp_path / "run"
    folder.mkdir()
    (folder / "00-stack.txt").write_text("the log\n")
    for n, (name, text) in enumerate(steps.items(), 1):
        (folder / f"{n:02d}-{name}.txt").write_text(text)
    return folder


def box(tmp_path: Path, text: str = DIARY, words: str = "") -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "diary.txt").write_text(text)
    b = tmp_path / "box"
    more = []
    if words:
        (tmp_path / "w.txt").write_text(words)
        (tmp_path / "w.txt").chmod(0o600)
        more = ["--words", str(tmp_path / "w.txt")]
    subprocess.run(
        [sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
         "--key", str(tmp_path / "k"), "--now", "2026-10-24T00:00:00Z", *more],
        check=True, capture_output=True,
    )  # fmt: skip
    return b


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    got = run()
    assert got.returncode == 2 and "look.py" in got.stderr
    r = a_run(tmp_path)
    for argv in (
        ["who owes me"],  # neither a run nor a box
        ["--run", r],  # no question
        ["one", "two", "--run", r],
        ["who owes me", "--run"],
        ["--nope", "--run", r],
    ):
        got = run(*argv)
        assert got.returncode == 2 and got.stderr.startswith("usage: look.py"), argv
    assert got.stdout == ""


def test_what_cant_be_read_is_refused_and_says_what(tmp_path):
    r = a_run(tmp_path)
    got = run("?!", "--run", r)
    assert got.returncode == 2 and "a question with no words" in got.stderr
    got = run("who owes me", "--run", tmp_path / "gone")
    assert got.returncode == 2 and "isn't a folder" in got.stderr
    got = run("who owes me", "--run", r, "--kinds", tmp_path / "gone")
    assert got.returncode == 2 and "could not be read" in got.stderr
    got = run("who owes me", "--run", r, "--kinds", kinds(tmp_path, "no arrow\n"))
    assert got.returncode == 2 and "the kinds file: line 1" in got.stderr
    got = run("ruth's phone number", "--box", tmp_path, "--kinds", kinds(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_a_question_is_answered_by_the_lines_its_steps_kept(tmp_path):
    r = a_run(
        tmp_path,
        debts="Dana owes you $40\n\n1 line speaks of debts\n",
        invoices="overdue  INV-7  Theatre  $640\n",
        people="Dad\n",
    )
    got = run(
        "who still owes me money", "--run", r, "--kinds", kinds(tmp_path), "--json"
    )
    assert got.returncode == 0, got.stderr
    doc = json.loads(got.stdout)
    assert doc["addon"] == "look" and doc["state"] == "populated"
    assert doc["said"] == (
        '"who still owes me money": money owed (by "owe"); '
        "3 lines from debts and invoices"
    )
    assert doc["groups"] == [
        {
            "name": "debts: its 2 lines (none holds still, money)",
            "rows": [
                {"where": "01-debts.txt:1", "what": "Dana owes you $40"},
                {"where": "01-debts.txt:3", "what": "1 line speaks of debts"},
            ],
        },
        {
            "name": "invoices: its 1 line (none holds still, money)",
            "rows": [
                {"where": "02-invoices.txt:1", "what": "overdue INV-7 Theatre $640"}
            ],
        },
    ]


def test_lines_holding_the_questions_words_come_first_most_held_first(tmp_path):
    text = "".join(f"paid  client {n}\n" for n in range(1, 11))
    text += "overdue  Lakeside Hall\npaid  Lakeside Hall  the lakeside church\n"
    r = a_run(tmp_path, debts="nothing\n", invoices=text)
    got = run(
        "did lakeside pay the church", "--run", r, "--kinds", kinds(tmp_path), "--json"
    )
    doc = json.loads(got.stdout)
    inv = doc["groups"][1]
    assert inv["name"] == (
        "invoices: 2 of its 12 lines hold lakeside, church, and come first; 8 shown"
    )
    assert [r["where"] for r in inv["rows"]] == [
        "02-invoices.txt:12",  # holds both words
        "02-invoices.txt:11",
        *[f"02-invoices.txt:{n}" for n in range(1, 7)],
    ]
    assert len(inv["rows"]) == look.SHOWN
    assert "9 lines from debts and invoices" in doc["said"]


def test_the_cues_own_words_are_not_counted_and_each_word_counts_once():
    assert look.want_of("who still owes me money, money", "owe") == ["still", "money"]
    assert look.want_of("did ruth pay", "did * pay") == ["ruth"]
    assert look.want_of("mom's goulash recipe", "") == ["mom", "goulash", "recipe"]


def test_a_long_line_is_cut_at_a_word_and_a_step_run_twice_shows_its_last(tmp_path):
    assert look.clip("a  b\n c") == "a b c"
    long = look.clip("word " * 100)
    assert len(long) <= look.WIDE + 1 and long.endswith("word…")
    r = a_run(tmp_path, debts="old\n")
    (r / "05-debts.txt").write_text("new\n")
    doc = json.loads(
        run("who owes me", "--run", r, "--kinds", kinds(tmp_path), "--json").stdout
    )
    assert doc["groups"][0]["rows"] == [{"where": "05-debts.txt:1", "what": "new"}]


def test_a_step_the_run_lacks_is_left_and_said_and_waits_on_you(tmp_path):
    r = a_run(tmp_path, debts="Dana owes you $40\n", invoices="\n\n")
    (r / "02-invoices.txt").unlink()
    got = run("who owes me", "--run", r, "--kinds", kinds(tmp_path), "--json")
    assert got.returncode == 42
    doc = json.loads(got.stdout)
    assert doc["said"].endswith("1 line from debts")
    assert doc["groups"][-1] == {
        "name": "left",
        "rows": [{"where": "invoices", "what": "its job, and not a step of this run"}],
    }
    (r / "02-invoices.txt").write_text("\n\n")
    doc = json.loads(
        run("who owes me", "--run", r, "--kinds", kinds(tmp_path), "--json").stdout
    )
    assert doc["groups"][-1]["rows"] == [
        {"where": "invoices", "what": "ran, and said nothing"}
    ]


def test_with_no_run_the_steps_are_left_and_nothing_is_answered(tmp_path):
    b = box(tmp_path)
    got = run("who owes me", "--box", b, "--kinds", kinds(tmp_path), "--json")
    assert got.returncode == 42
    doc = json.loads(got.stdout)
    assert doc["state"] == "populated"
    assert doc["said"].endswith("nothing to answer it from yet")
    assert [r["where"] for r in doc["groups"][0]["rows"]] == ["debts", "invoices"]
    assert "add --run FOLDER" in doc["groups"][0]["rows"][0]["what"]


def test_a_thing_written_down_is_asked_of_the_box(tmp_path):
    b = box(tmp_path)
    got = run(
        "ruth's telephone number", "--box", b, "--kinds", kinds(tmp_path), "--json"
    )
    assert got.returncode == 0, got.stderr
    doc = json.loads(got.stdout)
    assert doc["said"] == (
        '"ruth\'s telephone number": a thing you wrote down; 1 line from your files'
    )
    assert doc["groups"] == [
        {
            "name": "your files: the passages holding the most of your words; "
            "the best holds 2 of 3, lacks telephone",
            "rows": [
                {"where": "diary.txt:1", "what": "Ruth's phone number is 555 0142."}
            ],
        }
    ]
    whole = json.loads(run("frosts came early", "--box", b, "--json").stdout)
    assert whole["groups"][0]["name"] == (
        "your files: the passages holding the most of your words"
    )


def test_a_kind_that_names_the_ask_too_is_answered_by_both(tmp_path):
    b = box(tmp_path)
    r = a_run(tmp_path, people="12  Ruth  in 3 files\n40  Dad  in 9 files\n")
    argv = ["ruth's phone number", "--run", r, "--kinds", kinds(tmp_path), "--json"]
    doc = json.loads(run(*argv, "--box", b).stdout)
    assert doc["said"].endswith("3 lines from people and your files")
    assert [g["name"].split(":")[0] for g in doc["groups"]] == ["people", "your files"]
    assert doc["groups"][0]["name"] == (
        "people: 1 of its 2 lines hold ruth, and come first"
    )
    assert doc["groups"][0]["rows"][0]["what"] == "12 Ruth in 3 files"
    # without the box the ask is left, and that waits on you
    got = run(*argv)
    assert got.returncode == 42
    doc = json.loads(got.stdout)
    assert doc["groups"][-1] == {
        "name": "left",
        "rows": [
            {"where": "ask", "what": "not asked of your own files: add --box BOX"}
        ],
    }


def test_files_that_hold_nothing_are_empty_not_a_failure(tmp_path):
    b = box(tmp_path)
    got = run("zzqx plork", "--box", b, "--json")
    assert got.returncode == 0
    doc = json.loads(got.stdout)
    assert doc["state"] == "empty" and doc["groups"] == []
    assert doc["said"] == (
        '"zzqx plork": a thing you wrote down; '
        "your files hold nothing for it; why-not says why"
    )
    # beside a step that answered, it is said after it
    r = a_run(tmp_path, people="Dad\n")
    doc = json.loads(
        run("plork zzqx wim phone number", "--run", r, "--box", b, "--kinds", kinds(tmp_path), "--json").stdout
    )  # fmt: skip
    assert doc["said"].endswith(
        "1 line from people; your files hold nothing for it; why-not says why"
    )


def test_the_text_is_the_report_as_every_report_add_on_prints_it(tmp_path):
    r = a_run(tmp_path, debts="Dana owes you $40\n", invoices="overdue  Theatre\n")
    got = run("who owes me", "--run", r, "--kinds", kinds(tmp_path))
    assert got.stdout.splitlines() == [
        'look: populated, "who owes me": money owed (by "owe"); '
        "2 lines from debts and invoices",
        "## debts: its 1 line",
        "  01-debts.txt:1     Dana owes you $40",
        "## invoices: its 1 line",
        "  02-invoices.txt:1  overdue Theatre",
    ]


def test_the_kinds_that_ship_are_the_ones_used_when_none_is_given(tmp_path):
    r = a_run(tmp_path, debts="Dana owes you $40\n", invoices="overdue  Theatre\n")
    got = run("who still owes me money", "--run", r)
    assert got.returncode == 0, got.stderr
    assert "money owed" in got.stdout and "from debts and invoices" in got.stdout


def test_nothing_is_written(tmp_path):
    b = box(tmp_path)
    r = a_run(tmp_path, people="Ruth\n")

    def now():
        return {p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()}

    k = kinds(tmp_path)
    before = now()
    run("ruth's phone number", "--run", r, "--box", b, "--kinds", k)
    assert now() == before


def test_no_more_than_three_passages_of_your_files_are_shown(tmp_path):
    text = "".join(f"The frost came early in year {n}.\n\n" for n in range(1, 6))
    b = box(tmp_path, text)
    doc = json.loads(run("frost came early", "--box", b, "--json").stdout)
    assert len(doc["groups"][0]["rows"]) == look.PASSAGES == 3
    assert doc["said"].endswith("3 lines from your files")


def test_a_word_your_list_reads_another_way_is_not_said_to_be_lacking(tmp_path):
    b = box(tmp_path, words="telephone = phone\n")
    doc = json.loads(run("ruth's telephone number", "--box", b, "--json").stdout)
    assert doc["groups"][0]["name"] == (
        "your files: the passages holding the most of your words"
    )


def test_a_long_place_doesnt_push_every_row_past_sixty(tmp_path):
    b = box(tmp_path)
    long = "a-very-long-name-for-a-file-of-frost-" * 2 + ".txt"
    (tmp_path / "pile" / long).write_text("The frosts came early again.\n")
    lines = run("frosts came early", "--box", b).stdout.splitlines()
    assert len(long) > 60
    assert f"  {long}:1  The frosts came early again." in lines
    assert f"  {'diary.txt:3':<60}  The frosts came early last year." in lines
