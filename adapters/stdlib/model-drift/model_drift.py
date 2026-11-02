"""model_drift.py: your frozen questions asked again, flagging answers that
change while the model's name and card stay the same.

    python adapters/stdlib/model-drift/model_drift.py freeze --box DIR --url URL \\
        --model NAME --questions FILE [--card CARD] > frozen.json
    python adapters/stdlib/model-drift/model_drift.py again --box DIR --url URL \\
        --frozen frozen.json [--card CARD]

`freeze` asks the model at URL each question in FILE (one a line) that your
folder serves passages for, once, with openai-compatible's chat (the
passages, numbered, under the rule to answer only from them, at temperature
0 with a fixed seed), and prints what it said as JSON: the model's name,
the SHA-256 of its card when `--card` names one, and for each question the
passages served and the answer. It writes nothing: keep what it prints
where you keep things.

`again` asks the same model the same questions now and holds each answer to
the frozen one, its spaces closed up:

    same       what goes in biscochitos
    drifted    when does the gate stick
               then: It sticks in winter [1].
               now:  It sticks when it rains [1].
    not held   how many cups of flour: your folder serves other passages now
    1 of 2 held drifted, with the name gemma-3-4b-it and its card the same

A change is drift only when nothing else moved: the passages served are the
same ones, the model's name is the frozen one, and its card (given to both
or to neither) hashes the same. When the card differs, or one run names a
card and the other doesn't, nothing is flagged: a new card says a new model.

Exit codes, the kernel's: 0 frozen, or no held answer drifted; 42 one
drifted, nothing could be asked or held, or the endpoint didn't answer;
2 refused (a bad command line, not a box, a record that doesn't verify, a
file that can't be read or a frozen file that isn't one).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_drift",
    HERE.parent / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

USAGE = (
    "usage: model_drift.py freeze --box DIR --url URL --model NAME --questions FILE [--card CARD]\n"
    "       model_drift.py again --box DIR --url URL --frozen FILE [--card CARD]"
)
NEEDS = {
    "freeze": ({"--box", "--url", "--model", "--questions"}, {"--card"}),
    "again": ({"--box", "--url", "--frozen"}, {"--card"}),
}
FORMAT = "willow model-drift 1"


class WordsList(Exception):
    """The box's words list doesn't read."""


def served_for(box: Path, question: str) -> list[dict]:
    """What a bite would serve now, without the bite's row, echoes left out."""
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            raise WordsList(why)
    pile = kernel.chunks(Path(cfg["pile"]))
    return [
        {"id": c["id"], "where": f"{c['path']}:{c['line']}", "text": c["text"]}
        for c in kernel.rank(pile, question, alias)
        if not kernel.echo(question, c["text"])
    ]


def closed(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse(argv: list[str]) -> tuple[str, dict] | None:
    verb = argv[0] if argv else ""
    if verb not in NEEDS:
        return None
    need, may = NEEDS[verb]
    opts, it = {}, iter(argv[1:])
    for a in it:
        if a not in need | may or a in opts:
            return None
        opts[a] = next(it, "")
    if not need <= set(opts) or "" in opts.values():
        return None
    return verb, opts


def freeze(box: Path, opts: dict, card: str | None) -> int:
    try:
        text = Path(opts["--questions"]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: can't read the questions: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    asked = []
    for q in dict.fromkeys(q.strip() for q in text.splitlines() if q.strip()):
        served = served_for(box, q)
        if not served:
            print(f"not asked  {q}: nothing in your folder holds that", file=sys.stderr)
            continue
        reply = oc.ask_model(opts["--url"], opts["--model"], oc.messages(q, served))
        asked.append(
            {"question": q, "served": [s["id"] for s in served], "answer": reply}
        )
    if not asked:
        print(
            "nothing frozen: your folder serves passages for none of the questions",
            file=sys.stderr,
        )
        return kernel.ESCALATE
    doc = {"format": FORMAT, "model": opts["--model"], "card": card, "asked": asked}
    print(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True))
    return kernel.ALIVE


def frozen_from(path: Path) -> dict | None:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if (
        not isinstance(doc, dict)
        or doc.get("format") != FORMAT
        or not isinstance(doc.get("model"), str)
    ):
        return None
    asked = doc.get("asked")
    if not isinstance(asked, list) or not all(
        isinstance(a, dict) and isinstance(a.get("question"), str)
        and isinstance(a.get("answer"), str) and isinstance(a.get("served"), list)
        for a in asked
    ):  # fmt: skip
        return None
    return doc


def again(box: Path, opts: dict, card: str | None) -> int:
    doc = frozen_from(Path(opts["--frozen"]))
    if doc is None:
        print(
            f"refused: {opts['--frozen']} is not a frozen file model-drift printed",
            file=sys.stderr,
        )
        return kernel.REFUSED
    model = doc["model"]
    held = drifted = 0
    for a in doc["asked"]:
        q = a["question"]
        served = served_for(box, q)
        if [s["id"] for s in served] != a["served"]:
            print(f"not held   {q}: your folder serves other passages now")
            continue
        reply = oc.ask_model(opts["--url"], model, oc.messages(q, served))
        held += 1
        if closed(reply) == closed(a["answer"]):
            print(f"same       {q}")
        else:
            drifted += 1
            print(
                f"drifted    {q}\n           then: {closed(a['answer'])}\n           now:  {closed(reply)}"
            )
    if not held:
        print(
            f"nothing held: of {len(doc['asked'])} frozen, your folder serves other passages for each"
        )
        return kernel.ESCALATE
    if card != doc.get("card"):
        then = "no card" if doc.get("card") is None else f"card {doc['card']}"
        now = "no card" if card is None else f"card {card}"
        print(
            f"{drifted} of {held} held changed, but nothing is flagged: frozen with {then}, asked with {now}"
        )
        return kernel.ALIVE
    named = "and its card the same" if card else "the same, no card named"
    print(f"{drifted} of {held} held drifted, with the name {model} {named}")
    return kernel.ESCALATE if drifted else kernel.ALIVE


def main(argv: list[str]) -> int:
    got = parse(argv)
    if got is None:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    verb, opts = got
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    card = None
    if "--card" in opts:
        try:
            card = hashlib.sha256(Path(opts["--card"]).read_bytes()).hexdigest()
        except OSError as e:
            print(f"refused: can't read the card: {type(e).__name__}", file=sys.stderr)
            return kernel.REFUSED
    try:
        return (freeze if verb == "freeze" else again)(box, opts, card)
    except WordsList as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
        print(f"unreachable: {opts['--url']} ({e.__class__.__name__})")
        return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
