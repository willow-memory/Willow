"""package-contents: every member of a wheel, sdist, npm tarball or crate
listed, the code that runs on install cited by file and line, a clean package
clean, an escaping path flagged, a bad archive noted, a bad command line
refused, and nothing written or unpacked."""

from __future__ import annotations

import io
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "package_contents.py"
KERNEL = HERE.parents[2] / "kernel.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def wheel(path: Path, files: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return path


def tarball(path: Path, files: dict[str, str]) -> Path:
    with tarfile.open(path, "w:gz") as t:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return path


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}  # fmt: skip


def test_a_wheel_lists_every_file_and_flags_an_import_line_in_a_pth(tmp_path):
    w = wheel(tmp_path / "evil-1.0-py3-none-any.whl", {
        "evil/__init__.py": "x = 1\n",
        "evil.pth": "/some/path\nimport os; os.system('id')\n",
    })  # fmt: skip
    got = run("--from", str(w))
    assert got.returncode == 42, got.stderr
    assert "evil-1.0-py3-none-any.whl   wheel, 2 files" in got.stdout
    assert "evil/__init__.py" in got.stdout and "6 B" in got.stdout
    assert "evil.pth:2   import: the line runs at every Python start" in got.stdout
    assert "evil.pth:1" not in got.stdout  # a path line runs nothing
    assert "1 of 1 package would run code on install" in got.stdout


def test_a_wheel_without_a_pth_import_runs_nothing(tmp_path):
    wheel(tmp_path / "ok-1.0-py3-none-any.whl",
          {"ok/__init__.py": "", "ok.pth": "lib\n"})  # fmt: skip
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stderr
    assert "none would run code on install" in got.stdout


def test_an_sdist_runs_its_setup_py_and_its_build_backend(tmp_path):
    t = tarball(tmp_path / "pkg-1.0.tar.gz", {
        "pkg-1.0/PKG-INFO": "Name: pkg\n",
        "pkg-1.0/setup.py": "import os\n",
        "pkg-1.0/pyproject.toml": '[build-system]\nrequires = []\nbuild-backend = "mine"\nbackend-path = ["."]\n',
    })  # fmt: skip
    got = run("--from", str(t))
    assert got.returncode == 42, got.stderr
    assert "pkg-1.0.tar.gz   sdist, 3 files" in got.stdout
    assert "pkg-1.0/setup.py:1   setup.py: pip runs it" in got.stdout
    assert 'pkg-1.0/pyproject.toml:3   in-tree backend "mine"' in got.stdout


def test_an_npm_tarball_runs_its_hooks_cited_by_line(tmp_path):
    pj = '{\n "name": "x",\n "scripts": {\n  "build": "tsc",\n  "postinstall": "node a.js"\n }\n}\n'
    t = tarball(tmp_path / "x-1.0.0.tgz", {"package/package.json": pj})
    got = run("--from", str(t))
    assert got.returncode == 42, got.stderr
    assert "x-1.0.0.tgz   npm tarball, 1 file" in got.stdout
    assert "package/package.json:5   postinstall: node a.js" in got.stdout
    assert "build" not in got.stdout.split("runs on install:")[1]


def test_a_binding_gyp_runs_node_gyp_unless_an_install_script_is_set(tmp_path):
    files = {"package/package.json": '{"name": "n"}', "package/binding.gyp": "{}"}
    t = tarball(tmp_path / "n.tgz", files)
    got = run("--from", str(t))
    assert got.returncode == 42
    assert "package/binding.gyp:1   binding.gyp with no install script" in got.stdout


def test_a_crate_runs_its_build_script_and_a_proc_macro(tmp_path):
    cargo = '[package]\nname = "c"\n\n[lib]\nproc-macro = true\n'
    t = tarball(tmp_path / "c-0.1.0.crate", {
        "c-0.1.0/Cargo.toml": cargo,
        "c-0.1.0/build.rs": "fn main() {}\n",
    })  # fmt: skip
    got = run("--from", str(t))
    assert got.returncode == 42, got.stderr
    assert "c-0.1.0.crate   crate, 2 files" in got.stdout
    assert "c-0.1.0/build.rs:1   build script" in got.stdout
    assert "c-0.1.0/Cargo.toml:5   procedural macro" in got.stdout


