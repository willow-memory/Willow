"""lockfiles: a lockfile as a heading and a line for each locked package; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "lockfiles.py"
spec = importlib.util.spec_from_file_location("lockfiles", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"lockfileVersion":3,"packages":{"":{"name":"app","version":"1.0.0"},"node_modules/lodash":{"version":"4.17.21","resolved":"x","integrity":"y"},'
    b'"node_modules/left-pad":{"version":"1.3.0"},"node_modules/a/node_modules/left-pad":{"version":"0.0.3"},"node_modules/@scope/pkg":{"version":"2.0.0"},"node_modules/bad":{}}}'
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def test_an_npm_lockfile_lists_each_package_and_version_in_name_order():
    assert mod.convert(SAMPLE, "package-lock.json") == (
        "lockfile: package-lock.json (npm), 4 packages\n@scope/pkg 2.0.0\nleft-pad 0.0.3\nleft-pad 1.3.0\nlodash 4.17.21\n"
    )


def test_an_old_npm_lockfile_nests_its_dependencies():
    old = b'{"lockfileVersion":1,"dependencies":{"a":{"version":"1.0.0","dependencies":{"b":{"version":"2.0.0"}}},"c":{"version":"3.0.0"},"d":{}}}'
    assert (
        mod.convert(old, "package-lock.json")
        == "lockfile: package-lock.json (npm), 3 packages\na 1.0.0\nb 2.0.0\nc 3.0.0\n"
    )


def test_toml_lockfiles_are_read_by_their_package_blocks():
    cargo = (
        b'# generated\nversion = 3\n\n[[package]]\nname = "serde"\nversion = "1.0.1"\nsource = "registry"\ndependencies = [\n "x",\n]\n\n'
        b'[[package]]\nname = "app"\nversion = "0.1.0"\n\n[package.metadata]\nname = "ignored"\nversion = "9"\n'
    )
    assert (
        mod.convert(cargo, "Cargo.lock")
        == "lockfile: Cargo.lock (cargo), 2 packages\napp 0.1.0\nserde 1.0.1\n"
    )
    assert mod.convert(cargo, "poetry.lock").startswith(
        "lockfile: poetry.lock (poetry)"
    )
    uv = b'version = 1\n\n[[package]]\nname = "requests"\nversion = "2.31.0"\nsource = { registry = "https://pypi.org/simple" }\n\n[[package]]\nname = "nover"\n'
    assert (
        mod.convert(uv, "uv.lock")
        == "lockfile: uv.lock (uv), 1 package\nrequests 2.31.0\n"
    )


def test_the_first_name_and_version_in_a_block_are_the_packages_and_names_sort_without_regard_to_case_then_by_case():
    twice = b'[[package]]\nname = "a"\nversion = "1"\nname = "b"\nversion = "2"\n'
    assert mod.toml_blocks(twice.decode()) == {("a", "1")}
    s = b"example.com/foo v1.0.0 h1:x=\nexample.com/Foo v2.0.0 h1:y=\nexample.com/bar v3.0.0 h1:z=\n"
    assert mod.convert(s, "go.sum").splitlines()[1:] == [
        "example.com/bar v3.0.0",
        "example.com/Foo v2.0.0",
        "example.com/foo v1.0.0",
    ]


def test_pnpm_keys_in_old_and_new_shapes_and_only_in_the_packages_sections():
    new = (
        b"lockfileVersion: '9.0'\nimporters:\n  .:\n    dependencies:\n      lodash:\n        version: 4.17.21\n\n"
        b"packages:\n\n  lodash@4.17.21:\n    resolution: {integrity: x}\n\n  '@scope/pkg@2.0.0':\n    resolution: {integrity: y}\n\n"
        b"snapshots:\n\n  lodash@4.17.21: {}\n  'react-dom@18.2.0(react@18.2.0)':\n    dependencies: {}\n"
    )
    assert (
        mod.convert(new, "pnpm-lock.yaml")
        == "lockfile: pnpm-lock.yaml (pnpm), 3 packages\n@scope/pkg 2.0.0\nlodash 4.17.21\nreact-dom 18.2.0\n"
    )
    old = b"lockfileVersion: 5.4\npackages:\n  /lodash/4.17.21:\n    resolution: {}\n  /@scope/pkg/2.0.0:\n    resolution: {}\n"
    assert (
        mod.convert(old, "pnpm-lock.yaml")
        == "lockfile: pnpm-lock.yaml (pnpm), 2 packages\n@scope/pkg 2.0.0\nlodash 4.17.21\n"
    )


def test_a_yarn_lockfile_takes_the_first_spec_name_and_the_version_line():
    y = b'# yarn lockfile v1\n\n"@scope/pkg@^1.0.0", "@scope/pkg@^1.2.0":\n  version "1.2.3"\n  resolved "x"\n\nlodash@^4.17.0:\n  version "4.17.21"\n'
    assert (
        mod.convert(y, "yarn.lock")
        == "lockfile: yarn.lock (yarn), 2 packages\n@scope/pkg 1.2.3\nlodash 4.17.21\n"
    )
    berry = b'__metadata:\n  version: 6\n\n"lodash@npm:^4.17.0":\n  version: 4.17.21\n  resolution: "lodash@npm:4.17.21"\n'
    assert (
        mod.convert(berry, "yarn.lock")
        == "lockfile: yarn.lock (yarn), 1 package\nlodash 4.17.21\n"
    )


def test_go_sum_lines_for_a_module_and_its_go_mod_are_one_package():
    s = b"golang.org/x/text v0.3.0 h1:abc=\ngolang.org/x/text v0.3.0/go.mod h1:def=\nrsc.io/quote v1.5.2 h1:ghi=\nbroken line\n"
    assert (
        mod.convert(s, "go.sum")
        == "lockfile: go.sum (go), 2 packages\ngolang.org/x/text v0.3.0\nrsc.io/quote v1.5.2\n"
    )


def test_the_kind_is_the_file_name_and_other_names_empty_files_and_bad_json_are_no_result_or_an_error():
    assert (
        mod.kind_of("package-lock.json") == "npm"
        and mod.kind_of("sub/Cargo.lock") == "cargo"
        and mod.kind_of("my.package-lock.json") == "npm"
    )
    assert (
        mod.kind_of("package.json") == ""
        and mod.kind_of("notes.txt") == ""
        and mod.kind_of("") == ""
    )
    assert (
        mod.convert(b"{}", "package-lock.json") is None
        and mod.convert(b"[]", "package-lock.json") is None
    )
    assert (
        mod.convert(b"", "Cargo.lock") is None
        and mod.convert(b"x", "notes.txt") is None
    )
    try:
        mod.convert(b"{nope", "package-lock.json")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_lockfile_with_no_package_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path, {"package-lock.json": SAMPLE, "empty/Cargo.lock": b"version = 3\n"}
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"app/package-lock.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "app/package-lock.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "app/package-lock.json": SAMPLE,
            ".hid/app/package-lock.json": SAMPLE,
            ".app/package-lock.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["app/package-lock.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"app/package-lock.json": SAMPLE})
    before = (tmp_path / "src" / "app/package-lock.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "app/package-lock.json.txt").read_bytes() == (
        out / "app/package-lock.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "app/package-lock.json").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"good.package-lock.json": SAMPLE, "bad.package-lock.json": b"{not json"},
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.package-lock.json.txt").is_file() and not (
        out / "bad.package-lock.json.txt"
    ).exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert (
        run(
            "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
        ).returncode
        == 2
    )


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "lockfiles.py" in got.stderr
