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


def test_every_frozen_file_is_as_it_was_frozen():
    if not FROZEN_FILE.exists():
        pytest.skip("not frozen yet: FROZEN.json is the operator's freeze commit")
    frozen = json.loads(FROZEN_FILE.read_text(encoding="utf-8"))
    for rel, sha in frozen["files"].items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    assert {"gaps.json", "pins.json", "score.py", "trees.py", "resolve.py", "ask.py",
            "origin.py", "run.py"} <= set(frozen["files"])  # fmt: skip
    root = HERE.parents[1]
    for rel, sha in frozen["tools_at_freeze"].items():
        assert set(frozen["tools_at_freeze"]) == {
            "kernel.py",
            "adapters/stdlib/scan/scan.py",
            "adapters/stdlib/ci/whose.py",
        }
        assert (root / rel).exists(), rel  # the tools' hashes are held by the freeze


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
    hit = {"path": "app/guard.py", "line": 1}
    far = {**hit, "text": "far away context line one\nfar away context line two"}
    near = {**hit, "text": "x\nallowed = load_the_whole_policy(root_path)"}
    other = {**hit, "text": "something else entirely"}
    assert not score.hit(far, fix) and score.classify(far, fix) == "file"
    assert score.hit(near, fix) and score.classify(near, fix) == "hit"
    assert score.classify(other, fix) == "file"
    new_side = {**hit, "text": "verify_the_policy_signature(allowed)"}
    assert not score.hit(new_side, fix)  # a line the fix added is not in the old code
    assert score.classify(new_side, fix) == "file"
    assert score.classify({"path": "elsewhere.py", "line": 1, "text": near["text"]},
                          fix) == "miss"  # fmt: skip
    after = {**hit, "text": "    context at the very bottom"}
    assert score.hit(after, fix)  # the neighbour of an added run counts
    two_away = {**hit, "text": "context further down the file"}
    assert not score.hit(two_away, fix)  # a context line not next to an added run
    assert score.hit_lines(near, fix) == [2]
    assert score.ranges({**hit, "text": near["text"]}, fix) == ["app/guard.py:2-2"]
    assert trees.phase3.counts is score.PHP2SHELL_COUNTS  # put back after


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
    fix = {
        "old": {"a.py": {"aa bb cc one", "aa bb cc two", "aa bb cc three"}},
        "files": {"a.py"},
    }
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
    assert {r["gap"] for r in answers} == {
        "KG01",
        "null",
    }  # another gap's question isn't asked
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

    null = [scored_row("KG01", "null", "bm25", ten, None)]
    out = run.judge(stats, pairs(1) + null, group)
    assert out["passes"] == {"rank, bm25, strong": True, "rank, bm25, weaker": True,
                             "null questions hit nothing": True}  # fmt: skip
    assert out["draws"] == 100_000 and out["seed"] == run.SEED
    assert out["rank"]["bm25, strong"]["observed"] == 4.0
    assert out["top3_hit_rate"]["bm25, strong"]["hits"] == 4
    lost = run.judge(stats, pairs(None) + null, group)  # never returned: last
    assert not lost["passes"]["rank, bm25, strong"]
    assert lost["rank"]["bm25, strong"]["observed"] == pytest.approx(0.4)
    late = run.judge(stats, pairs(10) + null, group)
    assert (
        not late["passes"]["rank, bm25, weaker"]
        and late["passes"]["null questions hit nothing"]
    )
    leak = [scored_row("KG01", "null", "grep", ["miss", "hit"], 2)]
    assert not run.judge(stats, pairs(1) + leak, group)["passes"][
        "null questions hit nothing"
    ]
    deep = [scored_row("KG01", "null", "grep", ["miss"] * 3 + ["hit"], 4)]
    assert run.judge(stats, pairs(1) + deep, group)["passes"][
        "null questions hit nothing"
    ]
    assert not run.judge(stats, pairs(1), group)["passes"]["null questions hit nothing"]


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
    out = run.judge_before(stats, rows("KG01", hit) + rows("KG09", hit), group)
    assert out["passes"] == {"line level above chance, bm25, strong": True,
                             "line level above chance, bm25, weaker": True}  # fmt: skip
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


def test_run_refuses_what_is_not_built(capsys):
    run = trees.sibling("run")
    assert run.main(["spread"]) == 2 and run.main([]) == 2
    assert run.main(["found"]) == 2


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
    assert "phase1:null questions hit nothing" in text
    assert text.count('"verdict"') >= 3 and "failing" in text and "satisfied" in text
    assert any(json.loads(x)["best"] == "hit" for x in scored.read_text().splitlines())
    assert json.loads(capsys.readouterr().out)["null_answers"] == 3


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
    out = json.loads(capsys.readouterr().out)
    assert out["table"]["bm25, strong"]["file_hits@10"] == 1


def test_the_stubs_say_they_are_not_built(capsys):
    for name in ("spread", "outside"):
        mod = trees.sibling(name)
        assert mod.main([]) == 2
        assert "not in bite 2" in capsys.readouterr().err
