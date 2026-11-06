"""llm_cli.py: suggestions through the llm command — any model its plugins
reach. Python 3.9+.

    python adapters/deps/llm-cli/llm_cli.py ask --box DIR [--model NAME]
        [--system FILE] [--now TS] "your question"

First the kernel bites: the question goes on the record and the passages that
hold it are served. When none are, llm is never run: nothing in your folder
holds that, and a model with no passage has nothing to say.

Otherwise the served passages go to `llm` (Simon Willison's CLI), numbered,
with the rule that it answers only from them and cites each it uses as [1],
[2]. `--model` is passed as `llm -m`; without it, llm's default. `--system
FILE` puts that file's text before the rule. llm's own log names the model.

The reply goes to `kernel.py propose` as one suggestion, citing the passages
its brackets name. A reply that names none is printed and proposed to no one.
This add-on never seals, never reads your willow key, and sends the model
nothing but the passages this bite served and your question. Keys for the
model, when a plugin wants one, are llm's to hold.

Exit codes, the kernel's: 0 a suggestion is waiting on your seal; 42 nothing
served, llm unreachable, or a reply citing nothing; 2 refused.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_llm_cli",
    HERE.parents[1] / "stdlib" / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

USAGE = (
    "usage: llm_cli.py ask --box DIR [--model NAME] [--system FILE]"
    ' [--now TS] "your question"'
)
OPTS = ("--box", "--model", "--system", "--now")


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
    if not opts.get("--box") or len(words) != 1:
        return None
    if words[0].startswith("--") or not words[0].strip():
        return None
    return opts, words[0]


def ask_llm(model: str | None, chat: list[dict]) -> str:
    """The reply's text from the llm command."""
    exe = shutil.which("llm")
    if exe is None:
        raise FileNotFoundError("llm")
    system = chat[0]["content"]
    user = chat[1]["content"]
    cmd = [exe, "--no-stream", "-s", system]
    if model:
        cmd += ["-m", model]
    cmd.append(user)
    got = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if got.returncode != 0:
        raise RuntimeError(got.stderr.strip() or got.stdout.strip() or "llm failed")
    return got.stdout


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
    except ValueError:
        print(out, end="")
        return code
    served = [s for s in doc.get("served", []) if not s.get("echo")]
    if doc.get("state") == "sealed":
        print(f"sealed already: {doc['answer'].strip()}")
        return kernel.ALIVE
    if not served:
        print("nothing in your folder holds that; no model was asked")
        return kernel.ESCALATE
    model = opts.get("--model") or None
    try:
        reply = ask_llm(model, oc.messages(question, served, voice))
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"unreachable: llm ({e.__class__.__name__})")
        return kernel.ESCALATE
    print(reply.strip())
    cites = oc.cited(reply, served)
    if not cites:
        print("cited no passage; proposed to no one")
        return kernel.ESCALATE
    who = model or "llm-default"
    row = {
        "path": f"answers/{oc.slug(question)}.md",
        "data": reply.strip() + "\n",
        "cites": cites,
        "claim": f"{who} via llm answered from"
        f" {len(cites)} of the {len(served)} passages served",
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
