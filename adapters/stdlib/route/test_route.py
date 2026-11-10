"""route: a question is given its kind by the first line of the kinds file
with a cue in it, and the steps whose job that kind is are named, each with
its card's one line and, with --run, the file a kept run holds for it. The
rules are tried on small kinds files made here; the shipped kinds.txt is
held to a handful of real questions."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import route  # noqa: E402

ASK = "The kernel's own answer: the passage holding the most of your words."
#: whether this is the whole repo, or route copied out beside the kernel alone
WHOLE = any(p.is_dir() and p.name != "route" for p in HERE.parent.iterdir())

KINDS = """\
# what kind a question is

money owed: owe, paid me, did * pay -> debts, invoices
   # a comment, indented
a date: when is, Birthday -> coming-up, ask
a person: who, phone number -> people, ask
"""


def go(*argv) -> tuple[int, str, str]:
    """route's main, run here: (exit code, what it printed, what it said)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = route.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


def script(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "route.py"), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def table(text: str) -> list:
    got, why = route.kinds(text)
    assert why is None
    return got


def kind(question: str, text: str = KINDS) -> str:
    return route.kind_of(question, table(text))[0]


@pytest.fixture
def kinds(tmp_path) -> Path:
    f = tmp_path / "kinds.txt"
    f.write_text(KINDS, encoding="utf-8")
    return f


@pytest.fixture
def cards(tmp_path, monkeypatch) -> Path:
    """An adapters folder of our own, so a step's line is one written here:
    debts, invoices and coming-up in stdlib, people in deps."""
    adapters = tmp_path / "adapters"
    for base, name, line in (
        ("stdlib", "debts", "line: Who owes whom."),
        ("stdlib", "invoices", "line: Invoices you sent."),
        ("stdlib", "coming-up", "line: Dates in the next days."),
        ("deps", "people", "line: Everyone your files name."),
        ("stdlib", "tight", "line:No space after the colon."),
        ("stdlib", "bare", "section: Finding things"),
    ):
        (adapters / base / name).mkdir(parents=True)
        (adapters / base / name / "README.md").write_text(
            f"<!-- willow-addon\nsource: new\n{line}\nwrites: nothing\n-->\n# {name}\n",
            encoding="utf-8",
        )
    (adapters / "stdlib" / "empty").mkdir()  # a folder with no card is no add-on
    monkeypatch.setattr(route, "ADAPTERS", adapters)
    return adapters


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}  # fmt: skip


# ── the command line ─────────────────────────────────────────────────────────
def test_a_bad_command_line_is_refused_and_names_the_script():
    got = subprocess.run(
        [sys.executable, str(HERE / "route.py")], capture_output=True, text=True
    )
    assert got.returncode == 2 and "route.py" in got.stderr


def test_the_usage_is_both_command_lines_and_nothing_else():
    got = script()
    assert got.stdout == ""
    assert got.stderr.splitlines() == [
        '    python adapters/stdlib/route/route.py "who still owes me money" [--run FOLDER] [--kinds FILE] [--json]',
        "    python adapters/stdlib/route/route.py --questions FILE [--run FOLDER] [--kinds FILE] [--json]",
    ]


def test_run_as_a_script_it_routes_the_question_it_was_given(kinds):
    got = script("mom's goulash recipe", "--kinds", kinds)
    assert got.returncode == 0 and got.stderr == ""
    assert got.stdout == (
        'route: populated, "mom\'s goulash recipe": a thing you wrote down; that is the job of ask\n'
        f"  ask  {ASK}\n"
    )


@pytest.mark.parametrize(
    "argv",
    [
        [],  # neither a question nor --questions
        ["--json"],
        ["who owes me", "--questions", "{q}"],  # both
        ["who owes me", "when is it"],  # two questions
        ["one", "two", "three"],
        ["who owes me", "--run"],  # an option with no value
        ["who owes me", "--kinds"],
        ["--questions"],
        ["--kinds", "{k}"],  # options, and nothing to ask
        ["--run", "{t}"],
        ["--nope"],  # an option it doesn't have
        ["who owes me", "--nope"],
        ["--questions", "{q}", "--verbose"],
    ],
)
def test_a_command_line_it_cant_read_is_refused_with_the_usage(argv, tmp_path, kinds):
    q = tmp_path / "q.txt"
    q.write_text("who owes me\n", encoding="utf-8")
    places = {"q": q, "k": kinds, "t": tmp_path}
    code, out, err = go(*[a.format(**places) for a in argv])
    assert code == 2 and out == ""
    assert err == route.USAGE + "\n" and "--questions FILE" in err


