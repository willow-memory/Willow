"""ask-parts's tests: a question that asks two things is split where each side
asks, never elsewhere; each part is asked by the kernel's own rule; nothing
is written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-11-16T00:00:00Z"]
HEADSTONE = "what did colleen say about mam's headstone, how much was my half"
HALF = "how much was my half"

spec = importlib.util.spec_from_file_location("ask_parts", HERE / "ask_parts.py")
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    (pile / "Mail").mkdir(parents=True)
    (pile / "Mail" / "stone-done.eml.txt").write_text(
        "From: Colleen\nDate: 2024-04-22\nSubject: Stone done, photos\n\n"
        "Your half is 725 euro, whenever you can.\n"
    )
    (pile / "Mail" / "headstone-2022.eml.txt").write_text(
        "From: Colleen\nDate: 2022-03-02\nSubject: Mam's headstone\n\n"
        "Colleen says the headstone for Mam will be granite, from the mason in Ennis.\n"
    )
    (pile / "Mail" / "garden.eml.txt").write_text(
        "From: Pat\nDate: 2024-05-01\n\nThe garden gate is painted green.\n"
    )
    (pile / "Mail" / "tea.eml.txt").write_text(
        "From: Pat\nDate: 2024-05-02\n\nThe tea cost 4 euro.\n"
    )
    b = tmp_path / "box"
    key = tmp_path / "k"
    done = run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(key),
        *NOW,
    )
    assert done.returncode == 0, done.stderr
    return b


def test_the_headstone_question_is_two_parts():
    assert ap.parts(HEADSTONE) == [
        "what did colleen say about mam's headstone",
        HALF,
    ]


def test_a_question_of_one_part_is_itself_as_typed():
    for q in (
        "scone recipe",
        "salt and pepper",
        "tom and jerry's address",
        "  Salt, and pepper?  ",
    ):
        assert ap.parts(q) == [q]


def test_each_side_must_ask_in_its_own_right():
    # the second side opens with no question word: it stays in the first part
    assert ap.parts("what is salt and pepper") == ["what is salt and pepper"]
    assert ap.parts("what did she buy, tea and biscuits") == [
        "what did she buy, tea and biscuits"
    ]
    # the first side opens with no question word
    assert ap.parts("tell me about salt and how much it costs") == [
        "tell me about salt and how much it costs"
    ]
    # a side of function words only is no part: "how much" has nothing to hold
    assert ap.parts("what is it, and how much") == ["what is it, and how much"]
    assert ap.parts("what did colleen say, how much") == [
        "what did colleen say, how much"
    ]
    assert ap.parts("what is it, how much was my half") == [
        "what is it, how much was my half"
    ]


def test_each_break_word_and_three_parts():
    assert ap.parts("what is salt and what is pepper") == [
        "what is salt",
        "what is pepper",
    ]
    assert ap.parts("when is the vet; how much does it cost") == [
        "when is the vet",
        "how much does it cost",
    ]
    assert ap.parts("when is the vet also how much does it cost") == [
        "when is the vet",
        "how much does it cost",
    ]
    assert ap.parts("when is the vet, and also how much does it cost") == [
        "when is the vet",
        "how much does it cost",
    ]
    assert ap.parts(
        "WHAT did colleen say, AND how much was my half; when was it paid?"
    ) == [
        "WHAT did colleen say",
        "how much was my half",
        "when was it paid?",
    ]


def test_a_part_that_is_cut_off_rejoins_the_one_before_it():
    q = "what did she buy, tea and biscuits, and how much was my half"
    assert ap.parts(q) == ["what did she buy, tea and biscuits", "how much was my half"]


def test_nothing_inside_quotes_is_split():
    q = 'what did she say about "salt, and how much" pepper'
    assert ap.parts(q) == [q]
    q = "what did she say about “salt; and how much” pepper"
    assert ap.parts(q) == [q]
    # a quote left open is not ours to cut
    q = 'what did she say about "salt, and how much pepper'
    assert ap.parts(q) == [q]
    # outside the quote it still splits
    assert ap.parts('what is "tom and jerry" and how much was my half') == [
        'what is "tom and jerry"',
        HALF,
    ]


def test_the_kernel_loses_the_half_whole_and_finds_it_asked_alone(tmp_path):
    b = box(tmp_path)
    whole = json.loads(
        run(str(KERNEL), "bite", "--box", str(b), *NOW, HEADSTONE).stdout
    )
    assert not any("725" in s["text"] for s in whole["served"])
    alone = json.loads(run(str(KERNEL), "bite", "--box", str(b), *NOW, HALF).stdout)
    assert [s["where"] for s in alone["served"]] == ["Mail/stone-done.eml.txt:5"]


def test_asking_each_part_serves_what_the_whole_question_lost(tmp_path):
    b = box(tmp_path)
    got = run(str(HERE / "ask_parts.py"), "--box", str(b), HEADSTONE)
    doc = json.loads(got.stdout)
    assert got.returncode == 0 and doc["state"] == "populated"
    first, second = doc["parts"]
    assert first["part"] == "what did colleen say about mam's headstone"
    assert first["served"][0]["where"].startswith("Mail/headstone-2022.eml.txt")
    assert [s["where"] for s in second["served"]] == ["Mail/stone-done.eml.txt:5"]
    assert "725" in second["served"][0]["text"]


def test_a_part_is_asked_alone_not_with_the_first_parts_words(tmp_path):
    # with the first part's words added, "half" is one of five content words
    # and the kernel serves nothing: the part is asked as it stands
    b = box(tmp_path)
    with_context = json.loads(
        run(
            str(KERNEL), "bite", "--box", str(b), *NOW, "colleen say mam headstone half"
        ).stdout
    )
    assert not any("725" in s["text"] for s in with_context["served"])
    got = json.loads(run(str(HERE / "ask_parts.py"), "--box", str(b), HEADSTONE).stdout)
    assert got["parts"][1]["part"] == HALF


def test_each_part_is_what_the_kernels_bite_serves_and_its_key_is_the_kernels(tmp_path):
    b = box(tmp_path)
    got = json.loads(run(str(HERE / "ask_parts.py"), "--box", str(b), HEADSTONE).stdout)
    # biting the last part through the kernel serves the same passages, so a
    # proposal citing them is allowed; ask-parts itself wrote nothing
    for part in got["parts"]:
        bite = json.loads(
            run(str(KERNEL), "bite", "--box", str(b), *NOW, part["part"]).stdout
        )
        assert [s["id"] for s in bite["served"]] == [s["id"] for s in part["served"]]
        assert bite["bite_key"] == part["bite_key"]

    # the box's last bite is the last part: its passages can be cited, the
    # first part's, served by an earlier bite, can't
    def propose(cite: str) -> str:
        prop = {
            "path": "money/stone.md",
            "data": "725",
            "cites": [cite],
            "claim": "mail",
        }
        f = tmp_path / "p.jsonl"
        f.write_text(json.dumps(prop) + "\n")
        return run(
            str(KERNEL), "propose", "--box", str(b), *NOW, "--file", str(f)
        ).stdout

    assert propose(got["parts"][1]["served"][0]["id"]).startswith("pass")
    assert "didn't serve" in propose(got["parts"][0]["served"][0]["id"])


def test_it_writes_nothing(tmp_path):
    b = box(tmp_path)
    before = (b / "record.jsonl").read_bytes()
    run(str(HERE / "ask_parts.py"), "--box", str(b), HEADSTONE)
    run(str(HERE / "ask_parts.py"), HEADSTONE)
    assert (b / "record.jsonl").read_bytes() == before


def test_a_part_nothing_holds_leaves_the_exit_to_the_person(tmp_path):
    b = box(tmp_path)
    got = run(
        str(HERE / "ask_parts.py"),
        "--box",
        str(b),
        "how much was my half, when does the frost come",
    )
    doc = json.loads(got.stdout)
    assert got.returncode == 42 and doc["state"] == "partial"
    assert [p["state"] for p in doc["parts"]] == ["populated", "empty"]
    none = run(str(HERE / "ask_parts.py"), "--box", str(b), "when does the frost come")
    assert none.returncode == 42 and json.loads(none.stdout)["state"] == "empty"


def test_without_a_box_it_prints_the_parts():
    got = run(str(HERE / "ask_parts.py"), HEADSTONE)
    assert got.returncode == 0
    assert json.loads(got.stdout) == {"parts": ap.parts(HEADSTONE)}
    assert run(str(HERE / "ask_parts.py"), "the of and").returncode == 42


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in ([], ["a", "b"], ["--box"], ["--box", "", "tea"], ["?!"]):
        got = run(str(HERE / "ask_parts.py"), *argv)
        assert got.returncode == 2, argv
    assert "ask_parts.py" in run(str(HERE / "ask_parts.py")).stderr
    got = run(
        str(HERE / "ask_parts.py"), "--box", str(tmp_path), "how much was my half"
    )
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_their_words_list_is_read_for_each_part_and_a_bad_one_is_refused(tmp_path):
    b = box(tmp_path)
    words = tmp_path / "words.txt"
    words.write_text("share = half\n")
    words.chmod(0o600)
    cfg = b / "kernel.json"
    cfg.write_text(cfg.read_text().replace("}", f', "words": "{words}"}}'))
    got = json.loads(
        run(str(HERE / "ask_parts.py"), "--box", str(b), "what is the share").stdout
    )
    assert [s["where"] for s in got["parts"][0]["served"]] == [
        "Mail/stone-done.eml.txt:5"
    ]
    words.chmod(0o644)
    bad = run(str(HERE / "ask_parts.py"), "--box", str(b), "what is the share")
    assert bad.returncode == 2 and "readable beyond its owner" in bad.stderr
