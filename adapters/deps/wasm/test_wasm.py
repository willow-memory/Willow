"""wasm: a job that is WebAssembly runs over your folder read-only, sees
nothing else, and answers the same wherever its bytes run. Needs Wasmtime:
without it these fail, they never skip.

The jobs are small modules in WebAssembly's text format, written here:
WASI's preview 1 calls, a page of memory, nothing else."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
WASM = HERE / "wasm.py"
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
KART = ROOT / "adapters" / "deps" / "kart" / "kart.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]

WASI = """
 (import "wasi_snapshot_preview1" "path_open"
   (func $path_open (param i32 i32 i32 i32 i32 i64 i64 i32 i32) (result i32)))
 (import "wasi_snapshot_preview1" "fd_read" (func $fd_read (param i32 i32 i32 i32) (result i32)))
 (import "wasi_snapshot_preview1" "fd_write" (func $fd_write (param i32 i32 i32 i32) (result i32)))
 (memory (export "memory") 1)
 (func $print (param $n i32) (local $p i32)
   (local.set $p (i32.const 300))
   (i32.store8 (local.get $p) (i32.const 10))
   (loop $l
     (local.set $p (i32.sub (local.get $p) (i32.const 1)))
     (i32.store8 (local.get $p) (i32.add (i32.const 48) (i32.rem_u (local.get $n) (i32.const 10))))
     (local.set $n (i32.div_u (local.get $n) (i32.const 10)))
     (br_if $l (local.get $n)))
   (i32.store (i32.const 32) (local.get $p))
   (i32.store (i32.const 36) (i32.sub (i32.const 301) (local.get $p)))
   (drop (call $fd_write (i32.const 1) (i32.const 32) (i32.const 1) (i32.const 40))))
 (func $open (param $dir i32) (param $len i32) (param $oflags i32) (param $rights i64) (result i32)
   (call $path_open (local.get $dir) (i32.const 0) (i32.const 1024) (local.get $len)
         (local.get $oflags) (local.get $rights) (i64.const 0) (i32.const 0) (i32.const 16)))
 (func $read (param $fd i32) (result i32)
   (i32.store (i32.const 0) (i32.const 4096)) (i32.store (i32.const 4) (i32.const 4096))
   (drop (call $fd_read (local.get $fd) (i32.const 0) (i32.const 1) (i32.const 8)))
   (i32.load (i32.const 8)))
"""


def module(path: str, body: str) -> str:
    return f'(module {WASI} (data (i32.const 1024) "{path}") (func (export "_start") {body}))'


def count(path: str = "cases.md") -> str:
    """Prints the lines of one file in the folder; its errno if it can't open it."""
    return module(
        path,
        f"""(local $e i32) (local $fd i32) (local $n i32) (local $i i32) (local $c i32)
      (local.set $e (call $open (i32.const 3) (i32.const {len(path)}) (i32.const 0) (i64.const 2)))
      (if (local.get $e) (then (call $print (i32.add (i32.const 1000) (local.get $e))) (return)))
      (local.set $fd (i32.load (i32.const 16)))
      (block $done (loop $rd
        (local.set $n (call $read (local.get $fd)))
        (br_if $done (i32.eqz (local.get $n)))
        (local.set $i (i32.const 0))
        (loop $ch
          (if (i32.eq (i32.load8_u (i32.add (i32.const 4096) (local.get $i))) (i32.const 10))
            (then (local.set $c (i32.add (local.get $c) (i32.const 1)))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br_if $ch (i32.lt_u (local.get $i) (local.get $n))))
        (br $rd)))
      (call $print (local.get $c))""",
    )


def tries(path: str, oflags: int, rights: int) -> str:
    """Prints 0 if it could open PATH so, or its errno."""
    return module(
        path,
        f"""(call $print (call $open (i32.const 3) (i32.const {len(path)})
      (i32.const {oflags}) (i64.const {rights})))""",
    )


#: a runtime: prints the script it is given at /job/job, as an interpreter reads one
CAT = module(
    "job",
    """(local $e i32) (local $fd i32) (local $n i32)
  (local.set $e (call $open (i32.const 4) (i32.const 3) (i32.const 0) (i64.const 2)))
  (if (local.get $e) (then (call $print (local.get $e)) (return)))
  (local.set $fd (i32.load (i32.const 16)))
  (block $done (loop $rd
    (local.set $n (call $read (local.get $fd)))
    (br_if $done (i32.eqz (local.get $n)))
    (i32.store (i32.const 0) (i32.const 4096)) (i32.store (i32.const 4) (local.get $n))
    (drop (call $fd_write (i32.const 1) (i32.const 0) (i32.const 1) (i32.const 8)))
    (br $rd)))""",
)
SPIN = '(module (func (export "_start") (loop $l (br $l))))'
EXIT3 = """(module (import "wasi_snapshot_preview1" "proc_exit" (func $exit (param i32)))
  (memory (export "memory") 1) (func (export "_start") (call $exit (i32.const 3))))"""


