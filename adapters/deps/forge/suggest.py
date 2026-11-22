"""suggest.py: the Forge's matchmaker over this willow's add-on cards.
Python 3.11+ (forge-play's floor), forge-play 0.10 or newer.

    python adapters/deps/forge/suggest.py suggest --box DIR "what you want done" [--defaults FILE|none] [--json | --plan]
    python adapters/deps/forge/suggest.py propose --box DIR "what you want done" [--defaults FILE|none]
                                                  --choose WORD=NAME ... [--why WORD=REASON ...] [--json]
    python adapters/deps/forge/suggest.py build   --box DIR "what you want done" --to STACK [--json]
    python adapters/deps/forge/suggest.py next    --box DIR "what you want done" --stacks FOLDER [--json]
    python adapters/deps/forge/suggest.py scores  --box DIR [--json]

A sentence in, the add-ons it names or means out. The Forge's card box reads
every card beside this script (built, and the ideas in adapters/planned.json)
as rows for its keyword scan: a card's name, and the lines of
ui/search-words.txt that point at it, are what a sentence can hit. `suggest`
says what comes out as a report (adapters/stdlib/ci/README.md, the report
contract), a group per kind of thing:

    forge: populated, 2 forks wait on you
    ## fork “email”
      adapters/stdlib/apple-mail/README.md  apple-mail: Apple Mail's .emlx ...
      adapters/stdlib/mail/README.md        mail: Email in .eml and mbox ...

    steps   an add-on the sentence reaches and nothing else does, one line
            for a stack file; or a fork you settled before, read from your
            record: the kernel serves it only while its seal proves under
            your key, so it is a step, not a question, and you are not asked
            twice
    fork    one word that reaches several add-ons ("email": mail, apple-mail):
            a decision with the cards as options and their lines as tradeoffs
    stale   a seal whose card no longer does that word here; said, and the
            fork asked again
    ideas   an add-on the sentence names that isn't built yet
    close   for a sentence no card name or alias line reaches, the built
            cards similar's search points at (`Want`, the canvas's search),
            at most three, the first recommended, and `none`: a fork, never
            a step, each row saying it is close and not named. Its decision
            is this sentence's own (`willow-close-<hash of the words>`), so
            a seal for one sentence settles no other; `none`, sealed, keeps
            the miss on your record and runs nothing. Its proposal keeps
            what was shown: the cards in their order, the one recommended,
            the rank of your pick, and the matcher that ranked them. One
            close fork in five, by the hash of its words, is blind: its cards
            in an order of their own, nothing recommended and no confidence
            said, so your pick there measures the search and not your trust
            in it; its proposal keeps the search's order, your pick's rank in
            it, the order you saw, and the confidence it kept unsaid

`next` says what could go in after what you have: the steps of the stack you
sealed for these words (or, before one is sealed, what the words reach and
the defaults), held against every stack file under FOLDER, your own. For
each card you don't have, it counts how often your stacks put it beside a
step you do: "with mail in 9 of 12". It looks beside the steps your words or
picks brought, not the defaults, and it scores a card by how much more often
it sits beside those steps than in your stacks at large: a card in nearly
every stack is beside everything, says nothing, and is not offered. Counting
and nothing else, no model and no search: it offers what you have done
before, never what might be good. Beside that, said apart, it offers what you have never
stacked: built cards in none of your stacks that the catalogue's own search
puts near your words or near a step you have, so a card gets a first chance
that counting alone would never give it. A default is not looked beside: it
suits any folder, so what is near it says nothing of what you are after. It
writes nothing and asks nothing; exit 0.

`scores` reads those back: over the close decisions you sealed that still
stand, how often you took the first (the recommendation), the second, the
third, or none, all together and per matcher (known by the cards it ranks
first for ten fixed sentences, not by its bytes), and each one. Its blind
picks are the matchmaker's measured hit rate, the only number a close
fork's confidence comes from: once you have sealed five blind close picks
on one matcher, the fork says you took its first k of n and states
(k+1)/(n+2) as its confidence, never 1, and none while that is under one
half. A pick made with the recommendation in view counts not: it would
measure how often you went with it. `scores` sets the two rates side by
side, and scores each blind fork's kept confidence against your pick with
the Forge's calibration (Brier). It writes nothing; exit 0, empty before
any is sealed.

A stack you sealed for these very words is served first, as the kernel
serves any sealed answer, and nothing else is asked.

    several a fork may take more than one card: `--choose WORD=A,B`, or
            `--choose WORD=A` given again with B. Any one might be good, and
            more than one often is ("research": jeles and almanac). It is
            still one decision and one proposal: the one the search put
            highest is `chose`, the rest `also`, each with its card pinned;
            every one is a step of the stack. `none` and `not-now` stand
            alone. A close fork is scored on `chose`, so taking a second
            card with the search's first neither helps nor hurts its score.
    not-now every fork's other way out, beside `none`: `--choose WORD=not-now`
            leaves it undecided, and says so on your record. Not deciding is
            a decision: it is a proposal of its own, under its own question
            ("forge not now willow-WORD"), sealed or declined like any other,
            with your reason. The fork's own question stays unanswered, so
            the fork stays open, is offered again, and nothing is scored;
            the other steps and settled forks still make a stack. The report
            says each fork you said not now to, and each pick that waits on
            your seal, so neither goes quiet: a pick is scored only once
            sealed, and a stack sealed without its pick says which is left.
    defaults  the add-ons named in defaults.txt, beside this script: in every
            stack proposed, after the steps your words reached, because they
            suit any folder (open items, what is due, what is kept twice).
            A default is never an option of the `close` fork and is never
            scored, so picking one can't be taken for the search being
            right. One your words reached, or that a word's fork offers, is
            that step or that option and not a default too. They ride with
            a stack and never make one: with no step and no fork there is
            still nothing to run. A line naming no built add-on is said.
            `--defaults FILE` reads a list of your own, and `--defaults none`
            proposes with none; give `propose` what you gave `suggest`.

`propose` settles the open forks with `--choose WORD=NAME` (and a reason with
`--why WORD=...`) and hands the result to the kernel's door, nothing more:
one proposal per settled fork, under the words `forge decision willow-WORD`,
and one for the stack, under your sentence. Each waits on your seal
(`python kernel.py seal --box DIR proposal:...`); nothing is an answer before
that, and nothing runs. It carries the card's name, line, path and SHA-256,
so what you sealed is what you were shown. Its report is one row per
proposal: where it will be written, and what waits.

`build` runs the stack you sealed for these words, and nothing else: it
reads the sealed stack from the record (never a file you could edit), puts
each step's add-on into STACK with ui/assemble.py (every file hashed onto the
stack's own record, each contract checked), writes the stack file beside it,
and runs the stack add-on over your box, keeping the page at STACK/page.md.
Its report is one row per step: copied or not, its contract, and how it ran.
A step that can't be copied (one that works only in this repository) is
said and left out, never guessed at; a deps add-on goes in under
adapters/deps/ with its packages unchecked, and its step is flagged. It
refuses while no
stack is sealed for these words: the seal is the one gate between a
suggestion and a run. STACK's parent must exist; it never makes one.

--json prints the same report as one JSON object. --plan prints the whole as
the Forge reads it: the cards counted, the steps, the forks, what is sealed,
the ideas, and `plan`, a document forge.plan_shape validates,
forge.decision_extract turns into decisions and forge.build_loop resolves.
No model, and no ranking of its own: a step is a card that was named or an
alias line names; what similar's search ranks is only ever the `close`
fork's options and its recommendation, with a confidence only from your
own sealed picks, and the report says which is which.

What is sealed is read through the kernel's own `sealed` and `standing`: a
seal counts only while its proof holds under the key and the proposal still
hashes to what was sealed; the key is the kernel's to read, never this
script's. The first standing seal for a decision is the one kept, as the
kernel's bite serves the first for a question, so the Forge (which asks the
kernel) and this read the same answer; a later seal waits its turn until the
first no longer stands. Decisions are keyed by decision type, `willow-WORD`,
the words the Forge asks for, so one it proposed is read the same as one this
script proposed.

Exit codes, the report's: 0 steps found and nothing waits on you, a stack
sealed for these words, nothing named (`empty`), or a stack built with every
step run clean; 42 a fork waits on you, your seal is waited on, a built
stack with a step flagged or left out (`populated`), or forge-play missing
or older than 0.10 (`unreachable`, said); 2 refused (a bad command line, a
folder that isn't a box or whose record doesn't verify, a fork left
unsettled or settled with an option not on offer, a stack sealed for these
words already, no stack sealed for these words to build, a STACK whose
parent is missing, a card beside this script that won't read).

Phrases: the kernel's words list holds one word to a key, so the table at the
top of this file (NEEDS_PHRASE, NAMES) says what a word cannot. "back" reaches
backup only with "up" within a word or two ("back up", "back it up"), so "due
back" does not; "things to do", "still have to do", "left to do", "to-do" and
"to do list" name todo. Bare "to do" does not: it is in "what do I want to do".
Every verb reads the sentence through it, so they agree.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

NAME = "forge"
APP = "willow-stack"
STACK_PATH = "forge/stack.md"
NEEDS = "forge-play 0.10 or newer is not installed: pip install -r adapters/deps/forge/requirements.txt"
SIMILAR = ROOT / "adapters/stdlib/similar/similar.py"
DEFAULTS = HERE / "defaults.txt"
DEFAULT_WHY = "a default: in every stack, not asked and not scored"

#: Phrases, as data. The kernel's words list (ui/search-words.txt) is one word
#: to a key, and a multi-word key blanks the whole list, so it cannot say
#: "back up" or "things to do". Two kinds of row, applied to the scan's hits
#: (see `phrased`):
#:   NEEDS_PHRASE  a hit made by this word stands only if the sentence also
#:                 has one of the phrases (the hit then reads as the phrase)
#:   NAMES         these phrases name the add-on on their own
#: "to do" alone is not named: it is in "what do I want to do with this folder".
NEEDS_PHRASE = {
    "back": (
        "backup",
        r"back(?:\s+\w+){0,2}\s+up",
    ),  # back up, back it up, back them all up
}
NAMES = {
    "todo": (
        "a list of open items, said in more than one word",
        r"things\s+(?:(?:i|we)\s+)?(?:still\s+)?(?:have\s+|need\s+)?to\s+do"
        r"|(?:still\s+)?(?:have|need)\s+(?:still\s+)?to\s+do"
        r"|(?:left|more|else)\s+to\s+do"
        r"|to-do"
        r"|to\s+do\s+(?:list|items?)",
    ),
}
_EDGE = r"(?<![\w-])(?:{})(?![\w-])"


def phrased(hits: list, sentence: str) -> list:
    """The scan's hits, as the phrase table above reads them: a hit from a
    word in NEEDS_PHRASE is dropped unless its phrase is in the sentence (and
    then says the phrase as what it matched); a NAMES phrase adds a hit for
    its add-on when the scan has none for it. Same sentence, same answer, for
    every verb."""
    from dataclasses import replace

    out = []
    for h in hits:
        rule = NEEDS_PHRASE.get(h.matched)
        if rule is None or h.target != rule[0]:
            out.append(h)
        elif m := re.search(_EDGE.format(rule[1]), sentence, re.IGNORECASE):
            out.append(replace(h, matched=" ".join(m.group(0).lower().split())))
    for name, (reason, pattern) in NAMES.items():
        if any(h.target == name for h in out):
            continue
        if m := re.search(_EDGE.format(pattern), sentence, re.IGNORECASE):
            from forge.majors import Hit

            said = " ".join(m.group(0).lower().split())
            out.append(Hit(source=said, target=name, reason=reason, matched=said))
    return out


def defaults(by_name: dict) -> tuple[list[tuple[str, str]], list[str]]:
    """([(name, why it is a default)], [lines that name no built add-on]),
    from defaults.txt, in its order, each name once. No file, no defaults."""
    if not DEFAULTS.is_file():
        return [], []
    held, missing = [], []
    for raw in DEFAULTS.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, _, why = line.partition(" ")
        if name in by_name and by_name[name].built:
            if name not in [n for n, _ in held]:
                held.append((name, why.strip()))
        else:
            missing.append(name)
    return held, missing


#: the fork for a sentence no name or alias line reaches, and its way out
CLOSE, NONE = "close", "none"
#: a fork's other way out: not deciding it yet, which is a decision of its own
NOT_NOW = "not-now"
NOT_NOW_PATH = "forge/not-now/{}.json"
NOT_NOW_TRADEOFF = (
    "leave this one undecided: sealed, that is on your record as a decision "
    "of its own; the fork stays open and nothing is scored"
)


def not_now_question(dt: str) -> str:
    """The words a not-now is proposed and sealed under: never the decision's
    own, so the decision's question stays unanswered for the pick to come."""
    return f"forge not now {dt}"


