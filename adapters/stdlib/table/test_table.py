"""table: one way to sit at any table on the record. The host's typed answer
is the only thing that seals or declines; a guest's one move waits; a word
that meets one the table holds is raised before the host decides; a yes can
be taken back and nothing is erased; a call set aside and a sitting paused
name no one; and a sitting ends on one seal, with the record checked."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "table.py"
DAY = "2026-11-21"
SAY = "say "  # what the host types to keep something: a bare line is a bite
NOW = ["--now", DAY + "T09:00:00Z"]
#: the heads-up is the contradictions add-on's rule; the end, session-seal's
needs_rule = pytest.mark.skipif(
    not (HERE.parent / "contradictions").is_dir(), reason="no contradictions add-on"
)
needs_end = pytest.mark.skipif(
    not (HERE.parent / "session-seal").is_dir(), reason="no session-seal add-on"
)
MARCH = "The landlord agreed the move-out date is the last day of March."
APRIL = "The landlord agreed the move-out date is the middle of April."
DEPOSIT = "The deposit comes back within thirty days of moving out."


def run(*argv: str, typed: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], input=typed,
                          stdin=None if typed is not None else subprocess.DEVNULL,
                          capture_output=True, text=True)  # fmt: skip


def a_box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "lease.md").write_text("The lease runs to the end of March.\n")
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "key"), *NOW], check=True, capture_output=True)  # fmt: skip
    return box


def sit(box: Path, *typed: str, when: str = NOW[1], more: tuple = ()) -> subprocess.CompletedProcess:  # fmt: skip
    """The host sits down and types these lines, then is gone."""
    return run("--box", str(box), "--now", when, *more, typed="".join(t + "\n" for t in typed))  # fmt: skip


def rows(box: Path) -> list[dict]:
    return [json.loads(ln) for ln in (box / "record.jsonl").read_text().splitlines()]


def kinds(box: Path) -> list[str]:
    return [r["kind"] for r in rows(box)]


def stands(box: Path) -> list[dict]:
    got = run("--box", str(box), "stands", "--json")
    assert got.returncode in (0, 42), got.stderr
    return json.loads(got.stdout)


def holds(box: Path) -> bool:
    return subprocess.run([sys.executable, str(KERNEL), "verify", "--box", str(box)],
                          capture_output=True).returncode == 0  # fmt: skip


# ── the guest's seat: one move, and it waits ─────────────────────────────────
def test_what_a_guest_brings_in_waits_and_seals_nothing(tmp_path):
    box = a_box(tmp_path)
    got = run("--box", str(box), "bring", "--as", "the landlord", DEPOSIT, *NOW)
    assert got.returncode == 42 and got.stdout.startswith("waiting on the host's call: proposal:")  # fmt: skip
    assert "seal" not in kinds(box) and kinds(box).count("table-said") == 1
    assert stands(box) == []
    said = [r for r in rows(box) if r["kind"] == "table-said"][0]
    assert (said["by"], said["fact"]) == ("the landlord", DEPOSIT)
    # the same words by the same name that day are the one suggestion, not two
    again = run("--box", str(box), "bring", "--as", "the landlord", DEPOSIT, *NOW)
    assert again.returncode == 42 and kinds(box).count("table-said") == 1
    assert run("--box", str(box), "stands").returncode == 42


def test_no_guest_brings_in_the_hosts_own_word_or_nothing(tmp_path):
    box = a_box(tmp_path)
    before = rows(box)
    for argv in (["--as", "host", DEPOSIT], ["--as", "HOST", DEPOSIT], ["--as", "x" * 41, DEPOSIT],
                 ["--as", "a clerk", "  "], ["--as", "a clerk", "w" * 501]):  # fmt: skip
        got = run("--box", str(box), "bring", *argv, *NOW)
        assert got.returncode == 2 and got.stderr.startswith("refused: "), argv
    assert rows(box) == before


# ── the host's seat: the typed answer, and only it ───────────────────────────
def test_the_hosts_typed_yes_seals_and_their_no_declines(tmp_path):
    box = a_box(tmp_path)
    run("--box", str(box), "bring", "--as", "the landlord", DEPOSIT, *NOW)
    run(
        "--box",
        str(box),
        "bring",
        "--as",
        "the agent",
        "The carpet was worn before.",
        *NOW,
    )
    got = sit(box, "c", "y", "n")
    assert (
        "Your call. the landlord says:" in got.stdout and "It's true now." in got.stdout
    )
    assert (
        "Your call. the agent says:" in got.stdout and "It didn't happen." in got.stdout
    )
    assert [(t["by"], t["fact"], t["day"]) for t in stands(box)] == [("the landlord", DEPOSIT, DAY)]  # fmt: skip
    assert kinds(box).count("seal") == 1 and kinds(box).count("decline") == 1
    assert holds(box)
    # answered: neither is asked again
    again = sit(box, "c").stdout
    assert (
        "Your call." not in again
        and "Nothing has been left for you to look at." in again
    )


def test_what_the_host_refused_is_not_offered_to_them_again(tmp_path):
    """CONST-V-11, offered once: the same words by the same name wait once,
    on whatever day they come again; a no is not brought back by a guest; a
    yes that stands needs no asking; one taken back may be said anew."""
    box = a_box(tmp_path)
    worn = "The carpet was worn before."
    later = ("--now", "2026-11-25T09:00:00Z")

    def brought(by: str, fact: str):
        return run("--box", str(box), "bring", "--as", by, fact, *later)

    run("--box", str(box), "bring", "--as", "the agent", worn, *NOW)
    again = brought("the agent", worn)  # still waiting, days later: the one call
    assert again.returncode == 42 and kinds(box).count("table-said") == 1
    sit(box, "c", "n", SAY + DEPOSIT, "y")
    kept = rows(box)
    no = brought("the agent", worn)
    assert (no.returncode, no.stdout) == (0, f"the host said no to this on {DAY}: it is not offered again\n")  # fmt: skip
    assert rows(box) == kept and "Your call." not in sit(box, "c").stdout
    # another name's same words are another's to bring; the host's yes that stands isn't asked
    assert brought("the landlord", worn).returncode == 42
    run("--box", str(box), "bring", "--as", "the agent", DEPOSIT, *NOW)
    sit(box, "c", "n", "y")  # the landlord's carpet: no; the agent's deposit: yes
    held = brought("the agent", DEPOSIT)
    assert (held.returncode, held.stdout) == (0, f"this table has held this true since {DAY}\n")  # fmt: skip
    # the host brings a no back themselves, at the table; and a yes taken back may be said anew
    assert "It's true now." in sit(box, "o", "the agent", worn, "y").stdout
    sit(box, "u", "y")
    assert brought("the agent", worn).returncode == 42


def test_a_host_who_leaves_a_call_leaves_it_waiting_and_is_asked_again(tmp_path):
    box = a_box(tmp_path)
    run("--box", str(box), "bring", "--as", "the landlord", DEPOSIT, *NOW)
    for typed in (
        ("c",),
        ("c", "maybe"),
        ("c", ""),
    ):  # gone, a word that is no answer, Enter
        got = sit(box, *typed)
        assert got.returncode == 42 and "Your call. the landlord says:" in got.stdout
        assert "seal" not in kinds(box) and "decline" not in kinds(box)
    assert "Type y for yes, or n for no." in sit(box, "c", "maybe").stdout
    assert sit(box, "c", "y").returncode == 42 and stands(box)[0]["fact"] == DEPOSIT


def test_nothing_answers_for_the_host(tmp_path):
    box = a_box(tmp_path)
    run("--box", str(box), "bring", "--as", "the landlord", DEPOSIT, *NOW)
    for extra in (["--yes"], ["-y"], ["--answer", "y"], ["--seal"], ["y"], ["bring", "--yes", "x"]):  # fmt: skip
        got = run("--box", str(box), *extra, typed="")
        assert got.returncode == 2 and "table.py --box DIR" in got.stderr, extra
    assert "seal" not in kinds(box)


def test_the_hosts_own_word_is_kept_on_their_yes_and_not_on_their_no(tmp_path):
    box = a_box(tmp_path)
    got = sit(box, SAY + MARCH, "y", SAY + "The oven was left clean.", "n")
    assert got.returncode == 42, "they left without ending the sitting"
    assert [(t["by"], t["fact"]) for t in stands(box)] == [("host", MARCH)]
    assert "Not kept." in got.stdout and kinds(box).count("table-said") == 1
    # a word no one said yes to was never handed in at all
    assert "The oven" not in (box / "record.jsonl").read_text()
    long = sit(box, SAY + "w" * 501)
    assert "longer than one passage (500 characters)" in long.stdout
    assert len(stands(box)) == 1


def test_someone_brings_something_in_at_the_table_and_the_host_is_asked_first(tmp_path):
    box = a_box(tmp_path)
    before = rows(box)
    assert sit(box, "o", "the agent", DEPOSIT).returncode == 42  # gone at the call
    assert rows(box) == before, "leaving midway leaves nothing half done"
    sit(
        box,
        "o",
        "the agent",
        DEPOSIT,
        "y",
        "o",
        "host",
        "The keys go in the lockbox.",
        "n",
    )
    said = [(r["by"], r["fact"]) for r in rows(box) if r["kind"] == "table-said"]
    assert said == [("the agent", DEPOSIT), ("a guest", "The keys go in the lockbox.")]
    assert [t["by"] for t in stands(box)] == ["the agent"]
    assert kinds(box).count("decline") == 1, "a no to what was brought in is kept"
    kept = rows(box)
    assert sit(box, "o", "").returncode == 42 and rows(box) == kept, "no one, nothing"


# ── the heads-up: before the host decides ────────────────────────────────────
@needs_rule
def test_mine_stands_now_replaces_the_old_word_and_erases_nothing(tmp_path):
    box = a_box(tmp_path)
    got = sit(box, SAY + MARCH, "y", SAY + APRIL, "1")
    assert "Before you decide:" in got.stdout and MARCH in got.stdout.split("Before you decide:")[1]  # fmt: skip
    assert "It's true now, and the old one is replaced." in got.stdout
    assert [t["fact"] for t in stands(box)] == [APRIL]
    # the old yes is still on the record, its seal still holding
    assert kinds(box).count("seal") == 3 and kinds(box).count("table-replaces") == 1
    assert MARCH in (box / "record.jsonl").read_text() and holds(box)


@needs_rule
def test_keep_the_old_one_keeps_nothing_new_and_declines_what_was_brought(tmp_path):
    box = a_box(tmp_path)
    sit(box, SAY + MARCH, "y", SAY + APRIL, "2")
    assert [t["fact"] for t in stands(box)] == [MARCH]
    assert APRIL not in (box / "record.jsonl").read_text()
    run("--box", str(box), "bring", "--as", "the agent", APRIL, *NOW)
    got = sit(box, "c", "2")
    assert "The old one stands." in got.stdout and kinds(box).count("decline") == 1
    assert [t["fact"] for t in stands(box)] == [MARCH]


@needs_rule
def test_both_are_true_is_a_row_and_the_pair_is_not_raised_again(tmp_path):
    box = a_box(tmp_path)
    sit(box, SAY + MARCH, "y", SAY + APRIL, "3")
    assert [t["fact"] for t in stands(box)] == [MARCH, APRIL]
    assert (
        kinds(box).count("table-both") == 1 and kinds(box).count("table-replaces") == 0
    )
    third = "The landlord agreed the move-out date is flexible."
    got = sit(box, SAY + third, "9", "0", "3")  # only 1 to 4 is an answer
    assert got.stdout.count("1 to 4.") == 2
    assert got.stdout.count("Before you decide:") == 1
    assert len(stands(box)) == 3 and kinds(box).count("table-both") == 3


@needs_rule
def test_let_me_reword_it_asks_again_and_keeps_only_the_new_wording(tmp_path):
    box = a_box(tmp_path)
    got = sit(
        box, SAY + MARCH, "y", SAY + APRIL, "4", "The stairs were swept on Friday.", "y"
    )
    assert "Say it again, your way:" in got.stdout
    assert [t["fact"] for t in stands(box)] == [
        MARCH,
        "The stairs were swept on Friday.",
    ]
    assert APRIL not in (box / "record.jsonl").read_text()
    # only the host's own word can be reworded: what a guest brought is theirs
    run("--box", str(box), "bring", "--as", "the agent", APRIL, *NOW)
    asked = sit(box, "c").stdout
    assert "Before you decide:" in asked and "4. Let me reword it" not in asked


@needs_rule
def test_the_same_words_again_are_not_a_clash(tmp_path):
    box = a_box(tmp_path)
    got = sit(box, SAY + MARCH, "y", SAY + MARCH, "y", when="2026-11-22T09:00:00Z")
    assert "Before you decide:" not in got.stdout


# ── a slip, a call set aside, a pause ────────────────────────────────────────
def test_a_yes_pressed_by_mistake_is_taken_back_and_stays_on_the_record(tmp_path):
    box = a_box(tmp_path)
    assert "Nothing has been made true this time to take back." in sit(box, "u").stdout
    got = sit(box, SAY + DEPOSIT, "y", "u", "n", "u", "y", "s")
    assert got.stdout.count("Take back") == 2 and "Taken back. It no longer stands." in got.stdout  # fmt: skip
    assert stands(box) == [] and DEPOSIT in (box / "record.jsonl").read_text()
    assert kinds(box).count("seal") == 2 and holds(box)
    slip = [r for r in rows(box) if r["kind"] == "table-replaces"][0]
    assert slip["new"] == "" and slip["fact"].startswith("nothing: ")


def test_a_call_set_aside_waits_and_names_no_one(tmp_path):
    box = a_box(tmp_path)
    run("--box", str(box), "bring", "--as", "the landlord", DEPOSIT, *NOW)
    got = sit(box, "c", "x")
    assert (
        "Skipped for now. Nothing is decided, and nobody needs to say why."
        in got.stdout
    )
    aside = [r for r in rows(box) if r["kind"] == "table-x"]
    # only that it was set aside, and that it was a call: no one, no reason, no words
    assert len(aside) == 1 and aside[0]["part"] == "call" and aside[0]["who"] == "table"
    assert not {"by", "fact", "subject", "why", "reason"} & set(aside[0])
    assert "landlord" not in json.dumps(aside[0]) and "deposit" not in json.dumps(
        aside[0]
    )
    assert "seal" not in kinds(box) and "decline" not in kinds(box)
    assert "Your call. the landlord says:" in sit(box, "c").stdout, "it is asked again"


def test_a_pause_stops_the_sitting_and_names_no_one(tmp_path):
    box = a_box(tmp_path)
    run("--box", str(box), "bring", "--as", "the landlord", DEPOSIT, *NOW)
    for typed in (("c", "p"), ("c", "y", "p"), (SAY + "A new word that waits.", "p")):
        got = sit(box, *typed)
        assert got.returncode == 42 and "Paused. Nobody needs to say why." in got.stdout
    paused = [r for r in rows(box) if r["kind"] == "table-pause"]
    assert len(paused) == 3 and all(r["who"] == "table" for r in paused)
    assert all("landlord" not in json.dumps(r) and "by" not in r for r in paused)
    assert "A new word that waits." not in (box / "record.jsonl").read_text()


# ── the end of a sitting ─────────────────────────────────────────────────────
@needs_end
def test_a_sitting_ends_on_one_seal_and_the_note_is_there_next_time(tmp_path):
    box = a_box(tmp_path)
    got = sit(box, SAY + DEPOSIT, "y", "", "Ask for the terms in writing.", "y")
    assert got.returncode == 0, got.stdout + got.stderr
    assert "This time, the table made true:\n  - " + DEPOSIT in got.stdout
    assert got.stdout.rstrip().endswith("Saved and checked: nothing can be changed after the fact.")  # fmt: skip
    assert (
        kinds(box).count("session") == 1
        and kinds(box).count("seal") == 2
        and holds(box)
    )
    nxt = sit(box, when="2026-11-28T09:00:00Z")
    assert "Previously, this table made true:\n  - " + DEPOSIT in nxt.stdout
    assert (
        "Just for you, from last time:\n  Ask for the terms in writing." in nxt.stdout
    )
    # a second sitting made nothing true, and says so; the older note has gone by the third
    end = sit(box, "", "", "y", when="2026-11-28T09:00:00Z")
    assert end.returncode == 0 and "This time, nothing new was made true." in end.stdout
    assert "Ask for the terms" not in sit(box, when="2026-12-05T09:00:00Z").stdout
    note = [r for r in rows(box) if r["kind"] == "table-note"]
    assert len(note) == 1 and "seal" not in note[0], (
        "a note is the host's words, never sealed"
    )


@needs_end
def test_a_sitting_not_ended_stays_open(tmp_path):
    box = a_box(tmp_path)
    for typed in (("",), ("", "a note"), ("", "", "n")):
        got = sit(box, *typed)
        assert got.returncode == 42 and "session" not in kinds(box)
    assert "Left open." in sit(box, "", "", "n").stdout


# ── the words, and the command line ──────────────────────────────────────────
def test_a_tables_words_are_its_own_and_change_nothing_kept(tmp_path):
    box = a_box(tmp_path)
    words = tmp_path / "game.txt"
    words.write_text("# a game night\ntitle: Die-Namic\ncall: Your call, GM.\n"
                     "is_right: Is that true in your world? (y/n)\n")  # fmt: skip
    run("--box", str(box), "bring", "--as", "Juno", DEPOSIT, *NOW)
    got = sit(box, "c", "y", more=("--words", str(words)))
    assert (
        got.stdout.startswith("Die-Namic\n")
        and "Your call, GM. Juno says:" in got.stdout
    )
    assert "Is that true in your world? (y/n) " in got.stdout
    assert stands(box)[0]["fact"] == DEPOSIT
    words.write_text("titel: a slip\n")
    bad = sit(box, more=("--words", str(words)))
    assert (
        bad.returncode == 2 and "'titel' is not one of the table's words" in bad.stderr
    )


def test_moves_says_each_seats_and_a_guest_has_one():
    got = run("moves")
    assert got.returncode == 0 and got.stdout.startswith("host:\n  say ")
    assert run("moves", "--seat", "guest").stdout.splitlines()[:2] == [
        "guest:", "  bring      hand something in, under a name: it waits on the host's call"]  # fmt: skip
    assert run("moves", "--seat", "king").returncode == 2


def test_a_bad_command_line_or_no_box_is_refused(tmp_path):
    box = a_box(tmp_path)
    for argv in ([], ["--box"], ["--box", str(box), "stands", "extra"], ["--box", str(box), "bring", "x"],
                 ["--box", str(box), "sit"], ["stands"], ["--box", str(box), "moves"],
                 ["--box", str(box), "--box", str(box)], ["--box", str(box), "stands", "--words", "w"]):  # fmt: skip
        got = run(*argv, typed="")
        assert got.returncode == 2 and "table.py --box DIR" in got.stderr, argv
    got = run("--box", str(tmp_path / "nowhere"), typed="")
    assert (
        got.returncode == 2 and got.stderr == "refused: not a kernel box; init first\n"
    )


def test_a_record_that_does_not_check_out_is_refused(tmp_path):
    box = a_box(tmp_path)
    sit(box, SAY + DEPOSIT, "y")
    record = box / "record.jsonl"
    record.write_text(record.read_text().replace("thirty", "ninety"))
    for argv in (["stands"], ["bring", "--as", "a clerk", "anything"], []):
        got = run("--box", str(box), *argv, typed="")
        assert got.returncode == 2 and "the record doesn't check out" in got.stderr, (
            argv
        )


# ── one table, several matters: a box made from several folders ──────────────
TRUCK = "The truck is booked for the school holiday week."
AWAY = "The girls are away with their mother for the school holiday week."
FORM = "The office wants the form back in December."
LEASE = "Nothing moves until the lease is signed."


def a_table_of_three(tmp_path: Path) -> Path:
    """One box drawn from three folders: move, work and girls."""
    froms = []
    for name, line in (("move", "The movers were asked."), ("work", "The form."), ("girls", "The recital.")):  # fmt: skip
        folder = tmp_path / name
        folder.mkdir()
        (folder / "notes.md").write_text(line + "\n")
        froms += ["--from", f"{name}={folder}"]
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), *froms,
                    "--key", str(tmp_path / "key"), *NOW], check=True, capture_output=True)  # fmt: skip
    return box


def test_a_guest_says_which_matter_and_only_one_the_table_has(tmp_path):
    box = a_table_of_three(tmp_path)
    got = run(
        "--box", str(box), "bring", "--as", "the mover", "--at", "move", TRUCK, *NOW
    )
    assert got.returncode == 42
    said = [r for r in rows(box) if r["kind"] == "table-said"]
    assert [(r["by"], r["matter"], r["fact"]) for r in said] == [
        ("the mover", "move", TRUCK)
    ]
    # the same words about another matter are another suggestion; about none, another
    assert run("--box", str(box), "bring", "--as", "the mover", "--at", "girls", TRUCK, *NOW).returncode == 42  # fmt: skip
    assert (
        run("--box", str(box), "bring", "--as", "the mover", TRUCK, *NOW).returncode
        == 42
    )
    said = [r for r in rows(box) if r["kind"] == "table-said"]
    assert [r.get("matter") for r in said] == ["move", "girls", None]
    assert len({r["subject"] for r in said}) == 3
    before = rows(box)
    bad = run(
        "--box", str(box), "bring", "--as", "the mover", "--at", "garden", TRUCK, *NOW
    )
    assert (bad.returncode, bad.stderr) == (2, "refused: --at garden: this table's matters are girls, move, work\n")  # fmt: skip
    assert run("--box", str(box), "stands", "--at", "garden").returncode == 2
    assert rows(box) == before


def test_a_table_over_one_folder_has_no_matters(tmp_path):
    box = a_box(tmp_path)
    bad = run(
        "--box", str(box), "bring", "--as", "a clerk", "--at", "move", DEPOSIT, *NOW
    )
    assert bad.returncode == 2 and "this table is over one folder" in bad.stderr
    got = sit(box, "m", SAY + DEPOSIT, "y")
    assert (
        "This table is over one folder: it has no matters to choose from." in got.stdout
    )
    assert "several matters" not in got.stdout
    assert [(t["matter"], t["fact"]) for t in stands(box)] == [("", DEPOSIT)]
    assert "matter" not in [r for r in rows(box) if r["kind"] == "table-said"][0]


@needs_rule
def test_one_sitting_is_over_every_matter_and_the_heads_up_looks_across_them(tmp_path):
    box = a_table_of_three(tmp_path)
    run("--box", str(box), "bring", "--as", "the mover", "--at", "move", TRUCK, *NOW)
    got = sit(box, "c", "y", "m", "9", "3", SAY + FORM, "y", "m", "girls", SAY + AWAY, "3", "m", "0", SAY + LEASE, "y", "s")  # fmt: skip
    out = got.stdout
    assert "Your call. the mover (about move) says:" in out
    assert (
        'This table has several matters (girls, move, work). Type "about" to say which one you mean.'
        in out
    )
    assert "   0 to 3." in out and "\nwork> " in out and "\ngirls> " in out
    # a word about the girls meets one about the move: raised, and said which matter
    assert out.count("Before you decide:") == 1
    assert "on 2026-11-21 (about move) this table made this true:\n   " + TRUCK in out
    assert [(t["matter"], t["by"], t["fact"]) for t in stands(box)] == [
        ("move", "the mover", TRUCK), ("work", "host", FORM), ("girls", "host", AWAY), ("", "host", LEASE),
    ]  # fmt: skip
    # read back a matter at a time: the table's own first, then A to Z
    read = out.split("\n> ")[-2]  # what s printed: after the prompt it was typed at
    order = [read.index(x) for x in ("the table itself", "girls\n", "move\n", "work\n")]
    assert order == sorted(order)
    one = run("--box", str(box), "stands", "--at", "girls")
    assert one.stdout == f"table: 1 thing this table holds true about girls\n  {DAY}  host      {AWAY}\n"  # fmt: skip
    assert run("--box", str(box), "stands", "--at", "work", "--json").returncode == 0
    whole = run("--box", str(box), "stands").stdout.splitlines()
    assert whole[0] == "table: 4 things this table holds true"
    assert [ln for ln in whole if not ln.startswith("  2026")][1:] == [
        "  the table itself", "  girls", "  move", "  work"]  # fmt: skip
    assert holds(box)


@needs_end
def test_a_table_of_several_matters_ends_on_one_seal_and_reads_back_by_matter(tmp_path):
    box = a_table_of_three(tmp_path)
    got = sit(
        box, "m", "move", SAY + TRUCK, "y", "m", "work", SAY + FORM, "y", "", "", "y"
    )
    assert got.returncode == 0, got.stdout + got.stderr
    assert f"This time, the table made true:\n  move\n    - {TRUCK}\n  work\n    - {FORM}\n" in got.stdout  # fmt: skip
    assert kinds(box).count("session") == 1, (
        "one sitting, one seal, whatever it was about"
    )
    nxt = sit(box, when="2026-11-28T09:00:00Z")
    assert f"Previously, this table made true:\n  move\n    - {TRUCK}\n  work\n    - {FORM}\n" in nxt.stdout  # fmt: skip
    assert holds(box)


# ── the host's attention is the host's ───────────────────────────────────────
THINGS = [
    "The first thing was agreed.",
    "A second matter was settled.",
    "Third, the keys were returned.",
    "Fourth, the oven was cleaned.",
    "Fifth, the meter was read.",
]


def brought(box: Path, by: str, fact: str) -> subprocess.CompletedProcess:
    return run("--box", str(box), "bring", "--as", by, fact, *NOW)


def test_nothing_is_asked_until_the_host_asks_and_then_two_at_a_time(tmp_path):
    box = a_box(tmp_path)
    for thing in THINGS[:3]:
        brought(box, "the agent", thing)
    got = sit(box)  # they sit down, and say nothing
    assert "Your call." not in got.stdout, (
        "what waits is counted, never put to them unasked"
    )
    assert (
        'the agent left 3 things here for you to look at. Type "look" to see the first two.'
        in got.stdout
    )
    assert "seal" not in kinds(box) and "decline" not in kinds(box)
    # asked for: two, then "more?", and a no leaves the third waiting
    got = sit(box, "c", "y", "n", "n")
    assert got.stdout.count("Your call.") == 2
    assert "1 more. Press Enter for the next two, or type n to stop here." in got.stdout
    assert (
        "1 of 3. Your call. the agent says:" in got.stdout
        and "2 of 3. Your call." in got.stdout
    )
    assert (
        'The rest will keep. Type "look" whenever you want the next two.' in got.stdout
    )
    assert [t["fact"] for t in stands(box)] == THINGS[:1]
    assert kinds(box).count("decline") == 1
    assert "The rest will keep." in got.stdout.split("stop here.")[1], (
        "one left, said once more"
    )
    # a yes to "more?" goes on to the next two
    brought(box, "the agent", THINGS[3])
    brought(box, "the agent", THINGS[4])
    got = sit(box, "c", "y", "y", "", "y")  # Enter brings the next two
    assert got.stdout.count("Your call.") == 3 and len(stands(box)) == 4
    assert "for you to look at" not in got.stdout.split("Your call.")[-1], (
        "none left to count"
    )
    assert "That was the last of them." in got.stdout
    assert "Nothing has been left for you to look at." in sit(box, "c").stdout


def test_guests_may_leave_five_things_waiting_and_a_sixth_is_refused(tmp_path):
    box = a_box(tmp_path)
    for thing in THINGS:
        got = brought(box, "the agent", thing)
        assert got.returncode == 42
    assert "5 waiting on them now, of 5 at most" in got.stdout
    before = rows(box)
    sixth = brought(box, "a clerk", "A sixth thing came up.")
    assert sixth.returncode == 2 and sixth.stdout == ""
    assert sixth.stderr.startswith("refused: 5 things already wait on the host, and 5 is the most")  # fmt: skip
    assert rows(box) == before, "refused before anything is handed in"
    # what already waits may be asked after: it is the one suggestion, not a sixth
    assert brought(box, "the agent", THINGS[0]).returncode == 42 and rows(box) == before
    # the host answers one, and there is room again
    sit(box, "c", "y")
    assert brought(box, "a clerk", "A sixth thing came up.").returncode == 42
    # what the host brings in at their own table is theirs, and is never counted against it
    got = sit(box, "o", "a neighbour", "The fence is shared.", "y")
    assert "It's true now." in got.stdout and len(stands(box)) == 2


# ── the front door: the host's tables, and picking one ───────────────────────
def a_home(tmp_path: Path) -> Path:
    """A folder of three boxes: two that have been brought a word, and one
    nobody has, which is no table yet."""
    home = tmp_path / "home"
    for name in ("book", "cv", "untouched"):
        (home / name).mkdir(parents=True)
        made = a_box(home / name)
        assert made == home / name / "box"
    brought(home / "book" / "box", "a reader", THINGS[0])
    brought(home / "book" / "box", "a reader", THINGS[1])
    brought(home / "cv" / "box", "a reader", THINGS[2])
    (home / "book" / "table-words.txt").write_text(
        "title: The Book\ncall: Your call, author.\n"
    )
    return home


def at_home(home: Path, *typed: str) -> subprocess.CompletedProcess:
    return run("--home", str(home), *NOW, typed="".join(t + "\n" for t in typed))


def test_the_front_door_lists_the_tables_and_what_waits_at_each(tmp_path):
    home = a_home(tmp_path)
    before = {n: rows(home / n / "box") for n in ("book", "cv", "untouched")}
    got = at_home(home)  # they look, and leave
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith(
        "Hello. You have 2 tables.\n\n"
        "  1. The Book\n     Nothing settled yet. a reader left 2 things for you to look at.\n"
        "  2. cv\n     Nothing settled yet. a reader left 1 thing for you to look at.\n"
    )
    assert "untouched" not in got.stdout, (
        "a box nobody brought a word to is no table yet"
    )
    assert {n: rows(home / n / "box") for n in before} == before, (
        "looking writes nothing"
    )
    assert at_home(home, "").returncode == 0, "Enter leaves"


def test_the_host_picks_a_table_sits_and_is_back_at_the_list(tmp_path):
    home = a_home(tmp_path)
    # the book: its own words; one call answered; left with p; then the cv; then away
    got = at_home(home, "9", "1", "c", "y", "p", "2", "c", "n", "", "", "n", "")
    out = got.stdout
    assert got.returncode == 0, got.stderr
    assert "  1 to 2." in out, "a number that names no table is asked again"
    assert "The Book\n" in out and "Your call, author. a reader says:" in out
    assert out.count("You're back at your tables.") == 2
    assert "Paused. Nobody needs to say why." in out, (
        "a pause leaves the table, not the door"
    )
    # the list is read again each time: the book now holds one thing and one waits
    assert (
        "  1. The Book\n     You've settled 1 thing here. a reader left 1 thing for you to look at.\n"
        in out
    )
    assert (
        "  2. cv\n     Nothing settled yet.\n"
        in out.split("You're back at your tables.")[-1]
    )
    assert [t["fact"] for t in stands(home / "book" / "box")] == THINGS[:1]
    assert kinds(home / "cv" / "box").count("decline") == 1
    assert holds(home / "book" / "box") and holds(home / "cv" / "box")


def test_the_front_door_refuses_what_it_cant_be(tmp_path):
    home = a_home(tmp_path)
    for argv in (["--home", str(home), "--box", str(home / "cv" / "box")], ["--home", str(home), "--words", "w"],
                 ["--home", str(home), "stands"], ["--home"]):  # fmt: skip
        got = run(*argv, typed="")
        assert got.returncode == 2 and "table.py --home FOLDER" in got.stderr, argv
    got = run("--home", str(tmp_path / "nowhere"), typed="")
    assert got.returncode == 2 and got.stderr.endswith("isn't a folder\n")
    empty = tmp_path / "empty"
    empty.mkdir()
    got = run("--home", str(empty), typed="")
    assert got.returncode == 42 and "has been sat at yet" in got.stdout


def test_the_table_can_be_talked_to_in_words_and_says_what_else_there_is(tmp_path):
    box = a_box(tmp_path)
    for thing in THINGS[:2]:
        brought(box, "the agent", thing)
    got = sit(box, "?", "look", "s", "skip", "list", "undo", "pause")
    out = got.stdout
    assert got.returncode == 42 and "Paused. Nobody needs to say why." in out
    # the keys are behind ?: the opening asks one plain thing
    assert out.index("What is the first bite?") < out.index("You can type:")
    assert (
        "o: someone brings" not in out
        and "  look    see two of the things left for you" in out
    )
    # look is c; s and skip both set a call aside, and say what a yes and a no do
    assert "1 of 2. Your call. the agent says:" in out and "2 of 2. Your call." in out
    assert out.count("Type y to keep it, n to drop it, or s to skip it for now.") == 2
    assert out.count("Skipped for now.") == 2
    assert [r["part"] for r in rows(box) if r["kind"] == "table-x"] == ["call", "call"]
    assert "seal" not in kinds(box) and "decline" not in kinds(box)
    # list is s, undo is u: words a person would try
    assert "Nothing has been made true at this table yet." in out
    assert "Nothing has been made true this time to take back." in out


# ── a table's sheets: a stack of wants before a sitting, and one after ───────
needs_stack = pytest.mark.skipif(
    not all(HERE.parent.joinpath(a).is_dir() for a in ("stack", "todo", "box-health")),
    reason="the stack, todo or box-health add-on isn't here",
)


@needs_stack
def test_a_prep_sheet_is_run_when_the_host_asks_and_read_back_by_its_wants(tmp_path):
    box = a_box(tmp_path)
    assert "prep sheet" not in sit(box).stdout, "no sheet, nothing said of one"
    assert "This table has no prep sheet." in sit(box, "prep").stdout
    tmp_path.joinpath("pile", "list.md").write_text(
        "TODO call the landlord about the deposit\n"
    )
    tmp_path.joinpath("prep.md").write_text(
        "# before the call\n\nRun before I pick up the phone.\n\n## what I owe\n\n"
        'Want 1: "What do I still have to do?" The lines I marked to do.\n'
        "- todo -- --box {box}\n\n## how the box is\n\n- box-health -- --box {box}\n"
    )
    got = sit(box)
    assert (
        'This table has a prep sheet. Type "prep" to run it and see what it finds.'
        in got.stdout
    )
    runs = tmp_path.joinpath("prep")
    assert not runs.exists(), "nothing runs until the host asks"
    got = sit(box, "prep")
    out = got.stdout
    assert "Your prep sheet, run just now:" in out
    # each step is read back under the want written above it, or by its name
    assert (
        '  Want 1: "What do I still have to do?" The lines I marked to do.\n     todo: populated, 1 line'
        in out
    )
    assert "  box-health\n     box-health: " in out
    # asked, so answered: the line itself, and where it is from
    assert "TODO call the landlord about the deposit  (list.md:1)" in out
    first = runs.joinpath("001")
    assert f"Each one's page is in {first}" in out and first.is_dir()
    assert sit(box, "prep").returncode == 42 and len(list(runs.iterdir())) == 2, (
        "a run each time"
    )
    assert "seal" not in kinds(box), "a sheet reads and reports; it seals nothing"


@needs_stack
@needs_end
def test_an_end_sheet_is_run_at_the_end_and_the_sitting_is_still_sealed_as_one(
    tmp_path,
):
    box = a_box(tmp_path)
    tmp_path.joinpath("end.md").write_text(
        "# after the call\n\n## how the box is\n\n"
        'Want 1: "Is my box all right?"\n- box-health -- --box {box}\n'
    )
    got = sit(box, SAY + DEPOSIT, "y", "", "", "y")
    assert got.returncode == 0, got.stdout + got.stderr
    assert "Your end-of-sitting sheet, run just now:" in got.stdout
    assert '  Want 1: "Is my box all right?"\n     box-health: ' in got.stdout
    assert len(list(tmp_path.joinpath("end").iterdir())) == 1
    assert kinds(box).count("session") == 1 and holds(box)
    assert got.stdout.rstrip().endswith(
        "Saved and checked: nothing can be changed after the fact."
    )
    # an end sheet that bundles the sitting itself is not bundled twice
    tmp_path.joinpath("end.md").write_text(
        "# after\n\n## close\n\n- session-seal -- --box {box}\n"
    )
    got = sit(
        box,
        SAY + "The keys were returned.",
        "y",
        "",
        "",
        "y",
        when="2026-11-28T09:00:00Z",
    )
    assert got.returncode == 0 and kinds(box).count("session") == 2 and holds(box)


# ── the forge at the table: a want in the host's words, drafted into a sheet ─
FORGE = HERE.parents[1].joinpath("deps", "forge", "suggest.py")
DUE = "what is due and what I still have to do"
CLOSE = "count how often each suggestion was sealed or declined"


def a_box_to_ask(tmp_path: Path) -> Path:
    """A box with a date and a thing to do in it, and the forge reachable:
    skipped where the forge add-on or what it installs isn't."""
    if not FORGE.is_file() or sys.version_info < (3, 11):
        pytest.skip("the forge add-on needs Python 3.11 and its install")
    box = a_box(tmp_path)
    tmp_path.joinpath("pile", "list.md").write_text(
        "2026-11-30 The deposit is due back.\nTODO call the landlord\n"
    )
    seen = subprocess.run([sys.executable, str(FORGE), "suggest", "--box", str(box), DUE, "--json"],
                          capture_output=True, text=True)  # fmt: skip
    if '"unreachable"' in seen.stdout or not seen.stdout.strip():
        pytest.skip("forge-play isn't installed")
    return box


def test_a_want_is_drafted_by_the_forge_and_kept_only_on_the_hosts_yes(tmp_path):
    box = a_box_to_ask(tmp_path)
    page = tmp_path.joinpath("prep.md")
    before = rows(box)
    # they pick, then say no: nothing handed in, nothing written
    got = sit(box, DUE, "1", "", "n")
    assert "“due” could be answered more than one way:" in got.stdout
    assert "   1. coming-up: " in got.stdout and "   2. renewals: " in got.stdout
    assert "Then these would go on your prep sheet:" in got.stdout
    assert "Nothing was kept, and nothing was written." in got.stdout
    assert rows(box) == before and not page.exists()
    # gone at the fork, or at the yes: the same
    assert sit(box, DUE).returncode == 42 and sit(box, DUE, "1").returncode == 42
    assert rows(box) == before and not page.exists()
    # a pick that is no pick is asked again; then their yes seals the fork and the stack
    got = sit(box, DUE, "7", "1", "it has the dates", "y")
    assert "Why coming-up for “due”? A few words, or just press Enter:" in got.stdout
    assert "   1 to 2, n or s." in got.stdout
    assert kinds(box).count("seal") == 2 and holds(box)
    text = page.read_text()
    assert (
        "Want 2: “due”: coming-up, not renewals, because it has the dates.\ncoming-up: "
        in text
    ), "the fork's want comes after the step the sentence named, todo, as Want 1"
    assert "- coming-up -- --box {box}" in text and "- todo -- --box {box}" in text
    assert str(page) in got.stdout
    # and the sheet runs, read back by the wants the forge wrote
    assert "Here is what that found:" in got.stdout, (
        "asked, so answered: it is run at once"
    )
    assert "They are on your prep sheet now" in got.stdout
    ran = sit(box, "prep").stdout
    assert (
        "  Want 2: “due”: coming-up, not renewals, because it has the dates.\n     coming-up: "
        in ran
        and "     coming-up: " in ran
    )


