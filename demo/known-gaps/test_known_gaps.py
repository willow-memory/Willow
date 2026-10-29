"""demo/known-gaps: what was frozen stays frozen, and its tools do what they say.

The runs read the fleet's own repositories and are not part of CI; this is.
Every fixture is a tiny git repository built in a temporary folder.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trees  # noqa: E402

score = trees.sibling("score")
FROZEN_FILE = HERE / "FROZEN.json"
pytestmark = pytest.mark.skipif(not shutil.which("git"), reason="needs the git program")

OLD_GUARD = (
    "def check(user, path):\n"
    "    allowed = load_the_whole_policy(root_path)\n"
    "    return allowed\n"
)
NEW_GUARD = (
    "def check(user, path):\n"
    "    allowed = load_the_whole_policy(user.repo_path)\n"
    "    verify_the_policy_signature(allowed)\n"
    "    return allowed\n"
)


def freeze_is_listed() -> bool:
    """FILES.md lists FROZEN.json among this folder's files: true from the
    freeze commit on, which adds the line with the file."""
    text = (trees.ROOT / "FILES.md").read_text(encoding="utf-8")
    start = text.index("├── known-gaps/")
    end = text.index("├── craft-assembly/", start)
    return "FROZEN.json" in text[start:end]


def test_every_frozen_file_is_as_it_was_frozen():
    if not FROZEN_FILE.exists():
        if freeze_is_listed():
            pytest.fail(
                "FROZEN.json is listed in FILES.md but missing: the freeze is gone"
            )
        pytest.skip("not frozen yet: FROZEN.json is the operator's freeze commit")
    frozen = json.loads(FROZEN_FILE.read_text(encoding="utf-8"))
    for rel, sha in frozen["files"].items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    assert {"gaps.json", "pins.json", "score.py", "trees.py", "resolve.py", "ask.py",
            "origin.py", "run.py"} <= set(frozen["files"])  # fmt: skip
    # every tool the rule and the statistics run on, re-hashed too
    assert set(frozen["tools_at_freeze"]) == set(trees.TOOLS)
    for rel, sha in frozen["tools_at_freeze"].items():
        got = hashlib.sha256((trees.ROOT / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )


def test_the_twelve_gaps_are_whole_and_redacted():
    doc = json.loads((HERE / "gaps.json").read_text(encoding="utf-8"))
    assert set(doc) == {"about", "written", "gaps", "evidence_weight"}
    assert [g["id"] for g in doc["gaps"]] == [f"KG{n:02d}" for n in range(1, 13)]
    for g in doc["gaps"]:
        assert g["source_kind"] in ("gap_record", "audit_finding", "commit_message")
        assert g["fix_kind"] and g["class"] and g["fix"]
    spec = importlib.util.spec_from_file_location(
        "tr", trees.ROOT / "adapters/stdlib/transcript-redact/transcript_redact.py"
    )
    tr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tr)

    def strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for k, v in x.items():
                yield k
                yield from strings(v)
        elif isinstance(x, list):
            for v in x:
                yield from strings(v)

    for s in strings(doc):
        assert tr.redact(s) == (s, []), s  # nothing a redaction would take out
        assert "/home/" not in s and "/Users/" not in s, s


def test_the_pins_are_whole():
    pins = trees.load_pins()
    gaps = trees.load_gaps()
    assert {u["gap"] for u in pins.values()} == set(gaps)
    for unit, pin in pins.items():
        for side in ("vulnerable", "fixed"):
            assert len(pin[side]["commit"]) == 40 and len(pin[side]["tree"]) == 40, unit
        assert len(pin["diff_sha256"]) == 64 and pin["vulnerable"] != pin["fixed"], unit
    n = {g: sum(u["gap"] == g for u in pins.values()) for g in gaps}
    assert n["KG03"] == n["KG07"] == 2 and sum(n.values()) == 14
    assert {
        "KG03-kartikeya",
        "KG03-willow-mcp",
        "KG07-kartikeya",
        "KG07-willow-mcp",
    } <= set(pins)
    assert set(pins["KG12"]["files_scored"]) == {
        "grove/seat_record.py",
        "grove/table_boxes.py",
    }


def test_kg05_and_kg06_are_scored_on_the_file_their_finding_names():
    pins, gaps = trees.load_pins(), trees.load_gaps()
    for gid, name in (("KG05", "trust_owner_verbs.py"), ("KG06", "ci_lint_pin.py")):
        files = pins[gid]["files_scored"]
        assert len(files) == 1 and files[0].endswith("/" + name), gid
        assert files == gaps[gid]["fix"][0]["files_scored"]
        assert files[0] in pins[gid]["diff_files"]  # the fix's diff touches it
        assert name in gaps[gid]["class"] + " " + gaps[gid]["note"], gid
    assert pins["KG05"]["files_scored"] != pins["KG06"]["files_scored"]
    assert pins["KG05"]["diff_sha256"] != pins["KG06"]["diff_sha256"]
    assert pins["KG05"]["fixed"] == pins["KG06"]["fixed"]  # one fix commit
    for unit, pin in pins.items():  # every scored file is in its fix's diff
        for f in pin["files_scored"] or []:
            assert f in pin["diff_files"], (unit, f)


def test_this_folders_score_is_not_php2shells():
    assert "score" not in sys.modules or sys.modules["score"].__file__ != str(
        HERE / "score.py"
    )
    assert score.__file__ == str(HERE / "score.py")
    assert trees.phase3.score.__file__ != score.__file__


# -- the hit rule, on a hand-made diff ---------------------------------------

DIFF = """\
diff --git a/app/guard.py b/app/guard.py
--- a/app/guard.py
+++ b/app/guard.py
@@ -1,6 +1,7 @@
 far away context line one
 far away context line two
-    allowed = load_the_whole_policy(root_path)
+    allowed = load_the_whole_policy(user.repo_path)
 context just after the change
 context further down the file
 context at the very bottom
