"""kart: a job someone sent you runs only once you seal it, only in the
sandbox, only over your folder read-only, and what it found waits on your
seal. Needs Kartikeya and bubblewrap: without them these fail, they never skip."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
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
KEEP_GROUP: set[str] = set()  # a test that means the group puts its name here


def run(*argv, env=None) -> subprocess.CompletedProcess:
    # a resource group this machine exports for a fleet is not these tests'
    env = {k: v for k, v in (os.environ if env is None else env).items()
           if k != "KART_CGROUP_PARENT" or k in KEEP_GROUP}  # fmt: skip
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


def test_a_job_runs_on_the_systems_path_and_locale_not_yours(walt, tmp_path):
    """Your PATH and LANG change what a job's grep and sort say; the same job
    over everyone's folders should differ only by what the folders hold."""
    subj = walt.job('echo "$LANG"; echo "$PATH"')
    env = {
        **os.environ,
        "LANG": "tr_TR.UTF-8",
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
    }
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW, env=env)
    assert got.returncode == 42, got.stdout + got.stderr
    lang, path = (tmp_path / "o").read_text().splitlines()
    assert lang == "C" and path.split(":")[:2] == ["/usr/bin", "/bin"]
    assert str(tmp_path) not in path


def test_a_fleets_settings_in_your_environment_never_reach_a_job(walt, tmp_path):
    """A machine that also runs a fleet's Kartikeya has its settings exported:
    WILLOW_ROOT would put that fleet's venv first on the job's PATH, and
    Kartikeya adds its own (where it is installed, the Python it runs on, a
    sender's name). A job's environment is three variables of kart's and the
    shell's own, and no path of the person's."""
    fleet = tmp_path / "fleet"
    (fleet / ".venv" / "bin").mkdir(parents=True)
    conf = tmp_path / "theirs.json"
    conf.write_text(json.dumps({"version": 1, "bind_read_only": [str(walt.box)]}))
    subj = walt.job("env | sort; echo \"box: $(ls " + str(walt.box) + " 2>/dev/null | wc -l)\"")  # fmt: skip
    env = {**os.environ, "WILLOW_ROOT": str(fleet), "KART_SANDBOX_CONFIG": str(conf),
           "KART_PROBE": "planted", "WILLOW_HOME": str(fleet),
           "GROVE_SENDER": "walt-on-github"}  # fmt: skip
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW, env=env)
    assert got.returncode == 42, got.stdout + got.stderr
    out = (tmp_path / "o").read_text()
    *held, box = out.splitlines()
    names = {line.partition("=")[0] for line in held}
    assert names == {"HOME", "LANG", "PATH", "PWD", "SHLVL", "_"}, out
    assert "PATH=/usr/bin:/bin" in held and "LANG=C" in held and box == "box: 0"
    for theirs in ("fleet", "walt-on-github", "planted", str(Path.home()), sys.prefix,
                   "site-packages"):  # fmt: skip
        assert theirs not in out, theirs
    [ran] = [r for r in walt.rows() if r["kind"] == "ran"]
    assert ran["status"] == "completed" and str(walt.box) not in json.dumps(ran)


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
    assert sorted(ran["tools"]) == ["bash", "grep", "wc"] and ran["locale"] == "C"
    grep = Path(shutil.which("grep", path="/usr/bin:/bin")).resolve()
    assert ran["tools"]["grep"] == hashlib.sha256(grep.read_bytes()).hexdigest()
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


def test_a_bubblewrap_that_cant_sandbox_here_refuses_before_anything_runs(
    walt, tmp_path
):
    """Installed but forbidden its namespaces, as in a default Docker container
    or under Ubuntu 24.04's AppArmor: refused in bwrap's words, and nothing
    on the record, since nothing ran."""
    subj = walt.job("echo hi")
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "bwrap").write_text(
        "#!/bin/sh\necho 'bwrap: No permissions to create a new namespace' >&2\nexit 1\n"
    )
    (fake / "bwrap").chmod(0o755)
    env = {**os.environ, "PATH": f"{fake}{os.pathsep}{os.environ['PATH']}"}
    before = walt.rows()
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW, env=env)
    assert got.returncode == 2, got.stdout + got.stderr
    assert "can't make a sandbox" in got.stderr
    assert "No permissions to create a new namespace" in got.stderr
    assert walt.rows() == before and not (tmp_path / "o").exists()


