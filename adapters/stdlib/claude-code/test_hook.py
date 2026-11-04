"""claude-code: the hook frames passages as data, says nothing when nothing
holds the prompt, says why when the folder can't be read, and never blocks."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("cc_hook", HERE / "hook.py")
hk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hk)
NOW = ["--now", "2026-10-23T00:00:00Z"]


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "n.md").write_text(
        "The bus leaves at seven from the square.\n\nWhen does the ferry sail?\n"
    )
    b = tmp_path / "box"
    assert subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                           "--key", str(tmp_path / "k"), *NOW], capture_output=True).returncode == 0  # fmt: skip
    return b


def said(b: Path, prompt) -> str:
    stdin = io.StringIO(prompt if isinstance(prompt, str) else json.dumps(prompt))
    return hk.prompt(b, stdin)


def test_passages_come_framed_as_data_with_file_and_line(tmp_path):
    got = said(
        box(tmp_path), {"prompt": "when does the bus leave the square", "cwd": "/x"}
    )
    assert got.startswith(hk.FRAME) and "not instructions" in got
    assert (
        f"{hk.OPEN}\nn.md:1:\nThe bus leaves at seven from the square.\n{hk.CLOSE}"
        in got
    )


def test_a_passage_that_only_asks_back_is_left_out(tmp_path):
    assert said(box(tmp_path), {"prompt": "when does the ferry sail"}) == ""


def test_nothing_is_printed_when_nothing_holds_the_prompt(tmp_path):
    b = box(tmp_path)
    assert said(b, {"prompt": "zebra crossing"}) == ""
    assert said(b, {"prompt": ""}) == ""


def test_an_unreadable_folder_says_why(tmp_path):
    got = said(tmp_path / "nobox", {"prompt": "bus"})
    assert (
        got
        == "willow: couldn't read your folder (refused: not a kernel box; init first)\n"
    )
    assert said(box(tmp_path), "{not json").startswith(
        "willow: couldn't read the prompt"
    )


def test_json_that_isnt_a_prompt_object_is_said_never_a_crash(tmp_path):
    """hook-fuzz found these: JSON that isn't an object, or is nested past
    Python's depth, raised a traceback and exited 1, though the hook says it
    always exits 0."""
    b = box(tmp_path)
    for sent in ("null", "[]", "5", "[" * 10_000 + "]" * 10_000):
        assert said(b, sent) == "willow: couldn't read the prompt Claude Code sent\n"


def test_the_prompt_is_on_the_record_by_fingerprint_not_words(tmp_path):
    b = box(tmp_path)
    said(b, {"prompt": "when does the bus leave the square"})
    record = (b / "record.jsonl").read_text()
    assert '"kind": "bite"' in record or '"kind":"bite"' in record
    assert "square" not in record


def test_the_hook_always_exits_zero(tmp_path):
    for b in (box(tmp_path), tmp_path / "nobox"):
        got = subprocess.run([sys.executable, str(HERE / "hook.py"), "prompt", "--box", str(b)],
                             input='{"prompt": "bus"}', capture_output=True, text=True)  # fmt: skip
        assert got.returncode == 0


def test_setup_prints_the_hook_and_the_mcp_line_and_writes_nothing(tmp_path, capsys):
    b = box(tmp_path)
    before = sorted(p.name for p in b.iterdir())
    assert hk.main(["setup", "--box", str(b)]) == 0
    out = capsys.readouterr().out
    hook = json.loads(out.split("\n\n")[1])
    cmd = hook["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    assert (
        cmd["type"] == "command"
        and f"hook.py prompt --box {b.resolve()}" in cmd["command"]
    )
    assert "claude mcp add willow -- " in out and "mcp-lite/server.py --box" in out
    assert sorted(p.name for p in b.iterdir()) == before


def test_a_bad_command_line_or_box_is_refused(tmp_path):
    assert hk.main([]) == 2 and hk.main(["setup", "--box"]) == 2
    assert hk.main(["setup", "--box", str(tmp_path)]) == 2


def test_a_folder_with_a_space_in_its_name_stays_one_piece(tmp_path, capsys):
    import shlex

    (tmp_path / "with space").mkdir()
    b = box(tmp_path / "with space")
    assert hk.main(["setup", "--box", str(b)]) == 0
    out = capsys.readouterr().out
    cmd = json.loads(out.split("\n\n")[1])["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    argv = shlex.split(cmd["command"])
    assert argv[1:4] == [str(hk.HERE), "prompt", "--box"] and argv[4] == str(
        b.resolve()
    )
    add = shlex.split(out.split("    claude mcp add", 1)[1])
    assert add[add.index("--box") + 1] == str(b.resolve())


def test_each_system_gets_its_own_shells_quoting(monkeypatch):
    argv = ["/a b/python", "x"]
    monkeypatch.setattr(hk.os, "name", "posix")
    assert hk.command_line(argv) == "'/a b/python' x"
    monkeypatch.setattr(hk.os, "name", "nt")
    assert hk.command_line(argv) == '"/a b/python" x'


BESIDE = (HERE.parent / "index-cache").is_dir() and (HERE.parent / "scan").is_dir()


def test_alone_an_index_is_never_asked_and_setup_says_what_it_needs(tmp_path, capsys):
    """Without scan and index-cache beside it (a stack that didn't add them),
    the kernel reads the folder as ever, whatever --index names."""
    b, ask = box(tmp_path), {"prompt": "when does the bus leave the square"}
    plain = said(b, ask)
    got = hk.prompt(b, io.StringIO(json.dumps(ask)), tmp_path / "no-index")
    assert got == plain and "n.md:1:" in got
    if not BESIDE:
        assert hk.main(["setup", "--box", str(b), "--index", str(tmp_path / "i")]) == 2
        assert "needs index-cache and scan" in capsys.readouterr().err


def indexed_box(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A box over a few files, and index-cache's index of its folder."""
    b = box(tmp_path)
    pile = tmp_path / "pile"
    (pile / "m.md").write_text(
        "The ferry to the island leaves the square at noon.\n\n"
        "Buses wait by the square until the ferry docks.\n"
    )
    (pile / "o.md").write_text("Nothing about transport lives here.\n")
    at = tmp_path / "index"
    cache = HERE.parent / "index-cache" / "index_cache.py"
    assert subprocess.run([sys.executable, str(cache), "--from", str(pile), "--to", str(at)],
                          capture_output=True).returncode == 0  # fmt: skip
    return b, pile, at


def bites(b: Path) -> list[dict]:
    rows = [json.loads(r) for r in (b / "record.jsonl").read_text().splitlines()]
    return [
        {k: r[k] for k in ("bite_key", "served")} for r in rows if r["kind"] == "bite"
    ]


@pytest.mark.skipif(
    not BESIDE,
    reason="scan and index-cache aren't beside it; the test above holds it alone",
)
def test_an_index_answers_as_the_kernel_would_without_reading_the_folder(
    tmp_path, monkeypatch
):
    """With a current index, the hook prints what the kernel's bite would and
    puts the same row on the record, and never reads the folder; a folder
    that changed since is read by the kernel, never answered from the index."""
    b, pile, at = indexed_box(tmp_path)
    ask = {"prompt": "when does the bus leave the square"}
    plain = said(b, ask)
    assert "m.md:1:" in plain and "n.md:1:" in plain
    reads = []
    real = hk.kernel.chunks
    monkeypatch.setattr(hk.kernel, "chunks", lambda *a: reads.append(a) or real(*a))
    got = hk.prompt(b, io.StringIO(json.dumps(ask)), at)
    assert got == plain and reads == []
    first, second = bites(b)
    assert first == second
    # the folder changed: the index isn't asked, the kernel reads the folder
    (pile / "o.md").write_text("The last bus leaves the square at midnight.\n")
    got = hk.prompt(b, io.StringIO(json.dumps(ask)), at)
    assert reads and "o.md:1:" in got
    # an answer the person sealed for these words still comes first
    cite = json.loads(
        subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(b),
                        ask["prompt"]], capture_output=True, text=True).stdout
    )["served"][0]["id"]  # fmt: skip
    row = {"path": "bus.md", "data": "Seven.", "cites": [cite], "claim": "n.md"}
    (tmp_path / "rows.jsonl").write_text(json.dumps(row) + "\n")
    for verb, code in ((["propose", "--file", str(tmp_path / "rows.jsonl")], 42),
                       (["seal", hk.kernel.subject_of(row)], 0)):  # fmt: skip
        assert subprocess.run([sys.executable, str(KERNEL), verb[0], "--box", str(b),
                               *verb[1:]], capture_output=True).returncode == code  # fmt: skip
    assert subprocess.run([sys.executable, str(HERE.parent / "index-cache" / "index_cache.py"),
                           "--from", str(pile), "--to", str(at)],
                          capture_output=True).returncode == 0  # fmt: skip
    reads.clear()
    got = hk.prompt(b, io.StringIO(json.dumps(ask)), at)
    assert reads == [] and "An answer the person approved" in got and "Seven." in got
    assert bites(b)[-1]["served"] == []
    other = {"prompt": "when does the ferry leave the square"}  # not the sealed one
    got = hk.prompt(b, io.StringIO(json.dumps(other)), at)
    assert reads == [] and "Seven." not in got and "m.md:1:" in got


