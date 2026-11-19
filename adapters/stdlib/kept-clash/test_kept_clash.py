"""kept-clash: sealed answers other people sent you, read side by side, from
real boxes, real seals and real packages."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "kept_clash.py"
SHARE = HERE.parent / "share" / "share.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]
TOPICS = ["alpha", "beta", "gamma", "delta", "epsilon"]  # a question each


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)  # fmt: skip


def clash(*paths) -> subprocess.CompletedProcess:
    return run(SCRIPT, *paths)


class Person:
    """A box with a sender's identity, who seals answers and packs them."""

    def __init__(self, root: Path, name: str):
        self.dir = root / name
        (self.dir / "pile").mkdir(parents=True)
        (self.dir / "pile" / "notes.md").write_text(
            "".join(f"Topic {w} is in the notes of {name}.\n\n" for w in TOPICS)
        )
        self.box, self.id = self.dir / "box", self.dir / "id"
        got = run(KERNEL, "init", "--box", self.box, "--pile", self.dir / "pile",
                  "--key", self.dir / "key", *NOW)  # fmt: skip
        assert got.returncode == 0, got.stderr
        got = run(SHARE, "id", "--to", self.id)
        assert got.returncode == 0, got.stderr
        self.pub = got.stdout.strip()
        self.n = 0

    def seal(self, data: str, why: str = "my notes") -> str:
        bite = json.loads(
            run(
                KERNEL, "bite", "--box", self.box, f"topic {TOPICS[self.n]}", *NOW
            ).stdout
        )
        sug = self.dir / "s.jsonl"
        self.n += 1  # the next answer is to the next topic
        sug.write_text(json.dumps({"path": f"{self.n}.md", "data": data, "claim": why,
                                   "cites": [bite["served"][0]["id"]]}) + "\n")  # fmt: skip
        subj = run(KERNEL, "propose", "--box", self.box, "--file", sug, *NOW)
        subj = subj.stdout.split()[1]
        assert run(KERNEL, "seal", "--box", self.box, subj, *NOW).returncode == 0
        return subj

    def send(self, subjects, to: str, out: Path, *more) -> Path:
        got = run(SHARE, "send", "--box", self.box, "--id", self.id, "--answer",
                  ",".join(subjects), "--for", to, "--to", out, *NOW, *more)  # fmt: skip
        assert got.returncode == 0, got.stderr
        return out

    def says(self, data: str, out: Path, to: str, why: str = "my notes", *more) -> Path:
        return self.send([self.seal(data, why)], to, out, *more)


@pytest.fixture()
def world(tmp_path):
    class W:
        root = tmp_path
        keep = tmp_path / "kept"
        me = Person(tmp_path, "me")
        karst = Person(tmp_path, "karst")
        lumen = Person(tmp_path, "lumen")

    W.keep.mkdir()
    return W


def two(world, a: str, b: str, why_a="my notes", why_b="my notes"):
    world.karst.says(a, world.keep / "karst.pkg", world.me.pub, why_a)
    world.lumen.says(b, world.keep / "lumen.pkg", world.me.pub, why_b)
    return clash(world.keep)


def snapshot(folder: Path) -> dict[str, bytes]:
    return {str(p.relative_to(folder)): p.read_bytes() for p in folder.rglob("*") if p.is_file()}  # fmt: skip


def test_two_dates_for_one_thing_are_set_side_by_side_neither_picked(world):
    got = two(world, "Integration day began on 2026-06-12.",
              "Integration day began on 2026-06-19.")  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert "DATE    integration, began" in got.stdout
    assert "2026-06-12" in got.stdout and "2026-06-19" in got.stdout
    assert f"key {world.karst.pub[:12]}…" in got.stdout
    assert f"key {world.lumen.pub[:12]}…" in got.stdout
    assert "1 disagreement" in got.stdout and "neither side is picked" in got.stdout
    assert "never yours" in got.stdout
    # each answer is read: its text, its reason and the place it cites
    assert f"from key {world.karst.pub}" in got.stdout
    assert "answer: Integration day began on 2026-06-12." in got.stdout
    assert "why: my notes" in got.stdout and "cites 1.md" not in got.stdout
    assert "cites " in got.stdout


def test_two_times_for_one_thing_disagree_though_each_source_words_it_its_own_way(
    world,
):
    got = two(world, "The program schedule says integration day began at 08:00.",
              "The gate log says integration day began at 09:00.")  # fmt: skip
    assert got.returncode == 0
    assert "TIME    says, integration, began" in got.stdout
    assert "08:00" in got.stdout and "09:00" in got.stdout


def test_a_time_is_read_on_the_24_hour_clock_so_9pm_is_21_00(world):
    same = two(
        world, "Integration day began at 21:00.", "Integration day began at 9pm."
    )
    assert same.returncode == 42 and "No two answers" in same.stdout
    other = clash(world.keep)
    assert other.stdout == same.stdout


