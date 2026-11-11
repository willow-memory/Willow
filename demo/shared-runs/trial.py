"""trial.py: a blind handover, small: a script's report of a kept stack run,
the key to questions about it, the strike of what a handed-on account adds,
and the score of answers given from that account alone.

    python demo/shared-runs/trial.py report PROJECT          # the script's report, printed
    python demo/shared-runs/trial.py key PROJECT             # the key, as JSON, printed
    python demo/shared-runs/trial.py strike REPORT ACCOUNT   # the account, less what the report lacks
    python demo/shared-runs/trial.py score KEY ANSWERS       # each answer: right, not said, or wrong

PROJECT is a folder a stack was run into: its box, its stack file and its
run, as demo/kept's rebuild.sh leaves them. The report is what the handover
add-on says of it, the kernel's verify line, and the first line each step
printed: nothing an agent wrote. The key is read off the same files.

`strike` holds an account to the report by its figures: a sentence that
says a number the report never says is taken out, and named on stderr. A
sentence with no figure passes; this checks what was added, not what was
meant. `score` reads answers one a line, `name: answer`, and says each is
right, not said (the answer was "not said", and the key holds one) or
wrong. A question whose key is "not said" is right only when left unsaid.

It reads what it is given and writes nothing. Exit codes, the kernel's: 0
done (strike: nothing struck; score: nothing wrong); 42 something struck,
or an answer wrong; 2 refused.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
NOT_SAID = "not said"
FIGURE = re.compile(r"\d[\d,]*(?:[.:/-]\d+)*")


def first_lines(project: Path) -> list[tuple[str, str]]:
    """(step file's name, the first line it holds) for each step of the run."""
    out = []
    for path in sorted((project / "run").glob("[0-9][0-9]-*.txt")):
        if path.name.startswith("00-"):
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        out.append((path.stem, lines[0] if lines else ""))
    return out


def scrub(text: str, project: Path) -> str:
    """The text with this machine's folders named by what they are."""
    return text.replace(str(project), "<scratch>").replace(str(ROOT), "<repo>")


def report(project: Path) -> str:
    py = sys.executable
    hand = subprocess.run(
        [py, str(ROOT / "adapters/stdlib/handover/handover.py"), "--project", str(project)],
        capture_output=True, text=True)  # fmt: skip
    verify = subprocess.run(
        [py, str(ROOT / "kernel.py"), "verify", "--box", str(project / "box")],
        capture_output=True, text=True)  # fmt: skip
    log = (project / "run" / "00-stack.txt").read_text(encoding="utf-8").splitlines()
    out = ["# what the handover add-on says", hand.stdout.rstrip(), ""]
    out += ["# what the kernel says of the record", verify.stdout.strip(), ""]
    out += ["# how the run ended", log[-1], ""]
    out += ["# the first line each step printed"]
    out += [
        f"{name}: {scrub(line, project)[:200]}" for name, line in first_lines(project)
    ]
    return scrub("\n".join(out), project) + "\n"


def key(project: Path) -> dict[str, str]:
    """The answer to each question, read off the run's own files."""
    run = project / "run"
    log = (run / "00-stack.txt").read_text(encoding="utf-8")
    first = dict(first_lines(project))
    done = re.search(r"done: (\d+) of (\d+) steps flagged", log)
    flagged = re.findall(r"^(\d\d) [a-z0-9-]+: exit (?!0,)\d+", log, flags=re.M)
    verify = subprocess.run(
        [sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(project / "box")],
        capture_output=True, text=True).stdout  # fmt: skip
    rows = re.search(r"(\d+) rows, (\d+) sealed", verify)
    glance = re.search(r"(\d+) held whole", first["07-glance"])
    xref = re.search(r"(\d+) don't hold", first["13-xref"])
    mention = re.search(r"(\d{4}-\d\d-\d\d)", first["10-first-mention"])
    thesis = re.search(r"(\d+) held", first["29-thesis"])
    same = first["20-diverge"].startswith("The same")
    return {
        "steps": done.group(2),
        "flagged-count": done.group(1),
        "flagged-steps": " ".join(flagged),
        "same-bytes": "yes" if same else "no",
        "record-rows": rows.group(1),
        "sealed": rows.group(2),
        "held-whole": glance.group(1),
        "broken-references": xref.group(1),
        "first-mention": mention.group(1),
        "thesis-held": thesis.group(1),
        "seconds": NOT_SAID,  # the run's log keeps no time
        "machines": NOT_SAID,  # nothing kept says how many
    }


def figures(text: str) -> set[str]:
    return {m.group(0).replace(",", "").rstrip(".:/-") for m in FIGURE.finditer(text)}


def strike(report_text: str, account: str) -> tuple[str, list[str]]:
    """(the account less each sentence saying a figure the report never
    says, [the sentences struck])."""
    said = figures(report_text)
    kept, struck = [], []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", account.strip()):
        if not sentence.strip():
            continue
        (struck if figures(sentence) - said else kept).append(sentence.strip())
    return "\n".join(kept) + "\n", struck


def norm(answer: str) -> str:
    a = answer.strip().strip(".").lower()
    if a in ("not said", "not stated", "unknown", "the account does not say"):
        return NOT_SAID
    nums = re.findall(r"\d{4}-\d\d-\d\d|\d+", a.replace(",", ""))
    if nums:
        return " ".join(n.zfill(2) if len(nums) > 1 and len(n) < 3 else n for n in nums)
    return "yes" if a.startswith("yes") else "no" if a.startswith("no") else a


def score(keyed: dict[str, str], answers: str) -> dict[str, str]:
    """{question: right | not said | wrong | unanswered}."""
    given = {}
    for line in answers.splitlines():
        name, sep, answer = line.partition(":")
        if sep and name.strip() in keyed:
            given[name.strip()] = norm(answer)
    out = {}
    for name, want in keyed.items():
        got = given.get(name)
        if got is None:
            out[name] = "unanswered"
        elif got == norm(want):
            out[name] = "right"
        elif got == NOT_SAID:
            out[name] = "not said"
        else:
            out[name] = "wrong"
    return out


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] in ("report", "key") and Path(argv[1]).is_dir():
        project = Path(argv[1]).resolve()
        if argv[0] == "report":
            sys.stdout.write(report(project))
        else:
            print(json.dumps(key(project), indent=1))
        return kernel.ALIVE
    if (
        len(argv) == 3
        and argv[0] == "strike"
        and all(Path(a).is_file() for a in argv[1:])
    ):
        kept, struck = strike(*(Path(a).read_text(encoding="utf-8") for a in argv[1:]))
        sys.stdout.write(kept)
        for sentence in struck:
            print(f"struck: {sentence}", file=sys.stderr)
        return kernel.ESCALATE if struck else kernel.ALIVE
    if (
        len(argv) == 3
        and argv[0] == "score"
        and all(Path(a).is_file() for a in argv[1:])
    ):
        keyed = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        marks = score(keyed, Path(argv[2]).read_text(encoding="utf-8"))
        for name, mark in marks.items():
            print(f"{name}: {mark}")
        counts = {m: sum(1 for v in marks.values() if v == m) for m in ("right", "not said", "wrong", "unanswered")}  # fmt: skip
        print(", ".join(f"{n} {m}" for m, n in counts.items()))
        return (
            kernel.ESCALATE if counts["wrong"] or counts["unanswered"] else kernel.ALIVE
        )
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
