"""score.py: did a served passage land on the PHP2Shell fix? The frozen rule.

    python demo/php2shell/score.py --fixes DIR ANSWERS.jsonl

ANSWERS is what `scan.py scan` printed; DIR is make_trees.py's `--to`, whose
fixes/ holds each security commit's diff. Each answer is scored against the
fix of its index's branch (releases.json): a vulnerable release, or one
before, against the code the fix removed; a fixed release against the code
it added. A release on a branch with no fix of its own (5.6 to 8.1) is
scored against the 8.2 fix, and marked "nearest".

The rule, frozen before any phase ran (FROZEN.json holds this file's hash):

- A changed line is a line the security commit removed (`-`) or added (`+`),
  stripped of spaces at its ends, at least 8 characters and 2 of the
  kernel's words long. Context lines never count.
- Test files (any path with a `tests` folder, or ending .phpt) and NEWS and
  UPGRADING never count.
- A passage is `core` when it holds a changed line of a CORE file, `any`
  when it holds a changed line of another file, `file` when its file is one
  the commit changed but none of its lines is, and `miss` otherwise.
- An answer's score is its best passage's, with the rank of the first
  passage scoring `core` or `any`.

CORE is the advisories' mechanisms (multipart parsing, POST variables, the
memory limit's bailout, session upload progress) and the request startup
the commit message names. It was chosen after the first look at results,
and says so in the README.

Prints one JSON line an answer, then a count of scores. Exit 0, or 2 for a
bad command line or a missing fix.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import kernel  # noqa: E402

PINS = json.loads((HERE / "releases.json").read_text(encoding="utf-8"))
CORE = frozenset({
    "main/rfc1867.c", "main/php_variables.c", "main/SAPI.c", "main/main.c",
    "Zend/zend_alloc.c", "ext/session/session.c", "ext/session/php_session.h",
})  # fmt: skip
ORDER = ("core", "any", "file", "miss")


def counts(path: str) -> bool:
    parts = path.split("/")
    return not (
        "tests" in parts or path.endswith(".phpt") or parts[-1] in ("NEWS", "UPGRADING")
    )


def meaningful(line: str) -> bool:
    return len(line) >= 8 and len(kernel.words(line)) >= 2


def changed(diff: str) -> dict[str, dict[str, set[str]]]:
    """{"old"|"new": {file: its changed lines}}, and every file the commit
    changed under "files", from a unified diff."""
    out: dict[str, dict] = {"old": {}, "new": {}, "files": {}}
    old = new = None
    for ln in diff.splitlines():
        if ln.startswith("--- "):
            old = ln[6:] if ln.startswith("--- a/") else None
        elif ln.startswith("+++ "):
            new = ln[6:] if ln.startswith("+++ b/") else None
            for f in (old, new):
                if f and counts(f):
                    out["files"][f] = set()
        elif ln.startswith("-") and old and counts(old) and meaningful(ln[1:].strip()):
            out["old"].setdefault(old, set()).add(ln[1:].strip())
        elif ln.startswith("+") and new and counts(new) and meaningful(ln[1:].strip()):
            out["new"].setdefault(new, set()).add(ln[1:].strip())
    return out


def classify(where: str, text: str, fix: dict, side: str) -> str:
    path = where.rsplit(":", 1)[0]
    lines = {x.strip() for x in text.splitlines()}
    if lines & fix[side].get(path, set()):
        return "core" if path in CORE else "any"
    return "file" if path in fix["files"] else "miss"


def branch_of(version: str) -> tuple[str, str, bool]:
    """(the fix's branch, the side to score, whether it is the nearest fix)."""
    for b, f in PINS["fixes"].items():
        if version == f["fixed"]:
            return b, "new", False
    b = ".".join(version.split(".")[:2])
    if b in PINS["fixes"]:
        return b, "old", False
    return "8.2", "old", True


def score(answers: list[dict], fixes: Path) -> list[dict]:
    loaded: dict[str, dict] = {}
    out = []
    for a in answers:
        b, side, nearest = branch_of(a["index"])
        if b not in loaded:
            loaded[b] = changed((fixes / f"{b}.diff").read_text(encoding="utf-8"))
        got = [classify(s["where"], s["text"], loaded[b], side) for s in a["served"]]
        best = min(got, key=ORDER.index, default="miss")
        first = next((i for i, g in enumerate(got, 1) if g in ("core", "any")), None)
        out.append({"index": a["index"], "question": a["question"], "fix": b, "side": side,
                    "nearest": nearest, "best": best, "first_hit_rank": first, "served": got})  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != "--fixes":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    fixes = Path(argv[1]) / "fixes"
    try:
        rows = score(
            [json.loads(x) for x in Path(argv[2]).read_text().splitlines()], fixes
        )
    except OSError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    for r in rows:
        print(json.dumps(r))
    tally = {k: sum(r["best"] == k for r in rows) for k in ORDER}
    print(json.dumps({"answers": len(rows), **tally}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