def run(*argv, flags=()) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *flags, *map(str, argv)], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)  # fmt: skip


class Person:
    def __init__(self, root: Path, name: str, files: dict[str, str]):
        self.root, self.dir = root, root / name
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
                {"path": "kart/jobs/j.wat", "data": text, "cites": [], "claim": "mine"}
            )
            + "\n"
        )
        subj = run(KERNEL, "propose", "--box", self.box, "--file", self.dir / "s.jsonl",
                   *NOW).stdout.split()[1]  # fmt: skip
        self.seal(subj)
        return subj

    def seal(self, subj: str) -> None:
        assert run(KERNEL, "seal", "--box", self.box, subj, *NOW).returncode == 0

    def wasm(self, *argv) -> subprocess.CompletedProcess:
        return run(WASM, "run", "--box", self.box, *argv, *NOW)

    def ran(self) -> dict:
        return [r for r in self.rows() if r["kind"] == "ran"][-1]


NOTES = {
    "cases.md": "Johnson roof: fifteen tiles.\nKessler: a pipe.\nJohnson ceiling stain.\n"
}


@pytest.fixture
def walt(tmp_path):
    return Person(tmp_path, "walt", NOTES)


def test_a_module_reads_your_folder_and_its_result_waits_on_your_seal(walt, tmp_path):
    subj = walt.job(count())
    got = walt.wasm("--job", subj, "--to", tmp_path / "o.txt", "--shape", "numbers")
    assert got.returncode == 42, got.stdout + got.stderr
    assert (tmp_path / "o.txt").read_text() == "3\n"
    ran = walt.ran()
    assert (ran["who"], ran["status"], ran["returncode"], ran["network"]) == (
        "wasm", "completed", 0, "none")  # fmt: skip
    assert ran["engine"].startswith("wasmtime ") and ran["fuel"] > 0
    import wasmtime  # noqa: PLC0415

    want = hashlib.sha256(wasmtime.wat2wasm(count())).hexdigest()
    assert ran["tools"] == {"module": want}
    assert "Johnson" not in (walt.box / "record.jsonl").read_text()
    result = got.stdout.splitlines()[-1].split()[1]
    prop = json.loads((walt.box / "proposals" / f"{result[9:]}.json").read_text())
    assert prop["path"].startswith("kart/results/") and prop["data"] == "3\n"
    assert prop["claim"].endswith(
        f"job text {hashlib.sha256(count().encode()).hexdigest()}"
    )
    assert not any(r["kind"] == "seal" and r["subject"] == result for r in walt.rows())


def test_it_sees_the_folder_read_only_and_nothing_above_it(walt, tmp_path):
    (walt.dir / "pile" / "sub").mkdir()
    cases = [
        (tries("new", 1, 64), "write"),  # O_CREAT, fd_write
        (tries("cases.md", 0, 64), "write"),  # an existing file, for writing
        (tries("../key", 0, 2), "escape"),
        (tries("/etc/passwd", 0, 2), "escape"),
        (count("../box/record.jsonl"), "escape"),
    ]
    for i, (job, what) in enumerate(cases):
        got = walt.wasm("--job", walt.job(job), "--to", tmp_path / f"o{i}")
        printed = (tmp_path / f"o{i}").read_text().strip()
        assert got.returncode == 42 and printed not in ("0", "", "3"), (what, printed)
    assert not (walt.dir / "pile" / "new").exists()
    assert (walt.dir / "pile" / "cases.md").read_text() == NOTES["cases.md"]


def test_the_same_module_answers_alike_and_says_so_to_gather(tmp_path):
    """Two people, one module: the same tools, so gather says nothing of tools."""
    ines = Person(tmp_path, "ines", {"a.md": "x\n"})
    backs = []
    for name, files in (("walt", NOTES), ("aurelie", {"cases.md": "Johnson.\n"})):
        p = Person(tmp_path, name, files)
        got = p.wasm("--job", p.job(count()), "--to", tmp_path / f"{name}.txt",
                     "--shape", "numbers")  # fmt: skip
        result = got.stdout.splitlines()[-1].split()[1]
        p.seal(result)
        pkg = tmp_path / f"{name}.pkg"
        assert run(SHARE, "send", "--box", p.box, "--id", p.id, "--answer", result,
                   "--for", ines.pub, "--to", pkg, *NOW).returncode == 0  # fmt: skip
        assert run(SHARE, "receive", "--box", ines.box, "--id", ines.id, "--package",
                   pkg, *NOW).returncode == 0  # fmt: skip
        backs.append(str(pkg))
    got = run(KART, "gather", "--box", ines.box, "--package", ",".join(backs),
              "--words", "johnson lines", *NOW)  # fmt: skip
    assert got.returncode == 42, got.stdout + got.stderr
    assert "total          4  from 2 folders" in got.stdout
    assert "sets of tools" not in got.stdout