def test_an_option_may_come_before_the_question_or_after(kinds, cards):
    after = go("who owes me", "--kinds", kinds, "--json")
    before = go("--json", "--kinds", kinds, "who owes me")
    assert after == before and after[0] == 0


# ── the kinds file ───────────────────────────────────────────────────────────
def test_a_kinds_line_is_a_kind_its_cues_and_its_steps():
    assert table(KINDS) == [
        ("money owed", [["owe"], ["paid", "me"], ["did", "*", "pay"]], ["debts", "invoices"]),
        ("a date", [["when", "is"], ["birthday"]], ["coming-up", "ask"]),
        ("a person", [["who"], ["phone", "number"]], ["people", "ask"]),
    ]  # fmt: skip


def test_blank_lines_and_comments_are_skipped_and_spaces_dont_matter():
    text = "\n\n#only: a -> b\n  spaced out :  a cue ,other   ->  one ,  two  \n\n"
    assert table(text) == [("spaced out", [["a", "cue"], ["other"]], ["one", "two"])]
    assert table("") == [] and table("# nothing but a comment\n") == []


@pytest.mark.parametrize(
    "bad",
    [
        "money owed: owe, lent",  # no arrow
        "money owed owe -> debts",  # no colon
        ": owe -> debts",  # no kind
        "money owed: owe ->",  # no step
        "money owed: owe -> , ,",
        "money owed: -> debts",  # no cue
        "money owed: , -> debts",
        "money owed -> debts: owe",  # the colon after the arrow
        "just some words",
    ],
)
def test_a_malformed_kinds_line_is_refused_naming_its_number(bad, tmp_path):
    f = tmp_path / "kinds.txt"
    f.write_text(
        f"# a comment\n\na date: when is -> ask\n{bad}\na person: who -> ask\n"
    )
    assert route.kinds(f.read_text()) == (
        [],
        "line 4 isn't `kind: cue, cue -> step, step`",
    )
    code, out, err = go("when is it", "--kinds", f)
    assert code == 2 and out == ""
    assert (
        err == "refused: the kinds file: line 4 isn't `kind: cue, cue -> step, step`\n"
    )


def test_a_bad_first_line_is_line_one(tmp_path):
    f = tmp_path / "kinds.txt"
    f.write_text("no arrow here\n")
    assert go("anything", "--kinds", f)[2].startswith(
        "refused: the kinds file: line 1 "
    )


def test_an_empty_kinds_file_sends_every_question_to_the_ask(tmp_path):
    f = tmp_path / "kinds.txt"
    f.write_text("# nothing yet\n")
    code, out, _ = go("who still owes me money", "--kinds", f)
    assert code == 0
    assert out.splitlines()[0] == (
        'route: populated, "who still owes me money": a thing you wrote down; that is the job of ask'
    )


# ── cues ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("word", ["owe", "owes", "owed", "owing", "Owes", "OWED"])
def test_a_cue_is_a_word_in_any_of_its_forms(word):
    assert kind(f"who {word} me money", "money owed: owe -> debts\n") == "money owed"
    assert kind(f"who {word} me money", "money owed: owing -> debts\n") == "money owed"


def test_a_cue_is_a_whole_word_never_a_part_of_one():
    rule = "money owed: owe, lent -> debts\n"
    assert kind("the tower on the hill", rule) == route.PLAIN  # owe in tower
    assert kind("an excellent talent", rule) == route.PLAIN  # lent in excellent
    assert kind("what I lent ruth", rule) == "money owed"


def test_a_cue_written_in_capitals_finds_the_word_in_small_letters():
    assert kind("when is grace's birthday", "a date: Birthday -> ask\n") == "a date"
    assert kind("WHEN IS IT", "a date: When Is -> ask\n") == "a date"


def test_a_word_with_an_apostrophe_is_one_word():
    rule = "a date: when's -> ask\nleft: what's left -> todo\n"
    assert kind("when's the dentist", rule) == "a date"
    assert kind("when is the dentist", rule) == route.PLAIN
    assert kind("so what's left", rule) == "left"