#: how many cards similar's search may put in that fork
NEAR = 3
DOUBTED = "named, but not close: the search puts it nowhere near your words"
NONE_TRADEOFF = (
    "none of these does it: sealed, the miss is on your record and nothing runs"
)


def wanting():
    """similar's `Want` (its search for a card in a person's words), or None
    when this willow's similar hasn't one: then a sentence that names no
    card is said to name none, as before."""
    if not SIMILAR.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("willow_forge_similar", SIMILAR)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:  # noqa: BLE001  an older or broken similar: no search, said by its absence
        return None
    return getattr(mod, "Want", None)


#: how far down similar's search a card the scan reached alone may sit and
#: still be a step: past it, the search doesn't place the card near your words
AGREE = NEAR * 4
_SEARCH: dict = {}


def searched(sentence: str) -> list[dict] | None:
    """similar's search for a sentence, its first AGREE as [{name, why}], or
    None when this willow's similar hasn't one. Built once a run."""
    if _SEARCH.get("from") is not wanting:  # built again if the search was swapped
        want = wanting()
        _SEARCH.clear()  # and what was known of the old one (its ranks) with it
        _SEARCH.update({"from": wanting, "want": want() if want is not None else None})
    if _SEARCH["want"] is None:
        return None
    return _SEARCH["want"].find(sentence, top=AGREE)["found"]


def near(sentence: str, by_name: dict, leave_out: set = frozenset()) -> list[dict]:
    """The built cards similar's search points at for a sentence, best
    first, at most NEAR: [{name, why}]. Pointing, never answering: they are
    a fork's options and its recommendation, and never a step."""
    found = searched(sentence) or []
    out = [f for f in found if f["name"] in by_name and by_name[f["name"]].built
           and f["name"] not in leave_out]  # fmt: skip
    # the search's "you named it" (its whole name's words are in yours, in
    # another form than the scan reads) is said as that: the scan named none
    return [
        {**f, "why": "the words of its name are in yours"}
        if f["why"] == "you named it"
        else f
        for f in out[:NEAR]
    ]


#: the sentences a matcher is known by: demo/want-finders' ten wants, as that
#: study froze them on 2026-11-16, kept here so this needs no demo to run
PROBES = (
    "write down a prediction before the person is asked, and score it once they pick",
    "count how often each suggestion was sealed or declined",
    "keep a no with its reason and the condition that would reopen it",
    "check that my tests catch a broken line of code",
    "pin the ledger's tip outside the box so a truncation is caught",
    "which tests can a change reach",
    "a sealed answer stands only while what it cites still hashes the same",
    "what each step of a stack takes from an earlier step",
    "score a model against the answers the person sealed",
    "find a rubber stamp in the reasons people give",
)


def matcher() -> dict:
    """What ranks a close fork's cards, known by what it does, not by its
    bytes: the SHA-256 of the cards similar's search puts first, in order,
    for each of PROBES ("absent" with no search). A score is kept per
    matcher, so an edit to similar.py or the words list that moves no card
    keeps the count, and one that moves any card, or a new card that comes
    in among them, starts a count of its own. Asked once a run."""
    if searched(PROBES[0]) is None:
        return {"ranks": "absent"}
    if "ranks" not in _SEARCH:
        ranks = [[f["name"] for f in searched(p)] for p in PROBES]
        _SEARCH["ranks"] = kernel.h256(json.dumps(ranks, ensure_ascii=False))
    return {"ranks": _SEARCH["ranks"]}


#: one close fork in BLIND_EVERY is blind: its cards in an order that says
#: nothing of the search's, with no recommendation and no confidence, so a
#: pick there measures the search and not your trust in what it said
BLIND_EVERY = 5
BLIND_SAID = (
    f"blind (one close fork in {BLIND_EVERY}): in no order of the search's, "
    "nothing recommended, so your pick measures the search"
)
#: what every row of a blind fork says of itself, the same on each: the
#: search's own reasons ("email usually means", "the words of its name are in
#: yours") come in its order, and would say which it put first
BLIND_ROW = "close to your words or named in them; the search's reasons kept back"


def blind(sentence: str) -> bool:
    """Whether this sentence's close fork is blind: by the hash of its words,
    so suggest and propose agree, and nothing is kept to decide it."""
    key = kernel.bite_key(sentence) or sentence
    return int(kernel.h256(f"blind {key}")[:8], 16) % BLIND_EVERY == 0


def shuffled(sentence: str, names: list[str]) -> list[str]:
    """A blind fork's cards as shown: ordered by the hash of the sentence and
    each name, the same each time it is asked, and nothing of the search's."""
    key = kernel.bite_key(sentence) or sentence
    return sorted(names, key=lambda n: kernel.h256(f"shown {key} {n}"))


#: how many blind close picks you sealed on one matcher before its first
#: card is given a confidence: fewer is no measurement, and none is said
MEASURED = 5