def test_a_runtime_of_yours_runs_the_jobs_script(walt, tmp_path):
    runtime = tmp_path / "cat.wasm"
    import wasmtime  # noqa: PLC0415

    runtime.write_bytes(wasmtime.wat2wasm(CAT))
    script = "print(len(open('{pile}/cases.md').readlines()))\n"
    got = walt.wasm(
        "--job", walt.job(script), "--to", tmp_path / "o", "--runtime", runtime
    )
    assert got.returncode == 42, got.stdout + got.stderr
    assert (tmp_path / "o").read_text() == script.replace("{pile}", "/pile")
    assert walt.ran()["tools"] == {
        "runtime": hashlib.sha256(runtime.read_bytes()).hexdigest()
    }
    (tmp_path / "not.wasm").write_text("print(1)")
    got = walt.wasm("--job", walt.job(script), "--to", tmp_path / "o2",
                    "--runtime", tmp_path / "not.wasm")  # fmt: skip
    assert got.returncode == 2 and "isn't a WebAssembly module" in got.stderr


def test_a_job_that_runs_out_of_fuel_or_fails_proposes_nothing(walt, tmp_path):
    before = sum(r["kind"] == "proposal" for r in walt.rows())
    got = walt.wasm("--job", walt.job(SPIN), "--to", tmp_path / "a", "--fuel", "100000")
    assert got.returncode == 42 and "out of fuel" in got.stdout
    got = walt.wasm("--job", walt.job(EXIT3), "--to", tmp_path / "b")
    assert got.returncode == 42 and "failed, exit 3" in got.stdout
    assert walt.ran()["returncode"] == 3
    assert sum(r["kind"] == "proposal" for r in walt.rows()) == before + 2, (
        "the two jobs, and no result"
    )


def test_a_base64_module_runs_as_its_text_does(walt, tmp_path):
    import wasmtime  # noqa: PLC0415

    b64 = "wasm:" + base64.b64encode(wasmtime.wat2wasm(count())).decode()
    got = walt.wasm("--job", walt.job(b64), "--to", tmp_path / "o")
    assert got.returncode == 42 and (tmp_path / "o").read_text() == "3\n"
    for bad, said in (("wasm:%%%", "isn't base64"), ("(module (func", "doesn't compile"),
                      ("grep -r x {pile}", "isn't a module")):  # fmt: skip
        got = walt.wasm("--job", walt.job(bad), "--to", tmp_path / f"x{len(bad)}")
        assert got.returncode == 2 and said in got.stderr, got.stderr


def test_only_a_job_you_sealed_runs_and_never_one_asking_for_the_network(
    walt, tmp_path
):
    run(KERNEL, "bite", "--box", walt.box, "unsealed", *NOW)
    (walt.dir / "u.jsonl").write_text(
        json.dumps(
            {"path": "kart/jobs/u.wat", "data": count(), "cites": [], "claim": "x"}
        )
        + "\n"
    )
    unsealed = run(KERNEL, "propose", "--box", walt.box, "--file", walt.dir / "u.jsonl",
                   *NOW).stdout.split()[1]  # fmt: skip
    got = walt.wasm("--job", unsealed, "--to", tmp_path / "o")
    assert got.returncode == 2 and "not a job you sealed" in got.stderr
    got = walt.wasm(
        "--job", walt.job("# allow_net\n" + count()), "--to", tmp_path / "o"
    )
    assert got.returncode == 2 and "asks for the network" in got.stderr
    assert not (tmp_path / "o").exists()
    (tmp_path / "there").write_text("mine")
    got = walt.wasm("--job", walt.job(count()), "--to", tmp_path / "there")
    assert got.returncode == 2 and (tmp_path / "there").read_text() == "mine"


def test_without_wasmtime_it_refuses_and_names_it(walt, tmp_path):
    subj = walt.job(count())
    got = run(WASM, "run", "--box", walt.box, "--job", subj, "--to", tmp_path / "o",
              *NOW, flags=("-S",))  # fmt: skip
    assert got.returncode == 2 and "Wasmtime isn't installed" in got.stderr


def test_a_bad_command_line_says_how_to_run_it(walt):
    for argv in ([], ["run"], ["run", "--box", walt.box], ["go", "--box", walt.box]):
        got = run(WASM, *argv)
        assert got.returncode == 2 and "wasm.py run" in got.stderr
    got = run(WASM, "run", "--box", walt.dir / "x", "--job", "proposal:" + "0" * 64,
              "--to", walt.dir / "o")  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr
