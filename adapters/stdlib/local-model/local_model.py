"""local_model.py: suggestions from a model on this machine only.

    python adapters/stdlib/local-model/local_model.py servers [--url URL ...]
    python adapters/stdlib/local-model/local_model.py ask --box DIR [--url URL ...]
        [--model NAME] [--system FILE] [--reasoning EFFORT] [--now TS]
        "your question"

`servers` says which local model servers are running, and the models each
offers, by asking each one's `/v1/models` on the port it listens on unless
told otherwise: Ollama (11434), LM Studio (1234), llama.cpp's server,
llamafile and LocalAI (8080), vLLM (8000), KoboldCpp (5001), Jan (1337)
and GPT4All (4891).

    ollama         http://127.0.0.1:11434/v1  gemma3:4b, qwen3:8b
    lm-studio      http://127.0.0.1:1234/v1   not running

`ask` is openai-compatible's ask, held to this machine: the kernel bites
first, only the passages served go to the model, and its reply is proposed
for your seal citing the passages its brackets name. The first server
answering among those `--url` names, or else in the order above, is asked;
without `--model`, the first model it lists. A URL off this machine (anything but a loopback
address or localhost) is refused before anything is sent. `--system FILE` and
`--reasoning none|low|medium|high` go to openai-compatible's ask as they are.

Exit codes, the kernel's: for `servers`, 0 one is running, 42 none; for
`ask`, openai-compatible's (0 a suggestion waits on your seal; 42 nothing
served, no server running, or a reply citing nothing); 2 refused (a bad
command line, a URL off this machine, a server offering no model).
"""

from __future__ import annotations

import importlib.util
import ipaddress
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_local",
    HERE.parent / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

USAGE = (
    "usage: local_model.py servers [--url URL ...]\n"
    "       local_model.py ask --box DIR [--url URL ...] [--model NAME]"
    " [--system FILE] [--reasoning none|low|medium|high] [--now TS]"
    ' "your question"'
)
#: where each runtime listens unless told otherwise, in the order they are tried
KNOWN = (
    ("ollama", 11434),
    ("lm-studio", 1234),
    ("llama.cpp", 8080),
    ("vllm", 8000),
    ("koboldcpp", 5001),
    ("jan", 1337),
    ("gpt4all", 4891),
)


def on_this_machine(url: str) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def models(url: str) -> list[str] | None:
    """The models URL's /models lists, or None when nothing answers there."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/models", timeout=5) as r:
            doc = json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError):
        return None
    data = doc.get("data") if isinstance(doc, dict) else None
    if not isinstance(data, list):
        return None
    return [str(m["id"]) for m in data if isinstance(m, dict) and m.get("id")]


def known(urls: list[str]) -> list[tuple[str, str]]:
    """(name, url) for each server to try: those given, or the usual ports."""
    if urls:
        return [("given", u) for u in urls]
    return [(name, f"http://127.0.0.1:{port}/v1") for name, port in KNOWN]


def servers(urls: list[str]) -> int:
    running = 0
    for name, url in known(urls):
        got = models(url)
        if got is None:
            print(f"{name:<14} {url}  not running")
        else:
            running += 1
            print(f"{name:<14} {url}  {', '.join(got) or 'offers no model'}")
    return kernel.ALIVE if running else kernel.ESCALATE


def main(argv: list[str]) -> int:
    verb = argv[0] if argv else ""
    if verb == "servers":
        urls, it = [], iter(argv[1:])
        for a in it:
            if a != "--url":
                print(USAGE, file=sys.stderr)
                return kernel.REFUSED
            urls.append(next(it, ""))
        if "" in urls:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
        off = [u for u in urls if not on_this_machine(u)]
        if off:
            print(f"refused: not on this machine: {', '.join(off)}", file=sys.stderr)
            return kernel.REFUSED
        return servers(urls)
    rest, urls, given = [], [], {}
    it = iter(argv[1:])
    for a in it:
        if a == "--url":
            urls.append(next(it, ""))
        elif a == "--model" and a not in given:
            given[a] = next(it, "")
        else:
            rest.append(a)
    if verb != "ask" or "" in urls or "" in given.values():
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    off = [u for u in urls if not on_this_machine(u)]
    if off:
        print(f"refused: not on this machine: {', '.join(off)}; local-model asks a local model",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    # what openai-compatible would refuse, it refuses before any server is looked for
    if oc.parse(["ask", *rest, "--url", "u", "--model", "m"]) is None:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    tried = urls or [u for _, u in known([])]
    url, offered = None, None
    for u in tried:
        offered = models(u)
        if offered is not None:
            url = u
            break
    if url is None and len(urls) == 1 and "--model" in given:
        url = urls[0]  # one server, one model named: asked though it lists none
    if url is None:
        print(f"no local model server is running (looked at {', '.join(tried)})")
        return kernel.ESCALATE
    model = given.get("--model") or (offered[0] if offered else "")
    if not model:
        print(f"refused: {url} offers no model; name one with --model", file=sys.stderr)
        return kernel.REFUSED
    opts, question = oc.parse(["ask", *rest, "--url", url, "--model", model])
    return oc.ask(opts, question)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