+    verify_the_policy_signature(allowed)
diff --git a/app/test_guard.py b/app/test_guard.py
--- a/app/test_guard.py
+++ b/app/test_guard.py
@@ -1 +1 @@
-    assert check(user, path) == allowed_by_policy
+    assert check(user, path) == allowed_by_the_signed_policy
diff --git a/tests/helper.py b/tests/helper.py
--- a/tests/helper.py
+++ b/tests/helper.py
@@ -1 +1 @@
-    build_the_whole_policy_fixture(root_path)
+    build_the_whole_policy_fixture(user.repo_path)
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -1 +1 @@
-- Fixed the policy path escape
+- Fixed the policy path escape (gap)
diff --git a/pkg/version.py b/pkg/version.py
--- a/pkg/version.py
+++ b/pkg/version.py
@@ -1 +1 @@
-VERSION_STRING = "0.1.0"
+VERSION_STRING = "0.1.1"
"""


def test_the_hit_rule():
    fix = score.changed(DIFF)
    assert fix["old"] == {
        "app/guard.py": {
            "allowed = load_the_whole_policy(root_path)",
            "context just after the change",
            "context at the very bottom",
        }
    }  # removed lines, and the one line next to an added run; no far context
    assert set(fix["files"]) == {"app/guard.py"}  # tests, changelog, version never
    # by position: the removed line (3), the line after the added run that
    # replaces it (4), and the line before the run added at the bottom (6)
    assert fix["pos"] == {"app/guard.py": {3, 4, 6}}
    assert fix["hunks"] == {"app/guard.py": [(1, 6)]}

    def at(line, text, path="app/guard.py"):
        return {"path": path, "line": line, "text": text}

    far = at(1, "far away context line one\nfar away context line two")
    near = at(2, "x\nallowed = load_the_whole_policy(root_path)")
    other = at(1, "something else entirely")
    assert not score.hit(far, fix) and score.classify(far, fix) == "file"
    assert score.hit(near, fix) and score.classify(near, fix) == "hit"
    assert score.classify(other, fix) == "file"
    new_side = at(1, "verify_the_policy_signature(allowed)")
    assert not score.hit(new_side, fix)  # a line the fix added is not in the old code
    assert score.classify(new_side, fix) == "file"
    assert score.classify(at(2, near["text"], "elsewhere.py"), fix) == "miss"
    after = at(6, "    context at the very bottom")
    assert score.hit(after, fix)  # the neighbour of an added run counts
    two_away = at(5, "context further down the file")
    assert not score.hit(two_away, fix)  # a context line not next to an added run
    # the same line as a removed one, far from every hunk: text says hit, position no
    dup = at(40, "allowed = load_the_whole_policy(root_path)")
    assert score.hit_by_text(dup, fix) and not score.hit(dup, fix)
    assert score.classify(dup, fix) == "file" and not score.in_a_hunk(dup, fix)
    assert score.in_a_hunk(far, fix)
    # a long passage that spans the change is a hit, and names the lines it holds
    wide = at(1, "\n".join(f"line {n} of the file" for n in range(1, 8)))
    assert score.hit(wide, fix) and score.hit_lines(wide, fix) == [3, 4, 6]
    assert score.ranges(wide, fix) == ["app/guard.py:3-4", "app/guard.py:6-6"]
    assert score.hit_lines(near, fix) == [3]
    assert score.ranges(near, fix) == ["app/guard.py:3-3"]
    assert trees.phase3.counts is score.PHP2SHELL_COUNTS  # put back after


def test_positions_follow_the_hunk_header_not_the_look_of_a_line():
    d = (
        "diff --git a/q.sql b/q.sql\n--- a/q.sql\n+++ b/q.sql\n@@ -1,3 +1,2 @@\n"
        " select the whole table\n"
        "--- drop the comment line\n"
        " from some table here\n"
        "\\ No newline at end of file\n"
        "diff --git a/new.py b/new.py\n--- /dev/null\n+++ b/new.py\n@@ -0,0 +1,2 @@\n"
        "+a brand new first line\n+a brand new second line\n"
    )
    fix = score.changed(d)
    assert fix["pos"] == {"q.sql": {2}}  # a removed line that reads like a header
    assert fix["hunks"] == {"q.sql": [(1, 3)]}


def test_files_php2shell_counts_and_ours_left_out():
    for path in ("grove/seat_record.py", "src/willow/guard.py", "a/b/testing_tools.py"):
        assert score.counts(path), path
    for path in ("tests/x.py", "src/test_x.py", "x_test.py", "conftest.py", "CHANGELOG.md",
                 "docs/CHANGELOG", "VERSION", "pkg/_version.py", "NEWS", "version.h",
                 ".release-please-manifest.json", "a/spec/b.py", "src/changes/c.py"):  # fmt: skip
        assert not score.counts(path), path


def test_a_hit_range_joins_neighbouring_lines():
    p = {
        "path": "a.py",
        "line": 10,
        "text": "aa bb cc one\nxx\naa bb cc two\naa bb cc three",
    }
    fix = {"pos": {"a.py": {10, 12, 13}}, "files": {"a.py"}}
    assert score.ranges(p, fix) == ["a.py:10-10", "a.py:12-13"]


# -- fixtures: a tiny repository with a merged fix and a lone-commit fix -----

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.test",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.test"}  # fmt: skip


def git(repo: Path, *argv: str, date: str | None = None) -> str:
    env = {**os.environ, **ENV}
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    done = subprocess.run(["git", *argv], cwd=repo, env=env, check=True,
                          capture_output=True, text=True)  # fmt: skip
    return done.stdout.strip()


def make_repo(tmp: Path) -> tuple:
    """(repos, vulnerable commit, merge commit, lone fix commit)."""
    repo = tmp / "repos" / "demo-repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    (repo / "app").mkdir()
    (repo / "tests").mkdir()
    (repo / "app" / "guard.py").write_text(OLD_GUARD)
    (repo / "app" / "other.py").write_text("print('untouched file here')\n")
    (repo / "tests" / "t.py").write_text("assert True\n")
    git(repo, "add", "-A")
    git(
        repo,
        "commit",
        "-qm",
        "guard: first version, gap 0123456789ab",
        date="2026-01-01T12:00:00+00:00",
    )
    vuln = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "-b", "fix")
    (repo / "app" / "guard.py").write_text(NEW_GUARD)
    (repo / "tests" / "t.py").write_text("assert check\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "fix the policy path", date="2026-01-11T12:00:00+00:00")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "--no-ff", "-qm", "Merge pull request #7 from x/fix", "fix",
        date="2026-01-11T13:00:00+00:00")  # fmt: skip
    merge = git(repo, "rev-parse", "HEAD")
    (repo / "app" / "other.py").write_text("print('the lone fix, changed here')\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "lone fix", date="2026-01-12T12:00:00+00:00")
    return tmp / "repos", vuln, merge, git(repo, "rev-parse", "HEAD")


def gaps_for(merge: str, lone: str) -> dict:
    """KG01 a merged fix; KG09 a lone commit; KG10 the merge narrowed to a file;
    KG03 fixed twice (two units)."""
    fix = {"repo": "demo-repo", "kind": "merge", "pr": 7, "merge": merge[:7]}
    return {
        "KG01": {"id": "KG01", "fix": [fix]},
        "KG09": {"id": "KG09", "fix": [{"repo": "demo-repo", "kind": "commit",
                                        "commit": lone[:7]}]},
        "KG10": {"id": "KG10", "fix": [{**fix, "files_scored": ["app/guard.py"]}]},
        "KG03": {"id": "KG03", "fix": [fix, {**fix, "repo": "demo-twin"}]},
    }  # fmt: skip


def test_resolve_pins_the_two_sides_and_the_diff(tmp_path):
    resolve = trees.sibling("resolve")
    repos, vuln, merge, lone = make_repo(tmp_path)
    shutil.copytree(repos / "demo-repo", repos / "demo-twin")
    units = resolve.resolve(repos, gaps_for(merge, lone))
    assert set(units) == {"KG01", "KG09", "KG10", "KG03-demo-repo", "KG03-demo-twin"}
    repo = repos / "demo-repo"
    assert units["KG01"]["vulnerable"]["commit"] == git(repo, "rev-parse", merge + "^1")
    assert units["KG01"]["vulnerable"]["commit"] == vuln  # a merge's first parent
    assert units["KG01"]["fixed"]["commit"] == merge and units["KG01"]["gap"] == "KG01"
    assert units["KG01"]["vulnerable"]["tree"] == git(
        repo, "rev-parse", vuln + "^{tree}"
    )
    diff = subprocess.run(["git", *trees.DIFF, vuln, merge], cwd=repo, check=True,
                          capture_output=True).stdout  # fmt: skip
    assert units["KG01"]["diff_sha256"] == hashlib.sha256(diff).hexdigest()
    assert b"tests/t.py" in diff and units["KG01"]["files_scored"] is None
    assert units["KG01"]["diff_files"] == ["app/guard.py", "tests/t.py"]
    narrow = subprocess.run(["git", *trees.DIFF, vuln, merge, "--", "app/guard.py"], cwd=repo,
                            check=True, capture_output=True).stdout  # fmt: skip
    assert b"tests/t.py" not in narrow
    assert units["KG10"]["diff_sha256"] == hashlib.sha256(narrow).hexdigest()
    assert units["KG10"]["diff_sha256"] != units["KG01"]["diff_sha256"]
    assert units["KG09"]["vulnerable"]["commit"] == merge  # a lone commit's parent
    assert units["KG09"]["fixed"]["commit"] == lone


def test_resolve_refuses_what_it_cannot_pin(tmp_path):
    resolve = trees.sibling("resolve")
    repos, vuln, merge, lone = make_repo(tmp_path)
    fix = {"repo": "demo-repo", "kind": "merge", "pr": 8, "merge": merge[:7]}
    with pytest.raises(ValueError, match="#8"):
        resolve.resolve(repos, {"G": {"id": "G", "fix": [fix]}})
    first = {"repo": "demo-repo", "kind": "commit", "commit": vuln[:7]}
    with pytest.raises(ValueError, match="0 parents"):
        resolve.resolve(repos, {"G": {"id": "G", "fix": [first]}})
    twice = {"repo": "demo-repo", "kind": "commit", "commit": lone[:7]}
    with pytest.raises(ValueError, match="twice"):
        resolve.resolve(repos, {"G": {"id": "G", "fix": [twice, twice]}})
    outside = {**fix, "pr": 7, "files_scored": ["app/nope.py"]}
    with pytest.raises(ValueError, match="not in the diff"):
        resolve.resolve(repos, {"G": {"id": "G", "fix": [outside]}})
    assert resolve.main(["--repos", str(repos)]) == 2


def pinned(tmp_path):
    resolve = trees.sibling("resolve")
    repos, vuln, merge, lone = make_repo(tmp_path)
    units = resolve.resolve(repos, {k: v for k, v in gaps_for(merge, lone).items()
                                    if k != "KG03"})  # fmt: skip
    return repos, units, (vuln, merge, lone)


def test_trees_fetch_check_and_the_exit_codes(tmp_path, capsys):
    repos, units, _ = pinned(tmp_path)
    to = tmp_path / "work"
    assert trees.check(to, units) == 42
    assert "missing   KG01 old" in capsys.readouterr().out
    for unit, pin in units.items():
        trees.fetch_unit(to, repos, unit, pin)
    assert trees.check(to, units) == 0
    assert (to / "trees" / "KG01" / "old" / "app" / "guard.py").read_text() == OLD_GUARD
    assert (to / "trees" / "KG01" / "new" / "app" / "guard.py").read_text() == NEW_GUARD
    (to / "trees" / "KG01" / "new" / "app" / "guard.py").write_text("tampered\n")
    assert trees.check(to, units) == 2
    assert "DIFFERS   KG01 new" in capsys.readouterr().out
    (to / "trees" / "KG01" / "new" / "app" / "guard.py").write_text(NEW_GUARD)
    (to / "fixes" / "KG01.diff").write_bytes(b"not the diff")
    assert trees.check(to, units) == 2
    assert "DIFFERS   KG01 fix" in capsys.readouterr().out
    assert trees.main(["bogus"]) == 2 and trees.main(["check"]) == 2


def test_ask_scores_and_origin_follow_the_fix_back(tmp_path):
    ask = trees.sibling("ask")
    origin = trees.sibling("origin")
    repos, units, (vuln, merge, lone) = pinned(tmp_path)
    to, ix = tmp_path / "work", tmp_path / "ix"
    trees.fetch_unit(to, repos, "KG01", units["KG01"])
    pin = units["KG01"]
    qs = [("KG01 1", "load the whole policy from the root path"), ("KG01 2", "qqqq zzzz"),
          ("null 1", "load the whole policy from the root path"), ("KG09 1", "ignored")]  # fmt: skip
    rows = ask.ask(to, ix, "KG01", pin, qs, "found")
    answers = [r for r in rows if r["type"] == "answer"]
    # another gap's question isn't asked, and phase 1 asks no null question
    assert {r["gap"] for r in answers} == {"KG01"}
    assert {r["ranked_by"] for r in answers} == {"kernel", "bm25", "grep"}
    assert len(list((ix).iterdir())) == 2  # one index a tree hash
    stats = rows[-1]
    assert (
        stats["type"] == "stats"
        and stats["changed"] >= 1
        and stats["hit_passages"] >= 1
    )
    assert 0 < stats["random_rate"] <= 1
    assert stats["file_passages"] >= stats["hit_passages"]
    ranked = [r for r in answers if r["ranked_by"] == "bm25" and r["gap"] == "KG01"]
    assert len(ranked[0]["served"]) <= stats["changed"]  # all of the changed set ranked
    whole = ask.ask(to, ix, "KG01", pin, qs, "before")
    after = whole[-1]
    assert after["mode"] == "before" and after["changed"] > stats["changed"]
    assert after["random_rate"] == ask.phase4.chance_one(
        after["changed"], after["hit_passages"], 10
    )
    assert after["file_passages"] >= 1
    assert {r["gap"] for r in whole if r["type"] == "answer"} == {"KG01", "null"}
    for key in ("hit_by_text", "text_only", "text_outside_hunks"):
        assert key in stats and key in after
    assert (
        0 <= stats["text_outside_hunks"] <= stats["text_only"] <= stats["hit_by_text"]
    )
    scored = score.score(answers, to / "fixes")
    got = {(r["question"], r["ranked_by"]): r for r in scored}
    one = got[("KG01 1", "bm25")]
    assert one["best"] == "hit" and one["first_hit_rank"] == 1
    assert (
        got[("KG01 2", "bm25")]["best"] == "miss"
        and got[("KG01 2", "bm25")]["served"] == []
    )
    assert one["ranges"] == ["app/guard.py:2-3"]  # the changed line, and its neighbour
    assert ask.ask(to, ix, "KG01", pin, qs, "found") == rows  # the same bytes again
    # origin: whose.py at the vulnerable commit
    found = origin.origins(
        repos, {"KG01": units["KG01"]}, {("KG01", "app/guard.py:2-3")}
    )
    assert len(found) == 1 and found[0]["commit"] == vuln
    assert found[0]["refs"] == ["0123456789ab"] and found[0]["days_open"] == 10
    assert found[0]["title"].startswith("guard: first version")
    bad = origin.origins(repos, {"KG01": units["KG01"]}, {("KG01", "app/nope.py:1-1")})
    assert "why" in bad[0] and "commit" not in bad[0]  # listed with why, never dropped
    assert origin.main([]) == 2


def test_the_rank_of_the_first_hit_is_exact_under_random_order():
    import itertools

    run = trees.sibling("run")
    for n, h in [(5, 2), (6, 1), (4, 4), (7, 3)]:
        firsts = [min(c) for c in itertools.combinations(range(1, n + 1), h)]
        brute = [firsts.count(r) / len(firsts) for r in range(1, n + 1)]
        assert run.rank_pmf(n, h) == pytest.approx(brute), (n, h)
    assert run.rank_pmf(4, 0) == [0.0, 0.0, 0.0, 1.0]  # no hit: counts as last
    assert run.first_rank({"first_hit_rank": 3}, 7) == 3
    assert run.first_rank({"first_hit_rank": None}, 7) == 7  # never returned: last
    assert run.rank_statistic([(1, 5), (2, 5), (4, 5)]) == 1.75


def test_the_rank_statistic_beats_random_orderings_only_when_it_should():
    run = trees.sibling("run")
    sizes = [(10, 2)] * 12
    first = run.rank_statistic([(1, 10)] * 12)
    last = run.rank_statistic([(10, 10)] * 12)
    expected, p_first = run.rank_p(sizes, first, run.random.Random("a"))
    _, p_last = run.rank_p(sizes, last, run.random.Random("a"))
    assert p_first < 0.01 and p_last > 0.9 and last < expected < first
    again = run.rank_p(sizes, first, run.random.Random("a"))
    assert again == (expected, p_first)  # the seed fixes it


def scored_row(unit, gap, by, served, first, q="1"):
    return {"unit": unit, "gap": gap, "question": f"{gap} {q}", "ranked_by": by,
            "served": served, "first_hit_rank": first,
            "best": "hit" if "hit" in served else "file" if "file" in served else "miss"}  # fmt: skip


def test_phase_1_is_judged_by_the_rank_of_the_first_hit(tmp_path, capsys):
    run = trees.sibling("run")
    stats = [{"type": "stats", "unit": u, "gap": u, "changed": 10, "hit_passages": 2,
              "random_rate": 0.5} for u in ("KG01", "KG09")]  # fmt: skip
    group = {"KG01": "strong", "KG09": "weaker"}
    ten = ["miss"] * 10

    def pairs(first):
        out = []
        for u in ("KG01", "KG09"):
            for q in range(4):
                served = (
                    ten[:]
                    if first is None
                    else ten[: first - 1] + ["hit"] + ten[first:]
                )
                out.append(scored_row(u, u, "bm25", served, first, str(q)))
        return out

    out = run.judge(stats, pairs(1), group)
    # no null gate in phase 1: a null question's hit in a handful of passages
    # is luck, so the phase asks none
    assert out["passes"] == {"rank, bm25, strong": True, "rank, bm25, weaker": True}
    assert out["draws"] == 100_000 and out["seed"] == run.SEED
    assert out["rank"]["bm25, strong"]["observed"] == 4.0
    assert out["top3_hit_rate"]["bm25, strong"]["hits"] == 4
    lost = run.judge(stats, pairs(None), group)  # never returned: last
    assert not lost["passes"]["rank, bm25, strong"]
    assert lost["rank"]["bm25, strong"]["observed"] == pytest.approx(0.4)
    late = run.judge(stats, pairs(10), group)
    assert not late["passes"]["rank, bm25, weaker"]
    leak = [scored_row("KG01", "null", "bm25", ["hit"], 1)]
    assert run.judge(stats, pairs(1) + leak, group)["passes"] == out["passes"]


def test_phase_2_is_judged_at_the_line_level_against_exact_chance():
    run = trees.sibling("run")
    stats = [{"type": "stats", "unit": u, "gap": u, "changed": 100, "hit_passages": 5,
              "file_passages": 10, "random_rate": 0.4} for u in ("KG01", "KG09")]  # fmt: skip
    group = {"KG01": "strong", "KG09": "weaker"}
    chance = 1 - math.comb(95, 10) / math.comb(100, 10)
    assert 0.4 < chance < 0.45

    def rows(unit, served):
        return [scored_row(unit, unit, "bm25", served, None, str(q)) for q in range(16)]

    hit = ["miss", "hit", "miss"]
    # the null questions, asked of every unit, sit at chance: that passes
    quiet = [
        scored_row("KG01", "null", "bm25", ["miss"] * 10, None, str(q))
        for q in range(16)
    ]
    out = run.judge_before(stats, rows("KG01", hit) + rows("KG09", hit) + quiet, group)
    assert out["passes"] == {"line level above chance, bm25, strong": True,
                             "line level above chance, bm25, weaker": True,
                             "null questions not above chance, bm25": True}  # fmt: skip
    strong = out["table"]["bm25, strong"]
    assert strong["line_hits@10"] == 16 and strong["file_hits@10"] == 16
    assert strong["line_expected"] == pytest.approx(16 * chance)
    assert strong["line_p"] < 0.01
    # file hits alone do not pass: the file level is reported, not judged
    file_only = ["miss", "file", "miss"]
    only = run.judge_before(stats, rows("KG01", file_only) + rows("KG09", hit), group)
    assert not only["passes"]["line level above chance, bm25, strong"]
    assert only["table"]["bm25, strong"]["file_hits@10"] == 16  # still reported
    assert only["table"]["bm25, strong"]["file_p"] < 0.01
    none = run.judge_before(
        stats, rows("KG01", ["miss"] * 10) + rows("KG09", hit), group
    )
    assert not none["passes"]["line level above chance, bm25, strong"]
    assert none["table"]["bm25, strong"]["line_p"] == 1.0
    thin = run.judge_before(stats, rows("KG01", hit)[:3] + rows("KG09", hit), group)
    assert not thin["passes"]["line level above chance, bm25, strong"]  # 3 of 3
    deep = ["miss"] * 10 + ["hit"]  # an 11th is outside the top 10
    assert not run.judge_before(stats, rows("KG01", deep), group)["passes"][
        "line level above chance, bm25, strong"
    ]


def test_phase_2_null_questions_must_not_be_above_chance():
    run = trees.sibling("run")
    stats = [{"type": "stats", "unit": u, "gap": u, "changed": 100, "hit_passages": 5,
              "file_passages": 10, "random_rate": 0.4} for u in ("KG01", "KG09")]  # fmt: skip
    group = {"KG01": "strong", "KG09": "weaker"}  # chance per null question: 0.416

    def nulls(hits, n=16, by="bm25", served=10):
        return [scored_row("KG01", "null", by, (["hit"] if q < hits else ["miss"]) +
                           ["miss"] * (served - 1), None, str(q))
                for q in range(n)]  # fmt: skip

    def gate(rows):
        return run.judge_before(stats, rows, group)["passes"][
            "null questions not above chance, bm25"
        ]

    assert gate(nulls(7))  # 7 of 16 where 6.7 are expected: at chance, passes
    assert gate(nulls(0))
    assert not gate(nulls(16))  # every null a hit: well above chance, fails
    assert not gate(nulls(13))
    assert not gate([])  # none asked: not a pass
    # only bm25 is judged; a noisy grep null is reported, not gated
    assert gate(nulls(7) + nulls(16, by="grep"))
    table = run.judge_before(stats, nulls(16), group)["table"]["bm25, null"]
    assert table["line_hits@10"] == 16 and table["above_chance_p"] < 0.01


def test_phase_2_null_chance_is_for_the_passages_actually_served():
    run = trees.sibling("run")
    stats = [{"type": "stats", "unit": "KG01", "gap": "KG01", "changed": 100,
              "hit_passages": 5, "file_passages": 10, "random_rate": 0.4}]  # fmt: skip

    def nulls(hits, served, n=16):
        return [scored_row("KG01", "null", "bm25", (["hit"] if q < hits else ["miss"]) +
                           ["miss"] * (served - 1), None, str(q))
                for q in range(n)]  # fmt: skip

    def judged(rows):
        out = run.judge_before(stats, rows, {"KG01": "strong"})
        return out["passes"]["null questions not above chance, bm25"], out["table"]

    ok, _ = judged(nulls(7, served=10))  # 7 of 16, ten served each: at chance
    assert ok
    # the same 7 hits when each question was served only 3 passages: the chance
    # of a hit is 0.14 a question, so 7 of 16 is well above it (assumed 10, it passed)
    ok, table = judged(nulls(7, served=3))
    assert not ok
    assert table["bm25, null"]["line_expected"] == pytest.approx(
        16 * (1 - math.comb(95, 3) / math.comb(100, 3))
    )
    # a set that retrieves nothing is unreachable, never a trivial pass
    empty = [scored_row("KG01", "null", "bm25", [], None, str(q)) for q in range(16)]
    ok, table = judged(empty)
    assert not ok
    assert table["bm25, null"]["unreachable"] == "the null set retrieved nothing"
    assert table["bm25, null"]["served_nothing"] == 16
    # one empty question among served ones is reported, not fatal
    mixed = nulls(0, served=10)[:15] + empty[:1]
    ok, table = judged(mixed)
    assert ok and table["bm25, null"]["served_nothing"] == 1


def test_the_changed_set_is_limited_by_path_not_by_text(tmp_path):
    """An unscored file whose passage reads exactly like a scored file's must
    not enter the pool (the limit by text id let it in)."""
    ask = trees.sibling("ask")
    resolve = trees.sibling("resolve")
    repo = tmp_path / "repos" / "dup-repo"
    (repo / "app").mkdir(parents=True)
    (repo / "docs").mkdir()
    git(repo, "init", "-q", "-b", "main")
    for f in ("app/guard.py", "docs/copy.py"):  # the same paragraph, twice
        (repo / f).write_text(OLD_GUARD)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "first", date="2026-01-01T12:00:00+00:00")
    for f in ("app/guard.py", "docs/copy.py"):
        (repo / f).write_text(NEW_GUARD)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "fix", date="2026-01-02T12:00:00+00:00")
    fix = git(repo, "rev-parse", "HEAD")
    gaps = {"KG10": {"id": "KG10", "fix": [{"repo": "dup-repo", "kind": "commit",
                                            "commit": fix[:7],
                                            "files_scored": ["app/guard.py"]}]}}  # fmt: skip
    units = resolve.resolve(tmp_path / "repos", gaps)
    to, ix = tmp_path / "work", tmp_path / "ix"
    trees.fetch_unit(to, tmp_path / "repos", "KG10", units["KG10"])
    q = "load the whole policy from the root path"
    rows = ask.ask(to, ix, "KG10", units["KG10"], [("KG10 1", q)], "found")
    stats = rows[-1]
    assert stats["changed_all"] == 2 and stats["changed"] == 1  # one passage of each
    served = {r["ranked_by"]: {s["path"] for s in r["served"]}
              for r in rows if r["type"] == "answer"}  # fmt: skip
    assert served["bm25"] == {"app/guard.py"}
    for by, paths in served.items():
        assert paths <= {"app/guard.py"}, by


def test_the_changed_set_is_limited_to_files_scored(tmp_path):
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to, ix = tmp_path / "work", tmp_path / "ix"
    for u in ("KG01", "KG10"):  # the same fix; KG10 scores app/guard.py only
        trees.fetch_unit(to, repos, u, units[u])
    q = "assert true load the whole policy from the root path"
    whole = ask.ask(to, ix, "KG01", units["KG01"], [("KG01 1", q)], "found")
    limited = ask.ask(to, ix, "KG10", units["KG10"], [("KG10 1", q)], "found")
    paths = {s["path"] for r in whole if r["type"] == "answer" for s in r["served"]}
    assert "tests/t.py" in paths  # unlimited, the unscored file's passage is served
    for r in limited:
        if r["type"] == "answer":
            assert {s["path"] for s in r["served"]} <= {"app/guard.py"}, r["ranked_by"]
    s_all, s_lim = whole[-1], limited[-1]
    assert s_lim["changed_all"] == s_all["changed"] > s_lim["changed"] >= 1
    assert s_lim["hit_passages"] == s_all["hit_passages"]  # hits are all in the file
    assert s_lim["file_passages"] == s_lim["changed"]  # phase 2's file level, too
    before = ask.ask(to, ix, "KG10", units["KG10"], [("KG10 1", q)], "before")[-1]
    assert before["file_passages"] == 1  # only app/guard.py of the whole tree


def test_lines_are_counted_the_way_git_counts_them():
    # a context line holding U+2028 and then a "-": splitlines() would see a
    # second line, read as a removal, and shift the real removal by one
    d = (
        "diff --git a/q.py b/q.py\n--- a/q.py\n+++ b/q.py\n@@ -4,4 +4,3 @@\n"
        " context with a -dash starts the second half\n"
        " first plain line of context\n"
        "-removed line number six here\n"
        " last plain context line\n"
    )
    fix = score.changed(d)
    assert fix["pos"] == {"q.py": {6}} and fix["hunks"] == {"q.py": [(4, 7)]}
    # a passage's rows are joined by newlines: a form feed inside a row is not a line
    p = {"path": "q.py", "line": 10, "text": "one\x0ctwo\nthree"}
    assert list(score.span(p)) == [10, 11]


def test_the_characters_that_shift_the_kernels_lines():
    for ch in "\v\f\x1c\x1d\x1e\x85  \r":
        assert score.shifted(f"a{ch}b\n"), repr(ch)
    assert not score.shifted("a\r\nb\r\n") and not score.shifted("plain\n\ttext\n")


def test_a_file_the_kernel_counts_differently_gets_no_positions(tmp_path, capsys):
    """A form feed before a removed line: the kernel's passage lines are one
    ahead of git's. The file is reported unreachable and never a hit; a clean
    file in the same fix is a hit at git's own line numbers."""
    ask = trees.sibling("ask")
    resolve = trees.sibling("resolve")
    repo = tmp_path / "repos" / "ff-repo"
    (repo / "app").mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    page = "def check(user, path):\n    # a page break \x0c in a comment\n"
    old = page + "    allowed = load_the_whole_policy(root_path)\n    return allowed\n"
    new = (
        page
        + "    allowed = load_the_whole_policy(user.repo_path)\n    return allowed\n"
    )
    (repo / "app" / "guard.py").write_bytes(old.encode())
    (repo / "app" / "ok.py").write_text(OLD_GUARD)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_page.py").write_bytes(b"# \x0c in a test file\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "first", date="2026-01-01T12:00:00+00:00")
    (repo / "app" / "guard.py").write_bytes(new.encode())
    (repo / "app" / "ok.py").write_text(NEW_GUARD)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "fix", date="2026-01-02T12:00:00+00:00")
    fix = git(repo, "rev-parse", "HEAD")
    gaps = {"KG01": {"id": "KG01", "fix": [{"repo": "ff-repo", "kind": "commit",
                                            "commit": fix[:7]}]}}  # fmt: skip
    units = resolve.resolve(tmp_path / "repos", gaps)
    to = tmp_path / "work"
    trees.fetch_unit(to, tmp_path / "repos", "KG01", units["KG01"])
    old_tree = to / "trees" / "KG01" / "old"
    # counted files only: the test file's form feed is not reported
    assert trees.unreachable_files(old_tree) == ["app/guard.py"]
    capsys.readouterr()
    assert trees.check(to, units) == 0  # informational: the exit code is unchanged
    assert "unreachable   KG01 app/guard.py" in capsys.readouterr().out
    diff = (to / "fixes" / "KG01.diff").read_text()
    fixed = score.changed(diff, old_tree)
    assert fixed["unreachable"] == ["app/guard.py"]
    assert "app/guard.py" not in fixed["pos"] and fixed["pos"]["app/ok.py"] == {2, 3}
    # without the tree to look at, git's own lines (3 and 4) are all we have
    assert score.changed(diff)["pos"]["app/guard.py"] == {3, 4}
    rows = ask.ask(
        to, tmp_path / "ix", "KG01", units["KG01"],
        [("KG01 1", "load the whole policy from the root path")], "found",
    )  # fmt: skip
    assert rows[-1]["unreachable_files"] == ["app/guard.py"]
    answers = [r for r in rows if r["type"] == "answer" and r["ranked_by"] == "bm25"]
    served = answers[0]["served"]
    assert {s["path"] for s in served} == {"app/guard.py", "app/ok.py"}
    scored = score.score(answers, to / "fixes")[0]
    by_path = {s["path"]: c for s, c in zip(served, scored["served"])}
    assert by_path == {"app/guard.py": "file", "app/ok.py": "hit"}
    assert scored["ranges"] == ["app/ok.py:2-3"]
    # and the passage of the shifted file really is one line ahead of git's
    guard = next(s for s in served if s["path"] == "app/guard.py")
    assert guard["text"].split("\n")[3].strip().startswith("allowed")  # kernel line 4
    assert old.split("\n")[2].strip().startswith("allowed")  # git line 3


