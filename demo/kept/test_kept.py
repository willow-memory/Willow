"""kept: the stack names add-ons that are here and no machine of its own, a
step takes only an earlier step's output, the words list is one the kernel
reads, and the log kept is this stack's."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STACK = (HERE / "stack.md").read_text(encoding="utf-8")


def stack_module():
    spec = importlib.util.spec_from_file_location(
        "stack", ROOT / "adapters/stdlib/stack/stack.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def steps():
    pools, err = stack_module().parse_stack(STACK)
    assert err is None, err
    return [(name, args) for _, rows in pools for name, args in rows]


def test_the_stack_parses_and_names_only_add_ons_that_are_here():
    stack = stack_module()
    names = [name for name, _ in steps()]
    assert len(names) == 33
    assert len(set(names)) == 28, "at least thirteen add-ons were asked for"
    missing = sorted(n for n in set(names) if stack.resolve(n) is None)
    assert not missing, f"the stack names add-ons that aren't here: {missing}"


def test_the_stack_names_no_machine_of_its_own():
    assert "/tmp/" not in STACK and "/home/" not in STACK
    assert "<scratch>" in STACK and "<repo>" in STACK and "{box}" in STACK


def test_the_stack_asks_the_pinned_pile_and_never_this_checkout():
    for name, args in steps():
        said = " ".join(args)
        if name == "star-system":
            assert "<repo>/adapters/deps/star-system/example_repo" in said
        elif name == "thesis":
            # the note is read from here; what it is put to is the box over the pile
            assert said == "--box {box} <repo>/docs/design/one-shape.md"
            assert (ROOT / "docs/design/one-shape.md").is_file()
        else:
            assert "<repo>" not in said, f"{name} reads this checkout: {said}"
    asked = [name for name, args in steps() if "<pile>" in " ".join(args)]
    assert asked == [
        "code-comments", "git-history", "index-cache", "pile-store", "pile-rungs", "kinds", "kinds",
    ]  # fmt: skip
    script = (HERE / "rebuild.sh").read_text(encoding="utf-8")
    (pinned,) = re.findall(r"^PINNED=([0-9a-f]{40})$", script, flags=re.M)
    assert pinned.startswith("82983e8"), "the last commit before this folder existed"
    assert '--pile "$S/pile"' in script and "s#<pile>#$S/pile#g" in script


def test_what_was_kept_of_the_run_holds_nothing_of_this_folder():
    for path in sorted((HERE / "results").iterdir()):
        text = path.read_text(encoding="utf-8")
        assert (
            "demo/kept" not in text and "/tmp/" not in text and "/home/" not in text
        ), path.name


def test_every_step_has_its_want_above_it():
    wants = re.findall(r"^# want (\d+):", STACK, flags=re.M)
    assert wants == [str(n) for n in range(1, 32)], "the row of wants, in order"
    lines = [ln for ln in STACK.splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        if line.startswith("- "):
            assert lines[i - 1].startswith(("# ", "- ")), f"no want above: {line}"


def test_a_step_takes_only_an_earlier_steps_output():
    for place, (name, args) in enumerate(steps(), 1):
        for taken in re.findall(r"\{(\d\d)(?:\.json)?\}", " ".join(args)):
            assert int(taken) < place, f"step {place} ({name}) takes step {taken}"


def test_nothing_in_the_stack_seals_or_reads_a_key():
    for name, args in steps():
        said = " ".join(args)
        assert name not in ("seal", "session-seal"), name
        assert "--key" not in said and ".key" not in said, f"{name}: {said}"


def test_the_words_list_is_one_the_kernel_reads():
    alias, why = kernel.parse_words((HERE / "words.txt").read_text(encoding="utf-8"))
    assert why is None
    assert len(alias) == 6
    assert alias["supercomputer"] == ["runner", "runners", "shard", "shards"]
    assert "core" not in alias and "computed" not in alias, "the broad lines were cut"


def test_the_questions_are_sixteen_named_lines():
    rows = [
        ln.split("\t")
        for ln in (HERE / "questions.txt").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    assert len(rows) == 16 and all(len(r) == 2 and all(r) for r in rows)
    assert len({name for name, _ in rows}) == 16


def test_the_log_kept_is_this_stacks():
    log = (HERE / "results" / "00-stack.txt").read_text(encoding="utf-8")
    ended = re.findall(r"^(\d\d) ([a-z0-9-]+): exit (\d+)", log, flags=re.M)
    assert [name for _, name, _ in ended] == [name for name, _ in steps()]
    flagged = [n for n, _, code in ended if code != "0"]
    assert flagged == ["07", "11", "13", "26", "27", "29"]
    assert log.strip().endswith("done: 6 of 33 steps flagged")


def test_what_the_run_printed_is_listed_as_kept():
    import json

    kept = json.loads((HERE / "KEPT.json").read_text())
    assert kept["files"] == sorted(
        f"results/{p.name}" for p in (HERE / "results").iterdir()
    )
