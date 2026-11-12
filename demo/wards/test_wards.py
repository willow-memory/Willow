"""demo/wards: the made-up files are what make_life.py writes, and the
scene plays as its page tells it: who holds each box, what a held box
cannot find, whose key proves whose seal, and what a handover leaves."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_life  # noqa: E402
import scene  # noqa: E402
import adults  # noqa: E402
import askable  # noqa: E402
import card  # noqa: E402
import fourteen  # noqa: E402
import tense  # noqa: E402

make_life.main(
    []
)  # life/ is not kept in git: the files are made, the same bytes each time


def test_the_made_up_files_are_as_written_and_his_words_are_in_no_box_marit_holds():
    assert make_life.check() == []
    made = sorted({name.split("/")[0] for name in make_life.FILES})
    assert made == sorted(
        {*scene.BOXES, *tense.BOXES, "sable-with-bryony", *adults.BOXES, *adults.LATER, *fourteen.BOXES, *card.BOXES}
    )  # fmt: skip


def test_the_scene_plays_as_told(tmp_path, capsys):
    to = tmp_path / "scene"
    assert scene.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 0
    said = json.loads((to / "scene.json").read_text())
    assert said["wrong"] == []
    boxes = said["boxes"]
    assert {n: b["holder"] for n, b in boxes.items()} == {
        "marit": "marit", "wren": "marit", "tobias": "marit", "imani": "marit",
        "tobias-own": "tobias", "imani-own": "imani", "leo": "dana", "ravi": "ravi",
    }  # fmt: skip
    assert all(b["verify"].startswith("the chain holds") for b in boxes.values())
    assert {n for n, b in boxes.items() if b["held_for"]} == {
        "wren",
        "tobias",
        "imani",
        "leo",
    }
    assert said["said"]["wren"] == {"seals": 1, "same_key": True}
    tobias = said["said"]["tobias"]
    assert set(tobias["found"].values()) == {"empty"} and len(tobias["found"]) == 4
    assert tobias["named_by"] == [] and (tobias["his_key"], tobias["her_key"]) == (1, 0)
    assert said["said"]["imani"] == {
        "held_box_seals": 2, "own_box_seals": 1, "received": 1, "held_box_ends": "handed-over",
        "rewritten_copy_verifies_alone": True,
        "held_to_the_package": {"as it was": ["holds"], "rewritten": ["rewritten"]},
    }  # fmt: skip
    assert said["said"]["leo"] == {"received": 1, "ravis_notes_travelled": False, "leo_box_seals": 0}  # fmt: skip
    printed = capsys.readouterr().out
    assert "received, not sealed by you" in printed and "went otherwise" not in printed


def test_a_scene_is_played_outside_the_repository_and_never_over_another(tmp_path):
    life = str(HERE / "life")
    assert scene.main(["run", "--life", life, "--to", str(HERE / "out")]) == 2
    assert scene.main(["run", "--life", life, "--to", str(tmp_path)]) == 2
    assert (
        scene.main(["run", "--life", str(tmp_path), "--to", str(tmp_path / "x")]) == 2
    )
    assert scene.main(["run"]) == 2 and scene.main([]) == 2
    assert not (HERE / "out").exists()


def test_the_tense_scene_plays_as_told(tmp_path, capsys):
    to = tmp_path / "tense"
    assert tense.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 0
    said = json.loads((to / "tense.json").read_text())
    assert said["wrong"] == []
    assert all(
        b["verify"].startswith("the chain holds") for b in said["boxes"].values()
    )
    assert said["said"]["sable"] == {
        "his_asks": 4, "found": ["empty"], "guess_confirmed": True, "her_key": 1, "his_key": 0,
        "cards_differ": True, "answers_whoever_holds_it": True,
    }  # fmt: skip
    assert said["said"]["guardian"] == {
        "claim_to_hold": ["sable", "sable-with-bryony"],
        "old_holder_seals_after_order_by_his_clock": 1, "handed_over": False,
        "order_holds_alone": True, "hold_the_order": ["sable-with-bryony"],
        "court_sent_to": 3, "served_on_the_old_holder": True,
        "old_box_seals_its_record_puts_after": None, "had_he_taken_it": 1,
        "sable_has_the_order": True,
    }  # fmt: skip
    assert said["said"]["kit"] == {
        "before": "empty", "received": 1, "kits_notes_travelled": False, "rosa_asked_again": "empty",
    }  # fmt: skip
    printed = capsys.readouterr().out
    assert (
        printed.count("received, not sealed by you") == 4
        and "went otherwise" not in printed
    )
    assert (
        tense.main(["run", "--life", str(HERE / "life"), "--to", str(HERE / "out")])
        == 2
    )
    assert tense.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 2
    assert tense.main(["run"]) == 2 and not (HERE / "out").exists()


def test_what_a_minor_keeps_alone_is_in_no_box_their_caregiver_holds():
    held = dict(make_life.FILES)
    held["sable/appointments.md"] += "\nThe nurse wants to see her.\n"
    held["kit/clinic-letters.md"] += "\nBring the glucose log.\n"
    old, make_life.FILES = make_life.FILES, held
    try:
        wrong = make_life.check()
        assert any("sable/appointments.md says 'nurse'" in w for w in wrong)
        assert any("kit/clinic-letters.md says 'glucose'" in w for w in wrong)
    finally:
        make_life.FILES = old


def test_the_adults_scene_plays_as_told(tmp_path, capsys):
    to = tmp_path / "adults"
    assert adults.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 0
    said = json.loads((to / "adults.json").read_text())
    assert said["wrong"] == []
    assert all(
        b["verify"].startswith("the chain holds") for b in said["boxes"].values()
    )
    assert said["said"]["agnes"] == {
        "claim_to_hold": ["agnes-with-dorian", "agnes-with-petra"],
        "by_her_word_and_the_finding": ["agnes-with-petra"],
        "her_word_holds_alone": True, "finding_holds_alone": True, "sent_while_well": True,
    }  # fmt: skip
    assert said["said"]["key"] == {
        "seals_under_her_key": 3, "told_apart_by_the_record": 0, "before_the_finding": 1,
        "after_the_finding": 2, "first_word_still_holds": True,
    }  # fmt: skip
    assert said["said"]["marcus"] == {
        "card_signed_by_him": True, "mother_holds_his_word": False, "boxes_held_for_him": 0,
        "his_box_untouched_meanwhile": True, "took_in_on_waking": True,
        "hospital_record_holds": True, "his_own_seals": 2,
    }  # fmt: skip
    assert "went otherwise" not in capsys.readouterr().out
    assert adults.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 2
    assert (
        adults.main(["run", "--life", str(HERE / "life"), "--to", str(HERE / "out")])
        == 2
    )
    assert adults.main(["run"]) == 2 and not (HERE / "out").exists()


def test_leo_at_fourteen_plays_as_told(tmp_path, capsys):
    to = tmp_path / "fourteen"
    assert fourteen.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 0
    said = json.loads((to / "fourteen.json").read_text())
    assert said["wrong"] == []
    assert all(
        b["verify"].startswith("the chain holds") for b in said["boxes"].values()
    )
    assert said["said"] == {
        "parents_disagree": True, "either_parent_has_the_others_word": 0,
        "count_reached_father": False, "nurse_reached_a_house": False,
        "taken_in": {
            "leo-own": {"leo-at-fourteen": 1, "ravi-later": 1, "asthma-nurse": 1},
            "leo-at-fourteen": {"leo-own": 1}, "ravi-later": {"leo-own": 1}, "asthma-nurse": {},
        },
        "his_seals_under_his_key": 2, "under_his_mothers": 0,
        "parents_records_hold": {"leo-at-fourteen": "holds", "ravi-later": "holds"},
    }  # fmt: skip
    assert "went otherwise" not in capsys.readouterr().out
    assert fourteen.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 2
    assert fourteen.main(["run"]) == 2


def test_what_he_was_sent_is_askable_only_when_written_out_as_pages(tmp_path, capsys):
    to = tmp_path / "askable"
    assert askable.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 0
    got = json.loads((to / "askable.json").read_text())
    assert list(got) == ["as it is", "packages dropped", "written out"]
    asked = list(askable.ASKED)
    as_is = got["as it is"]
    assert as_is[asked[1]]["where"] == "" and as_is[asked[2]]["where"] == "mine.md:6", (
        "asked of the brown inhaler, it serves his line about the purple one"
    )
    assert not any(v["says_whose"] for v in as_is.values())
    dropped = got["packages dropped"]
    assert (
        dropped[asked[2]]["where"].endswith(".pkg:1")
        and not dropped[asked[2]]["readable"]
    )
    written = got["written out"]
    assert [written[q]["where"] for q in asked] == [
        "received/ravi-to-leo.md:5", "received/dana-to-leo.md:5",
        "received/ravi-to-leo.md:5", "received/nurse-to-leo.md:5",
    ]  # fmt: skip
    assert all(v["readable"] and v["says_whose"] for v in written.values())
    capsys.readouterr()
    assert askable.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 2
    assert askable.main(["run"]) == 2


def test_an_unknown_signer_can_make_a_ward_more_careful_and_never_less():
    ring = {"k-surgery": "the surgery"}
    inner = {"from": "k-him", "wraps": None}
    assert card.standing(inner, ring) == ("unknown", "")
    assert card.standing({"from": "k-partner", "wraps": inner}, ring) == ("unknown", "")
    assert card.standing({"from": "k-surgery", "wraps": inner}, ring) == (
        "vouched",
        "the surgery",
    )
    assert card.standing(inner, {**ring, "k-him": "him"}) == ("enrolled", "him")
    assert card.done("caution", "unknown") == "honoured"
    assert (
        card.done("all-clear", "unknown") == "held"
        and card.done("grant", "unknown") == "held"
    )
    assert card.done("all-clear", "vouched") == "honoured" and card.done("grant", "enrolled") == "honoured"  # fmt: skip
    assert card.done("fact", "unknown").startswith("shown, as said by") and card.done("fact", "vouched") == "shown"  # fmt: skip
    assert (
        card.done("caution", "broken") == "honoured"
        and card.done("grant", "broken") == "held"
    )


def test_the_card_scene_plays_as_told(tmp_path, capsys):
    to = tmp_path / "card"
    assert card.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 0
    doc = json.loads((to / "card.json").read_text())
    assert doc["wrong"] == [] and all(
        v.startswith("the chain holds") for v in doc["boxes"].values()
    )
    said = doc["said"]
    assert said["from_jun"] == {"caution": "honoured", "fact": "shown, as said by a signer not known", "grant": "held"}  # fmt: skip
    assert said["from_someone"] == {"all-clear": "held", "grant": "held"}
    assert said["from_the_surgery"] == {
        "caution": "honoured",
        "fact": "shown",
        "grant": "honoured",
    }
    assert said["sable"] == {
        "her_guardian_of_old": {"all-clear": "held", "grant": "held"},
        "her_own": {"all-clear": "held", "grant": "held"},
        "the_court": {"grant": "honoured"}, "called": "Bryony Okonjo",
    }  # fmt: skip
    assert (
        said["penicillin_withheld_throughout"] is True
        and said["an_unknown_all_clear_taken"] is False
    )
    assert (
        said["after_he_enrols"]["grant"] == "honoured"
        and said["the_second_card_then"] == "unknown"
    )
    assert said["lines_on_the_wards_record"] == len(doc["read"]) - 3 == 13
    assert "went otherwise" not in capsys.readouterr().out
    assert card.main(["run", "--life", str(HERE / "life"), "--to", str(to)]) == 2
    assert card.main(["run"]) == 2
