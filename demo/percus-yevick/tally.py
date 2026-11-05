"""tally.py: the pass rules in the README, counted from the pipeline's rows.

    import tally
    tally.tally(rows, text_of, random_found)   # {rule: verdict}

`rows` are pipeline.ask's, one per question: its set (author, blind or null),
its id (the step before the first dot), and the passages served. `text_of`
maps a passage's id to its text. `random_found` is R4's count, made by
`draw()`, or None when it wasn't drawn.

A verdict is {"state", "number", "needed"}: state is "satisfied", "failing",
"not asked" (the questions it needs weren't asked) or "judged by hand" (R6,
which the rubric scores, not this). Each rule stands alone: there is no
overall verdict.

No exit codes: a module, not a command.
"""

from __future__ import annotations

import random

import score

STEPS = [s["id"] for s in score.STEPS["steps"]]
R1_AT_LEAST, R1_MUST = 9, {"s5a", "s5b", "s7"}
R2_AT_LEAST, R2_MUST = 7, {"s5b", "s7"}
R3_AT_MOST = 2
R4_AT_MOST = 2
DRAWN = 3  # random passages for each author question, as the kernel serves three


def step_of(row: dict) -> str:
    return row["id"].split(".")[0]


def hits(rows: list[dict], text_of: dict) -> dict[str, list[str]]:
    """Each step found by these rows, with the texts of the passages that hold it."""
    out: dict[str, list[str]] = {}
    for r in rows:
        step = step_of(r)
        if step not in score.BY_ID:
            continue
        held = [
            text_of[c["id"]] for c in r["served"] if score.hit(step, text_of[c["id"]])
        ]
        if held:
            out.setdefault(step, []).extend(held)
    return out


def _found_rule(found: set[str], at_least: int, must: set[str]) -> dict:
    ok = len(found) >= at_least and must <= found
    missing = sorted(set(STEPS) - found)
    return {
        "state": "satisfied" if ok else "failing",
        "number": f"{len(found)} of {len(STEPS)} found; missing {', '.join(missing) or 'none'}",
        "needed": f"at least {at_least} of {len(STEPS)}, with {', '.join(sorted(must))}",
    }


def draw(pile: list[dict], questions: int, seed: int, hit=score.hit) -> int:
    """R4: for each of `questions` author questions, `DRAWN` passages drawn
    from the pile by `seed`; the steps any of them hold, counted."""
    rng = random.Random(seed)
    found: set[str] = set()
    for _ in range(questions):
        for c in rng.sample(pile, min(DRAWN, len(pile))):
            found |= {s for s in STEPS if hit(s, c["text"])}
    return len(found)


def tally(rows: list[dict], text_of: dict, random_found: int | None) -> dict:
    author = [r for r in rows if r["set"] == "author"]
    blind = [r for r in rows if r["set"].startswith("blind")]
    null = [r for r in rows if r["set"] == "null"]
    out = {}

    a = hits(author, text_of)
    out["R1"] = (_found_rule(set(a), R1_AT_LEAST, R1_MUST) if author
                 else {"state": "not asked", "number": "no author questions", "needed": ""})  # fmt: skip

    b = hits(blind, text_of)
    out["R2"] = (_found_rule(set(b), R2_AT_LEAST, R2_MUST) if blind
                 else {"state": "not asked", "number": "no blind questions yet", "needed": ""})  # fmt: skip

    if null:
        n = sum(
            any(score.steps_held(text_of[c["id"]]) for c in r["served"]) for r in null
        )
        out["R3"] = {"state": "satisfied" if n <= R3_AT_MOST else "failing",
                     "number": f"{n} of {len(null)} null questions served a chain step",
                     "needed": f"at most {R3_AT_MOST}"}  # fmt: skip
    else:
        out["R3"] = {"state": "not asked", "number": "no null questions", "needed": ""}

    if random_found is None:
        out["R4"] = {"state": "not asked", "number": "no random draw", "needed": ""}
    else:
        out["R4"] = {"state": "satisfied" if random_found <= R4_AT_MOST else "failing",
                     "number": f"{random_found} of {len(STEPS)} steps found by random passages",
                     "needed": f"at most {R4_AT_MOST}"}  # fmt: skip

    both: dict[str, list[str]] = {}
    for found in (a, b):
        for step, texts in found.items():
            both.setdefault(step, []).extend(texts)
    through = sorted(s for s, texts in both.items() if score.through_wertheim(texts))
    out["R5"] = {"state": "satisfied" if not through else "failing",
                 "number": f"{len(through)} found steps only through Wertheim"
                           + (f": {', '.join(through)}" if through else ""),
                 "needed": "none"}  # fmt: skip

    out["R6"] = {"state": "judged by hand", "number": "scored with rubric.md, blind",
                 "needed": "found mean at least the model's, and s5 at least 2"}  # fmt: skip
    return out
