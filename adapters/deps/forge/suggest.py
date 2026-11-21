"""suggest.py: the Forge's matchmaker over this willow's add-on cards.
Python 3.11+ (forge-play's floor), forge-play 0.10 or newer.

    python adapters/deps/forge/suggest.py suggest --box DIR "what you want done" [--json | --plan]
    python adapters/deps/forge/suggest.py propose --box DIR "what you want done"
                                                  --choose WORD=NAME ... [--why WORD=REASON ...] [--json]
    python adapters/deps/forge/suggest.py build   --box DIR "what you want done" --to STACK [--json]
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
#: the fork for a sentence no name or alias line reaches, and its way out
CLOSE, NONE = "close", "none"
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
                         "row": row["n"], "subject": subj},
                    )  # fmt: skip
    return decisions, stacks


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
    close = (
        near(sentence, by_name, reached) if sentence and (doubted or not found) else []
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
    chosen = {got["chose"]: word for word, got in settled.items() if "stale" not in got}
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
        said = f"a stack is sealed for these words (row {s['row']}); nothing to ask"
        return report(
            NAME,
            "populated",
            said,
            [(f"stack sealed for these words ({s['subject']})", rows)],
        ), kernel.ALIVE
    groups = [("steps", [(s["where"], f"{s['name']}: {s['line']} ({s['promises']})"
                          + (f"; {s['why']}" if s["why"].startswith("you sealed") else ""))
                         for s in out["steps"]])]  # fmt: skip
    for word, options in out["forks"].items():
        rows = [(o["where"], f"{o['name']}: {o['tradeoff']}") for o in options]
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
                f"refused: “{word}” is not settled: --choose {word}={'|'.join(names)}",
                file=sys.stderr,
            )
            return None, kernel.REFUSED
        if choose[word] not in names:
            print(f"refused: {choose[word]} is not an option for “{word}”: {', '.join(names)}", file=sys.stderr)  # fmt: skip
            return None, kernel.REFUSED
    for word in choose:
        if word not in out["forks"]:
            print(f"refused: nothing to choose for “{word}”", file=sys.stderr)
            return None, kernel.REFUSED
    by_name = {c.name: c for c in cards}
    run = [s["name"] for s in out["steps"]] + [
        n for n in choose.values() if n in by_name and by_name[n].built
    ]
    if not run and not choose:
        print(
            "refused: nothing to propose: no step and no settled fork", file=sys.stderr
        )
        return None, kernel.REFUSED
    ts = kernel.now()
    rows = []
    for word, name in choose.items():
        others = [
            o["name"] for o in out["forks"][word] if o["name"] not in (name, NONE)
        ]
        dt = fork_type(rec, word, sentence)
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
        shown = [o["name"] for o in out["forks"][word] if o["name"] != NONE]
        hidden = out.get("hidden") if word == CLOSE else None
        # a blind fork's pick is kept in the search's order, which it wasn't shown in
        offered = hidden["offered"] if hidden else shown
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
            card = by_name[name]
            pinned = hashlib.sha256((ROOT / card.where).read_bytes()).hexdigest()
            data["card"] = {
                "name": card.name,
                "line": card.line,
                "where": card.where,
                "sha256": pinned,
            }
        prop = {
            "path": rec.DECISION_PATH.format(dt),
            "data": json.dumps(data, sort_keys=True, ensure_ascii=False),
            "cites": [],
            "claim": f"for “{word}”: {name} over {', '.join(others)}; {why.get(word) or 'no reason given'}",
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
        rows.append((prop["path"], f"{said.split()[1]}  {name} for “{word}”"))
    if not run:  # only a miss settled: nothing to stack, and nothing runs
        said = f"{len(rows)} waiting on your seal, no stack: nothing settled runs"
        return report(NAME, "populated", said, [(None, rows)]), kernel.ESCALATE
    text = f"# {sentence}\n\n## for “{sentence}”\n" + "".join(step_line(n) for n in run)
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
    for verb in ("suggest", "propose", "build"):
        s = sub.add_parser(verb)
        s.add_argument("sentence", help="what you want done, in your own words")
        s.add_argument("--box", required=True, help="your record")
        if verb == "suggest":
            s.add_argument(
                "--plan",
                action="store_true",
                help="the plan as the Forge reads it, as JSON",
            )
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
    sealed, stacks = on_record(box, rec)
    lines, where_from = commands(str(kernel.folder(kernel.config(box))))
    STEPS.update(lines)

    def measured():  # only when a close fork is open: the matcher builds the search
        return confidence(outcomes(box, rec), matcher())

    out = plan(cards, cards.scan(a.sentence), shape, rec, sealed, a.sentence, measured)
    out["cards"]["commands"] = where_from
    if (k := kernel.bite_key(a.sentence)) in stacks:
        out["stack"] = stacks[k]
    if a.verb == "build":
        doc, code = build(box, a.sentence, Path(a.to), stacks)
        if doc is not None:
            say(doc, as_json)
        return code
    if a.verb == "propose":
        if "stack" in out:
            print(f"refused: a stack is sealed for these words already (row {out['stack']['row']})", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        choose, bad = pairs(a.choose, "--choose")
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
