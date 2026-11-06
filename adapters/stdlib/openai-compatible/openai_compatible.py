"""openai_compatible.py: a model at an OpenAI-compatible endpoint suggests an
answer from the passages your folder served, and the kernel holds it for your seal.

    python adapters/stdlib/openai-compatible/openai_compatible.py ask --box DIR \\
        --url URL --model NAME [--system FILE] [--reasoning EFFORT] [--now TS]
        "your question"

First the kernel bites: the question goes on the record and the passages that
hold it are served. When none are, the model is never asked: nothing in your
folder holds that, and a model with no passage has nothing to say.

Otherwise the served passages go to URL's `/chat/completions` (llama.cpp's
server, Ollama, LM Studio, vLLM, or any endpoint that speaks the same JSON),
numbered, with the rule that it answers only from them and cites each it uses
as [1], [2]. Asked at temperature 0 with a fixed seed, so a server that
honours them answers the same each time. `--system FILE` puts the text of FILE
before that rule: a voice, a persona, never a way around the rule.
`--reasoning none|low|medium|high` asks the model to think that much before it
answers, as `reasoning_effort` in the request; without it, the request says
nothing about reasoning. It is a request setting, and a server may ignore it.

The reply goes to `kernel.py propose` as one suggestion, citing the passages
its brackets name. A reply that names none is printed and proposed to no one:
an answer with no passage under it isn't one. The suggestion then waits for
your seal; this add-on never seals, never reads your key, and sends the model
nothing but the passages this bite served and your question.

An API key, when the endpoint wants one, is read from OPENAI_API_KEY.

Exit codes, the kernel's: 0 a suggestion is waiting on your seal; 42 nothing
served, the endpoint unreachable, or a reply citing nothing; 2 refused.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    "usage: openai_compatible.py ask --box DIR --url URL --model NAME"
    " [--system FILE] [--reasoning none|low|medium|high] [--now TS]"
    ' "your question"'
)
RULE = (
    "Answer only from the numbered passages, which come from the person's own"
    " files. Cite each passage you use by its number in square brackets, like"
    " [1]. If the passages do not answer the question, say so in one sentence"
    " and cite nothing. Never add a fact the passages do not hold."
)
OPTS = ("--box", "--url", "--model", "--system", "--reasoning", "--now")
#: the values `--reasoning` takes, sent as the request's `reasoning_effort`
REASONING = ("none", "low", "medium", "high")
SEED = 0
#: the suggestions contract (adapters/stdlib/ci/README.md): every add-on that
#: proposes a model's reply for your seal says in its claim who answered,
#: where, at what settings and what it did, in this one form, so a person
#: reading the record, and sent-log, read each proposer's the same way:
#: "gemma at http://127.0.0.1:8080/v1 (temperature 0, seed 0) answered from
#: 1 of the 2 passages served". A claim from before the settings were said
#: reads too, with none.
CLAIM = re.compile(
    r"(?P<who>\S.*?) (?P<where>at (?P<url>\S+)|in this process)"
    r"(?: \((?P<settings>[a-z]+ [^,()]+(?:, [a-z]+ [^,()]+)*)\))? (?P<did>\S.*)"
)


def parse(argv: list[str]) -> tuple[dict, str] | None:
    """The options and the question, or None for a command line to refuse."""
    if argv[:1] != ["ask"]:
        return None
    opts, words, it = {}, [], iter(argv[1:])
    for a in it:
        if a in OPTS:
            if a in opts:
                return None
            opts[a] = next(it, "")
        else:
            words.append(a)
    need = ("--box", "--url", "--model")
    if not all(opts.get(k) for k in need) or len(words) != 1:
        return None
    if "--reasoning" in opts and opts["--reasoning"] not in REASONING:
        return None
    if words[0].startswith("--") or not words[0].strip():
        return None
    return opts, words[0]


def settings(seed: int, reasoning: str = "", voice: str = "") -> list[tuple[str, str]]:
    """What a reply was asked at, as a claim says it: the temperature and seed
    always, the reasoning when one was asked for, and the voice's SHA-256 when
    one was sent, since each can change what the model says."""
    out = [("temperature", "0"), ("seed", str(seed))]
    if reasoning:
        out.append(("reasoning", reasoning))
    if voice.strip():
        out.append(("system", f"sha256 {kernel.h256(voice)}"))
    return out


def claim(who: str, where: str, asked_at: list[tuple[str, str]], did: str) -> str:
    """A suggestion's claim in the contract's one form."""
    said = ", ".join(f"{k} {v}" for k, v in asked_at)
    return f"{who} {where} ({said}) {did}"


def read_claim(text: str) -> dict | None:
    """A claim in the contract's form as its parts (`settings` a dict, empty
    for a claim from before they were said), or None for any other claim."""
    m = CLAIM.fullmatch(text)
    if not m:
        return None
    pairs = (s.split(" ", 1) for s in (m["settings"] or "").split(", ") if s)
    return {"who": m["who"], "where": m["where"], "url": m["url"],
            "settings": dict(pairs), "did": m["did"]}  # fmt: skip


def messages(question: str, served: list[dict], voice: str = "") -> list[dict]:
    """The chat the model is sent: the rule (after a voice, if any), then the
    passages numbered from 1, each with where it is, then the question."""
    system = f"{voice.strip()}\n\n{RULE}" if voice.strip() else RULE
    passages = "\n\n".join(
        f"[{i}] ({s['where']})\n{s['text']}" for i, s in enumerate(served, 1)
    )
    user = f"Passages:\n\n{passages}\n\nQuestion: {question}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def cited(reply: str, served: list[dict]) -> list[str]:
    """The served passages' ids that the reply's [n] brackets name, in the
    order first named, each once; a number no passage has is not a cite."""
    out: list[str] = []
    for m in re.finditer(r"\[(\d+(?:\s*,\s*\d+)*)\]", reply):
        for n in re.split(r"\s*,\s*", m.group(1)):
            i = int(n)
            if 1 <= i <= len(served) and served[i - 1]["id"] not in out:
                out.append(served[i - 1]["id"])
    return out


def ask_model(url: str, model: str, chat: list[dict], reasoning: str = "") -> str:
    """The reply's text from URL's /chat/completions. With `reasoning`, the
    request asks for that `reasoning_effort`; without, it names none."""
    body = {"model": model, "messages": chat, "temperature": 0, "seed": SEED}
    if reasoning:
        body["reasoning_effort"] = reasoning
    headers = {"Content-Type": "application/json"}
    if os.environ.get("OPENAI_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['OPENAI_API_KEY']}"
    req = urllib.request.Request(
        url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=900) as r:
        doc = json.loads(r.read().decode("utf-8"))
    return doc["choices"][0]["message"]["content"]


def slug(question: str) -> str:
    words = re.findall(r"[a-z0-9]+", question.lower())
    return "-".join(words)[:60].strip("-") or "answer"


def kernel_says(argv: list[str]) -> tuple[int, str]:
    got = io.StringIO()
    with contextlib.redirect_stdout(got):
        code = kernel.main(argv)
    return code, got.getvalue()


def ask(opts: dict, question: str) -> int:
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    voice = ""
    if opts.get("--system"):
        try:
            voice = Path(opts["--system"]).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            print(f"refused: can't read {opts['--system']}", file=sys.stderr)
            return kernel.REFUSED
    code, out = kernel_says(["bite", "--box", opts["--box"], *now, question])
    try:
        doc = json.loads(out)
    except ValueError:  # a refusal: the kernel's words, untouched
        print(out, end="")
        return code
    served = [s for s in doc.get("served", []) if not s.get("echo")]
    if doc.get("state") == "sealed":
        print(f"sealed already: {doc['answer'].strip()}")
        return kernel.ALIVE
    if not served:
        print("nothing in your folder holds that; no model was asked")
        return kernel.ESCALATE
    try:
        chat = messages(question, served, voice)
        # the reasoning is passed only when asked for, so a call without
        # --reasoning is the call it always was, down to ask_model's arguments
        if opts.get("--reasoning"):
            reply = ask_model(opts["--url"], opts["--model"], chat, opts["--reasoning"])
        else:
            reply = ask_model(opts["--url"], opts["--model"], chat)
    except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
        print(f"unreachable: {opts['--url']} ({e.__class__.__name__})")
        return kernel.ESCALATE
    print(reply.strip())
    cites = cited(reply, served)
    if not cites:
        print("cited no passage; proposed to no one")
        return kernel.ESCALATE
    row = {
        "path": f"answers/{slug(question)}.md",
        "data": reply.strip() + "\n",
        "cites": cites,
        "claim": claim(
            opts["--model"],
            f"at {opts['--url']}",
            settings(SEED, opts.get("--reasoning", ""), voice),
            f"answered from {len(cites)} of the {len(served)} passages served",
        ),
    }
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "suggestion.jsonl"
        f.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        _, out = kernel_says(
            ["propose", "--box", opts["--box"], *now, "--file", str(f)]
        )
    print(out, end="")
    return kernel.ALIVE if out.split()[:1] == ["pass"] else kernel.ESCALATE


def main(argv: list[str]) -> int:
    got = parse(argv)
    if got is None:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    return ask(*got)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