def test_a_few_words_are_a_cue_only_together_and_in_that_order():
    rule = "money owed: paid me -> debts\n"
    assert kind("has ruth paid me back", rule) == "money owed"
    assert kind("paid me", rule) == "money owed"
    assert kind("me, paid?", rule) == route.PLAIN  # the other way round
    assert kind("paid by me", rule) == route.PLAIN  # a word between
    assert (
        kind("who paid", rule) == route.PLAIN and kind("tell me", rule) == route.PLAIN
    )


def test_a_cue_cut_off_by_the_end_of_the_question_is_not_found():
    rule = "money owed: paid me, did * pay -> debts\n"
    assert kind("has ruth paid", rule) == route.PLAIN
    assert kind("what did ruth", rule) == route.PLAIN
    assert kind("did", rule) == route.PLAIN


def test_a_cue_at_the_start_the_middle_or_the_end_is_found():
    rule = "a person: phone number -> people\n"
    for q in (
        "phone number for ruth",
        "ruth's phone number please",
        "ruth's phone number",
    ):
        assert kind(q, rule) == "a person", q


def test_a_star_stands_for_any_one_word_and_only_one():
    rule = "money owed: did * pay -> debts\n"
    assert kind("did ruth pay", rule) == "money owed"
    assert kind("so did anyone pay for it", rule) == "money owed"
    assert kind("did pay", rule) == route.PLAIN  # no word for the star
    assert kind("did the tenant pay", rule) == route.PLAIN  # two words
    assert kind("did ruth say", rule) == route.PLAIN
    assert route.kind_of("did ruth pay", table(rule))[2] == "did * pay"


def test_a_star_in_a_question_is_not_a_word():
    assert route.said("Did * pay, or Ruth's?") == ["did", "pay", "or", "ruth's"]
    assert kind("5 * 3", "sums: * -> ask\n") == "sums"
    assert kind("* *", "sums: x -> ask\n") == route.PLAIN


def test_the_first_line_with_a_cue_wins_whatever_comes_first_in_the_question():
    rule = "a date: birthday -> coming-up\na person: who -> people\n"
    assert kind("who has a birthday", rule) == "a date"
    turned = "a person: who -> people\na date: birthday -> coming-up\n"
    assert kind("who has a birthday", turned) == "a person"


def test_the_cue_that_decided_is_the_first_of_its_line_found():
    got = route.kind_of("who owed me and has not paid me", table(KINDS))
    assert got == ("money owed", ["debts", "invoices"], "owe")
    got = route.kind_of("has ruth paid me", table(KINDS))
    assert got == ("money owed", ["debts", "invoices"], "paid me")


def test_a_question_with_no_cue_is_a_thing_you_wrote_down_for_the_ask():
    assert route.kind_of("mom's goulash recipe", table(KINDS)) == (
        "a thing you wrote down",
        ["ask"],
        "",
    )


# ── one question ─────────────────────────────────────────────────────────────
def test_one_question_is_said_with_its_kind_its_cue_and_a_row_a_step(kinds, cards):
    code, out, err = go("who still owes me money", "--kinds", kinds)
    assert code == 0 and err == ""
    assert out == (
        'route: populated, "who still owes me money": money owed (by "owe");'
        " that is the job of debts and invoices\n"
        "  debts     Who owes whom.\n"
        "  invoices  Invoices you sent.\n"
    )


def test_json_is_the_same_report_as_one_object(kinds, cards):
    code, out, err = go("who still owes me money", "--kinds", kinds, "--json")
    assert code == 0 and err == "" and out.count("\n") == 1
    assert json.loads(out) == {
        "addon": "route",
        "state": "populated",
        "said": '"who still owes me money": money owed (by "owe"); that is the job of debts and invoices',
        "groups": [
            {
                "name": None,
                "rows": [
                    {"where": "debts", "what": "Who owes whom."},
                    {"where": "invoices", "what": "Invoices you sent."},
                ],
            }
        ],
    }


def test_json_keeps_letters_as_they_were_written(kinds):
    out = go("où est la clé", "--kinds", kinds, "--json")[1]
    assert "où est la clé" in out and json.loads(out)["said"].startswith(
        '"où est la clé": '
    )


