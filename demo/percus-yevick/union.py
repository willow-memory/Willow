"""union.py: freeze 2, the claim as its author meant it.

    python demo/percus-yevick/union.py --work WORK --out FILE [--box DIR] [--dry]

Freeze 1's R1 to R4 count the kernel alone. The claim of the person running
this study is wider: a stack of sources and a pile of add-ons find the
derivation. This asks every question set (author, null, every blind set)
of all five rankers in arms.py (the kernel, the kernel with words.txt,
scan's BM25, pile-rungs and latent), three passages each, and counts a step
found when any ranker serves, to that step's own question, a passage
holding it by score.py's hit rule:

- R7: the author's questions find at least 9 of 11 steps, with s5a, s5b, s7;
- R8: the blind questions find at least 7 of 11, with s5b and s7;
- R9: at most 2 of the 10 null questions are served a chain step by any ranker;
- R10: fifteen passages drawn at random for each author question (five
  rankers, three each), by seed 0, find at most 2 of 11 steps.

Reported beside them, never counted: the steps found only through
Wertheim's Laplace method or only through sticky spheres, and each ranker's
own count. WORK is pipeline.py's --work, after it has built the pile and
the index. `--dry` asks nonsense, and its random passages hold nothing.
With --box, each verdict is a kernel row, named percus-yevick:R7 and on
(percus-yevick:dry:R7 for a dry run). Exit 0, or 2 on a bad command line.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import arms  # noqa: E402  (puts the kernel, scan and latent on the path)
import pipeline  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402
import tally  # noqa: E402

SEED = 0
RANKERS = ["kernel", "kernel+words", "bm25", "pile-rungs", "latent"]
DRAWN = arms.TOP * len(RANKERS)  # fifteen: as many as the five rankers serve
R7_AT_LEAST, R7_MUST = 9, {"s5a", "s5b", "s7"}
R8_AT_LEAST, R8_MUST = 7, {"s5b", "s7"}
R9_AT_MOST = 2
R10_AT_MOST = 2
USAGE = "usage: union.py --work WORK --out FILE [--box DIR] [--dry]"


def found(qs: list[dict], ranked: dict, set_test) -> dict[str, list[str]]:
    """Each chain step found by its own question, with the rankers that found it."""
    out: dict[str, list[str]] = {}
    for i, q in enumerate(qs):
        if set_test(q["set"]) and q["step"] in score.CHAIN:
            for name in RANKERS:
                if ranked[name][i]["hit"]:
                    out.setdefault(q["step"], []).append(name)
    return out


def draw(pile: list[dict], questions: int, seed: int, hit=score.hit) -> int:
    """R10: DRAWN passages for each of `questions` questions, by `seed`."""
    rng = random.Random(seed)
    held: set[str] = set()
    for _ in range(questions):
        for c in rng.sample(pile, min(DRAWN, len(pile))):
            held |= {s for s in score.CHAIN if hit(s, c["text"])}
    return len(held)


def rule(found_steps: set[str], at_least: int, must: set[str]) -> dict:
    return tally._found_rule(found_steps, at_least, must)


def judge(qs: list[dict], ranked: dict, random_found: int) -> dict:
    author = found(qs, ranked, lambda s: s == "author")
    blind = found(qs, ranked, lambda s: s.startswith("blind"))
    nulls = [i for i, q in enumerate(qs) if q["set"] == "null"]
    served = [
        i
        for i in nulls
        if any(set(ranked[n][i]["steps"]) & set(score.CHAIN) for n in RANKERS)
    ]
    out = {
        "R7": rule(set(author), R7_AT_LEAST, R7_MUST),
        "R8": (
            rule(set(blind), R8_AT_LEAST, R8_MUST)
            if any(q["set"].startswith("blind") for q in qs)
            else {"state": "not asked", "number": "no blind questions", "needed": ""}
        ),
        "R9": {
            "state": "satisfied" if len(served) <= R9_AT_MOST else "failing",
            "number": f"{len(served)} of {len(nulls)} null questions served a chain step"
            + (f": {', '.join(qs[i]['id'] for i in served)}" if served else ""),
            "needed": f"at most {R9_AT_MOST}",
        },
        "R10": {
            "state": "satisfied" if random_found <= R10_AT_MOST else "failing",
            "number": f"{random_found} of {len(score.CHAIN)} steps found by "
            f"{DRAWN} random passages a question",
            "needed": f"at most {R10_AT_MOST}",
        },
    }
    per = {}
    for name in RANKERS:
        a = sorted(s for s, by in author.items() if name in by)
        b = sorted(s for s, by in blind.items() if name in by)
        per[name] = (
            f"author {len(a)} ({', '.join(a) or 'none'}); blind {len(b)} ({', '.join(b) or 'none'})"
        )
    out["by ranker"] = {"state": "reported", "number": "; ".join(f"{k}: {v}" for k, v in per.items()),
                        "needed": ""}  # fmt: skip
    return out


def through(qs: list[dict], texts: list[list[str]]) -> dict:
    """Reported: chain steps whose every finding passage says Laplace, or names sticky spheres."""
    by_step: dict[str, list[str]] = {}
    for q, t in zip(qs, texts):
        if q["set"] != "null" and q["step"] in score.CHAIN:
            by_step.setdefault(q["step"], []).extend(
                x for x in t if score.hit(q["step"], x)
            )
    w = sorted(s for s, t in by_step.items() if t and score.through_wertheim(t))
    st = sorted(s for s, t in by_step.items() if t and score.through_sticky(t))
    return {"state": "reported", "number": f"only through Wertheim: {', '.join(w) or 'none'}; "
            f"only through sticky spheres: {', '.join(st) or 'none'}", "needed": ""}  # fmt: skip


def texts_served(idx, qs: list[dict], pile: Path) -> tuple[dict, list[list[str]]]:
    """arms.py's rankers, unchanged, and every passage any of them served each
    question, kept on the way for the Wertheim report."""
    keep: list[list[str]] = [[] for _ in qs]
    real = arms.found_by
    where = {id(q): i for i, q in enumerate(qs)}

    def spy(q, texts):
        keep[where[id(q)]].extend(texts)
        return real(q, texts)

    arms.found_by = spy
    try:
        ranked = arms.rankers(idx, qs, pile)
    finally:
        arms.found_by = real
    return ranked, keep


def main(argv: list[str]) -> int:
    opts, dry, i = {}, False, 0
    while i < len(argv):
        if argv[i] == "--dry":
            dry, i = True, i + 1
        elif argv[i] in ("--work", "--out", "--box") and i + 1 < len(argv):
            opts[argv[i]], i = argv[i + 1], i + 2
        else:
            break
    if i != len(argv) or not {"--work", "--out"} <= set(opts):
        print(USAGE, file=sys.stderr)
        return 2
    work = Path(opts["--work"])
    if not (work / "index" / "index.json").exists():
        print("refused: run pipeline.py with this --work first", file=sys.stderr)
        return 2
    idx = scan.Index(work / "index")
    qs = arms.questions(pipeline.SETS, dry)
    ranked, texts = texts_served(idx, qs, work / "pile")
    authors = sum(q["set"] == "author" for q in qs)
    hit = (lambda s, t: False) if dry else score.hit
    result = judge(qs, ranked, draw(idx.pile, authors, SEED, hit))
    result["R5 for the union"] = through(qs, texts)
    record = {
        "dry": dry,
        "seed": SEED,
        "verdicts": result,
        "questions": qs,
        "ranked": ranked,
        "tools": {rel: pipeline.sha_file(pipeline.ROOT / rel) for rel in (
            "kernel.py", "adapters/stdlib/scan/scan.py",
            "adapters/stdlib/pile-rungs/pile_rungs.py", "adapters/deps/latent/latent.py",
            "demo/percus-yevick/score.py", "demo/percus-yevick/steps.json",
            "demo/percus-yevick/arms.py", "demo/percus-yevick/union.py")},
    }  # fmt: skip
    text = json.dumps(record, indent=1) + "\n"
    Path(opts["--out"]).write_text(text, encoding="utf-8")
    if "--box" in opts:
        counted = {
            k: v for k, v in result.items() if k.startswith("R") and " " not in k
        }
        pipeline.verdicts(Path(opts["--box"]), pipeline.kernel.now(), counted, dry,
                          hashlib.sha256(text.encode("utf-8")).hexdigest(),
                          record["tools"])  # fmt: skip
    for name, v in result.items():
        print(f"{name}  {v['state']:<10} {v['number']}"
              + (f"  (needed: {v['needed']})" if v["needed"] else ""))  # fmt: skip
    if "--box" in opts:
        print(
            f"verdicts appended to {opts['--box']}: kernel.py verify --box {opts['--box']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
