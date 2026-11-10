"""glance: each question a scan was asked is one line, under what its best
passage holds of it (nothing, part, the whole), the thinnest first, as a
report (and --json the same); what isn't scan's is refused, and it writes
nothing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAN = HERE.parent / "scan" / "scan.py"


def run(*argv: object) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "glance.py"), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def answer(name: str, *served: tuple[str, str]) -> str:
    """One line as scan prints it: a question's name and the passages served."""
    return json.dumps({
        "index": "index", "question": name, "state": "populated" if served else "empty",
        "served": [{"rank": n, "where": where, "id": "0" * 64, "echo": False, "text": text}
                   for n, (where, text) in enumerate(served, 1)],
    })  # fmt: skip


def glance(tmp_path: Path, scanned: list[str], questions: list[str], *more: object):
    """glance over these lines of scan's and these lines of a questions file."""
    (tmp_path / "scanned.jsonl").write_text("".join(x + "\n" for x in scanned))
    (tmp_path / "questions.txt").write_text("".join(x + "\n" for x in questions))
    return run("--of", tmp_path / "scanned.jsonl", "--questions",
               tmp_path / "questions.txt", *more)  # fmt: skip


def rows(got: subprocess.CompletedProcess) -> list[str]:
    """The report's lines below its first."""
    return got.stdout.splitlines()[1:]


SUN = "sun\thow much sun do tomatoes want"
PAUSE = "pause\thow do I pause a task"
HISTORY = "history\topen the session history"
THREE = [
    answer("sun", ("notes/garden/veg.md:1", "Tomatoes want six hours of sun.")),
    answer("pause"),
    answer("history", ("plans/redesign.md:601", "You are Jeles, conducting an oral history")),
]  # fmt: skip


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = subprocess.run(
        [sys.executable, str(HERE / "glance.py")], capture_output=True, text=True
    )
    assert got.returncode == 2 and "glance.py" in got.stderr


def test_each_question_is_one_line_under_what_its_best_passage_holds(tmp_path):
    got = glance(tmp_path, THREE, [SUN, PAUSE, HISTORY])
    assert got.returncode == 42 and got.stderr == ""
    assert got.stdout == (
        "glance: populated, 3 questions: 1 held whole, 1 in part, 1 found nothing\n"
        "## found nothing\n"
        "  pause    how do I pause a task\n"
        "## held in part\n"
        "  history  1 of 3, lacks open, session: plans/redesign.md:601"
        "  You are Jeles, conducting an oral history\n"
        "## held whole\n"
        "  sun      garden/veg.md:1  Tomatoes want six hours of sun.\n"
    )


def test_json_is_the_same_report_as_one_object(tmp_path):
    got = glance(tmp_path, THREE, [SUN, PAUSE, HISTORY], "--json")
    assert got.returncode == 42 and got.stderr == ""
    assert got.stdout.count("\n") == 1
    assert json.loads(got.stdout) == {
        "addon": "glance",
        "state": "populated",
        "said": "3 questions: 1 held whole, 1 in part, 1 found nothing",
        "groups": [
            {"name": "found nothing",
             "rows": [{"where": "pause", "what": "how do I pause a task"}]},
            {"name": "held in part",
             "rows": [{"where": "history", "what": "1 of 3, lacks open, session: "
                       "plans/redesign.md:601  You are Jeles, conducting an oral history"}]},
            {"name": "held whole",
             "rows": [{"where": "sun",
                       "what": "garden/veg.md:1  Tomatoes want six hours of sun."}]},
        ],
    }  # fmt: skip
    # wherever --json is put, and with every question served it is 0 as the text is
    first = run("--json", "--of", tmp_path / "scanned.jsonl", "--questions",
                tmp_path / "questions.txt")  # fmt: skip
    assert first.returncode == 42 and first.stdout == got.stdout
    assert glance(tmp_path, THREE[:1], [SUN], "--json").returncode == 0


def test_every_question_served_is_exit_0_and_a_group_with_no_rows_isnt_printed(
    tmp_path,
):
    got = glance(tmp_path, THREE[:1], [SUN])
    assert got.returncode == 0
    assert got.stdout == (
        "glance: populated, 1 question: 1 held whole, 0 in part, 0 found nothing\n"
        "## held whole\n"
        "  sun  garden/veg.md:1  Tomatoes want six hours of sun.\n"
    )
    assert [g["name"] for g in json.loads(
        glance(tmp_path, THREE[:1], [SUN], "--json").stdout)["groups"]] == ["held whole"]  # fmt: skip