def test_the_scored_files_cache_is_checked_and_written_whole(tmp_path):
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to, ix = tmp_path / "work", tmp_path / "ix"
    trees.fetch_unit(to, repos, "KG10", units["KG10"])
    pin = units["KG10"]
    qs = [("KG10 1", "load the whole policy from the root path")]
    first = ask.ask(to, ix, "KG10", pin, qs, "found")
    src, at = ask.limited_paths(ix, pin["vulnerable"]["tree"], ["app/guard.py"])
    good = (src / "app" / "guard.py").read_bytes()
    assert good == OLD_GUARD.encode() and (at / "index.json").exists()
    assert ask.ask(to, ix, "KG10", pin, qs, "found") == first  # a good cache is reused
    # a crash part-way: a truncated copy, a stray file, a leftover temporary
    # folder, and no index (it was never finished)
    (src / "app" / "guard.py").write_bytes(good[:10])
    (src / "stray.py").write_text("stray")
    shutil.rmtree(at)
    (ix / ".tmp-src-dead").mkdir()
    again = ask.ask(to, ix, "KG10", pin, qs, "found")
    assert again == first  # not the answers of a truncated file
    assert (src / "app" / "guard.py").read_bytes() == good
    assert not (src / "stray.py").exists()
    assert not [
        p
        for p in ix.iterdir()
        if p.name.startswith(".tmp-src-") and p.name != ".tmp-src-dead"
    ]
    # a tree that is not the pinned one is refused, whatever the cache holds
    (to / "trees" / "KG10" / "old" / "app" / "guard.py").write_text("tampered\n")
    with pytest.raises(ValueError, match="pinned tree"):
        ask.ask(to, ix, "KG10", pin, qs, "found")


