"""secure-sum: the total of three people's counts reaches the one who asked,
and no package she holds has anyone's own count in it. Needs shamirs:
without it these fail, they never skip."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SUM = HERE / "secure_sum.py"
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]
JOB = "grep -rhi johnson {pile} | wc -l\ngrep -rhi kessler {pile} | wc -l"
TAIL = f"; tools {'a' * 64}; job text {hashlib.sha256(JOB.encode()).hexdigest()}"


def run(*argv, flags=()) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *flags, *map(str, argv)], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)  # fmt: skip


class Person:
    def __init__(self, root: Path, name: str):
        self.root, self.name = root, name
        self.dir = root / name
        (self.dir / "pile").mkdir(parents=True)
        (self.dir / "pile" / "notes.md").write_text("Johnson roof.\n")
        self.box, self.id = self.dir / "box", self.dir / "id"
        assert run(KERNEL, "init", "--box", self.box, "--pile", self.dir / "pile",
                   "--key", self.dir / "key", *NOW).returncode == 0  # fmt: skip
        self.pub = run(SHARE, "id", "--to", self.id).stdout.split()[0]

    def rows(self) -> list[dict]:
        return [
            json.loads(x) for x in (self.box / "record.jsonl").read_text().splitlines()
        ]

    def propose(self, words: str, prop: dict) -> str:
        run(KERNEL, "bite", "--box", self.box, words, *NOW)
        (self.dir / "s.jsonl").write_text(json.dumps(prop) + "\n")
        out = run(
            KERNEL, "propose", "--box", self.box, "--file", self.dir / "s.jsonl", *NOW
        )
        return out.stdout.split()[1]

    def result(self, data: str) -> str:
        """A kart result as `kart run` proposes one, sealed, as kart has you do."""
        subj = self.propose(f"result {data!r}", {"path": "kart/results/r.txt", "data": data,
                            "cites": [], "claim": f"what a job printed{TAIL}"})  # fmt: skip
        self.seal(subj)
        return subj

    def seal(self, subj: str) -> None:
        got = run(KERNEL, "seal", "--box", self.box, subj, *NOW)
        assert got.returncode == 0, got.stderr

    def send(self, subj: str, to: "Person", name: str) -> Path:
        pkg = self.root / f"{name}.pkg"
        got = run(SHARE, "send", "--box", self.box, "--id", self.id, "--answer", subj,
                  "--for", to.pub, "--to", pkg, *NOW)  # fmt: skip
        assert got.returncode == 0, got.stderr
        to.receive(pkg)
        return pkg

    def receive(self, pkg: Path) -> None:
        got = run(
            SHARE, "receive", "--box", self.box, "--id", self.id, "--package", pkg, *NOW
        )
        assert got.returncode == 0, got.stdout + got.stderr

    def sum(self, cmd: str, *argv) -> subprocess.CompletedProcess:
        ident = [] if cmd == "total" else ["--id", self.id]
        return run(SUM, cmd, "--box", self.box, *ident, *argv, *NOW)

    def prop(self, subj: str) -> dict:
        return json.loads((self.box / "proposals" / f"{subj[9:]}.json").read_text())


def subjects(out: str, word: str) -> list[str]:
    return [x.split()[1] for x in out.splitlines() if x.strip().startswith(word)]


class Round:
    """Ines asks Walt, Aurelie and Tamsin; each splits, sends the shares
    straight to each other, combines, and sends Ines a sum."""

    VALUES = {"walt": "3\n5\n", "aurelie": "1\n0\n", "tamsin": "4\n-2\n"}

    def __init__(self, tmp: Path, threshold: int | None = None):
        self.tmp = tmp
        self.ines = Person(tmp, "ines")
        self.people = [Person(tmp, n) for n in self.VALUES]
        self.among = ",".join(p.pub for p in self.people)
        self.t = [] if threshold is None else ["--threshold", str(threshold)]
        self.shares: dict[tuple[str, str], Path] = {}  # (from, to): package

    def split(self) -> None:
        for p in self.people:
            got = p.sum("split", "--result", p.result(self.VALUES[p.name]),
                        "--among", self.among, *self.t)  # fmt: skip
            assert got.returncode == 42, got.stdout + got.stderr
            for subj, q in zip(subjects(got.stdout, "share"),
                               [q for q in self.people if q is not p]):  # fmt: skip
                p.seal(subj)
                self.shares[(p.name, q.name)] = p.send(
                    subj, q, f"share-{p.name}-{q.name}"
                )

    def combine(self, p: Person) -> subprocess.CompletedProcess:
        mine = [str(v) for (f, t), v in self.shares.items() if t == p.name]
        return p.sum("combine", "--package", ",".join(mine))

    def sums(self) -> dict[str, Path]:
        out = {}
        for p in self.people:
            got = self.combine(p)
            assert got.returncode == 42, got.stdout + got.stderr
            [subj] = subjects(got.stdout, "sum")
            p.seal(subj)
            out[p.name] = p.send(subj, self.ines, f"sum-{p.name}")
        return out

    def total(
        self, *pkgs: Path, among: str | None = None
    ) -> subprocess.CompletedProcess:
        return self.ines.sum("total", "--among", among or self.among,
                             "--package", ",".join(map(str, pkgs)))  # fmt: skip


@pytest.fixture
def rnd(tmp_path):
    return Round(tmp_path)


def test_the_total_arrives_and_no_ones_own_count_does(rnd):
    rnd.split()
    sums = rnd.sums()
    got = rnd.total(*sums.values())
    assert got.returncode == 42, got.stdout + got.stderr
    assert "total          8 3  from 3 folders" in got.stdout
    subj = got.stdout.splitlines()[-1].split()[1]
    assert rnd.ines.prop(subj)["data"] == "8\n3\n"
    assert not any(r["kind"] == "seal" for r in rnd.ines.rows()), (
        "secure-sum never seals"
    )
    held = "".join(p.read_text() for p in sums.values())
    for values in Round.VALUES.values():
        assert json.dumps(values) not in held, "a count of one person's is in a package"
    received = [r for r in rnd.ines.rows() if r["kind"] == "received"]
    assert len(received) == 3, "Ines holds three sums and not one share"
    split = [r for p in rnd.people for r in p.rows() if r["kind"] == "split"]
    assert len({r["round"] for r in split}) == 1 and all("data" not in r for r in split)


def test_any_threshold_of_the_sums_make_the_total_and_a_wrong_one_is_caught(tmp_path):
    rnd = Round(tmp_path, threshold=2)
    rnd.split()
    sums = rnd.sums()
    for pair in (("walt", "aurelie"), ("aurelie", "tamsin"), ("walt", "tamsin")):
        got = rnd.total(*(sums[n] for n in pair))
        assert got.returncode == 42 and "total          8 3" in got.stdout, got.stderr
    # Tamsin sends a sum of her own making in place of hers: still signed by her
    tamsin = rnd.people[2]
    [mine] = [r["sum"] for r in tamsin.rows() if r["kind"] == "combined"]
    real = tamsin.prop(mine)
    bad = {
        "path": real["path"],
        "claim": real["claim"],
        "cites": [],
        "data": "12345\n678\n",
    }
    subj = tamsin.propose("a sum of my own", bad)
    tamsin.seal(subj)
    wrong = tamsin.send(subj, rnd.ines, "wrong-sum")
    got = rnd.total(sums["walt"], sums["aurelie"], wrong)
    assert got.returncode == 2 and "the sums disagree" in got.stderr
    got = rnd.total(sums["walt"])
    assert got.returncode == 2 and "1 sums of a round that needs 2" in got.stderr


def test_a_share_that_passed_through_someone_else_is_refused(rnd):
    """Walt's share for Aurelie sent by way of Ines: Ines held it, so it is
    one of the shares she could put together. Aurelie refuses it."""
    walt, aurelie, tamsin = rnd.people
    got = walt.sum("split", "--result", walt.result("3\n5\n"), "--among", rnd.among)
    for_aurelie = subjects(got.stdout, "share")[0]
    walt.seal(for_aurelie)
    via = walt.send(for_aurelie, rnd.ines, "via-ines")
    out = rnd.tmp / "forwarded.pkg"
    assert run(SHARE, "forward", "--box", rnd.ines.box, "--id", rnd.ines.id, "--package",
               via, "--for", aurelie.pub, "--to", out, *NOW).returncode == 0  # fmt: skip
    aurelie.receive(out)
    got = aurelie.sum("combine", "--package", out)
    assert got.returncode == 2 and "was forwarded" in got.stderr


def test_combine_needs_one_share_from_each_of_the_others_and_your_own(rnd):
    rnd.split()
    walt = rnd.people[0]
    one = rnd.shares[("aurelie", "walt")]
    got = walt.sum("combine", "--package", one)
    assert got.returncode == 2 and "one share from each of the other 2" in got.stderr
    got = walt.sum("combine", "--package", f"{one},{one}")
    assert got.returncode == 2 and "one share from each" in got.stderr
    got = walt.sum("combine", "--package", rnd.shares[("walt", "aurelie")])
    assert (
        got.returncode == 2
        and "not a package your record says you received" in got.stderr
    )


def test_a_sum_from_someone_not_at_its_place_or_another_round_is_refused(rnd):
    rnd.split()
    sums = rnd.sums()
    flipped = ",".join(p.pub for p in reversed(rnd.people))
    got = rnd.total(*sums.values(), among=flipped)
    assert got.returncode == 2 and "of a round other than these keys" in got.stderr
    got = rnd.total(sums["walt"], sums["walt"], sums["tamsin"])
    assert got.returncode == 2 and "two sums at place 1" in got.stderr


def test_split_takes_only_a_sealed_kart_result_of_yours_once(rnd):
    walt = rnd.people[0]
    unsealed = walt.propose("r", {"path": "kart/results/u.txt", "data": "1\n",
                                  "cites": [], "claim": f"x{TAIL}"})  # fmt: skip
    got = walt.sum("split", "--result", unsealed, "--among", rnd.among)
    assert got.returncode == 2 and "not an answer you sealed" in got.stderr
    note = walt.propose(
        "n", {"path": "notes/n.md", "data": "1\n", "cites": [], "claim": "n"}
    )
    walt.seal(note)
    got = walt.sum("split", "--result", note, "--among", rnd.among)
    assert got.returncode == 2 and "not a kart result" in got.stderr
    res = walt.result("2\n")
    assert walt.sum("split", "--result", res, "--among", rnd.among).returncode == 42
    got = walt.sum("split", "--result", res, "--among", rnd.among)
    assert got.returncode == 2 and "split already" in got.stderr


@pytest.mark.parametrize("among,threshold,said", [
    ("others", None, "your key isn't in --among"),
    ("two", None, "three people or more"),
    ("all", "1", "--threshold is from 2 to 3"),
    ("all", "4", "--threshold is from 2 to 3"),
    ("bad", None, "64 hex each"),
])  # fmt: skip
def test_a_round_that_cant_be_is_refused(rnd, among, threshold, said):
    walt, aurelie, tamsin = rnd.people
    keys = {
        "others": [aurelie.pub, tamsin.pub, rnd.ines.pub],
        "two": [walt.pub, aurelie.pub],
        "all": [p.pub for p in rnd.people],
        "bad": [walt.pub, "x", tamsin.pub],
    }[among]
    t = ["--threshold", threshold] if threshold else []
    got = walt.sum(
        "split", "--result", walt.result("1\n"), "--among", ",".join(keys), *t
    )
    assert got.returncode == 2 and said in got.stderr, got.stderr


def test_without_shamirs_it_refuses_and_names_it(rnd):
    walt = rnd.people[0]
    got = run(SUM, "split", "--box", walt.box, "--id", walt.id, "--result",
              walt.result("1\n"), "--among", rnd.among, *NOW, flags=("-S",))  # fmt: skip
    assert got.returncode == 2 and "shamirs isn't installed" in got.stderr


def test_a_bad_command_line_says_how_to_run_it(rnd):
    for argv in ([], ["split"], ["total", "--box", "x"], ["what"]):
        got = run(SUM, *argv)
        assert got.returncode == 2 and "secure_sum.py split" in got.stderr
