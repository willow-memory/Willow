"""rules.py: the next step of a stack, chosen by rule from what its last run
said, in the form a link of the chain replies in.

    python demo/shared-runs/rules.py next PROJECT

PROJECT is one chain.py made. Each rule reads what a step printed and
names the add-on whose job that is. The first rule that fits is the reply:

    repair    a step was refused as "not a kernel box": the same step
              again, with the record where the record goes
    explain   glance says some questions found nothing, and no step has
              said why: why-not, given what scan found
    by-pile   why-not says the box's files hold them, so the nothing was
              in another pile: fair-merge, each pile ranked alone, for
              each such question

When none fits it says so, and that is the answer: a gap, for a person or
a new rule. It reads the project and writes nothing. Exit codes, the
kernel's: 0 a step is offered; 42 no rule fits; 2 a bad command line.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
from chain import steps_of  # noqa: E402

USAGE = __doc__.split("\n\n")[1]


def state(project: Path) -> list[dict]:
    """Each step of the stack: its place, add-on, arguments as written, how
    its last run ended, and what it printed."""
    log = (project / "run" / "00-stack.txt").read_text(encoding="utf-8")
    out = []
    for place, (name, args) in enumerate(
        steps_of((project / "stack.txt").read_text()), 1
    ):
        ended = re.findall(
            rf"^{place:02d} {re.escape(name)}: exit (\d+)", log, flags=re.M
        )
        files = sorted((project / "run").glob(f"{place:02d}-*.txt"))
        text = files[0].read_text(encoding="utf-8", errors="replace") if files else ""
        out.append({"place": place, "name": name, "args": args,
                    "exit": int(ended[-1]) if ended else None, "text": text})  # fmt: skip
    return out


def found_nothing(glance_text: str) -> list[str]:
    """The questions glance lists under `## found nothing`, each once."""
    section = re.search(r"^## found nothing\n((?:  .*\n?)+)", glance_text, flags=re.M)
    asked = []
    for line in section.group(1).splitlines() if section else ():
        question = re.sub(r"^\s*\S+\s+", "", line).strip()
        if question and question not in asked:
            asked.append(question)
    return asked


def reply(want: str, step: str, why: str) -> str:
    return f"want: {want}\nstep: {step}\nwhy: {why}\ncards: none\n"


def repair(steps: list[dict]) -> str | None:
    have = {(s["name"], s["args"]) for s in steps}
    for s in steps:
        box = re.search(r"--box (\S+)", s["args"])
        if (
            s["exit"] == 2
            and "not a kernel box" in s["text"]
            and box
            and box.group(1) != "{box}"
        ):
            fixed = s["args"].replace(box.group(0), "--box {box}", 1)
            if (s["name"], fixed) not in have:
                return reply(
                    f"Run step {s['place']:02d} again with the record where the record goes.",
                    f"- {s['name']} -- {fixed}",
                    f"Step {s['place']:02d} ({s['name']}) was refused as not a kernel box: "
                    f"it was given {box.group(1)} for --box, and the record is {{box}}.",
                )
    return None


def explain(steps: list[dict]) -> str | None:
    glance = next(
        (s for s in steps if s["name"] == "glance" and s["exit"] is not None), None
    )
    scan = next((s for s in steps if s["name"] == "scan" and s["exit"] == 0), None)
    if not glance or not scan or not found_nothing(glance["text"]):
        return None
    if any(s["name"] == "why-not" and s["exit"] in (0, 42) for s in steps):
        return None
    n = len(found_nothing(glance["text"]))
    return reply(
        f"Say why the {n} question{'' if n == 1 else 's'} that found nothing found nothing.",
        f"- why-not -- --box {{box}} --questions <scratch>/questions.txt --of {{{scan['place']:02d}}}",
        f"Step {glance['place']:02d} (glance) lists {n} under found nothing, and no step says why.",
    )


def by_pile(steps: list[dict]) -> str | None:
    glance = next(
        (s for s in steps if s["name"] == "glance" and s["exit"] is not None), None
    )
    said = next(
        (s for s in steps if s["name"] == "why-not" and s["exit"] in (0, 42)), None
    )
    if not glance or not said or "nothing to explain" not in said["text"]:
        return None
    folders = ["<pile>"]
    for s in steps:  # a reader's mirror is a pile of its own
        to = re.search(r"mirror .*--to (\{box\}-[a-z]+)", s["args"])
        if to and s["exit"] == 0:
            folders.append(to.group(1))
    if len(folders) < 2:
        return None
    sources = " ".join(f"--from {f}" for f in folders)
    have = {(s["name"], s["args"]) for s in steps}
    for question in found_nothing(glance["text"]):
        if '"' in question:
            continue
        args = f'{sources} --top 6 "{question}"'
        if ("fair-merge", args) not in have:
            return reply(
                "Ask each pile on its own the question that found nothing, to see which pile lacks it.",
                f"- fair-merge -- {args}",
                f"Step {said['place']:02d} (why-not) says the box's files hold it, and step "
                f"{glance['place']:02d} (glance) says it found nothing, so the nothing was in "
                f"another of the {len(folders)} piles.",
            )
    return None


RULES = (("repair", repair), ("explain", explain), ("by-pile", by_pile))


def next_step(project: Path) -> tuple[str | None, str]:
    """(the rule that fit, its reply), or (None, why none did)."""
    steps = state(project)
    for name, rule in RULES:
        got = rule(steps)
        if got:
            return name, got
    return None, f"no rule fits: {len(steps)} steps, {len(RULES)} rules tried\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "next" or not Path(argv[1]).is_dir():
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    rule, said = next_step(Path(argv[1]).resolve())
    sys.stdout.write(said)
    return kernel.ALIVE if rule else kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
