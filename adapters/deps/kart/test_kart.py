"""kart: a job someone sent you runs only once you seal it, only in the
sandbox, only over your folder read-only, and what it found waits on your
seal. Needs Kartikeya and bubblewrap: without them these fail, they never skip."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KART = HERE / "kart.py"
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv, env=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL, env=env)  # fmt: skip


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
        self.pub = run(SHARE, "id", "--to", self.id).stdout.strip()

    def rows(self) -> list[dict]:
        return [
            json.loads(x) for x in (self.box / "record.jsonl").read_text().splitlines()
        ]

    def propose(self, words: str, prop: dict) -> str:
        run(KERNEL, "bite", "--box", self.box, words, *NOW)
        sug = self.dir / "s.jsonl"
        sug.write_text(json.dumps(prop) + "\n")
        out = run(KERNEL, "propose", "--box", self.box, "--file", sug, *NOW).stdout
        return out.split()[1]

    def seal(self, subj: str) -> None:
        got = run(KERNEL, "seal", "--box", self.box, subj, *NOW)
        assert got.returncode == 0, got.stderr

    def job(self, text: str, words: str = "my own job") -> str:
        """A job written and sealed by the person: as `take` leaves one."""
        subj = self.propose(words, {"path": "kart/jobs/j.sh", "data": text,
                                    "cites": [], "claim": "mine"})  # fmt: skip
        self.seal(subj)
        return subj

    def kart(self, *argv, env=None) -> subprocess.CompletedProcess:
        return run(KART, argv[0], "--box", self.box, *argv[1:], env=env)


NOTES = {
    "cases.md": "Johnson roof: fifteen tiles.\nKessler: a pipe.\nJohnson ceiling stain.\n"
}


@pytest.fixture
def walt(tmp_path):
    return Person(tmp_path, "walt", NOTES)


def seals(p: Person) -> int:
    return sum(r["kind"] == "seal" for r in p.rows())


# ── the sandbox ─────────────────────────────────────────────────────────────
def test_a_job_sees_your_folder_read_only_and_nothing_else(walt, tmp_path):
    """The probe a stranger's job would try: the key, the box, writing your
    folder, the network, your environment. Only the folder and scratch."""
    probe = f"""
