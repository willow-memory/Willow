"""retire: an approved answer is set aside only by a retirement you sealed
for that very answer, after it; the latest seal decides; and nothing is
proposed twice, for an answer that doesn't stand, or without a reason."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-21T00:00:00Z"]
WAITS = "waiting on your seal"
#: stale answers are the stale-answers add-on's, which the card only looks for
STALE = (HERE.parent / "stale-answers").is_dir()
NOT_LOOKED = "stale answers not looked for: stale-answers isn't beside this add-on"
needs_stale = pytest.mark.skipif(not STALE, reason="no stale-answers add-on")


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def retire(b: Path, *more: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HERE / "retire.py"), "--box", str(b), *more],
                          capture_output=True, text=True)  # fmt: skip


def module():
    spec = importlib.util.spec_from_file_location(
        "retire_under_test", HERE / "retire.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def subject(row: dict) -> str:
    canon = json.dumps({x: row[x] for x in ("path", "data", "cites", "claim")},
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False)  # fmt: skip
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def kept(b: Path, subj: str) -> Path:
    """The file the kernel keeps a suggestion in."""
    return Path(b, "proposals", subj[9:] + ".json")


def offer(b: Path, words: str, row: dict, cite: bool = True) -> str:
    """One suggestion at the door under these words; its subject."""
    got = json.loads(k("bite", "--box", str(b), *NOW, words).stdout)
    row = {**row, "cites": [got["served"][0]["id"]] if cite else []}
    f = b.parent / "rows.jsonl"
    f.write_text(json.dumps(row) + "\n")
    said = k("propose", "--box", str(b), "--file", str(f), *NOW).stdout
    assert f"{subject(row)}  {WAITS}" in said, said
    return subject(row)


def seal(b: Path, subj: str) -> None:
    got = k("seal", "--box", str(b), subj, *NOW)
    assert got.returncode == 0, got.stderr


def approved(tmp_path: Path) -> tuple[Path, Path, str, str]:
    """A box with two approved answers, each citing its own file."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    (pile / "shed.md").write_text("The shed door is painted blue.\n")
    b = tmp_path / "box"
    k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k"), *NOW)
    sun = offer(b, "how much sun do tomatoes want",
                {"path": "sun.md", "data": "Six hours.", "claim": "garden.md"})  # fmt: skip
    shed = offer(b, "what colour is the shed door",
                 {"path": "shed.md", "data": "Blue.", "claim": "shed.md"})  # fmt: skip
    seal(b, sun)
    seal(b, shed)
    return b, pile, sun, shed


def proposed(got: subprocess.CompletedProcess) -> str:
    return got.stdout.split("seal --box")[1].split()[1]


def aside(b: Path) -> dict:
    mod = module()
    return mod.set_aside(b, mod.kernel.read(b / "record.jsonl")[0])


def rows_of(b: Path) -> list[dict]:
    return [json.loads(x) for x in (b / "record.jsonl").read_text().splitlines()]


# ── the report ──────────────────────────────────────────────────────────────
def test_a_box_where_every_answer_holds_is_empty_and_nothing_waits(tmp_path):
    b, _, _, _ = approved(tmp_path)
    got = retire(b)
    assert got.returncode == 0, got.stderr
    line = f"retire: empty, 2 approved; 0 set aside; 0 {WAITS}; 0 no longer hold"
    assert got.stdout.strip() == (line if STALE else f"{line}; {NOT_LOOKED}")


def test_json_is_the_same_report(tmp_path):
    b, _, sun, _ = approved(tmp_path)
    seal(
        b, proposed(retire(b, "propose", sun, "--because", "it was the old bed", *NOW))
    )
    doc = json.loads(retire(b, "--json").stdout)
    assert doc["addon"] == "retire" and doc["state"] == "populated"
    assert module().report_text(doc) == retire(b).stdout.strip()
    assert doc["groups"] == [{"name": "set aside", "rows": [
        {"where": sun[:21] + "…", "what": f"at row {len(rows_of(b)) - 1}: it was the old bed"}]}]  # fmt: skip


