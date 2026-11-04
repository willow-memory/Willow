"""wasi-python: a job that is a Python script runs on CPython for WebAssembly
over your folder read-only, sees nothing else, and its result waits on your
seal. Needs wasi-python: without it these fail, they never skip.

The runtime takes most of a minute to compile, once a process, so most of
these call the add-on here, in this process, with --to on sys.argv as the
guard reads it; the refusals, which never reach the runtime, run as a
person runs them."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PY = HERE / "wasi_py.py"
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
KART = ROOT / "adapters" / "deps" / "kart" / "kart.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]

sys.path.insert(0, str(HERE))
import wasi_py  # noqa: E402

COUNT = """import os
n = 0
for d, _, files in os.walk("{pile}"):
    for f in sorted(files):
        n += sum("johnson" in line.lower() for line in open(os.path.join(d, f)))
print(n)
"""
PROBE = """import os
print("folder", open("/pile/cases.md").readline().strip())
for what, do in (("write", lambda: open("/pile/new", "w")),
                 ("host", lambda: open("/etc/passwd")),
                 ("up", lambda: open("/pile/../key"))):
    try:
        do(); print(what, "yes")
    except OSError as e:
        print(what, "no")
try:
    import socket; socket.create_connection(("1.1.1.1", 80), 1); print("net yes")
except Exception:
    print("net no")
print("env", sorted(k for k in os.environ if k not in ("HOME", "TMPDIR", "PYTHONTZPATH")))
"""


def run(*argv, flags=()) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *flags, *map(str, argv)], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)  # fmt: skip


class Person:
    def __init__(self, root: Path, name: str, files: dict[str, str]):
        self.dir = root / name
        (self.dir / "pile").mkdir(parents=True)
        for rel, text in files.items():
            (self.dir / "pile" / rel).write_text(text)
        self.box, self.key, self.id = (
            self.dir / "box",
            self.dir / "key",
            self.dir / "id",
        )
        assert run(KERNEL, "init", "--box", self.box, "--pile", self.dir / "pile",
                   "--key", self.key, *NOW).returncode == 0  # fmt: skip
        self.pub = run(SHARE, "id", "--to", self.id).stdout.split()[0]

    def rows(self) -> list[dict]:
        return [
            json.loads(x) for x in (self.box / "record.jsonl").read_text().splitlines()
        ]

    def job(self, text: str) -> str:
        """A job taken and sealed, as `kart take` and the person leave one."""
        run(KERNEL, "bite", "--box", self.box, "my job", *NOW)
        (self.dir / "s.jsonl").write_text(
            json.dumps(
                {"path": "kart/jobs/j.py", "data": text, "cites": [], "claim": "mine"}
            )
            + "\n"
        )
        subj = run(KERNEL, "propose", "--box", self.box, "--file", self.dir / "s.jsonl",
                   *NOW).stdout.split()[1]  # fmt: skip
        assert run(KERNEL, "seal", "--box", self.box, subj, *NOW).returncode == 0
        return subj

    def py(self, monkeypatch, capsys, *argv) -> tuple[int, str]:
        """The add-on's command line, in this process."""
        args = ["run", "--box", str(self.box), *map(str, argv), *NOW]
        monkeypatch.setattr(sys, "argv", [str(PY), *args])
        code = wasi_py.main(args)
        return code, capsys.readouterr().out

    def ran(self) -> dict:
        return [r for r in self.rows() if r["kind"] == "ran"][-1]


NOTES = {
    "cases.md": "Johnson roof: fifteen tiles.\nKessler: a pipe.\nJohnson ceiling stain.\n"
}


@pytest.fixture
def walt(tmp_path):
    return Person(tmp_path, "walt", NOTES)


