"""forge: a sentence in, the add-ons it names or means out, as a report and
as a plan the Forge reads; the settled forks and the stack to the kernel's
door, for the person to seal; what they sealed read back by both sides. The
cards are this willow's own, read beside the script; the box is a fresh one
in a scratch folder. The tests seal with the box's key, as the person would;
the script never does. The report contract is held here the way
test_contract.py holds the stdlib report add-ons, since a deps add-on's
tests run alone."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KERNEL = ROOT / "kernel.py"
SCRIPT = HERE / "suggest.py"

spec = importlib.util.spec_from_file_location("willow_forge_suggest", SCRIPT)
suggest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suggest)

EMAIL = "I want to read my email about the flat and know when the boiler is due"
#: a want no card name or alias line reaches, which similar's search can point at
COUNT = "count how often each suggestion was sealed or declined"
#: a want whose one scan hit (`against`, by an ordinary word) the search doubts
MODEL = "score a model against the answers the person sealed"
#: words nothing here holds, by name, by alias or by the search
NONSENSE = "qqqq zzzz kkwq"
HEAD = re.compile(r"[a-z0-9-]+: (?:populated|empty|unreachable), \S.*")
ROW = re.compile(r"  \S.*")


def run(*argv: str) -> subprocess.CompletedProcess:
    """The script, with no defaults unless the test names a list: a test
    about a word or the search then sees only what the words reached."""
    if argv[:1] in (("suggest",), ("propose",), ("next",)) and "--defaults" not in argv:
        argv = (*argv, "--defaults", "none")
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "flat.txt").write_text("The boiler service is due in March.\n")
    box = tmp_path / "box"
    got = k(
        "init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k.key")
    )
    assert got.returncode == 0, got.stderr
    return box


def rows(box: Path) -> list[dict]:
    return [json.loads(ln) for ln in (box / "record.jsonl").read_text().splitlines()]


def holds_the_contract(
    text: subprocess.CompletedProcess, data: subprocess.CompletedProcess
) -> dict:
    """test_contract.py's report assertions, on one run as text and one as JSON."""
    assert text.returncode == data.returncode, "--json changes nothing but the form"
    doc = json.loads(data.stdout)
    assert text.stdout.rstrip("\n") == suggest.report_text(doc), (
        "printed the same from its JSON"
    )
    return holds_the_shape(doc, text.returncode)


def holds_the_shape(doc: dict, code: int) -> dict:
    """The contract's assertions on one report and its exit code: for a verb
    that writes, which can't be run twice for the same report."""
    assert set(doc) == {"addon", "state", "said", "groups"} and doc["addon"] == "forge"
    head, *body = suggest.report_text(doc).splitlines()
    assert HEAD.fullmatch(head) and "\n" not in doc["said"], head
    found = [r for g in doc["groups"] for r in g["rows"]]
    names = [g["name"] for g in doc["groups"]]
    assert None not in names[1:], "rows of no group come first"
    assert all(g["rows"] for g in doc["groups"]), "an empty group isn't printed"
    assert all(
        set(r) == {"where", "what"}
        and r["where"].strip()
        and "\n" not in r["where"] + r["what"]
        for r in found
    )
    assert all(ROW.fullmatch(ln) or ln.startswith("## ") for ln in body), body
    state = doc["state"]
    assert (state == "populated") == bool(found), "populated is having rows"
    assert {
        "empty": code == 0,
        "unreachable": code == 42,
        "populated": code in (0, 42),
    }[state], (state, code)
    return doc


def suggested(
    box: Path, sentence: str = EMAIL
) -> tuple[subprocess.CompletedProcess, dict]:
    text = run("suggest", sentence, "--box", str(box))
    data = run("suggest", sentence, "--box", str(box), "--json")
    return text, holds_the_contract(text, data)


def proposed(box: Path, *choose: str, sentence: str = EMAIL) -> dict[str, str]:
    """`propose` with the choices given, its report held; {path: subject}."""
    argv = [
        "propose",
        sentence,
        "--box",
        str(box),
        *[a for c in choose for a in ("--choose", c)],
    ]
    data = run(*argv, "--json")  # once: propose writes
    assert data.returncode == 42, data.stderr
    doc = holds_the_shape(json.loads(data.stdout), data.returncode)
    assert doc["groups"][0]["name"] is None
    return {r["where"]: r["what"].split()[0] for r in doc["groups"][0]["rows"]}


def seal_all(box: Path, waiting: dict[str, str]) -> None:
    for subj in waiting.values():
        got = k("seal", "--box", str(box), subj)
        assert got.returncode == 0, got.stderr


# ── refusals ──────────────────────────────────────────────────────────────────


def test_no_arguments_is_refused_with_the_name():
    got = run()
    assert got.returncode == 2 and "suggest.py" in got.stderr


def test_a_stray_argument_is_refused(box):
    got = run("suggest", EMAIL, "--box", str(box), "--stray", "more")
    assert got.returncode == 2 and "suggest.py" in got.stderr


def test_a_folder_that_is_not_a_box_is_refused(tmp_path):
    got = run("suggest", EMAIL, "--box", str(tmp_path))
    assert got.returncode == 2 and "not a box" in got.stderr


def test_a_record_that_does_not_verify_is_refused(box):
    rec = box / "record.jsonl"
    rec.write_text(
        rec.read_text()
        .replace('"kind": "boot"', '"kind": "boat"')
        .replace('"kind":"boot"', '"kind":"boat"')
    )
    for verb in ("suggest", "propose"):
        got = run(verb, EMAIL, "--box", str(box))
        assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_card_that_will_not_read_is_refused_not_a_traceback(box, monkeypatch):
    card_box = pytest.importorskip("forge.card_box")
    card_table = pytest.importorskip("forge.card_table")

    def broken(root):
        raise card_table.CardTableError(
            "adapters/stdlib/x/README.md: no willow-addon header"
        )

    monkeypatch.setattr(card_box, "CardBox", broken)
    assert suggest.main(["suggest", EMAIL, "--box", str(box)]) == 2


def test_without_forge_play_the_report_is_unreachable_and_says_the_fix(
    box, monkeypatch, capsys
):
    monkeypatch.setattr(suggest, "forge", lambda: None)
    assert suggest.main(["suggest", EMAIL, "--box", str(box)]) == 42
    assert capsys.readouterr().out.startswith(
        "forge: unreachable, forge-play 0.10 or newer is not installed"
    )
    assert suggest.main(["propose", EMAIL, "--box", str(box), "--json"]) == 42
    assert json.loads(capsys.readouterr().out)["state"] == "unreachable"


# ── suggest ───────────────────────────────────────────────────────────────────


def test_the_twenty_lines_are_the_stack_add_ons_word_for_word():
    mine = ast.parse(SCRIPT.read_text())
    theirs = ast.parse(
        # the path in one string: test-impact reads a bare "stack.py" as every
        # file so named, and demo/bernadette has one that imports what_changed.py
        (ROOT / "adapters/stdlib/stack/stack.py").read_text(encoding="utf-8")
    )

    def source(tree, name):
        f = next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name
        )
        return ast.unparse(f)

    assert source(mine, "report_text") == source(theirs, "report_text")


def test_a_sentence_with_forks_is_populated_waits_on_you_and_writes_nothing(box):
    before = len(rows(box))
    text, doc = suggested(box)
    assert text.returncode == 42 and doc["said"] == "2 forks wait on you"
    assert [g["name"] for g in doc["groups"]] == ["fork “email”", "fork “due”"]
    assert len(rows(box)) == before, "suggest writes nothing to the record"


def test_one_card_named_alone_is_a_step_and_exit_0(box):
    text, doc = suggested(box, "a merkle proof of one row")
    assert text.returncode == 0 and doc["said"] == "1 step, nothing waits on you"
    assert [g["name"] for g in doc["groups"]] == ["steps"]


def test_one_fork_waits_in_the_singular(box):
    got = run("suggest", "my email", "--box", str(box))
    assert got.returncode == 42 and got.stdout.startswith(
        "forge: populated, 1 fork waits on you"
    )


def test_nothing_named_and_nothing_close_is_empty_and_exit_0(box):
    text, doc = suggested(box, NONSENSE)
    assert (
        text.returncode == 0
        and doc["state"] == "empty"
        and "search-words.txt" in doc["said"]
    )


def test_a_sentence_that_names_no_card_gets_the_close_fork(box):
    """No name and no alias line: similar's search points, and what it points
    at is a fork, never a step, each row saying so, the first recommended."""
    before = len(rows(box))
    text, doc = suggested(box, COUNT)
    assert text.returncode == 42 and doc["said"] == "1 fork waits on you"
    (g,) = doc["groups"]
    assert g["name"].startswith(
        "fork “close”: nothing named that the search agrees with"
    )
    names = [r["what"].split(":", 1)[0] for r in g["rows"]]
    assert (
        "assistant-scores" in names
        and names[-2:] == ["none", "not-now"]
        and len(names) <= 5
    )
    assert all("close, not named: " in r["what"] for r in g["rows"][:-2])
    assert g["rows"][0]["what"].endswith(
        "; recommended, the search's first"
        "; no confidence yet: 0 of 5 blind close picks sealed on this matcher"
    ), "and says it has no confidence, and why"
    assert not any(
        "recommended, the search's first" in r["what"] for r in g["rows"][1:]
    )
    assert "you named it" not in " ".join(r["what"] for r in g["rows"]), (
        "nothing named it"
    )
    assert len(rows(box)) == before, "suggest writes nothing to the record"


