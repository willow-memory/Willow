"""story-ideas: seeds dealt from the box's own words, the same seed dealing the
same ideas again; only the story last played; what the GM sealed and only
that; the binder's cast never named in a session's notes; every promise for
next time; one passage drawn through random-passage; and nothing proposed or
sealed by it. The world is game-master's test world, made up."""

from __future__ import annotations

import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "story_ideas.py"
GM = HERE.parent / "game-master" / "game_master.py"
spec = importlib.util.spec_from_file_location("story_ideas", SCRIPT)
si = importlib.util.module_from_spec(spec)
spec.loader.exec_module(si)
NOW = ["--now", "2026-11-23T09:00:00Z"]


def outcomes(tag: str) -> dict:
    return {b: f"{tag} {b}" for b in ("strong", "weak", "miss")}


BRIDGE = {
    "id": "toll-bridge",
    "title": "The Toll Bridge",
    "setting": "Made up for these tests.",
    "stats": ["Grit", "Wit"],
    "base_stat": 1,
    "characters": [
        {"id": "ana", "name": "Ana", "role": "keeper", "seat": True, "stats": {"Grit": 3}},
        {"id": "bo", "name": "Bo", "role": "drover", "seat": True, "stats": {"Wit": 2}},
        {"id": "cy", "name": "Cy", "role": "toll-man", "seat": False, "stats": {}},
    ],
    "places": [{"id": "bridge", "name": "The bridge"}, {"id": "inn", "name": "Mag's inn"}],
    "scenes": [
        {"id": "s1", "title": "Dusk", "place": "bridge", "opening": ["The light goes."],
         "beats": [
             {"id": "a1", "kind": "action", "prompt": "Ana forces the gate.", "suggests": "Grit", "outcomes": outcomes("a1")},
             {"id": "a2", "kind": "action", "prompt": "Bo reads the ledger.", "suggests": "Wit", "outcomes": outcomes("a2")},
             {"id": "d1", "kind": "decision", "prompt": "What does the ledger say?",
              "proposes": {"fact": "The toll was paid twice.", "proposed_by": "cy"}},
         ]},
    ],
}  # fmt: skip
#: a second story in the folder, never played: its names are not the ideas'
MILL = {**BRIDGE, "id": "old-mill", "title": "The Old Mill",
        "characters": [{"id": "zed", "name": "Zed", "role": "miller", "seat": True, "stats": {}}],
        "places": [{"id": "mill", "name": "The millrace"}],
        "scenes": [{"id": "m1", "title": "Morning", "place": "mill", "opening": ["Water."],
                    "beats": [{"id": "m1a", "kind": "action", "prompt": "Zed lifts the sluice.", "suggests": "Grit",
                               "outcomes": outcomes("m1a")}]}]}  # fmt: skip


def run(*argv: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], capture_output=True, text=True)  # fmt: skip


class Box:
    """A game box laid as willow's game box lays one: a binder, worlds, a record."""

    def __init__(self, tmp: Path):
        self.pile, self.worlds, self.box = tmp / "pile", tmp / "worlds", tmp / "box"
        for folder in ("people", "monsters", "sessions"):
            (self.pile / folder).mkdir(parents=True)
        (self.pile / "people" / "ferryman.md").write_text(
            "# The Ferryman\n\nRows for coin.\n"
        )
        (self.pile / "monsters" / "hag.md").write_text(
            "# River Hag\n\nWaits under the arches.\n"
        )
        (self.pile / "monsters" / "wolf.md").write_text(
            "# Toll Wolf\n\nGuards the far side.\n"
        )
        (self.pile / "sessions" / "night-1.md").write_text(
            "The toll wolf howled all night.\nNext time: where the toll money went.\n"
        )
        self.worlds.mkdir()
        (self.worlds / "bridge.json").write_text(json.dumps(BRIDGE))
        (self.worlds / "mill.json").write_text(json.dumps(MILL))
        self.key = tmp / "k"
        assert self.k("init", "--pile", str(self.pile), "--key", str(self.key)).returncode == 0  # fmt: skip

    def k(self, verb: str, *rest: str) -> subprocess.CompletedProcess:
        return run(verb, "--box", str(self.box), *NOW, *rest, script=KERNEL)

    def gm(self, *argv: str) -> subprocess.CompletedProcess:
        return run("--box", str(self.box), *argv, "--world", str(self.worlds / "bridge.json"), *NOW, script=GM)  # fmt: skip

    def rows(self) -> list[dict]:
        return si.kernel.read(self.box / "record.jsonl")[0]

    def play(self, answer: str = "seal") -> None:
        """The bridge played to its decision, and the GM's answer to it."""
        for argv in (["open"], ["act", "Grit"], ["act", "Wit"]):
            assert self.gm(*argv).returncode == 0
        assert self.gm("ask").returncode == 42
        subject = [r for r in self.rows() if r["kind"] == si.gm.ASK][-1]["subject"]
        assert (
            self.k(answer, subject).returncode == 0
        )  # the person's answer, by their own key

    def ideas(self, *more: str) -> subprocess.CompletedProcess:
        return run("--box", str(self.box), "--worlds", str(self.worlds), "--pile", str(self.pile), *more)  # fmt: skip


