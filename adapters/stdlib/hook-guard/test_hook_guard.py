"""hook-guard: two rules, named when they refuse: the key is never named, a box
is written only by the kernel; the same call gets the same answer; what it
can't tell it allows; a call it can't read is refused."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hook_guard.py"
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("hook_guard", SCRIPT)
hg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hg)
NOW = ["--now", "2026-10-24T00:00:00Z"]


def run(*argv: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        input=stdin,
        capture_output=True,
        text=True,
    )


def box(tmp_path: Path) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    b, key = tmp_path / "box", tmp_path / "secret" / "key"
    key.parent.mkdir()
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
            str(key),
            *NOW,
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b, key


def call(tool: str, **given) -> str:
    return json.dumps({"tool_name": tool, "tool_input": given})


def test_a_write_inside_the_box_is_refused_and_one_outside_is_not(tmp_path):
    b, _ = box(tmp_path)
    for tool, field in (
        ("Write", "file_path"),
        ("Edit", "file_path"),
        ("MultiEdit", "file_path"),
        ("NotebookEdit", "notebook_path"),
    ):
        got = run(
            "run", "--box", str(b), stdin=call(tool, **{field: str(b / "record.jsonl")})
        )
        assert got.returncode == 2, tool
        assert (
            got.stderr
            == f"refused: rule box-write: this {tool} is inside the box; only kernel.py writes there.\n"
        )
    ok = run(
        "run",
        "--box",
        str(b),
        stdin=call("Write", file_path=str(tmp_path / "pile" / "new.md"), content="x"),
    )
    assert ok.returncode == 0 and ok.stderr == ""
    assert (
        run("run", "--box", str(b), stdin=call("Write", file_path=str(b))).returncode
        == 2
    ), "the box itself"
    assert (
        run(
            "run", "--box", str(b), stdin=call("Write", file_path=str(b) + "-not/x")
        ).returncode
        == 0
    ), "a sibling by name"
    assert (
        run(
            "run",
            "--box",
            str(b),
            stdin=call(
                "Write", file_path=str(b / ".." / "box" / "proposals" / "x.json")
            ),
        ).returncode
        == 2
    ), "dots do not hide it"


def test_a_relative_path_is_read_against_the_calls_cwd(tmp_path):
    b, _ = box(tmp_path)
    raw = json.dumps(
        {
            "tool_name": "Write",
            "cwd": str(b),
            "tool_input": {"file_path": "record.jsonl"},
        }
    )
    assert run("run", "--box", str(b), stdin=raw).returncode == 2
    raw = json.dumps(
        {
            "tool_name": "Write",
            "cwd": str(tmp_path / "pile"),
            "tool_input": {"file_path": "record.jsonl"},
        }
    )
    assert run("run", "--box", str(b), stdin=raw).returncode == 0


def test_the_key_is_never_named(tmp_path):
    b, key = box(tmp_path)
    for raw in (
        call("Read", file_path=str(key)),
        call("Grep", pattern="a", path=str(key)),
        call("Bash", command=f"cat {key}"),
        call("Bash", command=f"echo hi && cp {key} /tmp/stolen"),
        call("Bash", command=f"cat {key.parent}/../secret/key"),
    ):
        got = run("run", "--box", str(b), stdin=raw)
        assert got.returncode == 2, raw
        assert got.stderr.startswith("refused: rule key: "), got.stderr
    assert "the key is the person's" in got.stderr
    assert (
        run(
            "run",
            "--box",
            str(b),
            stdin=call("Read", file_path=str(key.parent / "other")),
        ).returncode
        == 0
    )
    assert (
        run(
            "run",
            "--box",
            str(b),
            stdin=call("Read", file_path=str(b / "record.jsonl")),
        ).returncode
        == 0
    ), "the record may be read"


def test_a_command_that_changes_the_box_is_refused_and_one_that_reads_it_is_not(
    tmp_path,
):
    b, _ = box(tmp_path)
    refused = (
        f"echo x > {b}/record.jsonl", f"echo x>>{b}/record.jsonl", f"cat a 2> {b}/err", f"echo x &>{b}/o",
        f"rm {b}/record.jsonl", f"rm -rf {b}", f"mv a {b}/proposals/", f"cp /tmp/a {b}/", f"tee {b}/x < /tmp/a",
        f"touch {b}/x", f"mkdir {b}/d", f"truncate -s 0 {b}/record.jsonl", f"chmod 600 {b}/kernel.json",
        f"sed -i s/a/b/ {b}/kernel.json", f"sed --in-place s/a/b/ {b}/kernel.json", f"dd if=/dev/zero of={b}/x",
        f"ls && rm {b}/x", f"cat a | tee {b}/x",
    )  # fmt: skip
    for c in refused:
        got = run("run", "--box", str(b), stdin=call("Bash", command=c))
        assert got.returncode == 2 and "rule box-write" in got.stderr, c
    allowed = (
        f"cat {b}/record.jsonl", f"ls {b}", f"cp {b}/record.jsonl /tmp/copy", f"grep a {b}/record.jsonl > /tmp/out",
        f"python {KERNEL} bite --box {b} 'how much sun'", f"sed s/a/b/ {b}/kernel.json", "rm /tmp/other", "echo hi",
        f"python {KERNEL} out --box {b}",
    )  # fmt: skip
    for c in allowed:
        got = run("run", "--box", str(b), stdin=call("Bash", command=c))
        assert got.returncode == 0 and got.stderr == "", (c, got.stderr)


def test_a_command_that_runs_one_on_the_box_or_unpacks_into_it_is_refused(tmp_path):
    """Seen driving a provider's guard door: find -delete, find -exec rm,
    git -C BOX clean, tar -C BOX and unzip -d BOX each name the box in
    plain sight and changed it. What only reads it is let through."""
    b, _ = box(tmp_path)
    inside = str(b)
    refused = (
        (f"find {b} -name '*.jsonl' -delete", ""), (f"find {b} -type f -exec rm {{}} +", ""),
        (f"find {b} -execdir shred -u {{}} \\;", ""), ("find . -delete", inside),
        (f"git -C {b} clean -fdx", ""), (f"git --work-tree={b} checkout -- .", ""),
        (f"git -c a=b -C {b} reset --hard", ""), (f"tar -xf /tmp/x.tar -C {b}", ""),
        (f"tar xzf /tmp/x.tgz --directory={b}", ""), ("tar -xf /tmp/x.tar", inside),
        (f"unzip -o /tmp/x.zip -d {b}", ""), ("unzip /tmp/x.zip", inside),
    )  # fmt: skip
    for c, cwd in refused:
        sent = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": c}, "cwd": cwd}
        )
        got = run("run", "--box", str(b), stdin=sent)
        assert got.returncode == 2 and "rule box-write" in got.stderr, c
    allowed = (
        (f"find {b} -name '*.jsonl'", ""), (f"find {b} -exec grep sun {{}} +", ""),
        ("find /tmp -delete", ""), (f"git -C {b} status", ""), (f"git -C {b} log", ""),
        (f"tar -cf /tmp/out.tar -C {b} .", ""), (f"tar -tf /tmp/x.tar -C {b}", ""),
        ("unzip /tmp/x.zip -d /tmp/out", ""), ("unzip -l /tmp/x.zip", inside),
    )  # fmt: skip
    for c, cwd in allowed:
        sent = json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": c}, "cwd": cwd}
        )
        got = run("run", "--box", str(b), stdin=sent)
        assert got.returncode == 0 and got.stderr == "", (c, got.stderr)


def test_what_it_cannot_tell_it_allows_and_other_tools_pass(tmp_path):
    b, _ = box(tmp_path)
    for raw in (
        call("Bash", command="echo 'unterminated"),
        call("Bash", command=7),
        call("Bash"),
        call("WebFetch", url="https://example.org"),
        call("Task", prompt="x"),
        call("Read", file_path=7),
        call("Bash", command="cat \0/x > \0/y"),
        call("Write", file_path="a\0b"),
        json.dumps({"tool_name": "Write", "tool_input": "text"}),
    ):
        assert run("run", "--box", str(b), stdin=raw).returncode == 0, raw


def test_input_that_is_not_a_json_object_is_refused(tmp_path):
    b, _ = box(tmp_path)
    for raw in ("", "not json", "[1]", "7", "null"):
        got = run("run", "--box", str(b), stdin=raw)
        assert got.returncode == 2 and "can't say it is safe" in got.stderr, raw


def test_rules_are_listed_and_a_bad_command_line_is_refused(tmp_path):
    b, _ = box(tmp_path)
    got = run("rules")
    assert got.returncode == 0 and got.stdout.splitlines() == [
        "key        the call names the box's key file",
        "box-write  the call would change a file inside the box other than through kernel.py",
        "beside-write with --also DIR, the call would change a file inside that folder kept beside the box",
    ]
    for argv in (
        [],
        ["run"],
        ["run", "--box"],
        ["rules", "--stray"],
        ["run", "--box", str(tmp_path)],
        ["run", "--box", str(b), "x"],
    ):
        assert run(*argv).returncode == 2, argv
    assert "hook_guard.py" in run().stderr
    assert "not a kernel box" in run("run", "--box", str(tmp_path)).stderr


def test_it_writes_nothing_and_the_same_call_gets_the_same_answer(tmp_path):
    b, _ = box(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    raw = call("Bash", command=f"rm {b}/x")
    first = run("run", "--box", str(b), stdin=raw)
    assert run("run", "--box", str(b), stdin=raw).stderr == first.stderr
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.xfail(
    strict=True,
    reason="bug #90: a Grep or recursive Glob over the folder holding the key is allowed",
)
def test_a_search_of_the_folder_holding_the_key_is_refused(tmp_path):
    b, key = box(tmp_path)
    for raw in (call("Grep", pattern=".", path=str(key.parent)),
                call("Glob", pattern="**/*", path=str(key.parent))):  # fmt: skip
        assert hg.judge(raw, b, key)[0] == 2


@pytest.mark.xfail(
    strict=True,
    reason="bug #91: a command that runs kernel.py seal is allowed, and seal reads the key",
)
def test_a_command_that_seals_is_refused(tmp_path):
    b, key = box(tmp_path)
    for verb in ("seal", "decline"):
        raw = call(
            "Bash", command=f"python {KERNEL} {verb} --box {b} proposal:{'0' * 64}"
        )
        assert hg.judge(raw, b, key)[0] == 2


def beside(tmp_path: Path) -> tuple[Path, Path, Path]:
    b, key = box(tmp_path)
    return b, key, tmp_path / "box.runtime"  # kept beside the box, not made yet


def run_also(b: Path, also: Path, raw: str) -> subprocess.CompletedProcess:
    return run("run", "--box", str(b), "--also", str(also), stdin=raw)


def test_a_folder_kept_beside_the_box_is_held_like_the_box_and_may_be_read(tmp_path):
    b, _, side = beside(tmp_path)
    for tool, field in (
        ("Write", "file_path"),
        ("Edit", "file_path"),
        ("MultiEdit", "file_path"),
        ("NotebookEdit", "notebook_path"),
    ):
        got = run_also(b, side, call(tool, **{field: str(side / "stopped.json")}))
        assert got.returncode == 2, tool
        assert (
            got.stderr
            == f"refused: rule beside-write: this {tool} is inside a folder kept beside the box; only the runtime writes there.\n"
        )
    for c in (
        f"echo x > {side}/stopped.json", f"rm {side}/names.txt", f"rm -rf {side}", f"tee {side}/sent.jsonl < /tmp/a",
        f"mkdir {side}/shelf", f"sed -i s/a/b/ {side}/names.txt", f"cp /tmp/a {side}/x", f"dd if=/dev/zero of={side}/x",
        f"mv {side}/names.txt /tmp/x", f"mv a {side}/x", f"echo x>>{side}/sent.jsonl",
    ):  # fmt: skip
        got = run_also(b, side, call("Bash", command=c))
        assert got.returncode == 2 and "rule beside-write" in got.stderr, c
    for raw in (
        call("Read", file_path=str(side / "stopped.json")),
        call("Bash", command=f"cat {side}/names.txt"),
        call("Bash", command=f"cp {side}/names.txt /tmp/copy"),
        call("Bash", command=f"grep a {side}/sent.jsonl > /tmp/out"),
        call("Write", file_path=str(tmp_path / "pile" / "new.md")),
        call("Write", file_path=str(side) + "-old/x"),
        call("Write", file_path=str(side) + "/../box.runtime-old/x"),
    ):
        got = run_also(b, side, raw)
        assert got.returncode == 0 and got.stderr == "", (raw, got.stderr)


def test_a_folder_that_does_not_exist_yet_is_held_and_dots_and_links_do_not_hide_it(
    tmp_path,
):
    b, _, side = beside(tmp_path)
    assert not side.exists()
    dots = str(tmp_path / "pile" / ".." / "box.runtime" / "stopped.json")
    assert run_also(b, side, call("Write", file_path=dots)).returncode == 2
    link = tmp_path / "ln"
    link.symlink_to(tmp_path)
    got = run_also(b, side, call("Write", file_path=str(link / "box.runtime" / "x")))
    assert got.returncode == 2
    raw = json.dumps(
        {"tool_name": "Write", "cwd": str(side), "tool_input": {"file_path": "x"}}
    )
    assert run_also(b, side, raw).returncode == 2, "a relative path, against cwd"
    assert not side.exists(), "the hook made nothing"


def test_more_than_one_also_folder_is_held_and_without_also_only_the_box_is(tmp_path):
    b, _, side = beside(tmp_path)
    other = tmp_path / "other"
    argv = ["run", "--box", str(b), "--also", str(side), "--also", str(other)]
    for f in (side, other):
        got = run(*argv, stdin=call("Write", file_path=str(f / "x")))
        assert got.returncode == 2 and "beside-write" in got.stderr
    assert (
        run(*argv, stdin=call("Write", file_path=str(tmp_path / "x"))).returncode == 0
    )
    plain = ["run", "--box", str(b)]
    assert run(*plain, stdin=call("Bash", command=f"rm {side}/x")).returncode == 0
    assert run(*plain, stdin=call("Bash", command=f"rm {b}/x")).returncode == 2


def test_the_box_is_still_named_box_write_when_also_is_given(tmp_path):
    b, _, side = beside(tmp_path)
    got = run_also(b, side, call("Write", file_path=str(b / "record.jsonl")))
    assert got.returncode == 2 and "rule box-write" in got.stderr
    got = run_also(b, side, call("Bash", command=f"rm {b}/x"))
    assert got.returncode == 2 and "rule box-write" in got.stderr


def test_a_file_moved_out_of_the_box_changes_it_but_a_move_into_it_from_elsewhere_still_does_too(
    tmp_path,
):
    b, _ = box(tmp_path)
    for c in (
        f"mv {b}/record.jsonl /tmp/x",
        f"mv -f {b}/a {b}/b",
        f"mv /tmp/a {b}/x",
        f"mv {b}/a /tmp/b /tmp/dir/",
    ):
        got = run("run", "--box", str(b), stdin=call("Bash", command=c))
        assert got.returncode == 2 and "rule box-write" in got.stderr, c  # fmt: skip
    for c in (
        "mv /tmp/a /tmp/b",
        f"mv /tmp/a {b}-not/x",
        f"cp {b}/record.jsonl /tmp/x",
    ):
        assert (
            run("run", "--box", str(b), stdin=call("Bash", command=c)).returncode == 0
        ), c


def test_a_bad_also_is_a_bad_command_line(tmp_path):
    b, _ = box(tmp_path)
    for argv in (
        ["run", "--box", str(b), "--also"],
        ["run", "--box", str(b), "--also", str(tmp_path), "x"],
        ["run", "--also", str(tmp_path), "--box", str(b)],
        ["run", "--box", str(b), "--also", str(tmp_path), "--stray"],
    ):
        assert run(*argv).returncode == 2, argv