@needs_stack
def test_a_step_that_writes_to_tmp_writes_inside_the_runs_own_folder(tmp_path):
    if not HERE.parent.joinpath("backup").is_dir():
        pytest.skip("the backup add-on isn't here")
    box = a_box(tmp_path)
    tmp_path.joinpath("prep.md").write_text(
        "## keep a copy\n\n- backup -- --box {box} --to {tmp}/backups\n"
    )
    elsewhere = tmp_path.joinpath("elsewhere")
    elsewhere.mkdir()
    got = subprocess.run([sys.executable, str(SCRIPT), "--box", str(box), "--now", NOW[1]],
                         input="prep\n", cwd=elsewhere, capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 42 and "backup: backed up:" in got.stdout, got.stdout
    for under in (elsewhere, tmp_path):
        assert not [p for p in under.rglob("*") if "{" in str(p.relative_to(under))]
    assert not list(elsewhere.iterdir()), "nothing in the working directory"
    zips = list(tmp_path.joinpath("prep", "001").glob("**/willow-backup-*.zip"))
    assert len(zips) == 1, "the copy is in the run's own folder"


def test_a_fork_left_for_later_puts_nothing_on_the_sheet(tmp_path):
    box = a_box_to_ask(tmp_path)
    # a sentence that reaches only the fork: DUE also names a step, todo
    got = sit(box, "what is due", "s")
    assert "Nothing to put on a sheet this time." in got.stdout
    assert not tmp_path.joinpath("prep.md").exists()
    assert kinds(box).count("seal") == 1, (
        "that it was left is a decision of its own, and kept"
    )
    assert holds(box)


def test_a_table_laid_but_never_sat_at_is_at_the_front_door(tmp_path):
    home = tmp_path.joinpath("home")
    home.joinpath("move").mkdir(parents=True)
    box = a_box(home.joinpath("move"))
    assert at_home(home).returncode == 42, "a box alone is no table yet"
    home.joinpath("move", "table-words.txt").write_text("title: The move\n")
    got = at_home(home, "1")
    assert "  1. The move\n     Nothing settled yet.\n" in got.stdout
    # the first thing they are asked is for the first bite
    assert "What is the first bite?" in got.stdout
    assert rows(box) == rows(box) and kinds(box) == ["boot"], (
        "looking and leaving writes nothing"
    )


def test_a_long_list_of_what_is_settled_opens_on_its_newest_few(tmp_path):
    box = a_box(tmp_path)
    for thing in THINGS:
        sit(box, SAY + thing, "y")
    extra = "Sixth, the post was forwarded."
    sit(box, SAY + extra, "y")
    opening = sit(box).stdout.split("What is the first bite?")[0]
    assert THINGS[0] not in opening and THINGS[2] not in opening
    assert all(t in opening for t in (THINGS[3], THINGS[4], extra))
    assert 'and 3 more, settled earlier. Type "list" to read them all.' in opening
    assert all(t in sit(box, "list").stdout for t in THINGS)


@needs_stack
def test_a_step_that_found_a_lot_reads_back_its_first_few_and_says_where_the_rest_is(
    tmp_path,
):
    box = a_box(tmp_path)
    tmp_path.joinpath("pile", "list.md").write_text(
        "".join(f"TODO thing number {i}\n" for i in range(1, 8))
    )
    tmp_path.joinpath("prep.md").write_text(
        "# before\n\n## what I owe\n\n- todo -- --box {box}\n"
    )
    out = sit(box, "prep").stdout
    assert (
        "TODO thing number 1  (list.md:1)" in out
        and "TODO thing number 5  (list.md:5)" in out
    )
    assert "thing number 6" not in out and "       and 2 more, in its page." in out


def test_a_bite_can_be_a_page_and_each_thing_it_reaches_says_its_line(tmp_path):
    box = a_box_to_ask(tmp_path)
    pile = box.parent.joinpath("pile")
    pile.joinpath("plan.md").write_text(
        "# Moving out\n\nThe deposit is due at the end of the month.\nThe truck is booked.\n"
    )
    pile.joinpath("blank.md").write_text("zzzq qqqz.\n")
    before = rows(box)
    got = sit(box, "plan.md", "1", "", "n")
    assert (
        "I read plan.md. These are the lines in it that ask for something:"
        in got.stdout
    )
    assert (
        "     plan.md:3  The deposit is due at the end of the month.  (“due”)"
        in got.stdout
    )
    assert "“due” could be answered more than one way:" in got.stdout
    assert rows(box) == before, "a page read and left writes nothing"
    # said with `read`, the same; a page that reaches nothing, and no page, are said
    assert "plan.md:3" in sit(box, "read plan.md", "1", "", "n").stdout
    assert (
        "I read blank.md, and nothing in it matches" in sit(box, "read blank.md").stdout
    )
    assert (
        "There is no page named gone.md in your files here."
        in sit(box, "read gone.md").stdout
    )
    assert rows(box) == before
    # kept: the sheet says the want in the page's own word, and where it is from
    sit(box, "plan.md", "1", "", "y")
    assert "# due (from plan.md)" in tmp_path.joinpath("prep.md").read_text()


def test_a_bite_at_the_front_door_is_asked_at_every_table_and_a_fork_once(tmp_path):
    home = tmp_path.joinpath("home")
    boxes = []
    for name in ("move", "work"):
        home.joinpath(name).mkdir(parents=True)
        boxes.append(a_box_to_ask(home.joinpath(name)))
        home.joinpath(name, "table-words.txt").write_text("title: " + name + "\n")
    got = at_home(home, DUE, "1", "it has the dates", "y", "y")
    out = got.stdout
    assert "Asking 2 tables, one at a time." in out
    assert out.count("“due” could be answered more than one way:") == 1, "asked once"
    assert out.count("“due”: coming-up, as you said.") == 1
    assert out.count("Put them on it? (y/n)") == 2, (
        "each table's record takes its own yes"
    )
    for name in ("move", "work"):
        text = home.joinpath(name, "prep.md").read_text()
        assert (
            "Want 2: “due”: coming-up, not renewals, because it has the dates." in text
        )
    # a no at the second table leaves that one as it was
    for name in ("move", "work"):
        home.joinpath(name, "prep.md").unlink()
    before = rows(boxes[1])
    at_home(home, "what is due this month", "1", "", "y", "n")
    assert home.joinpath("move", "prep.md").is_file()
    assert not home.joinpath("work", "prep.md").exists() and rows(boxes[1]) == before


def test_a_folder_holding_one_box_is_a_front_door_of_one(tmp_path):
    box = a_box(tmp_path)
    assert at_home(tmp_path).returncode == 42, "a box alone is no table yet"
    sit(box, SAY + DEPOSIT, "y")
    got = at_home(tmp_path)
    assert "Hello. You have 1 table.\n\n  1. " + tmp_path.name + "\n" in got.stdout


OWN = "# the move, my own stack\n\nWritten by hand.\n\n## every week\n# Want: what I still owe.\n- todo -- --box {box}\n"


def test_a_bite_adds_to_the_folders_own_stack_and_puts_no_step_in_twice(tmp_path):
    box = a_box_to_ask(tmp_path)
    own = tmp_path.joinpath("stack.md")
    own.write_text(OWN)
    got = sit(box, DUE, "1", "", "y")
    assert "Then these would be added to your own stack here, stack.md:" in got.stdout
    text = own.read_text()
    assert text.startswith(OWN), "what was written by hand is as it was"
    assert text.count("- todo -- --box {box}") == 1, "the stack had it already"
    assert (
        "Want 2: “due”: coming-up, not renewals.\n" in text
        and "- coming-up -- " in text
    )
    assert (
        ", and 1 it already had." in got.stdout
        and "Added to your own stack, " in got.stdout
    )
    assert not tmp_path.joinpath("prep.md").exists()
    # asked, so answered: what the bite asked is run, the stack's own step among it
    assert "Here is what that found:" in got.stdout and "     todo: " in got.stdout
    assert tmp_path.joinpath("bites", "001").is_dir()
    # the same bite again adds nothing
    sit(box, DUE, "y")
    assert own.read_text() == text


def test_a_stack_made_from_a_source_is_left_alone(tmp_path):
    box = a_box_to_ask(tmp_path)
    own = tmp_path.joinpath("stack.md")
    own.write_text(OWN)
    tmp_path.joinpath("stack.src").write_text("made from this\n")
    got = sit(box, DUE, "1", "", "y")
    assert own.read_text() == OWN
    assert (
        "Your stack here is made from stack.src, so I left it alone and used prep.md."
        in got.stdout
    )
    assert "- coming-up -- " in tmp_path.joinpath("prep.md").read_text()


#: other folders' stacks that put renewals and car beside coming-up, twice
OTHERS = {"a": ["coming-up", "renewals", "car"], "b": ["coming-up", "renewals", "car"],
          "c": ["foia", "minutes"], "d": ["foia", "route"], "e": ["minutes", "route"]}  # fmt: skip


def other_stacks(home: Path, only: tuple = ()) -> None:
    """Folders beside the tables that have a stack of their own and no box."""
    for name, steps in OTHERS.items():
        if only and name not in only:
            continue
        home.joinpath(name).mkdir(parents=True, exist_ok=True)
        home.joinpath(name, "stack.md").write_text(
            "# a stack\n\n## weekly\n# Want: something.\n"
            + "".join("- " + s + " -- --box {box}\n" for s in steps)
        )


def two_tables(home: Path) -> list[Path]:
    boxes = []
    for name in ("move", "work"):
        home.joinpath(name).mkdir(parents=True)
        boxes.append(a_box_to_ask(home.joinpath(name)))
        home.joinpath(name, "table-words.txt").write_text("title: The " + name + "\n")
    return boxes


def test_a_bite_says_what_the_other_stacks_put_beside_its_steps_and_writes_nothing(
    tmp_path,
):
    plain, with_others = tmp_path.joinpath("plain"), tmp_path.joinpath("with")
    boxes = []
    for home in (plain, with_others):
        home.joinpath("move").mkdir(parents=True)
        boxes.append(a_box_to_ask(home.joinpath("move")))
    other_stacks(with_others)
    out = []
    for box in boxes:
        out.append(sit(box, DUE, "1", "", "y").stdout)
    assert "Your other stacks put these beside those steps:" not in out[0]
    lead = "   Your other stacks put these beside those steps:\n"
    assert lead in out[1]
    lines = out[1].split(lead)[1].split("\n\n")[0].splitlines()
    assert 1 <= len(lines) <= 3 and all(ln.startswith("   - ") for ln in lines)
    assert any(ln.startswith("   - renewals: ") and "with coming-up in 2 of 2" in ln for ln in lines)  # fmt: skip
    assert ".;" not in out[1]
    # it only reads: the record is what a bite without it leaves
    assert kinds(boxes[0]) == kinds(boxes[1]) and len(rows(boxes[0])) == len(rows(boxes[1]))  # fmt: skip
    assert holds(boxes[1])


def test_nothing_is_said_beside_when_the_other_stacks_have_nothing_to_add(tmp_path):
    home = tmp_path.joinpath("home")
    home.joinpath("move").mkdir(parents=True)
    box = a_box_to_ask(home.joinpath("move"))
    # no other stack in sight: nothing is asked of the forge, nothing said
    assert "Your other stacks put" not in sit(box, DUE, "1", "", "y").stdout
    # stacks that never put anything beside these steps: nothing said either
    other_stacks(home, only=("c", "d", "e"))
    got = sit(box, "what is due this month", "1", "", "y")
    assert "Your other stacks put" not in got.stdout and holds(box)


def test_a_bite_at_every_table_gathers_what_each_found_into_one_list(tmp_path):
    home = tmp_path.joinpath("home")
    two_tables(home)
    got = at_home(home, DUE, "1", "it has the dates", "y", "y").stdout
    gathered = got.split("Everything that found, from every table:\n")[1].split("\n\nYou're back at your tables.")[0]  # fmt: skip
    assert "  Want 2: “due”: coming-up, not renewals, because it has the dates.\n" in gathered  # fmt: skip
    assert (
        "       2026-11-30 The deposit is due back.  (The move, list.md:1)\n"
        "       2026-11-30 The deposit is due back.  (The work, list.md:1)"
    ) in gathered, "the fork's want is the last, so no newline after it"
    assert "TODO call the landlord  (The move, list.md:2)" in gathered
    assert "No passage of 8 words" not in gathered, "only what found lines"
    assert got.index("Everything that found") < got.rindex("You're back at your tables.")  # fmt: skip


def test_the_gathered_list_caps_each_table_and_says_how_many_more(tmp_path):
    home = tmp_path.joinpath("home")
    two_tables(home)
    home.joinpath("move", "pile", "list.md").write_text(
        "".join(f"TODO thing number {i}\n" for i in range(1, 9))
    )
    got = at_home(home, DUE, "1", "", "y", "y").stdout
    gathered = got.split("Everything that found, from every table:\n")[1]
    assert "thing number 5  (The move, list.md:5)" in gathered
    assert "thing number 6" not in gathered
    assert "       and 3 more at The move, in its page.\n" in gathered
    assert "at The work" not in gathered


def test_one_table_asked_gathers_nothing(tmp_path):
    home = tmp_path.joinpath("home")
    home.joinpath("move").mkdir(parents=True)
    a_box_to_ask(home.joinpath("move"))
    home.joinpath("move", "table-words.txt").write_text("title: The move\n")
    got = at_home(home, DUE, "1", "", "y").stdout
    assert "Here is what that found:" in got and "Everything that found" not in got


def test_the_front_door_names_the_folders_with_a_stack_and_no_box(tmp_path):
    home = tmp_path.joinpath("home")
    two_tables(home)
    assert "have a stack but no box" not in at_home(home).stdout
    other_stacks(home, only=("c",))
    one = at_home(home).stdout
    assert "\n1 more folder has a stack but no box yet: c.\n" in one
    other_stacks(home)
    got = at_home(home).stdout
    assert "\n5 more folders have a stack but no box yet: a, b, c, d, e.\n" in got
    assert got.index("5 more folders") > got.index("  2. The work")
    assert got.index("5 more folders") < got.index("Which one would you like?")
    assert not home.joinpath("a", "box").exists(), "no box or key is made for them"
    assert "init" not in got and "--key" not in got


def a_box_to_close(tmp_path: Path) -> Path:
    """A box the forge's close fork is asked of: nothing in it that a word of
    the sentence names. Skipped where the forge or its search isn't here."""
    box = a_box_to_ask(tmp_path)
    tmp_path.joinpath("pile", "list.md").unlink()
    seen = run_forge("suggest", "--box", str(box), CLOSE)
    groups = json.loads(seen.stdout or "{}").get("groups", [])
    if not any(g["name"].startswith("fork “close”") for g in groups):
        pytest.skip("the forge's search isn't here to close on")
    return box


def run_forge(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(FORGE), *argv, "--json"],
                          capture_output=True, text=True)  # fmt: skip