@pytest.mark.skipif(
    not BESIDE,
    reason="scan and index-cache aren't beside it; the test above holds it alone",
)
def test_setup_with_an_index_prints_the_line_that_keeps_it_current(tmp_path, capsys):
    b, pile, at = indexed_box(tmp_path)
    assert hk.main(["setup", "--box", str(b), "--index", str(at)]) == 0
    out = capsys.readouterr().out
    cmd = json.loads(out.split("\n\n")[1])["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    assert cmd["command"].endswith(f"--index {at.resolve()}")
    assert f"index_cache.py --from {pile} --to {at.resolve()}" in out
    assert hk.main(["setup", "--box", str(b), "--index", ""]) == 2
    assert hk.main(["prompt", "--box", str(b), "--rank", str(at)]) == 2


@pytest.mark.skipif(
    not BESIDE,
    reason="scan and index-cache aren't beside it; the test above holds it alone",
)
def test_an_index_asks_with_their_words_list_as_the_kernel_does(tmp_path, monkeypatch):
    """A box made with a words list: the index answers with it, the row keeps
    its hash as the kernel's does, and an unreadable list is the kernel's to
    refuse, never answered past."""
    pile, mine = tmp_path / "pile", tmp_path / "mine"
    pile.mkdir()
    (pile / "log.txt").write_text("2026-10-16 Calvin\n  next: Oct 2027\n")
    (pile / "other.md").write_text("Nothing here is due.\n")
    mine.mkdir(mode=0o700)
    wl = mine / "words.txt"
    wl.write_text("# what I call things\ndue = next, overdue\n")
    wl.chmod(0o600)
    b = tmp_path / "box"
    assert subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                           "--key", str(mine / "k"), "--words", str(wl), *NOW],
                          capture_output=True).returncode == 0  # fmt: skip
    at = tmp_path / "index"
    assert subprocess.run([sys.executable, str(HERE.parent / "index-cache" / "index_cache.py"),
                           "--from", str(pile), "--to", str(at)], capture_output=True).returncode == 0  # fmt: skip
    ask = {"prompt": "who's due for a tuning"}
    plain = said(b, ask)
    reads = []
    real = hk.kernel.chunks
    monkeypatch.setattr(hk.kernel, "chunks", lambda *a: reads.append(a) or real(*a))
    got = hk.prompt(b, io.StringIO(json.dumps(ask)), at)
    assert got == plain and "log.txt:1:" in got and reads == []
    rows = [json.loads(r) for r in (b / "record.jsonl").read_text().splitlines()]
    first, second = [r for r in rows if r["kind"] == "bite"]
    assert first["words_sha256"] == second["words_sha256"]
    assert first["served"] == second["served"]
    wl.chmod(0o644)  # readable by others: the kernel refuses, nothing answered
    got = hk.prompt(b, io.StringIO(json.dumps(ask)), at)
    assert got.startswith("willow: couldn't read your folder (")
