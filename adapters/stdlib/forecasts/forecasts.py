"""forecasts.py: a prediction written down before the outcome, settled by your
seal, and scored. Python 3.9+.

    python adapters/stdlib/forecasts/forecasts.py wager  --box DIR --p P [--now TS] CLAIM...
    python adapters/stdlib/forecasts/forecasts.py settle --box DIR [--now TS] ROW yes|no
    python adapters/stdlib/forecasts/forecasts.py score  --box DIR

`wager` writes a `wager` row: how likely you think the claim is (P, between
0.01 and 0.99) and the claim's SHA-256. The record keeps no words, so keep the
claim yourself; the hash says later that it was this claim and no other.

`settle` proposes what happened through the kernel's own door, like any
suggestion: it waits for your seal, made with `kernel.py seal` and your key.
Code never settles a wager; an outcome counts only once you have sealed it.

`score` reads the record back: each wager open, waiting on your seal, or
settled, and over the settled ones the Brier score (0 is prophecy, 0.25 is a
coin at 50%), the log score, and for each band of confidence how often you
were right. A wager with both outcomes sealed (`conflicting`), or a sealed outcome
whose file is no longer the bytes you sealed (`broken`), is said and not
scored.

Exit codes, the kernel's: `wager` 0; `settle` 42, waiting on your seal;
`score` 0, or 42 when an outcome waits on your seal or nothing is settled
yet; 2 refused (a broken outcome, a record that doesn't verify, a row that isn't a wager, one
already settled, a bad command line).
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WHO = "forecasts"
LOW, HIGH = 0.01, 0.99
_EPS = 1e-9
#: confidence bands, stated in the direction believed (a p below 0.5 is folded)
BIN_EDGES = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
SAID = {"yes": True, "no": False}


# ── the scores: willow-bot's one script's calibration.py, unchanged ─────────
def brier(confidence: float, outcome: bool) -> float:
    """Squared distance between what you said and what happened."""
    return (confidence - (1.0 if outcome else 0.0)) ** 2


def log_score(confidence: float, outcome: bool) -> float:
    """Negative log likelihood of the outcome under your stated belief."""
    p = confidence if outcome else 1.0 - confidence
    return -math.log(max(p, _EPS))


def fold(pair: tuple[float, bool]) -> tuple[float, bool]:
    """A claim thought false is a true claim restated: for the bands only."""
    p, o = pair
    return (1.0 - p, not o) if p < 0.5 else (p, o)


def bins(pairs: list[tuple[float, bool]]) -> list[dict]:
    """For each band of stated confidence, how often you were right. Empty
    bands are kept, so the whole range shows."""
    out = []
    for lo, hi in zip(BIN_EDGES, BIN_EDGES[1:]):
        members = [(c, o) for c, o in pairs if lo <= c < hi or (hi == 1.0 and c == 1.0)]
        n = len(members)
        out.append({"lo": lo, "hi": hi, "n": n,
                    "hit_rate": sum(1 for _, o in members if o) / n if n else None})  # fmt: skip
    return out


# ── the record ──────────────────────────────────────────────────────────────
def proposal(wager: dict, happened: bool) -> dict:
    """What the person seals: this wager's row hash and what happened."""
    return {
        "path": f"forecasts/{wager['n']}.json",
        "data": kernel.canon({"wager": wager["hash"], "happened": happened}),
        "cites": [],
        "claim": f"wager {wager['n']}: it " + ("happened" if happened else "didn't"),
    }


def outcomes(box: Path, rows: list[dict]) -> dict[int, dict]:
    """Each wager by row: its p, and what came of it: `open`, `waiting` (a
    settle row not yet sealed), `settled` with `happened`, `conflicting`
    (both outcomes sealed), or `broken` (a sealed outcome whose file is no
    longer the bytes sealed). A seal counts only while its proof holds under
    the person's key and its file is still the bytes sealed."""
    good = kernel.sealed(box, rows)
    out = {r["n"]: {"p": r["p"], "state": "open"} for r in rows if r["kind"] == "wager"}
    by_n = {r["n"]: r for r in rows}
    sealed: dict[int, set[bool]] = {}
    for r in rows:
        w = out.get(r.get("wager")) if r["kind"] == "settle" else None
        if w is None:
            continue
        for happened in (True, False):
            subj = kernel.subject_of(proposal(by_n[r["wager"]], happened))
            if subj != r.get("subject"):
                continue
            if subj in good:
                if kernel.standing(box, rows, subj, good[subj])[2] is None:
                    sealed.setdefault(r["wager"], set()).add(happened)
                else:
                    w["broken"] = True
            elif w["state"] == "open":
                w["state"] = "waiting"
    for n, said in sealed.items():
        if len(said) > 1:
            out[n].update(state="conflicting")
        else:
            out[n].update(state="settled", happened=said.pop())
    for w in out.values():
        if w.pop("broken", False):
            w["state"] = "broken"
    return out


