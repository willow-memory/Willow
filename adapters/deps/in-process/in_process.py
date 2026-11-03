"""in_process.py: suggestions from a GGUF model loaded inside this process.

    python adapters/deps/in-process/in_process.py ask --box DIR --model FILE.gguf
        [--system FILE] [--now TS] "your question"

openai-compatible's ask with no server: the kernel bites first, and when it
serves passages, the GGUF model in FILE is loaded here, through
llama-cpp-python, and given them, numbered, under the rule to answer only
from them, at temperature 0 with a fixed seed. Nothing listens on a port and
nothing leaves this process. A reply is proposed through `kernel.py propose`
citing the passages its brackets name, and waits for your seal; a reply that
cites nothing is printed and proposed to no one, and so is one that cites and
says nothing else (a bare `[1]`, or a path in brackets). When nothing is served, the
model is never loaded.

    Lard, not butter, and a spoonful of anise seed [1].
    pass  proposal:cdd2…  waiting on your seal

The claim names the model file by its name and SHA-256, never by where it
lives: "gemma.gguf (sha256 9c1e…) in this process answered from 1 of the 2
passages served".

Exit codes, the kernel's: 0 a suggestion waits on your seal; 42 nothing
served, the model wouldn't load or answer, or a reply citing nothing; 2
refused (a bad command line, FILE not a file, a --system file that can't be
read, llama-cpp-python not installed).
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_in_process",
    HERE.parent.parent / "stdlib" / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

USAGE = (
    "usage: in_process.py ask --box DIR --model FILE.gguf"
    ' [--system FILE] [--now TS] "your question"'
)
OPTS = ("--box", "--model", "--system", "--now")
#: the context it loads a model with: room for three passages and a reply
CONTEXT = 4096
#: the longest reply it lets a model give
MOST = 512


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
    if not opts.get("--box") or not opts.get("--model") or "" in opts.values():
        return None
    if len(words) != 1 or words[0].startswith("--") or not words[0].strip():
        return None
    return opts, words[0]


def load(path: Path):
    """The model in FILE, loaded here; ImportError when llama-cpp-python isn't."""
    from llama_cpp import Llama

    return Llama(model_path=str(path), n_ctx=CONTEXT, seed=oc.SEED, verbose=False)


def answer(model, chat: list[dict]) -> str:
    """The reply's text, at temperature 0 with the fixed seed."""
    got = model.create_chat_completion(
        messages=chat, temperature=0, seed=oc.SEED, max_tokens=MOST
    )
    return got["choices"][0]["message"]["content"] or ""


def says_something(reply: str) -> bool:
    """Whether the reply holds a content word once its citations are taken
    off: a bare `[1]`, or a path in brackets, points at a passage and answers
    nothing, and a suggestion with no words in it waits on nobody."""
    bare = re.sub(r"\[(?:\d+(?:\s*,\s*\d+)*)\]|\([^()]*:\d+\)", " ", reply)
    return any(w not in kernel.FUNCTION for w in kernel.words(bare))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(io.DEFAULT_BUFFER_SIZE), b""):
            h.update(block)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    got = parse(argv)
    if got is None:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    opts, question = got
    path = Path(opts["--model"])
    if not path.is_file():
        print(f"refused: not a file: {path}", file=sys.stderr)
        return kernel.REFUSED
    if importlib.util.find_spec("llama_cpp") is None:
        print("refused: llama-cpp-python isn't installed; "
              "pip install -r adapters/deps/in-process/requirements.txt", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    voice = ""
    if opts.get("--system"):
        try:
            voice = Path(opts["--system"]).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            print(f"refused: can't read {opts['--system']}", file=sys.stderr)
            return kernel.REFUSED
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    code, out = oc.kernel_says(["bite", "--box", opts["--box"], *now, question])
    try:
        doc = json.loads(out)
    except ValueError:  # a refusal: the kernel's words, untouched
        print(out, end="")
        return code
    if doc.get("state") == "sealed":
        print(f"sealed already: {doc['answer'].strip()}")
        return kernel.ALIVE
    served = [s for s in doc.get("served", []) if not s.get("echo")]
    if not served:
        print("nothing in your folder holds that; no model was loaded")
        return kernel.ESCALATE
    try:
        reply = answer(load(path), oc.messages(question, served, voice))
    # a file that won't load: ValueError at the pin, AssertionError at the floor
    except (
        ValueError,
        AssertionError,
        RuntimeError,
        OSError,
        KeyError,
        IndexError,
        TypeError,
    ) as e:
        print(f"the model didn't answer: {path.name} ({e.__class__.__name__})")
        return kernel.ESCALATE
    print(reply.strip())
    cites = oc.cited(reply, served)
    if not cites:
        print("cited no passage; proposed to no one")
        return kernel.ESCALATE
    if not says_something(reply):
        print("cited a passage and said nothing else; proposed to no one")
        return kernel.ESCALATE
    row = {
        "path": f"answers/{oc.slug(question)}.md",
        "data": reply.strip() + "\n",
        "cites": cites,
        "claim": f"{path.name} (sha256 {sha256_file(path)}) in this process answered"
        f" from {len(cites)} of the {len(served)} passages served",
    }
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "suggestion.jsonl"
        f.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        _, out = oc.kernel_says(
            ["propose", "--box", opts["--box"], *now, "--file", str(f)]
        )
    print(out, end="")
    return kernel.ALIVE if out.split()[:1] == ["pass"] else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
