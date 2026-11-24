"""game-canon: what a game's table holds true is each sealed call and offer,
less what a sealed replacement stands over; the heads-up raises only what is
about the same thing; mine-stands-now and take-back wait on the person's own
seal and erase nothing; both-are-true is a row, no seal. The world is made up
for these tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
GM = HERE.parent / "game-master" / "game_master.py"
SCRIPT = HERE / "game_canon.py"
spec = importlib.util.spec_from_file_location("game_canon", SCRIPT)
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)
kernel = gc.kernel
NOW = ["--now", "2026-11-20T19:00:00Z"]
OLD = "The egg is a real dragon's."
NEW = "The egg was never a real dragon's; it's a painted stone."

WORLD = {
    "id": "garden-egg",
    "title": "The Garden Egg",
    "setting": "Made up for these tests.",
    "stats": ["Grit"],
    "base_stat": 1,
    "characters": [{"id": "mira", "name": "Mira", "role": "kid", "seat": True, "stats": {"Grit": 2}}],  # fmt: skip
    "places": [{"id": "garden", "name": "The school garden"}],
    "scenes": [{"id": "s1", "title": "Morning", "place": "garden", "opening": ["Dew."],
                "beats": [{"id": "a1", "kind": "action", "prompt": "Mira digs.", "suggests": "Grit",
                           "outcomes": {"strong": "s", "weak": "w", "miss": "m"}}]}],
}  # fmt: skip


class Table:
    """A fresh box with one game of WORLD open, and the commands against it."""

    def __init__(self, tmp: Path):
        pile = tmp / "pile"
        pile.mkdir(parents=True)
        (pile / "a.txt").write_text("x\n")
        self.box, self.wf = tmp / "box", tmp / "world.json"
        self.wf.write_text(json.dumps(WORLD))
        assert (
            self.k("init", "--pile", str(pile), "--key", str(tmp / "k")).returncode == 0
        )
        got = self.gm("open")
        assert got.returncode == 0, got.stderr

    def k(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(KERNEL), argv[0], "--box", str(self.box), *NOW, *argv[1:]], capture_output=True, text=True)  # fmt: skip

    def gm(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(GM), "--box", str(self.box), *argv, "--world", str(self.wf), *NOW], capture_output=True, text=True)  # fmt: skip

    def run(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), "--box", str(self.box), *argv], capture_output=True, text=True)  # fmt: skip

    def rows(self) -> list[dict]:
        return kernel.read(self.box / "record.jsonl")[0]

    def offer(self, fact: str, seal: bool | None = True) -> str:
        """FACT offered at the table by Mira; sealed, declined (False) or left (None)."""
        got = self.gm("offer", "mira", fact)
        assert got.returncode in (0, 42), got.stderr
        subject = [r for r in self.rows() if r["kind"] == "table-offer" and r["fact"] == fact][-1]["subject"]  # fmt: skip
        if seal is not None:
            assert self.k("seal" if seal else "decline", subject).returncode == 0
        return subject

    def holds(self) -> list[dict]:
        got = self.run("holds", "--json")
        assert got.returncode == 0, got.stderr
        return json.loads(got.stdout)


@pytest.fixture
def t(tmp_path) -> Table:
    return Table(tmp_path)


# ── the command line ────────────────────────────────────────────────────────


def test_a_command_line_it_has_not_is_refused_with_its_usage(t):
    for argv in ([], ["meets"], ["replace", "--old", "x"], ["both", "--old", "x", "--new", "y"], ["roll"], ["meets", "a", "b"], ["holds", "--old"]):  # fmt: skip
        got = t.run(*argv)
        assert got.returncode == 2, argv
        assert "game_canon.py --box DIR holds" in got.stderr
    got = subprocess.run([sys.executable, str(SCRIPT), "holds"], capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2


def test_a_folder_that_is_not_a_box_is_refused(tmp_path):
    got = subprocess.run([sys.executable, str(SCRIPT), "--box", str(tmp_path), "holds"], capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "isn't a box" in got.stderr


def test_a_record_that_does_not_verify_is_refused(t):
    path = t.box / "record.jsonl"
    lines = path.read_text().splitlines()
    lines[-1] = lines[-1].replace('"who":"', '"who":"not ', 1)
    path.write_text("\n".join(lines) + "\n")
    got = t.run("holds")
    assert got.returncode == 2 and "doesn't verify" in got.stderr


# ── what the table holds true ───────────────────────────────────────────────


def test_nothing_sealed_is_nothing_held(t):
    got = t.run("holds")
    assert got.returncode == 0 and got.stdout.strip() == "nothing is held true at this table yet"  # fmt: skip


def test_only_what_the_person_sealed_is_held(t):
    kept = t.offer(OLD)
    t.offer("Mira hates beetles.", seal=False)
    t.offer("The groundskeeper saw everything.", seal=None)
    held = t.holds()
    assert [(h["subject"], h["fact"]) for h in held] == [(kept, OLD)]
    seal = next(r for r in t.rows() if r["kind"] == "seal" and r.get("subject") == kept)
    assert held[0]["n"] == seal["n"] and held[0]["day"] == "2026-11-20"
    words = t.run("holds").stdout
    assert f"on 2026-11-20 (row {seal['n']}): {OLD}" in words and kept in words


# ── the heads-up ────────────────────────────────────────────────────────────


def test_a_new_word_about_the_same_thing_meets_what_is_held(t):
    kept = t.offer(OLD)
    got = t.run("meets", NEW, "--json")
    assert got.returncode == 0
    assert [m["subject"] for m in json.loads(got.stdout)] == [kept]
    assert not [
        r for r in t.rows() if r["kind"] in (gc.REPLACES, gc.BOTH)
    ]  # asking writes nothing


@pytest.mark.parametrize("fact", ["The egg is warm.", "Mira sneezes.", OLD])
def test_a_different_thing_or_the_same_words_again_meet_nothing(t, fact):
    t.offer(OLD)
    got = t.run("meets", fact)
    assert got.returncode == 0
    assert got.stdout.strip() == "nothing the table holds true is about the same thing"


def test_a_word_does_not_meet_itself(t):
    kept = t.offer(OLD)
    got = t.run(
        "meets", "A real dragon's egg, the egg is.", "--subject", kept, "--json"
    )
    assert json.loads(got.stdout) == []


# ── mine stands now ─────────────────────────────────────────────────────────


def test_mine_stands_now_waits_on_the_persons_seal_and_erases_nothing(t):
    old = t.offer(OLD)
    new = t.offer(NEW, seal=None)
    got = t.run("replace", "--old", old, "--new", new, "--fact", NEW, *NOW)
    assert got.returncode == 42, got.stderr
    rep = next(r for r in t.rows() if r["kind"] == gc.REPLACES)
    assert (rep["old"], rep["new"], rep["fact"], rep["who"]) == (old, new, NEW, gc.WHO)
    assert f"waiting on your seal: {rep['subject']}" in got.stdout
    assert [r["kind"] for r in t.rows() if r.get("subject") == rep["subject"]] == ["proposal", gc.REPLACES]  # fmt: skip
    assert [h["subject"] for h in t.holds()] == [
        old
    ]  # nothing stops standing on code's word
    assert t.k("seal", rep["subject"]).returncode == 0
    assert t.k("seal", new).returncode == 0
    assert [h["fact"] for h in t.holds()] == [NEW]
    assert [r["kind"] for r in t.rows() if r.get("subject") == old and r["kind"] in ("seal", "decline")] == ["seal"]  # fmt: skip


def test_a_replacement_is_kept_under_the_old_subjects_own_hash(t):
    old = t.offer(OLD)
    t.run("replace", "--old", old, "--new", "", "--fact", NEW, *NOW)
    rep = next(r for r in t.rows() if r["kind"] == gc.REPLACES)
    claim = f"From now on this stands in place of what the table made true on 2026-11-20: {OLD}"  # fmt: skip
    prop = {"path": "table/replaces/" + old.split(":")[-1][:16] + ".txt", "data": NEW, "cites": [], "claim": claim}  # fmt: skip
    assert rep["subject"] == kernel.subject_of(
        prop
    )  # a record Die-Namic kept reads the same


def test_a_replacement_declined_leaves_the_old_one_standing(t):
    old = t.offer(OLD)
    t.run("replace", "--old", old, "--new", "", "--fact", NEW, *NOW)
    rep = next(r for r in t.rows() if r["kind"] == gc.REPLACES)
    assert t.k("decline", rep["subject"]).returncode == 0
    assert [h["subject"] for h in t.holds()] == [old]


@pytest.mark.parametrize("verb", ["replace", "both", "take-back"])
def test_only_what_the_table_holds_true_can_be_replaced_or_kept_beside(t, verb):
    waiting = t.offer(OLD, seal=None)
    more = [] if verb == "take-back" else ["--new", "x", "--fact", NEW]
    got = t.run(verb, "--old", waiting, *more, *NOW)
    assert got.returncode == 2 and "isn't something the table holds true now" in got.stderr  # fmt: skip
    assert not [r for r in t.rows() if r["kind"] in (gc.REPLACES, gc.BOTH)]


def test_a_replacement_the_kernel_will_not_take_is_refused_in_its_words(t, monkeypatch):  # fmt: skip
    monkeypatch.setattr(gc.gm, "hand_in", lambda *a: ("", "the kernel's propose: no"))
    old = {"subject": "proposal:" + "ab12" * 16, "day": "2026-11-20", "fact": OLD}
    with pytest.raises(RuntimeError, match="the kernel's propose: no"):
        gc.replace(Path("."), NOW[1], old, "", NEW)


# ── a yes taken back ────────────────────────────────────────────────────────


def test_a_yes_taken_back_waits_on_the_seal_then_no_longer_stands(t):
    old = t.offer(OLD)
    got = t.run("take-back", "--old", old, *NOW)
    assert got.returncode == 42, got.stderr
    rep = next(r for r in t.rows() if r["kind"] == gc.REPLACES)
    assert (rep["new"], rep["fact"]) == ("", gc.SLIP)
    assert [h["subject"] for h in t.holds()] == [old]
    assert t.k("seal", rep["subject"]).returncode == 0
    assert t.holds() == []


# ── both are true ───────────────────────────────────────────────────────────


def test_both_are_true_is_a_row_no_seal_and_the_pair_is_not_raised_again(t):
    old = t.offer(OLD)
    seals = len([r for r in t.rows() if r["kind"] == "seal"])
    got = t.run("both", "--old", old, "--new", "s2", "--fact", NEW, *NOW)
    assert got.returncode == 0, got.stderr
    row = t.rows()[-1]
    assert row["kind"] == gc.BOTH and row["pair"] == sorted((old, "s2")) and row["facts"] == sorted((OLD, NEW))  # fmt: skip
    assert len([r for r in t.rows() if r["kind"] == "seal"]) == seals
    assert json.loads(t.run("meets", NEW, "--json").stdout) == []
    assert [h["subject"] for h in t.holds()] == [old]


# ── tonight ─────────────────────────────────────────────────────────────────


def test_tonight_is_only_what_came_after_the_last_session_ended(monkeypatch):
    held = [{"n": n, "fact": f"fact {n}"} for n in (3, 8, 12)]
    monkeypatch.setattr(gc, "standing", lambda box, rows: held)
    two_nights = [{"kind": "session", "to": 5}, {"kind": "session", "to": 10}]
    assert [t["n"] for t in gc.tonight(Path("."), two_nights)] == [12]
    assert [t["n"] for t in gc.tonight(Path("."), [])] == [3, 8, 12]


def test_tonight_on_the_command_line(t):
    got = t.run("tonight")
    assert got.returncode == 0 and "nothing has been made true" in got.stdout
    t.offer(OLD)
    assert OLD in t.run("tonight").stdout
