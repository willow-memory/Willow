"""same_way.py: a local model asked each question three times, and how often it flips.

    python adapters/stdlib/same-way/same_way.py --box DIR --url URL --model NAME \\
        --questions FILE [--times N] [--system FILE] [--reasoning EFFORT]

FILE holds your questions, one a line. For each, the kernel ranks your
folder's passages as a bite would (nothing goes on the record), and when it
serves any, the model at URL is asked N times (three unless said), with the
same chat openai-compatible sends: the passages, numbered, under the rule to
answer only from them, at temperature 0 with a fixed seed. A server that
honours those says the same thing every time; one that doesn't, flips.
`--system FILE` and `--reasoning none|low|medium|high` mean what they mean to
openai-compatible's ask (a voice put before the rule; the request's
`reasoning_effort`), so this asks exactly the chat that ask would.

    same     3 of 3  what goes in biscochitos  (cites [1])
    flipped  2 ways in 3  when does the gate stick  (cites [2] / [1, 2])
    not asked  how tall is the moon: nothing in your folder holds that
    2 asked, 1 the same every time, 1 flipped (50%)

Answers are compared with their spaces closed up; a flip in what the
answer cites is a flip, even when the words stay. URL must be on this
machine (127.0.0.1, ::1 or localhost): this asks a local model, and your
passages go nowhere else.

Exit codes, the kernel's: 0 every question asked answered the same way
every time; 42 one flipped, none could be asked, or the endpoint didn't
answer; 2 refused (a bad command line, not a box, a record that doesn't
verify, a URL not on this machine, a questions or system file that can't be
read).
"""

from __future__ import annotations

import importlib.util
import ipaddress
import re
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_same_way",
    HERE.parent / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

USAGE = (
    "usage: same_way.py --box DIR --url URL --model NAME --questions FILE [--times N]"
    " [--system FILE] [--reasoning none|low|medium|high]"
)
OPTS = (
    "--box",
    "--url",
    "--model",
    "--questions",
    "--times",
    "--system",
    "--reasoning",
)
TIMES = 3


def on_this_machine(url: str) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def served_for(box: Path, question: str) -> tuple[list[dict], int]:
    """What a bite would serve, without the bite's row: the passages, and how
    many echoes (passages that only say the question back) were left out."""
    cfg = kernel.config(box)
    alias = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            raise ValueError(why)
    pile = kernel.chunks(Path(cfg["pile"]))
    out, echoes = [], 0
    for c in kernel.rank(pile, question, alias):
        if kernel.echo(question, c["text"]):
            echoes += 1
        else:
            out.append(
                {"id": c["id"], "where": f"{c['path']}:{c['line']}", "text": c["text"]}
            )
    return out, echoes


def numbers(reply: str, served: list[dict]) -> str:
    """The passages a reply cites, by their numbers in the chat."""
    ids = oc.cited(reply, served)
    order = [s["id"] for s in served]
    return "[" + ", ".join(str(order.index(i) + 1) for i in ids) + "]"


def main(argv: list[str]) -> int:
    opts, words, it = {}, [], iter(argv)
    for a in it:
        if a in OPTS and a not in opts:
            opts[a] = next(it, "")
        else:
            words.append(a)
    need = ("--box", "--url", "--model", "--questions")
    times = opts.get("--times", str(TIMES))
    if (
        words
        or not all(opts.get(k) for k in need)
        or not times.isdigit()
        or int(times) < 2
        or opts.get("--reasoning", "none") not in oc.REASONING
        or opts.get("--system") == ""
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    times = int(times)
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
    if not on_this_machine(opts["--url"]):
        print(f"refused: {opts['--url']} is not on this machine; same-way asks a local model",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    try:
        text = Path(opts["--questions"]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: can't read the questions: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    voice = ""
    if opts.get("--system"):
        try:
            voice = Path(opts["--system"]).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"refused: can't read the system file: {type(e).__name__}",
                  file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
    reasoning = opts.get("--reasoning", "")
    questions = list(dict.fromkeys(q.strip() for q in text.splitlines() if q.strip()))
    asked = same = 0
    for q in questions:
        try:
            served, echoes = served_for(box, q)
        except ValueError as e:
            print(f"refused: {e}", file=sys.stderr)
            return kernel.REFUSED
        if not served:
            why = (
                "your folder holds only the question itself"
                if echoes
                else "nothing in your folder holds that"
            )
            print(f"not asked  {q}: {why}")
            continue
        chat = oc.messages(q, served, voice)
        replies = []
        for _ in range(times):
            try:
                replies.append(
                    oc.ask_model(opts["--url"], opts["--model"], chat, reasoning)
                )
            except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
                print(f"unreachable: {opts['--url']} ({e.__class__.__name__}), at {q}")
                return kernel.ESCALATE
        ways = {(re.sub(r"\s+", " ", r).strip(), numbers(r, served)) for r in replies}
        cites = " / ".join(dict.fromkeys(numbers(r, served) for r in replies))
        asked += 1
        if len(ways) == 1:
            same += 1
            print(f"same     {times} of {times}  {q}  (cites {cites})")
        else:
            print(f"flipped  {len(ways)} ways in {times}  {q}  (cites {cites})")
    if not asked:
        print(f"0 asked of {len(questions)} questions")
        return kernel.ESCALATE
    flipped = asked - same
    print(f"{asked} asked, {same} the same every time, {flipped} flipped "
          f"({round(100 * flipped / asked)}%)")  # fmt: skip
    return kernel.ALIVE if flipped == 0 else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