def test_a_question_with_no_cue_names_no_cue_and_the_asks_own_line(kinds):
    code, out, _ = go("mom's goulash recipe", "--kinds", kinds)
    assert code == 0
    assert out == (
        'route: populated, "mom\'s goulash recipe": a thing you wrote down;'
        " that is the job of ask\n"
        f"  ask  {ASK}\n"
    )


def test_three_steps_are_joined_with_and(tmp_path):
    f = tmp_path / "kinds.txt"
    f.write_text("coming: due -> ask, ask, ask\n")
    head = go("what is due", "--kinds", f)[1].splitlines()[0]
    assert head.endswith('coming (by "due"); that is the job of ask and ask and ask')


def test_the_questions_spaces_are_made_single(kinds):
    code, out, _ = go("  mom's \t goulash\n recipe  ", "--kinds", kinds)
    assert code == 0 and out.startswith('route: populated, "mom\'s goulash recipe": ')


def test_a_step_is_found_in_stdlib_or_in_deps_and_its_line_is_its_cards(kinds, cards):
    code, out, _ = go("ruth's phone number", "--kinds", kinds)
    assert code == 0
    assert out.splitlines()[1:] == [
        "  people  Everyone your files name.",
        f"  ask     {ASK}",
    ]
    assert route.line_of("people") == "Everyone your files name."
    assert route.line_of("tight") == "No space after the colon."
    assert route.line_of("bare") == ""  # a card with no line still is an add-on
    assert route.line_of("ask") == ASK


def test_a_card_with_no_line_is_a_row_of_the_name_alone(tmp_path, cards):
    f = tmp_path / "kinds.txt"
    f.write_text("x: zebra -> bare, tight\n")
    code, out, _ = go("a zebra", "--kinds", f)
    assert code == 0
    assert out.splitlines()[1:] == ["  bare", "  tight  No space after the colon."]


def test_a_step_that_is_not_an_add_on_here_says_so_and_exits_42(tmp_path, cards):
    f = tmp_path / "kinds.txt"
    f.write_text("x: zebra -> debts, no-such-thing, empty, ask\n")
    code, out, err = go("a zebra", "--kinds", f)
    assert code == 42 and err == ""
    assert out.splitlines()[1:] == [
        "  debts          Who owes whom.",
        "  no-such-thing  not an add-on that is here",
        "  empty          not an add-on that is here",
        f"  ask            {ASK}",
    ]
    assert route.line_of("no-such-thing") is None and route.line_of("empty") is None
    doc = json.loads(go("a zebra", "--kinds", f, "--json")[1])
    assert doc["state"] == "populated"
    assert go("a zebra", "--kinds", f, "--json")[0] == 42
    assert go("no stripes", "--kinds", f)[0] == 0  # the ask is always here


# ── --run: what a kept run already found ─────────────────────────────────────
def a_run(tmp_path: Path, *names: str) -> Path:
    run = tmp_path / "mine" / "run"
    (run / "reports").mkdir(parents=True)
    for name in ("00-stack.txt", "notes.txt", "reports/03-debts.json", *names):
        (run / name).write_text("kept\n", encoding="utf-8")
    return run


def test_a_run_shows_the_file_it_kept_each_steps_output_in(tmp_path, kinds, cards):
    run = a_run(tmp_path, "02-scan.txt", "03-debts.txt")
    code, out, _ = go("who owes me", "--kinds", kinds, "--run", run)
    assert code == 0
    assert out.splitlines()[1:] == [
        f"  debts     Who owes whom.   {run / '03-debts.txt'}",
        "  invoices  Invoices you sent.",  # the run has no such step: nothing added
    ]
    doc = json.loads(go("who owes me", "--kinds", kinds, "--run", run, "--json")[1])
    assert doc["groups"][0]["rows"] == [
        {"where": "debts", "what": f"Who owes whom.   {run / '03-debts.txt'}"},
        {"where": "invoices", "what": "Invoices you sent."},
    ]


def test_a_step_that_ran_more_than_once_shows_the_last(tmp_path, kinds, cards):
    run = a_run(
        tmp_path, "03-debts.txt", "07-debts.txt", "12-debts.txt", "09-invoices.txt"
    )
    out = go("who owes me", "--kinds", kinds, "--run", run)[1]
    assert out.splitlines()[1:] == [
        f"  debts     Who owes whom.   {run / '12-debts.txt'}",
        f"  invoices  Invoices you sent.   {run / '09-invoices.txt'}",
    ]
    assert route.kept(run)["debts"] == [
        str(run / n) for n in ("03-debts.txt", "07-debts.txt", "12-debts.txt")
    ]