def test_an_index_planted_under_the_pinned_name_is_never_used(tmp_path):
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to, ix = tmp_path / "work", tmp_path / "ix"
    trees.fetch_unit(to, repos, "KG01", units["KG01"])
    pin = units["KG01"]
    qs = [("KG01 1", "load the whole policy from the root path"), ("null 1", "policy")]
    runs = {m: ask.ask(to, ix, "KG01", pin, qs, m) for m in ("found", "before")}
    other = tmp_path / "other"
    other.mkdir()
    (other / "z.py").write_text("load the whole policy from the root path, planted\n")
    for mode in ("found", "before"):
        for tree in (pin["vulnerable"]["tree"], pin["fixed"]["tree"]):
            shutil.rmtree(ix / tree, ignore_errors=True)
            ask.scan.build(other, ix / tree)  # a whole, valid index of another folder
        assert ask.ask(to, ix, "KG01", pin, qs, mode) == runs[mode], mode
    again = ask.ask(to, ix, "KG01", pin, qs, "found")
    paths = {s["path"] for r in again if r["type"] == "answer" for s in r["served"]}
    assert "z.py" not in paths


def test_a_tree_that_is_not_its_pin_is_refused_and_the_stats_name_what_was_asked(
    tmp_path,
):
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to, ix = tmp_path / "work", tmp_path / "ix"
    for u in ("KG01", "KG10"):
        trees.fetch_unit(to, repos, u, units[u])
    qs = [("KG01 1", "load the whole policy from the root path")]
    pin = units["KG01"]
    found = ask.ask(to, ix, "KG01", pin, qs, "found")[-1]
    before = ask.ask(to, ix, "KG01", pin, qs, "before")[-1]
    assert found["old_tree"] == pin["vulnerable"]["tree"]
    assert found["new_tree"] == pin["fixed"]["tree"]
    assert found["old_index_sha256"] == ask.index_hash(ix / pin["vulnerable"]["tree"])
    assert found["new_index_sha256"] == ask.index_hash(ix / pin["fixed"]["tree"])
    assert found["old_index_sha256"] != found["new_index_sha256"]
    assert found["limited_index_sha256"] is None
    assert (
        before["new_index_sha256"] is None and before["old_tree"] == found["old_tree"]
    )
    assert before["old_index_sha256"] == found["old_index_sha256"]  # rebuilt, the same
    qs10 = [("KG10 1", "load the whole policy from the root path")]
    lim = ask.ask(to, ix, "KG10", units["KG10"], qs10, "found")[-1]
    _, at = ask.limited_paths(ix, units["KG10"]["vulnerable"]["tree"], ["app/guard.py"])
    assert lim["limited_index_sha256"] == ask.index_hash(at)
    # a tree that differs from its pin, on either side, in either phase
    for side in ("old", "new"):
        f = to / "trees" / "KG01" / side / "app" / "guard.py"
        good = f.read_bytes()
        f.write_text("tampered\n")
        for mode in ("found", "before"):
            with pytest.raises(ValueError, match="pinned tree"):
                ask.ask(to, ix, "KG01", pin, qs, mode)
        f.write_bytes(good)
    assert ask.ask(to, ix, "KG01", pin, qs, "found")[-1] == found  # and then it's fine
    # and one that isn't there at all
    shutil.rmtree(to / "trees" / "KG01" / "new")
    for mode in ("found", "before"):
        with pytest.raises(ValueError, match="missing"):
            ask.ask(to, ix, "KG01", pin, qs, mode)


def test_a_scored_files_cache_with_an_extra_file_is_rebuilt(tmp_path, monkeypatch):
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to, ix = tmp_path / "work", tmp_path / "ix"
    trees.fetch_unit(to, repos, "KG10", units["KG10"])
    pin = units["KG10"]
    qs = [("KG10 1", "load the whole policy from the root path")]
    first = ask.ask(to, ix, "KG10", pin, qs, "found")
    src, _ = ask.limited_paths(ix, pin["vulnerable"]["tree"], ["app/guard.py"])
    extra = src / "docs" / "extra.py"
    extra.parent.mkdir()
    extra.write_text(
        "load the whole policy from the root path, in a file nobody scored\n"
    )
    again = ask.ask(to, ix, "KG10", pin, qs, "found")
    assert again == first and not extra.exists()  # rebuilt without it
    for r in again:
        if r["type"] == "answer":
            for s in r["served"]:
                assert s["path"] == "app/guard.py" and "nobody" not in s["text"]
    # the copy is written whole, then renamed into place
    renames = []
    real = os.rename

    def spy(a, b):
        renames.append((Path(a).name, Path(b).name,
                        sorted(p.name for p in Path(a).rglob("*") if p.is_file())))  # fmt: skip
        real(a, b)

    monkeypatch.setattr(ask.os, "rename", spy)
    (src / "app" / "guard.py").write_bytes(b"x")
    assert ask.ask(to, ix, "KG10", pin, qs, "found") == first
    into_src = [r for r in renames if r[1] == src.name]
    assert into_src and into_src[0][0].startswith(".tmp-src-")
    assert into_src[0][2] == ["guard.py"]  # complete when it appeared


def test_a_missing_tree_is_refused_not_skipped(tmp_path, capsys):
    ask = trees.sibling("ask")
    run = trees.sibling("run")
    repos, units, _ = pinned(tmp_path)
    to, ix = tmp_path / "work", tmp_path / "ix"
    trees.fetch_unit(to, repos, "KG01", units["KG01"])
    qs = [("KG01 1", "load the whole policy from the root path")]
    rows = ask.ask(to, ix, "KG01", units["KG01"], qs, "found")
    answers = [r for r in rows if r["type"] == "answer"]
    # the diffs alone, with no trees beside them
    bare = tmp_path / "bare"
    (bare / "fixes").mkdir(parents=True)
    shutil.copy(to / "fixes" / "KG01.diff", bare / "fixes" / "KG01.diff")
    with pytest.raises(ValueError, match="missing"):
        score.score(answers, bare / "fixes")
    with pytest.raises(ValueError, match="missing"):
        score.changed(
            (to / "fixes" / "KG01.diff").read_text(), bare / "trees" / "KG01" / "old"
        )
    f = tmp_path / "answers.jsonl"
    f.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    box = tmp_path / "box"
    code = run.main(["found", "--to", str(bare), "--answers", str(f), "--box", str(box),
                     "--out", str(tmp_path / "o.jsonl")])  # fmt: skip
    assert code == 2 and not (box / "record.jsonl").exists()
    assert "missing" in capsys.readouterr().err
    assert score.main(["--to", str(bare), str(f)]) == 2
    # a tree that lacks a file the fix changed is not the pinned tree either
    (to / "trees" / "KG01" / "old" / "app" / "guard.py").unlink()
    with pytest.raises(ValueError, match="not in"):
        score.score(answers, to / "fixes")


def test_run_refuses_what_is_not_built(capsys):
    run = trees.sibling("run")
    assert run.main(["spread"]) == 2 and run.main([]) == 2
    assert run.main(["found"]) == 2