def kart_itself():
    """kart.py loaded here, to hold its checks to answers a machine can't
    be made to give on demand (a resource group that is or isn't ready)."""
    sys.path.insert(0, str(HERE))
    import kart  # noqa: PLC0415

    return kart


@pytest.mark.parametrize(("status", "said"), [
    ({"ready": True, "env_parent": "/g"}, None),
    ({"ready": False, "env_parent": None, "systemd_parent": None,
      "slice_unit_path": "/nowhere/kart.slice"}, None),  # none set up: rlimits
    ({"ready": False, "env_parent": "/g/kart.slice", "systemd_parent": None,
      "slice_unit_path": "/nowhere/kart.slice"}, "isn't ready (/g/kart.slice)"),
    ({"ready": False, "env_parent": None, "systemd_parent": "/s/kart.slice",
      "slice_unit_path": "/nowhere/kart.slice"}, "isn't ready (/s/kart.slice)"),
    ({"ready": False, "env_parent": None, "systemd_parent": None,
      "slice_unit_path": __file__}, f"isn't ready ({__file__})"),  # the unit alone
])  # fmt: skip
def test_a_resource_group_set_up_but_not_ready_is_named_with_what_to_run(
    monkeypatch, status, said
):
    """A restarted kart.slice has lost what `kartikeya setup-cgroup` wrote
    (seen 2026-11-18: every job failed saying only cgroup_setup_failed)."""
    kart = kart_itself()
    from kartikeya import cgroup_setup  # noqa: PLC0415

    monkeypatch.setattr(cgroup_setup, "cgroup_status", lambda: status)
    got = kart.group_not_ready()
    if said is None:
        assert got is None
        return
    assert said in got and "nothing ran" in got and "kartikeya setup-cgroup" in got

    def broke():
        raise OSError("no systemd")

    monkeypatch.setattr(cgroup_setup, "cgroup_status", broke)
    assert (
        "couldn't say" in kart.group_not_ready()
        and "nothing ran" in kart.group_not_ready()
    )


def test_a_group_that_isnt_ready_refuses_before_anything_runs_or_is_recorded(
    walt, tmp_path, monkeypatch, capsys
):
    kart = kart_itself()
    subj = walt.job("echo hi")
    job = tmp_path / "j.sh"
    job.write_text("echo hi\n")
    monkeypatch.setattr(
        kart, "group_not_ready", lambda: "a resource group isn't ready; nothing ran"
    )
    before = walt.rows()
    for argv in (["run", "--box", str(walt.box), "--job", subj, "--to", str(tmp_path / "o")],
                 ["try", "--box", str(walt.box), "--file", str(job), "--to", str(tmp_path / "o")]):  # fmt: skip
        assert kart.main([*argv, *NOW]) == 2
        assert "isn't ready; nothing ran" in capsys.readouterr().err
    assert walt.rows() == before and not (tmp_path / "o").exists()


