"""todo.py: the things you wrote down to do, across your folder, oldest first.

    python adapters/stdlib/todo/todo.py --box DIR [--json]

Every line that marks something to do: `TODO`, `FIXME`, `- [ ]`, "need to",
"don't forget", "remember to". Oldest first, by the kernel's own date for the
passage the line is in (its `dates`: the latest date in the passage, its
file's name, or the log heading above it); undated ones last, by file.

    todo: populated, 3 lines marked to do, the oldest from 2021-04-02
      memos/2021-04-02.txt:3       2021-04-02  Need to call Mesa Mutual and take it off the policy.
      notes/todo_2024-09-09.txt:2  2024-09-09  - Q3 estimate by 15th
    ## undated
      README.md:40                 TODO: fix the install step

It prints a report, as every report add-on does (adapters/stdlib/ci/README.md,
the report contract), and `--json` gives the same report as one JSON object:
each row the file and line, then the date and the line (cut to 120
characters); the undated ones under their own heading.

The oldest open item is often the one that matters: a thing said once and
never done doesn't get newer.

A date no calendar has (1984-06-31) is no date to the kernel, so its line is
never ordered as if it were one: it's dated by the nearest real date above
it, or listed as undated.

It only reads. Exit codes, the kernel's: 0 found some (populated) or none
(empty); 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "todo"

MARK = re.compile(
    r"\bTODO\b|\bFIXME\b|^\s*[-*]\s*\[ \]|\bneed to\b|\bdon'?t forget\b|\bremember to\b",
    re.IGNORECASE,
)


def todos(pile: list[dict]) -> list[tuple[str, str, str]]:
    out = []
    for c, d in zip(pile, kernel.dates(pile)):
        when = f"{str(d)[:4]}-{str(d)[4:6]}-{str(d)[6:]}" if d else "undated"
        for i, line in enumerate(c["text"].splitlines()):
            if MARK.search(line):
                out.append((when, f"{c['path']}:{c['line'] + i}", line.strip()))
    return sorted(out)  # "undated" sorts after every YYYY-MM-DD, so undated come last


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    hits = todos(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not hits:
        say(
            report(NAME, "empty", "nothing in your folder is marked to do", []), as_json
        )
        return kernel.ALIVE
    real = [h for h in hits if h[0] != "undated"]
    dated = [(place, f"{when}  {line[:120]}") for when, place, line in real]
    undated = [(place, line[:120]) for when, place, line in hits if when == "undated"]
    said = f"{len(hits)} line{'s' if len(hits) != 1 else ''} marked to do, " + (
        f"the oldest from {real[0][0]}" if real else "none dated"
    )
    groups = [(None, dated), ("undated", undated)]
    say(report(NAME, "populated", said, groups), as_json)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