@pytest.fixture
def b(tmp_path):
    return Box(tmp_path)


def seeds(got: subprocess.CompletedProcess) -> str:
    return got.stdout.split("## Set up")[0]


# ── refusals ─────────────────────────────────────────────────────────────────


def test_a_command_line_it_has_not_is_refused_with_its_usage(b):
    for argv in ([], ["--box", str(b.box)], ["--box", str(b.box), "--worlds", str(b.worlds)],
                 ["--box", str(b.box), "--worlds", str(b.worlds), "--pile", str(b.pile), "deal"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2, argv
        assert "story_ideas.py --box DIR --worlds DIR --pile DIR" in got.stderr


def test_a_folder_that_is_not_a_box_is_refused(b, tmp_path):
    got = run("--box", str(tmp_path), "--worlds", str(b.worlds), "--pile", str(b.pile))
    assert got.returncode == 2 and "isn't a box" in got.stderr


def test_worlds_or_a_pile_that_is_not_a_folder_is_refused(b, tmp_path):
    got = run("--box", str(b.box), "--worlds", str(tmp_path / "none"), "--pile", str(b.pile))  # fmt: skip
    assert got.returncode == 2 and "--worlds" in got.stderr and "isn't a folder" in got.stderr  # fmt: skip
    got = run("--box", str(b.box), "--worlds", str(b.worlds), "--pile", str(tmp_path / "none"))  # fmt: skip
    assert got.returncode == 2 and "--pile" in got.stderr


@pytest.mark.parametrize(
    "count, said", [("five", "a whole number"), ("0", "at least 1")]
)
def test_a_count_that_is_not_one_or_more_is_refused(b, count, said):
    got = b.ideas("--count", count)
    assert got.returncode == 2 and said in got.stderr


def test_a_record_that_does_not_verify_is_refused(b):
    path = b.box / "record.jsonl"
    path.write_text(path.read_text().replace('"kind":"', '"kind":"x', 1))
    got = b.ideas("--seed", "s")
    assert got.returncode == 2 and "doesn't verify" in got.stderr


# ── the seeds ────────────────────────────────────────────────────────────────


def test_the_same_seed_deals_the_same_ideas_and_count_of_them(b):
    b.play()
    first, again = b.ideas("--seed", "between nights"), b.ideas("--seed", "between nights")  # fmt: skip
    assert first.returncode == 0, first.stderr
    assert seeds(first) == seeds(again)
    assert len([ln for ln in seeds(first).splitlines() if ln.startswith("  - ")]) == 5
    three = b.ideas("--seed", "between nights", "--count", "3")
    assert len([ln for ln in seeds(three).splitlines() if ln.startswith("  - ")]) == 3
    other = b.ideas("--seed", "another night")
    assert seeds(other) != seeds(first)


def test_with_no_seed_the_ideas_are_todays(b):
    b.play()
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    assert seeds(b.ideas()) == seeds(b.ideas("--seed", f"ideas {today}"))


def test_the_story_played_is_the_one_ideas_are_for(b):
    b.play()
    g = si.grammar(b.box, b.worlds, b.pile, b.rows())
    assert g["who"] == ["Ana", "Bo"] and "Zed" not in json.dumps(g)
    assert g["place"] == ["Mag's inn", "the bridge"]  # only a leading The is lowered
    assert g["npc"] == ["Cy", "the Ferryman"]


def test_with_nothing_played_every_story_in_the_folder_is_dealt_from(b):
    g = si.grammar(b.box, b.worlds, b.pile, b.rows())
    assert set(g["who"]) == {"Ana", "Bo", "Zed"}


def test_what_the_gm_sealed_is_canon_and_what_they_declined_is_not(b, tmp_path):
    b.play("seal")
    assert si.grammar(b.box, b.worlds, b.pile, b.rows())["canon"] == ["the toll was paid twice"]  # fmt: skip
    no = Box(tmp_path / "no")
    no.play("decline")
    assert "canon" not in si.grammar(no.box, no.worlds, no.pile, no.rows())


def test_a_thread_is_what_comes_after_next_time_and_one_that_ends_there_is_none(b):
    assert si.grammar(b.box, b.worlds, b.pile, b.rows())["thread"] == ["where the toll money went"]  # fmt: skip
    (b.pile / "sessions" / "night-2.md").write_text("We stopped there. Pick it up next time\n")  # fmt: skip
    assert si.grammar(b.box, b.worlds, b.pile, b.rows())["thread"] == ["where the toll money went"]  # fmt: skip
    assert b.ideas("--seed", "s").returncode == 0


def test_a_box_with_too_little_in_it_says_so(tmp_path):
    pile, worlds = tmp_path / "pile", tmp_path / "worlds"
    pile.mkdir()
    worlds.mkdir()
    (pile / "a.md").write_text("Nothing of a story here at all.\n")
    box = tmp_path / "box"
    assert run("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k"), *NOW, script=KERNEL).returncode == 0  # fmt: skip
    got = run("--box", str(box), "--worlds", str(worlds), "--pile", str(pile), "--seed", "s")  # fmt: skip
    assert got.returncode == 0 and "too little in it yet to deal from" in got.stdout
    assert "Everything the binder sets up has come out" in got.stdout
    assert "No promises made for next time." in got.stdout
    drawn = got.stdout.split("## Something you wrote and forgot\n")[1]
    assert (
        drawn.strip() == "No passage in your folder has 8 words or more."
    )  # random-passage's own words


def test_a_world_file_that_is_not_a_world_is_left_out(b):
    (b.worlds / "broken.json").write_text("{}")
    assert set(si.grammar(b.box, b.worlds, b.pile, b.rows())["who"]) == {
        "Ana",
        "Bo",
        "Zed",
    }


# ── the binder ───────────────────────────────────────────────────────────────


def test_the_cast_no_session_has_named_is_set_up_never_played(b):
    got = b.ideas("--seed", "s")
    assert "  - River Hag  (monsters/)" in got.stdout
    assert "  - The Ferryman  (people/)" in got.stdout
    assert "Toll Wolf" not in got.stdout.split("## Set up")[1].split("## Still open")[0]


def test_every_promise_for_next_time_is_still_open_by_file_and_line(b):
    got = b.ideas("--seed", "s")
    assert (
        "  sessions/night-1.md:2  Next time: where the toll money went." in got.stdout
    )


def test_a_capital_is_lowered_only_where_a_word_begins_a_sentence():
    assert si.lower_first("The hound") == "the hound"
    assert si.lower_first("NASA sent it") == "NASA sent it"
    assert si.lower_first("a hound") == "a hound" and si.lower_first("") == ""
    assert si.mid_sentence("The bridge") == "the bridge" and si.mid_sentence("Theo") == "Theo"  # fmt: skip


# ── what it writes ───────────────────────────────────────────────────────────


def test_one_passage_is_drawn_through_random_passage_and_nothing_is_handed_in(b):
    b.play()
    before = b.rows()
    got = b.ideas("--seed", "s")
    assert got.returncode == 0 and "## Something you wrote and forgot" in got.stdout
    new = b.rows()[len(before) :]
    assert [r["kind"] for r in new] == ["surprise"]
    assert not any(r["kind"] in ("seal", "decline", "proposal") for r in new)
