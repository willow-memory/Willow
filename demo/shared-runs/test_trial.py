"""shared-runs, trial 1: the strike takes out a sentence whose figure the
report lacks and no other, an answer is right, not said or wrong by the
key, and what the trial's page says is what its kept files score to."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRIAL = HERE / "trial-1"
sys.path.insert(0, str(HERE))
import trial  # noqa: E402

REPORT = "done: 6 of 29 steps flagged\nthe chain holds: 2 rows, 0 sealed\nfirst mention: 1959-04-17\n"


def test_a_sentence_with_a_figure_the_report_lacks_is_struck_and_no_other():
    account = "It ran 29 steps and 6 were flagged. It took 204 seconds.\nNothing was sealed. First said on 1959-04-17."
    kept, struck = trial.strike(REPORT, account)
    assert struck == ["It took 204 seconds."]
    assert (
        kept
        == "It ran 29 steps and 6 were flagged.\nNothing was sealed.\nFirst said on 1959-04-17.\n"
    )
    assert trial.strike(REPORT, "It ran 1,959 steps.")[1] == ["It ran 1,959 steps."], (
        "1959 is not 1959-04-17"
    )
    assert trial.strike(REPORT, "It ran 29 steps.")[1] == []


def test_an_answer_is_right_not_said_or_wrong_by_the_key():
    key = {
        "steps": "29",
        "flagged": "07 11",
        "same": "yes",
        "when": "1959-04-17",
        "time": trial.NOT_SAID,
    }
    marks = trial.score(
        key,
        "steps: 29.\nflagged: 7, 11\nsame: Yes\nwhen: not said\ntime: 204\nother: 3\n",
    )
    assert marks == {
        "steps": "right",
        "flagged": "right",
        "same": "right",
        "when": "not said",
        "time": "wrong",
    }
    marks = trial.score(key, "steps: 30\ntime: Not said.\n")
    assert marks["steps"] == "wrong" and marks["time"] == "right"
    assert marks["flagged"] == marks["same"] == marks["when"] == "unanswered"


def test_what_the_trials_page_says_is_what_its_files_score_to():
    key = json.loads((TRIAL / "key.json").read_text())
    assert len(key) == 12 and sum(1 for v in key.values() if v == trial.NOT_SAID) == 2
    asked = [
        ln.split(":")[0] for ln in (TRIAL / "questions.txt").read_text().splitlines()
    ]
    assert asked == list(key)
    report = (TRIAL / "report.txt").read_text()
    account = (TRIAL / "a-account.txt").read_text()
    kept, struck = trial.strike(report, account)
    assert struck == [] and kept == (TRIAL / "a-account-struck.txt").read_text()
    assert len(account.split()) <= 150
    b = trial.score(key, (TRIAL / "b-answers.txt").read_text())
    c = trial.score(key, (TRIAL / "c-answers.txt").read_text())
    assert sorted(k for k, v in b.items() if v == "not said") == [
        "first-mention",
        "same-bytes",
    ]
    assert list(b.values()).count("right") == 10 and "wrong" not in b.values()
    assert set(c.values()) == {"right"}
    assert b["seconds"] == b["machines"] == c["seconds"] == c["machines"] == "right"
    page = (TRIAL / "RESULTS.md").read_text()
    assert (
        "10 right, 2 `not said`, 0 wrong" in page
        and "12 right, 0 `not said`, 0 wrong" in page
    )


def test_the_report_and_briefs_name_no_machine_and_hold_no_answer_key():
    for name in ("report.txt", "brief-a.txt", "brief-b.txt", "questions.txt"):
        text = (TRIAL / name).read_text()
        assert "/tmp/" not in text and "/home/" not in text, name
    assert "not said" not in (TRIAL / "report.txt").read_text()


def test_the_chain_refuses_what_a_step_may_not_be_and_passes_what_it_may():
    import chain

    stack = "## a\n- scan -- scan --index x\n- glance -- --of {01}\n"
    passes = [("ids", "--box {box} kernel.py"), ("fixity", "--box {box}"),
              ("glance", "--of {02} --questions <scratch>/questions.txt"),
              ("fair-merge", '--from <pile> "kept so it is not computed again"')]  # fmt: skip
    for name, args in passes:
        assert chain.refusal(name, args, stack) is None, (name, args)
    refused = {
        ("nope", "--box {box}"): "not a built add-on",
        ("kinds", "count"): "not a built add-on",  # a repo tool, not a stack's step
        ("scan", "scan --index x"): "already on the stack",
        ("backup", "--box {box} --to /media/usb"): "no path of its own",
        ("ids", "--box {box} ../x"): "no path of its own",
        ("ids", "--box {box} ~/x"): "no path of its own",
        ("ids", "--box {box} <repo>/kernel.py"): "the only folders",
        ("glance", "--of {03}"): "not an earlier step",
        ("glance", "--of {00}"): "not an earlier step",
        ("share", "send --box {box} --id <scratch>/a.key"): "may not name .key",
        ("fixity", "--box {box} --key x"): "may not name",
        ("session-seal", "--box {box}"): "may not name seal",
    }
    for (name, args), why in refused.items():
        got = chain.refusal(name, args, stack)
        assert got and why in got, (name, args, got)


def test_a_reply_is_read_by_its_three_lines_and_the_catalog_is_what_a_stack_can_run():
    import chain

    said = chain.read_reply(
        "want: a thing\nstep: - ids -- --box {box} kernel.py\nwhy: because\ncards: none\n"
    )
    assert said == {
        "want": ["a thing"],
        "step": ["- ids -- --box {box} kernel.py"],
        "why": ["because"],
    }
    assert chain.steps_of("## a\n- ids -- --box {box}\n# - no -- x\n- scan -- scan\n") == [
        ("ids", "--box {box}"), ("scan", "scan")]  # fmt: skip
    cards = chain.catalog()
    assert "scan" in cards and "fixity" in cards and "star-system" in cards
    assert (
        "kinds" not in cards
        and "hook-handoff" not in cards
        and "starter-words" not in cards
    )
    page = (TRIAL.parent / "trial-2" / "handoff-1.txt").read_text()
    assert page.startswith(
        (TRIAL.parent / "trial-2" / "brief.txt").read_text().rstrip()
    )
    assert "/tmp/" not in page and "/home/" not in page
    assert "hook-handoff: no session before this one." in page


def test_what_trial_twos_page_says_is_what_its_kept_files_hold():
    import chain

    two = TRIAL.parent / "trial-2"
    turns = [
        json.loads(line) for line in (two / "chain.jsonl").read_text().splitlines()
    ]
    assert [(t["link"], t["model"]) for t in turns] == [
        ("link-1", "haiku"), ("link-2", "sonnet"), ("link-3", "haiku")]  # fmt: skip
    assert [t["refused"] for t in turns] == [None, None, None]
    assert [t["ended"] for t in turns] == ["exit 0", "exit 2", "exit 42"]
    assert [t["place"] for t in turns] == [8, 9, 10]
    stack = (two / "stack-at-the-end.txt").read_text()
    steps = chain.steps_of(stack)
    assert len(steps) == 10 and [name for name, _ in steps[7:]] == [
        "again",
        "why-not",
        "box-health",
    ]
    assert len(set(steps)) == len(steps), "no step is on the stack twice"
    cards = chain.catalog()
    for n, turn in enumerate(turns, 1):
        reply = (two / f"reply-{n}.txt").read_text()
        said = chain.read_reply(reply)
        assert (
            said["step"] == [turn["step"]]
            and turn["step"] == f"- {steps[6 + n][0]} -- {steps[6 + n][1]}"
        )
        page = (two / f"handoff-{n}.txt").read_text()
        assert steps[6 + n][0] in cards and f"\n{steps[6 + n][0]}: " in page, (
            "chosen from the page"
        )
        figures = set(trial.figures(" ".join(said["want"] + said["why"])))
        assert figures <= set(trial.figures(page)), (
            n,
            figures - set(trial.figures(page)),
        )
        assert "/tmp/" not in page and "/home/" not in page
    assert "no session before this one" in (two / "handoff-1.txt").read_text()
    assert "session link-1 ended" in (two / "handoff-2.txt").read_text()
    assert "session link-2 ended" in (two / "handoff-3.txt").read_text()
    assert "why-not: refused: not a kernel box" in (two / "handoff-3.txt").read_text()
    log = (two / "log-at-the-end.txt").read_text()
    assert (
        "09 why-not: exit 2" in log
        and "08 again: exit 0" in log
        and "10 box-health: exit 42" in log
    )


def project_with(tmp_path, steps):
    """A made-up project: (add-on, args, exit, what it printed) a step."""
    (tmp_path / "run").mkdir()
    stack, log = ["## a"], []
    for place, (name, args, code, text) in enumerate(steps, 1):
        stack.append(f"- {name} -- {args}")
        log.append(f"{place:02d} {name}: exit {code}, 1 line")
        (tmp_path / "run" / f"{place:02d}-{name}.txt").write_text(text)
    (tmp_path / "stack.txt").write_text("\n".join(stack) + "\n")
    (tmp_path / "run" / "00-stack.txt").write_text("\n".join(log) + "\n")
    return tmp_path


GLANCE = "glance: populated, 4 questions\n## found nothing\n  float  floats that differ\n  float  floats that differ\n## held whole\n  a  b\n"
START = [
    ("code-comments", "mirror --from <pile> --to {box}-code", 0, "wrote 2 files"),
    ("scan", "scan --index x", 0, "{}"),
    ("glance", "--of {02}", 42, GLANCE),
]


def test_each_rule_fits_its_own_situation_and_no_other(tmp_path):
    import rules

    one = (
        project_with(tmp_path / "one", START)
        if (tmp_path / "one").mkdir() is None
        else None
    )
    rule, said = rules.next_step(one)
    assert (
        rule == "explain"
        and "step: - why-not -- --box {box} --questions <scratch>/questions.txt --of {02}"
        in said
    )
    two = tmp_path / "two"
    two.mkdir()
    held = ("why-not", "--box {box} --questions <scratch>/questions.txt --of {02}", 0,
            "why-not: empty, your files hold all 1 question; nothing to explain")  # fmt: skip
    rule, said = rules.next_step(project_with(two, [*START, held]))
    assert rule == "by-pile"
    assert (
        'step: - fair-merge -- --from <pile> --from {box}-code --top 6 "floats that differ"'
        in said
    )
    three = tmp_path / "three"
    three.mkdir()
    merged = (
        "fair-merge",
        '--from <pile> --from {box}-code --top 6 "floats that differ"',
        0,
        "x",
    )
    rule, said = rules.next_step(project_with(three, [*START, held, merged]))
    assert rule is None and said.startswith("no rule fits: 5 steps, 3 rules tried")
    four = tmp_path / "four"
    four.mkdir()
    broken = (
        "why-not",
        "--box <pile> --questions q --of {02}",
        2,
        "refused: not a kernel box; init first",
    )
    rule, said = rules.next_step(project_with(four, [*START, broken]))
    assert (
        rule == "repair"
        and "step: - why-not -- --box {box} --questions q --of {02}" in said
    )
    five = tmp_path / "five"
    five.mkdir()
    fixed = (
        "why-not",
        "--box {box} --questions q --of {02}",
        0,
        "why-not: populated, 1 of 1",
    )
    rule, _ = rules.next_step(project_with(five, [*START, broken, fixed]))
    assert rule is None, "repaired, and why-not explained them: nothing left for a rule"


def test_a_rule_does_not_fire_on_what_it_was_not_written_for(tmp_path):
    import rules

    clean = [
        START[0],
        START[1],
        ("glance", "--of {02}", 0, "glance: populated\n## held whole\n  a  b\n"),
    ]
    assert rules.next_step(project_with(tmp_path, clean))[0] is None
    assert rules.found_nothing(GLANCE) == ["floats that differ"]
    assert rules.found_nothing("## held whole\n  a  b\n") == []
    other = [
        dict(
            place=1,
            name="ids",
            args="--box <pile>",
            exit=2,
            text="refused: no such file",
        )
    ]
    assert rules.repair(other) is None, "another refusal is not this rule's"


def test_what_trial_threes_page_says_is_what_its_kept_files_hold():
    import chain

    three = TRIAL.parent / "trial-3"
    turns = [
        json.loads(line) for line in (three / "chain.jsonl").read_text().splitlines()
    ]
    assert [(t["link"], t["model"], t["refused"], t["ended"]) for t in turns] == [
        ("link-1", "rules", None, "exit 0"), ("link-2", "rules", None, "exit 0")]  # fmt: skip
    steps = chain.steps_of((three / "stack-at-the-end.txt").read_text())
    assert [name for name, _ in steps[7:]] == ["why-not", "fair-merge"] and len(
        steps
    ) == 9
    assert steps[7][1] == "--box {box} --questions <scratch>/questions.txt --of {06}"
    assert (
        three / "reply-3.txt"
    ).read_text() == "no rule fits: 9 steps, 3 rules tried\n"
    merged = (three / "09-fair-merge.txt").read_text()
    assert (
        "box-code: found nothing" in merged and "box-commits: found nothing" in merged
    )
    assert merged.startswith("1. pile/")
    assert "nothing to explain" in (three / "08-why-not.txt").read_text()
    stood = json.loads((three / "chain-where-link-3-stood.jsonl").read_text())
    assert (
        stood["refused"] is None and stood["ended"] == "exit 0" and stood["place"] == 11
    )
    assert stood["step"] == f"- why-not -- {steps[7][1]}", (
        "the repair is the step the rules chose from the start"
    )
    two = [
        json.loads(line)
        for line in (TRIAL.parent / "trial-2" / "chain.jsonl").read_text().splitlines()
    ]
    assert [t["ended"] for t in two] == ["exit 0", "exit 2", "exit 42"], (
        "what the page sets it beside"
    )
    for path in three.iterdir():
        text = path.read_text()
        assert "/tmp/" not in text and "/home/" not in text, path.name


def run_of(tmp_path, name, steps):
    """A made-up project: (add-on, args as written, exit, what it printed),
    with its own folder filled into the arguments and the output."""
    project = tmp_path / name
    (project / "run").mkdir(parents=True)
    here = str(project)
    stack, log = ["## a"], []
    for place, (addon, args, code, text) in enumerate(steps, 1):
        ran = (
            args.replace("<scratch>", here)
            .replace("<pile>", here + "/pile")
            .replace("{box}", here + "/box")
        )
        stack.append(f"- {addon} -- {ran}")
        mark = __import__("hashlib").sha256(f"{addon} {ran}".encode()).hexdigest()[:8]
        log += [
            f"{place:02d} {addon}: started ({mark})",
            f"{place:02d} {addon}: exit {code}, 1 line",
        ]
        (project / "run" / f"{place:02d}-{addon}.txt").write_text(
            text.replace("<scratch>", here)
        )
    (project / "stack.md").write_text("\n".join(stack) + "\n")
    (project / "run" / "00-stack.txt").write_text("\n".join(log) + "\ndone\n")
    return project


def test_two_runs_are_compared_as_run_and_with_their_own_folders_taken_out(tmp_path):
    import same

    steps = [
        (
            "reader",
            "mirror --from <pile> --to <scratch>/out",
            0,
            "wrote 3 files to <scratch>/out\n",
        ),
        ("ids", "--box {box} kernel.py", 0, "kernel.py\n  swh:1:cnt:abc\n"),
        ("merkle", "root --box {box}", 0, "root ROOT over 2 rows\n"),
    ]
    a = run_of(tmp_path, "a", steps)
    b = run_of(
        tmp_path,
        "b",
        [
            steps[0],
            steps[1],
            ("merkle", "root --box {box}", 0, "root OTHER over 2 rows\n"),
        ],
    )
    rows = same.compare(a, b)
    assert [(r["n"], r["addon"]) for r in rows] == [
        (1, "reader"),
        (2, "ids"),
        (3, "merkle"),
    ]
    assert [r["asked"] for r in rows] == [False, False, False], (
        "each mark holds the folder it ran in"
    )
    assert [r["as_written"] for r in rows] == [True, True, True]
    assert [r["printed"] for r in rows] == [False, True, False]
    assert [r["placeless"] for r in rows] == [True, True, False]
    assert rows[2]["differs"] == ["root ROOT over 2 rows", "root OTHER over 2 rows"]
    assert "differs" not in rows[0] and all(r["exit"] for r in rows)
    assert same.first_difference("a\nb\n", "a\nb\nc\n") == ("(2 lines)", "(3 lines)")
    assert (
        same.main([str(a)]) == 2 and same.main([str(a), str(tmp_path / "absent")]) == 2
    )


def test_what_trial_fours_page_says_is_what_its_kept_files_hold():
    four = TRIAL.parent / "trial-4"

    def rows(name):
        lines = (four / name).read_text().splitlines()
        return [json.loads(line) for line in lines if line.startswith("{")], lines[-1]

    cold, cold_said = rows("cold.jsonl")
    warm, warm_said = rows("warm.jsonl")
    assert len(cold) == len(warm) == 30
    for found, placeless in ((cold, 23), (warm, 27)):
        assert (
            sum(r["asked"] for r in found) == 10
            and sum(r["as_written"] for r in found) == 30
        )
        assert (
            sum(r["printed"] for r in found) == 17
            and sum(r["placeless"] for r in found) == placeless
        )
        assert all(r["exit"] for r in found)
    assert cold_said.startswith(
        "30 steps: asked the same 10, the same as written 30, printed the same 17"
    )
    assert "the same without the place 27" in warm_said
    still = [(r["n"], r["addon"]) for r in warm if not r["placeless"]]
    assert still == [(21, "merkle"), (23, "tip-pin"), (28, "history")]
    only_cold = sorted(r["n"] for r in cold if not r["placeless"])
    assert only_cold == [3, 4, 5, 14, 21, 23, 28], (
        "the four more are the index steps and the store"
    )
    assert [r["addon"] for r in cold if r["n"] in (3, 4, 5, 14)] == [
        "index-cache"
    ] * 3 + ["pile-store"]
    assert sum(1 for r in warm[:29] if r["placeless"]) == 26, (
        "left out, the thirtieth makes it 26 of 29"
    )
    for name in ("cold.jsonl", "warm.jsonl"):
        text = (four / name).read_text()
        assert "/tmp/" not in text and "/home/" not in text, name


def test_what_the_trials_printed_is_listed_as_kept_and_what_was_written_is_not():
    here = TRIAL.parent
    kept = json.loads((here / "KEPT.json").read_text())["files"]
    written = {
        "RULES.md",
        "RESULTS.md",
        "brief.txt",
        "brief-a.txt",
        "brief-b.txt",
        "questions.txt",
    }
    printed = sorted(
        [
            f"{t.name}/{p.name}"
            for t in here.glob("trial-*")
            for p in t.iterdir()
            if p.name not in written
        ]
        + [f"study/dry/{p.name}" for p in (here / "study" / "dry").iterdir()]
        + [f"lies/dry/{p.name}" for p in (here / "lies" / "dry").iterdir()]
        + [
            p.relative_to(here).as_posix()
            for sub in ("results", "runs")
            for p in (here / "every-kind" / sub).rglob("*")
            if p.is_file()
        ]
        + [
            p.relative_to(here).as_posix()
            for sub in ("results", "runs")
            for p in (here / "study" / sub).rglob("*")
            if p.is_file()
        ]
    )
    assert kept == printed and len(kept) >= 36 + 8 + 60 + 2 + 6
    assert not [name for name in kept if name.rsplit("/", 1)[1] in written]
