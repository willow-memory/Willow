"""model_exam.py: a model scored against the answers you sealed, before you trust it.

    python adapters/stdlib/model-exam/model_exam.py --box DIR --url URL \\
        --model NAME --questions FILE

FILE holds your questions, one a line: the exam. Each question whose words
you sealed an answer for is marked; the rest are said and left unmarked.
For each, the kernel ranks your folder's passages as a bite would (nothing
goes on the record), and the model at URL is asked once, with
openai-compatible's chat: the passages, numbered, under the rule to answer
only from them, at temperature 0 with a fixed seed.

A reply passes when it does both of what your sealed answer did:

- **cites** a passage your answer cites, and
- **says it**: holds half the content words of whichever of the two is
  shorter, the kernel's own share (HOLD), counted against the shorter so a
  long reply can't hide a short answer it contains, nor pad its way past.

    pass      what goes in biscochitos  (cites [1] as you did; 4 of 5 words)
    fail      when does the gate stick  (cites [2], you cited [1]; 1 of 4 words)
    unmarked  how tall is the moon: no answer you sealed
    scored 1 of 2 marked (50%); 1 unmarked

Exit codes, the kernel's: 0 every marked question passed; 42 one failed,
none could be marked, or the endpoint didn't answer; 2 refused (a bad
command line, not a box, a record that doesn't verify, a questions file
that can't be read).
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_exam",
    HERE.parent / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

USAGE = "usage: model_exam.py --box DIR --url URL --model NAME --questions FILE"
OPTS = ("--box", "--url", "--model", "--questions")


def answers(box: Path, rows: list[dict]) -> dict[str, dict]:
    """Each sealed answer still standing, by the question's bite key."""
    out = {}
    for subj, seal in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, asked, why = kernel.standing(box, rows, subj, seal)
        if why is None:
            out[asked] = prop
    return out


def served_for(box: Path, question: str) -> list[dict]:
    """What a bite would serve now, without the bite's row, echoes left out."""
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            raise ValueError(why)
    pile = kernel.chunks(Path(cfg["pile"]))
    return [
        {"id": c["id"], "where": f"{c['path']}:{c['line']}", "text": c["text"]}
        for c in kernel.rank(pile, question, alias)
        if not kernel.echo(question, c["text"])
    ]


#: a citation, [1] or [1, 2]: what a text cites, never what it says
CITE = re.compile(r"\[\d+(?:\s*,\s*\d+)*\]")


def content(text: str) -> list[str]:
    words = kernel.words(CITE.sub(" ", text))
    return list(dict.fromkeys(w for w in words if w not in kernel.FUNCTION))


def said(reply: str, answer: str) -> tuple[int, int]:
    """(words held, words counted): the shorter text's content words that the
    longer one holds."""
    a, b = content(reply), content(answer)
    short, long_ = (a, b) if len(a) < len(b) else (b, a)
    toks = kernel.forms(long_)
    return sum(kernel.holds(w, toks) for w in short), len(short)


def numbered(ids: list[str], served: list[dict]) -> str:
    order = [s["id"] for s in served]
    return (
        "["
        + ", ".join(
            str(order.index(i) + 1) if i in order else "not served now" for i in ids
        )
        + "]"
    )


def main(argv: list[str]) -> int:
    opts, words, it = {}, [], iter(argv)
    for a in it:
        if a in OPTS and a not in opts:
            opts[a] = next(it, "")
        else:
            words.append(a)
    if words or not all(opts.get(k) for k in OPTS):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    try:
        text = Path(opts["--questions"]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: can't read the questions: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    sealed = answers(box, rows)
    questions = list(dict.fromkeys(q.strip() for q in text.splitlines() if q.strip()))
    marked = passed = unmarked = 0
    for q in questions:
        prop = sealed.get(kernel.bite_key(q) or "")
        if prop is None:
            unmarked += 1
            print(f"unmarked  {q}: no answer you sealed")
            continue
        try:
            served = served_for(box, q)
        except ValueError as e:
            print(f"refused: {e}", file=sys.stderr)
            return kernel.REFUSED
        if not served:
            unmarked += 1
            print(f"unmarked  {q}: your folder serves nothing for it now")
            continue
        try:
            reply = oc.ask_model(opts["--url"], opts["--model"], oc.messages(q, served))
        except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
            print(f"unreachable: {opts['--url']} ({e.__class__.__name__}), at {q}")
            return kernel.ESCALATE
        cites, yours = oc.cited(reply, served), list(prop.get("cites", []))
        held, counted = said(reply, prop.get("data", ""))
        cites_ok = bool(set(cites) & set(yours))
        says_ok = counted > 0 and held >= kernel.HOLD * counted
        marked += 1
        how = (f"cites {numbered(cites, served)} as you did" if cites_ok
               else f"cites {numbered(cites, served)}, you cited {numbered(yours, served)}")  # fmt: skip
        if cites_ok and says_ok:
            passed += 1
            print(f"pass      {q}  ({how}; {held} of {counted} words)")
        else:
            print(f"fail      {q}  ({how}; {held} of {counted} words)")
    if not marked:
        print(
            f"nothing marked: {unmarked} of {len(questions)} questions have no sealed answer to mark against"
        )
        return kernel.ESCALATE
    print(
        f"scored {passed} of {marked} marked ({round(100 * passed / marked)}%); {unmarked} unmarked"
    )
    return kernel.ALIVE if passed == marked else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
