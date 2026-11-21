"""hook-ask-first: a read by hand of a file a box holds is refused until the
box was asked this session; what a box holds comes from its stacks; its own
trouble never blocks a tool."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HOOK = HERE / "hook_ask_first.py"
KERNEL = ROOT / "kernel.py"
#: the readers the project's stack names: their card's own line is said when
#: they're beside this add-on, and the step alone when they aren't
BESIDE = {n: (HERE.parent / n / "README.md").is_file() for n in ("markdown", "copy-in")}


def project(tmp: Path) -> dict:
    """A project as a stack leaves it: sources a reader mirrors into a pile, a
    folder copied in first, a box, a stack beside it, and a list naming the box."""
    p = tmp / "project"
    (p / "sources" / "docs").mkdir(parents=True)
    (p / "sources" / "docs" / "rules.md").write_text("division must be exact\n")
    (p / "incoming").mkdir()
    (p / "incoming" / "table.csv").write_text("id,targets\n1,9\n")
    (p / "sources" / "data").mkdir()
    (p / "pile" / "docs").mkdir(parents=True)
    (p / "pile" / "docs" / "rules.md.txt").write_text("division must be exact\n")
    (p / "elsewhere").mkdir()
    (p / "elsewhere" / "free.txt").write_text("nobody holds this\n")
    box = p / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
                    str(p / "pile"), "--key", str(tmp / "key")], check=True, capture_output=True)  # fmt: skip
    (p / "stack.md").write_text(
        "# a stack\n\n## in\n"
        f"- copy-in -- --from {p}/incoming --to {p}/sources/data\n"
        f"- markdown -- mirror --from {p}/sources/docs --to {p}/pile/docs\n"
        f"- csv-rows -- mirror --from {p}/sources/data --to {p}/pile/data\n"
        "- todo -- --box {box}\n"
    )
    boxes = tmp / "list.boxes"
    boxes.write_text(json.dumps([{"box": str(box)}, {"box": str(tmp / "gone")}]))
    return {"p": p, "box": box, "boxes": boxes}


def hook(boxes: Path, call, *more: str) -> subprocess.CompletedProcess:
    raw = call if isinstance(call, str) else json.dumps(call)
    return subprocess.run([sys.executable, str(HOOK), "run", "--boxes", str(boxes), *more],
                          input=raw, capture_output=True, text=True)  # fmt: skip


def read(path, session="s1") -> dict:
    return {
        "tool_name": "Read",
        "session_id": session,
        "tool_input": {"file_path": str(path)},
    }


def bash(command: str, session="s1", cwd="/") -> dict:
    return {"tool_name": "Bash", "session_id": session, "cwd": cwd,
            "tool_input": {"command": command}}  # fmt: skip


def ask(box: Path, words: str) -> None:
    subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(box), words],
                   capture_output=True)  # fmt: skip


def rows(box: Path) -> list[dict]:
    return [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]


def test_a_held_file_read_by_hand_is_refused_and_says_who_holds_it(tmp_path):
    w = project(tmp_path)
    doc = w["p"] / "sources" / "docs" / "rules.md"
    got = hook(w["boxes"], read(doc))
    assert got.returncode == 2 and got.stdout == ""
    assert f"blocked: ask first  {doc}" in got.stderr
    assert f"the box at {w['box']} holds it" in got.stderr
    said = "the markdown step of stack.md reads it into the pile"
    assert (
        said + (" (markdown: Any Markdown" if BESIDE["markdown"] else "\n")
        in got.stderr
    )
    assert f'python {KERNEL} bite --box {w["box"]} "your question"' in got.stderr
    mine = [r for r in rows(w["box"]) if r.get("kind") == "hook-ask-first"]
    assert len(mine) == 1 and mine[0]["session"] == "s1"
    assert mine[0]["held"] == str(w["p"] / "sources" / "docs")
    assert "division" not in json.dumps(mine)  # never a word of the file


def test_refused_again_until_the_box_is_asked_then_read_freely(tmp_path):
    w = project(tmp_path)
    doc = w["p"] / "sources" / "docs" / "rules.md"
    assert hook(w["boxes"], read(doc)).returncode == 2
    assert hook(w["boxes"], read(doc)).returncode == 2
    assert (
        sum(r.get("kind") == "hook-ask-first" for r in rows(w["box"])) == 1
    )  # met once
    ask(w["box"], "must division be exact")
    got = hook(w["boxes"], read(doc))
    assert got.returncode == 0 and got.stderr == ""
    # and everything else that box holds, its pile and what was copied in
    assert (
        hook(w["boxes"], read(w["p"] / "pile" / "docs" / "rules.md.txt")).returncode
        == 0
    )
    assert hook(w["boxes"], read(w["p"] / "incoming" / "table.csv")).returncode == 0


def test_an_ask_from_before_the_session_met_the_box_does_not_count(tmp_path):
    w = project(tmp_path)
    ask(w["box"], "must division be exact")
    doc = w["p"] / "sources" / "docs" / "rules.md"
    assert hook(w["boxes"], read(doc)).returncode == 2
    ask(w["box"], "must division be exact")
    assert hook(w["boxes"], read(doc)).returncode == 0
    # another session has asked nothing yet
    other = hook(w["boxes"], read(doc, session="s2"))
    assert other.returncode == 2
    ask(w["box"], "division")
    assert hook(w["boxes"], read(doc, session="s2")).returncode == 0


def test_what_is_held_comes_from_the_stack_and_a_copy_in_is_followed(tmp_path):
    w = project(tmp_path)
    p = w["p"]
    for held in (p / "pile" / "docs" / "rules.md.txt", p / "sources" / "data",
                 p / "incoming" / "table.csv"):  # fmt: skip
        if held.is_file():
            assert hook(w["boxes"], read(held, session=held.name)).returncode == 2, held
    got = hook(w["boxes"], read(p / "incoming" / "table.csv", session="t"))
    said = "the copy-in step of stack.md reads it into the pile"
    assert said + (" (copy-in:" if BESIDE["copy-in"] else "\n") in got.stderr
    # nobody's: a file no step reads, the stack file itself, a file not there
    for free in (
        p / "elsewhere" / "free.txt",
        p / "stack.md",
        p / "sources" / "docs" / "no.md",
    ):
        got = hook(w["boxes"], read(free))
        assert got.returncode == 0 and got.stderr == "", free
    # take the reader step out of the stack and its folder is let go
    text = (p / "stack.md").read_text()
    (p / "stack.md").write_text(
        "\n".join(x for x in text.splitlines() if "markdown" not in x) + "\n"
    )
    assert (
        hook(
            w["boxes"], read(p / "sources" / "docs" / "rules.md", session="u")
        ).returncode
        == 0
    )


def test_bash_reads_are_seen_as_the_shell_would_run_them(tmp_path):
    w = project(tmp_path)
    p = w["p"]
    doc = p / "sources" / "docs" / "rules.md"
    n = 0
    for command in (f"tail -5 {doc} | cut -c1-80", f"P={p}; cat $P/sources/docs/rules.md",
                    f"cd {p}/sources && grep -n exact docs/rules.md", f"/usr/bin/head -1 '{doc}'",
                    f"sed -n 1,3p {doc}", f"wc -l {doc}"):  # fmt: skip
        n += 1
        got = hook(w["boxes"], bash(command, session=f"b{n}"))
        assert got.returncode == 2 and str(doc) in got.stderr, command
    for command in (f"ls {p}/sources/docs", f"python stack.py --stack {p}/stack.md",
                    f"cat {p}/elsewhere/free.txt", f"cp {doc} /tmp/x", "echo 'cat is a word here'",
                    "cat 'unclosed"):  # fmt: skip
        n += 1
        got = hook(w["boxes"], bash(command, session=f"b{n}"))
        assert got.returncode == 0, command
    # a relative path is read from the folder the call was made in
    got = hook(
        w["boxes"], bash("cat docs/rules.md", session="rel", cwd=str(p / "sources"))
    )
    assert got.returncode == 2


def test_grep_with_a_path_is_a_read_and_other_tools_are_not(tmp_path):
    w = project(tmp_path)
    docs = w["p"] / "sources" / "docs"
    grep = {
        "tool_name": "Grep",
        "session_id": "g",
        "tool_input": {"pattern": "x", "path": str(docs)},
    }
    assert hook(w["boxes"], grep).returncode == 2
    nowhere = {"tool_name": "Grep", "session_id": "g2", "tool_input": {"pattern": "x"}}
    assert hook(w["boxes"], nowhere).returncode == 0
    for tool, given in (("Write", {"file_path": str(docs / "rules.md"), "content": "x"}),
                        ("Edit", {"file_path": str(docs / "rules.md")}),
                        ("Glob", {"pattern": "*.md", "path": str(docs)}),
                        ("Read", "not a mapping")):  # fmt: skip
        got = hook(
            w["boxes"], {"tool_name": tool, "session_id": "w", "tool_input": given}
        )
        assert got.returncode == 0 and got.stderr == "", tool


def test_its_own_trouble_never_blocks_a_tool(tmp_path):
    w = project(tmp_path)
    doc = w["p"] / "sources" / "docs" / "rules.md"
    got = hook(tmp_path / "no-such.boxes", read(doc))
    assert got.returncode == 0 and "let through" in got.stderr
    bad = tmp_path / "bad.boxes"
    bad.write_text("not json")
    assert hook(bad, read(doc)).returncode == 0
    got = hook(w["boxes"], "not a call")
    assert got.returncode == 0 and "not a call it can read; let through" in got.stderr
    assert hook(w["boxes"], "[1, 2]").returncode == 0
    # a record that doesn't verify is someone else's to say; the read goes by
    rec = w["box"] / "record.jsonl"
    rec.write_text(rec.read_text().replace('"boot"', '"b00t"'))
    got = hook(w["boxes"], read(doc))
    assert got.returncode == 0 and "record doesn't verify; let through" in got.stderr


def test_the_row_takes_the_time_it_is_given(tmp_path):
    w = project(tmp_path)
    doc = w["p"] / "sources" / "docs" / "rules.md"
    hook(w["boxes"], read(doc), "--now", "2026-11-19T00:00:00Z")
    mine = [r for r in rows(w["box"]) if r.get("kind") == "hook-ask-first"]
    assert (
        mine[0]["ts"] == "2026-11-19T00:00:00Z" and mine[0]["who"] == "hook-ask-first"
    )


def test_check_says_for_a_person_who_holds_what(tmp_path):
    w = project(tmp_path)
    p = w["p"]
    ask(w["box"], "division")
    got = subprocess.run([sys.executable, str(HOOK), "check", "--boxes", str(w["boxes"]),
                          str(p / "sources" / "docs" / "rules.md"), str(p / "elsewhere" / "free.txt")],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 42
    assert f"held      {p}/sources/docs/rules.md" in got.stdout
    assert f"by {w['box']}: the markdown step of stack.md" in got.stdout
    assert "asked 1 times" in got.stdout
    assert f"not held  {p}/elsewhere/free.txt: no box listed holds it" in got.stdout
    none = subprocess.run([sys.executable, str(HOOK), "check", "--boxes", str(w["boxes"]),
                           str(p / "elsewhere" / "free.txt")], capture_output=True, text=True)  # fmt: skip
    assert none.returncode == 0
    assert (
        sum(r.get("kind") == "hook-ask-first" for r in rows(w["box"])) == 0
    )  # check writes nothing


def test_a_bad_command_line_is_refused(tmp_path):
    w = project(tmp_path)
    for argv in ([], ["run"], ["run", "--box", "x"], ["look", "--boxes", str(w["boxes"])],
                 ["check", "--boxes", str(w["boxes"])], ["check", "--boxes", str(w["boxes"]), "--x"],
                 ["run", "--boxes", str(w["boxes"]), "extra"]):  # fmt: skip
        got = subprocess.run(
            [sys.executable, str(HOOK), *argv],
            input="{}",
            capture_output=True,
            text=True,
        )
        assert (
            got.returncode == 2 and "hook_ask_first.py run --boxes FILE" in got.stderr
        ), argv
    got = subprocess.run([sys.executable, str(HOOK), "check", "--boxes", str(tmp_path / "none"), "x"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "is not a list of boxes" in got.stderr


def test_how_to_ask_names_the_projects_own_ask_script(tmp_path):
    w = project(tmp_path)
    (w["p"] / "ask.py").write_text("")
    got = hook(w["boxes"], read(w["p"] / "sources" / "docs" / "rules.md"))
    assert f'python {w["p"] / "ask.py"} "your question"' in got.stderr