def test_a_card_named_by_an_ordinary_word_the_search_puts_nowhere_near_is_asked_about(
    box,
):
    """`against` is a card, and "against" is an ordinary word here; the search
    puts that card nowhere near these words, so it is no step: it joins the
    close fork beside what the search does put near, saying why."""
    text, doc = suggested(box, MODEL)
    assert text.returncode == 42 and [g["name"] for g in doc["groups"]] == [
        "fork “close”: nothing named that the search agrees with; these are close to what you said"
    ]
    rows = {r["what"].split(":", 1)[0]: r["what"] for r in doc["groups"][0]["rows"]}
    assert list(rows)[0] == "model-exam" and list(rows)[-2:] == ["none", "not-now"]
    assert rows["against"].endswith(
        "named, but not close: the search puts it nowhere near your words"
    )
    assert "; recommended, the search's first; no confidence yet" in rows["model-exam"]


def test_a_named_card_the_search_agrees_with_stays_a_step(box, monkeypatch, capsys):
    """And with no search to ask, a named card is a step as before."""
    text, doc = suggested(box, "a merkle proof of one row")
    assert [g["name"] for g in doc["groups"]] == ["steps"]
    monkeypatch.setattr(suggest, "wanting", lambda: None)
    assert suggest.main(["suggest", MODEL, "--box", str(box)]) == 0
    assert "against: " in capsys.readouterr().out


def test_the_close_fork_carries_its_recommendation_and_no_confidence(box):
    plan_shape = pytest.importorskip("forge.plan_shape")
    decision_extract = pytest.importorskip("forge.decision_extract")
    d = json.loads(run("suggest", COUNT, "--box", str(box), "--plan").stdout)
    assert d["steps"] == [], "what the search points at is never a step"
    doc = plan_shape.validate(d["plan"])
    (fork,) = [e for e in doc.entries if isinstance(e, plan_shape.Fork)]
    labels = [o.label for o in fork.options]
    assert fork.recommended == labels[0] and fork.confidence is None, "no made-up 0.5"
    assert labels[-1] == "none" and fork.resolves["none"] == ()
    assert fork.decision_type.startswith("willow-close-")
    ex = decision_extract.extract(doc)
    assert len(ex.decisions) == 1 and not ex.refused, ex.to_dict()


def test_a_close_seal_is_its_sentences_own(box):
    waiting = proposed(box, "close=assistant-scores", sentence=COUNT)
    (path,) = [p for p in waiting if p != "forge/stack.md"]
    assert path.startswith("forge/decisions/willow-close-")
    prop = json.loads((box / "proposals" / f"{waiting[path][9:]}.json").read_text())
    data = json.loads(prop["data"])
    assert data["chose"] == "assistant-scores" and data["sentence"] == COUNT
    assert "none" not in data["over"] and data["card"]["name"] == "assistant-scores"
    seal_all(box, {path: waiting[path]})
    text, doc = suggested(box, COUNT)
    assert text.returncode == 0 and doc["said"] == "1 step, nothing waits on you"
    assert "you sealed it for “close”" in doc["groups"][0]["rows"][0]["what"]
    other, odoc = suggested(box, "count how often each suggestion was declined")
    assert other.returncode == 42 and odoc["groups"][0]["name"].startswith(
        "fork “close”"
    )


def test_none_sealed_keeps_the_miss_and_runs_nothing(box):
    got = run("propose", COUNT, "--box", str(box), "--choose", "close=none", "--json")
    assert got.returncode == 42, got.stderr
    doc = holds_the_shape(json.loads(got.stdout), got.returncode)
    assert doc["said"].endswith("no stack: nothing settled runs")
    (row,) = doc["groups"][0]["rows"]
    assert row["where"].startswith("forge/decisions/willow-close-")
    subj = row["what"].split()[0]
    data = json.loads(
        json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())["data"]
    )
    assert data["chose"] == "none" and data["card"] is None and data["over"]
    text, before = suggested(box, COUNT)
    assert text.returncode == 42, "not settled before the seal"
    assert k("seal", "--box", str(box), subj).returncode == 0
    text, after = suggested(box, COUNT)
    assert text.returncode == 0 and after["state"] == "empty"
    assert after["said"].startswith(
        "you sealed that no card close to these words does it (row "
    )


def test_a_close_proposal_keeps_what_was_shown(box):
    shown = json.loads(run("suggest", COUNT, "--box", str(box), "--plan").stdout)
    offered = [o["name"] for o in shown["forks"]["close"] if o["name"] != "none"]
    waiting = proposed(box, f"close={offered[1]}", sentence=COUNT)
    (path,) = [p for p in waiting if p != "forge/stack.md"]
    data = json.loads(
        json.loads((box / "proposals" / f"{waiting[path][9:]}.json").read_text())[
            "data"
        ]
    )
    assert data["offered"] == offered and data["recommended"] == offered[0]
    assert data["rank"] == 2 and set(data["matcher"]) == {"ranks"}
    assert len(data["matcher"]["ranks"]) == 64
    assert data["blind"] is False and "shown" not in data, (
        "in view, as the search had it"
    )


def scored(box: Path) -> tuple[subprocess.CompletedProcess, dict]:
    text = run("scores", "--box", str(box))
    data = run("scores", "--box", str(box), "--json")
    return text, holds_the_contract(text, data)


def test_scores_count_where_each_sealed_pick_fell_and_only_sealed_ones(box):
    text, doc = scored(box)
    assert text.returncode == 0 and doc["state"] == "empty"
    shown = json.loads(run("suggest", COUNT, "--box", str(box), "--plan").stdout)
    second = [o["name"] for o in shown["forks"]["close"]][1]
    took = proposed(box, f"close={second}", sentence=COUNT)
    seal_all(box, {p: s for p, s in took.items() if p != "forge/stack.md"})
    other = "count how often each suggestion was declined"
    miss = run("propose", other, "--box", str(box), "--choose", "close=none", "--json")
    subj = json.loads(miss.stdout)["groups"][0]["rows"][0]["what"].split()[0]
    unsealed = "count how often each suggestion was sealed"
    assert (
        run("propose", unsealed, "--box", str(box), "--choose", "close=none").returncode
        == 42
    )
    assert k("seal", "--box", str(box), subj).returncode == 0
    before = len(rows(box))
    text, doc = scored(box)
    assert text.returncode == 0 and len(rows(box)) == before, "scores writes nothing"
    assert (
        doc["said"] == "2 forks settled by your seal: 2 close, the first taken 0 of 2"
    )
    assert [g["name"] for g in doc["groups"]] == [
        "close: by rank",
        "close: by matcher",
        "close: its confidence",
        "each",
    ]
    assert doc["groups"][2]["rows"] == [
        {
            "where": "now",
            "what": "no confidence yet: 0 of 5 blind close picks sealed on this matcher",
        },
        {
            "where": "in view",
            "what": "its first taken 0 of 2 with the recommendation in view",
        },
    ], "both asked in view: neither counts toward a confidence, and none is scored"
    by_rank = {r["where"]: r["what"] for r in doc["groups"][0]["rows"]}
    assert by_rank["rank 1"].endswith(": 0 of 2") and by_rank["rank 2"].endswith(
        ": 1 of 2"
    )
    assert by_rank["none"] == "none of them: 1 of 2"
    (m,) = doc["groups"][1]["rows"]
    assert m["what"] == "the first taken 0 of 2"
    each = [r["what"] for r in doc["groups"][3]["rows"]]
    assert (
        each[0].startswith(f"“{COUNT}”: {second}, rank 2 of ") and "none of " in each[1]
    )


# ── the close fork's confidence: from your sealed picks, and scored ──────────


def picked(rank, *, matcher=None, kind="close", conf=None, blind=True) -> dict:
    """One sealed outcome as `outcomes` reads it, for `confidence` alone."""
    return {"kind": kind, "rank": rank, "confidence": conf, "blind": blind,
            "matcher": matcher or {"ranks": "r"}}  # fmt: skip


NOW = {"ranks": "r"}


def test_no_confidence_before_five_blind_close_picks_are_sealed_on_this_matcher():
    four = [picked(1)] * 4
    assert suggest.confidence(four, NOW) == (
        None,
        "no confidence yet: 4 of 5 blind close picks sealed on this matcher",
    )
    other = four + [picked(1, matcher={"ranks": "older"})]
    assert suggest.confidence(other, NOW)[0] is None, (
        "another matcher's pick counts not"
    )
    worded = four + [picked(1, kind="word")]
    assert suggest.confidence(worded, NOW)[0] is None, "a word's fork counts not"
    in_view = four + [picked(1, blind=False)] * 10
    assert suggest.confidence(in_view, NOW)[0] is None, (
        "a pick made with the recommendation in view counts not"
    )


def test_the_confidence_is_k_plus_one_over_n_plus_two_never_a_certainty():
    assert suggest.confidence([picked(1)] * 5, NOW) == (
        0.86,
        "confidence 0.86: its first taken 5 of 5 blind on this matcher",
    )
    four_of_five = [picked(1)] * 4 + [picked(None)]
    assert suggest.confidence(four_of_five, NOW)[0] == 0.71, "none is a miss"
    assert suggest.confidence([picked(1)] * 500, NOW)[0] == 0.99, "never 1"
    half = [picked(1)] * 3 + [picked(2)] * 3
    assert suggest.confidence(half, NOW)[0] == 0.5, "one half is said"


def test_under_half_says_no_confidence_and_why():
    two_of_five = [picked(1)] * 2 + [picked(2)] * 2 + [picked(None)]
    assert suggest.confidence(two_of_five, NOW) == (
        None,
        "no confidence: its first taken 2 of 5 blind on this matcher, under half",
    )


# ── blind forks: the pick that measures the search ──────────────────────────

