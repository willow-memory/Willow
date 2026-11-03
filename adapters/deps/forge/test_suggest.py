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
CLUB = "a site for my running club with the race dates"
HEAD = re.compile(r"[a-z0-9-]+: (?:populated|empty|unreachable), \S.*")
ROW = re.compile(r"  \S.*")


def run(*argv: str) -> subprocess.CompletedProcess:
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
        # file so named, and demo/bernadette has one that imports changed.py
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


def test_nothing_named_is_empty_and_exit_0(box):
    text, doc = suggested(box, CLUB)
    assert (
        text.returncode == 0
        and doc["state"] == "empty"
        and "search-words.txt" in doc["said"]
    )


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
        set(d) == {"cards", "steps", "forks", "sealed", "ideas", "plan"}
        and d["sealed"] == {}
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
        and "“due” is not settled: --choose due=coming-up|renewals" in got.stderr
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
    assert got.returncode == 2 and "WORD=VALUE" in got.stderr


def test_nothing_to_propose_is_refused(box):
    got = run("propose", CLUB, "--box", str(box))
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
    assert stack["data"].splitlines()[-1] == "- coming-up -- --box {box}"
    assert stack["data"].splitlines()[-2].startswith("- mail -- mirror --from ")


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
    ]


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
    sealed_stack(box, "what is due, and my pdf", "due=coming-up")
    to = tmp_path / "st"
    data = run(
        "build", "what is due, and my pdf", "--box", str(box), "--to", str(to), "--json"
    )
    assert data.returncode == 42
    doc = holds_the_shape(json.loads(data.stdout), data.returncode)
    assert doc["said"].endswith("1 left out") and [
        g["name"] for g in doc["groups"]
    ] == ["built", "left out"]
    left = doc["groups"][1]["rows"][0]
    assert left["where"] == "adapters/stdlib/pdf/" and "deps add-on" in left["what"]


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