def confidence(every: list[dict], now: dict) -> tuple[float | None, str]:
    """The close fork's confidence and what to say of it, from your sealed
    blind picks alone: of the blind close forks you settled on this matcher
    (the same ranks on PROBES), you took the search's first k of n, stated
    as (k+1)/(n+2), so five of five is 0.86 and never a certainty. A pick
    made with the recommendation in view counts not: it says how often you
    went with it, which it would have lifted. None before MEASURED are
    sealed, or when it falls under one half: the Forge states a confidence
    only in the direction it believes."""
    same = [o for o in every if o["kind"] == "close" and o.get("blind")
            and o["matcher"] == now]  # fmt: skip
    n, k = len(same), sum(o["rank"] == 1 for o in same)
    if n < MEASURED:
        return (
            None,
            f"no confidence yet: {n} of {MEASURED} blind close picks sealed on this matcher",
        )
    if 2 * k < n:  # (k+1)/(n+2) < 1/2
        return (
            None,
            f"no confidence: its first taken {k} of {n} blind on this matcher, under half",
        )
    c = min(round((k + 1) / (n + 2), 2), 0.99)
    return c, f"confidence {c:.2f}: its first taken {k} of {n} blind on this matcher"


def outcomes(box: Path, rec) -> list[dict]:
    """Every fork you settled and sealed that still stands, through the
    kernel: {kind, word, decision_type, sentence, offered, chose, rank,
    matcher, confidence, blind, row}; `offered` is in the search's order and
    `rank` is where the pick fell in it, blind or not; `confidence` is what
    the close fork said (or, blind, kept unsaid) when you were asked (None
    when it had none); `blind` is whether you were asked without the
    recommendation in view. `kind` is "close" for the search's fork and
    "word" for one a word reached through its name or alias line. A proposal
    from before `offered` was kept is left out: it says nothing of what was
    shown."""
    rows, _ = kernel.read(box / "record.jsonl")
    out = []
    for subj, row in kernel.sealed(box, rows).items():
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None or not prop["path"].startswith(
            rec.DECISION_PATH.split("{")[0]
        ):
            continue
        try:
            data = json.loads(prop["data"])
        except ValueError:
            continue
        dt = data.get("decision_type") if isinstance(data, dict) else None
        if (
            not isinstance(dt, str)
            or not isinstance(data.get("offered"), list)
            or not data["offered"]
        ):
            continue
        kind = "close" if dt.startswith(rec.decision_type(CLOSE) + "-") else "word"
        out.append({"kind": kind, "word": data.get("word", ""), "decision_type": dt,
                    "sentence": data.get("sentence", ""), "offered": data["offered"],
                    "chose": data.get("chose"), "rank": data.get("rank"),
                    "matcher": data.get("matcher") or {},
                    "confidence": data.get("confidence"),
                    "blind": data.get("blind") is True, "row": row["n"]})  # fmt: skip
    return sorted(out, key=lambda o: o["row"])


def scores(box: Path, rec) -> tuple[dict, int]:
    """Where each sealed pick fell. For the close fork, how often you took
    each place: the first (the recommendation), the second, the third, or
    none, all together and per matcher. For a word's fork, how often its
    alias line's cards held (you took one) or didn't (none): a word that keeps
    getting none is a line of ui/search-words.txt to argue. Writes nothing."""
    every = outcomes(box, rec)
    if not every:
        return report(
            NAME, "empty", "no fork settled by your seal yet", []
        ), kernel.ALIVE
    got = [o for o in every if o["kind"] == "close"]
    words = [o for o in every if o["kind"] == "word"]
    n = len(got)

    def tally(outs: list[dict]) -> list[tuple[str, str]]:
        places = [("first, the recommendation", 1), ("second", 2), ("third", 3)]
        rows = [(f"rank {r}", f"{label}: {sum(o['rank'] == r for o in outs)} of {len(outs)}")
                for label, r in places]  # fmt: skip
        rows.append(
            (
                "none",
                f"none of them: {sum(o['rank'] is None for o in outs)} of {len(outs)}",
            )
        )
        return rows

    def known_as(m: dict) -> str:
        if "ranks" in m:  # by what it ranks (this one's own)
            return f"ranks {m['ranks'][:12]}"
        # by the bytes it read, as forge 0.3 kept it: a count of its own
        return f"similar {m.get('similar', '?')[:12]}, words {m.get('words', '?')[:12]}"

    by_matcher: dict[str, list[dict]] = {}
    for o in got:
        by_matcher.setdefault(known_as(o["matcher"]), []).append(o)
    matchers = [(m, f"the first taken {sum(o['rank'] == 1 for o in outs)} of {len(outs)}")
                for m, outs in by_matcher.items()]  # fmt: skip
    by_word: dict[str, list[dict]] = {}
    for o in words:
        by_word.setdefault(o["word"], []).append(o)
    held = [(f"“{w}”", f"a card taken {sum(o['rank'] is not None for o in outs)} of "
             f"{len(outs)}, none {sum(o['rank'] is None for o in outs)}")
            for w, outs in sorted(by_word.items())]  # fmt: skip

    def said_of(o: dict) -> str:
        asked = f"“{o['sentence']}”" if o["kind"] == "close" else f"“{o['word']}”"
        picked = (f"rank {o['rank']} of {', '.join(o['offered'])}" if o["rank"] else
                  f"none of {', '.join(o['offered'])}")  # fmt: skip
        return f"{asked}: {o['chose']}, {picked} (row {o['row']})"

    # the confidence the close fork says now; the first taken blind and with
    # the recommendation in view, side by side (the gap is how far it is
    # followed for being said); and each confidence kept on a blind fork,
    # scored against your pick with the Forge's own calibration (Brier: 0 is
    # foresight, 0.25 a coin at one half). One said in view is never scored:
    # the pick it would be scored on is one it could have moved.
    trust = [("now", confidence(every, matcher())[1])] if got else []
    for where, outs, how in (
        ("blind", [o for o in got if o["blind"]], "blind"),
        ("in view", [o for o in got if not o["blind"]], "with the recommendation in view"),
    ):  # fmt: skip
        if outs:
            hit = sum(o["rank"] == 1 for o in outs)
            trust.append((where, f"its first taken {hit} of {len(outs)} {how}"))
    pairs = [(o["confidence"], o["rank"] == 1) for o in got
             if o["blind"] and isinstance(o["confidence"], (int, float))]  # fmt: skip
    if pairs:
        try:
            from forge import calibration
        except ImportError:
            trust.append(
                ("scored", f"{len(pairs)} said, unscored: forge.calibration missing")
            )
        else:
            s = calibration.summary(pairs)
            trust.append(("scored", f"brier {s['brier']:.3f} over {s['n']} said; "
                          f"mean said {s['mean_confidence']:.2f}, its first taken "
                          f"{s['hit_rate']:.2f}"))  # fmt: skip
    asks = [(rec.DECISION_PATH.format(o["decision_type"]), said_of(o)) for o in every]
    first = sum(o["rank"] == 1 for o in got)
    took = sum(o["rank"] is not None for o in words)
    bits = []
    if got:
        bits.append(f"{n} close, the first taken {first} of {n}")
    if words:
        bits.append(f"{len(words)} by a word, a card taken {took} of {len(words)}")
    m = len(every)
    said = f"{m} fork{'s' if m != 1 else ''} settled by your seal: " + "; ".join(bits)
    groups = [("close: by rank", tally(got) if got else []),
              ("close: by matcher", matchers if got else []),
              ("close: its confidence", trust),
              ("by a word: did its line's cards hold", held), ("each", asks)]  # fmt: skip
    return report(NAME, "populated", said, groups), kernel.ALIVE


def fork_type(rec, word: str, sentence: str) -> str:
    """A fork's decision type: the word said, or, for the `close` fork, the
    sentence itself, so a seal for one sentence never settles another."""
    if word != CLOSE:
        return rec.decision_type(word)
    key = kernel.bite_key(sentence) or sentence
    return rec.decision_type(f"{CLOSE}-{kernel.h256(key)[:12]}")


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
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


def forge():
    """The Forge's card box, plan shape and record naming, or None when
    forge-play is missing or too old to have them. Imported here, not at the
    top, so a bad command line is refused the same with or without it."""
    try:
        from forge import card_box, card_table, plan_shape, willow_record
    except ImportError:
        return None
    return card_box, card_table, plan_shape, willow_record


def quiet(fn, *args) -> tuple[int, str]:
    """A kernel verb run with its printing caught: (exit code, what it said)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def is_box(box: Path) -> str | None:
    """Why `box` can't be used, or None: not a box, or a record that
    doesn't verify. Nothing is read past a break."""
    if not (box / "kernel.json").is_file():
        return f"{box} is not a box (no kernel.json)"
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return "the record doesn't verify: " + "; ".join(breaks)
    return None


