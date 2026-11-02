"""hook-start: a SessionStart hook that tells the assistant what waits on the
person (suggestions, stale answers, dates coming up) as the JSON a hook reads;
a quiet box adds nothing; nothing is written, not even an out row; a record
that doesn't verify or a bad command line is refused."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_start.py"
KERNEL = HERE.parents[2] / "kernel.py"
#: what it tells comes from digest, whose stale and coming-up sections each
#: need that add-on beside it: each test holds it to whichever is here
BESIDE = {n: (HERE.parent / n).is_dir() for n in ("stale", "coming-up")}
NOW = ["--now", "2026-10-24T00:00:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def init(tmp_path: Path, files: dict[str, str]) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).write_text(text)
    b = tmp_path / "box"
    assert (
        k(
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "key"),
            *NOW,
        ).returncode
        == 0
    )
    return b, pile


def propose(
    tmp_path: Path,
    b: Path,
    question: str,
    path: str,
    answer: str,
    claim: str = "the note",
) -> None:
    served = json.loads(k("bite", "--box", str(b), *NOW, question).stdout)["served"]
    row = {
        "path": path,
        "data": answer,
        "cites": [served[0]["id"]],
        "claim": claim,
    }
    f = tmp_path / f"{path}.jsonl"
    f.write_text(json.dumps(row) + "\n")
    assert k("propose", "--box", str(b), "--file", str(f), *NOW).returncode == 42


def life(tmp_path: Path) -> Path:
    """One answer waiting, one approved then stale, a date coming up."""
    b, pile = init(
        tmp_path,
        {
            "car.txt": "The car insurance renews on 2026-10-30.\n",
            "bins.txt": "Bins go out on Thursday night.\n",
        },
    )
    propose(tmp_path, b, "when do the bins go out", "bins.md", "Thursday night")
    propose(tmp_path, b, "when does the car insurance renew", "car.md", "30 October")
    first = next(
        ln.split()[-1]
        for ln in k("out", "--box", str(b), *NOW).stdout.splitlines()
        if "waiting" in ln
    )
    assert k("seal", "--box", str(b), first, *NOW).returncode == 0
    (pile / "bins.txt").write_text("Bins go out on Wednesday now.\n")
    return b


def context(got: subprocess.CompletedProcess) -> str:
    out = json.loads(got.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "SessionStart"
    return out["additionalContext"]


def test_what_waits_is_told_as_the_json_a_session_start_hook_reads(tmp_path):
    got = run("--box", str(life(tmp_path)), *NOW)
    assert got.returncode == 0, got.stderr
    text = context(got)
    assert "1 suggestion waiting for their approval" in text
    assert "only the person approves, and an assistant never does" in text
    assert "30 October (why: the note)" in text
    assert ("1 approved answer is stale" in text) == BESIDE["stale"]
    assert ("Coming up (next 14 days): 2026-10-30 car.txt:1" in text) == BESIDE[
        "coming-up"
    ]


def test_the_days_window_decides_what_is_coming_up(tmp_path):
    b = life(tmp_path)
    six = "Coming up" in context(run("--box", str(b), "--days", "6", *NOW))
    assert six == BESIDE["coming-up"]
    assert "Coming up" not in context(run("--box", str(b), "--days", "5", *NOW))


def test_a_quiet_box_prints_nothing_at_all(tmp_path):
    b, _ = init(tmp_path, {"garden.txt": "Tomatoes want six hours of sun.\n"})
    got = run("--box", str(b), *NOW)
    assert got.returncode == 0 and got.stdout == "" and got.stderr == ""


def test_many_waiting_are_counted_and_only_the_first_few_shown(tmp_path):
    b, _ = init(
        tmp_path,
        {f"f{i}.txt": f"Fact number {i} about topic{i} is here.\n" for i in range(7)},
    )
    for i in range(7):
        propose(
            tmp_path, b, f"fact number {i} about topic{i}", f"a{i}.md", f"answer {i}"
        )
    text = context(run("--box", str(b), *NOW))
    assert (
        "7 suggestions waiting" in text
        and text.count("\n  - answer") == 5
        and "and 2 more" in text
    )


def test_it_writes_nothing_not_even_an_out_row(tmp_path):
    b = life(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(b), *NOW)
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_a_record_that_does_not_verify_adds_nothing_and_says_why(tmp_path):
    b = life(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("car.txt", "car.tzt", 1))
    got = run("--box", str(b), *NOW)
    assert got.returncode == 2 and got.stdout == "" and "refused:" in got.stderr


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b, _ = init(tmp_path, {"a.txt": "x\n"})
    for argv in ([], ["--box"], ["--box", str(b), "stray"], ["--box", str(b), "--days", "x"],
                 ["--box", str(b), "--now", "yesterday"], ["--box", str(tmp_path)]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, argv
    assert "hook_start.py" in run().stderr


def test_a_long_answer_and_a_long_reason_are_cut_short(tmp_path):
    b, _ = init(tmp_path, {"a.txt": "Tomatoes want six hours of sun every day.\n"})
    propose(
        tmp_path,
        b,
        "how much sun do tomatoes want",
        "sun.md",
        "A" * 200,
        claim="because " + "reason " * 30,
    )
    text = context(run("--box", str(b), *NOW))
    assert "A" * 79 + "…" in text and "A" * 80 not in text
    why = ("because " + "reason " * 30).split()
    assert f"(why: {' '.join(why)[:59]}…)" in text