def test_run_refuses_answers_made_in_the_other_mode(tmp_path, capsys, monkeypatch):
    run = trees.sibling("run")
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to = tmp_path / "work"
    trees.fetch_unit(to, repos, "KG01", units["KG01"])
    qs = [
        ("KG01 1", "load the whole policy from the root path"),
        ("null 1", "qqqq zzzz"),
    ]
    monkeypatch.setattr(
        trees, "load_gaps", lambda: {"KG01": {"source_kind": "gap_record"}}
    )
    files = {}
    for mode in ("found", "before"):
        rows = ask.ask(to, tmp_path / "ix", "KG01", units["KG01"], qs, mode)
        files[mode] = tmp_path / f"{mode}.jsonl"
        files[mode].write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
        )
    both = tmp_path / "both.jsonl"
    both.write_text(files["found"].read_text() + files["before"].read_text())
    capsys.readouterr()
    for cmd, answers in (("before", files["found"]), ("found", files["before"]),
                         ("found", both), ("before", both)):  # fmt: skip
        box = tmp_path / f"box-{cmd}-{answers.stem}"
        code = run.main([cmd, "--to", str(to), "--answers", str(answers), "--box",
                         str(box), "--out", str(tmp_path / "o.jsonl")])  # fmt: skip
        assert code == 2, (cmd, answers.name)
        assert "not asked in mode" in capsys.readouterr().err
        assert not (box / "record.jsonl").exists()  # no verdict was written
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    assert run.main(["found", "--to", str(to), "--answers", str(empty), "--box",
                     str(tmp_path / "box-e"), "--out", str(tmp_path / "o.jsonl")]) == 2  # fmt: skip


def test_run_end_to_end_on_a_fixture(tmp_path, capsys, monkeypatch):
    run = trees.sibling("run")
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to = tmp_path / "work"
    trees.fetch_unit(to, repos, "KG01", units["KG01"])
    qs = [
        ("KG01 1", "load the whole policy from the root path"),
        ("null 1", "qqqq zzzz"),
    ]
    answers = tmp_path / "answers.jsonl"
    answers.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in
                               ask.ask(to, tmp_path / "ix", "KG01", units["KG01"], qs, "found")))  # fmt: skip
    scored, box = tmp_path / "scored.jsonl", tmp_path / "box"
    monkeypatch.setattr(
        trees, "load_gaps", lambda: {"KG01": {"source_kind": "gap_record"}}
    )
    code = run.main(["found", "--to", str(to), "--answers", str(answers), "--box", str(box),
                     "--out", str(scored)])  # fmt: skip
    assert code == 42  # no weaker-group answers, so that rule fails
    verdicts = [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]
    text = json.dumps(verdicts)
    assert "phase1:rank, bm25, strong" in text and "phase1:rank, bm25, weaker" in text
    assert "phase1:null" not in text  # phase 1 has no null gate
    assert text.count('"verdict"') >= 2 and "failing" in text
    assert any(json.loads(x)["best"] == "hit" for x in scored.read_text().splitlines())
    assert "null_answers" not in json.loads(capsys.readouterr().out)


QDIR = HERE / "questions"
flag = trees.sibling("flag")


def test_the_flag_counts_are_the_ones_the_rule_was_fixed_on():
    sets = {
        w: [q for n in range(1, 13) for q in flag.read(QDIR / w / f"KG{n:02d}.txt")]
        for w in flag.WRITERS
    }
    sets["null"] = flag.read(QDIR / "null" / "null.txt")
    count = {w: (len(qs), sum(flag.flagged(q, False) for q in qs),
                 sum(flag.flagged(q) for q in qs)) for w, qs in sets.items()}  # fmt: skip
    # (questions, flagged before the allow_localhost exception, flagged after it)
    assert count["claude"] == (96, 1, 0)
    assert count["null"] == (50, 0, 0)
    # the local writer's 48 of 96; the exception takes 2 more of its lines out
    assert count["local"] == (96, 48, 46)


def test_the_flag_rule_on_hand_made_lines():
    for line in ("Why does the cleanup_task fail?", "Where is a.b set?", "Does run() end?",
                 "Is camelCase flagged?", "Look in a/b please", "At line:12 it stops",
                 "See issue #12", "What is abcdef1 here?",
                 "How does allow_localhost use /tmp?"):  # fmt: skip
        assert flag.flagged(line), line
    for line in ("Why do I see dead workers in fleet health?",
                 "Does allow_localhost give a task the internet?"):  # fmt: skip
        assert not flag.flagged(line), line  # allow_localhost is a flag a user types
    assert flag.flagged(
        "Does allow_localhost give a task the internet?", exception=False
    )


def test_the_questions_hold_no_home_path_gap_id_or_key():
    import re

    spec = importlib.util.spec_from_file_location(
        "tr", trees.ROOT / "adapters/stdlib/transcript-redact/transcript_redact.py"
    )
    tr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tr)
    known = set(re.findall(r"\b[0-9a-f]{12}\b", (HERE / "gaps.json").read_text()))
    files = sorted(p for p in QDIR.rglob("*") if p.is_file())
    # two writers' gaps, the null set, inputs.md, and two writers' seven cpython units
    assert len(files) == 12 + 12 + 1 + 1 + 7 + 7
    for p in files:
        for line in p.read_text(encoding="utf-8").splitlines():
            assert tr.redact(line) == (line, []), (p.name, line)
            assert "/home/" not in line and "/Users/" not in line, (p.name, line)
            assert "[REDACTED" not in line, (p.name, line)
            for gid in re.findall(r"\b[0-9a-f]{12}\b", line):
                assert gid in known, (p.name, gid)  # only a gap id gaps.json holds


def test_every_questions_file_is_listed_in_the_freeze():
    if not FROZEN_FILE.exists():
        pytest.skip("not frozen yet")
    frozen = json.loads(FROZEN_FILE.read_text(encoding="utf-8"))["files"]
    on_disk = {p.relative_to(HERE).as_posix() for p in QDIR.rglob("*") if p.is_file()}
    assert len(on_disk) == 26 + 14 and on_disk <= set(frozen)
    assert "flag.py" in frozen
    for rel in on_disk:  # byte for byte as frozen (the freeze test holds it too)
        assert hashlib.sha256((HERE / rel).read_bytes()).hexdigest() == frozen[rel], rel


def test_questions_are_read_per_writer_with_headers_skipped(tmp_path):
    ask = trees.sibling("ask")
    files = {
        "local": [
            "# writer: local",
            "# source: x",
            "First local one?",
            "",
            "Second local_one?",
        ],
        "claude": ["# writer: claude", "A claude one?"],
        "null": ["# writer: null", "How is the weather?"],
    }
    for w, lines in files.items():
        (tmp_path / w).mkdir()
        name = "null.txt" if w == "null" else "KG01.txt"
        (tmp_path / w / name).write_text("\n".join(lines) + "\n")
    got = ask.load_questions(tmp_path, "KG01", "before")
    assert got == [("KG01 local 1", "First local one?", "local"),
                   ("KG01 local 2", "Second local_one?", "local"),
                   ("KG01 claude 1", "A claude one?", "claude"),
                   ("null 1", "How is the weather?", "null")]  # fmt: skip
    found = [g[0] for g in ask.load_questions(tmp_path, "KG01", "found")]
    assert found == ["KG01 local 1", "KG01 local 2", "KG01 claude 1"]  # no nulls
    (tmp_path / "claude" / "KG01.txt").unlink()
    with pytest.raises(OSError):  # a missing file is never an empty set
        ask.load_questions(tmp_path, "KG01", "found")
    # a file of name<TAB>question lines still works (the dry run's form)
    f = tmp_path / "q.txt"
    f.write_text("KG01 1\tqqqq zzzz\n")
    assert ask.load_questions(f, "KG01", "found") == [("KG01 1", "qqqq zzzz")]


def test_answer_rows_name_their_writer_and_whether_the_line_is_flagged(tmp_path):
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to, ix = tmp_path / "work", tmp_path / "ix"
    trees.fetch_unit(to, repos, "KG01", units["KG01"])
    qs = [("KG01 local 1", "How does load_the_whole_policy get its root path?", "local"),
          ("KG01 claude 1", "How does the whole policy get its root path?", "claude"),
          ("null 1", "How is the weather?", "null")]  # fmt: skip
    rows = ask.ask(to, ix, "KG01", units["KG01"], qs, "before")
    got = {
        r["question"]: (r["writer"], r["flagged"])
        for r in rows
        if r["type"] == "answer"
    }
    assert got == {"KG01 local 1": ("local", True), "KG01 claude 1": ("claude", False),
                   "null 1": ("null", False)}  # fmt: skip
    found = ask.ask(to, ix, "KG01", units["KG01"], qs, "found")
    assert {r["writer"] for r in found if r["type"] == "answer"} == {"local", "claude"}
    scored = score.score([r for r in found if r["type"] == "answer"], to / "fixes")
    assert {(r["writer"], r["flagged"]) for r in scored} == {
        ("local", True),
        ("claude", False),
    }


def test_phase_4_tallies_hits_per_writer_twice_and_the_gates_pool_both():
    run = trees.sibling("run")
    stats = [{"type": "stats", "unit": u, "gap": u, "changed": 10, "hit_passages": 2,
              "file_passages": 4, "random_rate": 0.5} for u in ("KG01", "KG09")]  # fmt: skip
    group = {"KG01": "strong", "KG09": "weaker"}
    ten = ["miss"] * 10

    def row(gap, writer, flagged, first, q):
        served = ten[: first - 1] + ["hit"] + ten[first:] if first else ten[:]
        return {**scored_row(gap, gap, "bm25", served, first, q),
                "writer": writer, "flagged": flagged}  # fmt: skip

    rows = [row("KG01", "local", True, 1, "a"), row("KG01", "local", False, 2, "b"),
            row("KG01", "local", False, None, "c"), row("KG01", "claude", False, 1, "d"),
            row("KG01", "claude", False, 5, "e"), row("KG09", "claude", True, 2, "f")]  # fmt: skip
    out = run.judge(stats, rows, group)
    # phase 1: a hit is one in the top 3
    assert out["writers"]["bm25, local"] == {"all": {"of": 3, "hits": 2},
                                              "unflagged": {"of": 2, "hits": 1}}  # fmt: skip
    assert out["writers"]["bm25, claude"] == {"all": {"of": 3, "hits": 2},
                                               "unflagged": {"of": 2, "hits": 1}}  # fmt: skip
    # phase 2: a hit anywhere in the top 10
    out2 = run.judge_before(stats, rows, group)["writers"]
    assert out2["bm25, claude"] == {"all": {"of": 3, "hits": 3},
                                    "unflagged": {"of": 2, "hits": 2}}  # fmt: skip
    assert out2["bm25, local"] == {"all": {"of": 3, "hits": 2},
                                   "unflagged": {"of": 2, "hits": 1}}  # fmt: skip
    # the gates pool both writers' lines, flagged or not, as one set
    assert out["rank"]["bm25, strong"]["pairs"] == 5
    assert out["rank"]["bm25, weaker"]["pairs"] == 1
    # rows from a file of plain questions (no writer) are left out of the tally
    plain = [scored_row("KG01", "KG01", "bm25", ten, None)]
    assert run.judge(stats, plain, group)["writers"] == {}


def test_phase_2_end_to_end_on_a_fixture(tmp_path, capsys, monkeypatch):
    run = trees.sibling("run")
    ask = trees.sibling("ask")
    repos, units, _ = pinned(tmp_path)
    to = tmp_path / "work"
    trees.fetch_unit(to, repos, "KG01", units["KG01"])
    qs = [
        ("KG01 1", "load the whole policy from the root path"),
        ("null 1", "qqqq zzzz"),
    ]
    rows = ask.ask(to, tmp_path / "ix", "KG01", units["KG01"], qs, "before")
    answers = tmp_path / "answers.jsonl"
    answers.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    monkeypatch.setattr(
        trees, "load_gaps", lambda: {"KG01": {"source_kind": "gap_record"}}
    )
    box, scored = tmp_path / "box", tmp_path / "scored.jsonl"
    code = run.main(["before", "--to", str(to), "--answers", str(answers), "--box",
                     str(box), "--out", str(scored)])  # fmt: skip
    assert code == 42  # two passages of three in a file the fix changed: not rare
    text = (box / "record.jsonl").read_text()
    assert "phase2:line level above chance, bm25, strong" in text
    assert "phase2:line level above chance, bm25, weaker" in text
    assert "phase2:null questions not above chance, bm25" in text
    out = json.loads(capsys.readouterr().out)
    assert out["table"]["bm25, strong"]["file_hits@10"] == 1