echo "folder: $(cat {{pile}}/cases.md | head -1)"
echo "key: $(cat {walt.key} 2>/dev/null | wc -c)"
echo "box: $(ls {walt.box} 2>/dev/null | wc -l)"
(echo x > {{pile}}/new) 2>/dev/null && echo "folder write: yes" || echo "folder write: no"
echo ok > {{scratch}}/x && echo "scratch write: $(cat {{scratch}}/x)"
getent hosts example.com >/dev/null 2>&1 && echo "dns: yes" || echo "dns: no"
echo "planted: ${{KART_PROBE_PLANTED:-none}}"
echo "home: $(ls ~ 2>/dev/null | wc -l)"
"""
    subj = walt.job(probe)
    env = {**os.environ, "KART_PROBE_PLANTED": "hunter2"}
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "out.txt", *NOW, env=env)
    assert got.returncode == 42, got.stdout + got.stderr
    out = (tmp_path / "out.txt").read_text()
    assert out.splitlines() == [
        "folder: Johnson roof: fifteen tiles.", "key: 0", "box: 0", "folder write: no",
        "scratch write: ok", "dns: no", "planted: none", "home: 0",
    ], out  # fmt: skip
    assert not (walt.dir / "pile" / "new").exists()


def test_a_run_is_on_your_record_without_its_output(walt, tmp_path):
    subj = walt.job("grep -rhi johnson {pile} | wc -l")
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "out.txt", *NOW)
    assert got.returncode == 42 and "completed, exit 0" in got.stdout
    out = (tmp_path / "out.txt").read_text()
    assert out.strip() == "2"
    [ran] = [r for r in walt.rows() if r["kind"] == "ran"]
    assert (ran["job"], ran["status"], ran["returncode"], ran["who"]) == (
        subj,
        "completed",
        0,
        "kart",
    )
    assert ran["output_sha256"] == hashlib.sha256(out.encode()).hexdigest()
    assert (
        ran["engine"] == "bwrap"
        and ran["network"] == "isolated"
        and ran["bound_rw"] == 1
    )
    assert str((walt.dir / "pile").resolve()) in ran["bound_ro"]
    assert str(walt.box.resolve()) not in json.dumps(ran["bound_ro"])
    assert "Johnson" not in (walt.box / "record.jsonl").read_text(), (
        "the record keeps no output"
    )
    assert run(KERNEL, "verify", "--box", walt.box).stdout.startswith("the chain holds")


def test_what_a_job_found_waits_on_your_seal(walt, tmp_path):
    subj = walt.job("grep -rhi johnson {pile} | wc -l")
    before = seals(walt)
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "out.txt", *NOW)
    result = got.stdout.splitlines()[-1].split()[1]
    assert "waiting on your seal" in got.stdout and seals(walt) == before
    prop = json.loads((walt.box / "proposals" / f"{result[9:]}.json").read_text())
    assert prop["data"].strip() == "2" and prop["cites"] == []
    assert prop["path"].startswith("kart/results/") and subj in prop["claim"]
    walt.seal(result)
    assert (walt.box / "written" / prop["path"]).read_text().strip() == "2"


def test_a_job_that_fails_is_recorded_and_proposes_nothing(walt, tmp_path):
    subj = walt.job("echo partial; exit 3")
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "out.txt", *NOW)
    assert got.returncode == 42
    [ran] = [r for r in walt.rows() if r["kind"] == "ran"]
    assert ran["status"] == "failed" and ran["returncode"] == 3
    assert not [r for r in walt.rows() if r["kind"] == "proposal" and r["n"] > ran["n"]]


def test_kartikeyas_own_scan_refuses_before_any_sandbox(walt, tmp_path):
    subj = walt.job(
        "python3 -c \"import socket; socket.socket().connect(('192.0.2.1', 4444))\""
    )
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "out.txt", *NOW)
    assert got.returncode == 42 and "failed" in got.stdout
    [ran] = [r for r in walt.rows() if r["kind"] == "ran"]
    assert ran["status"] == "failed" and "KART-SECURITY" in ran["refused"]
    assert ran["engine"] is None, "refused before a sandbox was built"


# ── what runs at all ────────────────────────────────────────────────────────
def test_only_a_job_you_sealed_runs(walt, tmp_path):
    subj = walt.propose("a job", {"path": "kart/jobs/j.sh", "data": "echo hi",
                                  "cites": [], "claim": "unsealed"})  # fmt: skip
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 2 and "is not a job you sealed" in got.stderr
    other = walt.propose("an answer", {"path": "notes/a.md", "data": "echo hi",
                                       "cites": [], "claim": "an answer"})  # fmt: skip
    walt.seal(other)
    got = walt.kart("run", "--job", other, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 2 and "not a job you took" in got.stderr
    assert not (tmp_path / "o").exists() and not [
        r for r in walt.rows() if r["kind"] == "ran"
    ]


@pytest.mark.parametrize(
    "line", ["# allow_net", "# allow_db", "  # ALLOW_NET", "# allow_localhost"]
)
def test_a_job_asking_for_the_network_never_runs(walt, tmp_path, line):
    subj = walt.job(f"{line}\necho hi")
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 2 and "asks for the network" in got.stderr
    assert not [r for r in walt.rows() if r["kind"] == "ran"]


def test_the_output_is_never_written_in_the_box_or_folder_or_over_a_file(
    walt, tmp_path
):
    subj = walt.job("echo hi")
    for to, why in ((walt.box / "o", "inside the box"), (walt.dir / "pile" / "o", "inside your folder"),
                    (tmp_path / "no" / "o", "never makes one")):  # fmt: skip
        got = walt.kart("run", "--job", subj, "--to", to, *NOW)
        assert got.returncode == 2 and why in got.stderr, got.stderr
    (tmp_path / "o").write_text("mine")
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 2 and (tmp_path / "o").read_text() == "mine"


def test_without_bubblewrap_it_refuses_and_names_it(walt, tmp_path):
    subj = walt.job("echo hi")
    env = {**os.environ, "PATH": str(tmp_path / "empty")}
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW, env=env)
    assert got.returncode == 2 and "bubblewrap isn't installed" in got.stderr


def test_the_policy_is_willows_and_says_so(walt):
    got = walt.kart("policy")
    assert got.returncode == 0
    pol = json.loads(got.stdout)
    assert pol["bind_read_only"] == ["/usr", str((walt.dir / "pile").resolve())]
    assert pol["bind_read_write"] == ["<scratch, made new for each run>"]
    for k in ("env_prefixes", "credential_env_prefixes", "db_env_prefixes", "bind_try"):
        assert pol[k] == [], k


# ── take: a job that came in a package ──────────────────────────────────────
@pytest.fixture
def sent(tmp_path, walt):
    """Ines seals a job and sends it to Walt, who receives it."""
    ines = Person(tmp_path, "ines", {"a.md": "Nothing much here.\n"})
    subj = ines.propose("job count johnson", {"path": "jobs/count.sh",
                        "data": "grep -rhi johnson {pile} | wc -l", "cites": [],
                        "claim": "how many lines name Johnson"})  # fmt: skip
    ines.seal(subj)
    pkg = tmp_path / "job.pkg"
    got = run(SHARE, "send", "--box", ines.box, "--id", ines.id, "--answer", subj,
              "--for", walt.pub, "--to", pkg, *NOW)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return ines, pkg


def test_a_received_job_is_taken_to_your_door_and_runs_once_you_seal_it(
    walt, sent, tmp_path
):
    ines, pkg = sent
    assert run(SHARE, "receive", "--box", walt.box, "--id", walt.id, "--package", pkg,
               *NOW).returncode == 0  # fmt: skip
    got = walt.kart("take", "--package", pkg, "--words", "count johnson for ines", *NOW)
    assert got.returncode == 42 and "waiting on your seal" in got.stdout, got.stderr
    subj = got.stdout.split()[1]
    prop = json.loads((walt.box / "proposals" / f"{subj[9:]}.json").read_text())
    assert prop["path"] == "kart/jobs/count.sh" and prop["cites"] == []
    assert ines.pub[:12] in prop["claim"]
    assert walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW).returncode == 2
    walt.seal(subj)
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 42 and (tmp_path / "o").read_text().strip() == "2"


def test_only_a_package_you_received_and_that_held_is_taken(walt, sent, tmp_path):
    _, pkg = sent
    got = walt.kart("take", "--package", pkg, "--words", "x", *NOW)
    assert (
        got.returncode == 2
        and "not a package your record says you received" in got.stderr
    )
    bad = json.loads(pkg.read_text())
    bad["note"] = "edited"
    (tmp_path / "bad.pkg").write_text(json.dumps(bad))
    got = walt.kart("take", "--package", tmp_path / "bad.pkg", "--words", "x", *NOW)
    assert got.returncode == 2 and "doesn't hold" in got.stderr


def test_a_job_asking_for_the_network_is_not_even_taken(walt, tmp_path):
    ines = Person(tmp_path, "ines", {"a.md": "x\n"})
    subj = ines.propose("job net", {"path": "jobs/n.sh", "data": "# allow_net\ncurl x",
                                    "cites": [], "claim": "net"})  # fmt: skip
    ines.seal(subj)
    run(SHARE, "send", "--box", ines.box, "--id", ines.id, "--answer", subj,
        "--for", walt.pub, "--to", tmp_path / "n.pkg", *NOW)  # fmt: skip
    run(
        SHARE,
        "receive",
        "--box",
        walt.box,
        "--id",
        walt.id,
        "--package",
        tmp_path / "n.pkg",
        *NOW,
    )
    got = walt.kart("take", "--package", tmp_path / "n.pkg", "--words", "x", *NOW)
    assert got.returncode == 2 and "asks for the network" in got.stderr


@pytest.mark.parametrize("argv", [[], ["go"], ["run", "--box", "x"], ["policy"],
                                  ["policy", "--box", "x", "--box", "y"]])  # fmt: skip
def test_a_bad_command_line_says_how_to_run_it(argv):
    got = run(KART, *argv)
    assert got.returncode == 2 and "kart.py policy" in got.stderr


def test_what_isnt_a_box_is_refused(tmp_path):
    for cmd in (["policy"], ["take", "--package", "p", "--words", "w"],
                ["run", "--job", "proposal:x", "--to", str(tmp_path / "o")]):  # fmt: skip
        got = run(KART, cmd[0], "--box", tmp_path, *cmd[1:])
        assert got.returncode == 2 and "not a kernel box" in got.stderr


# ── real data: the Johnson folders ──────────────────────────────────────────
def test_one_job_runs_over_two_peoples_folders_and_comes_back_sealed(tmp_path):
    """demo/johnson/jobs.py on make_life.py's own files: Ines's job, run by
    Walt and Aurelie over their folders, sealed by each, back to Ines."""
    import shutil  # noqa: PLC0415

    demo = ROOT / "demo" / "johnson"
    shutil.copy(demo / "make_life.py", tmp_path / "make_life.py")
    got = subprocess.run([sys.executable, str(tmp_path / "make_life.py")], cwd=tmp_path,
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    to = tmp_path / "jobs"
    got = run(demo / "jobs.py", "run", "--life", tmp_path / "life", "--to", to)
    assert got.returncode == 0, got.stdout + got.stderr
    doc = json.loads((to / "jobs.json").read_text())
    assert doc["wrong"] == []
    assert doc["results"] == {"walt": "cases.md\n1", "aurelie": "claims.md\n1"}
    assert doc["network_refused"]
    for who in ("walt", "aurelie"):
        kinds = doc[who]["kinds"]
        assert kinds.count("ran") == 1 and kinds.count("seal") == 2 and "sent" in kinds
        assert doc[who]["verify"].startswith("the chain holds")
    assert doc["ines"]["kinds"].count("received") == 2
