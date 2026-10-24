"""demo/php2shell: what was frozen stays frozen, and its tools do what they say.

The runs fetch PHP's source and are not part of CI; this is.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_trees  # noqa: E402
import score  # noqa: E402

FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def test_every_frozen_file_is_as_it_was_frozen():
    for rel, sha in FROZEN["files"].items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    frozen = set(FROZEN["files"])
    assert {"releases.json", "score.py", "make_trees.py"} <= frozen
    assert {f"questions/{p.name}" for p in (HERE / "questions").iterdir()} <= frozen


def test_the_pins_are_whole():
    pins = make_trees.PINS
    for v, pin in pins["releases"].items():
        assert len(pin["commit"]) == 40 and len(pin["tree"]) == 40, v
    for b, fix in pins["fixes"].items():
        assert (
            fix["vulnerable"] in pins["releases"] and fix["fixed"] in pins["releases"]
        )
        assert len(fix["diff_sha256"]) == 64 and fix["vulnerable"].startswith(b + ".")


@pytest.mark.skipif(os.name != "posix", reason="the sample holds a symlink")
def test_a_tree_hashes_as_git_hashes_it(tmp_path):
    """The sample's hash is git's own (`git write-tree` of these files)."""
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "empty").mkdir()
    (tmp_path / "a" / "b" / "x.txt").write_bytes(b"hi\n")
    (tmp_path / "run.sh").write_bytes(b"#!/bin/sh\n")
    (tmp_path / "run.sh").chmod(0o755)
    (tmp_path / "link").symlink_to("a/b/x.txt")
    (tmp_path / "id.c").write_bytes(b"v1 $Id$ end\n")
    (tmp_path / "a-b").write_bytes(b"a-b\n")  # sorts before the folder a/
    assert make_trees.git_tree(tmp_path) == "8fe92cf6c5ece7e6a31b5629019a0b3867bac28d"
    (tmp_path / "run.sh").chmod(0o644)
    assert make_trees.git_tree(tmp_path) != "8fe92cf6c5ece7e6a31b5629019a0b3867bac28d"
    assert make_trees.git_tree(tmp_path / "empty") == make_trees.EMPTY


def test_an_ident_line_is_put_back_only_when_its_hash_is_the_files_own():
    stored = b"v1 $Id$ end\n"
    sha = make_trees.obj(b"blob", stored)
    assert make_trees.blob(b"v1 $Id: " + sha.encode() + b" $ end\n") == sha
    fake = b"v1 $Id: " + b"0" * 40 + b" $ end\n"
    assert make_trees.blob(fake) == make_trees.obj(b"blob", fake)


def test_check_says_missing_and_differs(tmp_path, capsys):
    assert make_trees.check(tmp_path) == 42
    assert "missing   8.5.11" in capsys.readouterr().out
    (tmp_path / "trees" / "8.5.11").mkdir(parents=True)
    (tmp_path / "trees" / "8.5.11" / "x").write_bytes(b"not php")
    assert make_trees.check(tmp_path) == 2
    assert "DIFFERS   8.5.11" in capsys.readouterr().out


DIFF = """\
diff --git a/main/rfc1867.c b/main/rfc1867.c
--- a/main/rfc1867.c
+++ b/main/rfc1867.c
@@ -1,4 +1,4 @@
 static void unchanged_context_line(void);
