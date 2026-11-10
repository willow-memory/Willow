"""why-not: for a question the folder doesn't hold, which words nothing holds,
the nearest passages and what they lacked, a close spelling with the words-list
line that would teach it, and the kind of file that would have answered; a
question it does hold said so; nothing written, not even a record row."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "why_not.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("why_not", SCRIPT)
wn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wn)

DIARY = "Tomatoes need six hours of sun.\n\nThe frosts came early last year.\n\nPlant the beans in May.\n"


def box(
    tmp_path: Path, files: dict[str, str] | None = None, words: str | None = None
) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(exist_ok=True)
    for name, text in (files or {"diary.txt": DIARY}).items():
        (pile / name).write_text(text)
    b = tmp_path / "box"
    argv = [
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
    ]
    if words is not None:
        (tmp_path / "w.txt").write_text(words)
        (tmp_path / "w.txt").chmod(0o600)
        argv += ["--words", str(tmp_path / "w.txt")]
    subprocess.run(argv, check=True, capture_output=True)
    return b


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def test_a_question_the_files_hold_says_so_and_where(tmp_path):
    b = box(tmp_path)
    got = run("--box", str(b), "how much sun do tomatoes want")
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        'why-not: empty, "how much sun do tomatoes want": '
        "your files do hold it: diary.txt:1\n"
    )
    doc = json.loads(
        run("--box", str(b), "how much sun do tomatoes want", "--json").stdout
    )
    assert doc == {
        "addon": "why-not", "state": "empty", "groups": [],
        "said": '"how much sun do tomatoes want": your files do hold it: diary.txt:1',
    }  # fmt: skip


def test_each_word_is_counted_and_a_word_nothing_holds_is_named(tmp_path):
    b = box(tmp_path)
    q = "when does the frost come in autumn"
    got = run("--box", str(b), q)
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        'why-not: populated, "when does the frost come in autumn": '
        "a passage has to hold 2 of the 3 words at once",
        "## words",
        "  frost         held by 1 passage: diary.txt:3",
        "  come          no passage holds it",
        "  autumn        no passage holds it",
        "## the nearest it came",
        "  diary.txt:3   holds 1 (frost); lacks come, autumn",
        "## what would have answered it",
        "  kind of file  a dated note, an event or a deadline, with the date on the line",
    ]
    doc = json.loads(run("--box", str(b), q, "--json").stdout)
    assert doc["state"] == "populated"
    assert [g["name"] for g in doc["groups"]] == [
        "words", "the nearest it came", "what would have answered it"]  # fmt: skip
    assert doc["groups"][0]["rows"][0] == {
        "where": "frost", "what": "held by 1 passage: diary.txt:3"}  # fmt: skip


def test_the_words_the_kernel_leaves_out_are_not_counted():
    assert wn.want_of("When does the frost come? Frost!") == ["frost", "come"]
    assert wn.want_of("how do I") == []


def test_a_question_of_only_common_words_says_to_name_the_thing(tmp_path):
    b = box(tmp_path)
    got = run("--box", str(b), "how do I")
    assert got.returncode == 42
    assert got.stdout == (
        'why-not: unreachable, "how do I": '
        "every word is a common one; name the thing you mean\n"
    )
    doc = json.loads(run("--box", str(b), "how do I", "--json").stdout)
    assert doc["state"] == "unreachable" and doc["groups"] == []


def test_a_word_held_by_its_plain_form_counts_as_held(tmp_path):
    b = box(tmp_path, {"bills.txt": "The invoices are in the blue folder.\n"})
    got = run("--box", str(b), "where is the invoice paperwork cabinet")
    assert got.returncode == 42, got.stdout
    assert "invoice" in got.stdout and "held by 1 passage: bills.txt:1" in got.stdout
    assert "  paperwork     no passage holds it" in got.stdout


def test_a_spelling_nothing_holds_but_a_close_one_does(tmp_path):
    b = box(
        tmp_path,
        {
            "n.txt": "The boiler service is due in November.\n\nCall the plumber about the radiator.\n"
        },
    )
    got = run("--box", str(b), "when is the radiater serviced again")
    assert got.returncode == 42
    assert "(your files say 'radiator': radiater = radiator)" in got.stdout
    assert json.loads(run("--box", str(b), "when is the radiater serviced again", "--json").stdout)[
        "groups"][0]["rows"][0]["what"].endswith("(your files say 'radiator': radiater = radiator)")  # fmt: skip


def test_the_kind_of_file_follows_the_questions_opening():
    kinds = {q: wn.kind_of(q) for q in ("how much rent", "how many hives", "when is it", "what time is it", "who owes me",
             "where is the key", "why did it fail", "how do I bake", "what is the code", "tell me more")}  # fmt: skip
    assert "number" in kinds["how much rent"] and "number" in kinds["how many hives"]
    assert "dated" in kinds["when is it"] and "dated" in kinds["what time is it"]
    assert "person" in kinds["who owes me"] and "place" in kinds["where is the key"]
    assert "reason" in kinds["why did it fail"] and "steps" in kinds["how do I bake"]
    assert "plainly" in kinds["what is the code"] and kinds["tell me more"] is None


def test_a_boxs_words_list_is_read_as_the_bite_reads_it(tmp_path):
    b = box(
        tmp_path,
        {"n.txt": "The boiler service is due in November.\n"},
        words="serviced = service\n",
    )
    assert run("--box", str(b), "when is the boiler serviced").returncode == 0


def test_it_writes_nothing_not_even_a_record_row(tmp_path):
    b = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(b), "when does the frost come in autumn")
    run("--box", str(b), "how much sun do tomatoes want")
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_a_passage_holding_none_of_the_words_is_said_so(tmp_path):
    got = run("--box", str(box(tmp_path)), "zebra giraffe")
    assert got.returncode == 42
    assert got.stdout.splitlines()[0] == (
        'why-not: populated, "zebra giraffe": a passage has to hold 1 of the 2 words '
        "at once; no passage holds any of them"
    )
    assert "## the nearest it came" not in got.stdout


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = box(tmp_path)
    for argv in (
        [],
        ["--box"],
        ["--box", str(b)],
        ["--box", str(b), "a", "b"],
        ["--box", str(b), "--stray"],
        ["--box", str(tmp_path), "q"],
    ):
        got = run(*argv)
        assert got.returncode == 2, argv
    assert "why_not.py" in run().stderr


def test_one_word_is_not_pluralised(tmp_path):
    got = run("--box", str(box(tmp_path)), "zebra")
    assert "a passage has to hold 1 of the 1 word at once" in got.stdout


# ── every question of a file, and only the ones a scan found nothing for ────
QUESTIONS = (
    "# what I ask\n"
    "beans\twhen do the beans go in\n"
    "\n"
    "frost\twhen does the frost come in autumn\n"
    "roof\twho mended the roof slates\n"
)


def asked(tmp_path: Path, text: str = QUESTIONS) -> Path:
    q = tmp_path / "questions.txt"
    q.write_text(text)
    return q


def scanned(tmp_path: Path, states: dict[str, str]) -> Path:
    """What scan would have printed: a line a question, its name and state."""
    path = tmp_path / "scanned.txt"
    path.write_text(
        "".join(
            json.dumps({"question": n, "state": s, "served": []}) + "\n"
            for n, s in states.items()
        )
    )
    return path


def test_each_question_of_a_file_that_finds_nothing_is_a_group(tmp_path):
    b = box(tmp_path)
    got = run("--box", str(b), "--questions", str(asked(tmp_path)), "--json")
    assert got.returncode == 42, got.stderr
    doc = json.loads(got.stdout)
    assert doc["state"] == "populated"
    assert doc["said"] == "2 of 3 questions found nothing; each says why"
    names = [g["name"] for g in doc["groups"]]
    assert names == [
        "frost: when does the frost come in autumn",
        "roof: who mended the roof slates",
    ], "the one the files hold has no group; the rest keep the file's order"
    frost = doc["groups"][0]["rows"]
    assert frost[0] == {
        "where": "",
        "what": "a passage has to hold 2 of the 3 words at once",
    }
    assert {"where": "autumn", "what": "no passage holds it"} in frost
    assert any(
        r["where"] == "diary.txt:3" and "holds 1 (frost)" in r["what"] for r in frost
    )
    assert not any(r["where"] == "kind of file" for r in frost), "the kind is left out"
    roof = doc["groups"][1]["rows"]
    assert roof[0]["what"].endswith("; no passage holds any of them")


def test_a_bare_question_is_named_by_its_line(tmp_path):
    b = box(tmp_path)
    q = asked(tmp_path, "when do the beans go in\nwho mended the roof slates\n")
    doc = json.loads(run("--box", str(b), "--questions", str(q), "--json").stdout)
    assert [g["name"] for g in doc["groups"]] == ["2: who mended the roof slates"]
    assert doc["said"] == "1 of 2 questions found nothing; each says why"


def test_a_file_the_folder_answers_whole_has_nothing_to_explain(tmp_path):
    b = box(tmp_path)
    q = asked(tmp_path, "beans\twhen do the beans go in\n")
    got = run("--box", str(b), "--questions", str(q), "--json")
    assert got.returncode == 0
    doc = json.loads(got.stdout)
    assert doc["state"] == "empty" and doc["groups"] == []
    assert doc["said"] == "your files hold all 1 question; nothing to explain"


def test_only_the_questions_a_scan_said_were_empty_are_explained(tmp_path):
    b = box(tmp_path)
    q = asked(tmp_path)
    of = scanned(
        tmp_path, {"beans": "populated", "frost": "populated", "roof": "empty"}
    )
    got = run("--box", str(b), "--questions", str(q), "--of", str(of), "--json")
    assert got.returncode == 42, got.stderr
    doc = json.loads(got.stdout)
    assert [g["name"] for g in doc["groups"]] == ["roof: who mended the roof slates"]
    assert doc["said"] == "1 of 1 question found nothing; each says why"


def test_a_scan_that_found_them_all_hands_on_nothing_to_explain(tmp_path):
    b = box(tmp_path)
    of = scanned(tmp_path, {"beans": "populated", "frost": "populated"})
    got = run(
        "--box", str(b), "--questions", str(asked(tmp_path)), "--of", str(of), "--json"
    )
    assert got.returncode == 0
    doc = json.loads(got.stdout)
    assert doc["state"] == "empty"
    assert doc["said"] == "the scan handed on no empty question; nothing to explain"


def test_what_isnt_a_scans_is_refused_and_says_which_line(tmp_path):
    b = box(tmp_path)
    q = asked(tmp_path)
    bad = tmp_path / "bad.txt"
    bad.write_text(json.dumps({"question": "roof", "state": "empty"}) + "\nnot json\n")
    got = run("--box", str(b), "--questions", str(q), "--of", str(bad))
    assert got.returncode == 2
    assert (
        "can't be taken: line 2 has no question and state, as scan's lines do"
        in got.stderr
    )
    bad.write_text(json.dumps({"question": "roof"}) + "\n")
    got = run("--box", str(b), "--questions", str(q), "--of", str(bad))
    assert got.returncode == 2 and "line 1 has no question and state" in got.stderr
    bad.write_text("\n\n")
    got = run("--box", str(b), "--questions", str(q), "--of", str(bad))
    assert got.returncode == 2
    assert "it is empty: the step before said nothing to hand on" in got.stderr
    got = run("--box", str(b), "--questions", str(q), "--of", str(tmp_path / "gone"))
    assert got.returncode == 2 and "could not be read" in got.stderr


def test_a_questions_file_with_no_question_or_asked_wrongly_is_refused(tmp_path):
    b = box(tmp_path)
    q = asked(tmp_path)
    none = tmp_path / "none.txt"
    none.write_text("# nothing here\n\n")
    got = run("--box", str(b), "--questions", str(none))
    assert got.returncode == 2 and "holds no question" in got.stderr
    of = scanned(tmp_path, {"roof": "empty"})
    for argv in (
        ["--box", str(b), "--questions", str(q), "a question too"],
        ["--box", str(b), "--of", str(of), "a question"],
        ["--box", str(b), "--questions"],
        ["--box", str(b), "--questions", str(q), "--of"],
        ["--box", str(b), "--questions", str(tmp_path / "gone")],
    ):
        assert run(*argv).returncode == 2, argv
    usage = run().stderr
    assert "--questions FILE [--of SCANNED]" in usage and "why_not.py" in usage


def test_many_questions_write_nothing(tmp_path):
    b = box(tmp_path)
    before = {p: p.read_bytes() for p in sorted(b.rglob("*")) if p.is_file()}
    of = scanned(tmp_path, {"roof": "empty"})
    run("--box", str(b), "--questions", str(asked(tmp_path)), "--of", str(of))
    assert {p: p.read_bytes() for p in sorted(b.rglob("*")) if p.is_file()} == before


def test_the_text_of_many_is_a_heading_a_question(tmp_path):
    b = box(tmp_path)
    got = run("--box", str(b), "--questions", str(asked(tmp_path)))
    lines = got.stdout.splitlines()
    assert (
        lines[0] == "why-not: populated, 2 of 3 questions found nothing; each says why"
    )
    assert "## frost: when does the frost come in autumn" in lines
    assert "## roof: who mended the roof slates" in lines