def test_a_script_reads_your_folder_and_its_result_waits_on_your_seal(
    walt, tmp_path, monkeypatch, capsys
):
    (walt.dir / "pile" / "sub").mkdir()
    (walt.dir / "pile" / "sub" / "more.md").write_text("Johnson again.\n")
    code, out = walt.py(monkeypatch, capsys, "--job", walt.job(COUNT), "--to",
                        tmp_path / "o.txt", "--shape", "numbers")  # fmt: skip
    assert code == 42, out
    assert (tmp_path / "o.txt").read_text() == "3\n"
    ran = walt.ran()
    assert (ran["who"], ran["status"], ran["returncode"], ran["network"]) == (
        "wasi-python", "completed", 0, "none")  # fmt: skip
    assert ran["engine"].startswith("wasi-python ") and sorted(ran["tools"]) == [
        "runtime",
        "stdlib",
    ]
    import wasi_python  # noqa: PLC0415

    snap = wasi_python.artifacts().snapshot
    assert ran["tools"]["runtime"] == hashlib.sha256(snap.read_bytes()).hexdigest()
    assert "Johnson" not in (walt.box / "record.jsonl").read_text()
    result = out.splitlines()[-1].split()[1]
    prop = json.loads((walt.box / "proposals" / f"{result[9:]}.json").read_text())
    assert prop["path"].startswith("kart/results/") and prop["data"] == "3\n"
    assert prop["claim"].endswith(
        f"job text {hashlib.sha256(COUNT.encode()).hexdigest()}"
    )
    assert not any(r["kind"] == "seal" and r["subject"] == result for r in walt.rows())