def test_a_step_with_a_hyphen_in_its_name_is_found_in_a_run(tmp_path, kinds, cards):
    run = a_run(tmp_path, "05-coming-up.txt", "06-up.txt")
    out = go("when is the dentist", "--kinds", kinds, "--run", run)[1]
    assert out.splitlines()[1] == (
        f"  coming-up  Dates in the next days.   {run / '05-coming-up.txt'}"
    )
    assert out.splitlines()[2] == f"  ask        {ASK}"  # no glance, no scan


def test_the_asks_file_is_the_runs_glance_or_else_its_scan(tmp_path, kinds):
    run = a_run(tmp_path, "01-scan.txt", "02-glance.txt", "04-scan.txt")
    out = go("mom's goulash recipe", "--kinds", kinds, "--run", run)[1]
    assert out.splitlines()[1] == f"  ask  {ASK}   {run / '02-glance.txt'}"
    (run / "02-glance.txt").unlink()
    out = go("mom's goulash recipe", "--kinds", kinds, "--run", run)[1]
    assert out.splitlines()[1] == f"  ask  {ASK}   {run / '04-scan.txt'}"
    (run / "01-scan.txt").unlink()
    (run / "04-scan.txt").unlink()
    (run / "03-ask.txt").write_text("kept\n")  # a step named ask is not the ask's
    out = go("mom's goulash recipe", "--kinds", kinds, "--run", run)[1]
    assert out.splitlines()[1] == f"  ask  {ASK}"


def test_the_runs_log_and_its_other_files_are_no_steps_output(tmp_path):
    run = a_run(tmp_path, "03-debts.txt", "debts.txt", "x3-debts.txt", "04-debts.json")
    assert route.kept(run) == {"debts": [str(run / "03-debts.txt")]}
    assert route.kept(None) == {}
    f = tmp_path / "kinds.txt"
    f.write_text("x: zebra -> stack, notes\n")
    out = go("a zebra", "--kinds", f, "--run", run)[1]
    assert str(run) not in out  # 00-stack.txt is the log, not a step's output


def test_a_run_with_none_of_the_steps_adds_nothing(tmp_path, kinds, cards):
    run = a_run(tmp_path)
    with_run = go("who owes me", "--kinds", kinds, "--run", run)
    assert with_run == go("who owes me", "--kinds", kinds) and with_run[0] == 0


def test_a_run_that_is_not_a_folder_is_refused(tmp_path, kinds):
    code, out, err = go("who owes me", "--kinds", kinds, "--run", tmp_path / "gone")
    assert code == 2 and out == ""
    assert err == f"refused: {tmp_path / 'gone'} isn't a folder\n"
    code, out, err = go("who owes me", "--run", kinds, "--kinds", kinds)
    assert code == 2 and out == "" and err == f"refused: {kinds} isn't a folder\n"


# ── --questions: many at once ────────────────────────────────────────────────
QUESTIONS = """\
dentist\twhen is the  dentist
# a comment

mom's goulash recipe
late\thas ruth paid me
  who owes me money
\truth's phone number
   # another comment
the shed key
"""


def asked(tmp_path: Path, text: str = QUESTIONS) -> Path:
    f = tmp_path / "questions.txt"
    f.write_text(text, encoding="utf-8")
    return f


def test_questions_are_grouped_by_kind_in_the_kinds_files_order(tmp_path, kinds, cards):
    code, out, err = go("--questions", asked(tmp_path), "--kinds", kinds)
    assert code == 0 and err == ""
    assert out == (
        "route: populated, 6 questions: 2 money owed, 1 a date, 1 a person,"
        " 2 a thing you wrote down\n"
        "## money owed: 2\n"
        "  -> debts      Who owes whom.\n"
        "  -> invoices   Invoices you sent.\n"
        "  late          has ruth paid me\n"
        "  6             who owes me money\n"
        "## a date: 1\n"
        "  -> coming-up  Dates in the next days.\n"
        f"  -> ask        {ASK}\n"
        "  dentist       when is the dentist\n"
        "## a person: 1\n"
        "  -> people     Everyone your files name.\n"
        f"  -> ask        {ASK}\n"
        "  7             ruth's phone number\n"
        "## a thing you wrote down: 2\n"
        f"  -> ask        {ASK}\n"
        "  4             mom's goulash recipe\n"
        "  9             the shed key\n"
    )