def test_a_crate_naming_its_build_script_runs_that_one(tmp_path):
    cargo = '[package]\nname = "c"\nbuild = "gen.rs"\n'
    t = tarball(tmp_path / "c.crate", {"c-1/Cargo.toml": cargo, "c-1/gen.rs": ""})
    got = run("--from", str(t))
    assert got.returncode == 42 and "c-1/gen.rs:1   build script" in got.stdout


def test_a_clean_crate_and_sdist_run_nothing(tmp_path):
    tarball(tmp_path / "c.crate", {"c-1/Cargo.toml": '[package]\nname = "c"\n'})
    tarball(tmp_path / "p.tar.gz", {"p-1/PKG-INFO": "Name: p\n"})
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stderr
    assert "2 packages listed; none would run code on install." in got.stdout


def test_a_path_that_climbs_out_is_flagged(tmp_path):
    t = tarball(tmp_path / "x.tgz", {
        "package/package.json": '{"name": "x"}',
        "package/../../evil": "x",
    })  # fmt: skip
    got = run("--from", str(t))
    assert got.returncode == 42, got.stderr
    assert "paths that escape:" in got.stdout
    assert "package/../../evil   absolute or climbs out with .." in got.stdout


def test_a_folder_is_searched_at_any_depth_and_other_files_ignored(tmp_path):
    (tmp_path / "a/b").mkdir(parents=True)
    wheel(tmp_path / "a/b/ok-1.0-py3-none-any.whl", {"ok.py": ""})
    (tmp_path / "notes.txt").write_text("not a package")
    got = run("--from", str(tmp_path))
    assert got.returncode == 0 and "ok-1.0-py3-none-any.whl" in got.stdout
    assert "notes.txt" not in got.stdout


def test_no_package_file_is_clean(tmp_path):
    got = run("--from", str(tmp_path))
    assert got.returncode == 0 and "No package file here" in got.stdout


def test_a_broken_archive_is_noted_and_not_checked(tmp_path):
    (tmp_path / "bad.whl").write_bytes(b"not a zip")
    wheel(tmp_path / "ok.whl", {"ok.py": ""})
    got = run("--from", str(tmp_path))
    assert got.returncode == 0, got.stderr
    assert "note: bad.whl couldn't be opened as a package" in got.stderr
    assert "ok.whl   wheel, 1 file" in got.stdout


def test_a_box_is_read_through_its_pile(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    wheel(pile / "evil.whl", {"evil.pth": "import os\n"})
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", "2026-10-29T00:00:00Z"],
                   check=True, capture_output=True)  # fmt: skip
    got = run("--box", str(box))
    assert got.returncode == 42 and "evil.pth:1" in got.stdout


def test_nothing_is_unpacked_or_written(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    wheel(pile / "evil.whl", {"evil.pth": "import os\n", "../x": "y"})
    before = snapshot(tmp_path)
    run("--from", str(pile))
    assert snapshot(tmp_path) == before and not (tmp_path / "x").exists()


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in (
        [],
        ["--from"],
        ["--box"],
        ["--from", str(tmp_path), "--box", str(tmp_path)],
        ["--from", str(tmp_path), "stray"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "package_contents.py" in got.stderr
    assert run("--from", str(tmp_path / "missing")).returncode == 2
    assert run("--box", str(tmp_path)).returncode == 2


def test_a_binding_gyp_beside_an_install_script_adds_no_line_of_its_own(tmp_path):
    pj = '{"name": "n", "scripts": {"install": "node x.js"}}'
    t = tarball(
        tmp_path / "n.tgz", {"package/package.json": pj, "package/binding.gyp": "{}"}
    )
    got = run("--from", str(t))
    assert got.returncode == 42
    assert "install: node x.js" in got.stdout and "node-gyp" not in got.stdout


def test_sizes_are_shown_in_bytes_kilobytes_and_megabytes(tmp_path):
    wheel(tmp_path / "s.whl", {"a": "x" * 1023, "b": "x" * 2048, "c": "x" * (1 << 20)})
    out = run("--from", str(tmp_path)).stdout
    assert "1023 B" in out and "2.0 KB" in out and "1.0 MB" in out
    wheel(tmp_path / "s.whl", {"a": "x" * 1024, "b": "x" * ((1 << 20) - 1)})
    out = run("--from", str(tmp_path)).stdout
    assert "1.0 KB" in out and "1024.0 KB" in out
