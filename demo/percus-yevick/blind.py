"""blind.py: the blind questions, written by a local model that has seen no
source, no anchor and none of the author's questions.

    python demo/percus-yevick/blind.py --url URL --model NAME --to FILE [--seed N]

The model gets questions/blind-prompt.txt and nothing else: the steps by
name, in plain words, with no formula. It is asked once, at temperature 0
with a fixed seed (0 unless --seed), with thinking off, through Ollama's
/api/generate at URL (http://127.0.0.1:11434, say), on this machine only.
Its reply is parsed into one question per step, `STEP.1<TAB>question`,
and written to FILE with a header naming the model, the seed, the prompt's
SHA-256 and the reply's, so the file says how it was made; the raw reply is
written beside it as FILE.raw.

A step it gave no question for is left out and said; nothing is filled in
by hand. Run once, before the freeze; the file it writes is frozen as it is.

Exit codes: 0 a question for every step; 42 some step has none; 2 refused.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score  # noqa: E402

PROMPT = HERE / "questions" / "blind-prompt.txt"
LINE = re.compile(
    r"^\s*[-*]?\s*\**\s*([se]\d[a-c]?)\s*\**\s*[:.)\]-]+\s*\**\s*(.+?)\s*$", re.I
)


def ask(url: str, model: str, prompt: str, seed: int) -> str:
    if not url.startswith(("http://127.0.0.1", "http://localhost")):
        raise ValueError("a model on this machine only")
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False,
                       "options": {"temperature": 0, "seed": seed}}).encode()  # fmt: skip
    req = urllib.request.Request(
        url.rstrip("/") + "/api/generate", body, {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.loads(r.read())["response"]


def parse(reply: str) -> dict[str, str]:
    """The first question the reply gives for each step it names."""
    out: dict[str, str] = {}
    for line in reply.splitlines():
        m = LINE.match(line)
        if m and m.group(1).lower() in score.BY_ID and m.group(1).lower() not in out:
            q = m.group(2).strip().strip("*").strip()
            if q:
                out[m.group(1).lower()] = q
    return out


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if (
        len(argv) % 2
        or not {"--url", "--model", "--to"} <= set(opts)
        or set(opts) - {"--url", "--model", "--to", "--seed"}
    ):
        print(
            "usage: blind.py --url URL --model NAME --to FILE [--seed N]",
            file=sys.stderr,
        )
        return 2
    seed = int(opts.get("--seed", "0"))
    prompt = PROMPT.read_text(encoding="utf-8")
    reply = ask(opts["--url"], opts["--model"], prompt, seed)
    got = parse(reply)
    to = Path(opts["--to"])
    head = (
        f"# Blind questions, written by {opts['--model']} through Ollama at temperature 0,\n"
        f"# seed {seed}, thinking off, from questions/blind-prompt.txt alone\n"
        f"# (SHA-256 {hashlib.sha256(prompt.encode()).hexdigest()}). Its reply's SHA-256:\n"
        f"# {hashlib.sha256(reply.encode()).hexdigest()}. Parsed by blind.py; nothing edited by hand.\n"
    )
    order = [s for s in score.BY_ID if s in got]
    to.write_text(head + "".join(f"{s}.1\t{got[s]}\n" for s in order), encoding="utf-8")
    Path(str(to) + ".raw").write_text(reply, encoding="utf-8")
    missing = [s for s in score.BY_ID if s not in got]
    print(
        f"wrote {len(order)} questions to {to}"
        + (f"; none for {', '.join(missing)}" if missing else "")
    )
    return 42 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
