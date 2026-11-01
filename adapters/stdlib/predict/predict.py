"""predict.py: what a question will come to, written down before it is asked,
graded after. Python 3.9+.

    python adapters/stdlib/predict/predict.py ask   --box DIR [--now TS] QUESTION...
    python adapters/stdlib/predict/predict.py score --box DIR

`ask` counts what the box's earlier bites came to (an answer you sealed,
passages served, or nothing found) and writes the likeliest down as a
`predict` row, on the chain before the question is asked. Then the kernel's
own bite, then a `graded` row: what it came to, and whether the prediction
was right. Counted, never guessed: a tie goes to `empty`, the answer that asks
the person, and the first bite has nothing to count, so it is not graded.

`score` reads the record back: how many were predicted, how many right, and
for each likeliest answer how often it held. It writes nothing.

The record keeps no words, so neither does this: a prediction is one of the
three states, and the counts behind it.

Exit codes, the kernel's: for `ask`, the bite's own (0 served or sealed, 42
nothing found, 2 refused); for `score`, 0, or 42 when nothing is graded yet;
2 refused (a record that doesn't verify, a bad command line).
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

SEALED, POPULATED, EMPTY = "sealed", "populated", "empty"


def came_to(r: dict) -> str:
    """What a bite row came to: a sealed answer, passages, or nothing."""
    if r.get("answered_by"):
        return SEALED
    return POPULATED if any(not s.get("echo") for s in r.get("served", [])) else EMPTY


def declare(rows: list[dict]) -> dict:
    """The likeliest of what the earlier bites came to, with the counts. Ties
    go to `empty`, then by name; with no bites yet there is nothing to say."""
    seen = [came_to(r) for r in rows if r["kind"] == "bite"]
    if not seen:
        return {"likely": None, "bites": 0, "seen": {}}
    counts = {s: seen.count(s) for s in sorted(set(seen))}
    order = sorted(counts, key=lambda s: (-counts[s], s != EMPTY, s))
    return {"likely": order[0], "bites": len(seen), "seen": counts}


def grades(rows: list[dict]) -> list[dict]:
    """Every graded prediction: a `graded` row, or a `predict` row that carries
    its own grade (the one script writes them that way), with what was likely."""
    likely = {r["n"]: r.get("likely") for r in rows if r["kind"] == "predict"}
    out = []
    for r in rows:
        if r["kind"] == "graded" and r.get("of") in likely:
            out.append({"likely": likely[r["of"]], "right": r.get("right")})
        elif r["kind"] == "predict" and "got" in r:
            out.append({"likely": r.get("likely"), "right": r.get("right")})
    return [g for g in out if isinstance(g["right"], bool)]


def quiet(fn, *args) -> tuple[int, str]:
    """A kernel verb run with its printing caught: (exit code, what it said)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def checked(box: Path) -> tuple[list[dict], str | None]:
    if not (box / "kernel.json").exists():
        return [], "not a kernel box; init first"
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return [], f"the record doesn't verify ({breaks[0]}); a person looks first"
    return rows, None


def ask(box: Path, question: str, ts: str) -> int:
    rows, why = checked(box)
    if why:
        return refuse(why)
    guess = declare(rows)
    before = kernel.append(box, ts, "predict", who="predict", **guess)
    code, said = quiet(kernel.bite, box, question, ts)
    if code == kernel.REFUSED:
        print(said.strip(), file=sys.stderr)
        return code
    rows, _ = kernel.read(box / "record.jsonl")
    bite = rows[-1]
    got = came_to(bite)
    right = None if guess["likely"] is None else guess["likely"] == got
    kernel.append(box, ts, "graded", who="predict", of=before["n"],
                  bite_row=bite["n"], got=got, right=right)  # fmt: skip
    doc = json.loads(said)
    doc["predicted"] = {**guess, "row": before["n"], "got": got, "right": right}
    print(json.dumps(doc, ensure_ascii=False))
    return code


def score(box: Path) -> int:
    rows, why = checked(box)
    if why:
        return refuse(why)
    gs = grades(rows)
    if not gs:
        print("nothing graded yet: ask through predict, and it counts from there")
        return kernel.ESCALATE
    right = sum(g["right"] for g in gs)
    print(f"{right} of {len(gs)} predictions right")
    for likely in sorted({g["likely"] for g in gs}):
        mine = [g["right"] for g in gs if g["likely"] == likely]
        print(f"  said {likely:<10} {sum(mine)} of {len(mine)} held")
    return kernel.ALIVE


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("ask", "score"):
        return usage()
    verb, opts, words = argv[0], {}, []
    it = iter(argv[1:])
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            return usage()
        else:
            words.append(a)
    if not opts.get("--box") or "--now" in opts and not opts["--now"]:
        return usage()
    box = Path(opts["--box"])
    if verb == "score":
        return usage() if words or "--now" in opts else score(box)
    question = " ".join(words)
    if not question.strip():
        return usage()
    return ask(box, question, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