def on_record(box: Path, rec) -> tuple[dict, dict]:
    """What the person sealed, through the kernel: ({decision_type: {chose,
    word, row, subject}}, {bite_key: {row, subject, text}}). The first
    standing seal for a decision is the one kept, as the kernel keeps it."""
    rows, _ = kernel.read(box / "record.jsonl")
    decisions, stacks = {}, {}
    for subj, row in kernel.sealed(box, rows).items():
        prop, asked, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            continue
        if prop["path"] == STACK_PATH:
            stacks.setdefault(
                asked, {"row": row["n"], "subject": subj, "text": prop["data"]}
            )
        elif prop["path"].startswith(rec.DECISION_PATH.split("{")[0]):
            try:
                data = json.loads(prop["data"])
            except ValueError:
                continue
            if isinstance(data, dict) and isinstance(data.get("chose"), str):
                dt = data.get("decision_type")
                if not isinstance(dt, str) and isinstance(data.get("word"), str):
                    dt = rec.decision_type(data["word"])
                if isinstance(dt, str):
                    decisions.setdefault(
                        dt,
                        {"chose": data["chose"], "word": data.get("word", ""),
                         "also": [n for n in data.get("also") or [] if isinstance(n, str)],
                         "row": row["n"], "subject": subj},
                    )  # fmt: skip
    return decisions, stacks


def undecided(box: Path, rec) -> tuple[dict, dict]:
    """What isn't settled yet and why, through the kernel: ({decision_type:
    {row, subject, why}}, the latest not-now you sealed for it, under its own
    question; {decision_type: [{row, subject, chose}]}, each pick or not-now
    that passed the door and that you neither sealed nor declined)."""
    rows, _ = kernel.read(box / "record.jsonl")
    later: dict = {}
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, asked, why = kernel.standing(box, rows, subj, row)
        if why is not None or not prop["path"].startswith(NOT_NOW_PATH.split("{")[0]):
            continue
        try:
            data = json.loads(prop["data"])
            dt = data["decision_type"]
        except (ValueError, KeyError, TypeError):
            continue
        if isinstance(dt, str) and asked == kernel.bite_key(not_now_question(dt)):
            later[dt] = {
                "row": row["n"],
                "subject": subj,
                "why": str(data.get("why", "")),
            }
    waits: dict = {}
    mine = (rec.DECISION_PATH.split("{")[0], NOT_NOW_PATH.split("{")[0])
    for subj, row in kernel.waiting(box, rows).items():
        try:
            prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
            data = json.loads(prop["data"]) if prop["path"].startswith(mine) else None
            dt, chose = data["decision_type"], data["chose"]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if (
            kernel.subject_of(prop) == subj
            and isinstance(dt, str)
            and isinstance(chose, str)
        ):
            waits.setdefault(dt, []).append(
                {"row": row["n"], "subject": subj, "chose": chose}
            )
    return later, waits


def held_back(out: dict, rec) -> list[tuple[str | None, list]]:
    """The report's two groups for what isn't settled: the forks you said not
    now to, and the picks that wait on your seal, each said so it never goes
    quiet. A pick is scored only once it is sealed."""
    return [
        ("you said not now", [
            (NOT_NOW_PATH.format(got["decision_type"]),
             f"“{w}” left undecided, by your seal (row {got['row']})"
             + (f": {got['why']}" if got["why"] else ""))
            for w, got in out.get("not_now", {}).items()]),
        ("picked, not sealed yet", [
            ((NOT_NOW_PATH if g["chose"] == NOT_NOW else rec.DECISION_PATH).format(dt),
             ("not now" if g["chose"] == NOT_NOW else g["chose"])
             + f" for “{w}”, proposed at row {g['row']}; it waits on your seal, and nothing is scored until then")
            for w, (dt, got) in out.get("unsealed", {}).items() for g in got]),
    ]  # fmt: skip


def promises(card) -> str:
    bits = [f"writes {card.writes or '?'}", f"network {card.network or '?'}"]
    if card.needs:
        bits.append(f"needs {card.needs}")
    if not card.built:
        bits.append("an idea, not built")
    return "; ".join(bits)


def tradeoff(card) -> str:
    return f"{card.line} ({promises(card)})"


#: each add-on's step line, `NAME -- ARGS`, filled by `commands`; the default
#: when the contract's rows can't be read is the one every page add-on takes
STEPS: dict[str, str] = {}
CONTRACT = ROOT / "adapters/stdlib/ci/test_contract.py"


def commands(pile: str) -> tuple[dict[str, str], str]:
    """Each add-on's own good command line, from the ci add-on's contract
    (test_contract.py's COMMANDS: the argv its contract test runs against a
    fresh box), as a step's args: `{box}` kept for the stack add-on to fill,
    `{pile}` filled with this box's folder, `{tmp}` kept for `build` to fill
    with a folder of its own, and the test's pinned `--now` taken off so the
    add-on runs at the real now. ({name: args}, where they came from); the
    ci add-on absent, or pytest (which its test file imports) missing, is
    said, and every step then takes the default `--box {box}`."""
    if not CONTRACT.is_file():
        return {}, "the ci add-on isn't here; steps take --box {box}"
    try:
        spec = importlib.util.spec_from_file_location("willow_contract", CONTRACT)
        tc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tc)
    except Exception as e:  # noqa: BLE001  the reason is the message (pytest, say)
        return (
            {},
            f"the ci add-on's contract couldn't be read ({type(e).__name__}: {e}); steps take --box {{box}}",
        )
    out = {}
    for name, (_, argv) in tc.COMMANDS.items():
        args, skip = [], False
        for a in argv:
            if skip:
                skip = False
                continue
            if a == "--now":
                skip = True
                continue
            a = a.replace("{pile}", pile)
            args.append(shlex.quote(a) if re.search(r"[\s'\"]", a) else a)
        out[name] = " ".join(args)
    return out, "from the ci add-on's contract, each add-on's own good command line"


def step_line(name: str) -> str:
    return f"- {name} -- {STEPS.get(name, '--box {box}')}\n"


