"""history: each row of the record said as what happened, by day, with no
words the record doesn't keep; and nothing written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("history", HERE / "history.py")
hs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hs)


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def life(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "dentist.txt").write_text("The dentist is on Tuesday at 3pm.\n")
    b = tmp_path / "box"
    k(
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "key"),
        "--now",
        "2026-10-23T09:12:00Z",
    )
    served = json.loads(
        k(
            "bite",
            "--box",
            str(b),
            "--now",
            "2026-10-23T09:13:00Z",
            "when is the dentist",
        ).stdout
    )["served"]
    k("bite", "--box", str(b), "--now", "2026-10-24T08:00:00Z", "where is my passport")
    k("bite", "--box", str(b), "--now", "2026-10-24T08:01:00Z", "where is my passport")
    k("bite", "--box", str(b), "--now", "2026-10-24T08:02:00Z", "when is the dentist")
    rows = [{"path": "dentist.md", "data": "SECRET-ANSWER Tuesday 3pm", "cites": [served[0]["id"]], "claim": "the note"},
            {"path": "../out", "data": "x", "cites": [], "claim": "x"}]  # fmt: skip
    (tmp_path / "s.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    k(
        "propose",
        "--box",
        str(b),
        "--file",
        str(tmp_path / "s.jsonl"),
        "--now",
        "2026-10-24T09:20:00Z",
    )
    k("out", "--box", str(b), "--now", "2026-10-24T09:20:30Z")
    subj = json.loads((b / "record.jsonl").read_text().splitlines()[-3])["subject"]
    k("seal", "--box", str(b), subj, "--now", "2026-10-24T09:21:00Z")
    k("bite", "--box", str(b), "--now", "2026-10-24T09:22:00Z", "when is the dentist")
    return b


def test_each_row_is_said_as_what_happened_by_day(tmp_path, capsys):
    b = life(tmp_path)
    assert hs.main(["--box", str(b)]) == 0
    out = capsys.readouterr().out
    assert out == (
        "2026-10-23\n"
        "  09:12  You started your record.\n"
        "  09:13  You asked a question. Your files held it: dentist.txt:1.\n"
        "\n2026-10-24\n"
        "  08:00  You asked a question. Nothing in your folder held it.\n"
        "  08:01  You asked a question again (2nd time). Nothing in your folder held it.\n"
        "  08:02  You asked a question again (2nd time). Your files held it: dentist.txt:1.\n"
        "  09:20  A suggestion was handed in for dentist.md. It waits for you.\n"
        "  09:20  A suggestion was turned away at the door: a path is plain and relative, inside the box.\n"
        "  09:20  You looked at what was waiting: 1 suggestion.\n"
        "  09:21  You approved the suggestion for dentist.md.\n"
        "  09:22  You asked a question again (3rd time). Your approved answer for dentist.md answered it.\n"
    )


def test_no_words_the_record_doesnt_keep(tmp_path, capsys):
    b = life(tmp_path)
    hs.main(["--box", str(b)])
    out = capsys.readouterr().out
    for word in ("dentist is", "passport", "SECRET-ANSWER", "Tuesday", "the note"):
        assert word not in out


def test_it_writes_nothing(tmp_path):
    b = life(tmp_path)
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    assert hs.main(["--box", str(b)]) == 0
    assert {p: p.read_bytes() for p in b.rglob("*") if p.is_file()} == before


def test_the_last_n_days_only(tmp_path, capsys):
    b = life(tmp_path)
    assert (
        hs.main(["--box", str(b), "--days", "1", "--now", "2026-10-24T12:00:00Z"]) == 0
    )
    out = capsys.readouterr().out
    assert "2026-10-23" not in out and "2026-10-24" in out
    assert (
        hs.main(["--box", str(b), "--days", "1", "--now", "2026-11-30T00:00:00Z"]) == 42
    )
    assert "Nothing on the record in that window." in capsys.readouterr().out


def test_a_row_of_another_kind_is_named_not_guessed(tmp_path):
    b = life(tmp_path)
    hs.kernel.append(b, "2026-10-25T00:00:00Z", "verdict", who="ci", gate="lint")
    rows, _ = hs.kernel.read(b / "record.jsonl")
    assert hs.sentences(b, rows)[-1] == (
        "2026-10-25T00:00:00Z",
        "A verdict row, written by ci.",
    )


def test_echo_only_and_ordinals():
    rows = [
        {
            "kind": "bite",
            "bite_key": "a",
            "served": [{"where": "f:1", "echo": True}],
            "ts": "2026-01-01T00:00:00Z",
        }
    ]
    assert (
        hs.sentences(Path("."), rows)[0][1]
        == "You asked a question. Your files only asked it back."
    )
    assert [hs.nth(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 111)] == [
        "1st",
        "2nd",
        "3rd",
        "4th",
        "11th",
        "12th",
        "13th",
        "21st",
        "22nd",
        "23rd",
        "111th",
    ]
    looked = [{"kind": "out", "ts": "2026-01-01T00:00:00Z"}]  # a row with no count kept
    assert (
        hs.sentences(Path("."), looked)[0][1]
        == "You looked at what was waiting: nothing."
    )
    many = [{"where": f"f{i}:1"} for i in range(5)]
    assert hs.places(many) == "f0:1, f1:1, f2:1 and 2 more"


def test_a_broken_record_is_refused(tmp_path, capsys):
    b = life(tmp_path)
    rec = b / "record.jsonl"
    rec.write_bytes(rec.read_bytes().replace(b'"bite"', b'"bitE"', 1))
    assert hs.main(["--box", str(b)]) == 2
    assert "doesn't verify" in capsys.readouterr().err


def test_a_bad_command_line_says_how_to_run_it(tmp_path, capsys):
    b = life(tmp_path)
    for argv in (
        [],
        ["--box"],
        ["--box", str(b), "--days", "x"],
        ["--box", str(b), "more"],
    ):
        assert hs.main(argv) == 2
    assert hs.main(["--box", str(tmp_path)]) == 2
    assert hs.main(["--box", str(b), "--days", "1", "--now", "soon"]) == 2


def test_a_changed_check_is_said_in_counts():
    rows = [
        {
            "kind": "changed",
            "first": True,
            "files": {"a": "1", "b": "2"},
            "ts": "2026-01-01T00:00:00Z",
        },
        {
            "kind": "changed",
            "new": {"c": "3"},
            "edited": {},
            "deleted": ["a", "b"],
            "ts": "2026-01-02T00:00:00Z",
        },
        {
            "kind": "changed",
            "new": {},
            "edited": {},
            "deleted": [],
            "ts": "2026-01-03T00:00:00Z",
        },
    ]
    said = [s for _, s in hs.sentences(Path("."), rows)]
    assert said == [
        "You fingerprinted your folder: 2 files.",
        "You checked what changed in your folder: 1 new, 2 deleted.",
        "You checked what changed in your folder: nothing had.",
    ]
