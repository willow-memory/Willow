"""say_check.py: a sentence said about your boxes, checked by code. Python 3.9+.

    python adapters/stdlib/say-check/say_check.py --sentence "TEXT" --boxes FILE
        [--you "your line"] [--earlier FILE] [--json]

    say-check: populated, struck: 1 of 4 checks failed
      every cite was served      held
      every box cited            held
      nothing the boxes lack     failed: 140 is no box's
      your words quoted exactly  nothing quoted

A model may say what code found, in one sentence a person would rather
read. It may not add to it. This holds a sentence to the boxes it was said
about, by four checks, and a sentence that fails one is struck: the caller
shows code's own line in its place. The model is a writer, never an
authority.

1. **every cite was served**: each tag the sentence cites, `[b1]`, is a box
   it was given, now or (with --earlier) earlier in the same sitting.
2. **every box cited**: each box it was given now is cited.
3. **nothing the boxes lack**: every number is a box's number, and every
   word is a box's, one of a few free glue words (`GLUE`), or a function
   word (`STOP`). Accents are folded; a word in a script the boxes don't
   hold fails. An earlier box's words count only when the sentence cites it.
4. **your words quoted exactly**: anything in double quotes is in --you,
   word for word. Words quoted from you aren't held to the boxes (they are
   yours, and marked as yours); a number inside a quote still is.

FILE is the boxes, as JSON: a list of `{"id": "b1", "text": "..."}`, or a
report (ci/README.md, "The report contract"), whose rows become boxes b1,
b2, ... in order, each its `where` and its `what`.

It reads the files it is given and writes nothing. It prints a report;
--json gives the same as one object. Exit codes, the kernel's: 0 every
check held; 42 the sentence is struck; 2 refused.

The four checks are willows-grove's (`grove/seat_say.py`, Apache-2.0),
brought here without its code-graph cites and its layer-5 gate, which
willow doesn't have.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    'usage: say_check.py --sentence "TEXT" --boxes FILE [--you "your line"] '
    "[--earlier FILE] [--json]"
)
NAME = "say-check"
#: the four checks, in the order they are run and shown
CHECK_NAMES = (
    "every cite was served",
    "every box cited",
    "nothing the boxes lack",
    "your words quoted exactly",
)
#: free words that carry no fact: the only ones a sentence may add
GLUE = (
    "morning", "oh", "and", "also", "still", "both", "heads up", "no rush",
    "looks like", "anytime", "got it",
)  # fmt: skip
#: function words that carry no fact. Everything else must come from a box
#: or GLUE; a sentence with any other word fails "nothing the boxes lack"
STOP = frozenset(
    "a an the is are was were be been to of in on for with but so that this "
    "it its or as at by you your i there has have had not than then now just "
    "yet from".split()
)
CITE = re.compile(r"\[(\w+)\]")
QUOTE = re.compile(r'["“]([^"“”\n]+)["”]')
NUMBER = re.compile(r"\d+(?:\.\d+)*")
#: any run of letters in any script, so a word the scan can't read is still
#: seen, and fails, and doesn't slip past
WORD = re.compile(r"[^\W\d_]+")


def _n(text: str) -> str:
    return " ".join(text.lower().split())


def _fold(text: str) -> str:
    """Lowercase with accents dropped (café reads as cafe)."""
    d = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in d if not unicodedata.combining(c))


def _stem(w: str) -> str:
    if w.endswith("ss"):
        return w
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            w = w[: -len(suf)]
            break
    return w.rstrip("e")


def _bare(sentence: str) -> str:
    """The sentence with cite tags and the possessive 's removed."""
    return re.sub(r"['’]s\b", "", CITE.sub(" ", sentence))


def _words(text: str) -> list[str]:
    return [w for w in WORD.findall(text) if len(w) > 1 or not w.isascii()]


# ── the four checks: each says what failed, and nothing when it held ────────
def unserved(sentence: str, boxes: list[dict], earlier: list[dict] | None = None):
    """The tags the sentence cites that are no box it was given, now or
    earlier in the sitting."""
    served = {b["id"] for b in boxes} | {b["id"] for b in earlier or []}
    return sorted(set(CITE.findall(sentence)) - served)


def uncited(sentence: str, boxes: list[dict]) -> list[str]:
    """The boxes given now that the sentence doesn't cite (earlier ones are
    its choice)."""
    cited = set(CITE.findall(sentence))
    return [b["id"] for b in boxes if b["id"] not in cited]


def lacking(
    sentence: str, boxes: list[dict], human: str = "", earlier: list[dict] | None = None
) -> list[str]:
    """The numbers and words of the sentence that no box holds. A span
    quoted word for word from the person is their own, so its words aren't
    scanned; its numbers still are, since a quote is no way to get a figure
    past the boxes. A sentence with no word at all is not one."""
    text = _fold(_bare(sentence))
    # an earlier box's facts count only when the sentence cites it
    now = {b["id"] for b in boxes}
    cited = set(CITE.findall(sentence))
    boxes = [*boxes, *(b for b in earlier or [] if b["id"] in cited and b["id"] not in now)]  # fmt: skip
    facts = _fold(re.sub(r"['’]s\b", "", " ".join(b["text"] for b in boxes)))
    if not _words(text):
        return ["(no word)"]
    have = set(NUMBER.findall(facts))
    out = [n for n in dict.fromkeys(NUMBER.findall(text)) if n not in have]
    human_n = _n(human)
    outside = QUOTE.sub(
        lambda m: " " if _n(m.group(1)) in human_n else m.group(0), _bare(sentence)
    )
    vocab = {_stem(w) for w in WORD.findall(facts)}
    vocab |= {_stem(w) for g in GLUE for w in WORD.findall(_fold(g))}
    vocab |= {_stem(w) for w in STOP}
    out += [w for w in dict.fromkeys(_words(_fold(outside))) if _stem(w) not in vocab]
    return out