def plan(
    box,
    hits,
    shape,
    rec,
    sealed: dict,
    sentence: str = "",
    measured=(None, ""),
) -> dict:
    """{cards, steps, forks, sealed, ideas, plan}, and `close` while that fork
    is open: what the sentence reaches, what the record settled, and the
    Forge's plan document (or None when there is nothing to run). A sentence
    that reaches no card by name or alias line gets the `close` fork: what
    similar's search points at, the first recommended, and `none` beside
    them. `measured` is `confidence()`'s (value, said): the close fork's
    confidence, from your sealed blind picks, or none; or a function that
    gives it, asked only when there is a close fork (knowing the matcher
    builds the search, a second, which a sentence with no close fork never
    needs)."""
    found = list(box.lookup(hits))
    # every fork offers `none`: a word's alias line can point wrong, and the
    # person saying so is an outcome, kept like any pick
    forks = {word: names + [NONE] for word, names in box.forks(hits).items()}
    by_name = {c.name: c for c in box.cards}
    reached = {c.name for c in found}
    # a card the scan reached alone is a step only while similar's search
    # agrees it is near these words; one it puts nowhere near is asked about
    in_forks = {n for names in forks.values() for n in names}
    alone = [c for c in found if c.name not in in_forks and by_name[c.name].built]
    doubted = []  # the search is built only when there is a step to check (a second)
    if sentence and alone and (ranked := searched(sentence)) is not None:
        placed = {f["name"] for f in ranked}
        doubted = [c for c in alone if c.name not in placed]
        found = [c for c in found if c not in doubted]
    kept, not_here = defaults(by_name)
    # a default never competes: the search's fork doesn't offer one
    close = (
        near(sentence, by_name, reached | {n for n, _ in kept})
        if sentence and (doubted or not found)
        else []
    )
    options = [f["name"] for f in close] + [c.name for c in doubted]
    if options:
        found += [SimpleNamespace(name=f["name"], why=f["why"]) for f in close]
        found += [SimpleNamespace(name=c.name, why=DOUBTED) for c in doubted]
        forks[CLOSE] = options + [NONE]
    if callable(measured):  # asked only now there is a close fork to say it for
        measured = measured() if options else (None, "")
    why_close = {f["name"]: f"close, not named: {f['why']}" for f in close}
    why_close.update({c.name: DOUBTED for c in doubted})
    settled, open_forks = {}, {}
    for word, names in forks.items():
        dt = fork_type(rec, word, sentence)
        got = sealed.get(dt)
        if got and got["chose"] in names:
            settled[word] = {**got, "decision_type": dt}
        else:
            open_forks[word] = names
            if got:
                settled[word] = {**got, "decision_type": dt,
                                 "stale": f"{got['chose']} no longer does “{word}” here"}  # fmt: skip
    in_fork = {n for names in open_forks.values() for n in names}
    chosen = {n: word for word, got in settled.items() if "stale" not in got
              for n in (got["chose"], *got.get("also", []))}  # fmt: skip
    in_any_fork = {n for names in forks.values() for n in names}
    steps, ideas, entries = [], [], []
    for cand in found:
        card = by_name[cand.name]
        if cand.name in in_fork:
            continue
        if cand.name in chosen:
            word = chosen[cand.name]
            why = f"you sealed it for “{word}” (row {settled[word]['row']})"
        elif card.name in in_any_fork:
            continue  # the other option of a settled fork
        else:
            why = cand.why
        if not card.built:
            ideas.append(
                {"name": cand.name, "line": card.line, "why": why, "where": card.where}
            )
            continue
        steps.append({"name": cand.name, "line": card.line, "why": why, "where": card.where,
                      "promises": promises(card)})  # fmt: skip
        entries.append(
            shape.FileWrite(
                dest_path=f"steps/{cand.name}.md", content=step_line(cand.name)
            )
        )
    # the defaults, after what the words reached: not one that is a step
    # already, or an option of a fork (there it is the person's to pick)
    stepped = {s["name"] for s in steps}
    riding = [
        {"name": n, "line": by_name[n].line, "why": why, "where": by_name[n].where,
         "promises": promises(by_name[n])}
        for n, why in kept if n not in stepped and n not in in_any_fork
    ]  # fmt: skip
    fork_docs, hidden = {}, None
    blinded = CLOSE in open_forks and blind(sentence)
    for word, names in open_forks.items():
        options, resolves, docs = [], {}, []
        if word == CLOSE and blinded:  # shown in no order of the search's
            hidden = {"offered": names[:-1], "confidence": measured[0]}
            names = shuffled(sentence, names[:-1]) + [NONE]
        for n in names:
            if n == NONE:  # every fork's way out, a word's as much as the search's
                options.append(shape.ForkOption(label=n, tradeoff=NONE_TRADEOFF))
                resolves[n] = ()
                docs.append({"name": n, "where": NONE, "tradeoff": NONE_TRADEOFF})
                continue
            card = by_name[n]
            said = tradeoff(card)
            if (
                word == CLOSE and blinded
            ):  # one line for all: the search's reasons say its order
                said += f"; {BLIND_ROW}"
            elif word == CLOSE:  # pointed at, or named and doubted: said on every row
                said += f"; {why_close[n]}"
            options.append(shape.ForkOption(label=n, tradeoff=said))
            resolves[n] = (
                (shape.FileWrite(dest_path=f"steps/{n}.md", content=step_line(n)),)
                if card.built
                else ()
            )
            docs.append({"name": n, "where": card.where, "tradeoff": said})
        if word == CLOSE:
            surface = (f"“{sentence}” names no add-on the search agrees with; the fork holds "
                       f"{', '.join(names[:-1])}: which, if any, does it?")  # fmt: skip
            # the search's first, and a confidence from your sealed blind
            # picks on this matcher (or none); blind, neither is said, so
            # nothing is put in front of you to follow
            recommended, conf = (None, None) if blinded else (names[0], measured[0])
        else:
            surface = (
                f"“{word}” could be {', '.join(names[:-1])}: which add-on, if any?"
            )
            recommended, conf = None, None
        entries.append(
            shape.Fork(
                decision_type=fork_type(rec, word, sentence),
                surface=surface,
                options=tuple(options),
                recommended=recommended,
                confidence=conf,
                resolves=resolves,
            )
        )
        fork_docs[word] = docs
    if entries:  # they ride with a plan, and never make one
        entries += [
            shape.FileWrite(
                dest_path=f"steps/{d['name']}.md", content=step_line(d["name"])
            )
            for d in riding
        ]
    doc = (
        shape.PlanDoc(app_name=APP, entries=tuple(entries)).to_dict()
        if entries
        else None
    )
    if doc is not None:
        shape.validate(doc)  # the Forge's own check, before anyone is told it is a plan
    built = sum(1 for c in box.cards if c.built)
    out = {
        "cards": {"built": built, "ideas": len(box.cards) - built},
        "steps": steps,
        "defaults": riding,
        "defaults_not_here": not_here,
        "forks": fork_docs,
        "sealed": settled,
        "ideas": ideas,
        "plan": doc,
    }
    if blinded:
        out["close"] = {"blind": True, "confidence": None, "said": BLIND_SAID}
        out["hidden"] = hidden  # for propose to keep, and main never to print
    elif CLOSE in open_forks:
        out["close"] = {"blind": False, "confidence": measured[0], "said": measured[1]}
    return out


def to_report(out: dict, rec) -> tuple[dict, int]:
    """The plan as a report, and the exit code: a fork waits on you (42), or
    nothing does (0)."""
    if "stack" in out:
        s = out["stack"]
        rows = [
            (f"{STACK_PATH}:{i}", ln)
            for i, ln in enumerate(s["text"].splitlines(), 1)
            if ln.strip()
        ]
        back = held_back(out, rec)
        left = sum(len(r) for _, r in back)
        said = f"a stack is sealed for these words (row {s['row']}); " + (
            f"{left} of its forks {'is' if left == 1 else 'are'} not settled, said below"
            if left
            else "nothing to ask"
        )
        return report(
            NAME,
            "populated",
            said,
            [(f"stack sealed for these words ({s['subject']})", rows), *back],
        ), kernel.ALIVE
    groups = [("steps", [(s["where"], f"{s['name']}: {s['line']} ({s['promises']})"
                          + (f"; {s['why']}" if s["why"].startswith("you sealed") else ""))
                         for s in out["steps"]])]  # fmt: skip
    for word, options in out["forks"].items():
        rows = [(o["where"], f"{o['name']}: {o['tradeoff']}") for o in options]
        rows.append(
            (NOT_NOW, f"{NOT_NOW}: {NOT_NOW_TRADEOFF}")
        )  # the other way out, always last
        if word == CLOSE and out.get("close", {}).get("blind"):
            # blind: in no order of the search's, nothing recommended, said once
            groups.append((f"fork “{CLOSE}”, {BLIND_SAID}: nothing named that the search agrees with; these are close to what you said", rows))  # fmt: skip
        elif word == CLOSE:  # the search's first is the recommendation, and says so
            said = out.get("close", {}).get("said")
            rows[0] = (rows[0][0], rows[0][1] + "; recommended, the search's first"
                       + (f"; {said}" if said else ""))  # fmt: skip
            groups.append((f"fork “{CLOSE}”: nothing named that the search agrees with; these are close to what you said", rows))  # fmt: skip
        else:
            groups.append((f"fork “{word}”", rows))
    groups += held_back(out, rec)
    groups.append((f"defaults: {DEFAULT_WHY[11:]}", [
        (d["where"], f"{d['name']}: {d['line']} ({d['promises']})" + (f"; {d['why']}" if d["why"] else ""))
        for d in out.get("defaults", [])]))  # fmt: skip
    groups.append(("defaults named that are no built add-on here", [
        (DEFAULTS.name, n) for n in out.get("defaults_not_here", [])]))  # fmt: skip
    misses = {w: got for w, got in out["sealed"].items()
              if got["chose"] == NONE and "stale" not in got}  # fmt: skip
    groups.append(("you sealed none of them", [
        (rec.DECISION_PATH.format(got["decision_type"]),
         f"no card offered for “{w}” does it, by your seal (row {got['row']})")
        for w, got in misses.items()]))  # fmt: skip
    groups.append(("stale seals, asked again", [
        (rec.DECISION_PATH.format(got["decision_type"]), f"{got['stale']} (row {got['row']})")
        for got in out["sealed"].values() if "stale" in got]))  # fmt: skip
    groups.append(
        (
            "ideas",
            [
                (i["where"], f"{i['name']}: {i['line']} (not built)")
                for i in out["ideas"]
            ],
        )
    )
    n_forks, n_steps = len(out["forks"]), len(out["steps"])
    if n_forks:
        said = f"{n_forks} fork{'s wait' if n_forks != 1 else ' waits'} on you"
        return report(NAME, "populated", said, groups), kernel.ESCALATE
    if n_steps:
        said = f"{n_steps} step{'s' if n_steps != 1 else ''}, nothing waits on you"
        return report(NAME, "populated", said, groups), kernel.ALIVE
    if out["ideas"]:
        return report(
            NAME, "populated", "only ideas, nothing built to run", groups
        ), kernel.ALIVE
    if CLOSE in misses and len(misses) == 1:
        said = (f"you sealed that no card close to these words does it (row {misses[CLOSE]['row']}); "
                "add a line to ui/search-words.txt, or an idea to adapters/planned.json")  # fmt: skip
        return report(NAME, "empty", said, []), kernel.ALIVE
    if misses:
        said = (f"you sealed that none of the cards offered does it for "
                f"{', '.join(f'“{w}”' for w in misses)}; nothing to run")  # fmt: skip
        return report(NAME, "populated", said, groups), kernel.ALIVE
    said = "nothing named: no card or alias line matched; add a line to ui/search-words.txt if one should"
    return report(NAME, "empty", said, []), kernel.ALIVE


def steps_of(stack_text: str) -> list[str]:
    """The add-ons a sealed stack file names, in order: each `- NAME -- ARGS`
    line's NAME, as the stack add-on reads them."""
    out = []
    for raw in stack_text.splitlines():
        line = raw.strip()
        if line.startswith("- "):
            name = line[2:].partition(" -- ")[0].strip()
            if name and name not in out:
                out.append(name)
    return out


NEXT_TOP = 8  # how many are offered next
NEXT_SEEN = (
    2  # a card counts beside a step only when two of your stacks put them together
)


