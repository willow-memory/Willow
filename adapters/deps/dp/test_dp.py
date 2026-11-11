"""dp: a count noised by OpenDP before it leaves, its spend on your record,
never twice, and still added up by kart's gather. Needs OpenDP: without it
these fail, they never skip."""

from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
DP = HERE / "dp.py"
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SHARE = ROOT / "adapters" / "stdlib" / "share" / "share.py"
KART = ROOT / "adapters" / "deps" / "kart" / "kart.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]
JOB = "grep -rhi johnson {pile} | wc -l\ngrep -rhi kessler {pile} | wc -l"
TAIL = f"; tools {'a' * 64}; job text {hashlib.sha256(JOB.encode()).hexdigest()}"

sys.path.insert(0, str(HERE))
import dp  # noqa: E402


def run(*argv, flags=()) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *flags, *map(str, argv)], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)  # fmt: skip


class Person:
    def __init__(self, root: Path, name: str):
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

    def result(self, data: str = "3\n5\n", path: str = "kart/results/r.txt") -> str:
        """A kart result as `kart run` proposes one, without running a job."""
        return self.propose(f"result {data!r}", {"path": path, "data": data, "cites": [],
                            "claim": f"what job proposal:{'b' * 64} printed{TAIL}"})  # fmt: skip

    def seal(self, subj: str) -> None:
        got = run(KERNEL, "seal", "--box", self.box, subj, *NOW)
        assert got.returncode == 0, got.stderr

    def dp(self, *argv) -> subprocess.CompletedProcess:
        return run(DP, argv[0], "--box", self.box, *argv[1:])

    def prop(self, subj: str) -> dict:
        return json.loads((self.box / "proposals" / f"{subj[9:]}.json").read_text())


@pytest.fixture
def walt(tmp_path):
    return Person(tmp_path, "walt")


def test_noise_proposes_the_numbers_noised_and_keeps_the_truth_in_your_box(walt):
    subj = walt.result()
    got = walt.dp("noise", "--result", subj, "--epsilon", "1", *NOW)
    assert got.returncode == 42, got.stdout + got.stderr
    noisy = got.stdout.splitlines()[-1].split()[1]
    prop = walt.prop(noisy)
    assert prop["path"] == f"kart/results/dp-{subj[9:21]}.txt" and prop["cites"] == []
    assert all(x.lstrip("-").isdigit() for x in prop["data"].split())
    assert len(prop["data"].split()) == 2
    assert prop["claim"].endswith(TAIL), "gather reads the tools and job text"
    assert "epsilon 1 for 1 an item" in prop["claim"]
    [row] = [r for r in walt.rows() if r["kind"] == "noised"]
    assert (row["result"], row["epsilon"], row["per_item"], row["lines"]) == (
        subj,
        1.0,
        1,
        2,
    )
    assert row["mechanism"] == "discrete laplace" and row["scale"] == 2.0
    assert row["spent"] <= 1.0 and row["within"] > 0
    assert "data" not in row and prop["data"] not in json.dumps(row)
    assert not any(r["kind"] == "seal" for r in walt.rows()), "dp never seals"


def test_a_result_is_noised_once(walt):
    subj = walt.result()
    assert walt.dp("noise", "--result", subj, "--epsilon", "1", *NOW).returncode == 42
    got = walt.dp("noise", "--result", subj, "--epsilon", "1", *NOW)
    assert got.returncode == 2 and "average back to the truth" in got.stderr


def test_only_a_kart_result_of_numbers_is_noised(walt, tmp_path):
    note = walt.propose("a note", {"path": "notes/n.md", "data": "4\n", "cites": [],
                                   "claim": f"a note{TAIL}"})  # fmt: skip
    got = walt.dp("noise", "--result", note, "--epsilon", "1", *NOW)
    assert got.returncode == 2 and "not a kart result" in got.stderr
    words = walt.result("Johnson roof\n", "kart/results/w.txt")
    got = walt.dp("noise", "--result", words, "--epsilon", "1", *NOW)
    assert got.returncode == 2 and "isn't numbers" in got.stderr
    first = walt.dp("noise", "--result", walt.result(), "--epsilon", "1", *NOW)
    noisy = first.stdout.splitlines()[-1].split()[1]
    got = walt.dp("noise", "--result", noisy, "--epsilon", "1", *NOW)
    assert got.returncode == 2 and "noised already" in got.stderr
    other = Person(tmp_path, "aurelie")
    theirs = other.result("9\n9\n")
    got = walt.dp("noise", "--result", theirs, "--epsilon", "1", *NOW)
    assert got.returncode == 2 and "not a proposal of yours" in got.stderr


def test_a_result_you_declined_is_not_noised(walt):
    subj = walt.result("7\n", "kart/results/d.txt")
    assert run(KERNEL, "decline", "--box", walt.box, subj, *NOW).returncode == 0
    got = walt.dp("noise", "--result", subj, "--epsilon", "1", *NOW)
    assert got.returncode == 2 and "you declined" in got.stderr


@pytest.mark.parametrize("eps,per", [("0", "1"), ("-1", "1"), ("nan", "1"),
                                     ("11", "1"), ("1", "0"), ("x", "1")])  # fmt: skip
def test_a_spend_out_of_range_is_refused(walt, eps, per):
    got = walt.dp("noise", "--result", walt.result(), "--epsilon", eps,
                  "--per-item", per, *NOW)  # fmt: skip
    assert got.returncode == 2 and "refused" in got.stderr
    assert not any(r["kind"] == "noised" for r in walt.rows())


def test_spent_adds_up_each_jobs_epsilon(walt):
    for data, eps in (("1\n", "0.5"), ("2\n", "0.25")):
        walt.dp("noise", "--result", walt.result(data, f"kart/results/{eps}.txt"),
                "--epsilon", eps, *NOW)  # fmt: skip
    got = walt.dp("spent")
    assert got.returncode == 0 and "spent  epsilon 0.75 over 1 jobs" in got.stdout


def test_the_noise_is_opendps_and_centred_on_the_truth():
    """The scale is OpenDP's: per_item times the lines over epsilon, and
    the noisy numbers fall about the truth, wider as epsilon shrinks."""
    wide = [dp.noisy([100, 0], 0.5, 1)[0][0] for _ in range(400)]
    tight = [dp.noisy([100, 0], 4.0, 1)[0][0] for _ in range(400)]
    assert (
        abs(statistics.mean(wide) - 100) < 2 and abs(statistics.mean(tight) - 100) < 1
    )
    assert statistics.pstdev(wide) > 2 * statistics.pstdev(tight)
    _, how = dp.noisy([1, 2, 3], 1.0, 2)
    assert how["scale"] == 6.0 and how["spent"] <= 1.0


def test_without_opendp_it_refuses_and_names_it(walt):
    subj = walt.result()
    got = run(DP, "noise", "--box", walt.box, "--result", subj, "--epsilon", "1",
              *NOW, flags=("-S",))  # fmt: skip
    assert got.returncode == 2 and "OpenDP isn't installed" in got.stderr


def test_kart_gather_adds_noisy_results_as_any_others(tmp_path):
    ines, walt, aurelie = (Person(tmp_path, n) for n in ("ines", "walt", "aurelie"))
    backs = []
    for p, data in ((walt, "3\n5\n"), (aurelie, "1\n0\n")):
        got = p.dp("noise", "--result", p.result(data), "--epsilon", "1", *NOW)
        noisy = got.stdout.splitlines()[-1].split()[1]
        p.seal(noisy)
        pkg = tmp_path / f"{p.dir.name}.pkg"
        assert run(SHARE, "send", "--box", p.box, "--id", p.id, "--answer", noisy,
                   "--for", ines.pub, "--to", pkg, *NOW).returncode == 0  # fmt: skip
        assert run(SHARE, "receive", "--box", ines.box, "--id", ines.id,
                   "--package", pkg, *NOW).returncode == 0  # fmt: skip
        backs.append((pkg, [int(x) for x in p.prop(noisy)["data"].split()]))
    got = run(KART, "gather", "--box", ines.box, "--package",
              ",".join(str(b) for b, _ in backs), "--words", "noisy totals", *NOW)  # fmt: skip
    assert got.returncode == 42, got.stdout + got.stderr
    want = [a + b for a, b in zip(backs[0][1], backs[1][1])]
    assert f"total          {' '.join(map(str, want))}  from 2 folders" in got.stdout


def test_a_bad_command_line_says_how_to_run_it(walt):
    for argv in ([], ["noise"], ["spent", "--box", walt.box, "--x", "1"], ["what"]):
        got = run(DP, *argv)
        assert got.returncode == 2 and "dp.py noise" in got.stderr
    got = run(DP, "spent", "--box", walt.dir / "nobox")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
