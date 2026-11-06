"""assistant-scores: each assistant's suggestions counted by who, where and
settings together, sealed, declined or waiting, from the record alone."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "assistant_scores.py"
NOW = ["--now", "2026-11-06T00:00:00Z"]
URL = "http://127.0.0.1:11434/v1"
LOW = f"qwen3:8b at {URL} (temperature 0, seed 0, reasoning low) answered from 1 of the 1 passages served"  # fmt: skip
NONE = f"qwen3:8b at {URL} (temperature 0, seed 0) answered from 1 of the 1 passages served"  # fmt: skip
OLD = f"gemma at {URL} answered from 1 of the 1 passages served"

spec = importlib.util.spec_from_file_location("assistant_scores", SCRIPT)
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)


def k(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv), *NOW],
                          capture_output=True, text=True)  # fmt: skip


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    assert (
        k("init", "--box", b, "--pile", pile, "--key", tmp_path / "key").returncode == 0
    )
    return b


def suggest(b: Path, claim: str, n: int) -> str:
    """One suggestion under `claim`, its own answer `n`, as a proposer makes it."""
    got = json.loads(k("bite", "--box", b, "how much sun do tomatoes want").stdout)
    row = {"path": f"answers/a{n}.md", "data": f"Six hours, {n} [1].\n",
           "cites": [got["served"][0]["id"]], "claim": claim}  # fmt: skip
    f = b.parent / f"s{n}.jsonl"
    f.write_text(json.dumps(row) + "\n")
    out = k("propose", "--box", b, "--file", f).stdout
    assert out.startswith("pass"), out
    return out.split()[1]


def test_one_model_at_two_settings_is_two_assistants(tmp_path):
    b = box(tmp_path)
    low = [suggest(b, LOW, n) for n in range(6)]
    none = [suggest(b, NONE, n) for n in range(6, 9)]
    for s in low[:4] + none[:1]:
        assert k("seal", "--box", b, s).returncode == 0
    assert k("decline", "--box", b, low[4]).returncode == 0
    got = run("--box", b)
    assert got.returncode == 0, got.stderr
    assert (
        got.stdout.splitlines()
        == [
            "assistant-scores: populated, 9 suggestions from 2 assistants, 6 decided by you",
            "## assistants",
            f"  qwen3:8b at {URL} (temperature 0, seed 0, reasoning low)  4 sealed, 1 declined, 1 waiting; 4 of the 5 decided sealed",  # fmt: skip
            f"  {'qwen3:8b at ' + URL + ' (temperature 0, seed 0)':<60}  1 sealed, 0 declined, 2 waiting; 1 of the 1 decided sealed",  # fmt: skip
        ]
    )
    doc = json.loads(run("--box", b, "--json").stdout)
    assert sc.report_text(doc) == got.stdout.rstrip("\n"), "--json is the same report"


def test_an_old_claim_yours_and_a_file_not_as_proposed_are_each_said(tmp_path):
    b = box(tmp_path)
    suggest(b, OLD, 0)
    suggest(b, "mine", 1)
    suggest(b, "my own too", 2)
    gone = suggest(b, NONE, 3)
    (b / "proposals" / f"{gone[9:]}.json").write_text('{"claim": "changed"}')
    got = run("--box", b).stdout.splitlines()
    w = len(f"gemma at {URL} (settings not said)")  # one where column, every group
    assert got[0] == "assistant-scores: populated, 1 suggestion from 1 assistant, 0 decided by you"  # fmt: skip
    assert (
        got[2]
        == f"  gemma at {URL} (settings not said)  0 sealed, 0 declined, 1 waiting"
    )
    assert (
        got[3:5]
        == [
            "## no assistant named",
            f"  {'proposals':<{w}}  2 suggestions whose claim names no assistant: yours, or another's",  # fmt: skip
        ]
    )
    assert got[5:] == [
        "## not read",
        f"  {gone[:21] + '…':<{w}}  its proposal file is not the bytes proposed",
    ]


def test_only_a_suggestion_naming_no_assistant_is_populated_not_empty(tmp_path):
    b = box(tmp_path)
    suggest(b, "mine", 0)
    got = run("--box", b).stdout.splitlines()
    assert (
        got[0]
        == "assistant-scores: populated, no assistant's suggestion is on the record"
    )
    assert got[1] == "## no assistant named" and "1 suggestion whose" in got[2]


def test_a_suggestion_proposed_twice_counts_once(tmp_path):
    b = box(tmp_path)
    first = suggest(b, NONE, 0)
    assert suggest(b, NONE, 0) == first
    assert "1 suggestion from 1 assistant" in run("--box", b).stdout


def test_a_box_with_no_suggestion_is_empty_and_zero(tmp_path):
    b = box(tmp_path)
    got = run("--box", b)
    assert got.returncode == 0
    assert got.stdout == "assistant-scores: empty, no suggestion is on the record\n"
    doc = json.loads(run("--box", b, "--json").stdout)
    assert doc == {"addon": "assistant-scores", "state": "empty",
                   "said": "no suggestion is on the record", "groups": []}  # fmt: skip


def test_it_reads_and_never_writes(tmp_path):
    b = box(tmp_path)
    suggest(b, LOW, 0)
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    assert run("--box", b).returncode == 0
    assert {p: p.read_bytes() for p in b.rglob("*") if p.is_file()} == before


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    b = box(tmp_path)
    suggest(b, LOW, 0)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("proposal", "proposals", 1))
    got = run("--box", b)
    assert got.returncode == 2 and got.stderr.startswith(
        "refused: the record doesn't verify"
    )


def test_a_bad_command_line_or_no_box_is_refused(tmp_path):
    for argv in ([], ["--box"], ["--box", ""], ["--box", "a", "b"], ["--from", "a"]):
        got = run(*argv)
        assert got.returncode == 2 and "assistant_scores.py" in got.stderr, argv
    got = run("--box", tmp_path)
    assert got.returncode == 2 and got.stderr.startswith("refused: ")