-\tzend_bailout_on_memory_limit(heap);
+\tzend_delay_the_oom(heap);
-\tx++;
diff --git a/ext/json/json.c b/ext/json/json.c
--- a/ext/json/json.c
+++ b/ext/json/json.c
@@ -1 +1 @@
-\treturn json_encode_value(buf);
+\treturn json_encode_checked(buf);
diff --git a/ext/session/tests/oom.phpt b/ext/session/tests/oom.phpt
--- a/ext/session/tests/oom.phpt
+++ b/ext/session/tests/oom.phpt
@@ -1 +1 @@
-session upload progress test
+session upload progress test again
diff --git a/NEWS b/NEWS
--- a/NEWS
+++ b/NEWS
@@ -1 +1 @@
-  . Fixed memory limit bailout
+  . Fixed memory limit bailout (CVE)
"""


def test_the_frozen_rule():
    fix = score.changed(DIFF)
    assert fix["old"] == {
        "main/rfc1867.c": {"zend_bailout_on_memory_limit(heap);"},
        "ext/json/json.c": {"return json_encode_value(buf);"},
    }  # x++ is too short; tests and NEWS never count
    assert fix["new"]["main/rfc1867.c"] == {"zend_delay_the_oom(heap);"}
    assert set(fix["files"]) == {"main/rfc1867.c", "ext/json/json.c"}
    c = score.classify
    assert (
        c("main/rfc1867.c:9", "a\n\tzend_bailout_on_memory_limit(heap);", fix, "old")
        == "core"
    )
    assert c("main/rfc1867.c:9", "zend_delay_the_oom(heap);", fix, "old") == "file"
    assert c("main/rfc1867.c:9", "zend_delay_the_oom(heap);", fix, "new") == "core"
    assert (
        c("main/rfc1867.c:1", "static void unchanged_context_line(void);", fix, "old")
        == "file"
    )
    assert c("ext/json/json.c:1", "return json_encode_value(buf);", fix, "old") == "any"
    assert (
        c("ext/session/tests/oom.phpt:1", "session upload progress test", fix, "old")
        == "miss"
    )
    assert (
        c("Zend/zend.c:1", "zend_bailout_on_memory_limit(heap);", fix, "old") == "miss"
    )


def test_each_release_is_scored_against_its_branchs_fix(tmp_path):
    assert score.branch_of("8.5.11") == ("8.5", "old", False)
    assert score.branch_of("8.5.12") == ("8.5", "new", False)
    assert score.branch_of("8.5.10") == ("8.5", "old", False)
    assert score.branch_of("7.4.33") == ("8.2", "old", True)
    (tmp_path / "8.5.diff").write_text(DIFF)
    answers = [
        {"index": "8.5.11", "question": "a", "served": [
            {"where": "ext/json/json.c:1", "text": "return json_encode_value(buf);"},
            {"where": "main/rfc1867.c:2", "text": "zend_bailout_on_memory_limit(heap);"}]},
        {"index": "8.5.12", "question": "a", "served": [
            {"where": "main/rfc1867.c:2", "text": "zend_bailout_on_memory_limit(heap);"}]},
        {"index": "8.5.11", "question": "b", "served": []},
    ]  # fmt: skip
    rows = score.score(answers, tmp_path)
    assert [(r["best"], r["first_hit_rank"], r["side"]) for r in rows] == [
        ("core", 1, "old"), ("file", None, "new"), ("miss", None, "old"),
    ]  # fmt: skip


def test_phase2s_baselines_rank_as_they_say():
    import phase2

    changed = [
        {"path": "a.c", "line": 1, "text": "memory limit here"},
        {"path": "a.c", "line": 9, "text": "memory limit bailout memory"},
        {"path": "b.c", "line": 1, "text": "the session upload"},
        {"path": "c.c", "line": 1, "text": "unrelated words only"},
    ]
    q = "the memory limit bailout"  # "the" is a common word, never counted
    assert [c["line"] for c in phase2.grep(changed, q)] == [9, 1]
    assert phase2.bm25(changed, q)[0]["line"] == 9
    assert phase2.grep(changed, "nothing matches") == []
    assert [c["path"] for c in phase2.diff_size(changed)] == ["a.c", "b.c", "c.c"]
    assert phase2.diff_size(changed)[0]["line"] == 1
    assert phase2.binomial_tail(0, 5, 0.3) == pytest.approx(1.0)
    assert phase2.binomial_tail(5, 5, 0.5) == pytest.approx(1 / 32)


def test_rule_2_adds_an_added_runs_neighbours_and_nothing_further():
    import score2

    d = (
        "--- a/main/main.c\n+++ b/main/main.c\n@@ -1,6 +1,8 @@\n"
        " far away context line\n"
        " before the added run\n"
        "+\tadded_reset_of_globals();\n"
        " after the added run\n"
        " far away again here\n"
        "-\tremoved_old_call(x);\n"
        "+\treplacement_call(x);\n"
        " after the replacement\n"
    )
    v1, v2 = (
        score.changed(d)["old"]["main/main.c"],
        score2.changed(d)["old"]["main/main.c"],
    )
    assert v1 == {"removed_old_call(x);"}
    assert v2 == v1 | {
        "before the added run",
        "after the added run",
        "after the replacement",
    }
    assert score2.changed(d)["new"] == score.changed(d)["new"]
    assert score.changed is not score2.changed  # put back after score_answers


def test_scans_bm25_is_phase_2s_baseline(tmp_path):
    """phase1 ranks with scan's BM25; it must be the BM25 phase 2 measured."""
    import subprocess

    import phase2

    root = HERE.parents[1]
    sys.path.insert(0, str(root / "adapters" / "stdlib" / "scan"))
    import scan

    kernel = phase2.kernel
    old = {"a.c": "memory limit bailout here\n\nsession upload progress\n",
           "b.c": "unchanged memory text\n", "c.c": "limit the post size\n"}  # fmt: skip
    new = {**old, "a.c": "memory limit unwind here\n\nsession upload progress\n"}
    for name, files in (("old", old), ("new", new)):
        for rel, text in files.items():
            (tmp_path / name).mkdir(exist_ok=True)
            (tmp_path / name / rel).write_text(text)
        subprocess.run([sys.executable, str(root / "adapters/stdlib/scan/scan.py"), "index",
                        "--from", str(tmp_path / name), "--to", str(tmp_path / f"ix-{name}")],
                       check=True, capture_output=True)  # fmt: skip
    before = {c["id"] for c in kernel.chunks(tmp_path / "new")}
    ix = scan.Index(tmp_path / "ix-old")
    changed = [c for c in ix.pile if c["id"] not in before]
    for q in ("memory limit bailout", "session memory", "post size limit", "nothing"):
        assert ix.bm25(q, 3, before) == phase2.bm25(changed, q), q