#: wants no name or alias line reaches whose close forks are blind; COUNT's,
#: and the other sentences above, are asked in view
WANTS = [
    "count how often each suggestion was kept",
    "count how often each suggestion was chosen",
    "count how often each suggestion was skipped",
    "count how often each suggestion was used",
    "count how often each proposal was approved",
]
BLIND = "count how often each proposal was accepted"


def test_one_close_fork_in_five_is_blind_by_its_words_and_always_the_same():
    assert all(suggest.blind(w) for w in WANTS + [BLIND])
    assert not any(suggest.blind(s) for s in (COUNT, MODEL, EMAIL))
    many = [f"want number {i}" for i in range(2000)]
    assert 300 < sum(map(suggest.blind, many)) < 500, "about one in five"
    names = ["a", "b", "c"]
    assert sorted(suggest.shuffled(BLIND, names)) == names, "the same cards"
    assert suggest.shuffled(BLIND, names) == suggest.shuffled(BLIND, names[::-1]), (
        "an order of its own, whatever order the search gave"
    )


def searchs_order(sentence: str, shown: list[str]) -> list[str]:
    """The cards of a fork in the search's own order, which a blind one hides."""
    return [f["name"] for f in suggest.searched(sentence) if f["name"] in shown]


def plan_of(box: Path, sentence: str) -> dict:
    return json.loads(run("suggest", sentence, "--box", str(box), "--plan").stdout)


def data_of(box: Path, took: dict) -> tuple[dict, dict]:
    """A close fork's proposal, as {path: subject} for seal_all, and its data."""
    (path,) = [p for p in took if p != "forge/stack.md"]
    prop = json.loads((box / "proposals" / f"{took[path][9:]}.json").read_text())
    return {path: took[path]}, json.loads(prop["data"])


def first_sealed(box: Path, sentence: str) -> None:
    """Take the search's first for a blind close fork, and seal it."""
    shown = [o["name"] for o in plan_of(box, sentence)["forks"]["close"]]
    first = searchs_order(sentence, shown)[0]
    waiting, data = data_of(box, proposed(box, f"close={first}", sentence=sentence))
    assert data["blind"] is True and data["rank"] == 1 and data["chose"] == first
    seal_all(box, waiting)


def test_a_blind_fork_says_so_recommends_nothing_and_hides_the_searchs_order(box):
    plan_shape = pytest.importorskip("forge.plan_shape")
    text, doc = suggested(box, BLIND)
    assert text.returncode == 42
    (g,) = doc["groups"]
    assert g["name"].startswith(f"fork “close”, {suggest.BLIND_SAID}: nothing named")
    assert not any("recommended" in r["what"] or "confidence" in r["what"]
                   for r in g["rows"]), "nothing in front of you to follow"  # fmt: skip
    cards = g["rows"][:-2]  # all but the two ways out, none and not-now
    assert all(r["what"].endswith(f"; {suggest.BLIND_ROW}") for r in cards), (
        "every card says the same of itself: the search's reasons would say its order"
    )
    assert not any("close, not named" in r["what"] or "usually means" in r["what"]
                   or "named, but not close" in r["what"] for r in cards)  # fmt: skip
    d = plan_of(box, BLIND)
    assert "hidden" not in d, "--plan prints all but what is kept from you"
    assert d["close"] == {"blind": True, "confidence": None, "said": suggest.BLIND_SAID}
    (fork,) = [e for e in plan_shape.validate(d["plan"]).entries
               if isinstance(e, plan_shape.Fork)]  # fmt: skip
    assert fork.recommended is None and fork.confidence is None
    shown = [o["name"] for o in d["forks"]["close"]]
    assert shown[-1] == "none" and shown[:-1] == suggest.shuffled(BLIND, shown[:-1])
    order = searchs_order(BLIND, shown)
    _, data = data_of(box, proposed(box, f"close={shown[0]}", sentence=BLIND))
    assert data["blind"] is True and data["shown"] == shown[:-1]
    assert data["offered"] == order and data["search_first"] == order[0]
    assert data["recommended"] is None, (
        "nothing was recommended, and the record says so"
    )
    assert data["rank"] == order.index(shown[0]) + 1, (
        "where it fell in the search's order"
    )


def test_five_sealed_blind_firsts_give_a_confidence_scored_on_blind_picks_alone(box):
    plan_shape = pytest.importorskip("forge.plan_shape")
    pytest.importorskip("forge.calibration")
    for want in WANTS:
        first_sealed(box, want)
    # asked in view, the next close fork says it, from the blind picks
    d = plan_of(box, COUNT)
    (fork,) = [e for e in plan_shape.validate(d["plan"]).entries
               if isinstance(e, plan_shape.Fork)]  # fmt: skip
    assert fork.confidence == 0.86 and fork.recommended == fork.options[0].label
    assert d["close"] == {
        "blind": False,
        "confidence": 0.86,
        "said": "confidence 0.86: its first taken 5 of 5 blind on this matcher",
    }
    text, doc = suggested(box, COUNT)
    assert doc["groups"][0]["rows"][0]["what"].endswith(
        "; recommended, the search's first; confidence 0.86: its first taken 5 of 5 blind on this matcher"
    )
    # you go with it, in view: kept, and neither counted nor scored
    waiting, data = data_of(
        box, proposed(box, f"close={fork.recommended}", sentence=COUNT)
    )
    assert data["confidence"] == 0.86 and data["blind"] is False and data["rank"] == 1
    seal_all(box, waiting)
    # blind, the 0.86 is kept unsaid, and you take the search's second
    shown = [o["name"] for o in plan_of(box, BLIND)["forks"]["close"]]
    second = searchs_order(BLIND, shown)[1]
    waiting, data = data_of(box, proposed(box, f"close={second}", sentence=BLIND))
    assert data["confidence"] == 0.86 and data["blind"] is True and data["rank"] == 2
    seal_all(box, waiting)
    text, doc = scored(box)
    trust = {r["where"]: r["what"] for r in doc["groups"][2]["rows"]}
    assert doc["groups"][2]["name"] == "close: its confidence"
    assert trust == {
        "now": "confidence 0.75: its first taken 5 of 6 blind on this matcher",
        "blind": "its first taken 5 of 6 blind",
        "in view": "its first taken 1 of 1 with the recommendation in view",
        # one said blind (0.86), and missed: (0.86 - 0)^2 = 0.7396
        "scored": "brier 0.740 over 1 said; mean said 0.86, its first taken 0.00",
    }


def test_the_matcher_is_known_by_what_it_ranks_not_by_its_bytes(monkeypatch):
    def search(names: list[str]):
        class Want:
            def find(self, sentence, top):
                return {"found": [{"name": n, "why": "x"} for n in names[:top]]}

        return lambda: Want

    monkeypatch.setattr(suggest, "wanting", search(["a", "b", "c"]))
    first = suggest.matcher()
    assert set(first) == {"ranks"} and len(first["ranks"]) == 64
    monkeypatch.setattr(suggest, "wanting", search(["a", "b", "c"]))
    assert suggest.matcher() == first, (
        "a new search that ranks the same keeps the count"
    )
    monkeypatch.setattr(suggest, "wanting", search(["b", "a", "c"]))
    assert suggest.matcher() != first, "one that moves a card starts a count of its own"
    monkeypatch.setattr(suggest, "wanting", lambda: None)
    assert suggest.matcher() == {"ranks": "absent"}


def test_a_words_fork_offers_none_and_keeps_what_was_shown(box):
    """An alias line can point wrong; saying so is an outcome. A word's fork
    has no recommendation: its order is only the scan's."""
    text, doc = suggested(box, "my email")
    (g,) = doc["groups"]
    assert [r["what"].split(":", 1)[0] for r in g["rows"]] == [
        "apple-mail",
        "mail",
        "none",
        "not-now",
    ]
    got = run(
        "propose", "my email", "--box", str(box), "--choose", "email=none", "--json"
    )
    assert got.returncode == 42, got.stderr
    rows_ = json.loads(got.stdout)["groups"][0]["rows"]
    assert len(rows_) == 1 and rows_[0]["where"] == "forge/decisions/willow-email.json"
    assert json.loads(got.stdout)["said"].endswith("no stack: nothing settled runs")
    subj = rows_[0]["what"].split()[0]
    data = json.loads(
        json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())["data"]
    )
    assert data["kind"] == "word" and data["offered"] == ["apple-mail", "mail"]
    assert data["recommended"] is None and data["rank"] is None and data["card"] is None
    assert k("seal", "--box", str(box), subj).returncode == 0
    text, after = suggested(box, "my email")
    assert text.returncode == 0 and after["said"] == (
        "you sealed that none of the cards offered does it for “email”; nothing to run"
    )
    assert [g["name"] for g in after["groups"]] == ["you sealed none of them"], (
        "not stale"
    )


def test_scores_count_whether_a_words_line_held(box):
    took = proposed(box, "email=mail", "due=none", sentence=EMAIL)
    seal_all(box, {p: s for p, s in took.items() if p != "forge/stack.md"})
    text, doc = scored(box)
    assert (
        doc["said"] == "2 forks settled by your seal: 2 by a word, a card taken 1 of 2"
    )
    assert [g["name"] for g in doc["groups"]] == [
        "by a word: did its line's cards hold",
        "each",
    ]
    held = {r["where"]: r["what"] for r in doc["groups"][0]["rows"]}
    assert held == {
        "“due”": "a card taken 0 of 1, none 1",
        "“email”": "a card taken 1 of 1, none 0",
    }
    each = [r["what"] for r in doc["groups"][1]["rows"]]
    assert any(e.startswith("“email”: mail, rank 2 of apple-mail, mail") for e in each)


