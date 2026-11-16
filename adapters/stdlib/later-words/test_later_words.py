"""later-words: a box made again with a words list it lacked. The record is
laid down again through the kernel's own append and comes out the same bytes;
seals, declines, proposals and answers are all still there and still verify;
the old box is untouched; the next bite reads the list; and a box that can't
be carried over exactly, or a list the kernel refuses, writes nothing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "later_words.py"
KERNEL = HERE.parents[2] / "kernel.py"
T0, T1, T2, T3, T4 = (f"2026-11-0{d}T09:00:00Z" for d in (1, 2, 3, 4, 5))


def run(script: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], capture_output=True, text=True)  # fmt: skip


def kernel(*argv: str) -> subprocess.CompletedProcess:
    return run(KERNEL, *argv)


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}  # fmt: skip


def words_file(tmp: Path, text: str = "rego = registration\n") -> Path:
    path = tmp / "my-words.txt"
    path.write_text(text, encoding="utf-8")
    if os.name == "posix":
        path.chmod(0o600)
    return path


def make(tmp: Path, name: str = "life") -> tuple[Path, Path, Path]:
    """A box with no words list and a real history: a bite nothing answered,
    one answer sealed, one suggestion declined; (box, key, pile)."""
    pile, box, key = tmp / f"{name}-files", tmp / f"{name}-box", tmp / f"{name}.key"
    pile.mkdir()
    (pile / "Mail").mkdir()
    (pile / "Mail" / "notice.txt").write_text(
        "Registration renewal notice for the Subaru: amount due $912.40\n",
        encoding="utf-8",
    )
    (pile / "dentist.txt").write_text("The dentist is on Tuesday at 3pm.\n", encoding="utf-8")  # fmt: skip
    (pile / "gym.txt").write_text(
        "The gym closes at 9pm on Fridays.\n", encoding="utf-8"
    )
    assert kernel("init", "--box", str(box), "--pile", str(pile), "--key", str(key), "--now", T0).returncode == 0  # fmt: skip
    assert kernel("bite", "--box", str(box), "--now", T1, "how much is the car rego").returncode == 42  # fmt: skip
    for when, ask, path, data, doing in (
        (T2, "when is the dentist", "dentist.md", "Tuesday 3pm.", "seal"),
        (T3, "when does the gym close", "gym.md", "9pm.", "decline"),
    ):
        got = kernel("bite", "--box", str(box), "--now", when, ask)
        ref = json.loads(got.stdout)["served"][0]["id"]
        line = json.dumps({"path": path, "data": data, "cites": [ref], "claim": ask})
        (tmp / f"{name}.jsonl").write_text(line + "\n", encoding="utf-8")
        got = kernel("propose", "--box", str(box), "--now", when, "--file", str(tmp / f"{name}.jsonl"))  # fmt: skip
        subj = got.stdout.split()[1]
        assert kernel(doing, "--box", str(box), "--now", T4, subj).returncode == 0
    assert kernel("verify", "--box", str(box)).returncode == 0
    return box, key, pile


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("made")
    box, key, pile = make(tmp)
    before, key_before = snapshot(box), key.read_bytes()
    words = words_file(tmp)
    new = tmp / "life-box-2"
    got = run(SCRIPT, "--box", str(box), "--words", str(words), "--to", str(new))
    return {"tmp": tmp, "box": box, "key": key, "pile": pile, "new": new,
            "words": words, "before": before, "key_before": key_before, "got": got}  # fmt: skip


def test_the_record_comes_out_the_same_bytes_and_verifies(made):
    got = made["got"]
    assert got.returncode == 0, got.stderr
    old, new = made["box"], made["new"]
    assert (new / "record.jsonl").read_bytes() == (old / "record.jsonl").read_bytes()
    check = kernel("verify", "--box", str(new))
    assert check.returncode == 0 and "the chain holds: 8 rows, 1 sealed" in check.stdout, check.stdout  # fmt: skip
    assert "8 rows byte for byte" in got.stdout and str(new) in got.stdout


def test_proposals_and_answers_are_carried_as_they_were(made):
    old, new = made["box"], made["new"]
    for name in ("proposals", "written"):
        assert snapshot(new / name) == snapshot(old / name) != {}
    assert (new / "written" / "dentist.md").read_text() == "Tuesday 3pm."


def test_it_changes_one_thing_the_words_list_in_the_new_boxes_settings(made):
    old, new = made["box"], made["new"]
    cfg = json.loads((new / "kernel.json").read_text())
    assert cfg == {**json.loads((old / "kernel.json").read_text()),
                   "words": str(made["words"].resolve())}  # fmt: skip
    assert sorted(snapshot(new)) == sorted(set(snapshot(old)) | {"kernel.json"})


def test_the_old_box_and_the_key_are_untouched(made):
    assert snapshot(made["box"]) == made["before"]
    assert made["key"].read_bytes() == made["key_before"]
    assert "words" not in json.loads((made["box"] / "kernel.json").read_text())


def test_the_new_box_reads_the_list_from_the_next_bite_and_the_old_still_does_not(tmp_path_factory, made):  # fmt: skip
    new, old = made["new"], made["box"]
    ask = "how much is the car rego"
    got = kernel("bite", "--box", str(new), "--now", "2026-11-06T09:00:00Z", ask)
    doc = json.loads(got.stdout)
    assert got.returncode == 0 and doc["state"] == "populated", got.stdout
    assert "$912.40" in doc["served"][0]["text"]
    row = [json.loads(x) for x in (new / "record.jsonl").read_text().splitlines()][-1]
    import hashlib

    assert row["words_sha256"] == hashlib.sha256(made["words"].read_bytes()).hexdigest()
    assert all("words_sha256" not in json.loads(x)
               for x in (old / "record.jsonl").read_text().splitlines())  # fmt: skip
    assert kernel("verify", "--box", str(new)).returncode == 0


def test_the_earlier_seal_still_answers_and_the_earlier_decline_still_holds(made):
    new = made["new"]
    got = kernel("bite", "--box", str(new), "--now", "2026-11-06T10:00:00Z", "when is the dentist")  # fmt: skip
    assert json.loads(got.stdout)["state"] == "sealed"
    rows = [json.loads(x) for x in (new / "record.jsonl").read_text().splitlines()]
    declined = next(r["subject"] for r in rows if r["kind"] == "decline")
    again = kernel("seal", "--box", str(new), "--now", "2026-11-06T11:00:00Z", declined)
    assert again.returncode == 2 and "you declined" in again.stderr


def refused(tmp: Path, why: str, *argv: str, new: Path | None = None) -> None:
    got = run(SCRIPT, *argv)
    assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr
    assert why in got.stderr, got.stderr
    if new is not None:
        assert not new.exists(), "a refusal writes nothing"


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in ([], ["--box", "x"], ["--box", "x", "--words", "w"],
                 ["--box", "x", "--words", "w", "--to", "n", "stray"]):  # fmt: skip
        got = run(SCRIPT, *argv)
        assert got.returncode == 2 and "later_words.py" in got.stderr, argv


def test_what_is_not_a_box_is_refused(tmp_path):
    new = tmp_path / "n"
    refused(tmp_path, "not a kernel box", "--box", str(tmp_path), "--words", str(words_file(tmp_path)), "--to", str(new), new=new)  # fmt: skip


def test_a_box_that_has_words_already_is_refused(tmp_path):
    pile, words, new = tmp_path / "p", words_file(tmp_path), tmp_path / "n"
    pile.mkdir()
    (pile / "a.txt").write_text("tomatoes want sun\n")
    box = tmp_path / "b"
    kernel("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k"), "--words", str(words))  # fmt: skip
    refused(tmp_path, "has a words list already", "--box", str(box), "--words", str(words), "--to", str(new), new=new)  # fmt: skip


def test_a_list_the_kernel_refuses_is_refused_with_its_reason(tmp_path):
    box, _, _ = make(tmp_path)
    new = tmp_path / "n"
    bad = words_file(tmp_path, "rego is registration\n")
    refused(tmp_path, "words list line 1", "--box", str(box), "--words", str(bad), "--to", str(new), new=new)  # fmt: skip
    if os.name == "posix":
        open_list = words_file(tmp_path)
        open_list.chmod(0o644)
        refused(tmp_path, "chmod 600", "--box", str(box), "--words", str(open_list), "--to", str(new), new=new)  # fmt: skip
    refused(tmp_path, "could not be read", "--box", str(box), "--words", str(tmp_path / "none.txt"), "--to", str(new), new=new)  # fmt: skip


def test_a_list_inside_either_box_is_refused(tmp_path):
    box, _, _ = make(tmp_path)
    new = tmp_path / "n"
    inside = box / "words.txt"
    inside.write_text("rego = registration\n")
    if os.name == "posix":
        inside.chmod(0o600)
    refused(tmp_path, "inside a box", "--box", str(box), "--words", str(inside), "--to", str(new), new=new)  # fmt: skip
    inside_new = new / "w.txt"  # a list that would sit in the new box
    refused(tmp_path, "inside a box", "--box", str(box), "--words", str(inside_new), "--to", str(new), new=new)  # fmt: skip


def test_a_missing_key_stops_it_and_no_key_is_made(tmp_path):
    box, key, _ = make(tmp_path)
    new = tmp_path / "n"
    key.unlink()
    refused(tmp_path, "your key is not where the box says", "--box", str(box), "--words", str(words_file(tmp_path)), "--to", str(new), new=new)  # fmt: skip
    assert not key.exists()


def test_a_record_that_does_not_verify_is_not_carried(tmp_path):
    box, _, _ = make(tmp_path)
    new = tmp_path / "n"
    path = box / "record.jsonl"
    path.write_bytes(
        path.read_bytes().replace(b'"verdict":"pass"', b'"verdict":"fail"', 1)
    )
    refused(tmp_path, "doesn't verify", "--box", str(box), "--words", str(words_file(tmp_path)), "--to", str(new), new=new)  # fmt: skip


def test_a_record_that_began_over_another_pile_is_refused(tmp_path):
    box, _, _ = make(tmp_path)
    new = tmp_path / "n"
    cfg = json.loads((box / "kernel.json").read_text())
    other = tmp_path / "elsewhere"
    other.mkdir()
    (box / "kernel.json").write_text(json.dumps({**cfg, "pile": str(other)}))
    refused(tmp_path, "first row can't be made again as it was", "--box", str(box), "--words", str(words_file(tmp_path)), "--to", str(new), new=new)  # fmt: skip


def test_settings_it_would_lose_are_refused(tmp_path):
    box, _, _ = make(tmp_path)
    new = tmp_path / "n"
    cfg = json.loads((box / "kernel.json").read_text())
    (box / "kernel.json").write_text(json.dumps({**cfg, "extra": "1"}))
    refused(tmp_path, "holds more than a pile and a key", "--box", str(box), "--words", str(words_file(tmp_path)), "--to", str(new), new=new)  # fmt: skip


def test_a_new_place_that_is_taken_or_unsafe_is_refused(tmp_path, tmp_path_factory):
    box, _, pile = make(tmp_path)
    words = str(words_file(tmp_path))
    taken = tmp_path / "taken"
    taken.mkdir()
    (taken / "keep.txt").write_text("mine")
    refused(tmp_path, "is there already, and not empty", "--box", str(box), "--words", words, "--to", str(taken))  # fmt: skip
    assert snapshot(taken) == {"keep.txt": b"mine"}
    refused(tmp_path, "can't be inside the old", "--box", str(box), "--words", words, "--to", str(box / "again"), new=box / "again")  # fmt: skip
    elsewhere = words_file(
        tmp_path_factory.mktemp("w")
    )  # so only the folders are in question
    refused(tmp_path, "can't be inside the old", "--box", str(box), "--words", str(elsewhere), "--to", str(tmp_path))  # fmt: skip
    other, _, _ = make(tmp_path, "other")
    refused(tmp_path, "is inside a box", "--box", str(box), "--words", words, "--to", str(other / "x"), new=other / "x")  # fmt: skip
    refused(tmp_path, "make it first", "--box", str(box), "--words", words, "--to", str(tmp_path / "no" / "n"), new=tmp_path / "no")  # fmt: skip
    file = tmp_path / "a-file"
    file.write_text("x")
    refused(tmp_path, "there already", "--box", str(box), "--words", words, "--to", str(file))  # fmt: skip


def test_an_empty_folder_will_do_for_the_new_box(tmp_path):
    box, _, _ = make(tmp_path)
    new = tmp_path / "ready"
    new.mkdir()
    got = run(SCRIPT, "--box", str(box), "--words", str(words_file(tmp_path)), "--to", str(new))  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert kernel("verify", "--box", str(new)).returncode == 0


def test_a_box_with_nothing_but_its_boot_row_is_made_again(tmp_path):
    pile, box = tmp_path / "p", tmp_path / "b"
    pile.mkdir()
    (pile / "a.txt").write_text("tomatoes want sun\n")
    kernel("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k"), "--now", T0)  # fmt: skip
    new = tmp_path / "n"
    got = run(SCRIPT, "--box", str(box), "--words", str(words_file(tmp_path)), "--to", str(new))  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert "1 rows byte for byte" in got.stdout
    assert not (new / "proposals").exists() and not (new / "written").exists()