def test_a_question_held_only_in_part_is_served_and_doesnt_wait_on_you(tmp_path):
    got = glance(tmp_path, THREE[2:], [HISTORY])
    assert got.returncode == 0
    assert got.stdout.splitlines()[:2] == [
        "glance: populated, 1 question: 0 held whole, 1 in part, 0 found nothing",
        "## held in part",
    ]


def test_one_question_that_found_nothing_is_exit_42(tmp_path):
    got = glance(tmp_path, THREE[1:2], [PAUSE])
    assert got.returncode == 42
    assert got.stdout == (
        "glance: populated, 1 question: 0 held whole, 0 in part, 1 found nothing\n"
        "## found nothing\n"
        "  pause  how do I pause a task\n"
    )


def test_held_in_part_is_thinnest_first_not_as_asked_or_by_name(tmp_path):
    got = glance(
        tmp_path,
        [
            answer("a-two", ("paint.md:1", "red and green")),
            answer("c-one", ("paint.md:2", "only red")),
            answer("b-half", ("paint.md:3", "only red")),
        ],
        ["a-two\tred green blue", "c-one\tred green blue", "b-half\tred green"],
    )
    assert got.returncode == 0
    assert rows(got) == [
        "## held in part",
        "  c-one   1 of 3, lacks green, blue: paint.md:2  only red",
        "  b-half  1 of 2, lacks green: paint.md:3  only red",
        "  a-two   2 of 3, lacks blue: paint.md:1  red and green",
    ]


def test_the_lacking_words_are_said_in_the_order_they_were_asked(tmp_path):
    got = glance(
        tmp_path, [answer("q", ("zoo.md:1", "A yak."))], ["q\tzebra yak aardvark"]
    )
    assert rows(got)[1] == "  q  1 of 3, lacks zebra, aardvark: zoo.md:1  A yak."


def test_only_the_best_passage_is_looked_at_not_the_ones_below_it(tmp_path):
    served = [("paint.md:2", "only red"), ("paint.md:9", "red green blue")]
    got = glance(tmp_path, [answer("q", *served)], ["q\tred green blue"])
    assert rows(got) == [
        "## held in part",
        "  q  1 of 3, lacks green, blue: paint.md:2  only red",
    ]


def test_common_words_dont_count_and_a_word_asked_twice_counts_once(tmp_path):
    got = glance(
        tmp_path,
        [answer("pause", ("run.md:4", "Pause it.")), answer("twice", ("sky.md:1", "The sun."))],
        [PAUSE, "twice\tsun sun moon"],
    )  # fmt: skip
    assert rows(got) == [
        "## held in part",
        "  pause  1 of 2, lacks task: run.md:4  Pause it.",
        "  twice  1 of 2, lacks moon: sky.md:1  The sun.",
    ]


def test_a_word_is_held_in_another_form_as_the_kernel_holds_it(tmp_path):
    got = glance(tmp_path, [answer("q", ("money.md:1", "Dev owes me forty."))],
                 ["q\twho is owing forty"])  # fmt: skip
    assert rows(got) == ["## held whole", "  q  money.md:1  Dev owes me forty."]


def test_a_word_the_passages_path_holds_is_not_lacking(tmp_path):
    got = glance(
        tmp_path,
        [answer("in", ("dad/log.md:3", "The care visit.")),
         answer("out", ("mum/log.md:3", "The care visit."))],
        ["in\tdad care", "out\tdad care"],
    )  # fmt: skip
    assert rows(got) == [
        "## held in part",
        "  out  1 of 2, lacks dad: mum/log.md:3  The care visit.",
        "## held whole",
        "  in   dad/log.md:3  The care visit.",
    ]


def test_a_words_list_keeps_a_word_it_reads_another_way_from_lacking(tmp_path):
    scanned = [answer("bills", ("money.md:2", "The bills are overdue."))]
    got = glance(tmp_path, scanned, ["bills\tbills due"])
    assert got.stdout == (
        "glance: populated, 1 question: 0 held whole, 1 in part, 0 found nothing\n"
        "## held in part\n"
        "  bills  1 of 2, lacks due: money.md:2  The bills are overdue.\n"
    )
    (tmp_path / "words.txt").write_text("# mine\n\ndue = next, overdue\n")
    got = glance(
        tmp_path, scanned, ["bills\tbills due"], "--words", tmp_path / "words.txt"
    )
    assert got.returncode == 0
    assert got.stdout == (
        "glance: populated, 1 question: 1 held whole, 0 in part, 0 found nothing\n"
        "## held whole\n"
        "  bills  money.md:2  The bills are overdue.\n"
    )
    (tmp_path / "words.txt").write_text("rent = lease\n")  # a list that doesn't read it
    got = glance(
        tmp_path, scanned, ["bills\tbills due"], "--words", tmp_path / "words.txt"
    )
    assert rows(got)[0] == "## held in part"


