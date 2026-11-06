"""stack-share: a stack sealed with the Forge comes out as a page to share,
each step with its card's line, its promises and why it is there; only what
the kernel proves sealed and standing is on it."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
NOW = ["--now", "2026-11-06T00:00:00Z"]
SENTENCE = "read my mail and tell me what is due"
STACK = (f"# {SENTENCE}\n\n## for “{SENTENCE}”\n"
         "- stack-share -- --box {box}\n- stack -- --box {box} --stack {box}.md\n")  # fmt: skip


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *argv], capture_output=True, text=True)  # fmt: skip


def share(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "stack_share.py"), *argv],
                          capture_output=True, text=True)  # fmt: skip


def subject(row: dict) -> str:
    keys = ("path", "data", "cites", "claim")
    canon = json.dumps({x: row[x] for x in keys}, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False)  # fmt: skip
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def proposed(box: Path, tmp: Path, asked: str, row: dict, seal: bool = True) -> str:
    """One proposal made under `asked`, as the forge add-on makes it, and
    sealed unless told not to; its subject."""
    k("bite", "--box", str(box), *NOW, asked)
    (tmp / "rows.jsonl").write_text(json.dumps(row, ensure_ascii=False) + "\n")
    got = k("propose", "--box", str(box), "--file", str(tmp / "rows.jsonl"), *NOW)
    assert got.returncode == 42 and got.stdout.startswith("pass "), (
        got.stdout + got.stderr
    )
    subj = subject(row)
    if seal:
        assert k("seal", "--box", str(box), subj, *NOW).returncode == 0
    return subj


def choice(sha: str | None = None) -> dict:
    # its own card and stack's, the one it uses: the cards a copy of it
    # alone has (alone.py), so the tests hold there too
    card = ROOT / "adapters/stdlib/stack/README.md"
    data = {"word": "due", "decision_type": "willow-due", "chose": "stack",
            "over": ["renewals"], "why": "the boiler isn't a subscription",
            "card": {"name": "stack", "where": "adapters/stdlib/stack/README.md",
                     "sha256": sha or hashlib.sha256(card.read_bytes()).hexdigest()}}  # fmt: skip
    return {"path": "forge/decisions/willow-due.json",
            "data": json.dumps(data, sort_keys=True, ensure_ascii=False), "cites": [],
            "claim": "for “due”: stack over renewals"}  # fmt: skip


STACK_ROW = {"path": "forge/stack.md", "data": STACK, "cites": [],
             "claim": "a stack: stack-share, stack"}  # fmt: skip


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "boiler.md").write_text("The boiler service is due on 2026-12-01.\n")
    b = tmp_path / "box"
    assert k("init", "--box", str(b), "--pile", str(pile), "--key",
             str(tmp_path / "key"), *NOW).returncode == 0  # fmt: skip
    return b


def test_a_sealed_stack_is_a_page_with_each_steps_card_promises_and_reason(tmp_path):
    b = box(tmp_path)
    proposed(b, tmp_path, "forge decision willow-due", choice())
    proposed(b, tmp_path, SENTENCE, STACK_ROW)
    got = share("--box", str(b))
    assert got.returncode == 0, got.stderr
    lines = got.stdout.splitlines()
    assert lines[0] == f"# {SENTENCE}"
    own = next(x for x in lines if x.startswith("| stack-share |"))
    assert "A stack you sealed with the Forge, written out to share" in own
    assert (
        "writes nothing; network none" in own and "your words reached it alone" in own
    )
    due = next(x for x in lines if x.startswith("| stack |"))
    assert "One page made from several add-ons run in the order you list them" in due
    assert "writes nothing; network none" in due
    assert "chosen for “due” over renewals: the boiler isn't a subscription |" in due
    # the stack itself, to run, and nothing of the folder
    assert (
        "- stack-share -- --box {box}\n- stack -- --box {box} --stack {box}.md\n```"
        in got.stdout
    )
    assert "2026-12-01" not in got.stdout and "boiler.md" not in got.stdout
    # the same words retyped choose it; other words are refused
    assert (
        share("--box", str(b), "--sentence", SENTENCE.upper() + "!").stdout
        == got.stdout
    )
    other = share("--box", str(b), "--sentence", "something else entirely")
    assert other.returncode == 2 and "no sealed stack" in other.stderr


def test_nothing_sealed_is_nothing_to_share(tmp_path):
    b = box(tmp_path)
    assert share("--box", str(b)).returncode == 42
    proposed(b, tmp_path, SENTENCE, STACK_ROW, seal=False)  # proposed, waiting
    got = share("--box", str(b))
    assert got.returncode == 42 and "nothing sealed to share" in got.stdout


def test_a_proposal_changed_after_its_seal_is_never_shared(tmp_path):
    b = box(tmp_path)
    subj = proposed(b, tmp_path, SENTENCE, STACK_ROW)
    path = b / "proposals" / f"{subj[9:]}.json"
    row = json.loads(path.read_text())
    path.write_text(json.dumps({**row, "data": row["data"] + "- send -- --all\n"}))
    assert share("--box", str(b)).returncode == 42


def test_an_unsealed_choice_is_no_reason_and_a_changed_card_is_said(tmp_path):
    b = box(tmp_path)
    proposed(b, tmp_path, "forge decision willow-due", choice(), seal=False)
    proposed(b, tmp_path, SENTENCE, STACK_ROW)
    due = [x for x in share("--box", str(b)).stdout.splitlines() if x.startswith("| stack |")]  # fmt: skip
    assert due and "your words reached it alone" in due[0]
    c = tmp_path / "c"
    c.mkdir()
    b = box(c)
    proposed(b, c, "forge decision willow-due", choice(sha="0" * 64))
    proposed(b, c, SENTENCE, STACK_ROW)
    assert "(its card has changed since)" in share("--box", str(b)).stdout


def test_a_step_with_no_card_here_says_so(tmp_path):
    b = box(tmp_path)
    row = {**STACK_ROW, "data": STACK + "- not-an-add-on -- --box {box}\n"}
    proposed(b, tmp_path, SENTENCE, row)
    line = next(x for x in share("--box", str(b)).stdout.splitlines()
                if x.startswith("| not-an-add-on |"))  # fmt: skip
    assert "no card here" in line


def test_a_bad_command_line_or_a_folder_that_isnt_a_box_is_refused(tmp_path):
    for argv in ([], ["--box"], ["--box", str(tmp_path), "--sentence"],
                 ["--box", str(tmp_path), "--words", "x"]):  # fmt: skip
        got = share(*argv)
        assert got.returncode == 2 and "stack_share.py" in got.stderr, argv
    got = share("--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_a_record_that_doesnt_verify_is_refused(tmp_path):
    b = box(tmp_path)
    proposed(b, tmp_path, SENTENCE, STACK_ROW)
    log = b / "record.jsonl"
    rows = log.read_text().splitlines()
    rows[0] = rows[0].replace("2026", "2025", 1)
    log.write_text("\n".join(rows) + "\n")
    got = share("--box", str(b))
    assert got.returncode == 2 and "doesn't verify" in got.stderr