def test_without_similars_search_a_sentence_that_names_no_card_is_empty(
    box, monkeypatch, capsys
):
    monkeypatch.setattr(suggest, "wanting", lambda: None)
    assert suggest.main(["suggest", COUNT, "--box", str(box)]) == 0
    assert capsys.readouterr().out.startswith("forge: empty, nothing named")


def test_an_idea_is_a_row_under_ideas_and_not_a_step(box):
    ideas = json.loads((ROOT / "adapters" / "planned.json").read_text())
    name = next(i["name"] for i in ideas if i["name"] != "forge")
    text, doc = suggested(box, f"I want {name} on this")
    assert text.returncode == 0 and doc["said"] == "only ideas, nothing built to run"
    assert [g["name"] for g in doc["groups"]] == ["ideas"]


def test_the_plan_is_one_the_forge_validates_and_extracts(box):
    plan_shape = pytest.importorskip("forge.plan_shape")
    decision_extract = pytest.importorskip("forge.decision_extract")
    got = run("suggest", EMAIL, "--box", str(box), "--plan")
    assert got.returncode == 42
    d = json.loads(got.stdout)
    assert (
        set(d)
        == {
            "cards",
            "steps",
            "defaults",
            "defaults_not_here",
            "forks",
            "sealed",
            "not_now",
            "unsealed",
            "ideas",
            "plan",
        }
        and d["sealed"] == {}
        and d["not_now"] == {}
        and d["unsealed"] == {}
        and d["defaults"] == []
        and d["defaults_not_here"] == []
    )
    doc = plan_shape.validate(d["plan"])
    forks = [e for e in doc.entries if isinstance(e, plan_shape.Fork)]
    assert [f.decision_type for f in forks] == ["willow-email", "willow-due"]
    assert all(f.recommended is None and f.confidence is None for f in forks), (
        "no fabricated 0.5"
    )
    ex = decision_extract.extract(doc)
    assert len(ex.decisions) == 2 and not ex.refused, ex.to_dict()


# ── propose ───────────────────────────────────────────────────────────────────


def test_an_unsettled_fork_is_refused_naming_its_options_and_nothing_is_written(box):
    before = len(rows(box))
    got = run("propose", EMAIL, "--box", str(box), "--choose", "email=mail")
    assert (
        got.returncode == 2
        and "“due” is not settled: --choose due=coming-up|renewals|none" in got.stderr
    )
    assert len(rows(box)) == before and not (box / "proposals").exists()


def test_a_choice_not_on_offer_is_refused(box):
    got = run(
        "propose",
        EMAIL,
        "--box",
        str(box),
        "--choose",
        "email=pdf",
        "--choose",
        "due=renewals",
    )
    assert got.returncode == 2 and "pdf is not an option for “email”" in got.stderr
    got = run(
        "propose",
        EMAIL,
        "--box",
        str(box),
        "--choose",
        "email=mail",
        "--choose",
        "due=renewals",
        "--choose",
        "x=y",
    )
    assert got.returncode == 2 and "nothing to choose for “x”" in got.stderr
    got = run("propose", EMAIL, "--box", str(box), "--choose", "email")
    assert got.returncode == 2 and "WORD=NAME" in got.stderr


def test_nothing_to_propose_is_refused(box):
    got = run("propose", NONSENSE, "--box", str(box))
    assert got.returncode == 2 and "nothing to propose" in got.stderr


def test_propose_puts_each_settled_fork_and_the_stack_at_the_door_as_a_report(box):
    waiting = proposed(box, "email=mail", "due=coming-up")
    assert set(waiting) == {
        "forge/decisions/willow-email.json",
        "forge/decisions/willow-due.json",
        "forge/stack.md",
    }
    out = k("out", "--box", str(box))
    assert out.returncode == 42 and out.stdout.count("waiting on your seal") == 3
    kinds = [(r["kind"], r.get("verdict")) for r in rows(box)]
    assert kinds[1:] == [("bite", None), ("proposal", "pass")] * 3 + [("out", None)]
    subj = waiting["forge/decisions/willow-email.json"]
    prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    data = json.loads(prop["data"])
    assert (
        data["chose"] == "mail"
        and data["over"] == ["apple-mail"]
        and data["decision_type"] == "willow-email"
    )
    assert (
        data["card"]["where"] == "adapters/stdlib/mail/README.md"
        and len(data["card"]["sha256"]) == 64
    )
    assert prop["claim"].endswith("no reason given")
    stack = json.loads(
        (box / "proposals" / f"{waiting['forge/stack.md'][9:]}.json").read_text()
    )
    # the stack is a page of wants: each step under the want it answers, what
    # it was chosen over and why, numbered in the order they run
    page = stack["data"].splitlines()
    assert page[-1] == "- coming-up -- --box {box}"
    assert page[-3].startswith("Want 2: “due”: coming-up, not ") and page[-4] == ""
    assert page[-2].startswith("coming-up: ") and "because" not in page[-3]
    mail = next(
        i for i, ln in enumerate(page) if ln.startswith("- mail -- mirror --from ")
    )
    assert page[mail - 2] == "Want 1: “email”: mail, not apple-mail." and page[mail - 1].startswith("mail: ")  # fmt: skip
    assert page[2] == suggest.WANTS_INTRO and "## what you chose" in page
    assert [ln for ln in page if ln.startswith("- ")] == [page[mail], page[-1]], "only the steps are steps"  # fmt: skip
    assert suggest.steps_of(stack["data"]) == ["mail", "coming-up"]


def test_propose_prints_its_report_as_text_too(box):
    got = run("propose", "my email", "--box", str(box), "--choose", "email=mail")
    assert got.returncode == 42
    head, decision, stack = got.stdout.rstrip("\n").splitlines()
    assert head.startswith(
        "forge: populated, 2 waiting on your seal"
    ) and HEAD.fullmatch(head)
    assert ROW.fullmatch(decision) and decision.lstrip().startswith(
        "forge/decisions/willow-email.json"
    )
    assert ROW.fullmatch(stack) and stack.lstrip().startswith("forge/stack.md")


def test_a_reason_rides_on_the_decision(box):
    got = run(
        "propose",
        "my email",
        "--box",
        str(box),
        "--choose",
        "email=mail",
        "--why",
        "email=the flat's mail is mbox",
        "--json",
    )
    assert got.returncode == 42, got.stderr
    subj = json.loads(got.stdout)["groups"][0]["rows"][0]["what"].split()[0]
    prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    assert json.loads(prop["data"])["why"] == "the flat's mail is mbox" and prop[
        "claim"
    ].endswith("the flat's mail is mbox")


def test_a_proposal_is_not_an_answer_until_sealed(box):
    proposed(box, "email=mail", "due=coming-up")
    text, doc = suggested(box)
    assert text.returncode == 42 and [g["name"] for g in doc["groups"]] == [
        "fork “email”",
        "fork “due”",
        "picked, not sealed yet",
    ], "still asked, and what waits on the seal is said"
    assert [r["what"].split(",")[0] for r in doc["groups"][2]["rows"]] == [
        "mail for “email”", "coming-up for “due”"]  # fmt: skip


# ── the seal, and both sides reading it back ──────────────────────────────────


def test_a_sealed_decision_settles_the_fork_and_asks_nothing_twice(box):
    waiting = proposed(box, "email=mail", "due=coming-up")
    seal_all(box, {p: s for p, s in waiting.items() if p != "forge/stack.md"})
    text, doc = suggested(box, "my email, and what is due")
    assert text.returncode == 0 and doc["said"] == "2 steps, nothing waits on you"
    whats = [r["what"] for r in doc["groups"][0]["rows"]]
    assert (
        whats[0].startswith("mail: ") and "you sealed it for “email” (row " in whats[0]
    )
    d = json.loads(
        run("suggest", "my email, and what is due", "--box", str(box), "--plan").stdout
    )
    assert (
        d["sealed"]["email"]["chose"] == "mail"
        and d["sealed"]["email"]["decision_type"] == "willow-email"
    )
    assert [e["kind"] for e in d["plan"]["entries"]] == ["file_write", "file_write"]


def test_a_sealed_stack_for_the_same_words_is_served_first(box):
    waiting = proposed(box, "email=mail", "due=coming-up")
    seal_all(box, waiting)
    text, doc = suggested(box, EMAIL.upper() + "?")
    assert text.returncode == 0 and doc["said"].startswith(
        "a stack is sealed for these words"
    )
    assert doc["groups"][0]["name"].startswith(
        "stack sealed for these words (proposal:"
    )
    assert doc["groups"][0]["rows"][-1]["what"] == "- coming-up -- --box {box}"
    again = run(
        "propose",
        EMAIL,
        "--box",
        str(box),
        "--choose",
        "email=mail",
        "--choose",
        "due=coming-up",
    )
    assert again.returncode == 2 and "sealed for these words already" in again.stderr
    bite = k("bite", "--box", str(box), EMAIL)
    assert bite.returncode == 0 and json.loads(bite.stdout)["state"] == "sealed"


def test_the_forge_reads_the_sealed_decision_back_through_the_kernel(box):
    willow_record = pytest.importorskip("forge.willow_record")
    waiting = proposed(box, "email=mail", "due=renewals")
    rec = willow_record.WillowRecord(KERNEL, box)
    assert rec.has_sealed("willow-email") is None, "not before the seal"
    seal_all(box, waiting)
    assert rec.has_sealed("willow-email").chosen == "mail"
    assert rec.has_sealed("willow-due").chosen == "renewals"
    assert rec.stack_for(EMAIL).splitlines()[-1] == "- renewals -- --box {box}"


