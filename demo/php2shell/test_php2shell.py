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