def test_questions_as_json_are_a_group_a_kind(tmp_path, kinds, cards):
    code, out, _ = go("--json", "--questions", asked(tmp_path), "--kinds", kinds)
    assert code == 0
    doc = json.loads(out)
    assert {k: doc[k] for k in ("addon", "state", "said")} == {
        "addon": "route",
        "state": "populated",
        "said": "6 questions: 2 money owed, 1 a date, 1 a person, 2 a thing you wrote down",
    }
    assert [g["name"] for g in doc["groups"]] == [
        "money owed: 2",
        "a date: 1",
        "a person: 1",
        "a thing you wrote down: 2",
    ]
    assert doc["groups"][0]["rows"] == [
        {"where": "-> debts", "what": "Who owes whom."},
        {"where": "-> invoices", "what": "Invoices you sent."},
        {"where": "late", "what": "has ruth paid me"},
        {"where": "6", "what": "who owes me money"},
    ]
    assert doc["groups"][3]["rows"] == [
        {"where": "-> ask", "what": ASK},
        {"where": "4", "what": "mom's goulash recipe"},
        {"where": "9", "what": "the shed key"},
    ]


def test_a_kind_no_question_has_is_no_group(tmp_path, kinds, cards):
    f = asked(tmp_path, "ruth's phone number\nwho is corinne\n")
    code, out, _ = go("--questions", f, "--kinds", kinds)
    assert code == 0
    assert out.splitlines() == [
        "route: populated, 2 questions: 2 a person",
        "## a person: 2",
        "  -> people  Everyone your files name.",
        f"  -> ask     {ASK}",
        "  1          ruth's phone number",
        "  2          who is corinne",
    ]


def test_one_question_in_a_file_is_still_a_group_and_is_counted_as_one(tmp_path, kinds):
    for text, name in (("mom's goulash recipe\n", "1"), ("soup\tmom's goulash recipe\n", "soup"),
                       ("\n\tmom's goulash recipe\n", "2")):  # fmt: skip
        code, out, _ = go("--questions", asked(tmp_path, text), "--kinds", kinds)
        assert code == 0
        assert out.splitlines() == [
            "route: populated, 1 question: 1 a thing you wrote down",
            "## a thing you wrote down: 1",
            f"  -> ask  {ASK}",
            f"  {name:<6}  mom's goulash recipe",
        ]


def test_a_kind_written_on_two_lines_is_one_group_with_both_lines_steps(
    tmp_path, cards
):
    f = tmp_path / "kinds.txt"
    f.write_text(
        "a date: birthday -> coming-up, ask\n"
        "a person: who -> people\n"
        "a date: when is -> ask, debts\n"
        "a thing you wrote down: recipe -> invoices\n"
    )
    q = asked(
        tmp_path, "when is it\nwho is it\ngrace's birthday\nthe recipe\nthe shed key\n"
    )
    code, out, _ = go("--questions", q, "--kinds", f)
    assert code == 0
    assert out.splitlines() == [
        "route: populated, 5 questions: 2 a date, 1 a person, 2 a thing you wrote down",
        "## a date: 2",
        f"  -> ask        {ASK}",
        "  -> debts      Who owes whom.",
        "  -> coming-up  Dates in the next days.",
        "  1             when is it",
        "  3             grace's birthday",
        "## a person: 1",
        "  -> people     Everyone your files name.",
        "  2             who is it",
        "## a thing you wrote down: 2",
        "  -> invoices   Invoices you sent.",
        f"  -> ask        {ASK}",
        "  4             the recipe",
        "  5             the shed key",
    ]


def test_questions_with_a_run_show_the_file_beside_each_step(tmp_path, kinds, cards):
    run = a_run(tmp_path, "03-debts.txt", "04-glance.txt")
    f = asked(tmp_path, "who owes me\nthe shed key\n")
    out = go("--questions", f, "--kinds", kinds, "--run", run)[1]
    assert out.splitlines()[1:] == [
        "## money owed: 1",
        f"  -> debts     Who owes whom.   {run / '03-debts.txt'}",
        "  -> invoices  Invoices you sent.",
        "  1            who owes me",
        "## a thing you wrote down: 1",
        f"  -> ask       {ASK}   {run / '04-glance.txt'}",
        "  2            the shed key",
    ]


