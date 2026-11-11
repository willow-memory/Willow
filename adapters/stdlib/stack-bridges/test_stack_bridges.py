"""stack-bridges: a step is tied to the earlier step whose output or `--to`
place it names, its depth is one more than the deepest it takes from, a
bridge that can't hold is said and ends 42, and nothing is run or written."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "stack_bridges.py"
sys.path.insert(0, str(HERE))
import stack_bridges  # noqa: E402

#: Copied out beside the kernel alone (alone.py), this add-on has the stack
#: add-on beside it and no other: the cards it reads of other add-ons, and
#: the repo's own stacks, are there only in the repo.
CARDS_HERE = all(
    (ROOT / "adapters" / kind / name / "README.md").is_file()
    for kind, name in (
        ("stdlib", "fixity"),
        ("stdlib", "backup"),
        ("stdlib", "glance"),
        ("deps", "dp"),
    )
)
REPO_HERE = (ROOT / "demo" / "kept" / "stack.md").is_file()
needs_cards = pytest.mark.skipif(
    not CARDS_HERE, reason="the other add-ons' cards aren't here"
)
needs_repo = pytest.mark.skipif(
    not REPO_HERE, reason="the repo's own stacks aren't here"
)

STACK = """# a stack
## read
- code-comments -- mirror --from PILE --to {box}-code
- index-cache -- --from {box}-code --to S/kept/index
- scan -- scan --index S/kept/index --questions S/q.txt
## look
- glance -- --of {03} --questions S/q.txt
- star-system -- --repo R --to S/out/a/star.md
- diverge -- S/out/a S/out/b
- backup -- --box {box} --to S/usb
- three-two-one -- --box {box} --copy usb:S/usb/backup.zip
- fixity -- --box {box}
"""


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)  # fmt: skip


def doc_of(tmp_path: Path, text: str) -> tuple[dict, int]:
    file = tmp_path / "stack.md"
    file.write_text(text, encoding="utf-8")
    got = run("--stack", str(file), "--json")
    assert got.stdout, got.stderr
    return json.loads(got.stdout), got.returncode


def rows(doc: dict, opens: str) -> dict[str, str]:
    for g in doc["groups"]:
        if g["name"].startswith(opens):
            return {r["where"]: r["what"] for r in g["rows"]}
    return {}


def test_each_step_is_tied_to_the_step_whose_output_or_place_it_names(tmp_path):
    doc, code = doc_of(tmp_path, STACK)
    assert code == 0 and doc["state"] == "populated"
    assert doc["said"] == "9 steps, 5 bridges, 3 deep; 4 rest on no other"
    assert rows(doc, "what each step takes") == {
        "02 index-cache": "01 code-comments: what it wrote, {box}-code",
        "03 scan": "02 index-cache: what it wrote, index",
        "04 glance": "03 scan: its output",
        "06 diverge": "05 star-system: what it wrote, star.md",
        "08 three-two-one": "07 backup: what it wrote, usb",
    }
    assert rows(doc, "a bridge that can't hold") == {}


@needs_cards
def test_the_order_is_by_depth_with_the_longest_way_down_and_the_record_said(tmp_path):
    doc, _ = doc_of(tmp_path, STACK)
    order = rows(doc, "the order")
    assert list(order) == ["rest on no other", "1 step deep", "2 steps deep", "3 steps deep",
                           "the longest way down", "write the record"]  # fmt: skip
    assert (
        order["rest on no other"]
        == "4: 01 code-comments, 05 star-system, 07 backup, 09 fixity"
    )
    assert order["1 step deep"] == "3: 02 index-cache, 06 diverge, 08 three-two-one"
    assert (
        order["2 steps deep"] == "1: 03 scan"
        and order["3 steps deep"] == "1: 04 glance"
    )
    assert (
        order["the longest way down"]
        == "04 glance → 03 scan → 02 index-cache → 01 code-comments"
    )
    assert order["write the record"].startswith(
        "1: 09 fixity; a step that names the record after"
    )
    assert "the record" not in " ".join(rows(doc, "what each step takes").values()), (
        "none comes after the writer"
    )


def test_a_place_is_reached_by_itself_what_is_under_it_and_the_folder_it_is_in():
    reaches = stack_bridges.reaches
    assert (
        reaches("S/usb", "S/usb")
        and reaches("S/usb/b.zip", "S/usb")
        and reaches("S/out/a", "S/out/a/star.md")
    )
    assert (
        not reaches("S/usb2", "S/usb")
        and not reaches("S/us", "S/usb")
        and not reaches("{box}", "{box}-code")
    )
    assert not reaches("S/out/b", "S/out/a/star.md")
    assert stack_bridges.written(
        ["mirror", "--to", "X/", "--from", "Y", "--to", "Z"]
    ) == ["X", "Z"]
    assert (
        stack_bridges.written(["--to"]) == []
        and stack_bridges.written(["--box", "{box}"]) == []
    )
    assert stack_bridges.read(["--from", "A/", "--to", "B", "--copy", "usb:C/d.zip", "{box}:x", "<p>:y", "a/b:c"]) == [
        "--from", "A", "--copy", "usb:C/d.zip", "C/d.zip", "{box}:x", "<p>:y", "a/b:c"]  # fmt: skip


def test_a_bridge_that_cannot_hold_is_said_with_its_step_and_ends_42(tmp_path):
    forward = (
        "## a\n- glance -- --of {02}\n- scan -- scan --index X\n- glance -- --of {00}\n"
    )
    doc, code = doc_of(tmp_path, forward)
    assert code == 42 and rows(doc, "a bridge that can't hold") == {
        "01 glance": "takes {02}, and no step before it has that number",
        "03 glance": "takes {00}, and no step before it has that number",
    }
    late = (
        "## a\n- scan -- scan --index S/index\n- index-cache -- --from P --to S/index\n"
    )
    doc, code = doc_of(tmp_path, late)
    assert code == 42 and rows(doc, "a bridge that can't hold") == {
        "01 scan": "takes index, which step 02 writes later"
    }
    assert doc["said"] == "2 steps, 0 bridges, 0 deep; 2 rest on no other"
    twice = "## a\n- prov -- --box {box} --to S/out.json\n- ids -- --box {box}\n- prov -- --box {box} --to S/out.json\n"
    doc, code = doc_of(tmp_path, twice)
    assert code == 0, "two steps writing to one place is said, and is not a fault"
    assert rows(doc, "two steps write to one place") == {
        "03 prov": "writes to out.json, as step 01 does"
    }
    assert rows(doc, "a bridge that can't hold") == {} and doc["state"] == "populated"
    own = "## a\n- backup -- --box {box} --to S/usb\n"
    assert doc_of(tmp_path, own)[1] == 0, "a step's own --to is not a bridge to itself"


def test_a_stack_with_no_bridge_is_empty_and_ends_zero(tmp_path):
    doc, code = doc_of(
        tmp_path, "## a\n- digest -- --box {box}\n- export -- --box {box}\n"
    )
    assert code == 0 and doc["state"] == "empty" and doc["groups"] == []
    assert doc["said"] == "2 steps, and none takes what another made"
    doc, _ = doc_of(tmp_path, "## a\n- digest -- --box {box}\n")
    assert doc["said"] == "1 step, and none takes what another made"


def test_a_step_taking_from_two_is_as_deep_as_the_deeper_and_its_json_data_counts(
    tmp_path,
):
    text = (
        "## a\n- a -- --to S/x\n- b -- --from S/x --to S/y\n- c -- --box {box}\n"
        "- d -- --from S/y --of {03.json}\n- e -- --from S/x --from S/y\n"
    )
    doc, code = doc_of(tmp_path, text)
    assert code == 0 and doc["said"] == "5 steps, 5 bridges, 2 deep; 2 rest on no other"
    takes = rows(doc, "what each step takes")
    assert takes["04 d"] == "02 b: what it wrote, y; 03 c: its output"
    assert takes["05 e"] == "01 a: what it wrote, x; 02 b: what it wrote, y"
    order = rows(doc, "the order")
    assert (
        order["2 steps deep"] == "2: 04 d, 05 e" and order["1 step deep"] == "1: 02 b"
    )
    assert order["the longest way down"] == "04 d → 02 b → 01 a"
    assert (
        order["no card here"] == "1: 03 c; whether these write the record isn't known"
    )
    assert "write the record" not in order
    assert stack_bridges.depths(3, {2: [(1, "x")], 3: [(1, "x"), (2, "y")]}) == {
        1: 0,
        2: 1,
        3: 2,
    }


def test_the_text_is_the_report_its_json_holds(tmp_path):
    doc, _ = doc_of(tmp_path, STACK)
    text = run("--stack", str(tmp_path / "stack.md")).stdout
    assert text == stack_bridges.report_text(doc) + "\n"
    assert text.splitlines()[0] == f"stack-bridges: populated, {doc['said']}"


@pytest.mark.parametrize(
    "argv,said",
    [
        ([], "usage: stack_bridges.py"),
        (["--json"], "usage: stack_bridges.py"),
        (["--stack"], "usage: stack_bridges.py"),
        (["--stack", "{f}", "extra"], "usage: stack_bridges.py"),
        (["--stack", "{f}", "--stack", "{f}"], "usage: stack_bridges.py"),
        (["--stack", "{d}/absent.md"], "no stack file"),
        (["--stack", "{d}"], "no stack file"),
        (["--stack", "{bad}"], "is not a stack: line 1: a step before any ## pool"),
        (["--stack", "{none}"], "is not a stack: the stack names no steps"),
    ],
)
def test_a_bad_command_line_or_a_file_that_is_not_a_stack_is_refused(
    tmp_path, argv, said
):
    (tmp_path / "ok.md").write_text("## a\n- digest -- --box {box}\n")
    (tmp_path / "bad.md").write_text("- digest -- --box {box}\n")
    (tmp_path / "none.md").write_text("# only prose\n")
    swap = {"{f}": "ok.md", "{bad}": "bad.md", "{none}": "none.md"}
    got = run(
        *[
            str(tmp_path / swap[a]) if a in swap else a.replace("{d}", str(tmp_path))
            for a in argv
        ]
    )
    assert got.returncode == 2 and said in got.stderr and got.stdout == ""


@needs_repo
def test_on_the_repos_own_stacks_every_bridge_holds():
    kept = run("--stack", str(ROOT / "demo/kept/stack.md"), "--json")
    doc = json.loads(kept.stdout)
    assert (
        kept.returncode == 0
        and doc["said"] == "33 steps, 28 bridges, 3 deep; 11 rest on no other"
    )
    assert rows(doc, "what each step takes")["07 glance"] == "06 scan: its output"
    assert (
        rows(doc, "the order")["the longest way down"]
        == "07 glance → 06 scan → 04 index-cache → 01 code-comments"
    )
    for file in sorted((ROOT / "adapters/stdlib/stack/examples").glob("*.md")):
        got = run("--stack", str(file))
        assert got.returncode == 0, f"{file.name}: {got.stdout[:300]}"


def test_it_writes_nothing_and_opens_no_place_the_stack_names(tmp_path):
    file = tmp_path / "stack.md"
    file.write_text(STACK.replace("S/", str(tmp_path / "scratch") + "/"))
    assert run("--stack", str(file)).returncode == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["stack.md"]


@needs_cards
def test_its_own_example_has_the_bridges_its_card_says():
    got = run("--stack", str(HERE / "example.md"), "--json")
    doc = json.loads(got.stdout)
    assert (
        got.returncode == 0
        and doc["said"] == "9 steps, 6 bridges, 3 deep; 3 rest on no other"
    )
    assert rows(doc, "the order")["write the record"].startswith("1: 08 fixity; ")
    assert (
        rows(doc, "what each step takes")["09 history"]
        == "08 fixity: the record as it left it"
    )


def test_a_step_is_never_a_bridge_to_itself(tmp_path):
    own_number = "## a\n- scan -- scan --index X\n- glance -- --of {02}\n"
    doc, code = doc_of(tmp_path, own_number)
    assert code == 42 and rows(doc, "a bridge that can't hold") == {
        "02 glance": "takes {02}, and no step before it has that number"
    }
    own_place = "## a\n- tidy -- --from S/x --to S/x\n- next -- --from S/x\n"
    doc, code = doc_of(tmp_path, own_place)
    assert code == 0 and rows(doc, "a bridge that can't hold") == {}
    assert rows(doc, "what each step takes") == {"02 next": "01 tidy: what it wrote, x"}
    assert doc["said"] == "2 steps, 1 bridge, 1 deep; 1 rest on no other"


def test_a_step_naming_the_record_after_one_that_writes_it_takes_the_record():
    steps = [("a", ["--box", "{box}"]), ("w", ["--box", "{box}"]), ("b", ["--from", "{box}-code"]),
             ("c", ["--box", "{box}"]), ("w", ["--box", "{box}"]), ("d", ["--box", "{box}"]),
             ("w", ["--to", "x"])]  # fmt: skip
    got = stack_bridges.record_bridges(steps, writes=lambda name: name == "w")
    assert got == {4: 2, 5: 2, 6: 5}, (
        "the last writer before it; {box}-code is not the record"
    )
    assert stack_bridges.record_bridges(steps, writes=lambda name: False) == {}
    assert stack_bridges.record_bridges(steps, writes=lambda name: None) == {}
    assert stack_bridges.writes_record("no-such-add-on") is None
    assert stack_bridges.writes_record("stack") is False, (
        "the one card that is always beside it"
    )


@needs_cards
def test_the_record_makes_a_step_deeper_and_is_said_beside_what_else_it_takes(tmp_path):
    text = (
        "## a\n- fixity -- --box {box}\n- backup -- --box {box} --to S/usb\n"
        "- three-two-one -- --box {box} --copy usb:S/usb/b.zip\n"
    )
    doc, code = doc_of(tmp_path, text)
    assert code == 0 and doc["said"] == "3 steps, 3 bridges, 2 deep; 1 rest on no other"
    assert rows(doc, "what each step takes") == {
        "02 backup": "01 fixity: the record as it left it",
        "03 three-two-one": "01 fixity: the record as it left it; 02 backup: what it wrote, usb",
    }
    assert (
        rows(doc, "the order")["the longest way down"]
        == "03 three-two-one → 02 backup → 01 fixity"
    )


@needs_cards
def test_whether_an_add_on_writes_the_record_is_read_off_its_card():
    assert (
        stack_bridges.writes_record("fixity") is True
        and stack_bridges.writes_record("glance") is False
    )
    assert stack_bridges.writes_record("backup") is False, (
        "it writes to a place, not the record"
    )
    assert stack_bridges.writes_record("no-such-add-on") is None
    assert stack_bridges.writes_record("dp") is True, "an add-on in deps has a card too"
