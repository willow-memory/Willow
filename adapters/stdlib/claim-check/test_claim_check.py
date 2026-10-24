"""claim-check: the passages holding every part of a claim, those holding
the most short of that with what they lack, and the parts no file has."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import claim_check  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "claim_check.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]


def box(tmp_path: Path, words: str | None = None) -> Path:
    pile = tmp_path / "pile"
    (pile / "gmail").mkdir(parents=True)
    (pile / "policy.txt").write_text(
        "We don't show you personalized ads based on your content from Gmail.\n\n"
        "Automated systems analyze your content for personalized ads.\n\n"
        "We never scan email for ads.\n"
    )
    (pile / "gmail" / "notes.txt").write_text("Spam is filtered.\n")
    extra = []
    if words is not None:
        wl = tmp_path / "words.txt"
        wl.write_text(words)
        os.chmod(wl, 0o600)
        extra = ["--words", str(wl)]
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *extra, *NOW],
                   check=True, capture_output=True)  # fmt: skip
    return b


def run(b: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--box", str(b), *argv],
                          capture_output=True, text=True)  # fmt: skip


def test_some_parts_and_the_part_no_file_has(tmp_path):
    got = run(box(tmp_path), "Google scans Gmail for ads")
    assert got.returncode == 42
    lines = got.stdout.splitlines()
    assert lines[0] == "some parts   policy.txt:1   gmail, ads   lacks google, scans"
    assert lines[-1] == "no file has  google"  # "scan" is held: scans is its plain form


def test_every_part_in_one_passage(tmp_path):
    got = run(box(tmp_path), "systems analyze content for ads")
    assert got.returncode == 0
    assert got.stdout.splitlines()[0] == (
        "all parts    policy.txt:3   systems, analyze, content, ads"
    )
    assert "no file has" not in got.stdout


def test_a_denial_holding_every_part_is_still_listed(tmp_path):
    got = run(box(tmp_path), "scan email ads")
    assert got.returncode == 0 and "all parts    policy.txt:5" in got.stdout


def test_a_folders_name_counts_and_top_limits_the_partial_list(tmp_path):
    got = run(box(tmp_path), "gmail spam filtered ads content", "--top", "1")
    lines = got.stdout.splitlines()
    assert lines == [
        "some parts   gmail/notes.txt:1   gmail, spam, filtered   lacks ads, content"
    ]


def test_the_words_list_is_read_as_bite_reads_it(tmp_path):
    b = box(tmp_path, "adverts = ads\n")
    got = run(b, "adverts gmail content personalized")
    assert got.returncode == 0 and got.stdout.startswith("all parts    policy.txt:1")


def test_nothing_held_and_refusals(tmp_path):
    b = box(tmp_path)
    got = run(b, "zebra quokka")
    assert got.returncode == 42
    assert got.stdout.splitlines() == ["no file has  zebra, quokka",
                                       "Nothing in your folder holds any part of it."]  # fmt: skip
    assert run(b, "the and for").returncode == 2
    assert run(b, "ads", "--top", "0").returncode == 2
    assert run(tmp_path, "ads").returncode == 2


def test_parts_drop_common_words_and_repeats():
    assert claim_check.parts("Is Google scanning Gmail for the ads, Google?") == [
        "google", "scanning", "gmail", "ads"]  # fmt: skip


def test_three_partial_passages_unless_top_says_otherwise(tmp_path):
    b = box(tmp_path)
    got = run(b, "content ads gmail spam")  # four passages hold some of it
    assert [s.split()[2] for s in got.stdout.splitlines()] == [
        "policy.txt:1", "gmail/notes.txt:1", "policy.txt:3"]  # fmt: skip
    assert len(run(b, "content ads gmail spam", "--top", "4").stdout.splitlines()) == 4