def misquoted(sentence: str, human: str) -> list[str] | None:
    """The quoted spans that aren't the person's words, exactly; None when
    nothing is quoted."""
    quotes = QUOTE.findall(sentence)
    if not quotes:
        return None
    return [q for q in quotes if _n(q) not in _n(human)]


def run_checks(
    sentence: str, boxes: list[dict], human: str = "", earlier: list[dict] | None = None
) -> list[tuple[str, bool | None, str]]:
    """(check, whether it held, what to say) for each of the four, in
    CHECK_NAMES order. A check with nothing to look at is None."""
    a = unserved(sentence, boxes, earlier)
    b = uncited(sentence, boxes)
    c = lacking(sentence, boxes, human, earlier)
    d = misquoted(sentence, human)
    n = len(c)
    return [
        (
            CHECK_NAMES[0],
            not a,
            f"failed: {', '.join(f'[{x}]' for x in a)} was never given"
            if a
            else "held",
        ),  # fmt: skip
        (
            CHECK_NAMES[1],
            not b,
            f"failed: {', '.join(f'[{x}]' for x in b)} is not cited" if b else "held",
        ),  # fmt: skip
        (
            CHECK_NAMES[2],
            not c,
            f"failed: {', '.join(c)} {'is' if n == 1 else 'are'} no box's"
            if c
            else "held",
        ),  # fmt: skip
        (
            CHECK_NAMES[3],
            None if d is None else not d,
            "nothing quoted"
            if d is None
            else "failed: not your words: " + "; ".join(f'"{q}"' for q in d)
            if d
            else "held",
        ),  # fmt: skip
    ]


def passed(results: list[tuple[str, bool | None, str]]) -> bool:
    return not any(ok is False for _, ok, _ in results)


# ── the boxes, from a file ──────────────────────────────────────────────────
def boxes_of(doc: object) -> tuple[list[dict] | None, str]:
    """(the boxes, "") from a list of {id, text} or from a report, whose rows
    are b1, b2, ... in order; (None, why) when it is neither."""
    if isinstance(doc, dict) and isinstance(doc.get("groups"), list):
        try:
            rows = [r for g in doc["groups"] for r in g["rows"]]
            return [
                {"id": f"b{n}", "text": f"{r['where']} {r['what']}"}
                for n, r in enumerate(rows, 1)
            ], ""
        except (KeyError, TypeError):
            return None, "a report's rows each have a where and a what"
    if not isinstance(doc, list):
        return None, 'it is not a list of {"id", "text"}, nor a report'
    seen: set[str] = set()
    for b in doc:
        ok = isinstance(b, dict) and isinstance(b.get("id"), str) and isinstance(b.get("text"), str)  # fmt: skip
        if not ok or not re.fullmatch(r"\w+", b["id"]):
            return None, 'each box is {"id": a tag of letters and digits, "text": its words}'  # fmt: skip
        if b["id"] in seen:
            return None, f"two boxes are both [{b['id']}]"
        seen.add(b["id"])
    return [{"id": b["id"], "text": b["text"]} for b in doc], ""


def report(results: list[tuple[str, bool | None, str]]) -> dict:
    failed = sum(ok is False for _, ok, _ in results)
    said = (
        f"struck: {failed} of {len(results)} checks failed"
        if failed
        else "the sentence stands: no check failed"
    )
    return {
        "addon": NAME,
        "state": "populated",
        "said": said,
        "groups": [
            {"name": None, "rows": [{"where": c, "what": w} for c, _, w in results]}
        ],
    }


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    lines = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    lines += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in rows]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    as_json = False
    it = iter(argv)
    for a in it:
        if a in ("--sentence", "--boxes", "--you", "--earlier"):
            opts[a] = next(it, "")
        elif a == "--json":
            as_json = True
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
    if not opts.get("--sentence", "").strip() or not opts.get("--boxes") or opts.get("--earlier") == "":  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    given: dict[str, list[dict]] = {}
    for opt in ("--boxes", "--earlier"):
        if opt not in opts:
            continue
        try:
            doc = json.loads(Path(opts[opt]).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"refused: {opts[opt]} could not be read: {type(e).__name__}", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        got, why = boxes_of(doc)
        if got is None:
            print(f"refused: {opts[opt]}: {why}", file=sys.stderr)
            return kernel.REFUSED
        given[opt] = got
    if not given["--boxes"]:
        print(f"refused: {opts['--boxes']} holds no box to say anything about", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    results = run_checks(
        opts["--sentence"],
        given["--boxes"],
        opts.get("--you", ""),
        given.get("--earlier"),
    )
    doc = report(results)
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))
    return kernel.ALIVE if passed(results) else kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
