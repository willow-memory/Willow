"""flashcards: sealed approvals become cards; the schedule is FSRS-5 replayed
from the review rows, and `check` holds every row to it."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "flashcards.py"
D0 = "2026-11-01T09:00:00Z"
spec = importlib.util.spec_from_file_location("flashcards", SCRIPT)
fc = importlib.util.module_from_spec(spec)
sys.modules["flashcards"] = fc
spec.loader.exec_module(fc)


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *argv],
                          capture_output=True, text=True)  # fmt: skip


def run(box: Path, *argv: str, now: str | None = D0) -> subprocess.CompletedProcess:
    extra = ["--now", now] if now else []
    return subprocess.run([sys.executable, str(SCRIPT), "--box", str(box), *argv, *extra],
                          capture_output=True, text=True)  # fmt: skip


def make(
    tmp_path: Path, seal: bool = True, path: str = "sun-hours.md"
) -> tuple[Path, str]:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True, exist_ok=True)
    (pile / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater at the root.\n"
    )
    b = tmp_path / "box"
    k(
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        "--now",
        D0,
    )
    got = json.loads(k("bite", "--box", str(b), "--now", D0,
                       "how much sun do tomatoes want").stdout)  # fmt: skip
    row = {"path": path, "data": "Six hours.", "cites": [got["served"][0]["id"]],
           "claim": "garden.md"}  # fmt: skip
    (tmp_path / "rows.jsonl").write_text(json.dumps(row) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "rows.jsonl"), "--now", D0)
    subj = "proposal:" + hashlib.sha256(
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()  # fmt: skip
    if seal:
        assert k("seal", "--box", str(b), subj, "--now", D0).returncode == 0
    return b, subj


def rows(b: Path) -> list[dict]:
    return [json.loads(x) for x in (b / "record.jsonl").read_text().splitlines()]


def test_fsrs_numbers_are_the_published_ones():
    # first grade: stability is w[g-1], difficulty w4 - e^(w5(g-1)) + 1
    s, d = fc.step(None, 3, 0)
    assert s == 3.173
    assert abs(d - (7.1949 - 2.718281828 ** (0.5345 * 2) + 1)) < 1e-6
    assert fc.step(None, 1, 0)[0] == 0.40255 and fc.step(None, 4, 0)[0] == 15.69105
    assert fc.step(None, 1, 0)[1] == 7.1949 and fc.step(None, 4, 0)[1] < d < 7.1949
    assert [fc.interval(x) for x in (0.4, 3.173, 15.69105, 1e9)] == [1, 3, 16, 36500]
    # recall after the interval at 90% retention: stability grows for good, not for again
    s2, _ = fc.step((3.173, d), 3, 3)
    assert s2 > 3.173 * 2
    assert fc.step((3.173, d), 1, 3)[0] < 3.173
    assert (
        fc.step((3.173, d), 2, 3)[0]
        < fc.step((3.173, d), 3, 3)[0]
        < fc.step((3.173, d), 4, 3)[0]
    )
    # the same day uses the short-term formula
    assert (
        abs(fc.step((3.173, d), 3, 0)[0] - 3.173 * 2.718281828 ** (0.51655 * 0.6621))
        < 1e-6
    )


def test_a_card_comes_only_from_a_seal_and_a_new_one_is_due_now(tmp_path):
    b, subj = make(tmp_path, seal=False)
    got = run(b, "due")
    assert got.returncode == 42 and "0 cards; 0 due" in got.stdout
    b, subj = make(tmp_path / "s")
    got = run(b, "due")
    assert got.returncode == 0 and f"{subj[9:19]}  sun hours  new" in got.stdout
    assert "1 cards; 1 due" in got.stdout
    assert "Six hours." in run(b, "show", subj[9:19]).stdout


def test_reviewing_writes_one_row_and_moves_the_card(tmp_path):
    b, subj = make(tmp_path)
    n = len(rows(b))
    got = run(b, "review", subj[9:19], "good")
    assert got.returncode == 0 and "next in 3 days, 2026-11-04T09:00:00Z" in got.stdout
    r = rows(b)
    assert len(r) == n + 1 and r[-1]["kind"] == "review" and r[-1]["grade"] == 3
    assert (r[-1]["days"], r[-1]["algo"], r[-1]["subject"]) == (3, "fsrs-5", subj)
    assert run(b, "due", now="2026-11-03T09:00:00Z").returncode == 42  # not yet
    assert run(b, "due", now="2026-11-04T09:00:00Z").returncode == 0  # on the day
    assert (
        "due 2026-11-04T09:00:00Z"
        in run(b, "due", "--all", now="2026-11-02T09:00:00Z").stdout
    )
    assert run(b, "check").returncode == 0


def test_the_schedule_replays_from_the_grades_alone(tmp_path):
    b, subj = make(tmp_path)
    i = subj[9:19]
    run(b, "review", i, "3", now="2026-11-01T09:00:00Z")
    run(b, "review", i, "good", now="2026-11-04T09:00:00Z")
    run(b, "review", i, "again", now="2026-11-20T09:00:00Z")
    rs = [r for r in rows(b) if r["kind"] == "review"]
    want = fc.replay(rs)
    assert [r["days"] for r in rs] == [w[0] for w in want]
    assert rs[1]["days"] > rs[0]["days"] > 0 and rs[2]["days"] < rs[1]["days"]
    assert run(b, "check").returncode == 0


def test_a_row_that_disagrees_with_its_grades_is_named(tmp_path):
    b, subj = make(tmp_path)
    run(b, "review", subj[9:19], "good")
    text = (b / "record.jsonl").read_text()
    lines = text.splitlines()
    row = json.loads(lines[-1])
    row["days"] = 400  # tampered, then re-chained so the chain itself holds
    body = {x: v for x, v in row.items() if x != "hash"}
    row["hash"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()  # fmt: skip
    lines[-1] = json.dumps(
        row, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    (b / "record.jsonl").write_text("\n".join(lines) + "\n")
    got = run(b, "check")
    assert got.returncode == 2 and "the row says 400" in got.stderr
    assert (
        run(b, "due").returncode == 2
    )  # nothing is scheduled from rows that don't hold


def test_a_review_of_an_unsealed_card_is_refused(tmp_path):
    b, subj = make(tmp_path, seal=False)
    kernel_row = {"subject": subj, "grade": 3, "days": 3, "due": "2026-11-04T09:00:00Z",
                  "algo": "fsrs-5"}  # fmt: skip
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel

    kernel.append(b, D0, "review", who="flashcards", **kernel_row)
    got = run(b, "check")
    assert got.returncode == 2 and "not sealed before it" in got.stderr


def test_a_changed_proposal_file_is_broken_and_never_studied(tmp_path):
    b, subj = make(tmp_path)
    f = b / "proposals" / f"{subj[9:]}.json"
    f.write_text(f.read_text().replace("Six hours.", "Eight hours."))
    got = run(b, "due")
    assert got.returncode == 42 and "1 broken" in got.stdout and "0 cards" in got.stdout


def test_bad_grades_ids_times_and_order_are_refused(tmp_path):
    b, subj = make(tmp_path)
    i = subj[9:19]
    for bad in (["review", i, "5"], ["review", i, "0"], ["review", i, "great"],
                ["review", "abc", "3"], ["review", "ffffffffff", "3"], ["show", i[:5]],
                ["due", "extra"], ["nope"], ["review", i]):  # fmt: skip
        got = run(b, *bad)
        assert got.returncode == 2 and not got.stdout.startswith("reviewed"), bad
    assert run(b, "due", now="yesterday").returncode == 2
    assert run(b, "due", "--all", now=None).returncode == 0
    assert run(b, "check", "--all").returncode == 2
    assert (
        run(b, "review", i, "good", now="2026-10-01T00:00:00Z").returncode == 2
    )  # before the seal
    run(b, "review", i, "good", now="2026-11-05T00:00:00Z")
    assert (
        run(b, "review", i, "good", now="2026-11-04T00:00:00Z").returncode == 2
    )  # before the last
    assert len([r for r in rows(b) if r["kind"] == "review"]) == 1
    assert run(tmp_path / "nowhere", "due").returncode == 2


def test_a_broken_record_is_refused(tmp_path):
    b, subj = make(tmp_path)
    with (b / "record.jsonl").open("a") as f:
        f.write("garbage\n")
    assert run(b, "due").returncode == 2


def test_it_never_seals_and_writes_only_review_rows(tmp_path):
    b, subj = make(tmp_path)
    before = rows(b)
    run(b, "due"), run(b, "show", subj[9:19]), run(b, "check")
    assert rows(b) == before
    run(b, "review", subj[9:19], "easy")
    new = rows(b)[len(before) :]
    assert [r["kind"] for r in new] == ["review"] and new[0]["standing"] == "unattested"
    assert (b / "proposals").exists() and len(list((b / "proposals").iterdir())) == 1


def test_the_front_is_the_words_of_the_file_name():
    assert fc.front({"path": "answers/why-runs_a.and.b.md"}) == "why runs a and b"
    assert fc.front({"path": "x/---.md"}) == "---"
