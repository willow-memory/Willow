"""score2.py: the second hit rule, frozen before phase 1 ran.

Phase 2 found the first rule (score.py) blind where the fix only added code:
asking the old code, only removed lines count, so the passage the fix added
lines into scored `file`. This rule keeps every line score.py counts and,
asking the old code, also counts each added run's neighbours: the one
unchanged line just before a run of added lines and the one just after, in
the same hunk. Anything further away still never counts. The same seven
CORE files, the same test files and NEWS left out, the same `meaningful`.

It was made after phase 2's results, to be run on questions none of which
had been asked yet (the blind sets of phase 1). score.py stays as frozen and
is reported beside it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score  # noqa: E402

RULE_1 = score.changed  # kept, since score_answers puts this rule in its place


def changed(diff: str) -> dict[str, dict[str, set[str]]]:
    """score.changed, with each added run's unchanged neighbours on the old side."""
    out = RULE_1(diff)
    old = None
    prev: str | None = None  # the line before, as the diff gives it, within a hunk
    in_run = False
    for ln in diff.splitlines() + [""]:
        if ln.startswith("--- "):
            old = ln[6:] if ln.startswith("--- a/") else None
            prev, in_run = None, False
            continue
        if ln.startswith(("+++ ", "@@", "diff ")):
            prev, in_run = None, False
            continue
        kind, text = ln[:1], ln[1:].strip()
        keep = old and score.counts(old)
        if kind == "+":
            if not in_run and prev is not None and prev[:1] == " " and keep:
                anchor(out, old, prev[1:].strip())
            in_run = True
        elif kind == " ":
            if in_run and keep:
                anchor(out, old, text)
            in_run = False
        else:
            in_run = False
        prev = ln
    return out


def anchor(out: dict, path: str, line: str) -> None:
    if score.meaningful(line):
        out["old"].setdefault(path, set()).add(line)


def score_answers(answers: list[dict], fixes: Path) -> list[dict]:
    """score.score under this rule."""
    was = score.changed
    score.changed = changed
    try:
        return score.score(answers, fixes)
    finally:
        score.changed = was
