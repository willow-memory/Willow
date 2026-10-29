"""hook-impact: before an edit, the places in the person's files that name the
file by its whole name, never blocking; the file's own lines don't count; any
other tool, or nothing found, prints nothing."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_impact.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("hook_impact", SCRIPT)
hi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hi)


def run(*argv: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        input=stdin,
        capture_output=True,
        text=True,
    )


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b


def call(tool: str, **given) -> str:
    return json.dumps({"tool_name": tool, "tool_input": given})


FILES = {
    "docs/notes.md": "intro\nsee kernel.py for the rules\nkernel.pyc is a cache\nmy-kernel.py is not it\nthe Kernel.py case\n",
    "README.md": "kernel.py is the one file that writes a box\n",
    "src/kernel.py": "# kernel.py: the kernel itself names kernel.py\n",
}


def test_a_name_is_matched_as_a_whole_word_with_its_extension():
    pile = [
        {
            "path": "n.md",
            "line": 1,
            "text": "kernel.py\nkernel.pyc\nmy-kernel.py\nxkernel.py\n(kernel.py)\nkernel.py,\nkernel.py-old\nthe kernel.py file\n",
        }
    ]
    got = hi.places(pile, Path("/x/kernel.py"), Path("/p"))
    assert [n for _, n, _ in got] == [1, 5, 6, 8]


def test_the_edited_files_own_lines_are_left_out_and_others_are_found(tmp_path):
    box(tmp_path, FILES)
    pile = tmp_path / "pile"
    pile_chunks = hi.kernel.chunks(pile)
    got = hi.places(pile_chunks, pile / "src" / "kernel.py", pile)
    assert [(p, n) for p, n, _ in got] == [("README.md", 1), ("docs/notes.md", 2)]
    elsewhere = hi.places(pile_chunks, tmp_path / "elsewhere" / "kernel.py", pile)
    assert ("src/kernel.py", 1) in [(p, n) for p, n, _ in elsewhere]


def test_a_hook_run_hands_the_places_as_context_and_allows(tmp_path):
    b = box(tmp_path, FILES)
    target = tmp_path / "pile" / "src" / "kernel.py"
    got = run(
        "run",
        "--box",
        str(b),
        stdin=call("Edit", file_path=str(target), old_string="a", new_string="b"),
    )
    assert got.returncode == 0 and got.stderr == ""
    out = json.loads(got.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["additionalContext"].splitlines() == [
        "Before editing kernel.py, these places in the person's files name it:",
        "  README.md:1  kernel.py is the one file that writes a box",
        "  docs/notes.md:2  see kernel.py for the rules",
        "Check they still say what is true after the edit.",
    ]
    for tool, field in (
        ("Write", "file_path"),
        ("MultiEdit", "file_path"),
        ("NotebookEdit", "notebook_path"),
    ):
        assert (
            run("run", "--box", str(b), stdin=call(tool, **{field: str(target)})).stdout
            == got.stdout
        ), tool


def test_a_relative_path_is_read_against_cwd_and_the_pile_file_is_still_itself(
    tmp_path,
):
    b = box(tmp_path, FILES)
    raw = json.dumps(
        {
            "tool_name": "Edit",
            "cwd": str(tmp_path / "pile" / "src"),
            "tool_input": {"file_path": "kernel.py"},
        }
    )
    ctx = json.loads(run("run", "--box", str(b), stdin=raw).stdout)[
        "hookSpecificOutput"
    ]["additionalContext"]
    assert "src/kernel.py" not in ctx


def test_ten_places_are_listed_then_counted_and_long_lines_are_cut():
    found = [("f.md", i, "x" * 150 if i == 1 else "line") for i in range(1, 14)]
    text = hi.sentences("a.py", found).splitlines()
    assert len(text) == 1 + 10 + 1 + 1
    assert text[1] == "  f.md:1  " + "x" * 99 + "…"
    assert text[-2] == "  and 3 more"
    exactly = hi.sentences("a.py", [("f.md", 1, "y" * 100)]).splitlines()[1]
    assert exactly == "  f.md:1  " + "y" * 100, "a line of exactly 100 is not cut"
    assert hi.sentences("a.py", found[:10]).count("more") == 0


def test_nothing_found_or_another_tool_or_a_call_it_cannot_read_prints_nothing(
    tmp_path,
):
    b = box(tmp_path, FILES)
    for raw in (
        call("Edit", file_path=str(tmp_path / "pile" / "unmentioned.py")),
        call("Read", file_path=str(tmp_path / "pile" / "src" / "kernel.py")),
        call("Bash", command="rm kernel.py"),
        call("Edit", file_path=""),
        call("Edit"),
        json.dumps({"tool_name": "Edit", "tool_input": "x"}),
        "not json", "[1]", "",
    ):  # fmt: skip
        got = run("run", "--box", str(b), stdin=raw)
        assert got.returncode == 0 and got.stdout == "", raw


def test_check_lists_the_places_for_a_person(tmp_path):
    b = box(tmp_path, FILES)
    got = run("check", "--box", str(b), str(tmp_path / "pile" / "src" / "kernel.py"))
    assert got.returncode == 42 and got.stdout.splitlines() == [
        "README.md:1  kernel.py is the one file that writes a box",
        "docs/notes.md:2  see kernel.py for the rules",
    ]
    none = run("check", "--box", str(b), "nobody.py")
    assert (
        none.returncode == 0
        and none.stdout == "Nothing in your files names nobody.py.\n"
    )


def test_it_writes_nothing_and_a_bad_command_line_is_refused(tmp_path):
    b = box(tmp_path, FILES)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("run", "--box", str(b), stdin=call("Edit", file_path="kernel.py"))
    run("check", "--box", str(b), "kernel.py")
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    for argv in (
        [],
        ["run"],
        ["run", "--box"],
        ["run", "--box", str(b), "x"],
        ["check", "--box", str(b)],
        ["check", "--box", str(b), "a", "b"],
        ["run", "--box", str(tmp_path)],
        ["go", "--box", str(b)],
    ):
        assert run(*argv).returncode == 2, argv
    assert "hook_impact.py" in run().stderr
    assert "not a kernel box" in run("check", "--box", str(tmp_path), "x").stderr


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'hook_impact.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "habits"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )
