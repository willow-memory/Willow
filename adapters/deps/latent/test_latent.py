"""latent: ranks a scan index by meaning, deterministically; honours
--changed-from; refuses, never skips, without numpy or a real index."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCAN = ROOT / "adapters" / "stdlib" / "scan" / "scan.py"
LATENT = HERE / "latent.py"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))


def index(tmp: Path, name: str, files: dict[str, str]) -> Path:
    src = tmp / f"src-{name}"
    for rel, text in files.items():
        p = src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    out = tmp / f"ix-{name}"
    subprocess.run([sys.executable, str(SCAN), "index", "--from", str(src), "--to", str(out)],
                   check=True, capture_output=True)  # fmt: skip
    return out


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LATENT), *argv], capture_output=True, text=True
    )


#: "payment" and "invoice" never share a passage, but both keep company with
#: "owed"/"client", so LSA links them; a bare word match for "payment" finds
#: only the one passage that says it, not the invoice passage.
CORPUS = {
    "a.md": "the client owed money\n\nan invoice was owed by the client\n",
    "b.md": "the client paid money\n\na payment cleared from the client\n",
    "c.md": "unrelated notes about the weather and the garden\n",
    "d.md": "more unrelated notes about trains and timetables\n",
}


def test_ranks_by_meaning_and_is_deterministic(tmp_path):
    ix = index(tmp_path, "m", CORPUS)
    got = run("rank", "--index", str(ix), "--top", "4", "outstanding invoice payment")
    assert got.returncode == 0, got.stderr
    served = json.loads(got.stdout)["served"]
    assert served and served[0]["rank"] == 1
    # every ranked passage is a real one, with a file:line and the kernel's id
    import scan

    ids = {c["id"] for c in scan.passages(ix)}
    assert all(s["id"] in ids and ":" in s["where"] for s in served)
    # same index, same question, same order every run
    again = run("rank", "--index", str(ix), "--top", "4", "outstanding invoice payment")
    assert [s["id"] for s in served] == [
        s["id"] for s in json.loads(again.stdout)["served"]
    ]


def test_changed_from_ranks_only_what_the_other_index_lacks(tmp_path):
    old = index(tmp_path, "old", {
        "x.md": "the client owed money\n\nan invoice was owed\n",
        "keep.md": "a line that does not change at all here\n"})  # fmt: skip
    new = index(tmp_path, "new", {
        "x.md": "the client paid money\n\na payment cleared today\n",
        "keep.md": "a line that does not change at all here\n"})  # fmt: skip
    got = run(
        "rank",
        "--index",
        str(old),
        "--changed-from",
        str(new),
        "--top",
        "9",
        "money owed",
    )
    assert got.returncode == 0, got.stderr
    import scan

    changed = {c["id"] for c in scan.passages(old)} - {
        c["id"] for c in scan.passages(new)
    }
    served = json.loads(got.stdout)["served"]
    assert served and all(
        s["id"] in changed for s in served
    )  # never the unchanged keep.md


def test_nothing_shares_a_sense_is_42(tmp_path):
    ix = index(tmp_path, "n", {"a.md": "tomatoes and basil in the garden\n"})
    got = run("rank", "--index", str(ix), "zxqw nonsense term")
    assert got.returncode == 42 and json.loads(got.stdout)["state"] == "empty"


def test_a_bad_command_line_is_refused(tmp_path):
    for argv in ([], ["find"], ["rank"], ["rank", "--index"],
                 ["rank", "--top", "3", "q"], ["rank", "--index", "i", "--top", "0", "q"],
                 ["rank", "--index", "i", "q", "extra"], ["rank", "--index", "i", "--bad", "x", "q"]):  # fmt: skip
        got = subprocess.run([sys.executable, str(LATENT), *argv], capture_output=True,
                             text=True, cwd=tmp_path)  # fmt: skip
        assert got.returncode == 2 and "latent.py" in got.stderr, (argv, got.stderr)


def test_not_an_index_is_refused(tmp_path):
    (tmp_path / "empty").mkdir()
    got = run("rank", "--index", str(tmp_path / "empty"), "anything")
    assert got.returncode == 2 and got.stderr.startswith("refused")


def test_without_numpy_it_refuses_naming_numpy(tmp_path):
    ix = index(tmp_path, "z", CORPUS)
    # a sitecustomize that hides numpy, injected ahead on the path
    block = tmp_path / "noblock"
    block.mkdir()
    (block / "sitecustomize.py").write_text(
        "import sys\n"
        "class _No:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name == 'numpy' or name.startswith('numpy.'):\n"
        "            raise ImportError('numpy hidden for the test')\n"
        "        return None\n"
        "sys.meta_path.insert(0, _No())\n"
    )
    env = {"PYTHONPATH": str(block), "PATH": __import__("os").environ.get("PATH", "")}
    got = subprocess.run([sys.executable, str(LATENT), "rank", "--index", str(ix), "money"],
                         capture_output=True, text=True, env=env)  # fmt: skip
    assert got.returncode == 2 and "numpy" in got.stderr, got.stderr
