"""agent-transcript: numbered spoken turns; tools and thinking left out;
the same folder gives the same bytes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
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


def held_mirror(mod, folder, to):
    """mirror() called in-process with the command line it would have had,
    since the guard holds a write to the --to it reads from sys.argv."""
    saved = sys.argv
    sys.argv = [str(SCRIPT), "mirror", "--from", str(folder), "--to", str(to)]
    try:
        return mod.mirror(folder, to)
    finally:
        sys.argv = saved


def test_spoken_turns_are_numbered_and_tools_are_left_out(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "sess.jsonl").write_text(CLAUDE, encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "sess.jsonl.txt").read_text(encoding="utf-8")
    assert text.startswith("session sess-1\ntime: not in the file\n2 turns\n")
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


def _line(who, text, **extra):
    msg = {"role": who, "content": text}
    return json.dumps({"type": who, "sessionId": "s", "message": msg, **extra})


def _header(tmp_path, lines) -> list[str]:
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "s.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert mirror(folder, to).returncode == 0
    text = (to / "s.jsonl.txt").read_text(encoding="utf-8")
    return text.split("\n\n")[0].splitlines()


def test_timestamps_give_started_and_ended(tmp_path):
    got = _header(
        tmp_path,
        [
            _line("user", "hi", timestamp="2026-07-05T18:48:00.123Z"),
            _line("assistant", "yo", timestamp="2026-07-05T18:49:30.000Z"),
        ],
    )
    assert got == [
        "session s",
        "started: 2026-07-05T18:48:00.123Z",
        "ended: 2026-07-05T18:49:30.000Z",
        "2 turns",
    ]


def test_earliest_and_latest_even_when_lines_are_out_of_order(tmp_path):
    got = _header(
        tmp_path,
        [
            _line("user", "a", timestamp="2026-07-05T10:00:00Z"),
            _line("assistant", "b", timestamp="2026-07-06T10:00:00Z"),
            _line("user", "c", timestamp="2026-07-04T10:00:00Z"),
            json.dumps({"type": "system", "timestamp": "2026-07-05T11:00:00Z"}),
        ],
    )
    assert "started: 2026-07-04T10:00:00Z" in got
    assert "ended: 2026-07-06T10:00:00Z" in got


def test_a_malformed_timestamp_is_ignored_not_fatal(tmp_path):
    got = _header(
        tmp_path,
        [
            _line("user", "a", timestamp="yesterday-ish"),
            _line("assistant", "b", timestamp="2026-07-05T10:00:00Z"),
            _line("user", "c", timestamp=12345),
            _line("user", "d", timestamp="2026-13-45T99:00:00Z"),
        ],
    )
    assert got[1:3] == [
        "started: 2026-07-05T10:00:00Z",
        "ended: 2026-07-05T10:00:00Z",
    ]


def test_only_malformed_timestamps_means_not_in_the_file(tmp_path):
    got = _header(tmp_path, [_line("user", "a", timestamp="soon")])
    assert got == ["session s", "time: not in the file", "1 turns"]


def test_a_cursor_timestamp_tag_is_the_start_as_written(tmp_path):
    tag = "<timestamp>Sunday, Jul 5, 2026, 12:48 PM (UTC-6)</timestamp>"
    later = "<timestamp>Monday, Jul 6, 2026, 1:00 PM (UTC-6)</timestamp>"
    got = _header(
        tmp_path,
        [
            _line("user", f"{tag}\nplease"),
            _line("assistant", "ok"),
            _line("user", later),
        ],
    )
    assert got == [
        "session s",
        "started: Sunday, Jul 5, 2026, 12:48 PM (UTC-6) (from the text)",
        "3 turns",
    ]


def test_a_tag_in_an_assistant_turn_is_not_a_time(tmp_path):
    got = _header(
        tmp_path,
        [_line("user", "q"), _line("assistant", "<timestamp>Monday</timestamp>")],
    )
    assert "time: not in the file" in got


def test_iso_timestamps_win_over_a_tag(tmp_path):
    got = _header(
        tmp_path,
        [
            _line(
                "user",
                "<timestamp>Monday</timestamp>",
                timestamp="2026-07-05T10:00:00Z",
            )
        ],
    )
    assert got[1] == "started: 2026-07-05T10:00:00Z"
    assert not any("from the text" in g for g in got)


def test_modification_time_is_never_used(tmp_path):
    import os

    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    path = folder / "s.jsonl"
    path.write_text(_line("user", "hi") + "\n", encoding="utf-8")
    os.utime(path, (1_000_000_000, 1_000_000_000))
    assert mirror(folder, to).returncode == 0
    text = (to / "s.jsonl.txt").read_text(encoding="utf-8")
    assert "time: not in the file" in text and "2001" not in text


# ── long sessions: written in parts, under the kernel's limit ───────────────
def load():
    """The module itself, so a test can lower PART instead of making 900 KB."""
    spec = importlib.util.spec_from_file_location("agent_transcript_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def session(turns: list[str], name: str = "long-1") -> str:
    """A made-up session: you and the assistant, turn about."""
    lines = []
    for i, text in enumerate(turns):
        who = "user" if i % 2 == 0 else "assistant"
        lines.append(
            json.dumps(
                {
                    "type": who,
                    "sessionId": name,
                    "timestamp": f"2026-10-31T09:00:{i % 60:02d}.000Z",
                    "message": {"role": who, "content": text},
                }
            )
        )
    return "\n".join(lines) + "\n"


def write_session(folder: Path, turns: list[str], name: str = "sess.jsonl") -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(session(turns), encoding="utf-8")


def in_order(to: Path) -> list[Path]:
    return sorted(to.iterdir(), key=lambda p: (len(p.name), p.name))


def numbered(text: str) -> list[int]:
    return [int(m) for m in re.findall(r"^(\d+)  (?:you|assistant)$", text, re.M)]


def test_a_session_that_fits_is_one_file_with_no_part_line(tmp_path):
    mod = load()
    folder, to = tmp_path / "f", tmp_path / "m"
    write_session(folder, ["one", "two"])
    assert held_mirror(mod, folder, to) == (1, 0)
    assert [p.name for p in to.iterdir()] == ["sess.jsonl.txt"]
    text = (to / "sess.jsonl.txt").read_text(encoding="utf-8")
    assert "part " not in text and text.startswith("session long-1\n")


def test_a_long_session_is_three_parts_each_under_the_limit(tmp_path, monkeypatch):
    mod = load()
    monkeypatch.setattr(mod, "PART", 700)  # a few turns to a part, not 900 KB
    folder, to = tmp_path / "f", tmp_path / "m"
    turns = [f"turn {i} " + "w" * 150 for i in range(1, 9)]
    write_session(folder, turns)
    assert held_mirror(mod, folder, to) == (1, 0)
    names = sorted(p.name for p in to.iterdir())
    assert names == ["sess.jsonl.2.txt", "sess.jsonl.3.txt", "sess.jsonl.txt"]
    texts = [
        (to / n).read_text(encoding="utf-8")
        for n in ("sess.jsonl.txt", "sess.jsonl.2.txt", "sess.jsonl.3.txt")
    ]
    header = (
        "session long-1\nstarted: 2026-10-31T09:00:00.000Z\n"
        "ended: 2026-10-31T09:00:07.000Z\n8 turns\n"
    )
    seen = []
    for n, text in enumerate(texts, 1):
        assert len(text.encode("utf-8")) <= 700
        assert text.startswith(header + f"part {n} of 3\n")
        seen += numbered(text)
    assert seen == list(range(1, 9))  # numbers go on across parts
    body = "".join(texts)
    where = [body.index(f"turn {i} ") for i in range(1, 9)]
    assert [body.count(f"turn {i} ") for i in range(1, 9)] == [1] * 8
    assert where == sorted(where)


def test_a_turn_longer_than_a_part_goes_on_at_a_line_end(tmp_path, monkeypatch):
    mod = load()
    monkeypatch.setattr(mod, "PART", 500)
    folder, to = tmp_path / "f", tmp_path / "m"
    big = "\n".join(f"line {i:03d} " + "x" * 20 for i in range(60))  # ~1.7 KB
    write_session(folder, ["first", big, "last"])
    assert held_mirror(mod, folder, to) == (1, 0)
    texts = [p.read_text(encoding="utf-8") for p in in_order(to)]
    assert len(texts) > 2
    assert all(len(t.encode("utf-8")) <= 500 for t in texts)
    body = "".join(texts)
    assert numbered(body) == [1, 2, 3]
    assert [body.count(f"line {i:03d} ") for i in range(60)] == [1] * 60
    for t in texts:  # whole lines only: none starts or ends mid-line
        for ln in t.splitlines():
            assert not ln.startswith("line") or ln.endswith("x" * 20)
    assert "last" in texts[-1] and "part 1 of" in texts[0]


def test_a_line_longer_than_a_part_is_cut_between_characters(tmp_path, monkeypatch):
    mod = load()
    monkeypatch.setattr(mod, "PART", 500)
    for lead in ("", "a", "ab", "abc"):  # moves where the cut lands in a character
        folder, to = tmp_path / f"f{len(lead)}", tmp_path / f"m{len(lead)}"
        long = lead + "日" * 400 + "é" * 300 + "🙂" * 50  # 2.2 KB, one line
        write_session(folder, ["go", long])
        assert held_mirror(mod, folder, to) == (1, 0)
        texts = []
        for p in in_order(to):
            raw = p.read_bytes()
            assert len(raw) <= 500
            texts.append(raw.decode("utf-8"))  # strict: no character was split
        assert len(texts) > 3
        body = "".join(texts)
        assert body.count("日") == 400 and body.count("é") == 300
        assert body.count("🙂") == 50 and body.count("�") == 0


def test_a_rerun_after_the_session_shortens_removes_only_the_stale_part(
    tmp_path, monkeypatch
):
    mod = load()
    monkeypatch.setattr(mod, "PART", 700)
    folder, to = tmp_path / "f", tmp_path / "m"
    write_session(folder, [f"turn {i} " + "w" * 150 for i in range(1, 9)])
    assert held_mirror(mod, folder, to) == (1, 0)
    assert (to / "sess.jsonl.3.txt").exists()
    other = {  # not this session's parts: left alone
        "sess2.jsonl.3.txt": b"another session's part",
        "sess.jsonl.3.txt.bak": b"a backup",
        "sess.jsonl.3.notes.txt": b"notes",
        "sess.jsonl.x.txt": b"not a part number",
    }
    for name, data in other.items():
        (to / name).write_bytes(data)
    (to / "sub").mkdir()
    (to / "sub" / "sess.jsonl.3.txt").write_bytes(b"same name, another folder")
    write_session(folder, [f"turn {i} " + "w" * 150 for i in range(1, 6)])
    assert held_mirror(mod, folder, to) == (1, 0)
    assert not (to / "sess.jsonl.3.txt").exists()
    assert (to / "sess.jsonl.2.txt").exists()
    for name, data in other.items():
        assert (to / name).read_bytes() == data
    assert (
        to / "sub" / "sess.jsonl.3.txt"
    ).read_bytes() == b"same name, another folder"
    first = snapshot(to)
    assert held_mirror(mod, folder, to) == (1, 0)
    assert snapshot(to) == first  # the same source gives the same files
    write_session(folder, ["one", "two"])  # now it fits: one file, no parts
    assert held_mirror(mod, folder, to) == (1, 0)
    assert not (to / "sess.jsonl.2.txt").exists()
    assert "part " not in (to / "sess.jsonl.txt").read_text(encoding="utf-8")


def test_a_line_is_cut_only_between_characters():
    spec = importlib.util.spec_from_file_location("agent_transcript_cut", SCRIPT)
    at = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(at)
    # "À" is C3 80: a cut at its second byte steps back to before it
    assert at._cut("a\u00c0b", 2) == ("a", "\u00c0b")
    # DEL (7F) is a whole character, not the tail of one: cut right there
    assert at._cut("ab\x7fc", 2) == ("ab", "\x7fc")
