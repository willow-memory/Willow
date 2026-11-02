"""digest: what waits on the person, what went stale, what's coming up and
what keeps finding nothing, each section in one of three states; and it
writes nothing, not even an `out` row."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("digest", HERE / "digest.py")
dg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dg)
NOW = ["--now", "2026-10-24T00:00:00Z"]
TODAY = date(2026, 10, 24)
#: the add-ons two of its sections are read by: each test holds digest to
#: whichever is true here, so a copy with only some add-ons is checked too
BESIDE = {n: (HERE.parent / n).is_dir() for n in ("stale", "coming-up")}


def gone(name: str) -> dict:
    return {"state": "unreachable", "why": f"the {name} add-on isn't here", "items": []}


def k(*argv: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *argv], input=stdin,
                          capture_output=True, text=True)  # fmt: skip


def life(tmp_path: Path) -> Path:
    """A folder with a date coming up, an answer approved then stale, one
    waiting, and a question asked twice that nothing holds."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "car.txt").write_text("The car insurance renews on 2026-10-30.\n")
    (pile / "bins.txt").write_text("Bins go out on Thursday night.\n")
    b = tmp_path / "box"
    assert k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW).returncode == 0  # fmt: skip
    for q, path, answer in (("when do the bins go out", "bins.md", "Thursday night"),
                            ("when does the car insurance renew", "car.md", "30 October")):  # fmt: skip
        served = json.loads(k("bite", "--box", str(b), *NOW, q).stdout)["served"]
        row = {
            "path": path,
            "data": answer,
            "cites": [served[0]["id"]],
            "claim": "the note",
        }
        sugg = tmp_path / f"{path}.jsonl"
        sugg.write_text(json.dumps(row) + "\n")
        got = k("propose", "--box", str(b), "--file", str(sugg), *NOW)
        assert got.returncode == 42, got.stdout + got.stderr
    first = next(ln.split()[-1] for ln in k("out", "--box", str(b), *NOW).stdout.splitlines() if "waiting" in ln)  # fmt: skip
    assert k("seal", "--box", str(b), first, *NOW).returncode == 0
    (pile / "bins.txt").write_text(
        "Bins go out on Wednesday now.\n"
    )  # its source moved
    for _ in range(2):
        k("bite", "--box", str(b), *NOW, "where is the passport")
    return b


def test_each_section_shows_what_it_found(tmp_path):
    doc = dg.digest(life(tmp_path), TODAY)
    assert [w["answer"] for w in doc["waiting"]["items"]] == ["30 October"]
    if BESIDE["stale"]:
        assert [e["data"] for e in doc["stale"]["items"]] == ["Thursday night"]
    else:
        assert doc["stale"] == gone("stale")
    if BESIDE["coming-up"]:
        assert [(c["date"], c["where"]) for c in doc["coming"]["items"]] == [
            ("2026-10-30", "car.txt:1")
        ]
    else:
        assert doc["coming"] == gone("coming-up")
    assert doc["again"]["items"] == [2]
    assert doc["waiting"]["state"] == doc["again"]["state"] == "populated"
    assert dg.code_of(doc) == 42


def test_it_writes_nothing_not_even_an_out_row(tmp_path, capsys):
    b = life(tmp_path)
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    assert dg.main(["--box", str(b), *NOW]) == 42
    assert {p: p.read_bytes() for p in b.rglob("*") if p.is_file()} == before
    out = capsys.readouterr().out
    for title in (
        "Waiting for you",
        "Gone stale",
        "Coming up (next 14 days)",
        "Asked again",
    ):
        assert title in out
    assert "2 questions" not in out and "1 question asked more than once" in out
    assert "approve: python kernel.py seal --box BOX proposal:" in out


def test_nothing_is_said_as_nothing(tmp_path, capsys):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.txt").write_text("Nothing dated here.\n")
    b = tmp_path / "box"
    k(
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "key"),
        *NOW,
    )
    assert dg.main(["--box", str(b), *NOW]) == 0
    out = capsys.readouterr().out
    assert "Nothing is waiting for your approval." in out
    assert ("Every approved answer's sources still hold." in out) == BESIDE["stale"]
    assert ("Nothing dated in that window." in out) == BESIDE["coming-up"]
    assert ("couldn't look: the coming-up add-on isn't here" in out) != BESIDE[
        "coming-up"
    ]
    assert "No question has gone unanswered twice." in out


def test_a_deleted_add_on_is_couldnt_look_and_the_rest_still_show(
    tmp_path, monkeypatch, capsys
):
    b = life(tmp_path)
    fake = tmp_path / "stdlib"
    fake.mkdir()
    if BESIDE["coming-up"]:
        shutil.copytree(HERE.parent / "coming-up", fake / "coming-up")
    monkeypatch.setattr(dg, "STDLIB", fake)
    doc = dg.digest(b, TODAY)
    assert doc["stale"] == gone("stale")
    assert doc["coming"]["state"] == (
        "populated" if BESIDE["coming-up"] else "unreachable"
    )
    assert doc["waiting"]["state"] == "populated"
    assert dg.code_of(doc) == 42
    print(dg.render(doc, 14))
    assert "couldn't look: the stale add-on isn't here" in capsys.readouterr().out


def test_the_window_is_the_days_asked(tmp_path):
    b = life(tmp_path)
    five, six = (dg.digest(b, TODAY, n)["coming"]["state"] for n in (5, 6))
    if BESIDE["coming-up"]:
        assert (five, six) == ("empty", "populated")
    else:
        assert five == six == "unreachable"


def test_an_answered_question_asked_again_is_not_counted(tmp_path):
    b = life(tmp_path)
    for _ in range(3):
        k("bite", "--box", str(b), *NOW, "when does the car insurance renew")
    assert dg.digest(b, TODAY)["again"]["items"] == [2]


def test_a_broken_record_is_refused(tmp_path, capsys):
    b = life(tmp_path)
    rec = b / "record.jsonl"
    rec.write_bytes(rec.read_bytes().replace(b'"bite"', b'"bitE"', 1))
    assert dg.main(["--box", str(b), *NOW]) == 2
    assert "refused" in capsys.readouterr().err


def test_a_bad_command_line_says_how_to_run_it(tmp_path, capsys):
    for argv in (
        [],
        ["--box"],
        ["--box", str(tmp_path), "--days", "x"],
        ["--box", str(tmp_path), "more"],
    ):
        assert dg.main(argv) == 2
    assert dg.main(["--box", str(tmp_path)]) == 2
    assert "not a kernel box" in capsys.readouterr().err
    b = life(tmp_path)
    assert dg.main(["--box", str(b), "--now", "soon"]) == 2


def test_a_suggestion_you_declined_no_longer_waits(tmp_path):
    b = life(tmp_path)
    subj = dg.digest(b, TODAY)["waiting"]["items"][0]["subject"]
    assert k("decline", "--box", str(b), subj, *NOW).returncode == 0
    assert dg.digest(b, TODAY)["waiting"] == {"state": "empty", "items": []}