def test_two_amounts_of_one_unit_disagree(world):
    got = two(
        world, "The gate fee is $1,200 a night.", "The gate fee is $1250 a night."
    )
    assert got.returncode == 0
    assert "AMOUNT  gate, fee, night" in got.stdout
    assert "$1,200" in got.stdout and "$1250" in got.stdout


def test_one_unit_the_same_amount_written_two_ways_is_no_disagreement(world):
    got = two(
        world, "The gate fee is $1,200 a night.", "The gate fee is $1200.00 a night."
    )
    assert got.returncode == 42 and "No two answers saying the same thing" in got.stdout


def test_the_same_word_defined_as_two_kinds_of_thing_is_side_by_side(world):
    got = two(world, "An operator is a process that runs the gate.",
              "The operator is a person who signs people in.")  # fmt: skip
    assert got.returncode == 0
    assert "WORD    operator" in got.stdout
    assert "a process" in got.stdout and "a person" in got.stdout


def test_a_definition_with_a_kind_in_common_is_no_clash(world):
    got = two(world, "An operator is a person who signs people in.",
              "An operator is a human person on shift.")  # fmt: skip
    assert got.returncode == 42 and "WORD" not in got.stdout


def test_two_other_words_defined_differently_are_left_alone(world):
    got = two(
        world, "A gate is a barrier at the dock.", "A pass is a ticket for a day."
    )
    assert got.returncode == 42 and "WORD" not in got.stdout


def test_one_word_in_common_is_a_label_not_a_subject(world):
    got = two(world, "Rent is $900.", "Rent is $950.")
    assert got.returncode == 42


def test_different_subjects_with_different_dates_are_not_a_disagreement(world):
    got = two(
        world,
        "The harbour opens on 2026-06-12.",
        "The orchard picking ends 2026-06-19.",
    )
    assert got.returncode == 42


def test_a_reason_is_read_too_and_an_answer_against_the_others_reason(world):
    got = two(world, "Integration day was on time.", "It was late.",
              why_a="The schedule has integration day began on 2026-06-12.",
              why_b="The gate log shows integration day began on 2026-06-19.")  # fmt: skip
    assert got.returncode == 0 and "DATE" in got.stdout
    assert "(reason)" in got.stdout


def test_two_dates_inside_one_sentence_are_no_one_date(world):
    got = two(world, "Integration day moved from 2026-06-12 to 2026-06-19.",
              "Integration day began on 2026-06-19.")  # fmt: skip
    assert got.returncode == 42


def test_a_clock_time_is_not_read_as_an_amount_of_hours(world):
    got = two(
        world,
        "Integration day began at 09:00 hours.",
        "Integration day began at 09:00.",
    )
    assert got.returncode == 42, got.stdout


def test_the_answers_of_one_package_are_read_but_one_answer_never_clashes_with_itself(
    world,
):
    subj = [
        world.karst.seal(
            "Integration day began on 2026-06-12.", "the schedule: 2026-06-12"
        )
    ]
    got = clash(world.karst.send(subj, world.me.pub, world.keep / "k.pkg"))
    assert got.returncode == 42 and "1 answer read" in got.stdout


def test_a_package_that_does_not_hold_is_left_out_and_never_compared(world):
    good = world.karst.says("Integration day began on 2026-06-12.",
                            world.keep / "karst.pkg", world.me.pub)  # fmt: skip
    bad = world.lumen.says("Integration day began on 2026-06-19.",
                           world.keep / "lumen.pkg", world.me.pub)  # fmt: skip
    pkg = json.loads(bad.read_text())
    pkg["answers"][0]["data"] = "Integration day began on 2026-06-30."
    bad.write_text(json.dumps(pkg))
    got = clash(world.keep)
    assert got.returncode == 42
    assert "left out, does not hold" in got.stdout
    assert "2026-06-30" not in got.stdout and "2026-06-19" not in got.stdout
    assert "2 packages given, 1 hold" in got.stdout
    assert good.exists()


def test_a_file_that_is_not_a_package_is_left_out_by_name(world):
    (world.keep / "stray.pkg").write_text("not json")
    world.karst.says(
        "Integration day began on 2026-06-12.", world.keep / "k.pkg", world.me.pub
    )
    got = clash(world.keep)
    assert "stray.pkg: left out, could not read" in got.stdout.replace(
        str(world.keep) + "/", ""
    )


def test_a_package_a_kept_one_replaces_is_left_out(world):
    old = world.karst.says("Integration day began on 2026-06-12.",
                           world.keep / "old.pkg", world.me.pub)  # fmt: skip
    pid = run(SHARE, "check", "--package", old).stdout.split()[0]
    world.karst.says("Integration day began on 2026-06-12, 08:00.",
                     world.keep / "new.pkg", world.me.pub, "my notes", "--replaces", pid)  # fmt: skip
    world.lumen.says("Integration day began on 2026-06-12.",
                     world.keep / "lumen.pkg", world.me.pub)  # fmt: skip
    got = clash(world.keep)
    assert got.returncode == 42
    assert "a package you kept replaces it" in got.stdout
    assert "2 answers read" in got.stdout