def test_the_opening_is_the_passages_first_words_on_one_line(tmp_path):
    text = "First line\n\n  second\tline,\r\nthird."
    got = glance(tmp_path, [answer("q", ("a.md:1", text))], ["q\tfirst"])
    assert rows(got)[1] == "  q  a.md:1  First line second line, third."


def test_a_long_opening_is_cut_at_a_word_with_an_ellipsis(tmp_path):
    fits = "abcd " * 17 + "abcde"  # 90 characters: shown whole
    over = "abcd " * 17 + "abcdef"  # 91: cut before the word that doesn't fit
    assert len(fits) == 90 and len(over) == 91
    got = glance(
        tmp_path,
        [answer("fits", ("a.md:1", fits)), answer("over", ("a.md:2", over)),
         answer("more", ("a.md:3", over + " and a good deal more after it")),
         answer("one", ("a.md:4", "abcd" + "x" * 200))],
        ["fits\tabcd", "over\tabcd", "more\tabcd", "one\tabcd"],
    )  # fmt: skip
    cut = ("abcd " * 17).rstrip() + "…"
    assert rows(got) == [
        "## held in part",  # a run of letters too long to show holds no word of it
        f"  one   0 of 1, lacks abcd: a.md:4  abcd{'x' * 86}…",
        "## held whole",
        f"  fits  a.md:1  {fits}",
        f"  over  a.md:2  {cut}",
        f"  more  a.md:3  {cut}",
    ]


def test_a_place_is_its_last_two_path_parts_and_its_line(tmp_path):
    got = glance(
        tmp_path,
        [answer("deep", ("a/b/c/d.md:12", "sun")), answer("two", ("c/d.md:7", "sun")),
         answer("top", ("d.md:1", "sun")), answer("colon", ("a/b:c/d e.md:4", "sun"))],
        ["deep\tsun", "two\tsun", "top\tsun", "colon\tsun"],
    )  # fmt: skip
    assert rows(got) == [
        "## held whole",
        "  deep   c/d.md:12  sun",
        "  two    c/d.md:7  sun",
        "  top    d.md:1  sun",
        "  colon  b:c/d e.md:4  sun",
    ]


def test_the_names_column_is_as_wide_as_the_longest_name_up_to_60(tmp_path):
    long, longer = "n" * 60, "m" * 61
    got = glance(
        tmp_path,
        [answer("a", ("d.md:1", "sun")), answer(long, ("d.md:1", "sun"))],
        ["a\tsun", f"{long}\tsun"],
    )
    assert rows(got)[1:] == [f"  a{' ' * 59}  d.md:1  sun", f"  {long}  d.md:1  sun"]
    got = glance(
        tmp_path,
        [answer("a", ("d.md:1", "sun")), answer(longer, ("d.md:1", "sun"))],
        ["a\tsun", f"{longer}\tsun"],
    )
    assert rows(got)[1:] == [f"  a{' ' * 59}  d.md:1  sun", f"  {longer}  d.md:1  sun"]


def test_a_bare_question_is_named_by_its_line_and_blank_and_hash_lines_are_skipped(
    tmp_path,
):
    got = glance(
        tmp_path,
        [answer("1"), answer("4"), answer("6"), answer("named")],
        ["how do I pause a task", "# not a question", "", "where is the moon rocket",
         "  # nor this", "  the shed's colour  ", " named \t  what a name is  "],
    )  # fmt: skip
    assert got.returncode == 42
    assert rows(got) == [
        "## found nothing",
        "  1      how do I pause a task",
        "  4      where is the moon rocket",
        "  6      the shed's colour",
        "  named  what a name is",
    ]


def test_a_hash_line_is_no_question_even_when_scan_has_one_by_its_number(tmp_path):
    got = glance(tmp_path, [answer("2"), answer("3")], ["sun", "# moon", ""])
    assert rows(got) == [
        "## found nothing",
        "  2  (not in the questions file)",
        "  3  (not in the questions file)",
    ]


def test_a_question_scan_has_that_the_questions_file_lacks_is_still_shown(tmp_path):
    got = glance(tmp_path, [answer("gone"), *THREE[:1]], [SUN])
    assert got.returncode == 42
    assert rows(got)[:2] == ["## found nothing", "  gone  (not in the questions file)"]
    got = glance(tmp_path, [answer("gone", ("shed.md:1", "The shed is blue."))], [SUN])
    assert got.returncode == 0  # served: its words aren't known, its place is
    assert got.stdout.splitlines()[0].startswith("glance: populated, 1 question: ")
    assert rows(got)[1] == "  gone  shed.md:1  The shed is blue."