def test_a_decision_the_forge_proposed_is_read_the_same(box):
    """The Forge's build loop proposes under the decision type with no word
    beside it; keyed by decision type, it settles the fork here too."""
    willow_record = pytest.importorskip("forge.willow_record")
    rec = willow_record.WillowRecord(KERNEL, box)
    subj = rec.propose(
        "willow-email", "apple-mail", over=["mail"], why="the Mac's mail"
    )
    assert k("seal", "--box", str(box), subj).returncode == 0
    d = json.loads(run("suggest", "my email", "--box", str(box), "--plan").stdout)
    assert d["forks"] == {} and d["sealed"]["email"]["chose"] == "apple-mail"


def test_a_changed_proposal_is_no_longer_sealed_for_either_side(box):
    waiting = proposed(box, "email=mail", "due=renewals")
    seal_all(box, waiting)
    f = box / "proposals" / f"{waiting['forge/decisions/willow-email.json'][9:]}.json"
    f.write_text(f.read_text().replace("no reason given", "a reason given"))  # any byte
    text, doc = suggested(box, "my email")
    assert text.returncode == 42 and [g["name"] for g in doc["groups"]] == [
        "fork “email”"
    ]


def test_the_first_standing_seal_for_a_decision_is_the_one_kept_as_the_kernel_keeps_it(
    box,
):
    first = proposed(box, "email=mail", "due=renewals")
    seal_all(box, {p: s for p, s in first.items() if "email" in p})
    data = json.dumps(
        {
            "word": "email",
            "decision_type": "willow-email",
            "chose": "apple-mail",
            "over": [],
            "why": "",
        }
    )
    prop = {
        "path": "forge/decisions/willow-email.json",
        "data": data,
        "cites": [],
        "claim": "second",
    }
    assert (
        k("bite", "--box", str(box), "forge decision willow-email").returncode == 0
    ), "the first is served"
    f = box / "p.jsonl"
    f.write_text(json.dumps(prop) + "\n")
    second = k("propose", "--box", str(box), "--file", str(f)).stdout.split()[1]
    assert k("seal", "--box", str(box), second).returncode == 0
    d = json.loads(run("suggest", "my email", "--box", str(box), "--plan").stdout)
    assert d["sealed"]["email"]["chose"] == "mail"
    pf = box / "proposals" / f"{first['forge/decisions/willow-email.json'][9:]}.json"
    pf.write_text(pf.read_text().replace("no reason given", "a reason given"))
    d = json.loads(run("suggest", "my email", "--box", str(box), "--plan").stdout)
    assert d["sealed"]["email"]["chose"] == "apple-mail"


def test_a_seal_for_a_card_that_no_longer_does_the_word_is_said_and_asked_again(box):
    data = json.dumps(
        {
            "word": "email",
            "decision_type": "willow-email",
            "chose": "pdf",
            "over": [],
            "why": "",
        }
    )
    prop = {
        "path": "forge/decisions/willow-email.json",
        "data": data,
        "cites": [],
        "claim": "pdf",
    }
    assert k("bite", "--box", str(box), "forge decision willow-email").returncode == 42
    f = box / "p.jsonl"
    f.write_text(json.dumps(prop) + "\n")
    got = k("propose", "--box", str(box), "--file", str(f))
    assert got.returncode == 42, got.stderr
    assert k("seal", "--box", str(box), got.stdout.split()[1]).returncode == 0
    text, doc = suggested(box, "my email")
    assert text.returncode == 42
    assert [g["name"] for g in doc["groups"]] == [
        "fork “email”",
        "stale seals, asked again",
    ]
    stale = doc["groups"][1]["rows"][0]
    assert stale["where"] == "forge/decisions/willow-email.json" and stale[
        "what"
    ].startswith("pdf no longer does “email” here")


def test_the_same_box_gives_the_same_report_twice(box):
    assert (
        run("suggest", EMAIL, "--box", str(box)).stdout
        == run("suggest", EMAIL, "--box", str(box)).stdout
    )


# ── build ─────────────────────────────────────────────────────────────────────


def sealed_stack(box: Path, sentence: str, *choose: str) -> None:
    seal_all(box, proposed(box, *choose, sentence=sentence))


def test_build_refuses_while_no_stack_is_sealed_for_these_words(box, tmp_path):
    proposed(box, "due=coming-up", sentence="what is due")
    got = run("build", "what is due", "--box", str(box), "--to", str(tmp_path / "st"))
    assert got.returncode == 2 and "no stack is sealed for these words" in got.stderr
    assert not (tmp_path / "st").exists()


def test_build_refuses_a_missing_parent_and_makes_nothing(box, tmp_path):
    sealed_stack(box, "what is due", "due=coming-up")
    got = run(
        "build", "what is due", "--box", str(box), "--to", str(tmp_path / "no" / "st")
    )
    assert (
        got.returncode == 2
        and "is missing" in got.stderr
        and not (tmp_path / "no").exists()
    )


def test_build_assembles_the_sealed_steps_runs_the_stack_and_keeps_the_page(
    box, tmp_path
):
    sealed_stack(box, "what is due", "due=coming-up")
    to = tmp_path / "st"
    argv = ["build", "what is due", "--box", str(box), "--to", str(to)]
    data = run(*argv, "--json")
    assert data.returncode == 0, data.stderr
    doc = holds_the_shape(json.loads(data.stdout), data.returncode)
    assert doc["said"].startswith(
        f"1 of 1 step built into {to}, page at {to / 'page.md'}; 0 flagged, 0 left out"
    )
    assert [g["name"] for g in doc["groups"]] == ["built"]
    row = doc["groups"][0]["rows"][0]
    assert row["where"] == "adapters/stdlib/coming-up/" and row["what"].startswith(
        "coming-up: contract held; tests unreachable"
    )
    assert row["what"].endswith("; ran: clean")
    manifest = json.loads((to / "stack" / "STACK.json").read_text(encoding="utf-8"))
    assert (
        "coming-up" in manifest["addons"]
        and (
            to / "stack" / "adapters" / "stdlib" / "coming-up" / "coming_up.py"
        ).is_file()
    )
    assert (to / "forge-stack.md").read_text(encoding="utf-8").splitlines()[
        -1
    ] == "- coming-up -- --box {box}"
    page = (to / "page.md").read_text(encoding="utf-8")
    assert page.startswith("# stack over ") and "- `coming-up -- --box " in page
    again = run(*argv)
    assert again.returncode == 0 and "coming-up: already in the stack" in again.stdout


def test_build_leaves_out_what_assemble_refuses_and_says_so(box, tmp_path):
    """readme works on willow's own repository, so assemble won't copy it."""
    sealed_stack(box, "what is due, and my readme", "due=coming-up")
    to = tmp_path / "st"
    data = run(
        "build",
        "what is due, and my readme",
        "--box",
        str(box),
        "--to",
        str(to),
        "--json",
    )
    assert data.returncode == 42
    doc = holds_the_shape(json.loads(data.stdout), data.returncode)
    assert doc["said"].endswith("1 left out") and [
        g["name"] for g in doc["groups"]
    ] == ["built", "left out"]
    left = doc["groups"][1]["rows"][0]
    assert left["where"] == "adapters/stdlib/readme/"
    assert "works on willow's own repository" in left["what"]
    assert not (to / "stack/adapters/stdlib/readme").exists()


def test_build_puts_a_deps_step_in_its_own_folder_and_finds_it_there_again(
    box, tmp_path
):
    """pdf comes in under adapters/deps/, as in willow, with its packages
    unchecked (build names no Python), so it is flagged, not left out; built
    again, it is already there."""
    sealed_stack(box, "what is due, and my pdf", "due=coming-up")
    to = tmp_path / "st"
    argv = ("build", "what is due, and my pdf", "--box", str(box), "--to", str(to))
    data = run(*argv, "--json")
    assert data.returncode == 42
    doc = holds_the_shape(json.loads(data.stdout), data.returncode)
    assert doc["said"].endswith("0 left out")
    built = {r["where"]: r["what"] for r in doc["groups"][0]["rows"]}
    assert "packages unreachable" in built["adapters/deps/pdf/"]
    assert (to / "stack/adapters/deps/pdf").is_dir()
    assert not (to / "stack/adapters/stdlib/pdf").exists()
    again = run(*argv)
    assert "pdf: already in the stack" in again.stdout


def test_steps_of_reads_a_stack_file_as_the_stack_add_on_does():
    text = "# a title\n\n## for it\n- coming-up -- --box {box}\n- pdf -- --box {box}\nprose\n- coming-up -- --box {box}\n"
    assert suggest.steps_of(text) == ["coming-up", "pdf"]


def test_build_flags_a_step_that_runs_and_does_not_come_back_clean(box, tmp_path):
    """box-health on a fresh box needs you (no out row yet): exit 42 on the
    page, and build says so rather than hide it."""
    sealed_stack(box, "what is due, and my box health", "due=coming-up")
    to = tmp_path / "st"
    data = run(
        "build",
        "what is due, and my box health",
        "--box",
        str(box),
        "--to",
        str(to),
        "--json",
    )
    assert data.returncode == 42
    doc = holds_the_shape(json.loads(data.stdout), data.returncode)
    assert "0 flagged" not in doc["said"] and doc["said"].endswith("0 left out")
    rows = {r["where"]: r["what"] for r in doc["groups"][0]["rows"]}
    assert rows["adapters/stdlib/coming-up/"].endswith("ran: clean")
    # a report step's note on the page is its state; flagged, since it exited 42
    assert rows["adapters/stdlib/box-health/"].endswith("ran: populated")
    assert "`  (populated)" in (to / "page.md").read_text(encoding="utf-8")