# -- phase 6, outside: cpython as the control --------------------------------


def make_cpython(tmp: Path) -> tuple:
    """(repos, draft, advisory rows): a repository `cpython` with seven fixes,
    each a commit naming its CVE, in the shape the desk's draft has."""
    repo = tmp / "repos" / "cpython"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    (repo / "Lib").mkdir()
    for n in range(1, 8):
        (repo / "Lib" / f"mod{n}.py").write_text(
            f"def old{n}(value):\n    return value + {n}\n    # alpha{n} beta{n} gamma{n}\n"
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base", date="2026-01-01T12:00:00+00:00")
    units, rows = [], []
    for n in range(1, 8):
        parent = git(repo, "rev-parse", "HEAD")
        (repo / "Lib" / f"mod{n}.py").write_text(
            f"def old{n}(value):\n    return check{n}(value) + {n}\n    # delta{n} epsilon{n} zeta{n}\n"
        )
        git(repo, "add", "-A")
        cve = f"CVE-2026-100{n}"
        git(repo, "commit", "-qm", f"fix parsing {n} ({cve})",
            date=f"2026-01-{n + 1:02d}T12:00:00+00:00")  # fmt: skip
        fix = git(repo, "rev-parse", "HEAD")
        weaker = n in (5, 6)
        units.append({"id": f"CP{n}", "cve": cve, "fix": fix[:11], "vulnerable": parent[:11],
                      "tree_old": git(repo, "rev-parse", parent + "^{tree}")[:12],
                      "tree_new": git(repo, "rev-parse", fix + "^{tree}")[:12],
                      "code_files": 1, "weight": "weaker" if weaker else "strong",
                      **({"why_weaker": "the advisory is another project's"} if weaker else {})})  # fmt: skip
        rows.append({"id": cve, "address": f"https://api.osv.dev/v1/vulns/{cve}",
                     "fetched_at": "2026-10-28T20:27Z", "osv_modified": "2026-10-28T02:30:39Z",
                     "summary": None if n == 1 else f"Planted title number {n} of the fixture",
                     "details": f"Planted details sentence number {n} of the fixture. Then more.",
                     "osv_fix_commits_main": [fix[:11]]})  # fmt: skip
    return tmp / "repos", {"units": units}, rows


def cpython_units(tmp: Path) -> tuple:
    outside = trees.sibling("outside")
    repos, draft, rows = make_cpython(tmp)
    return repos, outside.resolve(repos, draft, rows), draft, rows


def test_outside_pins_each_unit_from_git_and_keeps_no_advisory_text(tmp_path):
    outside = trees.sibling("outside")
    repos, doc, draft, rows = cpython_units(tmp_path)
    repo = repos / "cpython"
    outside.check_sources(doc)
    assert list(doc["units"]) == [f"CP{n}" for n in range(1, 8)]
    for name, u in doc["units"].items():
        fix = u["fixed"]["commit"]
        assert u["vulnerable"]["commit"] == git(
            repo, "rev-parse", fix + "^"
        )  # first parent
        assert u["vulnerable"]["tree"] == git(repo, "rev-parse", fix + "^^{tree}")
        assert u["fixed"]["tree"] == git(repo, "rev-parse", fix + "^{tree}")
        assert u["gap"] == name and u["counted_files"] == 1
        assert u["osv_address"] == "https://api.osv.dev/v1/vulns/" + u["cve"]
        diff = subprocess.run(["git", *trees.DIFF, u["vulnerable"]["commit"], fix], cwd=repo,
                              check=True, capture_output=True).stdout  # fmt: skip
        assert u["diff_sha256"] == hashlib.sha256(diff).hexdigest()
    row = rows[3]
    assert (
        doc["units"]["CP4"]["details_sha256"]
        == hashlib.sha256(row["details"].encode()).hexdigest()
    )
    assert (
        doc["units"]["CP4"]["summary_sha256"]
        == hashlib.sha256(row["summary"].encode()).hexdigest()
    )
    assert doc["units"]["CP1"]["summary_sha256"] is None  # an advisory with no summary
    text = json.dumps(doc)
    assert all(
        r["details"][:20] not in text and "Planted title" not in text for r in rows
    )


def test_outside_refuses_a_draft_that_git_does_not_bear_out(tmp_path):
    outside = trees.sibling("outside")
    repos, draft, rows = make_cpython(tmp_path)
    repo = repos / "cpython"

    def refused(change, row_change=None, match=""):
        d = {
            "units": [
                {**u, **(change if u["id"] == "CP3" else {})} for u in draft["units"]
            ]
        }
        rs = [
            {**r, **(row_change or {})} if r["id"] == "CVE-2026-1003" else r
            for r in rows
        ]
        with pytest.raises(ValueError, match=match):
            outside.resolve(repos, d, rs)

    fix = draft["units"][2]["fix"]
    grandparent = git(repo, "rev-parse", fix + "~2")[:11]
    refused({"vulnerable": grandparent}, match="first parent")  # the wrong parent
    refused({"tree_old": "0" * 12}, match="vulnerable tree")
    refused({"tree_new": "0" * 12}, match="fixed tree")
    refused({"cve": "CVE-2026-9999"}, match="no advisory row|advisory row")
    refused({}, {"osv_fix_commits_main": [draft["units"][3]["fix"]]}, match="OSV names")
    refused(
        {}, {"address": "https://api.osv.dev/v1/vulns/CVE-2026-1"}, match="advisory row"
    )
    refused({}, {"details_sha256": "0" * 64}, match="details hash")
    # a fix whose message does not name the CVE is tied to it by OSV, or refused
    (repo / "Lib" / "mod3.py").write_text(
        "def other():\n    return 3  # something else\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "an unrelated change")
    new = git(repo, "rev-parse", "HEAD")
    d3 = {**draft["units"][2], "fix": new[:11], "vulnerable": git(repo, "rev-parse", new + "^")[:11],
          "tree_old": git(repo, "rev-parse", new + "^^{tree}")[:12],
          "tree_new": git(repo, "rev-parse", new + "^{tree}")[:12]}  # fmt: skip
    with pytest.raises(ValueError, match="neither"):
        outside.resolve_unit(repo, d3, {**rows[2], "osv_fix_commits_main": []})
    assert outside.resolve_unit(
        repo, d3, {**rows[2], "osv_fix_commits_main": [new[:11]]}
    )


def test_outside_sources_file_is_whole_and_splits_five_and_two():
    outside = trees.sibling("outside")
    doc = json.loads(outside.SOURCES.read_text(encoding="utf-8"))
    outside.check_sources(doc)
    weights = {n: u["weight"] for n, u in doc["units"].items()}
    assert [n for n, w in weights.items() if w == "weaker"] == ["CP5", "CP6"]
    assert sum(w == "strong" for w in weights.values()) == 5
    for u in doc["units"].values():
        assert u["osv_address"].startswith("https://api.osv.dev/v1/vulns/CVE-")
        assert "summary" not in u and "details" not in u  # hashes only, never text
    # a swapped weight, a stray text field and a missing unit are each refused
    for bad in (lambda d: d["units"]["CP1"].update(weight="weaker"),
                lambda d: d["units"]["CP5"].update(weight="strong"),
                lambda d: d["units"]["CP2"].update(details="x"),
                lambda d: d["units"].pop("CP7")):  # fmt: skip
        d = json.loads(json.dumps(doc))
        bad(d)
        with pytest.raises(ValueError):
            outside.check_sources(d)


def first_sentence(text: str) -> str:
    text = " ".join(text.split())
    cut = re.search(r"(?<=[.!?]) ", text)
    return text[: cut.start()] if cut else text


def leaks(sentences: list, files: dict) -> list:
    """(sentence, file) for each sentence found in a file's text, whitespace
    folded."""
    folded = {f: " ".join(t.split()) for f, t in files.items()}
    return [(s, f) for s in sentences for f, t in folded.items() if s in t]


def tracked_texts() -> dict:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=trees.ROOT, check=True,
                         capture_output=True).stdout.decode().split("\0")  # fmt: skip
    files = {}
    for rel in filter(None, out):
        p = trees.ROOT / rel
        if p.is_file() and not p.is_symlink() and p.stat().st_size < 5_000_000:
            files[rel] = p.read_bytes().decode("utf-8", "ignore")
    return files


def test_the_leak_check_finds_a_planted_sentence():
    sentence = first_sentence(
        "Planted details sentence number 9 of\nthe fixture. Then more."
    )
    assert sentence == "Planted details sentence number 9 of the fixture."
    clean = {
        "a.md": "nothing here",
        "b.md": "Planted details sentence number 8 of the fixture.",
    }
    assert leaks([sentence], clean) == []
    dirty = {**clean, "c.md": "x Planted details sentence number 9\nof the fixture.  y"}
    assert leaks([sentence], dirty) == [(sentence, "c.md")]


#: the desk's private advisory rows, beside this worktree (KNOWN_GAPS_ADVISORIES
#: names another place, for a scratch worktree)
ADVISORIES = Path(
    os.environ.get("KNOWN_GAPS_ADVISORIES")
    or trees.ROOT.parent / "work" / "private" / "cpython" / "advisories.jsonl"
)


def test_no_advisory_text_is_in_the_branch():
    if not ADVISORIES.exists():
        pytest.skip(f"the advisory text is private and is not here ({ADVISORIES.name}): "
                    "nothing to check it against")  # fmt: skip
    rows = [
        json.loads(x)
        for x in ADVISORIES.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    sentences = [
        first_sentence(r[k]) for r in rows for k in ("summary", "details") if r.get(k)
    ]
    assert len(sentences) >= 7 and all(len(s) >= 20 for s in sentences)
    assert leaks(sentences, tracked_texts()) == []


def write_cpython_questions(qdir: Path) -> None:
    for w in ("local", "claude"):
        (qdir / "cpython" / w).mkdir(parents=True)
        for n in range(1, 8):
            (qdir / "cpython" / w / f"CP{n}.txt").write_text(
                f"# header {w}\nwhere does old{n} return value alpha{n} beta{n}\n"
                f"which function checks gamma{n} and delta{n}\n"
            )
    (qdir / "null").mkdir()
    (qdir / "null" / "null.txt").write_text("# null\nwhat is the weather like today\n")


def test_outside_runs_the_frozen_method_on_its_units(tmp_path, capsys):
    outside = trees.sibling("outside")
    repos, doc, draft, rows = cpython_units(tmp_path)
    units = doc["units"]
    to = tmp_path / "to"
    to.mkdir()
    for name, pin in units.items():
        trees.fetch_unit(to, repos, name, pin)
    assert trees.check(to, units) == 0
    qdir = tmp_path / "q"
    write_cpython_questions(qdir)
    frozen = {f"questions/{p.relative_to(qdir).as_posix()}": hashlib.sha256(p.read_bytes()).hexdigest()
              for p in qdir.rglob("*.txt")}  # fmt: skip
    qs = outside.unit_questions(qdir, "CP5", "before", frozen)
    assert [q[2] for q in qs] == ["local"] * 2 + ["claude"] * 2 + ["null"]
    assert [q[0] for q in qs][:2] == ["CP5 local 1", "CP5 local 2"]  # headers skipped
    assert [q[2] for q in outside.unit_questions(qdir, "CP5", "found", frozen)] == [
        "local"
    ] * 2 + ["claude"] * 2
    # a changed question file is not the frozen one
    edited = qdir / "cpython" / "local" / "CP5.txt"
    original = edited.read_text()
    edited.write_text("where does something else live\n")
    with pytest.raises(ValueError, match="not the file FROZEN.json holds"):
        outside.unit_questions(qdir, "CP5", "before", frozen)
    edited.write_text(original)
    assert len(outside.unit_questions(qdir, "CP5", "before", frozen)) == 5
    # each mode, every unit, then the judge: strong and weaker apart
    for mode in ("found", "before"):
        lines = []
        for name in units:
            for r in outside.ask_unit(to, tmp_path / "ix", name, mode, units,
                                      outside.unit_questions(qdir, name, mode, None)):  # fmt: skip
                lines.append(json.dumps(r, sort_keys=True))
        answers = tmp_path / f"{mode}.jsonl"
        answers.write_text("\n".join(lines) + "\n")
        capsys.readouterr()
        code = outside.judge(
            mode,
            to,
            answers,
            tmp_path / f"box-{mode}",
            tmp_path / f"scored-{mode}.jsonl",
            units,
        )
        assert code in (0, 42)
        out = json.loads(capsys.readouterr().out)
        if mode == "found":
            # 5 strong units and 2 weaker, 4 questions each, per ranker
            assert out["rank"]["bm25, strong"]["pairs"] == 5 * 4
            assert out["rank"]["bm25, weaker"]["pairs"] == 2 * 4
        else:
            assert out["table"]["bm25, strong"]["of"] == 5 * 4
            assert out["table"]["bm25, weaker"]["of"] == 2 * 4
            assert (
                out["table"]["bm25, null"]["of"] == 7
            )  # the null question, every unit
        record = (tmp_path / f"box-{mode}" / "record.jsonl").read_text()
        assert ("phase1:rank, bm25, weaker" if mode == "found"
                else "phase2:line level above chance, bm25, weaker") in record  # fmt: skip


def test_outside_parts_ask_every_question_once_under_its_own_name(tmp_path):
    outside = trees.sibling("outside")
    qs = [(f"CP1 local {n}", f"q{n}", "local") for n in range(1, 11)]
    for n in (1, 2, 3, 4, 7, 10, 11):
        parts = [outside.part_of(qs, f"{i}/{n}") for i in range(1, n + 1)]
        assert [q for p in parts for q in p] == qs  # joined: the list, in order, once
        assert max(map(len, parts)) - min(map(len, parts)) <= 1 or n > len(qs)
    for bad in ("0/3", "4/3", "3", "a/b", "1/0", ""):
        with pytest.raises(ValueError, match="not a part"):
            outside.part_of(qs, bad)
    # the same answers, asked whole or in parts
    repos, doc, draft, rows = cpython_units(tmp_path)
    units = doc["units"]
    to = tmp_path / "to"
    to.mkdir()
    trees.fetch_unit(to, repos, "CP2", units["CP2"])
    qdir = tmp_path / "q"
    write_cpython_questions(qdir)
    full = outside.unit_questions(qdir, "CP2", "before", None)
    whole = outside.ask_unit(to, tmp_path / "ix", "CP2", "before", units, full)
    joined = []
    for i in (1, 2, 3):
        joined += outside.ask_unit(to, tmp_path / "ix", "CP2", "before", units,
                                   outside.part_of(full, f"{i}/3"))  # fmt: skip

    def answers(rs):
        return sorted(
            json.dumps(r, sort_keys=True) for r in rs if r["type"] == "answer"
        )

    def stats(rs):  # the unit's own counts, but for how many questions this call asked
        return [{k: v for k, v in r.items() if k != "questions"}
                for r in rs if r["type"] == "stats"]  # fmt: skip

    assert answers(joined) == answers(whole) and len(answers(whole)) == 3 * len(full)
    assert all(s == stats(whole)[0] for s in stats(joined))


def test_outside_main_refuses_a_bad_command_line_and_missing_questions(
    capsys, tmp_path
):
    outside = trees.sibling("outside")
    assert outside.main([]) == 2
    assert outside.main(["ask", "--unit", "CP1"]) == 2
    assert outside.main(["fetch", "--to", str(tmp_path)]) == 2
    assert outside.main(["check", "--to", str(tmp_path), "--unit", "CP9"]) == 2
    capsys.readouterr()
    # the real command, with the frozen questions, refuses when the trees are not
    # there: nothing is asked and nothing is written
    code = outside.main(["ask", "--to", str(tmp_path), "--ix", str(tmp_path / "ix"),
                         "--unit", "CP1", "--mode", "before", "--out", str(tmp_path / "o")])  # fmt: skip
    assert code == 2 and "missing" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


def test_the_cpython_questions_are_frozen_eight_a_unit_a_writer():
    outside = trees.sibling("outside")
    frozen = json.loads(FROZEN_FILE.read_text(encoding="utf-8"))["files"]
    assert not (
        outside.QDIR / "cpython" / "inputs.md"
    ).exists()  # it holds advisory text
    flagged = {"local": 0, "claude": 0}
    for w in ("local", "claude"):
        for n in range(1, 8):
            rel = f"questions/cpython/{w}/CP{n}.txt"
            assert frozen[rel] == hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
            lines = flag.read(HERE / rel)
            assert len(lines) == 8, rel
            flagged[w] += sum(flag.flagged(q) for q in lines)
    assert flagged == {"local": 22, "claude": 1}  # counted when they were frozen
    for mode, extra in (("found", 0), ("before", 50)):
        qs = outside.unit_questions(outside.QDIR, "CP5", mode, frozen)
        assert len(qs) == 16 + extra


# -- phase 5, spread --------------------------------------------------------


def make_spread_repo(tmp: Path, name: str = "fixrepo") -> Path:
    repo = tmp / "repos" / name
    files = {
        "docs/a.md": "zebraword alpha notes thing\n",
        "docs/b.md": "quokkaword beta notes thing\n",
        "docs/c.md": "yakword gamma notes thing\n",
        "docs/d.md": "ibexword delta notes thing\n",
        "node_modules/pkg/e.md": "zebraword inside a vendored folder\n",
    }
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "fixture", date="2026-01-01T12:00:00+00:00")
    return repo


def spread_questions(tmp: Path, local: list, claude: list) -> Path:
    q = tmp / "q"
    for w, lines in (("local", local), ("claude", claude)):
        (q / w).mkdir(parents=True, exist_ok=True)
        (q / w / "KG01.txt").write_text("# header\n" + "\n".join(lines) + "\n")
    return q


def ask_about(word: str) -> str:
    return f"What about {word} please?"


def threshold_questions(tmp: Path) -> Path:
    """zebra: 2 local + 2 claude (4, both writers); quokka: 4 local (4, one
    writer); yak: 1 local + 2 claude (3); ibex: 1 local + 3 claude (4, one
    local, the least both writers allow)."""
    local = ([ask_about("zebraword")] * 2 + [ask_about("quokkaword")] * 4
             + [ask_about("yakword")] + [ask_about("ibexword")])  # fmt: skip
    claude = ([ask_about("zebraword")] * 2 + [ask_about("yakword")] * 2
              + [ask_about("ibexword")] * 3 + ["qqqq zzzz"] * 1)  # fmt: skip
    assert len(local) == len(claude) == 8
    return spread_questions(tmp, local, claude)


def test_a_candidate_needs_four_questions_and_both_writers(tmp_path):
    spread = trees.sibling("spread")
    repo = make_spread_repo(tmp_path)
    q = threshold_questions(tmp_path)
    rows, stats = spread.spread_repo(repo, ["KG01"], q, tmp_path / "ix" / "fixrepo", {})
    assert [(r["path"], r["questions"], r["writers"]) for r in rows] == [
        ("docs/a.md", 4, ["claude", "local"]),
        ("docs/d.md", 4, ["claude", "local"]),
    ]  # quokka reached 4 times by one writer, yak 3 times: neither is one
    assert all(r["best_rank"] == 1 and r["gap"] == "KG01" and r["repo"] == "fixrepo"
               for r in rows)  # fmt: skip
    assert all(len(r["sha256"]) == 64 and "text" not in r for r in rows)
    s = stats[0]
    assert (
        s["candidates"] == 2 and s["passages"] == 4 and s["reached_4_any_writer"] == 3
    )
    assert s["chance"] == 4.0 and s["at_or_below_chance"] is True
    assert s["skipped"] == [
        "node_modules"
    ]  # the vendored copy of zebraword is not asked
    assert (
        len(s["head"]) == 40 and len(s["tree"]) == 40 and len(s["index_sha256"]) == 64
    )


def test_the_top_ten_is_the_limit(tmp_path):
    spread = trees.sibling("spread")
    repo = tmp_path / "repos" / "crowd"
    for n in range(12):  # twelve passages hold the word; a question reaches ten
        (repo / f"f{n}.md").parent.mkdir(parents=True, exist_ok=True)
        (repo / f"f{n}.md").write_text(f"commonword number {n} here\n")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "crowd", date="2026-01-01T12:00:00+00:00")
    q = spread_questions(
        tmp_path, [ask_about("commonword")] * 8, [ask_about("commonword")] * 8
    )
    rows, stats = spread.spread_repo(repo, ["KG01"], q, tmp_path / "ix" / "crowd", {})
    assert len(rows) == 10 and {r["questions"] for r in rows} == {16}
    assert {r["best_rank"] for r in rows} == set(range(1, 11))
    assert stats[0]["passages"] == 12


