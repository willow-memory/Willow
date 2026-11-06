"""stack_share.py: a stack you sealed with the Forge, written out to share.
Python 3.9+.

    python adapters/stdlib/stack-share/stack_share.py --box DIR [--sentence TEXT]

It prints, as Markdown, each stack you sealed with the forge add-on's
`propose`: your sentence, a row for each step (the add-on, its card's line,
its promises, and why it is there: the fork it settled and what it was
chosen over, with your reason, or your words reaching it alone), then the
stack file itself, to run with the stack add-on. With --sentence, only the
stack sealed for those words.

It believes the record only on the kernel's word: a stack or a choice is on
the page only while its seal proves under your key and its proposal still
hashes to what you sealed (`kernel.sealed`, `kernel.standing`). It reads no
key itself, and nothing of your folder: what it prints is your sentence, the
add-ons and your reasons.

Exit codes, the kernel's: 0 a page printed; 42 nothing sealed to share; 2
refused (a bad command line, a folder that isn't a box, a record that
doesn't verify, or no sealed stack for --sentence).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: stack_share.py --box DIR [--sentence TEXT]"
#: where the forge add-on proposes, as its card says
STACK_PATH = "forge/stack.md"
DECISIONS = "forge/decisions/"
STEP = re.compile(r"^- (\S+) -- ")
FIELD = re.compile(r"^(line|writes|network): (.*)$", re.M)


def on_record(box: Path) -> tuple[list[dict], list[dict]]:
    """(stacks, choices) sealed and still standing, in the order sealed:
    each stack its row, the words it was sealed for and its text; each
    choice the fork's decision as the forge add-on proposed it."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        raise ValueError(breaks[0])
    stacks, choices = [], []
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, asked, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            continue
        if prop["path"] == STACK_PATH:
            stacks.append({"row": row["n"], "asked": asked, "text": prop["data"]})
        elif prop["path"].startswith(DECISIONS):
            try:
                data = json.loads(prop["data"])
            except ValueError:
                continue
            if isinstance(data, dict) and isinstance(data.get("chose"), str):
                choices.append(data)
    return stacks, choices


def sentence_of(text: str) -> str:
    """The words a stack was proposed for: its first heading."""
    first = text.splitlines()[0] if text else ""
    return first[2:].strip() if first.startswith("# ") else first.strip()


def steps_of(text: str) -> list[str]:
    return [m.group(1) for line in text.splitlines() if (m := STEP.match(line))]


def card_of(name: str) -> tuple[Path | None, dict]:
    """An add-on's card here, and its line and promises."""
    for kind in ("stdlib", "deps"):
        path = ROOT / "adapters" / kind / name / "README.md"
        if path.is_file():
            head = path.read_text(encoding="utf-8").split("-->")[0]
            return path, dict(FIELD.findall(head))
    return None, {}


def why_row(name: str, choices: list[dict]) -> str:
    """Why a step is in the stack: each fork it settled, or your words."""
    said = []
    for c in choices:
        if c["chose"] != name:
            continue
        over = ", ".join(c.get("over") or []) or "nothing else"
        reason = c.get("why") or "no reason given"
        line = f"chosen for “{c.get('word', '?')}” over {over}: {reason}"
        pinned = (c.get("card") or {}).get("sha256")
        path, _ = card_of(name)
        if pinned and path and hashlib.sha256(path.read_bytes()).hexdigest() != pinned:
            line += " (its card has changed since)"
        said.append(line)
    return "; ".join(said) or "your words reached it alone"


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def page(stack: dict, choices: list[dict]) -> str:
    sentence = sentence_of(stack["text"])
    out = [
        f"# {sentence}",
        "",
        "A willow stack, sealed with the Forge, shared with stack-share. It holds",
        "the add-ons and the reasons they were chosen, never a file of the folder.",
        "",
        "| Step | What it does | Promises | Why this one |",
        "|---|---|---|---|",
    ]
    for name in steps_of(stack["text"]):
        _, card = card_of(name)
        promises = (f"writes {card.get('writes', '?')}; network {card.get('network', '?')}"
                    if card else "no card here")  # fmt: skip
        out.append(f"| {cell(name)} | {cell(card.get('line', ''))} | {cell(promises)} "
                   f"| {cell(why_row(name, choices))} |")  # fmt: skip
    out += [
        "",
        "## The stack, to run",
        "",
        "```",
        stack["text"].rstrip("\n"),
        "```",
        "",
        "    python adapters/stdlib/stack/stack.py --box DIR --stack <this stack>.md",
    ]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    if (
        len(argv) not in (2, 4)
        or argv[0] != "--box"
        or (len(argv) == 4 and argv[2] != "--sentence")
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").is_file():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        stacks, choices = on_record(box)
    except ValueError as why:
        print(f"refused: the record doesn't verify: {why}", file=sys.stderr)
        return kernel.REFUSED
    if len(argv) == 4:
        asked = kernel.bite_key(argv[3])
        stacks = [s for s in stacks if s["asked"] == asked]
        if not stacks:
            print(f"refused: no sealed stack for “{argv[3]}”", file=sys.stderr)
            return kernel.REFUSED
    if not stacks:
        print("stack-share: nothing sealed to share; seal a stack the forge add-on proposed first")  # fmt: skip
        return kernel.ESCALATE
    print("\n".join(page(s, choices) for s in stacks), end="")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
