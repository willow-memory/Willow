"""licenses: the licence of each installed Python and npm package read from its
own metadata and put in a class, copyleft and undeclared ones listed by file
and line; an SPDX expression read through (OR picks, AND binds); free text
read by its words; a clean set clean; a bad command line refused; and nothing
written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "licenses.py"
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("licenses", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
P, W, S, U = mod.PERMISSIVE, mod.WEAK, mod.STRONG, mod.UNDECLARED


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def py(root: Path, name: str, extra: str, version: str = "1.0") -> None:
    d = root / f"{name}-{version}.dist-info"
    d.mkdir(parents=True)
    (d / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n{extra}\n\nlong description\n",
        encoding="utf-8",
    )


def npm(root: Path, name: str, body: dict) -> None:
    d = root / "node_modules" / name
    d.mkdir(parents=True)
    (d / "package.json").write_text(
        json.dumps({"name": name, "version": "2.0.0", **body}, indent=1),
        encoding="utf-8",
    )


def test_an_expression_is_read_through_or_picks_and_and_binds():
    assert mod.expression_class("MIT") == P
    assert mod.expression_class("MIT OR GPL-3.0-only") == P  # you may pick MIT
    assert mod.expression_class("MIT AND GPL-3.0-or-later") == S  # both apply
    assert mod.expression_class("(MIT OR Apache-2.0) AND LGPL-2.1+") == W
    assert mod.expression_class("GPL-2.0-only WITH Classpath-exception-2.0") == S
    assert mod.expression_class("Apache-2.0 OR (GPL-2.0 AND MIT)") == P
    assert mod.expression_class("Weird-License-1.0") == U
    assert mod.expression_class("") == U


def test_free_text_is_read_by_its_words():
    assert mod.text_class("GNU Affero General Public License v3") == S
    assert mod.text_class("GNU Lesser General Public License v3 (LGPLv3)") == W
    assert mod.text_class("GNU General Public License v2 or later (GPLv2+)") == S
    assert mod.text_class("Mozilla Public License 2.0 (MPL 2.0)") == W
    assert mod.text_class("MIT License") == P and mod.text_class("BSD-3-Clause") == P
    assert mod.text_class("Apache Software License") == P
    assert mod.text_class("Something Proprietary And Long Winded") == U


def test_a_copyleft_package_is_listed_with_its_file_and_line(tmp_path):
    py(tmp_path, "gpl_thing", "License-Expression: GPL-3.0-or-later")
    py(tmp_path, "fine", "License-Expression: MIT")
    got = run("--from", str(tmp_path))
    assert got.returncode == 42, got.stderr
    out = got.stdout
    assert out.splitlines()[0] == "strong copyleft"
    assert "gpl_thing 1.0" in out and "gpl_thing-1.0.dist-info/METADATA:4" in out
    assert "GPL-3.0-or-later" in out and "fine" not in out.split("\n\n")[0]
    assert "2 packages: 1 permissive, 1 strong copyleft." in out


def test_classifiers_are_used_when_there_is_no_expression_and_dual_picks_the_easier(
    tmp_path,
):
    py(tmp_path, "dual", "Classifier: License :: OSI Approved :: MIT License\n"
                         "Classifier: License :: OSI Approved :: GNU General Public License v3 (GPLv3)")  # fmt: skip
    py(
        tmp_path,
        "weak",
        "Classifier: License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    )
    got = run("--from", str(tmp_path))
    assert "weak copyleft" in got.stdout and "dual" not in got.stdout
    assert "1 permissive, 1 weak copyleft." in got.stdout


def test_a_license_line_and_a_missing_one_are_read_and_unknown_is_undeclared(tmp_path):
    py(tmp_path, "old", "License: GNU General Public License v2")
    py(tmp_path, "none", "License: UNKNOWN")
    py(tmp_path, "blank", "")
    got = run("--from", str(tmp_path))
    assert got.returncode == 42
    assert "strong copyleft" in got.stdout and "undeclared" in got.stdout
    assert "(none)" in got.stdout and "1 strong copyleft, 2 undeclared." in got.stdout


def test_npm_packages_are_read_in_node_modules_only(tmp_path):
    npm(tmp_path, "gnu", {"license": "AGPL-3.0"})
    npm(tmp_path, "oldstyle", {"licenses": [{"type": "MIT"}, {"type": "GPL-2.0"}]})
    npm(tmp_path, "ok", {"license": "ISC"})
    npm(tmp_path, "none", {})
    (tmp_path / "package.json").write_text('{"name": "mine", "license": "GPL-3.0"}')
    got = run("--from", str(tmp_path))
    assert got.returncode == 42
    assert "gnu 2.0.0" in got.stdout and "node_modules/gnu/package.json:4" in got.stdout
    assert "oldstyle" not in got.stdout and "mine" not in got.stdout  # OR picks MIT
    assert "4 packages: 2 permissive, 1 strong copyleft, 1 undeclared." in got.stdout


def test_all_permissive_is_clean(tmp_path):
    py(tmp_path, "a", "License-Expression: MIT OR GPL-3.0")
    npm(tmp_path, "b", {"license": "Apache-2.0"})
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == "2 packages: 2 permissive."


def test_nothing_installed_is_clean(tmp_path):
    got = run("--from", str(tmp_path))
    assert got.returncode == 0 and "No installed packages found" in got.stdout


def test_a_package_json_that_isnt_json_is_noted(tmp_path):
    d = tmp_path / "node_modules" / "bad"
    d.mkdir(parents=True)
    (d / "package.json").write_text("{nope")
    got = run("--from", str(tmp_path))
    assert "note: node_modules/bad/package.json couldn't be read" in got.stderr


def test_site_reads_this_pythons_packages():
    got = run("--site")
    assert got.returncode in (0, 42) and "packages:" in got.stdout


def test_a_box_is_read_through_its_pile_and_nothing_is_written(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    py(pile, "gpl_thing", "License-Expression: GPL-3.0-only")
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-10-29T00:00:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    before = {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()}
    got = run("--box", str(box))
    assert got.returncode == 42 and "gpl_thing" in got.stdout
    assert before == {p: p.read_bytes() for p in pile.rglob("*") if p.is_file()}


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in ([], ["--from"], ["--from", str(tmp_path), "stray"], ["--site", "--from", str(tmp_path)],
                 ["--from", str(tmp_path), "--box", str(tmp_path)]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and "licenses.py" in got.stderr
    assert run("--from", str(tmp_path / "missing")).returncode == 2
    assert run("--box", str(tmp_path)).returncode == 2
