r"""score.py: the hit rule. Whether a served passage holds a step of the chain.

    import score
    score.hit("s7", passage_text)          # True when it holds step s7
    score.steps_held(passage_text)         # every step it holds
    score.traps(passage_text)              # the traps it holds
    score.through_wertheim(passages)       # every hit says "Laplace"

steps.json says what each step is and what holds it: an anchor's words must
all be in the passage (any case, whole words), and when it names regular
expressions, one of them must match the passage's math, normalized. A step
is held when any one of its anchors is.

Normalizing takes out what changes a formula's look and not its meaning:
spaces, `\left` and `\right` and the `\big` sizes, `\,` and the other
spacing commands, `\displaystyle`; `\dfrac` and `\tfrac` read as `\frac`;
`\mathrm{e}` as `e`; and the packing fraction's other names, `\phi`,
`\varphi` and `\xi`, as `\eta`. Nothing else: a formula in another form
(`1/(1-\eta)^2` written out as a product, say) is not held. That is the
rule's strictness, stated, not an oversight.

No exit codes: a module, not a command.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = json.loads((HERE / "steps.json").read_text(encoding="utf-8"))
CHAIN = [s["id"] for s in STEPS["steps"]]
EXTENDED = [s["id"] for s in STEPS.get("extended", [])]
BY_ID = {s["id"]: s for s in STEPS["steps"] + STEPS.get("extended", [])}

_DROP = re.compile(
    r"\\(?:left|right|[Bb]igg?[lr]?|displaystyle|textstyle|quad|qquad)(?![A-Za-z])"
    r"|\\[,;:! ]|~"
)
_FRAC = re.compile(r"\\[dt]frac(?![A-Za-z])")
_ETA = re.compile(r"\\(?:var)?phi(?![A-Za-z])|\\xi(?![A-Za-z])")
_E = re.compile(r"\\mathrm\{e\}")


def normalize(text: str) -> str:
    """A passage's math with its looks taken out (see the module's doc)."""
    text = _DROP.sub("", text)
    text = _FRAC.sub(r"\\frac", text)
    text = _ETA.sub(r"\\eta", text)
    text = _E.sub("e", text)
    return "".join(text.split())


def _has_word(word: str, text: str) -> bool:
    return (
        re.search(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", text, re.I)
        is not None
    )


def holds(anchor: dict, text: str) -> bool:
    """One anchor: all its words in `text`, and one of its expressions, if it
    names any, in `text`'s normalized math."""
    if not all(_has_word(w, text) for w in anchor.get("words", [])):
        return False
    pats = anchor.get("regex", [])
    if not pats:
        return True
    math = normalize(text)
    return any(re.search(p, math) for p in pats)


def hit(step: str, text: str) -> bool:
    return any(holds(a, text) for a in BY_ID[step]["anchors"])


def steps_held(text: str) -> list[str]:
    """The chain's steps a passage holds; the extended steps are asked for by name."""
    return [s for s in CHAIN if hit(s, text)]


def extended_held(text: str) -> list[str]:
    return [s for s in EXTENDED if hit(s, text)]


def traps(text: str) -> list[str]:
    math = normalize(text)
    return [
        t["id"] for t in STEPS["traps"] if any(re.search(p, math) for p in t["regex"])
    ]


def through_wertheim(passages: list[str]) -> bool:
    """A step reached only through Wertheim's method: there were passages
    holding it, and every one of them says the forbidden words."""
    words = STEPS["forbidden"]["words"]
    return bool(passages) and all(all(_has_word(w, p) for w in words) for p in passages)


def through_sticky(passages: list[str]) -> bool:
    """A step reached only through Baxter's sticky spheres: there were
    passages holding it, and every one of them names them."""
    words = STEPS["sticky"]["any_words"]
    return bool(passages) and all(any(_has_word(w, p) for w in words) for p in passages)