def test_phase6s_kappa():
    import phase6

    assert phase6.kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert phase6.kappa([True, True, False, False], [True, False, True, False]) == 0.0
    assert phase6.kappa([True, False], [False, True]) == -1.0


def test_phase3s_files_left_out():
    import phase3

    assert phase3.counts("c/dec/decode.c") and phase3.counts("regcomp.c")
    for path in ("test/ruby/test_regexp.rb", "log4j-core/src/test/java/A.java",
                 "src/changes/changes.xml", "version.h", "NEWS", "a/tests/x.c", "x.phpt"):  # fmt: skip
        assert not phase3.counts(path), path


def test_phase3s_rule_is_rule_2_with_its_files_left_out():
    import phase3

    d = (
        "--- a/regcomp.c\n+++ b/regcomp.c\n@@ -1,3 +1,4 @@\n"
        " if (num_repeat > max_repeats)\n+    return ONIGERR_TOO_BIG;\n"
        " reg->num_repeat = num_repeat;\n"
        "--- a/version.h\n+++ b/version.h\n@@ -1 +1 @@\n"
        "-#define RUBY_PATCHLEVEL 111\n+#define RUBY_PATCHLEVEL 112\n"
    )
    fix = phase3.changed(d)
    assert set(fix["old"]) == {"regcomp.c"}
    assert score.counts("version.h")  # put back after
    assert phase3.hit(
        {"path": "regcomp.c", "text": "x\nif (num_repeat > max_repeats)"}, fix
    )
    assert not phase3.hit({"path": "regcomp.c", "text": "something else entirely"}, fix)
    assert not phase3.hit(
        {"path": "version.h", "text": "#define RUBY_PATCHLEVEL 111"}, fix
    )


@pytest.mark.skipif(os.name != "posix", reason="the sample holds a symlink")
def test_phase3_writes_a_tree_as_git_stores_it(tmp_path):
    import shutil
    import subprocess

    import phase3

    if not shutil.which("git"):
        pytest.skip("needs the git program")  # the runs need it too; CI has it
    repo = tmp_path / "repo"
    repo.mkdir()

    def run(*a):
        return subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True)

    run("init", "-q")
    (repo / "a").mkdir()
    (repo / "a" / "x.c").write_bytes(b"int x;\r\n")  # CRLF, kept as stored
    (repo / "run.sh").write_bytes(b"#!/bin/sh\n")
    (repo / "run.sh").chmod(0o755)
    (repo / "link").symlink_to("a/x.c")
    (repo / ".gitattributes").write_bytes(b"a/* export-ignore\n*.sh eol=crlf\n")
    run("add", "-A")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x")
    commit = run("rev-parse", "HEAD").stdout.decode().strip()
    tree = run("rev-parse", "HEAD^{tree}").stdout.decode().strip()
    out = tmp_path / "out"
    phase3.write_tree(repo, commit, out)
    assert make_trees.git_tree(out) == tree  # export rules leave nothing out
    assert (out / "a" / "x.c").read_bytes() == b"int x;\r\n"