def quiet(fn, *args) -> tuple[int, str]:
    """A kernel verb run with its printing caught: (exit code, what it said)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


# ── the verbs ───────────────────────────────────────────────────────────────
def wager(box: Path, p: float, claim: str, ts: str) -> int:
    row = kernel.append(box, ts, "wager", who=WHO, p=p, claim=kernel.h256(claim))
    print(f"wager row {row['n']}: p {p:g}, claim {row['claim'][:12]}…")
    print("the record keeps no words: keep the claim yourself")
    print(f"  settle it:  forecasts.py settle --box {box} {row['n']} yes|no")
    return kernel.ALIVE


def settle(box: Path, rows: list[dict], n: int, happened: bool, ts: str) -> int:
    w = next((r for r in rows if r["n"] == n and r["kind"] == "wager"), None)
    if w is None:
        return refuse(f"row {n} is not a wager")
    if outcomes(box, rows)[n]["state"] in ("settled", "conflicting", "broken"):
        return refuse(f"wager {n} is settled already; your seal is on it")
    code, said = quiet(kernel.bite, box, f"wager {n} settled", ts)
    if code == kernel.REFUSED:
        return refuse(f"the kernel wouldn't take the bite: {said.strip()}")
    prop = proposal(w, happened)
    code, said = quiet(kernel.propose, box, [json.dumps(prop)], ts)
    if code != kernel.ESCALATE:
        return refuse(f"the kernel's door: {said.strip()}")
    subj = kernel.subject_of(prop)
    kernel.append(box, ts, "settle", who=WHO, wager=n, subject=subj)
    print(f"wager {n}: {prop['claim'].split(': ', 1)[1]}, waiting on your seal")
    print(f"  seal it:  python kernel.py seal --box {box} {subj}")
    return kernel.ESCALATE


def score(box: Path, rows: list[dict]) -> int:
    told = outcomes(box, rows)
    if not told:
        print("no wagers yet: wager first, settle after")
        return kernel.ESCALATE
    pairs = [(w["p"], w["happened"]) for w in told.values() if w["state"] == "settled"]
    counts = {s: sum(1 for w in told.values() if w["state"] == s)
              for s in ("settled", "waiting", "open", "conflicting", "broken")}  # fmt: skip
    print(
        ", ".join(f"{c} {s}" for s, c in counts.items() if c)
        + f" of {len(told)} wagers"
    )
    for n, w in told.items():
        if w["state"] in ("waiting", "conflicting", "broken"):
            print(f"  row {n}: {w['state']}")
    if not pairs:
        if counts["broken"]:
            return kernel.REFUSED
        print("nothing settled yet: an outcome counts once you seal it")
        return kernel.ESCALATE
    b = sum(brier(p, o) for p, o in pairs) / len(pairs)
    ls = sum(log_score(p, o) for p, o in pairs) / len(pairs)
    print(f"Brier {b:.3f}  log score {ls:.3f}  over {len(pairs)} settled")
    for band in bins([fold(x) for x in pairs]):
        if band["n"]:
            print(f"  said {band['lo']:.1f}-{band['hi']:.1f}: right "
                  f"{band['hit_rate']:.0%} of {band['n']}")  # fmt: skip
    if counts["broken"]:
        return kernel.REFUSED
    return kernel.ESCALATE if counts["waiting"] else kernel.ALIVE


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("wager", "settle", "score"):
        return usage()
    verb, opts, words = argv[0], {}, []
    it = iter(argv[1:])
    for a in it:
        if a in ("--box", "--now", "--p"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            return usage()
        else:
            words.append(a)
    if not opts.get("--box") or any(not opts[o] for o in opts):
        return usage()
    if (
        ("--p" in opts) != (verb == "wager")
        or verb == "score"
        and (words or "--now" in opts)
    ):
        return usage()
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        return refuse("not a kernel box; init first")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse(f"the record doesn't verify ({breaks[0]}); a person looks first")
    ts = opts.get("--now") or kernel.now()
    if verb == "score":
        return score(box, rows)
    if verb == "settle":
        if (
            len(words) != 2
            or not (words[0].isascii() and words[0].isdigit())
            or words[1] not in SAID
        ):
            return usage()
        return settle(box, rows, int(words[0]), SAID[words[1]], ts)
    try:
        p = float(opts["--p"])
    except ValueError:
        return usage()
    claim = " ".join(words).strip()
    if not claim or not LOW <= p <= HIGH:
        return usage()
    return wager(box, p, claim, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