def test_the_chance_is_exact(tmp_path):
    spread = trees.sibling("spread")

    def brute(n):  # every pattern of the 16 questions that reach a passage
        p = min(1, 10 / n)
        total = 0.0
        for pattern in range(1 << 16):
            k = bin(pattern).count("1")
            if k >= 4:
                total += p**k * (1 - p) ** (16 - k)
        return n * total

    for n in (5, 12, 40, 1000):
        assert spread.chance(n) == pytest.approx(brute(n), rel=1e-9), n
    assert spread.chance(5) == pytest.approx(5.0)  # ten reach every passage of five
    assert spread.chance(0) == 0.0
    assert 0 < spread.chance(1000) < 1  # a big tree: well under one passage by luck


def test_own_repo_is_marked_for_the_repository_the_fix_landed_in(tmp_path):
    spread = trees.sibling("spread")
    pins = trees.load_pins()
    assert spread.own_repo("KG01", "kartikeya", pins)
    assert not spread.own_repo("KG01", "willow-mcp", pins)
    assert spread.own_repo("KG03", "kartikeya", pins) and spread.own_repo(
        "KG03", "willow-mcp", pins
    )
    assert not spread.own_repo("KG08", "kartikeya", pins) and spread.own_repo(
        "KG08", "willow-bot", pins
    )
    repo = make_spread_repo(tmp_path)
    q = threshold_questions(tmp_path)
    fixture = {"KG01": {"gap": "KG01", "repo": "fixrepo"}}
    rows, stats = spread.spread_repo(
        repo, ["KG01"], q, tmp_path / "ix1" / "fixrepo", fixture
    )
    assert rows and all(r["own_repo"] for r in rows) and stats[0]["own_repo"] is True
    elsewhere = {"KG01": {"gap": "KG01", "repo": "somewhere-else"}}
    rows, stats = spread.spread_repo(
        repo, ["KG01"], q, tmp_path / "ix2" / "fixrepo", elsewhere
    )
    assert (
        rows and not any(r["own_repo"] for r in rows) and stats[0]["own_repo"] is False
    )