def stacks_in(home: Path) -> list[list[str]]:
    """Every stack file under HOME, as the add-ons it names, in order: a file
    called stack*.md or across*.md, at most four folders down, never one kept
    in a pile, a box or a run. A stack that names one add-on says nothing of
    what goes with what, and is left out."""
    skip = {"pile", "piles", "box", "runs", "sources", "index", "store", "backups"}
    out = []
    for f in sorted(home.rglob("*.md")):
        rel = f.relative_to(home).parts
        if (
            len(rel) > 5
            or skip & set(rel[:-1])
            or not f.name.startswith(("stack", "across"))
        ):
            continue
        try:
            names = steps_of(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if len(names) > 1:
            out.append(names)
    return out


def what_next(have: list[str], stacks: list[list[str]], by_name: dict, beside: list[str] | None = None) -> list[dict]:  # fmt: skip
    """What your own stacks put beside the steps you have, best first:
    [{name, score, beside}]. Counting, and nothing else: for a card you don't
    have, and each step you do, the share of your stacks holding that step
    that hold the card too; its score is the mean over the steps it was seen
    beside twice or more. `beside` is those steps, strongest first, each
    {step, both, of}. A card no stack of yours puts with any of them is not
    offered: this says what you have done, never what might be good."""
    # `beside` is the steps looked beside, when not all of them: a default is in
    # nearly every stack, so what sits with it is what sits with everything
    look = set(beside if beside is not None else have)
    has = {n: sum(1 for st in stacks if n in st) for n in look}
    seen: dict[str, list[dict]] = {}
    for st in stacks:
        held = set(st)
        for step in held & look:
            for card in held - set(have):
                if card in by_name and by_name[card].built:
                    row = seen.setdefault(card, {}).setdefault(
                        step, {"step": step, "both": 0, "of": has[step]}
                    )
                    row["both"] += 1
    out = []
    for card, rows in seen.items():
        beside = sorted((r for r in rows.values() if r["both"] >= NEXT_SEEN),
                        key=lambda r: (-r["both"] / r["of"], r["step"]))  # fmt: skip
        if beside:
            # how much more often beside these steps than in your stacks at large:
            # a card in nearly every stack is beside everything, and says nothing
            everywhere = sum(1 for st in stacks if card in st) / len(stacks)
            score = sum(r["both"] / r["of"] for r in beside) / len(beside) - everywhere
            if score > 0:
                out.append({"name": card, "score": round(score, 3), "beside": beside})
    return sorted(out, key=lambda c: (-c["score"], -len(c["beside"]), c["name"]))


def untried(have: list[str], stacks: list[list[str]], by_name: dict, sentence: str) -> list[dict] | None:  # fmt: skip
    """The built cards no stack of yours has ever held, that the catalogue's
    own search puts near what you asked for or near a step you have, best
    first: [{name, words, steps}]. `words` is whether it is near your
    sentence; `steps` the steps of yours it is near, by each step's own card
    line. Near your words comes first, then near the most steps. None when
    this willow's similar has no search. Pointing, never answering."""
    if searched(sentence or "x") is None:
        return None
    stacked = {n for st in stacks for n in st} | set(have)
    found: dict[str, dict] = {}

    def note(names: list[str], step: str | None) -> None:
        for n in names:
            if n in by_name and by_name[n].built and n not in stacked:
                row = found.setdefault(
                    n, {"name": n, "words": False, "steps": [], "at": len(found)}
                )
                if step is None:
                    row["words"] = True
                elif step not in row["steps"]:
                    row["steps"].append(step)

    if sentence:
        note([f["name"] for f in searched(sentence) or []], None)
    # a default suits any folder, so what is near one says nothing of what you
    # are after: only the steps your words or your picks brought are looked beside
    base = {n for n, _ in defaults(by_name)[0]}
    for step in have:
        if step in by_name and step not in base:
            note([f["name"] for f in searched(by_name[step].line) or []], step)
    return sorted(
        found.values(), key=lambda r: (not r["words"], -len(r["steps"]), r["at"])
    )


def next_report(have: list[str], stacks: list[list[str]], by_name: dict, where: str, sentence: str = "") -> tuple[dict, int]:  # fmt: skip
    """What could go in next, as a report, from two places said apart: what
    your stacks have put beside these steps, and what you have never stacked
    that the catalogue puts near. Exit 0: it offers, it never asks."""
    if not have:
        return report(NAME, "empty", "no steps yet to look beside: say what you want first", []), kernel.ALIVE  # fmt: skip
    base = {n for n, _ in defaults(by_name)[0]}
    own = [n for n in have if n not in base]  # what the words or the picks brought
    found = what_next(have, stacks, by_name, own or None)
    rows = []
    for c in found[:NEXT_TOP]:
        card = by_name[c["name"]]
        b = "; ".join(
            f"with {r['step']} in {r['both']} of {r['of']}" for r in c["beside"][:3]
        )
        more = (
            f"; and {len(c['beside']) - 3} more of your steps"
            if len(c["beside"]) > 3
            else ""
        )
        rows.append(
            (card.where, f"{card.name}: {card.line} ({promises(card)}); {b}{more}")
        )
    new = untried(have, stacks, by_name, sentence)
    fresh = []
    for c in (new or [])[:NEXT_TOP]:
        card = by_name[c["name"]]
        near_ = (["near your words"] if c["words"] else []) + (
            ["near " + ", ".join(c["steps"][:3]) + (f" and {len(c['steps']) - 3} more" if len(c["steps"]) > 3 else "")]
            if c["steps"] else [])  # fmt: skip
        fresh.append(
            (
                card.where,
                f"{card.name}: {card.line} ({promises(card)}); {'; '.join(near_)}",
            )
        )
    said = (f"{len(rows)} of {len(found)} your stacks put beside these {len(have)} steps, "
            f"from {len(stacks)} stacks in {where}; "
            + ("no search here for what you haven't tried" if new is None
               else f"{len(fresh)} of {len(new)} you have never stacked and the catalogue puts near"))  # fmt: skip
    if not rows and not fresh:
        said = (f"none of your {len(stacks)} stacks in {where} puts anything beside these {len(have)} steps twice, "
                "and nothing you haven't stacked is near them")  # fmt: skip
        return report(NAME, "empty", said, []), kernel.ALIVE
    groups = [("you have", [(by_name[n].where if n in by_name else n, n) for n in have]),
              ("what your stacks put beside them, most often first", rows),
              ("what you have never stacked, and the catalogue puts near", fresh)]  # fmt: skip
    return report(NAME, "populated", said, groups), kernel.ALIVE


ASSEMBLED = re.compile(r"^\+ (\S+)\s+.*?contract (\S+)\s+tests (\S+)(?::\s*(.*))?$")


def folder_of(name: str) -> str:
    """Where an add-on sits, in willow and in a stack alike: adapters/deps/
    for a deps add-on, adapters/stdlib/ for the rest (and a name willow
    hasn't, which assemble refuses by name)."""
    kind = "deps" if (ROOT / "adapters" / "deps" / name).is_dir() else "stdlib"
    return f"adapters/{kind}/{name}/"


def assemble(to: Path, name: str) -> tuple[str, str]:
    """One add-on into the stack at `to` through ui/assemble.py, one at a
    time: ("copied", what assemble said of its contract and tests) or
    ("left out", why). A piece already there is left as it is."""
    stack = to / "stack"
    if (stack / folder_of(name)).is_dir():
        return "copied", "already in the stack"
    got = subprocess.run(
        [
            sys.executable,
            str(ROOT / "ui/assemble.py"),
            "add",
            name,
            "--to",
            str(to),
        ],
        capture_output=True,
        text=True,
    )
    if got.returncode == kernel.REFUSED:
        why = (got.stderr or got.stdout).strip().splitlines()[-1:] or ["refused"]
        return "left out", why[0].removeprefix("refused: ")
    for line in got.stdout.splitlines():
        m = ASSEMBLED.match(line.strip())
        if m and m.group(1) == name:
            tests = m.group(3) + (f" ({m.group(4)})" if m.group(4) else "")
            return "copied", f"contract {m.group(2)}; tests {tests}"
    return "copied", "assemble said nothing of it"


def build(box: Path, sentence: str, to: Path, stacks: dict) -> tuple[dict | None, int]:
    """The stack sealed for these words, assembled into `to` and run over
    the box: (the report, 0 clean or 42 flagged), or (None, 2) refused."""
    k = kernel.bite_key(sentence)
    if k not in stacks:
        print(
            "refused: no stack is sealed for these words; suggest, propose, then seal",
            file=sys.stderr,
        )
        return None, kernel.REFUSED
    if not to.parent.is_dir():
        print(
            f"refused: {to.parent} is missing; a folder to build in is yours to make",
            file=sys.stderr,
        )
        return None, kernel.REFUSED
    sealed = stacks[k]
    if not (to / "stack" / "STACK.json").is_file():
        got = subprocess.run(
            [sys.executable, str(ROOT / "ui/assemble.py"), "init", "--to", str(to)],
            capture_output=True,
            text=True,
        )
        if got.returncode != kernel.ALIVE:
            print(
                "refused:",
                (got.stderr or got.stdout).strip().splitlines()[-1],
                file=sys.stderr,
            )
            return None, kernel.REFUSED
    state, said = assemble(to, "stack")  # the runner, the one piece every stack has
    if state != "copied":
        print(f"refused: the stack add-on could not be put in: {said}", file=sys.stderr)
        return None, kernel.REFUSED
    names = steps_of(sealed["text"])
    rows, left = [], []
    for name in names:
        state, said = assemble(to, name)
        (rows if state == "copied" else left).append(
            (folder_of(name), f"{name}: {said}")
        )
    stack_file = to / "forge-stack.md"
    scratch = to / "out"  # what the contract calls {tmp}: a folder of the build's own
    scratch.mkdir(exist_ok=True)
    stack_file.write_text(
        sealed["text"].replace("{tmp}", str(scratch)), encoding="utf-8"
    )
    runner = (
        to / "stack/adapters/stdlib/stack/stack.py"
    )  # the built copy, not the repo's
    got = subprocess.run(
        [sys.executable, str(runner), "--box", str(box), "--stack", str(stack_file)],
        capture_output=True,
        text=True,
    )
    page = to / "page.md"
    page.write_text(got.stdout, encoding="utf-8")
    ran = {}
    for line in got.stdout.splitlines():
        m = re.match(r"^- `(\S+)(?: --.*?)?`(?:\s+\((.*)\))?$", line)
        if m:
            ran[m.group(1)] = m.group(2) or "clean"
    rows = [(w, f"{x}; ran: {ran.get(x.split(':')[0], 'not run')}") for w, x in rows]
    flagged = sum(1 for n in names if ran.get(n, "") not in ("clean", "none found"))
    said = (f"{len(rows)} of {len(names)} step{'s' if len(names) != 1 else ''} built into {to}, "
            f"page at {page}; {flagged} flagged, {len(left)} left out")  # fmt: skip
    doc = report(NAME, "populated", said, [("built", rows), ("left out", left)])
    code = (
        kernel.ESCALATE
        if flagged or left or got.returncode == kernel.REFUSED
        else kernel.ALIVE
    )
    return doc, code


def pairs(items: list[str], what: str) -> tuple[dict[str, str], str | None]:
    """`WORD=VALUE` arguments as a dict, or why one isn't."""
    out = {}
    for it in items or []:
        word, sep, value = it.partition("=")
        if not sep or not word.strip() or not value.strip():
            return {}, f"{what} takes WORD=VALUE, not {it!r}"
        out[word.strip()] = value.strip()
    return out, None


def picks(items: list[str]) -> tuple[dict[str, list[str]], str | None]:
    """`--choose WORD=NAME` arguments as {word: [names]}, or why one isn't.
    A fork may take more than one: `WORD=A,B`, or `--choose WORD=A` given
    again with B. A name given twice counts once."""
    out: dict[str, list[str]] = {}
    for it in items or []:
        word, sep, value = it.partition("=")
        names = [n.strip() for n in value.split(",") if n.strip()]
        if not sep or not word.strip() or not names:
            return {}, f"--choose takes WORD=NAME or WORD=NAME,NAME, not {it!r}"
        held = out.setdefault(word.strip(), [])
        held += [n for n in names if n not in held]
    return out, None


WANTS_INTRO = (
    "A stack of wants, each above the step that answers it. They are "
    "proposals: cut any, add your own (a want in your words, then the add-on "
    "that answers it), and it is your stack."
)


def wants(sentence: str, out: dict, choose: dict, why: dict, by_name: dict, run: list[str]) -> str:  # fmt: skip
    """The stack as a page of wants, the way a person writes one: each step
    under the want it answers (a short line) and the card's own line,
    numbered in the order they run. Three pools, each only when it has a
    step: what the words asked for, what the person chose at a fork (with
    what it was chosen over and their reason, in their words), and what
    rides in every stack. The stack add-on skips every line here but the
    pools and the steps, and heads each step's page with the lines above
    it, so the why is carried from the fork to the page that is read."""
    said: dict[str, tuple[str, str]] = {}
    pools: list[tuple[str, list[str]]] = [(f"for “{sentence}”", []), ("what you chose", []), ("in every stack", [])]  # fmt: skip
    for s in out["steps"]:
        said[s["name"]] = (
            f"“{sentence}”: {s['name']} ({s['why']}).",
            f"{s['name']}: {s['line']}",
        )
        pools[0][1].append(s["name"])
    for word, names in choose.items():
        taken = [n for n in names if n in by_name and by_name[n].built]
        others = [o["name"] for o in out["forks"].get(word, []) if o["name"] not in (*names, NONE)]  # fmt: skip
        for n in taken:
            over = f", not {' or '.join(others)}" if others else ""
            reason = f", because {why[word]}" if why.get(word) else ""
            said[n] = (f"“{word}”: {n}{over}{reason}.", f"{n}: {by_name[n].line}")
            pools[1][1].append(n)
    for d in out.get("defaults", []):
        if d["name"] in run and d["name"] not in said:
            said[d["name"]] = (
                f"{d['why'] or DEFAULT_WHY}.",
                f"{d['name']}: {d['line']}",
            )
            pools[2][1].append(d["name"])
    text, n = [f"# {sentence}", "", WANTS_INTRO], 0
    for heading, names in pools:
        names = [x for x in run if x in names]  # in the order they run
        if not names:
            continue
        text += ["", f"## {heading}"]
        for name in names:
            n += 1
            head, card = said[name]
            text += ["", f"Want {n}: {head}", card, step_line(name).rstrip("\n")]
    return "\n".join(text) + "\n"


def propose(
    box: Path, sentence: str, out: dict, cards, choose: dict, why: dict, rec
) -> tuple[dict | None, int]:
    """Each settled fork, and the stack, to the kernel's door: (the report,
    exit 42), or (None, 2) refused before writing anything, when a fork is
    left open or settled with an option not on offer. After the refusals,
    every write is the kernel's."""
    for word, options in out["forks"].items():
        names = [o["name"] for o in options]
        if word not in choose:
            print(
                f"refused: “{word}” is not settled: --choose {word}={'|'.join((*names, NOT_NOW))}",
                file=sys.stderr,
            )
            return None, kernel.REFUSED
        for name in choose[word]:
            if name not in (*names, NOT_NOW):
                print(f"refused: {name} is not an option for “{word}”: {', '.join((*names, NOT_NOW))}", file=sys.stderr)  # fmt: skip
                return None, kernel.REFUSED
        alone = [n for n in choose[word] if n in (NONE, NOT_NOW)]
        if alone and len(choose[word]) > 1:  # a way out is taken alone, or not at all
            print(f"refused: {alone[0]} for “{word}” stands alone; take it, or the cards, not both", file=sys.stderr)  # fmt: skip
            return None, kernel.REFUSED
    for word in choose:
        if word not in out["forks"]:
            print(f"refused: nothing to choose for “{word}”", file=sys.stderr)
            return None, kernel.REFUSED
    by_name = {c.name: c for c in cards}
    run = [s["name"] for s in out["steps"]] + [
        n
        for names in choose.values()
        for n in names
        if n in by_name and by_name[n].built
    ]
    if run:  # the defaults ride with a stack, after its own steps; they never make one
        run += [d["name"] for d in out.get("defaults", []) if d["name"] not in run]
    if not run and not choose:
        print(
            "refused: nothing to propose: no step and no settled fork", file=sys.stderr
        )
        return None, kernel.REFUSED
    ts = kernel.now()
    rows = []
    for word, taken in choose.items():
        # what was shown, and the search's own order when that was kept from you
        shown = [o["name"] for o in out["forks"][word] if o["name"] != NONE]
        hidden = out.get("hidden") if word == CLOSE else None
        offered = hidden["offered"] if hidden else shown
        # more than one may be taken: the one the search put highest is `chose`,
        # so a pick is scored the same taken alone or with others; the rest are `also`
        taken = sorted(
            taken, key=lambda n: offered.index(n) if n in offered else len(offered)
        )
        name, also = taken[0], taken[1:]
        others = [
            o["name"] for o in out["forks"][word] if o["name"] not in (*taken, NONE)
        ]
        dt = fork_type(rec, word, sentence)
        if name == NOT_NOW:
            # not deciding is a decision: its own proposal, under its own
            # question, so the fork's question stays open for the pick to come.
            # It keeps what you were shown, in the order you saw it, and when:
            # a second not-now for one fork is then a proposal of its own.
            later = {
                "word": word, "decision_type": dt, "chose": NOT_NOW, "why": why.get(word, ""),
                "shown": others, "sentence": sentence,
                "asked_at": len(kernel.read(box / "record.jsonl")[0]),
            }  # fmt: skip
            prop = {
                "path": NOT_NOW_PATH.format(dt),
                "data": json.dumps(later, sort_keys=True, ensure_ascii=False),
                "cites": [],
                "claim": f"for “{word}”: not now; {why.get(word) or 'no reason given'}",
            }
            code, said = quiet(kernel.bite, box, not_now_question(dt), ts)
            if code == kernel.REFUSED:
                print("refused:", said.strip(), file=sys.stderr)
                return None, kernel.REFUSED
            code, said = quiet(
                kernel.propose, box, [json.dumps(prop, ensure_ascii=False)], ts
            )
            if not said.startswith("pass "):
                print("refused:", said.strip(), file=sys.stderr)
                return None, kernel.REFUSED
            rows.append((prop["path"], f"{said.split()[1]}  not now for “{word}”"))
            continue
        data = {
            "word": word,
            "decision_type": dt,
            "chose": name,
            "over": others,
            "why": why.get(word, ""),
            "card": None,  # none of them: the miss, kept, with nothing to run
        }
        # what was shown is the outcome once sealed: the cards in their order,
        # the one recommended (only the search's fork has one), where the pick
        # fell, and what put them there. The close fork is this sentence's own.
        # A blind fork's pick is kept in the search's order, which it wasn't shown in:
        # blind, nothing was recommended, and the search's first is kept under
        # its own name, so the record says what was shown and what was not
        data.update(kind="close" if word == CLOSE else "word", offered=offered,
                    recommended=offered[0] if word == CLOSE and not hidden else None,
                    rank=offered.index(name) + 1 if name in offered else None,
                    matcher=matcher())  # fmt: skip
        if hidden:
            data["search_first"] = offered[0]
        if word == CLOSE:  # and the confidence it had, said or not, to be scored
            data["sentence"] = sentence
            data["blind"] = hidden is not None
            data["confidence"] = (
                hidden["confidence"]
                if hidden
                else out.get("close", {}).get("confidence")
            )
            if hidden:  # and the order you saw, in its own word
                data["shown"] = shown
        if name != NONE:
            pinned = [
                {"name": c.name, "line": c.line, "where": c.where,
                 "sha256": hashlib.sha256((ROOT / c.where).read_bytes()).hexdigest()}
                for c in (by_name[n] for n in taken)
            ]  # fmt: skip
            data["card"] = pinned[0]
            if (
                also
            ):  # said only when more than one was taken, so one pick reads as before
                data["also"] = also
                data["also_cards"] = pinned[1:]
        prop = {
            "path": rec.DECISION_PATH.format(dt),
            "data": json.dumps(data, sort_keys=True, ensure_ascii=False),
            "cites": [],
            "claim": f"for “{word}”: {' and '.join(taken)} over {', '.join(others) or 'nothing'}; {why.get(word) or 'no reason given'}",
        }
        code, said = quiet(kernel.bite, box, rec.question(dt), ts)
        if code == kernel.REFUSED:
            print("refused:", said.strip(), file=sys.stderr)
            return None, kernel.REFUSED
        code, said = quiet(
            kernel.propose, box, [json.dumps(prop, ensure_ascii=False)], ts
        )
        if not said.startswith("pass "):
            print("refused:", said.strip(), file=sys.stderr)
            return None, kernel.REFUSED
        rows.append(
            (prop["path"], f"{said.split()[1]}  {' and '.join(taken)} for “{word}”")
        )
    if not run:  # only a miss settled: nothing to stack, and nothing runs
        said = f"{len(rows)} waiting on your seal, no stack: nothing settled runs"
        return report(NAME, "populated", said, [(None, rows)]), kernel.ESCALATE
    text = wants(sentence, out, choose, why, by_name, run)
    prop = {
        "path": STACK_PATH,
        "data": text,
        "cites": [],
        "claim": f"a stack for “{sentence}”: {', '.join(run)}",
    }
    code, said = quiet(kernel.bite, box, sentence, ts)
    if code == kernel.REFUSED:
        print("refused:", said.strip(), file=sys.stderr)
        return None, kernel.REFUSED
    code, said = quiet(kernel.propose, box, [json.dumps(prop, ensure_ascii=False)], ts)
    if not said.startswith("pass "):
        print("refused:", said.strip(), file=sys.stderr)
        return None, kernel.REFUSED
    rows.append((STACK_PATH, f"{said.split()[1]}  a stack: {', '.join(run)}"))
    said = f"{len(rows)} waiting on your seal: python kernel.py seal --box DIR proposal:..."
    return report(NAME, "populated", said, [(None, rows)]), kernel.ESCALATE


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    p = argparse.ArgumentParser(prog="suggest.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="verb", required=True)
    for verb in ("suggest", "propose", "build", "next"):
        s = sub.add_parser(verb)
        s.add_argument("sentence", help="what you want done, in your own words")
        s.add_argument("--box", required=True, help="your record")
        if verb == "next":
            s.add_argument(
                "--stacks",
                required=True,
                metavar="FOLDER",
                help="the folder your own stacks are kept under",
            )
        if verb != "build":
            s.add_argument(
                "--defaults",
                metavar="FILE",
                help="your own list of defaults, or `none` for no defaults",
            )
        if verb == "suggest":
            s.add_argument(
                "--plan",
                action="store_true",
                help="the plan as the Forge reads it, as JSON",
            )
        elif verb == "next":
            pass
        elif verb == "build":
            s.add_argument(
                "--to",
                required=True,
                help="the folder to build in; its parent must exist",
            )
        else:
            s.add_argument(
                "--choose", action="append", metavar="WORD=NAME", help="settle a fork"
            )
            s.add_argument(
                "--why", action="append", metavar="WORD=REASON", help="your reason"
            )
    s = sub.add_parser("scores")
    s.add_argument("--box", required=True, help="your record")
    a = p.parse_args(argv)
    box = Path(a.box)
    why = is_box(box)
    if why:
        print("refused:", why, file=sys.stderr)
        return kernel.REFUSED
    got = forge()
    if got is None:
        say(report(NAME, "unreachable", NEEDS, []), as_json)
        return kernel.ESCALATE
    card_box, card_table, shape, rec = got
    if a.verb == "scores":
        doc, code = scores(box, rec)
        say(doc, as_json)
        return code
    try:
        cards = card_box.CardBox(ROOT)
    except card_table.CardTableError as e:  # a card beside this script that won't read
        print("refused:", e, file=sys.stderr)
        return kernel.REFUSED
    if getattr(a, "defaults", None):  # the person's own list, or none at all
        global DEFAULTS
        DEFAULTS = Path(a.defaults)
        if a.defaults != "none" and not DEFAULTS.is_file():
            print(f"refused: {a.defaults} isn't a file of defaults", file=sys.stderr)
            return kernel.REFUSED
    sealed, stacks = on_record(box, rec)
    lines, where_from = commands(str(kernel.folder(kernel.config(box))))
    STEPS.update(lines)

    def measured():  # only when a close fork is open: the matcher builds the search
        return confidence(outcomes(box, rec), matcher())

    out = plan(
        cards,
        phrased(cards.scan(a.sentence), a.sentence),
        shape,
        rec,
        sealed,
        a.sentence,
        measured,
    )
    out["cards"]["commands"] = where_from
    later, waits = undecided(box, rec)
    types = {w: fork_type(rec, w, a.sentence) for w in out["forks"]}
    out["not_now"] = {w: {**later[dt], "decision_type": dt} for w, dt in types.items() if dt in later}  # fmt: skip
    out["unsealed"] = {w: (dt, waits[dt]) for w, dt in types.items() if dt in waits}
    if (k := kernel.bite_key(a.sentence)) in stacks:
        out["stack"] = stacks[k]
    if a.verb == "next":
        home = Path(a.stacks)
        if not home.is_dir():
            print(f"refused: {a.stacks} isn't a folder of stacks", file=sys.stderr)
            return kernel.REFUSED
        # what you have: the stack you sealed for these words, or what the words reach now
        have = (steps_of(out["stack"]["text"]) if "stack" in out
                else [s["name"] for s in out["steps"]] + [d["name"] for d in out.get("defaults", [])])  # fmt: skip
        doc, code = next_report(
            have,
            stacks_in(home),
            {c.name: c for c in cards.cards},
            a.stacks,
            a.sentence,
        )
        say(doc, as_json)
        return code
    if a.verb == "build":
        doc, code = build(box, a.sentence, Path(a.to), stacks)
        if doc is not None:
            say(doc, as_json)
        return code
    if a.verb == "propose":
        if "stack" in out:
            print(f"refused: a stack is sealed for these words already (row {out['stack']['row']})", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        choose, bad = picks(a.choose)
        reasons, worse = pairs(a.why, "--why")
        if bad or worse:
            print("refused:", bad or worse, file=sys.stderr)
            return kernel.REFUSED
        doc, code = propose(box, a.sentence, out, cards.cards, choose, reasons, rec)
        if doc is not None:
            say(doc, as_json)
        return code
    doc, code = to_report(out, rec)
    if a.plan:  # all of it but what a blind fork keeps from you
        shown = {k: v for k, v in out.items() if k != "hidden"}
        print(json.dumps(shown, indent=2, ensure_ascii=False))
    else:
        say(doc, as_json)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
