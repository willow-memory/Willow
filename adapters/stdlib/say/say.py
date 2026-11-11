"""say.py: one sentence a model on this machine says about your boxes. Python 3.9+.

    python adapters/stdlib/say/say.py --boxes FILE [--you "your line"] [--earlier FILE]
        [--model TAG] [--host HOST:PORT] [--timeout SECONDS] [--json]

    say: populated, the sentence stands, said by qwen3:4b
      said                       You need to ratify the work order [b5]. PR 712's still waiting [b4].
      every cite was served      held
      every box cited            held
      nothing the boxes lack     held
      your words quoted exactly  nothing quoted

Code finds things and says them plainly. A small model can say the same
things in a sentence a person would rather read. This asks one, on this
machine, for one sentence about the boxes you give it, and then holds that
sentence to the boxes with the say-check add-on's four checks. A sentence
that adds a number or a word the boxes lack, cites a box it wasn't given,
leaves one out, or misquotes you is struck:

    say: populated, struck: 1 of 4 checks failed; code's own line stands
      struck                     You need to ratify the work order [b5]. PR 712's waiting, 140 tests pass [b4].
      nothing the boxes lack     failed: 140 is no box's

The model is a writer, never an authority. What it is told: say one short
sentence, use only the boxes' facts, put each box's tag after its fact,
cite every box once, in the order given, with a short list of free glue
words and nothing else, and quote you only word for word.

FILE is the boxes, as say-check reads them: a list of `{"id", "text"}`, or
a report, whose rows are b1, b2, ... --earlier is boxes shown earlier in
the same sitting, which the sentence may refer back to by their tags.

The model is Ollama's, on this machine only: --host (or OLLAMA_HOST, or
127.0.0.1:11434) must be a loopback address, and anything else is not
asked. --model is the tag (qwen3:4b). When nothing answers, or the tag
isn't installed, it says so, unreachable, and code's line stands.

It reads the files it is given, asks the model on this machine, and writes
nothing: no row on your record, no file. It prints a report (ci/README.md,
"The report contract"); --json gives the same as one object. Exit codes,
the kernel's: 0 the sentence stands; 42 it was struck, or the model
couldn't be asked; 2 refused.

The prompt, the voice and the way Ollama is asked are willows-grove's
(`grove/seat_say.py`, Apache-2.0).
"""

from __future__ import annotations

import json
import os
import re
import sys
import types
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    'usage: say.py --boxes FILE [--you "your line"] [--earlier FILE] [--model TAG] '
    "[--host HOST:PORT] [--timeout SECONDS] [--json]"
)
NAME = "say"
STDLIB = Path(__file__).resolve().parents[1]
MODEL = "qwen3:4b"
DEFAULT_HOST = "127.0.0.1:11434"
#: seconds a sentence is waited for
TIMEOUT = 60.0
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})
#: the voice, scoped to the glue words: it changes no fact
VOICE = (
    "Voice, on the free glue words only: Willow's. Lead with the outcome, "
    "flat and plain, no emotion, no apology, no closing line. The facts stay "
    "exactly as the boxes give them."
)


class SayUnreachable(Exception):
    """The model on this machine can't be asked: the say's unreachable state."""


