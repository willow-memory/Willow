"""cursor-chats: ordered spoken turns from a chat store; system, tools and
reasoning left out; the original store untouched."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "cursor_chats.py"


def _varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def field(num: int, payload: bytes) -> bytes:
    return _varint(num << 3 | 2) + _varint(len(payload)) + payload


def node(*fields: bytes) -> bytes:
    return b"".join(fields)


def put(rows: dict[str, bytes], data: bytes) -> bytes:
    """Store a blob under its content hash; return the 32-byte id."""
    ident = hashlib.sha256(data).digest()
    rows[ident.hex()] = data
    return ident


def msg(rows, role, content) -> bytes:
    return put(rows, json.dumps({"role": role, "content": content}).encode())


def make_store(path: Path, meta: dict | None, rows: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE blobs (id TEXT PRIMARY KEY, data BLOB)")
    con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    con.executemany("INSERT INTO blobs VALUES (?, ?)", rows.items())
    if meta is not None:
        con.execute(
            "INSERT INTO meta VALUES ('0', ?)", (json.dumps(meta).encode().hex(),)
        )
    con.commit()
    con.close()


def chat_store(path: Path, root_ok: bool = True) -> None:
    """system, user, assistant(+tool call), tool result, user, assistant,
    with the second half reached through a child node (field 13)."""
    rows: dict[str, bytes] = {}
    sysm = msg(rows, "system", "SYSTEMPROMPT")
    u1 = msg(rows, "user", [{"type": "text", "text": "When is the dentist?"}])
    a1 = msg(
        rows,
        "assistant",
        [
            {"type": "redacted-reasoning", "data": "HIDDENTHOUGHT"},
            {"type": "text", "text": "Let me look."},
            {"type": "tool-call", "toolName": "Grep", "args": {}},
        ],
    )
    t1 = msg(rows, "tool", [{"type": "tool-result", "result": "TOOLRESULT"}])
    u2 = msg(rows, "user", "Thanks, and the vet?")
    a2 = msg(rows, "assistant", "Tuesday at 3.")
    child = put(rows, node(field(1, u2), field(3, b"\x01"), field(1, a2)))
    other = put(rows, node(field(1, b"\x07" * 3)))  # a node nobody links
    root = node(
        field(1, sysm),
        field(1, u1),
        field(1, a1),
        field(1, t1),
        field(5, b"cli America/Denver"),
        field(8, other),
        field(13, child),
    )
    root_id = put(rows, root).hex()
    meta = {
        "agentId": "chat-0001",
        "latestRootBlobId": root_id if root_ok else "00" * 32,
        "name": "Dentist  visit",
        "createdAt": 1788174000000,
        "lastUsedModel": "some-model",
    }
    make_store(path, meta, rows)


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


def test_turns_follow_the_root_and_leave_out_system_tools_and_reasoning(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    chat_store(folder / "proj" / "chat" / "store.db")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 0"
    text = (to / "proj" / "chat" / "store.db.txt").read_text(encoding="utf-8")
    assert text == (
        "chat chat-0001\n"
        "name: Dentist visit\n"
        "started: 2026-08-31T11:00:00Z\n"
        "model: some-model\n"
        "4 turns\n\n"
        "1  you\nWhen is the dentist?\n\n"
        "2  assistant\nLet me look.\n\n"
        "3  you\nThanks, and the vet?\n\n"
        "4  assistant\nTuesday at 3.\n"
    )
    for hidden in ("SYSTEMPROMPT", "HIDDENTHOUGHT", "TOOLRESULT", "Grep"):
        assert hidden not in text


def test_an_unreadable_root_says_so_and_lists_in_sqlite_order(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    chat_store(folder / "store.db", root_ok=False)
    assert mirror(folder, to).returncode == 0
    text = (to / "store.db.txt").read_text(encoding="utf-8")
    head = text.split("\n\n", 1)[0]
    assert "order: not found in the store" in head.splitlines()
    assert "4 turns" in head.splitlines()
    assert "SYSTEMPROMPT" not in text and "TOOLRESULT" not in text
    assert text.count("Tuesday at 3.") == 1


def test_a_root_that_is_not_a_protobuf_is_not_ordered(tmp_path):
    rows: dict[str, bytes] = {}
    msg(rows, "user", "hello there")
    root_id = put(rows, b"\xff\xff\xff\xff").hex()
    make_store(
        tmp_path / "f" / "store.db",
        {"agentId": "c", "latestRootBlobId": root_id},
        rows,
    )
    assert mirror(tmp_path / "f", tmp_path / "m").returncode == 0
    text = (tmp_path / "m" / "store.db.txt").read_text(encoding="utf-8")
    assert "order: not found in the store" in text and "1  you\nhello there" in text


def test_no_meta_and_not_a_chat_are_skipped_and_counted(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    chat_store(folder / "good" / "store.db")
    rows: dict[str, bytes] = {}
    msg(rows, "user", "no header here")
    make_store(folder / "nometa" / "store.db", None, rows)
    (folder / "plain" / "store.db").parent.mkdir()
    con = sqlite3.connect(folder / "plain" / "store.db")
    con.execute("CREATE TABLE notes (a TEXT)")
    con.commit()
    con.close()
    (folder / "text" / "store.db").parent.mkdir()
    (folder / "text" / "store.db").write_text("not sqlite at all", encoding="utf-8")
    (folder / ".hidden").mkdir()
    chat_store(folder / ".hidden" / "store.db")
    got = mirror(folder, to)
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 3"
    made = sorted(p.relative_to(to).as_posix() for p in to.rglob("*") if p.is_file())
    assert made == ["good/store.db.txt"]


def test_nothing_readable_exits_42(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "store.db").write_bytes(b"junk")
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 1"


def test_the_original_store_is_byte_identical_and_two_runs_agree(tmp_path):
    folder = tmp_path / "f"
    chat_store(folder / "a" / "store.db")
    before = snapshot(folder)
    first, second = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, first).returncode == 0
    assert mirror(folder, second).returncode == 0
    assert snapshot(folder) == before
    assert snapshot(first) == snapshot(second)


def test_a_bad_command_line_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and "refused:" in got.stderr
    assert run(SCRIPT).returncode == 2
    assert "cursor_chats.py" in run(SCRIPT, "mirror", "--from", tmp_path).stderr
    folder = tmp_path / "f"
    chat_store(folder / "store.db")
    before = snapshot(folder)
    got = mirror(folder, folder / "out")
    assert got.returncode == 2 and snapshot(folder) == before
