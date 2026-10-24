"""install-scripts: each install script the packages in node_modules would run,
cited by package, file and line, the command as written; a package.json
outside node_modules ignored; a folder with no node_modules clean; a bad
command line or target refused; and nothing written."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "install_scripts.py"
KERNEL = HERE.parents[2] / "kernel.py"

#: postinstall is on line 5
ESBUILD = (
    '{\n  "name": "esbuild",\n  "version": "0.19.0",\n'
    '  "scripts": {\n    "postinstall": "node install.js"\n  }\n}\n'
)
#: preinstall on line 4, build (not a hook) on 5, install on 6, postinstall on 7
ALL_HOOKS = (
    '{\n  "name": "tool",\n  "scripts": {\n'
    '    "preinstall": "echo a",\n    "build": "tsc",\n'
    '    "install": "node b.js",\n    "postinstall": "echo c"\n  }\n}\n'
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def write(folder: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = folder / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}  # fmt: skip


def test_an_install_script_is_cited_by_package_file_and_line(tmp_path):
    write(tmp_path, {"web/node_modules/esbuild/package.json": ESBUILD})
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    lines = got.stdout.splitlines()
    assert lines[0] == "esbuild"
    assert lines[1] == (
        "    web/node_modules/esbuild/package.json:5   postinstall   node install.js"
    )
    assert "1 install script in 1 package would run on npm install" in got.stdout


def test_each_hook_gets_its_own_line_and_other_scripts_do_not(tmp_path):
    write(tmp_path, {"node_modules/tool/package.json": ALL_HOOKS})
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    p = "    node_modules/tool/package.json"
    lines = got.stdout.splitlines()
    assert f"{p}:4   {'preinstall':<11}   echo a" in lines
    assert f"{p}:6   {'install':<11}   node b.js" in lines
    assert f"{p}:7   {'postinstall':<11}   echo c" in lines
    assert "tsc" not in got.stdout and "build" not in got.stdout
    assert "3 install scripts in 1 package would run" in got.stdout


def test_the_line_is_the_scripts_key_not_a_look_alike_before_it(tmp_path):
    write(tmp_path, {"node_modules/x/package.json": (
        '{\n  "name": "x",\n  "config": {\n    "postinstall": "ignored"\n  },\n'
        '  "scripts": {\n    "postinstall": "node run.js"\n  }\n}\n')})  # fmt: skip
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    assert "node_modules/x/package.json:7   postinstall   node run.js" in got.stdout
    assert "ignored" not in got.stdout


def test_a_leading_blank_line_is_counted(tmp_path):
    write(tmp_path, {"node_modules/esbuild/package.json": "\n" + ESBUILD})
    got = run("--from", str(tmp_path))
    assert "node_modules/esbuild/package.json:6   postinstall" in got.stdout


def test_a_key_written_with_escapes_is_cited_at_line_one_or_placed(tmp_path):
    # the hook's key written with a \u escape can't be placed: cited at line 1
    write(tmp_path, {"node_modules/esc/package.json": (
        '{\n  "name": "esc",\n  "scripts": {\n    "post\\u0069nstall": "node e.js"\n  }\n}\n')})  # fmt: skip
    # the scripts key written with an escape: the hook is still placed
    write(tmp_path, {"node_modules/esc2/package.json": (
        '{\n  "name": "esc2",\n  "\\u0073cripts": {\n    "postinstall": "node z.js"\n  }\n}\n')})  # fmt: skip
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    assert re.search(
        r"node_modules/esc/package\.json:1\s+postinstall\s+node e\.js", got.stdout
    )
    assert re.search(
        r"node_modules/esc2/package\.json:4\s+postinstall\s+node z\.js", got.stdout
    )


def test_a_package_with_no_install_scripts_is_clean(tmp_path):
    write(tmp_path, {"node_modules/left-pad/package.json": (
        '{"name": "left-pad", "scripts": {"test": "node test.js"}}')})  # fmt: skip
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stderr
    assert "No install scripts in 1 package in node_modules." in got.stdout


def test_a_package_json_outside_node_modules_is_ignored(tmp_path):
    write(
        tmp_path,
        {
            "package.json": ESBUILD,
            "web/package.json": ESBUILD,
            "garden.md": "Tomatoes want sun.\n",
        },
    )
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "No node_modules folder here" in got.stdout


def test_a_folder_with_no_node_modules_is_clean(tmp_path):
    write(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run("--from", str(tmp_path))
    assert got.returncode == 0 and "No node_modules folder here" in got.stdout


def test_a_name_comes_from_the_package_or_else_its_folder(tmp_path):
    write(tmp_path, {
        "node_modules/plain/package.json": '{"scripts": {"install": "node i.js"}}',
        "node_modules/@scope/tool/package.json": '{"scripts": {"postinstall": "x"}}',
        "node_modules/dir/package.json": '{"name": "real-name", "scripts": {"postinstall": "y"}}',
        "node_modules/blank/package.json": '{"name": "", "scripts": {"postinstall": "z"}}',
        "node_modules/num/package.json": '{"name": 5, "scripts": {"postinstall": "w"}}',
    })  # fmt: skip
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    lines = set(got.stdout.splitlines())
    assert {"plain", "@scope/tool", "real-name", "blank", "num"} <= lines


def test_a_package_json_that_is_not_an_object_or_has_no_object_scripts_is_clean(
    tmp_path,
):
    write(tmp_path, {
        "node_modules/arr/package.json": "[1, 2]",
        "node_modules/str/package.json": '{"scripts": "node x.js"}',
    })  # fmt: skip
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stderr
    assert "No install scripts in 2 packages in node_modules." in got.stdout


def test_a_package_json_that_is_not_valid_json_is_noted_and_not_checked(tmp_path):
    write(tmp_path, {"node_modules/bad/package.json": "{not json"})
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "node_modules/bad/package.json couldn't be read" in got.stderr
    assert "No install scripts in 0 packages" in got.stdout
    write(tmp_path, {"node_modules/esbuild/package.json": ESBUILD})
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    assert "node_modules/bad/package.json couldn't be read" in got.stderr
    assert "node_modules/esbuild/package.json:5" in got.stdout


def test_a_package_json_that_is_not_utf8_is_still_checked(tmp_path):
    p = tmp_path / "node_modules" / "latin" / "package.json"
    p.parent.mkdir(parents=True)
    p.write_bytes(b'{"name": "caf\xe9", "scripts": {"postinstall": "node l.js"}}')
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    assert "postinstall   node l.js" in got.stdout


def test_a_directory_named_package_json_is_not_read(tmp_path):
    (tmp_path / "node_modules" / "dirpkg" / "package.json").mkdir(parents=True)
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stderr
    assert got.stderr == "" and "No node_modules folder here" in got.stdout


def test_any_depth_inside_node_modules_is_read(tmp_path):
    write(tmp_path, {
        "node_modules/a/node_modules/b/package.json": ESBUILD,
        "node_modules/package.json": ESBUILD,
    })  # fmt: skip
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    assert re.search(
        r"    node_modules/a/node_modules/b/package\.json:5\s+postinstall", got.stdout
    )
    assert re.search(r"\n    node_modules/package\.json:5\s+postinstall", got.stdout)
    assert "2 install scripts in 2 packages" in got.stdout


def test_scanning_a_node_modules_folder_itself_works(tmp_path):
    write(tmp_path, {"node_modules/esbuild/package.json": ESBUILD})
    got = run("--from", str(tmp_path / "node_modules"))
    assert got.returncode == 42, got.stderr
    assert (
        "    esbuild/package.json:5   postinstall   node install.js"
        in got.stdout.splitlines()
    )


def test_a_command_is_shown_on_one_line_and_a_non_string_as_json(tmp_path):
    write(tmp_path, {
        "node_modules/one/package.json": '{"scripts": {"postinstall": "echo one\\necho two"}}',
        "node_modules/two/package.json": '{"scripts": {"postinstall": ["node", "x.js"]}}',
    })  # fmt: skip
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    assert "postinstall   echo one\\necho two" in got.stdout
    assert 'postinstall   ["node", "x.js"]' in got.stdout


def test_a_box_is_scanned_from_its_pile(tmp_path):
    pile = tmp_path / "pile"
    write(pile, {"node_modules/esbuild/package.json": ESBUILD, "garden.md": "Sun.\n"})
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
                    str(pile), "--key", str(tmp_path / "key")], check=True,
                   capture_output=True)  # fmt: skip
    got = run("--box", str(box))
    assert got.returncode == 42, got.stderr
    assert "node_modules/esbuild/package.json:5   postinstall" in got.stdout


def test_it_writes_nothing(tmp_path):
    write(tmp_path, {
        "node_modules/esbuild/package.json": ESBUILD,
        "node_modules/left-pad/package.json": '{"name": "left-pad"}',
        "garden.md": "Sun.\n",
    })  # fmt: skip
    before = snapshot(tmp_path)
    run("--from", str(tmp_path))
    assert snapshot(tmp_path) == before


def test_a_bad_command_line_is_refused_and_says_how_to_run_it(tmp_path):
    for argv in (
        [],
        ["--box"],
        ["--from"],
        ["--from", str(tmp_path), "--box", str(tmp_path)],
        ["--from", str(tmp_path), "stray"],
        ["--from", ""],
        ["--from", "x", "--box", ""],
    ):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "install_scripts.py" in got.stderr, (
            argv,
            got.stderr,
        )


def test_a_bad_target_is_refused(tmp_path):
    got = run("--from", str(tmp_path / "missing"))
    assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr
    got = run("--box", str(tmp_path))
    assert got.returncode == 2 and "not a kernel box" in got.stderr, got.stderr