# ── propose, one named ──────────────────────────────────────────────────────
def test_a_proposal_sets_nothing_aside_until_it_is_sealed(tmp_path):
    b, _, sun, shed = approved(tmp_path)
    before = len(rows_of(b))
    got = retire(b, "propose", sun, "--because", "it was the old bed", *NOW)
    assert got.returncode == 42, got.stderr
    r = proposed(got)
    assert f"{r}  {WAITS}" in got.stdout
    assert f"to set {sun[:21]}… aside, seal it with your key:" in got.stdout
    assert [x["kind"] for x in rows_of(b)[before:]] == ["bite", "proposal"]
    assert rows_of(b)[-1]["ts"] == NOW[1], "--now is the time on its rows"
    assert aside(b) == {}, "waiting is not aside"
    said = retire(b)
    assert said.returncode == 42, "a retirement waits on you"
    assert f"2 approved; 0 set aside; 1 {WAITS}; 0 no longer hold" in said.stdout
    assert f"## {WAITS}\n  {sun[:21]}…  by {r[:21]}…: it was the old bed" in said.stdout

    seal(b, r)
    n = len(rows_of(b)) - 1
    assert aside(b) == {
        sun: {"by": r, "row": n, "because": "it was the old bed", "instead": None}
    }
    said = retire(b)
    assert said.returncode == 0, "sealed: nothing waits any more"
    assert f"2 approved; 1 set aside; 0 {WAITS}" in said.stdout
    assert f"## set aside\n  {sun[:21]}…  at row {n}: it was the old bed" in said.stdout
    assert shed not in aside(b)


def test_a_sealed_retirement_is_served_through_the_kernel_for_its_own_question(
    tmp_path,
):
    b, _, sun, _ = approved(tmp_path)
    r = proposed(retire(b, "propose", sun, "--because", "it was the old bed", *NOW))
    seal(b, r)
    got = json.loads(k("bite", "--box", str(b), *NOW, f"retire {sun}").stdout)
    assert got["state"] == "sealed" and got["by"] == r
    assert json.loads(got["answer"]) == {
        "retire": sun, "because": "it was the old bed", "instead": None}  # fmt: skip
    assert Path(b, "written", "retire", sun[9:] + ".json").is_file()
    still = json.loads(
        k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want").stdout
    )
    assert still["by"] == sun, (
        "the kernel still serves it for its own words; the card says so"
    )


def test_what_stands_instead_is_kept_and_said(tmp_path):
    b, _, sun, shed = approved(tmp_path)
    r = proposed(
        retire(b, "propose", sun, "--because", "moved", "--instead", shed, *NOW)
    )
    seal(b, r)
    assert aside(b)[sun]["instead"] == shed
    assert f"moved; instead {shed[:21]}…" in retire(b).stdout


def test_setting_a_retirement_aside_brings_its_answer_back(tmp_path):
    b, _, sun, _ = approved(tmp_path)
    r = proposed(retire(b, "propose", sun, "--because", "it was the old bed", *NOW))
    seal(b, r)
    again = retire(b, "propose", r, "--because", "I was wrong, it holds", *NOW)
    assert again.returncode == 42, again.stderr
    assert sun in aside(b), "proposed, not sealed: still aside"
    seal(b, proposed(again))
    assert list(aside(b)) == [r], "the retirement is aside, and its answer stands again"
    assert "2 approved; 0 set aside" in retire(b).stdout, (
        "a retirement is not one of your answers"
    )
    back = retire(b, "propose", sun, "--because", "it was the old bed after all", *NOW)
    assert back.returncode == 42, "and it can be set aside afresh, for a new reason"


# ── what is refused ─────────────────────────────────────────────────────────
def refused(got: subprocess.CompletedProcess, why: str) -> None:
    assert got.returncode == 2 and why in got.stderr, (got.returncode, got.stderr)
    assert got.stdout == ""


def test_only_an_approved_answer_that_stands_can_be_set_aside(tmp_path):
    b, _, sun, _ = approved(tmp_path)
    before = rows_of(b)
    refused(retire(b, "propose", "proposal:" + "0" * 64, "--because", "x", *NOW),
            "is not an approved answer that still stands in this box")  # fmt: skip
    waits = offer(b, "which colour was the shed door painted",
                  {"path": "s2.md", "data": "Green.", "claim": "shed.md"})  # fmt: skip
    refused(
        retire(b, "propose", waits, "--because", "x", *NOW), "is not an approved answer"
    )
    held = kept(b, sun)
    held.write_text(held.read_text().replace("Six hours.", "Nine hours."))
    refused(
        retire(b, "propose", sun, "--because", "x", *NOW), "is not an approved answer"
    )
    assert [r["kind"] for r in rows_of(b)[len(before) :]] == ["bite", "proposal"], (
        "a refusal writes nothing: only the offer made here is on the record"
    )


