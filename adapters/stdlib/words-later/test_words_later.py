"""words-later: a box made again with a words list it lacked; its record is
the old one byte for byte, the old box is untouched, and it refuses rather
than leave half a box."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOOL = HERE / "words_later.py"
KERNEL = ROOT / "kernel.py"


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def kernel(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def old_box(tmp: Path, words: Path | None = None) -> dict:
    pile = tmp / "pile"
    pile.mkdir()
    (pile / "a.txt").write_text("the licence is apache\n")
    more = ["--words", str(words)] if words else []
    assert (
        kernel(
            "init", "--box", tmp / "old", "--pile", pile, "--key", tmp / "key", *more
        ).returncode
        == 0
    )
    kernel("bite", "--box", tmp / "old", "license")
    return {"old": tmp / "old", "new": tmp / "new", "key": tmp / "key"}


def a_list(tmp: Path, text="license = licence\n", mode=0o600) -> Path:
    w = tmp / "words.txt"
    w.write_text(text)
    os.chmod(w, mode)
    return w


def test_made_again_it_reads_the_list_and_the_record_is_the_old_one(tmp_path):
    b, w = old_box(tmp_path), a_list(tmp_path)
    was = {p.name: p.read_bytes() for p in b["old"].iterdir()}
    assert '"state": "empty"' in kernel("bite", "--box", b["old"], "license").stdout
    was = {p.name: p.read_bytes() for p in b["old"].iterdir()}
    got = run("make", "--box", b["old"], "--words", w, "--to", b["new"])
    assert got.returncode == 0, got.stderr
    rows = len(was["record.jsonl"].splitlines())
    assert got.stdout.splitlines()[0] == (
        f"made: {b['new']}, with {b['old']}'s record as it was ({rows} rows), reading {w} (1 words)"
    )
    assert (
        f"  mv {b['old']} {b['old']}.before-words\n  mv {b['new']} {b['old']}\n"
        in got.stdout
    )
    # the record byte for byte, the settings the old ones and the list, no more
    assert (b["new"] / "record.jsonl").read_bytes() == was["record.jsonl"]
    cfg, old = (
        json.loads((b["new"] / "kernel.json").read_text()),
        json.loads(was["kernel.json"]),
    )
    assert cfg == {**old, "words": str(w.resolve())}
    assert sorted(p.name for p in b["new"].iterdir()) == ["kernel.json", "record.jsonl"]
    # the old box is as it was, and was never moved
    assert {p.name: p.read_bytes() for p in b["old"].iterdir()} == was
    assert not Path(f"{b['old']}.before-words").exists()
    # the kernel takes the new box: its chain holds, and the list is read
    assert f"the chain holds: {rows} rows" in kernel("verify", "--box", b["new"]).stdout
    assert '"state": "populated"' in kernel("bite", "--box", b["new"], "license").stdout
    assert (b["old"] / "record.jsonl").read_bytes() == was["record.jsonl"]


def test_a_sealed_answer_still_proves_in_the_new_box(tmp_path):
    b, w = old_box(tmp_path), a_list(tmp_path)
    bite = json.loads(kernel("bite", "--box", b["old"], "licence").stdout)
    said = tmp_path / "s.jsonl"
    said.write_text(json.dumps({"bite_key": bite["bite_key"], "answer": "apache",
                                "cites": [bite["served"][0]["id"]], "reason": "the file says so"}) + "\n")  # fmt: skip
    put = kernel("propose", "--box", b["old"], "--file", said)
    subject = [x for x in put.stdout.split() if x.startswith("proposal:")]
    if not subject:  # this kernel words a suggestion another way: nothing to carry
        return
    assert kernel("seal", "--box", b["old"], subject[0]).returncode == 0
    before = kernel("verify", "--box", b["old"]).stdout
    assert "1 sealed" in before
    assert (
        run("make", "--box", b["old"], "--words", w, "--to", b["new"]).returncode == 0
    )
    assert kernel("verify", "--box", b["new"]).stdout == before


def test_check_says_whether_a_box_names_a_list(tmp_path):
    b, w = old_box(tmp_path), a_list(tmp_path)
    got = run("check", "--box", b["old"])
    assert (
        got.returncode == 42
        and got.stdout == f"no words list: {b['old']} was made without one\n"
    )
    run("make", "--box", b["old"], "--words", w, "--to", b["new"])
    got = run("check", "--box", b["new"])
    assert (
        got.returncode == 0
        and got.stdout == f"words list: {b['new']} reads {w.resolve()}, 1 words\n"
    )
    os.chmod(w, 0o644)
    got = run("check", "--box", b["new"])
    assert got.returncode == 2 and "readable beyond its owner" in got.stderr
    assert run("check", "--box", tmp_path / "pile").returncode == 2


def test_a_box_that_has_a_list_is_refused_and_told_which(tmp_path):
    w = a_list(tmp_path)
    b = old_box(tmp_path, w)
    got = run("make", "--box", b["old"], "--words", w, "--to", b["new"])
    assert got.returncode == 2 and not b["new"].exists()
    assert f"already names a words list, {w.resolve()}" in got.stderr


def test_a_list_the_kernel_would_not_take_is_refused(tmp_path):
    b = old_box(tmp_path)
    for text, mode, why in (("license = the licence\n", 0o600, "words list line 1"),
                            ("license = licence\n", 0o644, "readable beyond its owner")):  # fmt: skip
        w = a_list(tmp_path, text, mode)
        got = run("make", "--box", b["old"], "--words", w, "--to", b["new"])
        assert got.returncode == 2 and why in got.stderr and not b["new"].exists(), why
    got = run(
        "make", "--box", b["old"], "--words", tmp_path / "none.txt", "--to", b["new"]
    )
    assert got.returncode == 2 and "could not be read" in got.stderr
    inside = b["old"] / "words.txt"
    inside.write_text("license = licence\n")
    os.chmod(inside, 0o600)
    got = run("make", "--box", b["old"], "--words", inside, "--to", b["new"])
    assert got.returncode == 2 and "can't live inside the box" in got.stderr
    inside.unlink()
    assert not b["new"].exists()


def test_not_a_box_a_broken_record_or_a_new_that_is_there_is_refused(tmp_path):
    b, w = old_box(tmp_path), a_list(tmp_path)
    got = run("make", "--box", tmp_path / "pile", "--words", w, "--to", b["new"])
    assert got.returncode == 2 and "is not a box" in got.stderr
    b["new"].mkdir()
    got = run("make", "--box", b["old"], "--words", w, "--to", b["new"])
    assert got.returncode == 2 and "is already there" in got.stderr
    assert list(b["new"].iterdir()) == []
    b["new"].rmdir()
    got = run("make", "--box", b["old"], "--words", w, "--to", tmp_path / "no" / "new")
    assert got.returncode == 2 and "its folder isn't there" in got.stderr
    rec = b["old"] / "record.jsonl"
    rec.write_text(rec.read_text().replace('"boot"', '"b00t"'))
    got = run("make", "--box", b["old"], "--words", w, "--to", b["new"])
    assert (
        got.returncode == 2
        and "record doesn't verify" in got.stderr
        and not b["new"].exists()
    )


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in ([], ["remake"], ["make"], ["make", "--box", "a", "--words", "b"],
                 ["make", "--box", "a", "--words", "b", "--to", "c", "--to", "d"],
                 ["make", "--box", "a", "--words", "b", "--into", "c"],
                 ["check"], ["check", "--box"], ["check", "--box", "a", "--words", "b"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "words_later.py make --box OLD" in got.stderr, (
            argv
        )
