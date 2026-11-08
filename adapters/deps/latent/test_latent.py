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


def test_past_the_bound_it_refuses_before_allocating(tmp_path, monkeypatch, capsys):
    import latent  # puts the repo root, and so the kernel, on the path
    import scan

    import kernel

    ix = index(tmp_path, "big", CORPUS)
    texts = [c["text"] for c in scan.passages(ix)]
    n, m = len(texts), len({w for t in texts for w in kernel.words(t)})
    argv = ["rank", "--index", str(ix), "outstanding invoice payment"]
    # exactly at the bound it still ranks
    monkeypatch.setattr(latent, "LIMIT", n * m * 8)
    assert latent.main(argv) == 0
    capsys.readouterr()
    # one byte under, it refuses, naming the passages and the memory; gib()
    # is made exact here, since this small a matrix rounds to 0.0 GiB
    monkeypatch.setattr(latent, "LIMIT", n * m * 8 - 1)
    monkeypatch.setattr(latent, "gib", lambda b: f"<{b} bytes>")
    assert latent.main(argv) == 2
    err = capsys.readouterr().err
    assert err.startswith("refused") and f"{n} passages and {m} terms" in err
    assert f"need a <{n * m * 8} bytes> matrix" in err
    assert f"bound is <{n * m * 8 - 1} bytes>" in err


def test_the_bound_is_the_cards():
    import latent

    assert latent.LIMIT == 2**29  # 512 MiB, as the card says


def test_gib_says_gibibytes():
    import latent

    assert latent.gib(21 * 2**30 + 2**29) == "21.5 GiB"


def lines(out: str) -> list[dict]:
    return [json.loads(x) for x in out.splitlines()]


def test_questions_file_builds_the_space_once_and_answers_each(
    tmp_path, monkeypatch, capsys
):
    import latent

    ix = index(tmp_path, "q", CORPUS)
    qf = tmp_path / "q.txt"
    qf.write_text("# a comment\nbill\toutstanding invoice payment\n\nzxqw nonsense\n")
    built = []
    real = latent.space
    monkeypatch.setattr(latent, "space", lambda *a: built.append(a) or real(*a))
    assert (
        latent.main(["rank", "--index", str(ix), "--top", "4", "--questions", str(qf)])
        == 0
    )
    got = lines(capsys.readouterr().out)
    assert len(built) == 1  # one space for every question
    assert [r["question"] for r in got] == ["bill", "4"]
    assert [r["state"] for r in got] == ["populated", "empty"]
    # each answer is the one that question gets asked alone
    alone = run("rank", "--index", str(ix), "--top", "4", "outstanding invoice payment")
    assert got[0]["served"] == json.loads(alone.stdout)["served"]
    assert "question" not in json.loads(alone.stdout)
    one = run("rank", "--index", str(ix), "--top", "1", "outstanding invoice payment")
    assert (
        one.returncode == 0 and json.loads(one.stdout)["served"] == got[0]["served"][:1]
    )


def test_questions_that_all_find_nothing_are_42(tmp_path):
    ix = index(tmp_path, "q0", CORPUS)
    qf = tmp_path / "q.txt"
    qf.write_text("zxqw\nqqqv nonsense\n")
    got = run("rank", "--index", str(ix), "--questions", str(qf))
    assert (
        got.returncode == 42
        and [r["state"] for r in lines(got.stdout)] == ["empty"] * 2
    )


def test_a_question_and_a_questions_file_together_or_neither_is_refused(tmp_path):
    ix = index(tmp_path, "qb", CORPUS)
    qf = tmp_path / "q.txt"
    qf.write_text("money\n")
    for argv in (["--questions", str(qf), "money"], ["--only"]):
        got = run("rank", "--index", str(ix), *argv)
        assert got.returncode == 2 and "latent.py" in got.stderr, argv
    got = run("rank", "--index", str(ix), "--questions", str(tmp_path / "none.txt"))
    assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr


def ids_of(ix: Path) -> dict[str, str]:
    import scan

    return {c["text"].strip(): c["id"] for c in scan.passages(ix)}


def test_only_ranks_just_the_passages_scans_output_names(tmp_path):
    ix = index(tmp_path, "o", CORPUS)
    qf = tmp_path / "q.txt"
    qf.write_text("client\n")
    words = subprocess.run([sys.executable, str(SCAN), "scan", "--index", str(ix),
                            "--questions", str(qf), "--rank", "bm25", "--top", "9"],
                           capture_output=True, text=True, check=True)  # fmt: skip
    picked = {s["id"] for r in lines(words.stdout) for s in r["served"]}
    assert 2 <= len(picked) < len(ids_of(ix))
    out = tmp_path / "bm25.jsonl"
    out.write_text(words.stdout)
    got = run(
        "rank", "--index", str(ix), "--only", str(out), "--top", "9", "money owed"
    )
    assert got.returncode == 0, got.stderr
    served = json.loads(got.stdout)["served"]
    assert served and {s["id"] for s in served} <= picked


