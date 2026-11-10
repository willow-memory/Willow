"""red_on_main.py: a pull request's failing checks held to main's last run.
Python 3.9+.

    python adapters/stdlib/red-on-main/red_on_main.py --pr DIR --main DIR [--main-sha SHA] [--json]

DIR is a folder of CI records (each `record.jsonl` under it, at any depth,
as the run's `ci-record-*` artifacts download): `--pr` the pull request's
run, `--main` main's last run. For each check that failed on the pull
request, it reads the same check's last verdict on main:

    red-on-main: populated, 3 failing; 1 the pull request's, 2 red on main too
    ## the pull request's
      tests:adapters-6   green on main: this change broke it
    ## red on main too
      tests:alone        red on main at 1394b08 too: not this change's
      deps:kart          red on main at 1394b08 too: not this change's

A check red on main too is main's to fix, not the pull request's; one green
on main is the pull request's; one main's record doesn't hold (main didn't
run it, or couldn't) is said so, and left to a person. It prints a report,
as every report add-on does (adapters/stdlib/ci/README.md, the report
contract), and `--json` gives the same report as one JSON object.

It believes a record only when the kernel reads its chain whole.

Exit codes, the kernel's: 0 nothing failing is the pull request's (nothing
failed, or every failing check is red on main too); 42 one is, or main's
record doesn't say (populated); 2 refused (a bad command line, a folder
with no record, or a record whose chain doesn't hold).

It only reads. It writes nothing and goes nowhere: fetching the records is
CI's job (ci.yml's red-on-main job).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "red-on-main"
USAGE = "usage: red_on_main.py --pr DIR --main DIR [--main-sha SHA] [--json]"
FAILING, SATISFIED = "failing", "satisfied"


def verdicts(folder: Path) -> dict[str, dict]:
    """{gate: its last verdict row} over every record under `folder`, in path
    order. ValueError when there is none, or a chain doesn't hold."""
    records = sorted(folder.rglob("record.jsonl"))
    if not records:
        raise ValueError(f"no record.jsonl under {folder}")
    out: dict[str, dict] = {}
    for path in records:
        rows, breaks = kernel.read(path)
        if breaks:
            raise ValueError(f"{path}: {breaks[0]}")
        for r in rows:
            if r.get("kind") == "verdict" and isinstance(r.get("gate"), str):
                out[r["gate"]] = r
    return out


def held(
    pr: dict[str, dict], main: dict[str, dict], sha: str
) -> list[tuple[str, str, str]]:
    """(group, gate, what) for each gate failing on the pull request."""
    at = f" at {sha[:7]}" if sha else ""
    out = []
    for gate in sorted(g for g, r in pr.items() if r.get("state") == FAILING):
        there = main.get(gate, {}).get("state")
        if there == FAILING:
            out.append(
                ("red on main too", gate, f"red on main{at} too: not this change's")
            )
        elif there == SATISFIED:
            out.append(
                ("the pull request's", gate, "green on main: this change broke it")
            )
        else:
            why = (
                f"main's record says {there}"
                if there
                else "main's record doesn't hold it"
            )
            out.append(("not on main's record", gate, f"{why}: look at it yourself"))
    return out


def report(rows: list[tuple[str, str, str]]) -> dict:
    """The report every report add-on prints (ci/README.md): state, a line
    said, and each group's rows, the pull request's own first."""
    order = ("the pull request's", "red on main too", "not on main's record")
    mine = sum(g == order[0] for g, _, _ in rows)
    theirs = sum(g == order[1] for g, _, _ in rows)
    said = (f"{len(rows)} failing; {mine} the pull request's, {theirs} red on main too"
            + (f", {len(rows) - mine - theirs} not on main's record" if len(rows) > mine + theirs else ""))  # fmt: skip
    groups = [{"name": name, "rows": [{"where": gate, "what": what}
                                      for g, gate, what in rows if g == name]}
              for name in order]  # fmt: skip
    return {"addon": NAME, "state": "populated" if rows else "empty",
            "said": said if rows else "nothing failing",
            "groups": [g for g in groups if g["rows"]]}  # fmt: skip


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    opts = dict(zip(argv[0::2], argv[1::2]))
    if len(argv) % 2 or set(opts) - {"--pr", "--main", "--main-sha"} or not {"--pr", "--main"} <= set(opts):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        pr, main_ = verdicts(Path(opts["--pr"])), verdicts(Path(opts["--main"]))
    except ValueError as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    rows = held(pr, main_, opts.get("--main-sha", ""))
    doc = report(rows)
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))
    return (
        kernel.ESCALATE
        if any(g != "red on main too" for g, _, _ in rows)
        else kernel.ALIVE
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