def test_a_reason_is_required(tmp_path):
    b, _, sun, _ = approved(tmp_path)
    refused(
        retire(b, "propose", sun, "--because", "  ", *NOW), "say why it no longer holds"
    )
    assert retire(b, "propose", sun, *NOW).returncode == 2, (
        "and --because must be there"
    )


def test_nothing_is_proposed_twice_and_a_no_is_final(tmp_path):
    b, _, sun, shed = approved(tmp_path)
    r = proposed(retire(b, "propose", sun, "--because", "old", *NOW))
    refused(retire(b, "propose", sun, "--because", "old", *NOW),
            f"this was proposed before: already {WAITS}, row")  # fmt: skip
    seal(b, r)
    refused(retire(b, "propose", sun, "--because", "another reason", *NOW),
            f"{sun} is already set aside, at row {len(rows_of(b)) - 1}")  # fmt: skip
    no = proposed(retire(b, "propose", shed, "--because", "repainted", *NOW))
    assert k("decline", "--box", str(b), no, *NOW).returncode == 0
    refused(retire(b, "propose", shed, "--because", "repainted", *NOW),
            "this was proposed before: you declined it at row")  # fmt: skip
    assert shed not in aside(b) and f"0 {WAITS}" in retire(b).stdout


def test_what_stands_instead_must_be_another_answer_that_stands(tmp_path):
    b, _, sun, shed = approved(tmp_path)
    refused(retire(b, "propose", sun, "--because", "x", "--instead", sun, *NOW),
            "an answer can't stand instead of itself")  # fmt: skip
    refused(retire(b, "propose", sun, "--because", "x", "--instead", "proposal:" + "1" * 64, *NOW),
            "is not an approved answer that still stands, to stand instead")  # fmt: skip
    r = proposed(retire(b, "propose", shed, "--because", "repainted", *NOW))
    seal(b, r)
    refused(retire(b, "propose", sun, "--because", "x", "--instead", shed, *NOW),
            "to stand instead")  # fmt: skip
    refused(
        retire(b, "propose", sun, "--because", "x", "--instead", r, *NOW),
        "to stand instead",
    )


def test_not_a_box_a_broken_record_and_a_bad_command_line_are_refused(tmp_path):
    b, _, sun, _ = approved(tmp_path)
    refused(retire(tmp_path / "nowhere"), "isn't a box")
    for bad in (["propose"], ["propose", sun], ["propose", sun, "--because", "x", "--stale"],
                ["propose", "--stale", "--because", "x"], ["propose", sun, sun, "--because", "x"],
                ["--stale"], ["propose", sun, "--because", "x", "--json"], ["drop", sun],
                ["--instead", sun], ["propose", "--stale", "--json"]):  # fmt: skip
        got = retire(b, *bad)
        assert got.returncode == 2 and "retire.py --box DIR" in got.stderr, bad
    none = subprocess.run(
        [sys.executable, str(HERE / "retire.py")], capture_output=True, text=True
    )
    assert none.returncode == 2 and "retire.py" in none.stderr
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("seal", "seel", 1))
    refused(retire(b), "the record doesn't verify")
    refused(
        retire(b, "propose", sun, "--because", "x", *NOW), "the record doesn't verify"
    )


# ── what counts as a retirement ─────────────────────────────────────────────
def by_hand(b: Path, words: str, target: str, path: str | None = None, data: str | None = None,
            why: str = "by hand") -> str:  # fmt: skip
    mod = module()
    row = mod.proposal(target, why, None)
    row = {**row, "path": path or row["path"], "data": data or row["data"]}
    return offer(b, words, row, cite=False)


def test_a_seal_under_another_question_or_another_path_is_no_retirement(tmp_path):
    b, _, sun, shed = approved(tmp_path)
    seal(b, by_hand(b, "set that one aside please", sun))
    seal(b, by_hand(b, f"retire {shed}", sun, why="under another answer's question"))
    seal(b, by_hand(b, f"retire {sun}", sun, path="notes/" + sun[9:] + ".json"))
    seal(b, by_hand(b, f"retire {sun}", sun, path="retire/x.json", data="not json"))
    seal(
        b, by_hand(b, f"retire {sun}", sun, path="retire/y.json", data='{"retire": 7}')
    )
    assert aside(b) == {}, (
        "the path, the data and the question must all name the answer"
    )
    assert "7 approved; 0 set aside" in retire(b).stdout, (
        "what is no retirement is an answer like any other"
    )