def sibling(folder: str, module: str):
    """Another add-on's module, from its source beside this one."""
    path = STDLIB / folder / f"{module}.py"
    mod = types.ModuleType(f"say_{module}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


# ── the model: Ollama, on this machine only ─────────────────────────────────
def ollama_base(host: str | None = None) -> str:
    """The loopback base url for a host; anything else is refused, unasked."""
    raw = (host or os.environ.get("OLLAMA_HOST") or DEFAULT_HOST).strip()
    if "://" not in raw:
        raw = "http://" + raw
    try:
        u = urlparse(raw)
        port = u.port or 11434
    except ValueError as e:
        raise SayUnreachable(f"{raw!r} is not a host:port") from e
    name = (u.hostname or "").lower()
    if u.scheme != "http" or name not in LOOPBACK:
        raise SayUnreachable(f"{raw!r} is not this machine; not asked")
    return f"http://[{name}]:{port}" if ":" in name else f"http://{name}:{port}"


def strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", " ", text, flags=re.S).strip()


def ollama_say(model: str = MODEL, host: str | None = None, timeout: float = TIMEOUT):
    """A say: prompt in, the model's words out, by Ollama's /api/generate on
    this machine, through no proxy. It raises SayUnreachable for every way
    it can't answer."""

    def say(prompt: str) -> str:
        base = ollama_base(host)
        # qwen3 thinks aloud unless told not to, twice
        think_off = " /no_think" if model.startswith("qwen3") else ""
        body = json.dumps(
            {
                "model": model,
                "prompt": prompt + think_off,
                "stream": False,
                "think": False,
                "options": {"temperature": 0},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            base + "/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with op.open(req, timeout=timeout) as r:
                got = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            why = "that model isn't installed" if e.code == 404 else f"HTTP {e.code}"
            raise SayUnreachable(f"{model} at {base}: {why}") from e
        except (OSError, ValueError) as e:
            raise SayUnreachable(f"{model} at {base}: {type(e).__name__}") from e
        if not isinstance(got, dict) or not isinstance(got.get("response"), str):
            raise SayUnreachable(f"{model} at {base}: it sent no sentence")
        return strip_think(got["response"])

    return say


# ── what the model is told ──────────────────────────────────────────────────
def flat(text: str) -> str:
    return " ".join(text.split())


def build_prompt(
    boxes: list[dict], human: str, glue, earlier: list[dict] | None = None
) -> str:
    """The prompt for one sentence: the rules, the earlier boxes for context,
    your line, then the boxes with their tags, in the order they are given."""
    lines = [
        VOICE,
        "Say ONE short sentence about the boxes below, and nothing else.",
        "Use only their facts: add no number, name or status they lack.",
        "After each fact put its box tag, like [b1]. Cite every box once, "
        "and no other tag.",
        "Say them in the order given: the boxes are already ranked, most "
        "pressing first.",
        "Free words, and only these: " + ", ".join(glue) + ".",
        "Quote the human only word for word, in double quotes, or not at all.",
        "Reply with the sentence only.",
    ]
    if earlier:
        lines.append(
            "Earlier in this conversation, for context only: you may refer back "
            "to these with that or still, and cite one only by its tag below. "
            "Never quote the human from here."
        )
        lines += [f"[{b['id']}] {flat(b['text'])}" for b in earlier]
    lines += [f"The human asked: {flat(human)}", "Boxes:"]
    lines += [f"[{b['id']}] {flat(b['text'])}" for b in boxes]
    return "\n".join(lines)


def said(
    boxes: list[dict],
    human: str = "",
    earlier: list[dict] | None = None,
    say=None,
    model: str = MODEL,
) -> dict:
    """One sentence about the boxes, and whether it stands: `state` is
    populated (a sentence came: `sentence`, `stands`, and `checks`, say-check's
    four) or unreachable (`why`). `say` is prompt -> words; left None, it is
    Ollama on this machine."""
    check = sibling("say-check", "say_check")
    ask = say or ollama_say(model)
    try:
        sentence = flat(ask(build_prompt(boxes, human, check.GLUE, earlier)))
    except SayUnreachable as e:
        return {"state": "unreachable", "why": str(e), "model": model}
    if not sentence:
        return {"state": "unreachable", "why": f"{model} said nothing", "model": model}
    checks = check.run_checks(sentence, boxes, human, earlier)
    return {
        "state": "populated",
        "sentence": sentence,
        "stands": check.passed(checks),
        "checks": checks,
        "model": model,
    }


def report(got: dict) -> dict:
    if got["state"] == "unreachable":
        return {"addon": NAME, "state": "unreachable", "said": got["why"], "groups": []}
    failed = [c for c in got["checks"] if c[1] is False]
    if got["stands"]:
        line = f"the sentence stands, said by {got['model']}"
        rows = [("said", got["sentence"]), *((c, w) for c, _, w in got["checks"])]
    else:
        n = len(failed)
        line = f"struck: {n} of {len(got['checks'])} checks failed; code's own line stands"  # fmt: skip
        rows = [("struck", got["sentence"]), *((c, w) for c, _, w in failed)]
    return {
        "addon": NAME,
        "state": "populated",
        "said": line,
        "groups": [{"name": None, "rows": [{"where": w, "what": x} for w, x in rows]}],
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
        if a in ("--boxes", "--you", "--earlier", "--model", "--host", "--timeout"):
            opts[a] = next(it, "")
        elif a == "--json":
            as_json = True
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
    try:
        timeout = float(opts.get("--timeout", TIMEOUT))
    except ValueError:
        timeout = 0.0
    if (
        not opts.get("--boxes")
        or any(opts.get(o) == "" for o in ("--earlier", "--model", "--host"))
        or not 0 < timeout < float("inf")
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    check = sibling("say-check", "say_check")
    given: dict[str, list[dict]] = {}
    for opt in ("--boxes", "--earlier"):
        if opt not in opts:
            continue
        try:
            doc = json.loads(Path(opts[opt]).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"refused: {opts[opt]} could not be read: {type(e).__name__}", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        got, why = check.boxes_of(doc)
        if got is None:
            print(f"refused: {opts[opt]}: {why}", file=sys.stderr)
            return kernel.REFUSED
        given[opt] = got
    if not given["--boxes"]:
        print(f"refused: {opts['--boxes']} holds no box to say anything about", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    model = opts.get("--model", MODEL)
    got = said(
        given["--boxes"],
        opts.get("--you", ""),
        given.get("--earlier"),
        ollama_say(model, opts.get("--host"), timeout),
        model,
    )
    doc = report(got)
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))
    return kernel.ALIVE if got.get("stands") else kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
