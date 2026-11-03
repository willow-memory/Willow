"""session_seal.py: one seal at the end of a session, over all of it. Python 3.9+.

    python adapters/stdlib/session-seal/session_seal.py --box DIR [--now TS]
    python adapters/stdlib/session-seal/session_seal.py --box DIR check [--json]

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
bundle no longer matches the record row for row. It prints a report, as
every report add-on does (adapters/stdlib/ci/README.md, the report
contract), a group per state, and `--json` gives the same report as one
JSON object. `check` as a function prints its own lines, as it always has.

Exit codes, the kernel's: 0 nothing waits (for `check`, every session
sealed, or none yet: empty); 42 a session waits on the person's seal, or
(for `check`) one's bundle is broken; 2 refused (a record that doesn't
verify, a bad command line).
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "session-seal"
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


def each_session(box: Path, rows: list[dict]) -> list[tuple[str, str, str]]:
    """Each `session` row read back: (its span, `sealed`, `waiting` or
    `broken`, its subject). Broken is a bundle no longer the record's rows."""
    good = kernel.sealed(box, rows)
    out = []
    for s in (r for r in rows if r["kind"] == KIND):
        subj = str(s.get("subject", ""))
        try:
            prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
            ok = kernel.subject_of(prop) == subj
            b = json.loads(prop["data"])
            ok = ok and b["rows"] == [[r["n"], r["kind"], r["hash"]]
                                      for r in rows[b["from"]:b["to"] + 1]]  # fmt: skip
        except (OSError, ValueError, KeyError, TypeError):
            ok = False
        state = "broken" if not ok else "sealed" if subj in good else "waiting"
        out.append((f"rows {s.get('from')} to {s.get('to')}", state, subj))
    return out


def tally(told: list[tuple[str, str, str]], rows: list[dict]) -> str:
    """The sessions counted, and the rows since the last, on one line."""
    n = {k: sum(1 for _, s, _ in told if s == k) for k in ("waiting", "broken")}
    return (f"{len(told)} sessions: {len(told) - n['waiting'] - n['broken']} "
            f"sealed, {n['waiting']} waiting, {n['broken']} broken; "
            f"{len(rows) - start(rows)} rows since, not yet bundled")  # fmt: skip


def check(box: Path, rows: list[dict]) -> int:
    told = each_session(box, rows)
    for span, state, subj in told:
        if state == "broken":
            print(f"broken   {span}: its bundle no longer matches the record")
        elif state == "sealed":
            print(f"sealed   {span}")
        else:
            print(f"waiting  {span}: {subj}")
    print(tally(told, rows))
    if any(s == "broken" for _, s, _ in told):
        return kernel.REFUSED
    return kernel.ESCALATE if any(s == "waiting" for _, s, _ in told) else kernel.ALIVE


#: the report's groups, in its order: what waits on you first
GROUPS = {
    "broken": ("broken", "its bundle no longer matches the record: {subj}"),
    "waiting": ("waiting on your seal", "python kernel.py seal --box {box} {subj}"),
    "sealed": ("sealed", "{subj}"),
}


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


def check_report(box: Path, rows: list[dict]) -> tuple[dict, int]:
    """`check` as a report, by state, and its exit code: 42 when a session
    waits on your seal or its bundle is broken, both yours to look at."""
    told = each_session(box, rows)
    if not told:
        said = (f"no session bundled yet; {len(rows) - start(rows)} rows since,"
                " not yet bundled")  # fmt: skip
        return report(NAME, "empty", said, []), kernel.ALIVE
    groups = [(name, [(span, what.format(box=box, subj=subj))
                      for span, s, subj in told if s == state])
              for state, (name, what) in GROUPS.items()]  # fmt: skip
    code = kernel.ESCALATE if any(s != "sealed" for _, s, _ in told) else kernel.ALIVE
    return report(NAME, "populated", tally(told, rows), groups), code


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        elif a == "--json":
            opts[a] = "yes"
        else:
            args.append(a)
    if (
        not opts.get("--box")
        or args not in ([], ["check"])
        or ("--json" in opts and args != ["check"])
    ):
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
        doc, code = check_report(box, rows)
        say(doc, "--json" in opts)
        return code
    return close(box, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