def test_questions_naming_a_step_that_is_not_here_exit_42(tmp_path, cards):
    f = tmp_path / "kinds.txt"
    f.write_text("x: zebra -> no-such-thing\n")
    code, out, _ = go(
        "--questions", asked(tmp_path, "a zebra\nthe shed key\n"), "--kinds", f
    )
    assert code == 42
    assert out.splitlines()[2] == "  -> no-such-thing  not an add-on that is here"
    assert go("--questions", asked(tmp_path, "the shed key\n"), "--kinds", f)[0] == 0


def test_the_first_column_is_as_wide_as_its_longest_up_to_sixty(tmp_path, kinds):
    for n in (59, 60):
        name = "n" * n
        out = go(
            "--questions", asked(tmp_path, f"{name}\tthe shed key\n"), "--kinds", kinds
        )[1]
        assert out.splitlines()[2:] == [
            f"  {'-> ask':<{n}}  {ASK}",
            f"  {name}  the shed key",
        ]
    name = "n" * 61
    out = go(
        "--questions", asked(tmp_path, f"{name}\tthe shed key\n"), "--kinds", kinds
    )[1]
    assert out.splitlines()[2:] == [
        f"  {'-> ask':<60}  {ASK}",
        f"  {name}  the shed key",
    ]


# ── refused ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("question", ["", " ", "\t\n", "?", "...", "* *"])
def test_a_question_with_no_words_is_refused(question, kinds):
    code, out, err = go(question, "--kinds", kinds)
    assert code == 2 and out == ""
    assert err == "refused: a question with no words\n"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "\n\n",
        "# only a comment\n",
        "late\t\n",
        "who owes me\nlate\t  \n",
        "ok\n?!\n",
    ],
)
def test_a_questions_file_with_no_question_or_an_empty_one_is_refused(
    text, tmp_path, kinds
):
    code, out, err = go("--questions", asked(tmp_path, text), "--kinds", kinds)
    assert code == 2 and out == ""
    assert err == "refused: a question with no words\n"


def test_a_file_that_cant_be_read_is_refused(tmp_path, kinds):
    gone = tmp_path / "gone.txt"
    for argv in (
        ["who owes me", "--kinds", gone],
        ["--questions", gone, "--kinds", kinds],
        ["who owes me", "--kinds", tmp_path],  # a folder
        ["--questions", tmp_path, "--kinds", kinds],
    ):
        code, out, err = go(*argv)
        assert code == 2 and out == "", argv
        assert err.startswith("refused: a file could not be read: "), argv
    assert go("who owes me", "--kinds", gone)[2] == (
        "refused: a file could not be read: FileNotFoundError\n"
    )
    latin = tmp_path / "latin.txt"
    latin.write_bytes("où: clé -> ask\n".encode("latin-1"))
    assert go("who owes me", "--kinds", latin) == (
        2,
        "",
        "refused: a file could not be read: UnicodeDecodeError\n",
    )
    assert go("--questions", latin, "--kinds", kinds)[0] == 2


def test_a_bad_kinds_file_is_refused_before_any_question_is_read(tmp_path):
    f = tmp_path / "kinds.txt"
    f.write_text("no arrow here\n")
    err = go("--questions", asked(tmp_path, "who owes me\n"), "--kinds", f)[2]
    assert err.startswith("refused: the kinds file: line 1 ")


# ── what it never does ───────────────────────────────────────────────────────
def test_it_reads_and_never_writes(tmp_path, kinds, cards):
    run = a_run(tmp_path, "03-debts.txt", "04-glance.txt")
    q = asked(tmp_path)
    before = snapshot(tmp_path)
    for argv in (
        ["who owes me", "--kinds", kinds, "--run", run],
        ["--questions", q, "--kinds", kinds, "--run", run, "--json"],
        ["who owes me", "--kinds", kinds, "--run", tmp_path / "gone"],
    ):
        go(*argv)
    assert script("who owes me", "--kinds", kinds, "--run", run).returncode in (0, 42)
    assert snapshot(tmp_path) == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "adapters", "kinds.txt", "mine", "questions.txt",
    ]  # fmt: skip