def test_a_retirement_sealed_before_its_answer_sets_nothing_aside(tmp_path):
    b, _, _, _ = approved(tmp_path)
    late = offer(b, "which colour was the shed door painted",
                 {"path": "s2.md", "data": "Green.", "claim": "shed.md"})  # fmt: skip
    early = by_hand(b, f"retire {late}", late)
    seal(b, early)
    assert aside(b) == {}, "the answer isn't approved yet"
    seal(b, late)
    assert aside(b) == {}, (
        "a retirement can't reach forward to an answer sealed after it"
    )


def test_a_waiting_retirement_whose_file_was_changed_is_not_counted(tmp_path):
    b, _, sun, shed = approved(tmp_path)
    r = proposed(retire(b, "propose", sun, "--because", "old", *NOW))
    held = kept(b, r)
    held.write_text(held.read_text().replace(sun, shed))
    assert f"0 {WAITS}" in retire(b).stdout
    held.unlink()
    assert f"0 {WAITS}" in retire(b).stdout


# ── stale answers ───────────────────────────────────────────────────────────
@needs_stale
def test_an_answer_whose_cited_passage_went_is_named_then_proposed_once(tmp_path):
    b, pile, sun, shed = approved(tmp_path)
    assert retire(b, "propose", "--stale", *NOW).stdout.strip() == (
        "nothing to propose: every approved answer's cited passages are still in your folder"
    )
    (pile / "garden.md").write_text("Tomatoes want eight hours of sun.\n")
    said = retire(b)
    assert said.returncode == 42, "one no longer holds, and nobody has proposed it"
    assert f"2 approved; 0 set aside; 0 {WAITS}; 1 no longer hold" in said.stdout
    why = "its cited passage is no longer in your folder (garden.md:1)"
    assert f"## no longer holds, not proposed yet\n  {sun[:21]}…  {why}" in said.stdout

    got = retire(b, "propose", "--stale", *NOW)
    assert got.returncode == 42 and got.stdout.count(WAITS) == 1, got.stderr
    r = proposed(got)
    said = retire(b)
    assert f"1 {WAITS}; 0 no longer hold" in said.stdout and said.returncode == 42
    again = retire(b, "propose", "--stale", *NOW)
    assert again.returncode == 0 and again.stdout.startswith(
        f"left  {sun[:21]}…  this was proposed"
    )
    seal(b, r)
    assert aside(b)[sun]["because"] == why and shed not in aside(b)
    assert retire(b).returncode == 0
    done = retire(b, "propose", "--stale", *NOW)
    assert done.returncode == 0 and "is already set aside" in done.stdout


@needs_stale
def test_each_stale_answer_gets_a_proposal_of_its_own(tmp_path):
    b, pile, _, _ = approved(tmp_path)
    (pile / "garden.md").unlink()
    (pile / "shed.md").write_text("The shed door is painted red.\n")
    got = retire(b, "propose", "--stale", *NOW)
    assert got.returncode == 42 and got.stdout.count(WAITS) == 2
    assert f"2 {WAITS}" in retire(b).stdout


@pytest.mark.skipif(
    STALE, reason="stale-answers is here: this is for a copy without it"
)
def test_without_stale_answers_it_is_said_and_propose_stale_is_refused(tmp_path):
    b, _, _, _ = approved(tmp_path)
    said = retire(b)
    assert said.returncode == 0 and NOT_LOOKED in said.stdout
    got = retire(b, "propose", "--stale", *NOW)
    assert (
        got.returncode == 2
        and got.stderr == "refused: stale-answers isn't beside this add-on\n"
    )


def test_a_box_stale_answers_cant_read_is_said_not_crashed_on(tmp_path):
    b, _, sun, _ = approved(tmp_path)
    cfg = json.loads((b / "kernel.json").read_text())
    cfg["sources"] = {"a": cfg.pop("pile")}
    (b / "kernel.json").write_text(json.dumps(cfg))
    said = retire(b)
    assert said.returncode == 0 and "stale answers not looked for: " in said.stdout
    why = said.stdout.split("stale answers not looked for: ", 1)[1].splitlines()[0]
    got = retire(b, "propose", "--stale", *NOW)
    assert got.returncode == 2 and got.stderr == f"refused: {why}\n"  # its own words