def test_every_indexs_answer_to_a_question_is_a_line_of_its_own(tmp_path):
    got = glance(tmp_path, [THREE[0], answer("sun")], [SUN])
    assert got.returncode == 42
    assert got.stdout == (
        "glance: populated, 2 questions: 1 held whole, 0 in part, 1 found nothing\n"
        "## found nothing\n"
        "  sun  how much sun do tomatoes want\n"
        "## held whole\n"
        "  sun  garden/veg.md:1  Tomatoes want six hours of sun.\n"
    )


def refused(got: subprocess.CompletedProcess, *said: str) -> bool:
    """Exit 2, nothing printed, and every one of `said` on stderr."""
    return (
        got.returncode == 2 and got.stdout == "" and all(s in got.stderr for s in said)
    )


def test_a_command_line_it_cant_read_is_refused_with_how_to_run_it(tmp_path):
    glance(tmp_path, THREE, [SUN, PAUSE, HISTORY])
    of, qs = (
        ["--of", tmp_path / "scanned.jsonl"],
        ["--questions", tmp_path / "questions.txt"],
    )
    usage = "usage: glance.py --of SCANNED --questions FILE [--words FILE] [--json]"
    assert run(*of, *qs).returncode == 42, "the command that works"
    for argv in (
        of,  # no questions
        qs,  # no scan
        [*of, *qs, "--stray"],
        [*of, *qs, "stray"],
        [*of, "--questions"],  # a name with nothing after it
        [*qs, "--of"],
        [*of, *qs, "--words"],
        [*of, *qs, "--words", ""],
        ["--of", "", *qs],
        [*of, "--questions", ""],
        ["--json"],
    ):
        got = run(*argv)
        assert refused(got, usage) and got.stderr.count("\n") == 1, argv


def test_a_file_that_cant_be_read_is_refused(tmp_path):
    glance(tmp_path, THREE, [SUN, PAUSE, HISTORY])
    (tmp_path / "words.txt").write_text("due = overdue\n")
    (tmp_path / "bytes.txt").write_bytes(b"sun\twhat \xff\xfe is this\n")
    good = {"--of": tmp_path / "scanned.jsonl", "--questions": tmp_path / "questions.txt",
            "--words": tmp_path / "words.txt"}  # fmt: skip
    assert run(*[x for kv in good.items() for x in kv]).returncode == 42
    for name in good:
        # one that isn't there, a folder, and bytes that aren't text
        for bad in (tmp_path / "missing.txt", tmp_path, tmp_path / "bytes.txt"):
            got = run(*[x for kv in {**good, name: bad}.items() for x in kv])
            assert refused(got, "refused: a file could not be read"), (name, bad)
            assert "Traceback" not in got.stderr


def test_lines_that_arent_scans_are_refused_and_the_line_is_named(tmp_path):
    good = THREE[0]
    for bad in (
        "not json at all",
        '{"question": "sun", "state": "populated"}',  # nothing served
        '{"state": "empty", "served": []}',
        '{"question": "sun", "served": []}',
        '{"question": "sun", "state": "populated", "served": null}',
        '{"question": "sun", "state": "populated", "served": 3}',
        '{"question": "sun", "state": "populated", "served": "a passage"}',
        '{"question": "sun", "state": "populated", "served": ["a passage"]}',
        '{"question": "sun", "state": "populated", "served": {"where": "a.md:1"}}',
        '{"question": "sun", "state": "populated", "served": [{"where": "a.md:1"}]}',
        '{"question": "sun", "state": "populated", "served": [{"text": "sun"}]}',
        '{"question": "sun", "state": "populated", "served": [{"where": 1, "text": "sun"}]}',
        '{"question": "sun", "state": "populated", "served": [{"where": "a.md:1", "text": 5}]}',
        '["question", "state", "served"]',
        '"question state served"',
        "42",
        "null",
    ):
        got = glance(tmp_path, [good, bad], [SUN])
        assert refused(got, f"refused: {tmp_path / 'scanned.jsonl'} can't be taken: line 2 has"
                       " no question, state and served, as scan's lines do"), bad  # fmt: skip
        assert "Traceback" not in got.stderr
    # the line is the file's own, blank ones counted
    got = glance(tmp_path, [good, "", "  ", "nope"], [SUN])
    assert refused(got, "line 4 has no question")
    assert refused(glance(tmp_path, ["nope", good], [SUN]), "line 1 has no question")


