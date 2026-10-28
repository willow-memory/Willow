"""score.py: did a served passage land on the fix? The hit rule.

    python demo/known-gaps/score.py --to DIR ANSWERS.jsonl

ANSWERS is what ask.py wrote; DIR is trees.py's `--to`, whose fixes/ holds
each unit's diff. Each answer is scored against its unit's fix, asked of the
vulnerable side.

The rule is php2shell's rule 2 (phase3.py `changed`) by position, not by text:
a passage hits when its line range in the old file, [line, line + its lines -
1], overlaps a line the fix removed, or the one unchanged line just before or
just after a run of added lines (the old-side line number the diff gives).
php2shell's `hit` matches a line by its stripped text anywhere in the file, so
an identical line far from every hunk was a hit: 68 of 159 hit passages over
the 14 old trees were that (Loki's audit). Text matching is kept as a reported
column (`hit_by_text`), never the rule. A line counts when it is at least 8
characters and 2 of the kernel's words long. Context lines further away never count. Never
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
import re
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


def positions(diff: str) -> tuple:
    """(pos, hunks): per old path, the old-side line numbers rule 2 counts (a
    removed line; the unchanged line just before and just after a run of added
    lines, in the same hunk), and each hunk's old-side range. Read by the
    hunk header's counts, so a removed line that reads like a file header is
    still a line."""
    pos: dict = {}
    hunks: dict = {}
    meaningful = phase3.score.meaningful
    lines = diff.splitlines()
    i, path = 0, None
    while i < len(lines):
        ln = lines[i]
        i += 1
        if ln.startswith("--- "):
            path = ln[6:] if ln.startswith("--- a/") else None
        elif ln.startswith("@@"):
            m = HUNK.match(ln)
            if not m:
                continue
            old_no = int(m.group(1))
            old_rem = int(m.group(2) if m.group(2) is not None else 1)
            new_rem = int(m.group(4) if m.group(4) is not None else 1)
            keep = path is not None and counts(path)
            if keep:
                hunks.setdefault(path, []).append(
                    (old_no, old_no + max(old_rem, 1) - 1)
                )
            prev = None  # (kind, old line number, text) of the line before
            run = False
            while (old_rem > 0 or new_rem > 0) and i < len(lines):
                ln = lines[i]
                i += 1
                kind, text = ln[:1], ln[1:].strip()
                if kind == "\\":
                    continue
                if kind == " ":
                    if run and keep and meaningful(text):
                        pos.setdefault(path, set()).add(old_no)
                    run = False
                    prev = (" ", old_no, text)
                    old_no += 1
                    old_rem -= 1
                    new_rem -= 1
                elif kind == "-":
                    if keep and meaningful(text):
                        pos.setdefault(path, set()).add(old_no)
                    run = False
                    prev = ("-", old_no, text)
                    old_no += 1
                    old_rem -= 1
                else:  # "+"
                    if (
                        not run
                        and prev
                        and prev[0] == " "
                        and keep
                        and meaningful(prev[2])
                    ):
                        pos.setdefault(path, set()).add(prev[1])
                    run = True
                    prev = ("+", old_no, text)
                    new_rem -= 1
    return pos, hunks


HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def changed(diff: str) -> dict:
    """phase3.changed (rule 2) with this folder's files left out, and the
    positions rule 2 counts (`pos`) and each hunk's old range (`hunks`)."""
    was = phase3.counts
    phase3.counts = counts
    try:
        fix = phase3.changed(diff)
        fix["pos"], fix["hunks"] = positions(diff)
        return fix
    finally:
        phase3.counts = was


def span(passage: dict) -> range:
    """The old-file lines a passage covers."""
    return range(passage["line"], passage["line"] + len(passage["text"].splitlines()))


def hit_by_text(passage: dict, fix: dict) -> bool:
    """php2shell's rule: a line of the passage reads like a removed or
    neighbouring line, wherever it sits. Reported, not the rule."""
    return phase3.hit(passage, fix)


def hit(passage: dict, fix: dict) -> bool:
    """The rule: the passage's lines include a line the fix changed or
    borders, by position."""
    pos = fix["pos"].get(passage["path"])
    return bool(pos) and any(n in pos for n in span(passage))


def in_a_hunk(passage: dict, fix: dict) -> bool:
    """The passage overlaps some hunk of the fix in its file."""
    return any(a <= n <= b for a, b in fix["hunks"].get(passage["path"], [])
               for n in span(passage))  # fmt: skip


def classify(passage: dict, fix: dict) -> str:
    if hit(passage, fix):
        return "hit"
    return "file" if passage["path"] in fix["files"] else "miss"


def hit_lines(passage: dict, fix: dict) -> list:
    """The line numbers within a passage that the rule counts, by position."""
    pos = fix["pos"].get(passage["path"], set())
    return [n for n in span(passage) if n in pos]


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
