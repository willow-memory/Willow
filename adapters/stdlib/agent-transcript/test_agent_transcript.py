"""agent-transcript: numbered spoken turns; tools and thinking left out;
the same folder gives the same bytes."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "agent_transcript.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-31T00:00:00Z"]

CLAUDE = (
    "\n".join(
        [
            json.dumps(
                {
                    "type": "user",
                    "sessionId": "sess-1",
                    "origin": {"kind": "human"},
                    "message": {"role": "user", "content": "When is the dentist?"},
                }
            ),
            json.dumps(
                {
                    "type": "assistant",
                    "sessionId": "sess-1",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "thinking", "thinking": "secret"},
                            {"type": "text", "text": "Tuesday at 3."},
                            {"type": "tool_use", "name": "Bash", "input": {}},
                        ],
                    },
                }
            ),
            json.dumps(
                {
                    "type": "user",
                    "sessionId": "sess-1",
                    "message": {
                        "role": "user",
                        "content": [
                            {"type": "tool_result", "content": "a key sk-secret"}
                        ],
                    },
                }
            ),
        ]
    )
    + "\n"
)

CURSOR = (
    "\n".join(
        [
            json.dumps(
                {
                    "role": "user",
                    "message": {
                        "content": [{"type": "text", "text": "Pick up the pile."}]
                    },
                }
            ),
            json.dumps(
                {
                    "role": "assistant",
                    "message": {
                        "content": [
                            {"type": "text", "text": "Pile 2 is the transcripts."},
                            {"type": "tool_use", "name": "Read", "input": {}},
                        ]
                    },
                }
            ),
        ]
    )
    + "\n"
)


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(SCRIPT, "mirror", "--from", folder, "--to", to)


def snapshot(folder: Path) -> dict[str, bytes]:
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def test_spoken_turns_are_numbered_and_tools_are_left_out(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "sess.jsonl").write_text(CLAUDE, encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "sess.jsonl.txt").read_text(encoding="utf-8")
    assert text.startswith("session sess-1\n2 turns\n")
    assert "1  you\nWhen is the dentist?" in text
    assert "2  assistant\nTuesday at 3." in text
    assert "secret" not in text and "sk-secret" not in text and "Bash" not in text


def test_a_cursor_session_is_read_the_same_way(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    (folder / "proj").mkdir(parents=True)
    (folder / "proj" / "chat.jsonl").write_text(CURSOR, encoding="utf-8")
    assert mirror(folder, to).returncode == 0
    text = (to / "proj" / "chat.jsonl.txt").read_text(encoding="utf-8")
    assert "1  you\nPick up the pile." in text
    assert "2  assistant\nPile 2 is the transcripts." in text
    assert "Read" not in text


def test_not_a_session_is_skipped_and_hidden_parts_are_not_read(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "sess.jsonl").write_text(CLAUDE, encoding="utf-8")
    (folder / "notes.jsonl").write_text('{"hello": 1}\n', encoding="utf-8")
    (folder / ".hidden").mkdir()
    (folder / ".hidden" / "sess.jsonl").write_text(CLAUDE, encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 1"
    made = sorted(p.relative_to(to).as_posix() for p in to.rglob("*") if p.is_file())
    assert made == ["sess.jsonl.txt"]


def test_nothing_readable_exits_42(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "x.jsonl").write_text("{not json\n", encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 1"


def test_two_runs_give_identical_bytes_and_originals_are_unchanged(tmp_path):
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "sess.jsonl").write_text(CLAUDE, encoding="utf-8")
    before = snapshot(folder)
    first, second = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, first).returncode == 0
    assert mirror(folder, second).returncode == 0
    assert {k: hashlib.sha256(v).hexdigest() for k, v in snapshot(first).items()} == {
        k: hashlib.sha256(v).hexdigest() for k, v in snapshot(second).items()
    }
    assert snapshot(folder) == before


def test_kernel_serves_a_turn_from_the_mirror(tmp_path):
    folder, to, box, key = (
        tmp_path / "f",
        tmp_path / "m",
        tmp_path / "box",
        tmp_path / "k",
    )
    folder.mkdir()
    (folder / "sess.jsonl").write_text(CLAUDE, encoding="utf-8")
    assert mirror(folder, to).returncode == 0
    init = run(KERNEL, "init", "--box", box, "--pile", to, "--key", key, *NOW)
    assert init.returncode == 0, init.stderr
    got = run(KERNEL, "bite", "--box", box, *NOW, "when is the dentist")
    assert got.returncode in (0, 42), got.stderr
    assert "Tuesday at 3." in got.stdout or "When is the dentist?" in got.stdout


def test_a_bad_command_line_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and "refused:" in got.stderr
    folder = tmp_path / "f"
    folder.mkdir()
    (folder / "sess.jsonl").write_text(CLAUDE, encoding="utf-8")
    before = snapshot(folder)
    got = mirror(folder, folder / "out")
    assert got.returncode == 2 and snapshot(folder) == before