def test_phase4s_chance_is_exact():
    import itertools
    import random as _r

    import phase4

    # chance_one against brute force over all k-subsets
    for n, h, k in [(6, 2, 3), (8, 3, 2), (5, 0, 3), (5, 5, 1), (7, 1, 4)]:
        ids = list(range(n))
        hits = set(range(h))
        total = win = 0
        for combo in itertools.combinations(ids, k):
            total += 1
            win += any(x in hits for x in combo)
        assert phase4.chance_one(n, h, k) == pytest.approx(win / total), (n, h, k)

    # poisson_binomial_tail against Monte Carlo
    ps = [0.1, 0.3, 0.5, 0.9, 0.2]
    rng = _r.Random(0)
    trials = 200000
    for k in (1, 3, 5):
        mc = sum(sum(rng.random() < p for p in ps) >= k for _ in range(trials)) / trials
        assert abs(phase4.poisson_binomial_tail(ps, k) - mc) < 0.01, k
    assert phase4.poisson_binomial_tail([], 0) == 1.0


def test_phase4s_recall_and_hit_sets():
    import phase4

    class FakeIx:
        def __init__(self, pile):
            self.pile = pile

    pile = [
        {"id": "a", "path": "main/rfc1867.c", "text": "the changed line here"},
        {"id": "b", "path": "main/rfc1867.c", "text": "untouched line"},
        {"id": "c", "path": "ext/json/json.c", "text": "the changed line here"},
        {"id": "d", "path": "other.c", "text": "nothing"},
    ]
    fix = {
        "old": {
            "main/rfc1867.c": {"the changed line here"},
            "ext/json/json.c": {"the changed line here"},
        },
        "files": {"main/rfc1867.c", "ext/json/json.c"},
    }
    line, file, n = phase4.hit_sets(FakeIx(pile), fix, {"main/rfc1867.c"})
    assert line == {"a"} and file == {"a", "b"} and n == 4
    line2, file2, _ = phase4.hit_sets(FakeIx(pile), fix, None)
    assert line2 == {"a", "c"} and file2 == {"a", "b", "c"}
    served = [pile[3], pile[1], pile[0]]  # a (a hit) is third
    assert phase4.recall_at(served, {"a"}, (1, 3)) == {1: False, 3: True}
    assert phase4.recall_at(served, {"z"}, (1, 3)) == {1: False, 3: False}


def test_phase4_grep_matches_brute_force(tmp_path):
    import subprocess as sp
    import sys as _s

    import phase4

    root = HERE.parents[1]
    _s.path.insert(0, str(root / "adapters" / "stdlib" / "scan"))
    import scan

    files = {
        "a.c": "memory limit bailout during request\n\nunrelated text here\n",
        "b.c": "the request bailout path\n",
        "c.c": "limit the memory again\n",
        "d.c": "nothing relevant at all\n",
        "e.c": "memory memory memory limit\n",
    }
    src = tmp_path / "src"
    src.mkdir()
    for rel, text in files.items():
        (src / rel).write_text(text)
    sp.run(
        [
            _s.executable,
            str(root / "adapters/stdlib/scan/scan.py"),
            "index",
            "--from",
            str(src),
            "--to",
            str(tmp_path / "ix"),
        ],
        check=True,
        capture_output=True,
    )
    ix = scan.Index(tmp_path / "ix")

    def brute(q, top):
        ws = set(w for w in scan.kernel.words(q) if w not in scan.kernel.FUNCTION)
        got = [
            (-len(ws & set(scan.kernel.words(c["text"]))), i)
            for i, c in enumerate(ix.pile)
        ]
        got = [(h, i) for h, i in got if h]
        return [ix.pile[i] for _, i in sorted(got)][:top]

    for q in (
        "memory limit bailout",
        "request path",
        "the",
        "memory memory",
        "nothing relevant",
    ):
        fast = [(c["path"], c["line"]) for c in phase4.grep_rank(ix, q, 50)]
        slow = [(c["path"], c["line"]) for c in brute(q, 50)]
        assert fast == slow, q