# ── steps from each add-on's own command line ─────────────────────────────────


def contract_rows() -> dict:
    spec = importlib.util.spec_from_file_location(
        "willow_contract_t", ROOT / "adapters/stdlib/ci/test_contract.py"
    )
    tc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tc)
    return tc.COMMANDS


def step_of(box: Path, sentence: str, name: str) -> str:
    d = json.loads(run("suggest", sentence, "--box", str(box), "--plan").stdout)
    assert d["cards"]["commands"].startswith("from the ci add-on's contract")
    for e in d["plan"]["entries"]:
        if e["kind"] == "file_write" and e["dest_path"] == f"steps/{name}.md":
            return e["content"]
        if e["kind"] == "fork":
            for writes in e["resolves"].values():
                for w in writes:
                    if w["dest_path"] == f"steps/{name}.md":
                        return w["content"]
    raise AssertionError(f"no step for {name}")


def test_a_step_is_the_add_ons_own_good_command_line_not_one_shape_for_all(box):
    assert (
        step_of(box, "a merkle proof of one row", "merkle")
        == "- merkle -- root --box {box}\n"
    )
    assert step_of(box, "my email", "mail").startswith("- mail -- mirror --from ")
    rows = contract_rows()
    assert rows["merkle"][1] == ["root", "--box", "{box}"], (
        "the line is the contract's row"
    )


def test_the_contracts_pinned_now_is_taken_off_and_the_pile_is_filled_in(box):
    rows = contract_rows()
    assert "--now" in rows["coming-up"][1], (
        "the contract pins a now for its own determinism"
    )
    assert step_of(box, "what is due", "coming-up") == "- coming-up -- --box {box}\n"
    pile = json.loads((box / "kernel.json").read_text())["pile"]
    assert any("{pile}" in a for a in rows["mail"][1])
    line = step_of(box, "my email", "mail")
    assert pile in line and "{pile}" not in line and "{tmp}" in line


def test_a_path_with_a_space_in_it_is_quoted_for_the_stack_add_on(tmp_path):
    pile = tmp_path / "my pile"
    pile.mkdir()
    (pile / "a.txt").write_text("hello\n")
    box = tmp_path / "box"
    assert (
        k(
            "init",
            "--box",
            str(box),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k.key"),
        ).returncode
        == 0
    )
    line = step_of(box, "my email", "mail")
    assert f"'{pile}'" in line


def test_build_fills_tmp_with_a_folder_of_its_own_and_a_reader_step_runs_clean(
    box, tmp_path
):
    pile = Path(json.loads((box / "kernel.json").read_text())["pile"])
    (pile / "roof.eml").write_text(
        "From: ada@example.org\nTo: me@example.org\nSubject: the roof\nDate: Mon, 3 Nov 2026 09:00:00 +0000\n\nThe roofer comes Tuesday.\n"
    )
    sealed_stack(box, "my email", "email=mail")
    to = tmp_path / "st"
    data = run("build", "my email", "--box", str(box), "--to", str(to), "--json")
    assert data.returncode == 0, data.stdout + data.stderr
    doc = json.loads(data.stdout)
    assert doc["groups"][0]["rows"][0]["what"].endswith("ran: clean")
    written = (to / "forge-stack.md").read_text(encoding="utf-8")
    assert "{tmp}" not in written and str(to / "out") in written
    assert (to / "out").is_dir() and any((to / "out").iterdir()), (
        "the mirror landed under the build's own folder"
    )


def test_without_the_contract_every_step_takes_the_default_and_says_so(
    box, monkeypatch, capsys
):
    monkeypatch.setattr(suggest, "CONTRACT", Path("/nonesuch/test_contract.py"))
    suggest.STEPS.clear()
    code = suggest.main(
        ["suggest", "a merkle proof of one row", "--box", str(box), "--plan"]
    )
    d = json.loads(capsys.readouterr().out)
    assert code == 0 and d["cards"]["commands"].startswith("the ci add-on isn't here")
    assert d["plan"]["entries"][0]["content"] == "- merkle -- --box {box}\n"


# ── the defaults: in every stack, never asked and never scored ───────────────
def with_defaults(tmp_path: Path, text: str) -> list[str]:
    f = tmp_path / "defaults.txt"
    f.write_text(text, encoding="utf-8")
    return ["--defaults", str(f)]


def default_names(doc: dict) -> list[str]:
    return [d["name"] for d in doc["defaults"]]


