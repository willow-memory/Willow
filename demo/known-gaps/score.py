"""score.py: did a served passage land on the fix? The hit rule.

    python demo/known-gaps/score.py --to DIR ANSWERS.jsonl

ANSWERS is what ask.py wrote; DIR is trees.py's `--to`, whose fixes/ holds
each unit's diff. Each answer is scored against its unit's fix, asked of the
vulnerable side.

The rule is php2shell's rule 2 (phase3.py `changed` and `hit`): a passage
hits when it holds a line the fix removed, or the one unchanged line next to
a run of added lines. A line counts when it is at least 8 characters and 2 of
the kernel's words long. Context lines further away never count. Never
counted: any path with a folder named test, tests, testing, spec or changes;
a file named test_*.py, *_test.py or conftest.py; files named NEWS, UPGRADING,
ChangeLog, CHANGES, CHANGES.md, CHANGELOG.md, version.h, RELEASE-NOTES.md,
VERSION, version.txt, version.py, _version.py or .release-please-manifest.json;
and a CHANGELOG file. php2shell's own counts() is kept and added to.

A passage is `hit` when it holds a counted line, `file` when its file is one
the fix changed but none of its lines is, and `miss` otherwise. An answer's
score is its best passage's, with the rank of the first `hit` and the
`path:first-last` ranges of the hit lines.

Prints one JSON line an answer. Exit 0, or 2 for a bad command line or a
missing fix.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees  # noqa: E402

phase3 = trees.phase3
PHP2SHELL_COUNTS = phase3.counts  # phase3.counts is swapped for ours inside changed()
ORDER = ("hit", "file", "miss")
SKIP_NAMES = frozenset({"VERSION", "version.txt", "version.py", "_version.py",
                        ".release-please-manifest.json"})  # fmt: skip


def counts(path: str) -> bool:
    """php2shell's counts(), and also a test file named beside its code, a
    changelog and a version file."""
    name = path.rsplit("/", 1)[-1]
    return (
        PHP2SHELL_COUNTS(path)
        and not (name.startswith("test_") and name.endswith(".py"))
        and not name.endswith("_test.py")
        and name != "conftest.py"
        and not name.upper().startswith("CHANGELOG")
        and name not in SKIP_NAMES
    )


def changed(diff: str) -> dict:
    """phase3.changed (rule 2) with this folder's files left out."""
    was = phase3.counts
    phase3.counts = counts
    try:
        return phase3.changed(diff)
    finally:
        phase3.counts = was


def hit(passage: dict, fix: dict) -> bool:
    return phase3.hit(passage, fix)


def classify(passage: dict, fix: dict) -> str:
    if hit(passage, fix):
        return "hit"
    return "file" if passage["path"] in fix["files"] else "miss"


def hit_lines(passage: dict, fix: dict) -> list:
    """The line numbers within a passage of the lines the rule counts."""
    old = fix["old"].get(passage["path"], set())
    return [passage["line"] + n for n, ln in enumerate(passage["text"].splitlines())
            if ln.strip() in old]  # fmt: skip


def ranges(passage: dict, fix: dict) -> list:
    out = []
    for n in hit_lines(passage, fix):
        if out and out[-1][1] + 1 == n:
            out[-1][1] = n
        else:
            out.append([n, n])
    return [f"{passage['path']}:{a}-{b}" for a, b in out]


def score(answers: list, fixes: Path) -> list:
    loaded: dict = {}
    out = []
    for a in answers:
        if a["unit"] not in loaded:
            loaded[a["unit"]] = changed(
                (fixes / f"{a['unit']}.diff").read_text(encoding="utf-8")
            )
        fix = loaded[a["unit"]]
        got = [classify(s, fix) for s in a["served"]]
        best = min(got, key=ORDER.index, default="miss")
        first = next((i for i, g in enumerate(got, 1) if g == "hit"), None)
        out.append({"unit": a["unit"], "gap": a["gap"], "question": a["question"],
                    "ranked_by": a["ranked_by"], "best": best, "first_hit_rank": first,
                    "served": got,
                    "ranges": [r for s in a["served"] for r in ranges(s, fix)]})  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != "--to":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    try:
        rows = [json.loads(x) for x in Path(argv[2]).read_text().splitlines()]
        scored = score([r for r in rows if r.get("type") == "answer"],
                       Path(argv[1]) / "fixes")  # fmt: skip
    except OSError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    for r in scored:
        print(json.dumps(r))
    tally = {k: sum(r["best"] == k for r in scored) for k in ORDER}
    print(json.dumps({"answers": len(scored), **tally}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