def test_blank_lines_between_scans_lines_are_passed_over(tmp_path):
    got = glance(tmp_path, ["", THREE[0], "   ", THREE[1], ""], [SUN, PAUSE])
    assert got.returncode == 42
    assert got.stdout.startswith(
        "glance: populated, 2 questions: 1 held whole, 0 in part, 1 found"
    )


def test_an_empty_scan_is_refused_not_reported_as_nothing_to_see(tmp_path):
    for nothing in ([], ["", "   "]):
        got = glance(tmp_path, nothing, [SUN])
        assert refused(got, f"refused: {tmp_path / 'scanned.jsonl'} can't be taken: it is"
                       " empty: the step before said nothing to hand on")  # fmt: skip


def test_a_words_list_that_doesnt_parse_is_refused_with_its_line(tmp_path):
    (tmp_path / "words.txt").write_text("due = overdue\ntwo words = one\n")
    got = glance(tmp_path, THREE[:1], [SUN], "--words", tmp_path / "words.txt")
    assert refused(got, "refused: words list line 2: one word = one or more words")


def test_it_reads_and_never_writes(tmp_path):
    (tmp_path / "words.txt").write_text("due = overdue\n")
    glance(tmp_path, THREE, [SUN, PAUSE, HISTORY])
    before = {
        p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()
    }
    for more in ([], ["--json"], ["--words", tmp_path / "words.txt"]):
        got = run("--of", tmp_path / "scanned.jsonl", "--questions",
                  tmp_path / "questions.txt", *more)  # fmt: skip
        assert got.returncode == 42
    assert {
        p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()
    } == before


def test_the_same_scan_gives_the_same_report_twice(tmp_path):
    first = glance(tmp_path, THREE, [SUN, PAUSE, HISTORY])
    assert glance(tmp_path, THREE, [SUN, PAUSE, HISTORY]).stdout == first.stdout


def scan(*argv: object) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCAN), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def test_it_reads_what_scan_really_prints(tmp_path):
    """scan's own lines over a folder, not ones written here by hand: the two
    stay in step, with a words list given to both and without one."""
    pile = tmp_path / "pile"
    (pile / "notes" / "garden").mkdir(parents=True)
    (pile / "notes" / "garden" / "veg.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater the beans at the root.\n"
    )
    (pile / "shed.md").write_text("The shed is blue.\n")
    questions = tmp_path / "questions.txt"
    questions.write_text(
        "sun\thow much sun do tomatoes want\n"
        "# the next is named by its line, 3\n"
        "where is the moon rocket\n"
        "\n"
        "shed\twhat colour is the shed\n"
    )
    assert scan("index", "--from", pile, "--to", tmp_path / "index").returncode == 0
    asked = scan("scan", "--index", tmp_path / "index", "--questions", questions)
    assert asked.returncode == 0
    served = {
        r["question"]: bool(r["served"])
        for r in map(json.loads, asked.stdout.splitlines())
    }
    assert served == {"sun": True, "3": False, "shed": True}
    (tmp_path / "scanned.jsonl").write_text(asked.stdout)
    got = run("--of", tmp_path / "scanned.jsonl", "--questions", questions)
    assert got.returncode == 42 and got.stderr == ""
    assert got.stdout == (
        "glance: populated, 3 questions: 1 held whole, 1 in part, 1 found nothing\n"
        "## found nothing\n"
        "  3     where is the moon rocket\n"
        "## held in part\n"
        "  shed  1 of 2, lacks colour: shed.md:1  The shed is blue.\n"
        "## held whole\n"
        "  sun   garden/veg.md:1  Tomatoes want six hours of sun.\n"
    )
    words = tmp_path / "words.txt"
    words.write_text("colour = blue\nrocket = beans\n")
    asked = scan("scan", "--index", tmp_path / "index", "--questions", questions,
                 "--words", words)  # fmt: skip
    assert asked.returncode == 0
    (tmp_path / "scanned.jsonl").write_text(asked.stdout)
    got = run(
        "--of", tmp_path / "scanned.jsonl", "--questions", questions, "--words", words
    )
    assert got.returncode == 0 and got.stderr == ""
    assert got.stdout == (
        "glance: populated, 3 questions: 2 held whole, 1 in part, 0 found nothing\n"
        "## held in part\n"
        "  3     1 of 2, lacks moon: garden/veg.md:3  Water the beans at the root.\n"
        "## held whole\n"
        "  sun   garden/veg.md:1  Tomatoes want six hours of sun.\n"
        "  shed  shed.md:1  The shed is blue.\n"
    )