def test_how_a_run_failed_is_recorded_without_what_it_printed(walt, tmp_path):
    """Kartikeya's error for a job that exits badly ends with the last line
    it printed (seen 2026-11-18, on a real record). That line is the
    person's files'."""
    job = tmp_path / "leak.sh"
    job.write_text("cat {pile}/cases.md; exit 3\n")
    got = walt.kart("try", "--file", job, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 42, got.stdout + got.stderr
    assert "Johnson" in (tmp_path / "o").read_text()  # in the file, on their machine
    subj = walt.job("grep -h Kessler {pile}/cases.md; exit 4")
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o2", *NOW)
    assert got.returncode == 42, got.stdout + got.stderr
    tried, ran = [r for r in walt.rows() if r["kind"] == "ran"]
    assert (tried["refused"], ran["refused"]) == ("exited 3", "exited 4")
    for row in (tried, ran):
        for word in ("Johnson", "Kessler", "stain", "pipe"):
            assert word not in json.dumps(row), (word, row)
    kart = kart_itself()
    assert (
        kart.why_failed({"error": "KART-SECURITY: blocked a socket"}) == "KART-SECURITY"
    )
    assert kart.why_failed({"error": "timeout"}) == "timeout"
    assert kart.why_failed({}) is None and kart.why_failed({"error": " "}) is None


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


# ── try: a job of your own, with no seal ────────────────────────────────────
def test_a_job_you_try_runs_in_the_sandbox_and_proposes_nothing(walt, tmp_path):
    job = tmp_path / "count.sh"
    job.write_text("grep -rhi johnson {pile} | wc -l\necho \"key: $(cat " + str(walt.key)
                   + " 2>/dev/null | wc -c)\"\n")  # fmt: skip
    got = walt.kart("try", "--file", job, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    assert (tmp_path / "o").read_text().splitlines() == ["2", "key: 0"]
    text = hashlib.sha256(job.read_bytes()).hexdigest()
    assert got.stdout.startswith(f"tried  text:{text}  completed, exit 0, row ")
    assert "nothing is proposed" in got.stdout
    [ran] = [r for r in walt.rows() if r["kind"] == "ran"]
    assert (ran["job"], ran["sealed"], ran["status"]) == (
        f"text:{text}",
        False,
        "completed",
    )
    assert ran["network"] == "isolated"
    out = (tmp_path / "o").read_text()
    assert ran["output_sha256"] == hashlib.sha256(out.encode()).hexdigest()
    assert not list((walt.box / "proposals").glob("*")) and seals(walt) == 0
    assert "Johnson" not in json.dumps(walt.rows())


def test_a_job_you_try_that_fails_says_so_and_is_on_the_record(walt, tmp_path):
    job = tmp_path / "bad.sh"
    job.write_text("echo partial; exit 3\n")
    got = walt.kart("try", "--file", job, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 42 and "failed, exit 3" in got.stdout, (
        got.stdout + got.stderr
    )
    [ran] = [r for r in walt.rows() if r["kind"] == "ran"]
    assert ran["status"] == "failed" and ran["returncode"] == 3
    assert not list((walt.box / "proposals").glob("*"))


def test_a_job_you_try_is_held_to_what_every_job_is(walt, tmp_path):
    ok = tmp_path / "ok.sh"
    ok.write_text("echo hi\n")
    net = tmp_path / "net.sh"
    net.write_text("# allow_net\ncurl x\n")
    (tmp_path / "mine").write_text("mine")
    before = walt.rows()
    for argv, why in (
        (["--file", net, "--to", tmp_path / "o"], "asks for the network"),
        (["--file", walt.box / "record.jsonl", "--to", tmp_path / "o"], "is inside the box"),
        (["--file", tmp_path / "gone.sh", "--to", tmp_path / "o"], "can't be read as text"),
        (["--file", ok, "--to", walt.box / "o"], "inside the box"),
        (["--file", ok, "--to", walt.dir / "pile" / "o"], "inside your folder"),
        (["--file", ok, "--to", tmp_path / "mine"], ""),
        (["--file", ok, "--to", tmp_path / "o", "--timeout", "soon"], "whole seconds"),
    ):  # fmt: skip
        got = walt.kart("try", *argv, *NOW)
        assert got.returncode == 2 and why in got.stderr, (argv, got.stderr)
    assert walt.rows() == before and not (tmp_path / "o").exists()
    assert (tmp_path / "mine").read_text() == "mine"
    env = {**os.environ, "PATH": str(tmp_path / "empty")}
    got = walt.kart("try", "--file", ok, "--to", tmp_path / "o", *NOW, env=env)
    assert got.returncode == 2 and "bubblewrap isn't installed" in got.stderr
    # what a tried job printed is never an answer: run refuses its text as a job
    got = walt.kart("try", "--file", ok, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 0
    text = hashlib.sha256(ok.read_bytes()).hexdigest()
    got = walt.kart("run", "--job", f"text:{text}", "--to", tmp_path / "o2", *NOW)
    assert got.returncode == 2 and "is not a job you sealed" in got.stderr


# ── queue, work, status: jobs of your own, run later ────────────────────────
def queued(walt, tmp_path, text, name="j.sh"):
    f = tmp_path / name
    f.write_text(text)
    got = walt.kart("queue", "--file", f, "--db", tmp_path / "q.db")
    assert got.returncode == 0 and got.stdout.startswith("queued  "), got.stderr
    return got.stdout.split()[1]


def status(walt, tmp_path, tid, *more):
    got = walt.kart("status", "--db", tmp_path / "q.db", "--id", tid, *more)
    assert got.returncode == 0, got.stderr
    return json.loads(got.stdout)


def test_a_queued_job_runs_when_worked_and_says_where_it_stands(walt, tmp_path):
    a = queued(walt, tmp_path, "grep -rhi johnson {pile} | wc -l\n")
    b = queued(walt, tmp_path, "cat {pile}/cases.md; exit 3\n", "b.sh")
    assert status(walt, tmp_path, a) == {"characters": None, "how": None, "id": a,
                                         "returncode": None, "status": "pending"}  # fmt: skip
    assert not [r for r in walt.rows() if r["kind"] == "ran"]  # queueing runs nothing
    got = walt.kart(
        "status", "--db", tmp_path / "q.db", "--id", a, "--to", tmp_path / "o"
    )
    assert (
        got.returncode == 2
        and "hasn't ended" in got.stderr
        and not (tmp_path / "o").exists()
    )
    got = walt.kart("work", "--db", tmp_path / "q.db", *NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    assert "worked 2 queued jobs; the queue is empty" in got.stdout
    assert (
        status(walt, tmp_path, a, "--to", tmp_path / "a.txt")["status"] == "completed"
    )
    assert (tmp_path / "a.txt").read_text().strip() == "2"
    bad = status(walt, tmp_path, b, "--to", tmp_path / "b.txt")
    assert (bad["status"], bad["how"], bad["returncode"]) == ("failed", "exited 3", 3)
    assert "Johnson" in (tmp_path / "b.txt").read_text()
    ran = [r for r in walt.rows() if r["kind"] == "ran"]
    assert [r["queued"] for r in ran] == [a, b] and all(
        r["sealed"] is False for r in ran
    )
    assert "Johnson" not in json.dumps(ran) and seals(walt) == 0
    assert not list((walt.box / "proposals").glob("*"))
    # worked again: nothing queued, nothing run, nothing left running
    got = walt.kart("work", "--db", tmp_path / "q.db", *NOW)
    assert got.returncode == 0 and "worked 0 queued jobs" in got.stdout
    assert len([r for r in walt.rows() if r["kind"] == "ran"]) == 2


def test_a_queue_is_held_to_what_every_job_is(walt, tmp_path):
    ok = tmp_path / "ok.sh"
    ok.write_text("echo hi\n")
    net = tmp_path / "net.sh"
    net.write_text("# allow_net\ncurl x\n")
    before = walt.rows()
    for argv, why in (
        (["queue", "--file", net, "--db", tmp_path / "q.db"], "asks for the network"),
        (["queue", "--file", walt.box / "record.jsonl", "--db", tmp_path / "q.db"], "is inside the box"),
        (["queue", "--file", ok, "--db", walt.box / "q.db"], "is inside the box"),
        (["queue", "--file", ok, "--db", walt.dir / "pile" / "q.db"], "is inside your folder"),
        (["queue", "--file", ok, "--db", tmp_path / "no" / "q.db"], "never makes one"),
        (["work", "--db", tmp_path / "none.db"], "isn't a queue"),
        (["status", "--db", tmp_path / "none.db", "--id", "x"], "isn't a queue"),
    ):  # fmt: skip
        got = walt.kart(*argv)
        assert got.returncode == 2 and why in got.stderr, (argv, got.stderr)
    assert walt.rows() == before and not (tmp_path / "q.db").exists()
    tid = queued(walt, tmp_path, "echo hi\n")
    got = walt.kart("status", "--db", tmp_path / "q.db", "--id", "nope")
    assert got.returncode == 2 and "isn't a job in this queue" in got.stderr
    got = walt.kart("work", "--db", tmp_path / "q.db", "--timeout", "soon")
    assert got.returncode == 2 and "whole seconds" in got.stderr
    env = {**os.environ, "PATH": str(tmp_path / "empty")}
    got = walt.kart("work", "--db", tmp_path / "q.db", env=env)
    assert got.returncode == 2 and "bubblewrap isn't installed" in got.stderr
    assert status(walt, tmp_path, tid)["status"] == "pending"  # still waiting, not lost


def test_a_network_line_put_in_the_queue_file_by_hand_is_still_never_run(
    walt, tmp_path
):
    """The queue is a file: what is in it is held again when it is worked."""
    queued(walt, tmp_path, "echo hi\n")
    sys.path.insert(0, str(HERE))
    from kartikeya import SqliteTaskQueue  # noqa: PLC0415

    SqliteTaskQueue(tmp_path / "q.db").submit("by-hand", "# allow_net\necho out\n")
    got = walt.kart("work", "--db", tmp_path / "q.db", *NOW)
    assert got.returncode == 0 and "refused  by-hand" in got.stdout, got.stdout
    assert "worked 1 queued job;" in got.stdout
    bad = status(walt, tmp_path, "by-hand")
    assert (bad["status"], bad["how"]) == ("failed", "asks for the network")
    assert len([r for r in walt.rows() if r["kind"] == "ran"]) == 1


# ── write: a job of your own ────────────────────────────────────────────────
def test_a_job_you_wrote_waits_on_your_seal_and_runs_once_you_seal_it(walt, tmp_path):
    job = tmp_path / "count.sh"
    job.write_text("grep -rhi johnson {pile} | wc -l\n")
    before = walt.rows()
    got = walt.kart("write", "--file", job, "--words", "count johnson", *NOW)
    assert got.returncode == 42 and got.stdout.startswith("written  proposal:"), (
        got.stderr
    )
    assert "waiting on your seal" in got.stdout
    subj = got.stdout.split()[1]
    prop = json.loads((walt.box / "proposals" / f"{subj[9:]}.json").read_text())
    assert prop["path"] == "kart/jobs/count.sh" and prop["cites"] == []
    assert prop["data"] == job.read_text()
    text = hashlib.sha256(job.read_bytes()).hexdigest()
    assert (
        prop["claim"]
        == f"a job you wrote yourself, text {text}; it runs only once sealed"
    )
    # writing ran nothing and sealed nothing
    assert not [r for r in walt.rows() if r["kind"] in ("ran", "seal")]
    assert len(walt.rows()) > len(before)
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 2 and "is not a job you sealed" in got.stderr
    walt.seal(subj)
    got = walt.kart("run", "--job", subj, "--to", tmp_path / "o", *NOW)
    assert got.returncode == 42 and (tmp_path / "o").read_text().strip() == "2"
    assert "result proposal:" in got.stdout and "waiting on your seal" in got.stdout


@pytest.mark.parametrize("line", ["# allow_net", "  # ALLOW_DB", "# allow_localhost"])
def test_a_job_you_wrote_asking_for_the_network_is_not_even_written(
    walt, tmp_path, line
):
    job = tmp_path / "n.sh"
    job.write_text(f"{line}\ncurl x\n")
    before = walt.rows()
    got = walt.kart("write", "--file", job, "--words", "x", *NOW)
    assert got.returncode == 2 and "asks for the network" in got.stderr
    assert walt.rows() == before


def test_a_job_file_that_is_no_job_is_refused_and_nothing_is_proposed(walt, tmp_path):
    (walt.box / "in.sh").write_text("echo hi\n")
    (tmp_path / "empty.sh").write_text("  \n")
    (tmp_path / "bin.sh").write_bytes(b"\xff\xfe\x00")
    (tmp_path / "long.sh").write_text("echo hi\n" + "#" * 20_000)
    (tmp_path / "most.sh").write_text("echo hi\n" + "#" * (20_000 - 8))
    before = walt.rows()
    for name, why in ((walt.box / "in.sh", "is inside the box"),
                      (walt.box / "record.jsonl", "is inside the box"),
                      (tmp_path / "gone.sh", "can't be read as text"),
                      (tmp_path, "can't be read as text"),
                      (tmp_path / "bin.sh", "can't be read as text"),
                      (tmp_path / "empty.sh", "is empty"),
                      (tmp_path / "long.sh", "is 20008 characters; a job is at most 20000")):  # fmt: skip
        got = walt.kart("write", "--file", name, "--words", "x", *NOW)
        assert got.returncode == 2 and why in got.stderr, (name, got.stderr)
        assert got.stderr.startswith("refused: ")
    assert walt.rows() == before and not list((walt.box / "proposals").glob("*"))
    got = walt.kart("write", "--file", tmp_path / "most.sh", "--words", "x", *NOW)
    assert got.returncode == 42, got.stderr  # exactly the most is still a job


def test_a_job_you_wrote_goes_through_the_kernels_door_like_any_other(tmp_path):
    """A box that isn't one, and words the kernel refuses, write nothing."""
    job = tmp_path / "j.sh"
    job.write_text("echo hi\n")
    got = run(KART, "write", "--box", tmp_path / "nobox", "--file", job, "--words", "x")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    walt = Person(tmp_path, "walt", NOTES)
    got = walt.kart("write", "--file", job, "--words", "", *NOW)
    assert got.returncode == 2 and "didn't take the job" in got.stderr
    assert not list((walt.box / "proposals").glob("*"))


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
    if not demo.is_dir():  # a stack carries the add-on, not willow's demos
        pytest.skip("demo/johnson isn't here: kart outside willow's repository")
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
        assert kinds.count("ran") == 2 and kinds.count("seal") == 4 and "sent" in kinds
        assert doc[who]["verify"].startswith("the chain holds")
    assert doc["ines"]["kinds"].count("received") == 6
    assert doc["aggregates"] == {"total": ["4", "5"], "sneak_held": True, "each": 4}


# ── only aggregates leave: --shape and gather ───────────────────────────────
def test_a_shape_held_lets_the_numbers_through(walt, tmp_path):
    subj = walt.job(
        "grep -rhi johnson {pile} | wc -l\ngrep -rhi kessler {pile} | wc -l"
    )
    got = walt.kart(
        "run", "--job", subj, "--to", tmp_path / "o", "--shape", "numbers", *NOW
    )
    assert got.returncode == 42 and "waiting on your seal" in got.stdout
    [ran] = [r for r in walt.rows() if r["kind"] == "ran"]
    assert (ran["shape"], ran["held_shape"]) == ("numbers", True)
    result = got.stdout.splitlines()[-1].split()[1]
    prop = json.loads((walt.box / "proposals" / f"{result[9:]}.json").read_text())
    assert prop["data"].split() == ["2", "1"] and "held to numbers" in prop["claim"]


@pytest.mark.parametrize("job", [
    "cat {pile}/cases.md",                       # the folder's own words
    "ls {pile}",                                 # its file names
    "grep -rhi johnson {pile} | wc -l; echo ok",  # a number and a word
    "seq 1 101",                                 # too many lines
    "true",                                      # nothing at all
])  # fmt: skip
def test_output_that_breaks_the_shape_is_never_proposed(walt, tmp_path, job):
    subj = walt.job(job)
    before = [r["n"] for r in walt.rows() if r["kind"] == "proposal"]
    got = walt.kart(
        "run", "--job", subj, "--to", tmp_path / "o", "--shape", "numbers", *NOW
    )
    assert (
        got.returncode == 42 and "isn't numbers, the shape you asked for" in got.stdout
    )
    [ran] = [r for r in walt.rows() if r["kind"] == "ran"]
    assert (ran["shape"], ran["held_shape"]) == ("numbers", False)
    assert [r["n"] for r in walt.rows() if r["kind"] == "proposal"] == before


def test_a_shape_kart_doesnt_know_is_refused(walt, tmp_path):
    subj = walt.job("echo 1")
    got = walt.kart(
        "run", "--job", subj, "--to", tmp_path / "o", "--shape", "words", *NOW
    )
    assert got.returncode == 2 and "--shape is one of: numbers" in got.stderr


class Ask:
    """Ines asks several people one job; each runs it held to numbers,
    seals what it printed and sends it back; Ines receives each."""

    def __init__(self, tmp_path: Path, folders: dict[str, dict[str, str]]):
        self.tmp = tmp_path
        self.ines = Person(tmp_path, "ines", {"a.md": "Nothing here.\n"})
        self.people = {n: Person(tmp_path, n, f) for n, f in folders.items()}
        self.results: dict[str, str] = {}

    def job(self, text: str, words: str) -> str:
        subj = self.ines.propose(words, {"path": "jobs/j.sh", "data": text, "cites": [],
                                         "claim": "a count"})  # fmt: skip
        self.ines.seal(subj)
        return subj

    def send(self, frm: Person, subj: str, to: Person, name: str) -> Path:
        pkg = self.tmp / f"{name}.pkg"
        got = run(SHARE, "send", "--box", frm.box, "--id", frm.id, "--answer", subj,
                  "--for", to.pub, "--to", pkg, *NOW)  # fmt: skip
        assert got.returncode == 0, got.stderr
        return pkg

    def receive(self, p: Person, pkg: Path) -> None:
        got = run(
            SHARE, "receive", "--box", p.box, "--id", p.id, "--package", pkg, *NOW
        )
        assert got.returncode == 0, got.stdout + got.stderr

    def answer(self, name: str, job: str) -> Path:
        p = self.people[name]
        pkg = self.send(self.ines, job, p, f"job-{name}-{job[9:15]}")
        self.receive(p, pkg)
        taken = p.kart(
            "take", "--package", pkg, "--words", f"ines asked {job[9:15]}", *NOW
        )
        subj = taken.stdout.split()[1]
        p.seal(subj)
        got = p.kart("run", "--job", subj, "--to", self.tmp / f"{name}-{job[9:15]}.txt",
                     "--shape", "numbers", *NOW)  # fmt: skip
        result = got.stdout.splitlines()[-1].split()[1]
        p.seal(result)
        self.results[name] = result
        back = self.send(p, result, self.ines, f"result-{name}-{job[9:15]}")
        self.receive(self.ines, back)
        return back

    def gather(self, *pkgs: Path) -> subprocess.CompletedProcess:
        return self.ines.kart("gather", "--package", ",".join(map(str, pkgs)),
                              "--words", "johnson across the firm", *NOW)  # fmt: skip


COUNT = "grep -rhi johnson {pile} | wc -l\ngrep -rhi kessler {pile} | wc -l"


@pytest.fixture
def ask(tmp_path):
    return Ask(tmp_path, {
        "walt": NOTES,
        "aurelie": {"claims.md": "Johnson claim open.\nJohnson roof, storm.\n"},
        "tamsin": {"files.md": "Kessler v Mill Lane.\n"},
    })  # fmt: skip


def test_gather_adds_everyones_numbers_and_waits_on_your_seal(ask):
    job = ask.job(COUNT, "count johnson and kessler")
    pkgs = [ask.answer(n, job) for n in ("walt", "aurelie", "tamsin")]
    got = ask.gather(*pkgs)
    assert got.returncode == 42, got.stdout + got.stderr
    assert "total          4 2  from 3 folders" in got.stdout
    assert "sets of tools" not in got.stdout
    subj = got.stdout.splitlines()[-1].split()[1]
    prop = json.loads((ask.ines.box / "proposals" / f"{subj[9:]}.json").read_text())
    assert prop["data"] == "4\n2\n" and prop["cites"] == []
    assert "on the same tools" in prop["claim"]
    assert sum(r["kind"] == "seal" for r in ask.ines.rows()) == 1, (
        "only Ines's job so far"
    )
    ask.ines.seal(subj)


def test_gather_refuses_what_doesnt_add_up(ask, tmp_path):
    a = ask.job(COUNT, "count both")
    b = ask.job("grep -rhi johnson {pile} | wc -l", "count johnson")
    w, au = ask.answer("walt", a), ask.answer("aurelie", a)
    t = ask.answer("tamsin", b)
    got = ask.gather(w, t)
    assert got.returncode == 2 and "ran different jobs" in got.stderr
    got = ask.gather(w, w)
    assert got.returncode == 2 and "two results come from one chain" in got.stderr
    # Walt's sealed result again, in a package Ines never received
    stray = ask.send(ask.people["walt"], ask.results["walt"], ask.ines, "stray")
    got = ask.gather(au, stray)
    assert (
        got.returncode == 2
        and "not a package your record says you received" in got.stderr
    )
    bad = json.loads(au.read_text())
    bad["note"] = "edited"
    (tmp_path / "bad.pkg").write_text(json.dumps(bad))
    got = ask.gather(w, tmp_path / "bad.pkg")
    assert got.returncode == 2 and "doesn't hold" in got.stderr


def test_gather_refuses_lines_that_dont_line_up_and_what_isnt_a_result(ask, tmp_path):
    per_file = ask.job("grep -rhic johnson {pile}/*", "johnson per file")
    ask.people["aurelie"].dir.joinpath("pile", "more.md").write_text("Johnson again.\n")
    w, au = ask.answer("walt", per_file), ask.answer("aurelie", per_file)
    got = ask.gather(w, au)
    assert got.returncode == 2 and "don't have the same number of lines" in got.stderr
    walt = ask.people["walt"]
    note = walt.propose("a note", {"path": "notes/n.md", "data": "4", "cites": [],
                                   "claim": "a note, not a result"})  # fmt: skip
    walt.seal(note)
    pkg = ask.send(walt, note, ask.ines, "note")
    ask.receive(ask.ines, pkg)
    got = ask.gather(w, pkg)
    assert got.returncode == 2 and "isn't one kart result" in got.stderr


def test_gather_says_when_results_ran_on_different_tools(ask):
    """Two machines' grep can count one job differently (busybox's and GNU's
    read `-lic` apart): the totals still add, and say so before you seal."""
    job = ask.job(COUNT, "count johnson and kessler")
    w = ask.answer("walt", job)
    tamsin = ask.people["tamsin"]
    claim = (f"what job {job} printed; tools {'0' * 64}; "
             f"job text {hashlib.sha256(COUNT.encode()).hexdigest()}")  # fmt: skip
    other = tamsin.propose("a result from elsewhere", {"path": "kart/results/x.txt",
                           "data": "0\n1\n", "cites": [], "claim": claim})  # fmt: skip
    tamsin.seal(other)
    back = ask.send(tamsin, other, ask.ines, "other-tools")
    ask.receive(ask.ines, back)
    got = ask.gather(w, back)
    assert got.returncode == 42, got.stdout + got.stderr
    assert "total          2 2  from 2 folders" in got.stdout
    assert "ran on 2 different sets of tools" in got.stdout
    subj = got.stdout.splitlines()[-1].split()[1]
    prop = json.loads((ask.ines.box / "proposals" / f"{subj[9:]}.json").read_text())
    assert "on 2 sets of tools" in prop["claim"]