def test_the_list_beside_the_script_names_built_add_ons_each_once_with_its_reason():
    names = []
    for raw in (HERE / "defaults.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            name, _, why = line.partition(" ")
            assert why.strip(), f"{name} says why it is a default"
            assert (ROOT / "adapters/stdlib" / name / "README.md").is_file(), name
            names.append(name)
    assert names and len(set(names)) == len(names)
    assert {"todo", "duplicates", "contradictions"} <= set(names)


def test_defaults_ride_after_the_steps_in_their_own_group_and_in_the_plan(
    box, tmp_path
):
    mine = with_defaults(tmp_path, "# mine\ntodo   open items\n\npeople  who is named  # a note\ntodo  again\n")  # fmt: skip
    got = run(
        "suggest", "a merkle proof of one row", "--box", str(box), *mine, "--json"
    )
    assert got.returncode == 0, got.stderr
    doc = json.loads(got.stdout)
    assert [g["name"] for g in doc["groups"]] == [
        "steps", "defaults: in every stack, not asked and not scored"]  # fmt: skip
    whats = [r["what"] for r in doc["groups"][1]["rows"]]
    assert [w.split(":", 1)[0] for w in whats] == ["todo", "people"], (
        "in the list's order, each once"
    )
    assert whats[0].endswith("; open items") and whats[1].endswith("; who is named")
    plan = json.loads(run("suggest", "a merkle proof of one row", "--box", str(box), *mine, "--plan").stdout)  # fmt: skip
    assert default_names(plan) == ["todo", "people"]
    assert [e["dest_path"] for e in plan["plan"]["entries"]] == [
        "steps/merkle.md", "steps/todo.md", "steps/people.md"]  # fmt: skip


def test_the_shipped_list_is_what_is_read_when_none_is_named(box):
    got = subprocess.run(
        [sys.executable, str(SCRIPT), "suggest", "a merkle proof of one row", "--box", str(box), "--plan"],
        capture_output=True, text=True)  # fmt: skip
    assert "todo" in default_names(json.loads(got.stdout))
    none = json.loads(run("suggest", "a merkle proof of one row", "--box", str(box), "--plan").stdout)  # fmt: skip
    assert none["defaults"] == [], "--defaults none proposes with none"


def test_a_default_is_never_an_option_of_the_close_fork(box, tmp_path):
    """Picking a default there would be scored as the search being right."""
    plain = [o["name"] for o in plan_of(box, COUNT)["forks"]["close"]]
    first = plain[0]
    mine = with_defaults(tmp_path, f"{first}  kept in every stack\n")
    doc = json.loads(run("suggest", COUNT, "--box", str(box), *mine, "--plan").stdout)
    offered = [o["name"] for o in doc["forks"]["close"]]
    assert first not in offered and offered[-1] == "none"
    assert default_names(doc) == [first], "it rides beside the fork instead"
    assert doc["plan"]["entries"][-1]["dest_path"] == f"steps/{first}.md"


def test_a_default_the_words_reached_is_that_step_and_not_a_default_too(box, tmp_path):
    mine = with_defaults(tmp_path, "merkle  kept in every stack\ntodo  open items\n")
    doc = json.loads(run("suggest", "a merkle proof of one row", "--box", str(box), *mine, "--plan").stdout)  # fmt: skip
    assert [s["name"] for s in doc["steps"]] == ["merkle"] and default_names(doc) == [
        "todo"
    ]


def test_twice_reaches_duplicates_as_a_step_and_not_a_default_too(box):
    """ "anything said twice" reached nothing; "twice" is a line of
    ui/search-words.txt now, and duplicates (a shipped default) is that step."""
    sentence = "Check for anything said twice"
    doc = plan_of(box, sentence)
    assert [s["name"] for s in doc["steps"]] == ["duplicates"] and "close" not in doc["forks"]  # fmt: skip
    shipped = subprocess.run(
        [sys.executable, str(SCRIPT), "suggest", sentence, "--box", str(box), "--plan"],
        capture_output=True, text=True)  # fmt: skip
    got = json.loads(shipped.stdout)
    assert [s["name"] for s in got["steps"]] == ["duplicates"]
    assert "duplicates" not in default_names(got) and "todo" in default_names(got)


def test_back_up_reaches_backup_and_a_due_back_deposit_does_not_fork_it(box):
    """The words list is one word to a line, so "back up" is the word "back";
    suggest's phrase table keeps the hit only with "up" within a word or two."""
    for said in ("back up my record", "back it up", "back them all up"):
        up = plan_of(box, said)
        assert [s["name"] for s in up["steps"]] == ["backup"], said
    due = plan_of(box, "The deposit is due back at the end of the month")
    assert due["steps"] == []
    assert list(due["forks"]) == ["due"]
    assert [o["name"] for o in due["forks"]["due"]][:2] == ["coming-up", "renewals"]


def test_a_back_up_step_says_the_phrase_it_came_from(box):
    got = run("suggest", "back it up", "--box", str(box), "--plan")
    steps = json.loads(got.stdout)["steps"]
    assert [s["name"] for s in steps] == ["backup"]
    assert "“back it up”" in steps[0]["why"]


def test_phrases_for_open_items_reach_todo_and_bare_to_do_does_not(box):
    for said in (
        "I still have a list of things to do",
        "what do I still have to do",
        "what is left to do",
        "a to-do list",
    ):
        got = plan_of(box, said)
        assert [s["name"] for s in got["steps"]] == ["todo"], said
        assert "close" not in got["forks"], said
    mixed = plan_of(box, "what is due and what do I still have to do")
    assert [s["name"] for s in mixed["steps"]] == ["todo"]
    assert list(mixed["forks"]) == ["due"]
    ordinary = plan_of(box, "what do I want to do with this folder")
    assert ordinary["steps"] == []
    assert list(ordinary["forks"]) == ["close"]


def test_a_default_a_words_fork_offers_stays_yours_to_pick(box, tmp_path):
    mine = with_defaults(tmp_path, "mail  kept in every stack\ntodo  open items\n")
    doc = json.loads(
        run("suggest", "my email", "--box", str(box), *mine, "--plan").stdout
    )
    assert "mail" in [o["name"] for o in doc["forks"]["email"]]
    assert default_names(doc) == ["todo"]


def test_defaults_never_make_a_plan_or_a_stack_of_their_own(box, tmp_path):
    mine = with_defaults(tmp_path, "todo  open items\n")
    got = run("suggest", NONSENSE, "--box", str(box), *mine, "--plan")
    assert json.loads(got.stdout)["plan"] is None, (
        "nothing reached: still nothing to run"
    )
    miss = run(
        "propose", COUNT, "--box", str(box), *mine, "--choose", "close=none", "--json"
    )
    assert miss.returncode == 42, miss.stderr
    assert "no stack: nothing settled runs" in json.loads(miss.stdout)["said"]


def test_a_proposed_stack_carries_the_defaults_after_its_own_steps(box, tmp_path):
    mine = with_defaults(tmp_path, "todo  open items\nmail  kept in every stack\n")
    got = run(
        "propose",
        "my email",
        "--box",
        str(box),
        *mine,
        "--choose",
        "email=mail",
        "--json",
    )
    assert got.returncode == 42, got.stderr
    rows_ = [r for g in json.loads(got.stdout)["groups"] for r in g["rows"]]
    (stack,) = [r["what"] for r in rows_ if r["where"] == "forge/stack.md"]
    assert stack.endswith("a stack: mail, todo"), (
        "its own step first; a default picked is not twice"
    )
    subj = stack.split()[0]
    text = json.loads((box / "proposals" / (subj[9:] + ".json")).read_text())["data"]
    assert [ln.split()[1] for ln in text.splitlines() if ln.startswith("- ")] == [
        "mail",
        "todo",
    ]


def test_a_line_naming_no_built_add_on_is_said_and_left_out(box, tmp_path):
    mine = with_defaults(tmp_path, "todo  open items\nno-such-thing  a typo\n")
    doc = json.loads(run("suggest", "a merkle proof of one row", "--box", str(box), *mine, "--json").stdout)  # fmt: skip
    last = doc["groups"][-1]
    assert last["name"] == "defaults named that are no built add-on here"
    assert last["rows"] == [{"where": "defaults.txt", "what": "no-such-thing"}]


def test_a_defaults_file_that_isnt_there_is_refused(box, tmp_path):
    got = run(
        "suggest",
        "my email",
        "--box",
        str(box),
        "--defaults",
        str(tmp_path / "gone.txt"),
    )
    assert got.returncode == 2 and "isn't a file of defaults" in got.stderr


# ── not now: not deciding is a decision, and nothing waiting goes quiet ──────
def test_every_fork_offers_not_now_last_and_the_plan_does_not(box):
    text, doc = suggested(box, EMAIL)
    forks = [g for g in doc["groups"] if g["name"].startswith("fork ")]
    assert len(forks) == 2
    for g in forks:
        assert g["rows"][-1]["where"] == "not-now"
        assert g["rows"][-1]["what"].startswith("not-now: leave this one undecided")
        assert g["rows"][-2]["where"] == "none", "beside none, after it"
    plan = plan_of(box, EMAIL)
    assert all(
        o["name"] != "not-now" for opts in plan["forks"].values() for o in opts
    ), "it is no option of the Forge's fork: nothing there resolves to it"


def test_not_now_is_proposed_under_its_own_question_and_the_rest_still_stacks(box):
    before = len(rows(box))
    got = run("propose", EMAIL, "--box", str(box), "--choose", "email=mail",
              "--choose", "due=not-now", "--why", "due=I haven't looked at either", "--json")  # fmt: skip
    assert got.returncode == 42, got.stderr
    took = {
        r["where"]: r["what"]
        for g in json.loads(got.stdout)["groups"]
        for r in g["rows"]
    }
    assert set(took) == {"forge/decisions/willow-email.json", "forge/not-now/willow-due.json",
                         "forge/stack.md"}  # fmt: skip
    assert took["forge/not-now/willow-due.json"].endswith("not now for “due”")
    assert took["forge/stack.md"].endswith("a stack: mail"), (
        "no card of the fork left open"
    )
    subj = took["forge/not-now/willow-due.json"].split()[0]
    prop = json.loads((box / "proposals" / (subj[9:] + ".json")).read_text())
    data = json.loads(prop["data"])
    assert data["chose"] == "not-now" and data["why"] == "I haven't looked at either"
    assert data["decision_type"] == "willow-due" and data["shown"] == [
        "coming-up",
        "renewals",
    ]
    assert data["asked_at"] > before and prop["claim"].startswith(
        "for “due”: not now; "
    )
    assert prop["bite_key"] == suggest.kernel.bite_key("forge not now willow-due")
    assert prop["bite_key"] != suggest.kernel.bite_key("forge decision willow-due"), (
        "the decision's own question stays unanswered"
    )


def test_a_sealed_not_now_is_said_keeps_the_fork_open_and_is_never_scored(box):
    took = proposed(box, "email=not-now", "due=not-now")
    assert set(took) == {
        "forge/not-now/willow-email.json",
        "forge/not-now/willow-due.json",
    }
    text, doc = suggested(box, EMAIL)
    assert "picked, not sealed yet" in [g["name"] for g in doc["groups"]], (
        "said while it waits"
    )
    seal_all(box, took)
    text, doc = suggested(box, EMAIL)
    assert text.returncode == 42 and doc["said"] == "2 forks wait on you", (
        "still open, still asked"
    )
    (said,) = [g for g in doc["groups"] if g["name"] == "you said not now"]
    assert [r["where"] for r in said["rows"]] == [
        "forge/not-now/willow-email.json", "forge/not-now/willow-due.json"]  # fmt: skip
    assert said["rows"][0]["what"].startswith(
        "“email” left undecided, by your seal (row "
    )
    assert "picked, not sealed yet" not in [g["name"] for g in doc["groups"]]
    assert plan_of(box, EMAIL)["sealed"] == {}, "no decision was sealed"
    assert (
        json.loads(run("scores", "--box", str(box), "--json").stdout)["state"]
        == "empty"
    )


def test_a_pick_made_after_a_not_now_settles_the_fork_and_the_not_now_goes(box):
    seal_all(box, proposed(box, "email=not-now", sentence="my email"))
    again = proposed(box, "email=not-now", sentence="my email")
    assert again, "a second not now for one fork is a proposal of its own"
    seal_all(box, proposed(box, "email=mail", sentence="my email"))
    text, doc = suggested(box, "my email")
    assert "a stack is sealed for these words" in doc["said"]
    assert "you said not now" not in [g["name"] for g in doc["groups"]]


def test_a_stack_sealed_without_its_pick_says_which_pick_is_left(box):
    took = proposed(box, "email=mail", sentence="my email")
    seal_all(box, {"forge/stack.md": took["forge/stack.md"]})
    text, doc = suggested(box, "my email")
    assert text.returncode == 0
    assert doc["said"].endswith("1 of its forks is not settled, said below")
    (left,) = [g for g in doc["groups"] if g["name"] == "picked, not sealed yet"]
    assert left["rows"][0]["where"] == "forge/decisions/willow-email.json"
    assert left["rows"][0]["what"].startswith("mail for “email”, proposed at row ")
    assert "nothing is scored until then" in left["rows"][0]["what"]
    seal_all(box, {k: v for k, v in took.items() if k != "forge/stack.md"})
    text, doc = suggested(box, "my email")
    assert doc["said"].endswith("nothing to ask") and len(doc["groups"]) == 1


def test_not_now_alone_makes_no_stack(box):
    got = run(
        "propose", "my email", "--box", str(box), "--choose", "email=not-now", "--json"
    )
    assert got.returncode == 42, got.stderr
    assert "no stack: nothing settled runs" in json.loads(got.stdout)["said"]


def test_a_refusal_names_not_now_among_the_options(box):
    got = run("propose", "my email", "--box", str(box))
    assert (
        got.returncode == 2
        and "--choose email=apple-mail|mail|none|not-now" in got.stderr
    )
    got = run("propose", "my email", "--box", str(box), "--choose", "email=later")
    assert got.returncode == 2 and got.stderr.strip().endswith(
        "apple-mail, mail, none, not-now"
    )


# ── more than one: any one might be good, and so might two ───────────────────
def test_a_fork_takes_more_than_one_as_one_decision_and_every_one_is_a_step(box):
    got = run("propose", EMAIL, "--box", str(box), "--choose", "email=mail,apple-mail",
              "--choose", "due=renewals", "--choose", "due=coming-up", "--choose", "due=renewals",
              "--why", "email=both kinds are in the folder", "--json")  # fmt: skip
    assert got.returncode == 42, got.stderr
    took = {
        r["where"]: r["what"]
        for g in json.loads(got.stdout)["groups"]
        for r in g["rows"]
    }
    assert set(took) == {"forge/decisions/willow-email.json", "forge/decisions/willow-due.json",
                         "forge/stack.md"}, "one proposal a fork, however many were taken"  # fmt: skip
    assert took["forge/decisions/willow-email.json"].endswith(
        "apple-mail and mail for “email”"
    )
    assert took["forge/stack.md"].endswith(
        "a stack: mail, apple-mail, renewals, coming-up"
    ), "the stack runs them in the order you named them"
    subj = took["forge/decisions/willow-email.json"].split()[0]
    prop = json.loads((box / "proposals" / (subj[9:] + ".json")).read_text())
    data = json.loads(prop["data"])
    assert data["chose"] == "apple-mail" and data["also"] == ["mail"], (
        "in the order offered"
    )
    assert (
        data["rank"] == 1
        and data["over"] == []
        and data["card"]["name"] == "apple-mail"
    )
    assert [c["name"] for c in data["also_cards"]] == ["mail"] and len(
        data["also_cards"][0]["sha256"]
    ) == 64
    assert prop["claim"].startswith(
        "for “email”: apple-mail and mail over nothing; both kinds"
    )
    due = json.loads(json.loads((box / "proposals" / (
        took["forge/decisions/willow-due.json"].split()[0][9:] + ".json")).read_text())["data"])  # fmt: skip
    assert due["chose"] == "coming-up" and due["also"] == ["renewals"], (
        "given twice counts once"
    )


def test_one_pick_reads_as_it_always_did(box):
    took = proposed(box, "email=mail", sentence="my email")
    subj = took["forge/decisions/willow-email.json"]
    data = json.loads(
        json.loads((box / "proposals" / (subj[9:] + ".json")).read_text())["data"]
    )
    assert data["chose"] == "mail" and "also" not in data and "also_cards" not in data


def test_sealed_every_card_taken_is_a_step_and_nothing_is_asked(box):
    took = proposed(box, "email=mail,apple-mail", sentence="my email")
    seal_all(box, {k: v for k, v in took.items() if k != "forge/stack.md"})
    plan = plan_of(box, "my email")
    assert [s["name"] for s in plan["steps"]] == ["apple-mail", "mail"] and plan[
        "forks"
    ] == {}
    assert all(s["why"].startswith("you sealed it for “email”") for s in plan["steps"])
    assert plan["sealed"]["email"]["chose"] == "apple-mail" and plan["sealed"]["email"][
        "also"
    ] == ["mail"]


def test_a_way_out_is_taken_alone(box):
    for both in ("email=mail,none", "email=not-now,mail", "email=none,not-now"):
        got = run("propose", "my email", "--box", str(box), "--choose", both)
        assert got.returncode == 2 and "stands alone" in got.stderr, both
    got = run("propose", "my email", "--box", str(box), "--choose", "email=mail,pigeon")
    assert got.returncode == 2 and "pigeon is not an option" in got.stderr
    got = run("propose", "my email", "--box", str(box), "--choose", "email=,")
    assert got.returncode == 2 and "WORD=NAME or WORD=NAME,NAME" in got.stderr
    assert len(rows(box)) == 1, "a refusal writes nothing"


def test_a_close_fork_is_scored_on_the_highest_of_what_was_taken(box):
    shown = [
        o["name"] for o in plan_of(box, COUNT)["forks"]["close"] if o["name"] != "none"
    ]
    waiting, data = data_of(
        box, proposed(box, f"close={shown[2]},{shown[0]}", sentence=COUNT)
    )
    assert (
        data["chose"] == shown[0] and data["also"] == [shown[2]] and data["rank"] == 1
    )
    assert data["over"] == [shown[1]] and data["recommended"] == shown[0]


# ── next: what your own stacks put beside what you have ──────────────────────
def a_home_of_stacks(tmp_path: Path) -> Path:
    home = tmp_path / "stacks"
    for name, steps in {
        "one": ["merkle", "todo", "people"],
        "two": ["merkle", "todo", "duplicates"],
        "three": ["merkle", "todo"],
        "four": ["mail", "people"],
        "lonely": ["merkle"],
    }.items():
        (home / name).mkdir(parents=True)
        (home / name / "stack.md").write_text(
            "# a stack\n" + "".join(f"- {s} -- --box {{box}}\n" for s in steps),
            encoding="utf-8",
        )
    (home / "one" / "pile").mkdir()
    (home / "one" / "pile" / "stack.md").write_text(
        "- merkle -- x\n- amounts -- x\n- amounts -- y\n"
    )
    (home / "one" / "notes.md").write_text("- merkle -- x\n- amounts -- x\n")
    return home


def group_of(doc: dict, opens: str) -> list[str]:
    """The rows' text of the report group whose name opens so; [] when it isn't there."""
    return [
        r["what"]
        for g in doc["groups"]
        if (g["name"] or "").startswith(opens)
        for r in g["rows"]
    ]


BESIDE, UNTRIED = "what your stacks put beside them", "what you have never stacked"


def test_next_counts_what_your_stacks_put_beside_what_you_have(box, tmp_path):
    home = a_home_of_stacks(tmp_path)
    got = run(
        "next",
        "a merkle proof of one row",
        "--box",
        str(box),
        "--stacks",
        str(home),
        "--json",
    )
    assert got.returncode == 0, got.stderr
    doc = holds_the_shape(json.loads(got.stdout), 0)
    assert doc["said"].startswith(
        "1 of 1 your stacks put beside these 1 steps, from 4 stacks in "
    )
    assert group_of(doc, "you have") == ["merkle"]
    (row,) = group_of(doc, BESIDE)
    assert row.startswith("todo: ") and row.endswith("with merkle in 3 of 3")
    beside = " ".join(group_of(doc, BESIDE))
    assert "amounts" not in beside, (
        "a file in a pile, or not called a stack, is no stack of yours"
    )
    assert "people" not in beside and "duplicates" not in beside, (
        "beside it once is not a habit"
    )


def test_next_starts_from_the_stack_you_sealed_for_these_words(box, tmp_path):
    home = a_home_of_stacks(tmp_path)
    seal_all(box, proposed(box, "email=mail", sentence="my email"))
    doc = json.loads(
        run(
            "next", "my email", "--box", str(box), "--stacks", str(home), "--json"
        ).stdout
    )
    assert group_of(doc, BESIDE) == [], "mail sits beside people in one stack only"
    for d in ("five", "six"):
        (home / d).mkdir()
        (home / d / "stack.md").write_text("- mail -- x\n- people -- x\n- todo -- x\n")
    doc = json.loads(
        run(
            "next", "my email", "--box", str(box), "--stacks", str(home), "--json"
        ).stdout
    )
    whats = group_of(doc, BESIDE)
    assert [w.split(":")[0] for w in whats] == ["people"], (
        "todo is beside mail in 2 of 3, but in 5 of your 7 stacks: beside everything says nothing"
    )
    assert whats[0].endswith("with mail in 3 of 3")


def test_next_offers_what_you_never_stacked_and_the_catalogue_puts_near(box, tmp_path):
    """Counting can only offer what you have done; the search gives the rest a first chance."""
    home = a_home_of_stacks(tmp_path)
    seal_all(box, proposed(box, "email=mail", sentence="my email"))
    doc = json.loads(
        run(
            "next", "my email", "--box", str(box), "--stacks", str(home), "--json"
        ).stdout
    )
    fresh = [w.split(":")[0] for w in group_of(doc, UNTRIED)]
    assert fresh and "apple-mail" in fresh, (
        "near mail by its own card, and in no stack of yours"
    )
    stacked = {"merkle", "todo", "people", "duplicates", "mail"}
    assert not stacked & set(fresh), "a card any stack of yours holds is not untried"
    assert all("near " in w for w in group_of(doc, UNTRIED)), (
        "each says what it is near"
    )
    assert " you have never stacked and the catalogue puts near" in doc["said"]
    (home / "seven").mkdir()
    (home / "seven" / "stack.md").write_text("- apple-mail -- x\n- todo -- x\n")
    doc = json.loads(
        run(
            "next", "my email", "--box", str(box), "--stacks", str(home), "--json"
        ).stdout
    )
    assert "apple-mail" not in [w.split(":")[0] for w in group_of(doc, UNTRIED)], (
        "stacked once, it's tried"
    )


def test_next_does_not_look_beside_a_default(box, tmp_path):
    home = a_home_of_stacks(tmp_path)
    mine = with_defaults(tmp_path, "todo  open items\n")
    plain = json.loads(run("next", "a merkle proof of one row", "--box", str(box), "--stacks", str(home), "--json").stdout)  # fmt: skip
    withd = json.loads(run("next", "a merkle proof of one row", "--box", str(box), "--stacks", str(home), *mine, "--json").stdout)  # fmt: skip
    assert group_of(withd, "you have") == ["merkle", "todo"]
    assert not any("near todo" in w for w in group_of(withd, UNTRIED)), (
        "a default suits any folder: what is near it says nothing of the want"
    )
    assert set(group_of(withd, UNTRIED)) <= set(group_of(plain, UNTRIED))


def test_next_writes_nothing_and_refuses_a_folder_that_isnt_there(box, tmp_path):
    before = len(rows(box))
    home = a_home_of_stacks(tmp_path)
    assert (
        run("next", NONSENSE, "--box", str(box), "--stacks", str(home)).returncode == 0
    )
    got = run("next", "my email", "--box", str(box), "--stacks", str(tmp_path / "gone"))
    assert got.returncode == 2 and "isn't a folder of stacks" in got.stderr
    assert len(rows(box)) == before
