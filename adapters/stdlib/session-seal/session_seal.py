"""session_seal.py: one seal at the end of a session, over all of it. Python 3.9+.

    python adapters/stdlib/session-seal/session_seal.py --box DIR [--now TS]
    python adapters/stdlib/session-seal/session_seal.py --box DIR check

A session is the record's rows since the last one was bundled (from row 0,
the first time). Its bundle is every row by number, kind and hash, and what
came of each: what was asked, what found nothing, what was proposed and
approved. No words, since the record keeps none.

The bundle goes in through the kernel's own verbs, so nothing here can
approve it: a bite asks "session FROM to TO", and the bundle is proposed as
the answer to it, citing nothing. It waits for the person's seal, made with
`kernel.py seal` and their key: yes, these were my actions. Not sealing it
is the No; the rows stay on the record either way. Then one `session` row
says which rows it covers and its subject.

`check` reads each session back: sealed, waiting, or broken, when its
bundle no longer matches the record row for row.

Exit codes, the kernel's: 0 nothing waits; 42 a session waits on the
person's seal; 2 refused (a record that doesn't verify, a bundle that no
longer matches, a bad command line).
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "session"
#: The kernel's own words for what came of a row, in the order looked for.
SAID = ("state", "verdict")


def came_of(r: dict) -> str:
    """A row as its kind and what came of it: `bite: empty`, `proposal: pass`."""
    if r["kind"] == "bite":
        if r.get("answered_by"):
            return "bite: sealed"
        return "bite: served" if r.get("served") else "bite: empty"
    for k in SAID:
        if isinstance(r.get(k), str) and r[k]:
            return f"{r['kind']}: {r[k]}"
    return r["kind"]


def start(rows: list[dict]) -> int:
    """The open session's first row: just past the last `session` row."""
    done = [r["n"] for r in rows if r["kind"] == KIND]
    return done[-1] + 1 if done else 0


def bundle(rows: list[dict], first: int) -> dict:
    """Rows `first` to the tip, each by number, kind and hash, with counts."""
    mine = rows[first:]
    told = [came_of(r) for r in mine]
    return {
        "from": first,
        "to": mine[-1]["n"],
        "tip": mine[-1]["hash"],
        "rows": [[r["n"], r["kind"], r["hash"]] for r in mine],
        "came_of": {t: told.count(t) for t in sorted(set(told))},
    }


def quiet(fn, *args) -> tuple[int, str]:
    """A kernel verb run with its printing caught: (exit code, what it said)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def close(box: Path, ts: str) -> int:
    rows, _ = kernel.read(box / "record.jsonl")
    first = start(rows)
    if first >= len(rows):
        print("Nothing since the last session; nothing to seal.")
        return kernel.ALIVE
    b = bundle(rows, first)
    ask = f"session {b['from']} to {b['to']}"
    code, said = quiet(kernel.bite, box, ask, ts)
    if code == kernel.REFUSED:
        print(f"refused: the kernel wouldn't take the bite: {said.strip()}",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    prop = {
        "path": f"sessions/{b['from']}-{b['to']}.json",
        "data": kernel.canon(b),
        "cites": [],
        "claim": f"yes, these were my actions: rows {b['from']} to {b['to']}",
    }
    code, said = quiet(kernel.propose, box, [json.dumps(prop)], ts)
    subj = kernel.subject_of(prop)
    if code != kernel.ESCALATE:
        print(f"refused: the kernel's door: {said.strip()}", file=sys.stderr)
        return kernel.REFUSED
    row = kernel.append(box, ts, KIND, who="session-seal", subject=subj,
                        **{"from": b["from"], "to": b["to"]})  # fmt: skip
    print(f"session rows {b['from']} to {b['to']}: {len(b['rows'])} rows, "
          + ", ".join(f"{n} {t}" for t, n in b["came_of"].items()))  # fmt: skip
    print(f"waiting on your seal (row {row['n']}): {subj}")
    print(f"  seal it:  python kernel.py seal --box {box} {subj}")
    print("  or leave it unsealed: the rows stay on the record either way")
    return kernel.ESCALATE


def check(box: Path, rows: list[dict]) -> int:
    good = kernel.sealed(box, rows)
    sessions = [r for r in rows if r["kind"] == KIND]
    broken = waiting = 0
    for s in sessions:
        subj = str(s.get("subject", ""))
        try:
            prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
            ok = kernel.subject_of(prop) == subj
            b = json.loads(prop["data"])
            ok = ok and b["rows"] == [[r["n"], r["kind"], r["hash"]]
                                      for r in rows[b["from"]:b["to"] + 1]]  # fmt: skip
        except (OSError, ValueError, KeyError, TypeError):
            ok = False
        span = f"rows {s.get('from')} to {s.get('to')}"
        if not ok:
            broken += 1
            print(f"broken   {span}: its bundle no longer matches the record")
        elif subj in good:
            print(f"sealed   {span}")
        else:
            waiting += 1
            print(f"waiting  {span}: {subj}")
    first = start(rows)
    print(f"{len(sessions)} sessions: {len(sessions) - waiting - broken} sealed, "
          f"{waiting} waiting, {broken} broken; "
          f"{len(rows) - first} rows since, not yet bundled")  # fmt: skip
    if broken:
        return kernel.REFUSED
    return kernel.ESCALATE if waiting else kernel.ALIVE


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args not in ([], ["check"]):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    if args == ["check"]:
        return check(box, rows)
    return close(box, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