def test_a_correction_is_not_compared_with_the_package_it_replaces(world):
    old = world.karst.says("Integration day began on 2026-06-12.",
                           world.keep / "old.pkg", world.me.pub)  # fmt: skip
    pid = run(SHARE, "check", "--package", old).stdout.split()[0]
    world.karst.says("Integration day began on 2026-06-19.",
                     world.keep / "new.pkg", world.me.pub, "my notes", "--replaces", pid)  # fmt: skip
    got = clash(world.keep)
    assert got.returncode == 42 and "DATE" not in got.stdout


def test_a_forwarded_package_names_the_one_who_sealed_not_the_one_who_passed_it_on(
    world,
):
    first = world.karst.says("Integration day began on 2026-06-12.",
                             world.root / "to-lumen.pkg", world.lumen.pub)  # fmt: skip
    got = run(SHARE, "receive", "--box", world.lumen.box, "--id", world.lumen.id,
              "--package", first, *NOW)  # fmt: skip
    assert got.returncode == 0, got.stderr
    got = run(SHARE, "forward", "--box", world.lumen.box, "--id", world.lumen.id,
              "--package", first, "--for", world.me.pub, "--to", world.keep / "fwd.pkg", *NOW)  # fmt: skip
    assert got.returncode == 0, got.stderr
    out = clash(world.keep)
    assert f"from key {world.karst.pub}, forwarded 1 time" in out.stdout
    assert world.lumen.pub not in out.stdout.replace("forwarded", "")


def test_the_same_answer_kept_twice_is_read_once(world):
    p = world.karst.says(
        "Integration day began on 2026-06-12.", world.keep / "a.pkg", world.me.pub
    )
    (world.keep / "copy.pkg").write_bytes(p.read_bytes())
    got = clash(world.keep)
    assert "1 answer read" in got.stdout and "1 package" in got.stdout.replace(
        "2 packages", "1 package"
    )


def test_a_form_field_said_on_three_answers_is_left_alone(world):
    for i, who in enumerate((world.karst, world.lumen, world.me)):
        who.says(
            f"Total due is ${100 + i} for the gate.",
            world.keep / f"{i}.pkg",
            world.me.pub,
        )
    got = clash(world.keep)
    assert got.returncode == 42 and "form's field left alone" in got.stdout


def test_a_folder_is_searched_down_and_hidden_ones_are_not_read(world):
    sub = world.keep / "deep" / "er"
    sub.mkdir(parents=True)
    (world.keep / ".hidden").mkdir()
    world.karst.says(
        "Integration day began on 2026-06-12.", sub / "a.pkg", world.me.pub
    )
    world.lumen.says(
        "Integration day began on 2026-06-19.",
        world.keep / ".hidden" / "b.pkg",
        world.me.pub,
    )
    got = clash(world.keep)
    assert got.returncode == 42 and "1 answer read" in got.stdout


def test_a_list_of_files_is_read_as_given(world):
    a = world.karst.says(
        "Integration day began on 2026-06-12.", world.root / "a.dat", world.me.pub
    )
    b = world.lumen.says(
        "Integration day began on 2026-06-19.", world.root / "b.dat", world.me.pub
    )
    got = clash(a, b)
    assert got.returncode == 0 and "DATE" in got.stdout
    assert clash(a, b).stdout == got.stdout, "the same input, the same bytes"


def test_it_only_reads_and_a_second_run_changes_nothing(world):
    two(
        world,
        "Integration day began on 2026-06-12.",
        "Integration day began on 2026-06-19.",
    )
    before, boxes = snapshot(world.keep), snapshot(world.karst.dir)
    clash(world.keep)
    assert snapshot(world.keep) == before and snapshot(world.karst.dir) == boxes
    rows = (world.me.box / "record.jsonl").read_text()
    assert "received" not in rows and "seal" not in rows, "nothing of yours is written"


def test_an_empty_folder_and_a_folder_with_no_package_say_so(world):
    got = clash(world.keep)
    assert got.returncode == 42 and "no .pkg file" in got.stdout
    (world.keep / "notes.md").write_text("Tomatoes want sun.\n")
    assert clash(world.keep).returncode == 42


def test_only_packages_that_do_not_hold_means_nothing_to_set_side_by_side(world):
    (world.keep / "x.pkg").write_text("{}")
    got = clash(world.keep)
    assert got.returncode == 42 and "Nothing to set side by side" in got.stdout


def test_a_bad_command_line_is_refused_and_says_how_to_run_it(world):
    for argv in ([], ["--box", "x"], [str(world.root / "missing")]):
        got = clash(*argv)
        assert got.returncode == 2 and got.stderr.startswith(("usage", "refused"))
    assert "kept_clash.py" in clash().stderr


def test_it_never_reads_the_key_it_is_given_by_mistake(world):
    got = clash(world.me.dir / "key")
    assert got.returncode == 42 and "left out" in got.stdout
    assert "kernel" not in got.stdout.lower()