def test_it_sees_the_folder_read_only_and_nothing_else(
    walt, tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("WILLOW_PROBE_PLANTED", "hunter2")
    code, out = walt.py(
        monkeypatch, capsys, "--job", walt.job(PROBE), "--to", tmp_path / "o"
    )
    assert code == 42, out
    assert (tmp_path / "o").read_text().splitlines() == [
        "folder Johnson roof: fifteen tiles.", "write no", "host no", "up no", "net no", "env []",
    ]  # fmt: skip
    assert not (walt.dir / "pile" / "new").exists()


def test_two_people_one_runtime_and_gather_says_nothing_of_tools(
    tmp_path, monkeypatch, capsys
):
    ines = Person(tmp_path, "ines", {"a.md": "x\n"})
    backs = []
    for name, files in (("walt", NOTES), ("aurelie", {"c.md": "Johnson.\n"})):
        p = Person(tmp_path, name, files)
        code, out = p.py(monkeypatch, capsys, "--job", p.job(COUNT), "--to",
                         tmp_path / f"{name}.txt", "--shape", "numbers")  # fmt: skip
        result = out.splitlines()[-1].split()[1]
        assert run(KERNEL, "seal", "--box", p.box, result, *NOW).returncode == 0
        pkg = tmp_path / f"{name}.pkg"
        assert run(SHARE, "send", "--box", p.box, "--id", p.id, "--answer", result,
                   "--for", ines.pub, "--to", pkg, *NOW).returncode == 0  # fmt: skip
        assert run(SHARE, "receive", "--box", ines.box, "--id", ines.id, "--package",
                   pkg, *NOW).returncode == 0  # fmt: skip
        backs.append(str(pkg))
    got = run(KART, "gather", "--box", ines.box, "--package", ",".join(backs),
              "--words", "johnson lines", *NOW)  # fmt: skip
    assert got.returncode == 42, got.stdout + got.stderr
    assert "total          3  from 2 folders" in got.stdout
    assert "sets of tools" not in got.stdout


def test_a_script_that_fails_runs_out_of_fuel_or_breaks_its_shape_proposes_nothing(
    walt, tmp_path, monkeypatch, capsys
):
    before = sum(r["kind"] == "proposal" for r in walt.rows())
    code, out = walt.py(monkeypatch, capsys, "--job", walt.job("import sys; sys.exit(3)"),
                        "--to", tmp_path / "a")  # fmt: skip
    assert code == 42 and "failed, exit 3" in out
    code, out = walt.py(monkeypatch, capsys, "--job", walt.job("while True: pass"),
                        "--to", tmp_path / "b", "--fuel", "100000000")  # fmt: skip
    assert code == 42 and "out of fuel" in out
    code, out = walt.py(monkeypatch, capsys, "--job", walt.job("print('Johnson roof')"),
                        "--to", tmp_path / "c", "--shape", "numbers")  # fmt: skip
    assert code == 42 and "isn't numbers" in out
    assert (tmp_path / "c").read_text() == "Johnson roof\n", "it stays on your machine"
    assert sum(r["kind"] == "proposal" for r in walt.rows()) == before + 3, (
        "the three jobs, and no result"
    )


def test_only_a_job_you_sealed_runs_and_never_one_asking_for_the_network(
    walt, tmp_path
):
    run(KERNEL, "bite", "--box", walt.box, "unsealed", *NOW)
    (walt.dir / "u.jsonl").write_text(
        json.dumps({"path": "kart/jobs/u.py", "data": COUNT, "cites": [], "claim": "x"})
        + "\n"
    )
    unsealed = run(KERNEL, "propose", "--box", walt.box, "--file", walt.dir / "u.jsonl",
                   *NOW).stdout.split()[1]  # fmt: skip
    got = run(
        PY, "run", "--box", walt.box, "--job", unsealed, "--to", tmp_path / "o", *NOW
    )
    assert got.returncode == 2 and "not a job you sealed" in got.stderr
    net = walt.job("# allow_net\nimport urllib.request")
    got = run(PY, "run", "--box", walt.box, "--job", net, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 2 and "asks for the network" in got.stderr
    assert not (tmp_path / "o").exists()
    for flag, value, said in (("--shape", "words", "--shape is one of"),
                              ("--fuel", "0", "--fuel is at least 1")):  # fmt: skip
        got = run(PY, "run", "--box", walt.box, "--job", walt.job(COUNT), "--to",
                  tmp_path / "o", flag, value, *NOW)  # fmt: skip
        assert got.returncode == 2 and said in got.stderr


def test_without_wasi_python_it_refuses_and_names_it(walt, tmp_path):
    got = run(PY, "run", "--box", walt.box, "--job", walt.job(COUNT), "--to",
              tmp_path / "o", *NOW, flags=("-S",))  # fmt: skip
    assert got.returncode == 2 and "wasi-python isn't installed" in got.stderr


def test_a_bad_command_line_says_how_to_run_it(walt):
    for argv in ([], ["run"], ["run", "--box", walt.box], ["go", "--box", walt.box]):
        got = run(PY, *argv)
        assert got.returncode == 2 and "wasi_py.py run" in got.stderr


def snapshot(folder: Path) -> dict[str, tuple[int, int]]:
    return {
        p.name: (p.stat().st_size, p.stat().st_mtime_ns)
        for p in sorted(folder.iterdir())
    }


def test_warm_keeps_the_runtime_compiled_and_run_only_reads_it(walt, tmp_path):
    """index-cache's way: made once in a folder you name, left alone while it
    is current, and read by run, which then starts in a moment."""
    cache = tmp_path / "cache"
    cache.mkdir(mode=0o700)
    got = run(PY, "warm", "--to", cache)
    assert got.returncode == 0 and got.stdout.startswith("compiled"), (
        got.stdout + got.stderr
    )
    assert (cache / "wasi-py.json").is_file() and list(cache.glob("*.cwasm"))
    made = snapshot(cache)
    got = run(PY, "warm", "--to", cache)
    assert got.returncode == 0 and got.stdout.startswith("current")
    got = run(PY, "run", "--box", walt.box, "--job", walt.job(COUNT), "--to",
              tmp_path / "o", "--shape", "numbers", "--cache", cache, *NOW)  # fmt: skip
    assert got.returncode == 42, got.stdout + got.stderr
    assert (tmp_path / "o").read_text() == "2\n" and walt.ran()["cache"] == "used"
    assert snapshot(cache) == made, "a run never writes the cache"


def test_a_cache_made_for_another_runtime_is_left_alone(
    walt, tmp_path, monkeypatch, capsys
):
    cache = tmp_path / "cache"
    cache.mkdir(mode=0o700)
    (cache / "wasi-py.json").write_text(
        json.dumps({"tools": {}, "wasi-python": "0.0.1"})
    )
    before = snapshot(cache)
    code, out = walt.py(monkeypatch, capsys, "--job", walt.job(COUNT), "--to", tmp_path / "o",
                        "--cache", cache)  # fmt: skip
    assert code == 42 and "is stale for this runtime" in out
    assert walt.ran()["cache"] == "stale" and snapshot(cache) == before


def test_warm_refuses_a_folder_that_isnt_a_cache(tmp_path):
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "a.md").write_text("mine\n")
    got = run(PY, "warm", "--to", tmp_path / "notes")
    assert got.returncode == 2 and "holds other things" in got.stderr
    got = run(PY, "warm", "--to", tmp_path / "cache")
    assert got.returncode == 2 and "make it first" in got.stderr
    assert not (tmp_path / "cache").exists(), "making a folder is a write"
    (tmp_path / "f").write_text("x")
    got = run(PY, "warm", "--to", tmp_path / "f")
    assert got.returncode == 2 and "is not a folder" in got.stderr
    open_ = tmp_path / "open"
    open_.mkdir()
    (open_ / "wasi-py.json").write_text("{}")
    open_.chmod(0o777)
    got = run(PY, "warm", "--to", open_)
    assert got.returncode == 2 and "written by others" in got.stderr