def a_table_to_close(tmp_path: Path, name: str) -> tuple[Path, Path]:
    """(a box asked the close fork, the prep sheet beside it): one to a
    question, since a sealed none is not asked again for the same words."""
    here = tmp_path.joinpath(name)
    here.mkdir()
    return a_box_to_close(here), here.joinpath("prep.md")


def test_a_sentence_no_card_is_named_for_is_one_plain_question_and_none_is_a_miss(
    tmp_path,
):
    box, page = a_table_to_close(tmp_path, "none")
    out = sit(box, CLOSE, "n").stdout
    assert "Nothing here is named for that. These are the closest:" in out
    assert "“close”" not in out and "could be answered more than one way" not in out
    assert "   1. " in out and "   2. " in out
    assert "recommended" not in out and "confidence" not in out
    assert kinds(box).count("seal") == 1 and holds(box), "the miss is sealed"
    assert not page.exists() or "Want 1:" not in page.read_text()


def test_a_close_fork_left_for_later_puts_nothing_on_the_sheet(tmp_path):
    box, page = a_table_to_close(tmp_path, "later")
    out = sit(box, CLOSE, "s").stdout
    assert "Nothing here is named for that." in out
    assert not page.exists() or "Want 1:" not in page.read_text()
    assert holds(box)


def test_a_close_pick_and_a_yes_put_the_want_on_the_sheet_and_run_it(tmp_path):
    box, page = a_table_to_close(tmp_path, "pick")
    got = sit(box, CLOSE, "1", "it is close", "y")
    assert "Why assistant-scores? A few words, or just press Enter:" in got.stdout
    assert "for “close”?" not in got.stdout
    assert "Want 1:" in page.read_text() and "it is close" in page.read_text()
    assert "Here is what that found:" in got.stdout, got.stdout
    assert kinds(box).count("seal") == 2 and holds(box)