def test_the_same_question_goes_the_same_way_every_time(kinds, cards):
    first = go("who still owes me money", "--kinds", kinds, "--json")
    assert all(
        go("who still owes me money", "--kinds", kinds, "--json") == first
        for _ in range(3)
    )


# ── the kinds file it ships with ─────────────────────────────────────────────
def shipped() -> list:
    return table((HERE / "kinds.txt").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "question, is_a, by",
    [
        ("who still owes me money", "money owed", "owe"),
        ("how much do I still owe dev", "money owed", "owe"),
        ("has the tenant paid me for october", "money owed", "paid me"),
        ("did ruth pay for the tickets", "money owed", "did * pay"),
        ("which invoices are overdue", "money owed", "overdue"),
        (
            "is there anything I'm about to forget before november",
            "what is coming",
            "about to forget",
        ),
        ("when does the passport expire", "what is coming", "expire"),
        ("what's coming up this month", "what is coming", "coming up"),
        ("ruth's phone number", "a person", "phone number"),
        ("who fixed the boiler", "a person", "who"),
        ("is it bad that dad's still driving", "a judgement", "is it bad"),
        ("should I renew the gym", "a judgement", "should i"),
        ("is it bad that I owe ruth money", "a judgement", "is it bad"),
        ("how much did I make in 2025", "money spent or made", "how much"),
        ("what did I spend on the roof", "money spent or made", "spend"),
        ("when's grace's birthday", "a date", "when's"),
        ("when is the dentist", "a date", "when is"),
        ("what's left to do before the talk", "where it stands", "left to do"),
        ("did I ever send the form back", "where it stands", "did i ever"),
        ("mom's goulash recipe", "a thing you wrote down", ""),
        (
            "the papers from when corinne and I split the house",
            "a thing you wrote down",
            "",
        ),
        ("the wifi password", "a thing you wrote down", ""),
    ],
)
def test_the_shipped_kinds_send_a_real_question_to_its_kind(question, is_a, by):
    got, steps, cue = route.kind_of(question, shipped())
    assert (got, cue) == (is_a, by)
    assert (
        steps
        == {
            "a judgement": ["ask"],
            "money owed": ["debts", "invoices"],
            "what is coming": ["coming-up", "renewals", "digest"],
            "where it stands": ["todo", "digest"],
            "money spent or made": ["amounts", "invoices", "subscriptions"],
            "a date": ["coming-up", "ask"],
            "a person": ["people", "ask"],
            "a thing you wrote down": ["ask"],
        }[is_a]
    )


def test_the_bare_word_when_is_not_a_date():
    """ "the papers from when corinne and I split the house" asks for papers."""
    assert all(cue != ["when"] for _, cues, _ in shipped() for cue in cues)
    assert route.kind_of("from when we split the house", shipped())[0] == route.PLAIN


def test_the_shipped_kinds_are_the_narrower_first_and_none_twice():
    names = [k for k, _, _ in shipped()]
    assert names == [
        "a judgement", "money owed", "what is coming", "where it stands",
        "money spent or made", "a date", "a person",
    ]  # fmt: skip
    assert route.PLAIN not in names


def test_the_kinds_file_beside_the_script_is_the_one_read_without_kinds():
    code, out, _ = go("who still owes me money", "--json")
    doc = json.loads(out)
    assert doc["said"] == (
        '"who still owes me money": money owed (by "owe"); that is the job of debts and invoices'
    )
    assert [r["where"] for r in doc["groups"][0]["rows"]] == ["debts", "invoices"]
    assert code == (0 if WHOLE else 42)


def test_every_step_the_shipped_kinds_name_is_the_ask_or_an_add_on_here():
    """A renamed add-on is caught here. Copied out beside the kernel alone,
    none of them is there, and each is said not to be."""
    steps = sorted({s for _, _, steps in shipped() for s in steps} - {"ask"})
    assert len(steps) == 9
    adapters = HERE.parents[1]
    here = [s for s in steps
            if any((adapters / b / s / "README.md").is_file() for b in ("stdlib", "deps"))]  # fmt: skip
    assert here == (steps if WHOLE else [])
    for s in steps:
        line = route.line_of(s)
        assert (line is not None and len(line) > 10) if WHOLE else line is None, s
