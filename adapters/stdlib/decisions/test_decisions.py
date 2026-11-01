"""decisions: a yes and a no kept with their reasons, a never told from a
not-yet, and a lookup of what the record says about a new question."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "decisions.py"
spec = importlib.util.spec_from_file_location("decisions", SCRIPT)
dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc)
NOW = ["--now", "2026-11-01T09:00:00Z"]


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv],
                          capture_output=True, text=True)  # fmt: skip


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "notes.md").write_text("We host our own mail.\n")
    box = tmp_path / "box"
    got = run("init", "--box", str(box), "--pile", str(pile),
              "--key", str(tmp_path / "key"), *NOW, script=KERNEL)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    got, breaks = dc.kernel.read(box / "record.jsonl")
    assert breaks == []
    return got


def chose(box, q, a, why, *more) -> subprocess.CompletedProcess:
    return run("chose", "--box", str(box), "--question", q, "--answer", a,
               "--reason", why, *more, *NOW)  # fmt: skip


def no(box, q, opt, why, *more) -> subprocess.CompletedProcess:
    return run("no", "--box", str(box), "--question", q, "--option", opt,
               "--reason", why, *more, *NOW)  # fmt: skip


def ask(box, *words) -> subprocess.CompletedProcess:
    return run("ask", "--box", str(box), *words)


def test_a_yes_keeps_its_question_answer_and_reason_unattested(tmp_path):
    box = make(tmp_path)
    got = chose(
        box,
        "Which database holds the orders?",
        "Postgres",
        "it is the one we can restore",
    )
    assert got.returncode == 0 and "unattested" in got.stdout
    row = rows(box)[-1]
    assert row["kind"] == "chose" and row["who"] == "decisions"
    assert row["standing"] == "unattested" and row["replaces"] is None
    assert (row["question"], row["answer"]) == (
        "Which database holds the orders?",
        "Postgres",
    )
    assert row["reason"] == "it is the one we can restore"


def test_a_no_is_a_never_or_a_not_yet_and_says_which(tmp_path):
    box = make(tmp_path)
    assert (
        no(
            box, "Should we sell the data?", "sell it", "we promised not to", "--never"
        ).returncode
        == 0
    )
    never = rows(box)[-1]
    assert (never["door"], never["reopen_when"]) == ("never", None)
    got = no(box, "Should we move to the cloud?", "move now", "too dear this year",
             "--reopen-when", "the hosting bill passes 500 a month")  # fmt: skip
    assert (
        got.returncode == 0
        and "ask again when: the hosting bill passes 500" in got.stdout
    )
    yet = rows(box)[-1]
    assert (yet["door"], yet["reopen_when"]) == (
        "not yet",
        "the hosting bill passes 500 a month",
    )
    assert yet["standing"] == "unattested" and yet["kind"] == "no"


def test_a_no_with_neither_kind_or_both_is_refused_and_writes_nothing(tmp_path):
    box = make(tmp_path)
    before = len(rows(box))
    for more in ([], ["--never", "--reopen-when", "later"]):
        got = no(box, "Should we move?", "move", "too dear", *more)
        assert got.returncode == 2 and "say which no it is" in got.stderr
    assert len(rows(box)) == before


def test_a_missing_or_blank_reason_is_refused(tmp_path):
    box = make(tmp_path)
    before = len(rows(box))
    assert chose(box, "Which database?", "Postgres", "   ").returncode == 2
    assert no(box, "Should we move?", "move", "", "--never").returncode == 2
    assert (
        no(box, "Should we move?", "move", "dear", "--reopen-when", " ").returncode == 2
    )
    got = run("chose", "--box", str(box), "--question", "q", "--answer", "a")
    assert got.returncode == 2 and "decisions.py" in got.stderr
    assert len(rows(box)) == before


def test_asking_finds_the_answer_its_lineage_and_the_reasons(tmp_path):
    box = make(tmp_path)
    chose(box, "Which database holds the orders?", "SQLite", "one file, nothing to run")
    first = rows(box)[-1]["n"]
    got = chose(box, "Which database holds the orders?", "Postgres", "the orders outgrew one file",
                "--replaces", str(first))  # fmt: skip
    assert got.returncode == 0 and f"replaces row {first}" in got.stdout
    got = ask(box, "what database should hold orders now")
    assert got.returncode == 0
    assert "chose, row 2" in got.stdout and "Postgres" in got.stdout
    assert "because: the orders outgrew one file" in got.stdout
    assert (
        f"replaced row {first}: SQLite (because: one file, nothing to run)"
        in got.stdout
    )
    assert "every row stands unattested" in got.stdout
    assert got.stdout.count("chose, row") == 1


def test_a_replaced_decision_is_found_through_its_replacement_once(tmp_path):
    box = make(tmp_path)
    chose(box, "Which mailer sends the receipts?", "Sendmail", "it was there")
    chose(box, "How do receipts go out by email?", "Postfix", "sendmail is not kept up",
          "--replaces", "1")  # fmt: skip
    got = ask(box, "mailer sends receipts")  # words only the first row's question holds
    assert got.returncode == 0 and got.stdout.count("chose, row") == 1
    assert "chose, row 2" in got.stdout and "replaced row 1: Sendmail" in got.stdout


def test_a_row_replaced_already_or_not_a_decision_cannot_be_replaced(tmp_path):
    box = make(tmp_path)
    chose(box, "Which database?", "SQLite", "simple")
    chose(box, "Which database?", "Postgres", "grew", "--replaces", "1")
    again = chose(box, "Which database?", "MySQL", "a whim", "--replaces", "1")
    assert again.returncode == 2 and "replaced already, by row 2" in again.stderr
    assert chose(box, "Which database?", "x", "y", "--replaces", "0").returncode == 2
    assert chose(box, "Which database?", "x", "y", "--replaces", "99").returncode == 2
    assert chose(box, "Which database?", "x", "y", "--replaces", "-1").returncode == 2
    assert len(rows(box)) == 3


def test_a_never_and_a_not_yet_are_told_apart_when_asked(tmp_path):
    box = make(tmp_path)
    no(
        box,
        "Should we sell the customer data?",
        "sell it",
        "we promised not to",
        "--never",
    )
    no(box, "Should we move hosting to the cloud?", "move now", "too dear this year",
       "--reopen-when", "the hosting bill passes 500 a month")  # fmt: skip
    got = ask(box, "sell customer data")
    assert got.returncode == 0 and "no, never, row 1" in got.stdout
    assert (
        "because: we promised not to" in got.stdout and "reopen when" not in got.stdout
    )
    got = ask(box, "cloud hosting")
    assert "no, not yet, row 2" in got.stdout
    assert (
        "reopen when: the hosting bill passes 500 a month  (yours to check)"
        in got.stdout
    )


def test_reopening_a_not_yet_keeps_the_no_and_says_why(tmp_path):
    box = make(tmp_path)
    no(
        box,
        "Should we move hosting to the cloud?",
        "move now",
        "too dear",
        "--reopen-when",
        "bill passes 500",
    )
    got = run(
        "reopen",
        "--box",
        str(box),
        "--row",
        "1",
        "--because",
        "the bill was 640 in October",
        *NOW,
    )
    assert got.returncode == 0 and "stays on the record" in got.stdout
    assert rows(box)[1]["kind"] == "no" and rows(box)[-1]["kind"] == "reopen"
    assert rows(box)[-1]["of"] == 1 and rows(box)[-1]["standing"] == "unattested"
    out = ask(box, "cloud hosting").stdout
    assert "reopened, row 2: the bill was 640 in October" in out
    assert "yours to check" not in out and "because: too dear" in out
    again = run("reopen", "--box", str(box), "--row", "1", "--because", "again")
    assert again.returncode == 2 and "reopened already" in again.stderr


def test_a_never_cannot_be_reopened_and_a_non_no_cannot_either(tmp_path):
    box = make(tmp_path)
    no(box, "Should we sell the data?", "sell it", "promised", "--never")
    chose(box, "Which database?", "Postgres", "restorable")
    for row in ("1", "2", "0", "9"):
        got = run(
            "reopen", "--box", str(box), "--row", row, "--because", "changed my mind"
        )
        assert got.returncode == 2, row
    assert (
        "names no condition"
        in run("reopen", "--box", str(box), "--row", "1", "--because", "x").stderr
    )
    assert len(rows(box)) == 3


def test_nothing_on_the_record_is_42_and_not_the_same_as_free(tmp_path):
    box = make(tmp_path)
    got = ask(box, "should we adopt kubernetes")
    assert got.returncode == 42 and "not the same as free to decide" in got.stdout
    chose(box, "Which database holds the orders?", "Postgres", "restorable")
    got = ask(box, "should we adopt kubernetes")
    assert got.returncode == 42


def test_a_question_must_hold_half_of_the_shorter_texts_words():
    q = "Which database holds the orders"
    assert dc.about("what database holds orders now", q) == [
        "database",
        "holds",
        "orders",
    ]
    assert dc.about("database backups", q) == ["database"]  # one of its two: half
    assert dc.about("database backups nightly weekly", q) == []  # one of four: not half
    # counted against the shorter one: a long stored line holds a short question
    assert dc.about(
        "orders", "Which database holds the customer orders and invoices"
    ) == ["orders"]
    assert dc.about("the and of", q) == [] and dc.about(q, "") == []


def test_a_plain_form_of_a_word_still_matches():
    assert dc.about("hosting costs", "Which hosts cost too much") == [
        "costs",
        "hosting",
    ]


def test_a_question_of_function_words_is_refused(tmp_path):
    box = make(tmp_path)
    got = ask(box, "what is the")
    assert got.returncode == 2 and "say more" in got.stderr


def test_asking_writes_nothing(tmp_path):
    box = make(tmp_path)
    chose(box, "Which database holds the orders?", "Postgres", "restorable")
    before = (box / "record.jsonl").read_bytes()
    ask(box, "database orders")
    ask(box, "kubernetes")
    assert (box / "record.jsonl").read_bytes() == before


def test_asking_twice_gives_the_same_words(tmp_path):
    box = make(tmp_path)
    chose(box, "Which database holds the orders?", "Postgres", "restorable")
    no(box, "Should orders move to a document store?", "mongo", "no joins", "--never")
    assert ask(box, "database orders").stdout == ask(box, "database orders").stdout


def test_a_row_that_cannot_be_read_is_skipped_and_said(tmp_path):
    box = make(tmp_path)
    chose(box, "Which database holds the orders?", "Postgres", "restorable")
    dc.kernel.append(
        box,
        "2026-11-01T09:00:00Z",
        "chose",
        who="decisions",
        question="Which database?",
        answer="x",
    )
    dc.kernel.append(box, "2026-11-01T09:00:00Z", "chose", who="decisions", question="Which database orders?",
                     answer="MySQL", reason="r", replaces=7)  # fmt: skip
    dc.kernel.append(box, "2026-11-01T09:00:00Z", "no", who="decisions", question="Which database orders?",
                     option="o", reason="r", door="never", reopen_when="later")  # fmt: skip
    dc.kernel.append(
        box, "2026-11-01T09:00:00Z", "reopen", who="decisions", of=1, because="b"
    )
    got = ask(box, "database orders")
    assert (
        got.returncode == 0 and "Postgres" in got.stdout and "MySQL" not in got.stdout
    )
    for n, why in ((2, "missing its question, answer or reason"), (3, "not an earlier decision"),
                   (4, "neither a never nor a not-yet"), (5, "not an earlier not-yet")):  # fmt: skip
        assert f"skipped row {n}: " in got.stderr and why in got.stderr


def test_a_second_row_replacing_one_already_replaced_is_skipped():
    base = {"standing": "unattested", "who": "decisions", "ts": "t"}
    r = lambda n, k, **f: {"n": n, "kind": k, **base, **f}  # noqa: E731
    one = dict(question="Which database?", answer="a", reason="r")
    d = dc.decode([r(0, "chose", **one, replaces=None), r(1, "chose", **one, replaces=0),
                   r(2, "chose", **one, replaces=0)])  # fmt: skip
    assert d["replaced_by"] == {0: 1} and d["skipped"] == [
        (2, "replaces row 0, already replaced")
    ]
    # a row naming a row that comes later is no earlier decision either
    d = dc.decode(
        [r(0, "chose", **one, replaces=1), r(1, "chose", **one, replaces=None)]
    )
    assert d["skipped"] == [(0, "replaces a row that is not an earlier decision")]


def test_it_never_seals_reads_the_key_or_approves(tmp_path):
    box = make(tmp_path)
    chose(box, "Which database?", "Postgres", "restorable")
    no(box, "Should we sell?", "sell", "promised", "--never")
    assert {r["kind"] for r in rows(box)} == {"boot", "chose", "no"}
    assert {r["standing"] for r in rows(box)[1:]} == {"unattested"}
    src = SCRIPT.read_text()
    assert "seal(" not in src and "read_key" not in src and "propose" not in src


def test_a_box_that_is_not_one_or_does_not_verify_is_refused(tmp_path):
    got = ask(tmp_path, "database orders")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    box = make(tmp_path)
    rec = box / "record.jsonl"
    rec.write_bytes(rec.read_bytes().replace(b'"boot"', b'"booT"', 1))
    for got in (ask(box, "database orders"), chose(box, "q", "a", "r")):
        assert got.returncode == 2 and "doesn't verify" in got.stderr


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["chose"],
        ["toss", "--box", "x"],
        ["ask", "--box"],
        ["ask", "--box", "x"],
        ["ask", "--box", "x", "--now", "t", "words"],
        ["ask", "--box", "x", "--question", "q", "words"],
        ["reopen", "--box", "x", "--row", "one", "--because", "b"],
        ["reopen", "--box", "x", "--row", "1", "--because", "b", "extra"],
        [
            "chose",
            "--box",
            "x",
            "--question",
            "q",
            "--answer",
            "a",
            "--reason",
            "r",
            "--never",
        ],
        [
            "chose",
            "--box",
            "x",
            "--box",
            "y",
            "--question",
            "q",
            "--answer",
            "a",
            "--reason",
            "r",
        ],
        ["chose", "--box", "x", "--bogus", "z"],
    ],
)
def test_a_bad_command_line_is_refused_with_the_usage(argv):
    got = run(*argv)
    assert got.returncode == 2 and "decisions.py" in got.stderr