def test_only_reads_ripgreps_lines_and_bare_ids_and_skips_a_summary(tmp_path):
    ix = index(tmp_path, "r", CORPUS)
    ids = ids_of(ix)
    a, b = (
        ids["an invoice was owed by the client"],
        ids["a payment cleared from the client"],
    )
    f = tmp_path / "rg.txt"
    f.write_text(f"a.md:3  {a[:12]}  an invoice was owed by the client\n{b}\n"
                 "2 hits in 2 passages\n")  # fmt: skip
    got = run(
        "rank", "--index", str(ix), "--only", str(f), "--top", "9", "client invoice"
    )
    assert got.returncode == 0, got.stderr
    assert {s["id"] for s in json.loads(got.stdout)["served"]} == {a, b}
    assert got.stderr == ""


def test_ids_in_reads_each_shape():
    import latent

    a, b = "a" * 64, "b" * 12
    text = (f'{{"served": [{{"id": "{a}"}}]}}\n'
            f"x.md:1  {b}  some text\n{b}\n"
            f"{a} is not an id line\n\nsummary words here\n")  # fmt: skip
    assert latent.ids_in(text) == (3, [a, b, b])
    assert latent.ids_in(f"x.md:1 {b}\n") == (1, [b])  # a line of two fields
    assert latent.ids_in("x.md:1  short  text\n" + "c" * 11) == (0, [])
    assert latent.ids_in("d" * 65) == (0, [])


def test_resolve_names_whole_ids_from_their_prefixes():
    import latent

    class Ix:
        pile = [{"id": "ab" * 32}, {"id": "ab" * 6 + "cd" * 26}, {"id": "ef" * 32}]

    got, missed = latent.resolve(Ix, ["ab" * 6, "ab" * 32, "ef" * 7, "0" * 12])
    assert got == {"ab" * 32, "ab" * 6 + "cd" * 26, "ef" * 32} and missed == 1
    assert latent.resolve(Ix, ["ab" * 6 + "ce"]) == (set(), 1)


def test_only_with_ids_of_another_folder_is_refused_and_some_missing_said(tmp_path):
    ix = index(tmp_path, "x", CORPUS)
    a = ids_of(ix)["an invoice was owed by the client"]
    b = ids_of(ix)["a payment cleared from the client"]
    f = tmp_path / "ids.txt"
    f.write_text("0" * 64 + "\n" + "1" * 12 + "\n")
    got = run("rank", "--index", str(ix), "--only", str(f), "money")
    assert got.returncode == 2 and "none of the 2 ids" in got.stderr, got.stderr
    f.write_text(f"{'0' * 64}\n{a}\n{b}\n")
    got = run("rank", "--index", str(ix), "--only", str(f), "--top", "9", "client")
    assert got.returncode == 0 and "1 of the 3 ids" in got.stderr, got.stderr
    assert {s["id"] for s in json.loads(got.stdout)["served"]} <= {a, b}


def test_only_a_file_naming_nothing_is_refused_and_an_empty_answer_is_42(tmp_path):
    ix = index(tmp_path, "e", CORPUS)
    f = tmp_path / "junk.txt"
    f.write_text("nothing here names a passage\n")
    got = run("rank", "--index", str(ix), "--only", str(f), "money")
    assert got.returncode == 2 and "names no passage" in got.stderr, got.stderr
    f.write_text('{"state": "empty", "served": []}\n')
    got = run("rank", "--index", str(ix), "--only", str(f), "money")
    assert got.returncode == 42, got.stderr
    f.write_text('{"state": "empty"}\n')
    got = run("rank", "--index", str(ix), "--only", str(f), "money")
    assert "names no served passages" in got.stderr, got.stderr
    for bad in ("{not json\n", '{"state": "empty"}\n', "[1]\n"):
        f.write_text(bad)
        got = run("rank", "--index", str(ix), "--only", str(f), "money")
        assert got.returncode == 2 and got.stderr.startswith("refused"), (
            bad,
            got.stderr,
        )


def test_the_bound_counts_only_what_only_kept(tmp_path, monkeypatch, capsys):
    import latent

    ix = index(tmp_path, "b", CORPUS)
    ids = ids_of(ix)
    f = tmp_path / "two.txt"
    f.write_text(
        ids["the client owed money"] + "\n" + ids["the client paid money"] + "\n"
    )
    monkeypatch.setattr(latent, "LIMIT", 2 * 5 * 8)  # two passages, five terms
    assert latent.main(["rank", "--index", str(ix), "client money"]) == 2
    assert "--only" in capsys.readouterr().err
    assert (
        latent.main(["rank", "--index", str(ix), "--only", str(f), "client money"]) == 0
    )
