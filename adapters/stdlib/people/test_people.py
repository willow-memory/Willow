"""people: a name is known by what the files do with it — capitalized more
often than not, doing a person's thing at least once, no month or weekday —
and every mention of one, in any case, is counted and cited."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("people", HERE / "people.py")
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)
NOW = ["--now", "2026-10-23T00:00:00Z"]


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


def pile_of(**files: str) -> list[dict]:
    return [{"path": name, "line": 1, "text": text} for name, text in files.items()]


def test_a_name_is_capitalized_more_often_than_not_and_does_a_persons_thing():
    pile = pile_of(a=(
        "Kati came by for the frames.\n"
        "Walked the loop. We walked again, walked far.\n"
        "Walked to the shed.\n"
        "saw kati at the market\n"
        "Kati said the hives look strong.\n"
    ))  # fmt: skip
    assert pp.persons(pile) == {"kati"}, (
        "Walked starts sentences, but walked outnumbers it; Kati stays capitalized"
    )


def test_speech_being_done_to_and_a_chats_speaker_all_count():
    assert pp.persons(pile_of(a="rang Priya about the quote\n")) == {"priya"}
    assert pp.persons(pile_of(a="[2026-01-02 09:00] Mags: the kettle's on\n")) == {
        "mags"
    }
    assert pp.persons(pile_of(a="Ferris left early.\n")) == {"ferris"}
    assert pp.persons(pile_of(a="A quiet morning on the water.\n")) == set()
    assert pp.persons(pile_of(a="Ballarat is lovely in spring.\n")) == set(), (
        "a town that does nothing is no one"
    )


def test_a_word_more_often_lowercase_is_no_one_even_acting():
    pile = pile_of(a="Rose came by with the ladder.\nthe rose bush\nrose early\n")
    assert pp.persons(pile) == set(), (
        "rose outnumbers Rose, so the files say it is a flower or a verb"
    )
    pile = pile_of(a="Rose came by.\nthe rose bush\n")
    assert pp.persons(pile) == {"rose"}, "a tie keeps the name"


def test_the_drill_down_lists_undated_mentions_last():
    pile = pile_of(**{
        "z.md": "Kati came by.\n",
        "a.md": "2026-01-02 met Kati\n",
    })  # fmt: skip
    found = pp.mentions(pile, pp.persons(pile))
    lines = pp.drill("kati", found["kati"])
    assert lines[0].startswith("2026-01-02") and lines[1].startswith("undated")


def test_months_weekdays_and_function_words_are_no_one():
    assert (
        pp.persons(pile_of(a="March came in like a lion. See you Monday.\n")) == set()
    )
    assert pp.persons(pile_of(a="Then came the rain.\n")) == set()


def test_every_mention_counts_in_any_case_and_is_dated(tmp_path):
    b = box(tmp_path, {
        "log.md": "2026-01-02 Kati came by.\nthanks kati!\n",
        "mail/2026-02-01.txt": "KATI'S invoice attached\n",
    })  # fmt: skip
    got = run(str(HERE / "people.py"), "--box", str(b))
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0] == "    3  Kati  in 2 files, 2026-01-02 to 2026-02-01"
    assert lines[1] == "1 people, by what the files do with a name"
    got = run(str(HERE / "people.py"), "--box", str(b), "KATI")
    lines = got.stdout.splitlines()
    assert lines[0].startswith("2026-01-02") and "log.md:1" in lines[0]
    assert lines[1].startswith("2026-01-02") and "log.md:2" in lines[1]
    assert lines[2].startswith("2026-02-01") and "mail/2026-02-01.txt:1" in lines[2]
    assert lines[3] == '3 mentions of "Kati" in 2 files'
    assert got.stdout == run(str(HERE / "people.py"), "--box", str(b), "kati").stdout


def test_the_roster_comes_most_mentioned_first_and_spans_skip_the_undated():
    pile = pile_of(**{
        "a.md": "Kati came.\nKati again, kati twice in a line counts once.\nkati.\n",
        "b.md": "2026-01-02 met Priya\n",
    })  # fmt: skip
    found = pp.mentions(pile, pp.persons(pile))
    lines = pp.roster(found)
    assert lines[0].startswith("    3  Kati ") and "to" not in lines[0], (
        "a mention is a line; no dated mention, no span"
    )
    assert (
        lines[1].startswith("    1  Priya") and "2026-01-02 to 2026-01-02" in lines[1]
    )


def test_nobody_found_and_nobody_by_that_name_escalate(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "people.py"), "--box", str(b))
    assert got.returncode == 42 and "No word of your folder" in got.stdout
    b2 = box(tmp_path / "b2", {"a.md": "Kati came by.\n"})
    got = run(str(HERE / "people.py"), "--box", str(b2), "gerry")
    assert got.returncode == 42 and 'answers to "gerry"' in got.stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "people.py"))
    assert got.returncode == 2 and "people.py" in got.stderr
    got = run(str(HERE / "people.py"), "--box", str(tmp_path / "b"), "a", "b")
    assert got.returncode == 2, "one person at a time"
    got = run(str(HERE / "people.py"), "--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