def spread_run(repo, root, *extra):
    """spread.main on the frozen questions, one private root."""
    spread = trees.sibling("spread")
    out = root / "candidates.jsonl"
    return spread.main(["--repo", str(repo), "--gap", "KG01", "--out", str(out),
                        "--private", str(root), *extra])  # fmt: skip


def test_findings_go_to_the_one_private_root_and_the_frozen_questions(tmp_path, capsys):
    spread = trees.sibling("spread")
    repo = make_spread_repo(tmp_path)
    root = tmp_path / "work" / "private"
    assert spread_run(repo, root) == 0
    stats = [json.loads(x) for x in (root / "stats.jsonl").read_text().splitlines()]
    assert len(stats) == 1 and stats[0]["question_count"] == 16
    frozen = json.loads(FROZEN_FILE.read_text())["files"]
    assert stats[0]["questions_sha256"] == {
        f"{w}/KG01.txt": frozen[f"questions/{w}/KG01.txt"] for w in ("local", "claude")
    }  # the files the freeze holds, named by hash
    assert stats[0]["symlinks_skipped"] == 0
    assert spread_run(repo, root) == 0  # appended, not rewritten
    assert len((root / "stats.jsonl").read_text().splitlines()) == 2
    # the default root is the one beside this worktree, never a path of the caller's
    assert spread.DEFAULT_ROOT == trees.ROOT.parent / "work" / "private"
    capsys.readouterr()
    assert spread.main([]) == 2 and spread.main(["--repo", str(repo)]) == 2
    code = spread.main(["--repo", str(repo), "--gap", "KG99", "--out", str(root / "c.jsonl"),
                        "--private", str(root)])  # fmt: skip
    assert code == 2


def test_every_output_lies_strictly_under_the_root_and_in_no_git_work_tree(
    tmp_path, capsys
):
    spread = trees.sibling("spread")
    repo = make_spread_repo(tmp_path)
    root = tmp_path / "work" / "private"
    assert spread_run(repo, root) == 0
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (root / "lnk").symlink_to(outside)  # a link under the root that leaves it
    other = make_spread_repo(tmp_path, "other")
    main_checkout = Path(subprocess.run(
        ["git", "rev-parse", "--git-common-dir"], cwd=trees.ROOT, capture_output=True,
        text=True, check=True).stdout.strip()).resolve().parent  # fmt: skip
    capsys.readouterr()
    base = ["--repo", str(repo), "--gap", "KG01", "--private", str(root)]
    bad_outs = [
        tmp_path / "candidates.jsonl",  # not under the root
        root,  # the root itself
        root / "lnk" / "c.jsonl",  # a link out of the root
        root / ".." / "c.jsonl",  # a dot-dot out of it
        trees.ROOT / "c.jsonl",  # inside this worktree
    ]
    for bad in bad_outs:
        assert spread.main([*base, "--out", str(bad)]) == 2, bad
        assert "refused" in capsys.readouterr().err
    for flag_ in ("--stats", "--ix"):  # each option is held to the same root
        for bad in (tmp_path / "x", root / "lnk" / "x", root):
            code = spread.main([*base, "--out", str(root / "c.jsonl"), flag_, str(bad)])
            assert code == 2, (flag_, bad)
    assert (
        not (outside / "c.jsonl").exists()
        and not (tmp_path / "candidates.jsonl").exists()
    )
    # a root inside a git work tree is refused, whatever its name: the scanned
    # repository's own work/private, another repository's, and the main checkout's
    for bad_root in (repo / "work" / "private", other / "work" / "private",
                     main_checkout / "work" / "private"):  # fmt: skip
        code = spread.main(["--repo", str(repo), "--gap", "KG01", "--private", str(bad_root),
                            "--out", str(bad_root / "c.jsonl")])  # fmt: skip
        assert code == 2, bad_root
        assert "git work tree" in capsys.readouterr().err
        assert not (bad_root / "c.jsonl").exists()
    assert not (repo / "work").exists() and not (other / "work").exists()


def test_the_git_environment_cannot_switch_off_the_work_tree_refusal(
    tmp_path, capsys, monkeypatch
):
    spread = trees.sibling("spread")
    repo = make_spread_repo(tmp_path)
    main_checkout = Path(subprocess.run(
        ["git", "rev-parse", "--git-common-dir"], cwd=trees.ROOT, capture_output=True,
        text=True, check=True).stdout.strip()).resolve().parent  # fmt: skip
    bare = tmp_path / "bare.git"
    git(tmp_path, "init", "-q", "--bare", str(bare))
    target = main_checkout / "work" / "private"
    assert spread.in_git_tree(target)  # the plain answer
    # GIT_DIR at a bare repository made `git rev-parse --show-toplevel` fail
    # everywhere, and a ceiling can hide the checkout: neither may matter
    monkeypatch.setenv("GIT_DIR", str(bare))
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(main_checkout))
    assert spread.in_git_tree(target)
    assert spread.in_git_tree(repo / "work" / "private")
    with pytest.raises(ValueError, match="git work tree"):
        spread.private_root(target)  # as the root
    fake_root = repo / "work" / "private"  # a root's output that is in a work tree
    with pytest.raises(ValueError, match="git work tree"):
        spread.under(fake_root, fake_root / "c.jsonl")  # as an output
    root = tmp_path / "work" / "private"
    capsys.readouterr()
    code = spread.main(["--repo", str(repo), "--gap", "KG01", "--private", str(target),
                        "--out", str(target / "c.jsonl")])  # fmt: skip
    assert code == 2 and "git work tree" in capsys.readouterr().err
    assert not (main_checkout / "work" / "private" / "c.jsonl").exists()
    # a run itself is unaffected by the variables, which it removes
    monkeypatch.setenv("GIT_DIR", str(bare))
    assert spread_run(repo, root) == 0
    assert "GIT_DIR" not in os.environ


def test_the_private_root_must_be_an_absolute_path(tmp_path, capsys, monkeypatch):
    spread = trees.sibling("spread")
    repo = make_spread_repo(tmp_path)
    work = tmp_path / "cwd"
    work.mkdir()
    monkeypatch.chdir(
        work
    )  # a folder in no git work tree: a relative root would work there
    capsys.readouterr()
    code = spread.main(["--repo", str(repo), "--gap", "KG01", "--private", "work/private",
                        "--out", str(work / "work" / "private" / "c.jsonl")])  # fmt: skip
    assert code == 2 and "absolute" in capsys.readouterr().err
    assert not (work / "work").exists()
    with pytest.raises(ValueError, match="absolute"):
        spread.private_root(Path("work/private"))


def test_the_stats_row_names_the_freeze_it_read(tmp_path):
    repo = make_spread_repo(tmp_path)
    root = tmp_path / "work" / "private"
    assert spread_run(repo, root) == 0
    stats = [json.loads(x) for x in (root / "stats.jsonl").read_text().splitlines()]
    assert (
        stats[0]["frozen_json_sha256"]
        == hashlib.sha256(FROZEN_FILE.read_bytes()).hexdigest()
    )


def test_a_repo_that_would_name_the_private_root_is_refused(
    tmp_path, capsys, monkeypatch
):
    spread = trees.sibling("spread")
    repo = make_spread_repo(tmp_path)
    root = tmp_path / "work" / "private"
    assert spread_run(repo, root) == 0
    (root / "keep.jsonl").write_text("keep\n")
    before = sorted(p.name for p in root.iterdir())
    capsys.readouterr()
    monkeypatch.chdir(tmp_path)
    for arg in (str(repo / "docs" / ".."),  # ends in ..: its name is ".."
                ".",  # an empty name
                "..",
                str(root),  # the private root
                str(root / "ix-spread"),  # inside it
                str(tmp_path / "work"),  # above it
                str(tmp_path)):  # fmt: skip
        assert spread_run(arg, root) == 2, arg
        assert "refused" in capsys.readouterr().err
    assert sorted(p.name for p in root.iterdir()) == before  # nothing was replaced
    assert (root / "keep.jsonl").read_text() == "keep\n"
    assert (root / "ix-spread").is_dir()
    # a repository spelt with a dot is only that repository, and is asked
    assert spread.repo_path(str(repo) + "/.", root) == repo.resolve()


def test_a_symlink_in_a_repository_is_never_followed(tmp_path):
    spread = trees.sibling("spread")
    secret = tmp_path / "secret.txt"
    secret.write_text("zebraword leaked from outside the repository\n")
    repo = make_spread_repo(tmp_path)
    (repo / "link.md").symlink_to(secret)  # a link to a file outside
    (repo / "linkdir").symlink_to(tmp_path / "repos")  # a link to a folder
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "links", date="2026-01-02T12:00:00+00:00")
    q = threshold_questions(tmp_path)
    ix = tmp_path / "work" / "private" / "ix" / "fixrepo"
    rows, stats = spread.spread_repo(repo, ["KG01"], q, ix, {})
    assert stats[0]["symlinks_skipped"] == 2 and stats[0]["passages"] == 4
    index = trees.sibling("ask").scan.Index(ix)
    assert not any("leaked" in c["text"] for c in index.pile)
    assert not any(c["path"].startswith("link") for c in index.pile)
    # the zebra passage was not made a second one by the link: still 4 questions
    assert [(r["path"], r["questions"]) for r in rows] == [
        ("docs/a.md", 4),
        ("docs/d.md", 4),
    ]


def test_the_question_set_is_the_frozen_one_or_nothing(tmp_path, capsys, monkeypatch):
    spread = trees.sibling("spread")
    repo = make_spread_repo(tmp_path)
    root = tmp_path / "work" / "private"
    # a copy of the questions with one word changed is refused, and nothing is written
    copy = tmp_path / "qcopy"
    shutil.copytree(spread.QDIR, copy)
    victim = copy / "local" / "KG01.txt"
    victim.write_text(
        victim.read_text() + "# edited\n"
    )  # a header line: same questions
    monkeypatch.setattr(spread, "QDIR", copy)
    capsys.readouterr()
    assert spread_run(repo, root) == 2
    assert "FROZEN.json" in capsys.readouterr().err
    assert not (root / "candidates.jsonl").exists()
    monkeypatch.undo()
    # there is no option to name another set
    assert spread.main(["--repo", str(repo), "--gap", "KG01", "--out", str(root / "c.jsonl"),
                        "--private", str(root), "--questions", str(tmp_path / "q")]) == 2  # fmt: skip
    # and the library refuses a gap whose questions are not 16, 8 a writer
    short = spread_questions(tmp_path / "short", ["one"] * 7, ["two"] * 8)
    with pytest.raises(ValueError, match="not 16"):
        spread.spread_repo(repo, ["KG01"], short, tmp_path / "ix" / "fixrepo", {})
    lopsided = spread_questions(tmp_path / "lop", ["one"] * 9, ["two"] * 7)
    with pytest.raises(ValueError, match="not 16"):
        spread.spread_repo(repo, ["KG01"], lopsided, tmp_path / "ix" / "fixrepo", {})


def test_an_unreachable_repository_is_listed_and_exits_42(tmp_path):
    root = tmp_path / "work" / "private"
    nothing = tmp_path / "repos" / "nothing"
    nothing.mkdir(parents=True)
    plain = tmp_path / "repos" / "plain"
    plain.mkdir()
    for repo in (nothing, plain, tmp_path / "repos" / "missing"):
        assert spread_run(repo, root) == 42, repo
    stats = [json.loads(x) for x in (root / "stats.jsonl").read_text().splitlines()]
    assert len(stats) == 3 and all(
        "unreachable" in s and "candidates" not in s for s in stats
    )
    assert (root / "candidates.jsonl").read_text() == ""


def test_the_vendored_folders_are_left_out():
    spread = trees.sibling("spread")
    assert spread.SKIP_DIRS == {".git", "node_modules", "vendor", "third_party", "venv",
                                ".venv", "target", "dist", "build"}  # fmt: skip
