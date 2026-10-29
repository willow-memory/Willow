"""hook_leaks.py: a hook that refuses a write or a command holding a key,
password or card number. Python 3.9+.

    python adapters/stdlib/hook-leaks/hook_leaks.py run
    python adapters/stdlib/hook-leaks/hook_leaks.py check --from FILE

`run` is a PreToolUse hook. It reads what the assistant is about to do (the
JSON Claude Code, Gemini CLI and Cursor send on standard input) and looks at
the text the call would write or run: a Write's content, an Edit's new text, a
notebook cell, a Bash command. If that text holds a key, a password or a card
number, by the shapes of the [privacy](../privacy/) add-on, the call is
refused: exit 2, and a reason on standard error that says only the kind.

    refused: this Write holds a key and a card number; the value is not shown.
    Take it out, or leave it for the person to put there.

The reason never holds the value, so a refusal can't leak what it stopped.
The text an Edit takes out (`old_string`) is not looked at, so a secret can
still be removed from a file. Any other tool passes: a Read or a search
writes nothing. Input that is not a JSON object is refused too, since a hook
that can't read the call can't say it is safe (hook-fail-closed puts the same
rule round any hook).

`check` is the same look at a file, for a person: it lists the kinds and how
many, and exits 42 when it found any.

It reads nothing else and writes nothing. Exit codes: 0 allowed (or `check`
found nothing); 2 refused, or a bad command line; 42 `check` found something.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "privacy"))
import kernel  # noqa: E402
import privacy  # noqa: E402

#: the tools whose input becomes text on disk or a command
WRITES = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash"}
#: the kinds refused; an email or a phone number is not a secret
KINDS = {"key": "a key", "password": "a password", "card": "a card number"}
#: text a call takes out, which may be a secret on its way out
REMOVED = {"old_string", "old_str", "old_source"}


def strings(value, skip: set[str] = REMOVED):
    """Every string in a tool's input, except the text it removes."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            if k not in skip:
                yield from strings(v, skip)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v, skip)


def leaks(texts) -> dict[str, int]:
    """How many of each refused kind the texts hold."""
    found: dict[str, int] = {}
    for text in texts:
        privacy.scrub(text, found)
    return {k: n for k, n in found.items() if k in KINDS}


def said(found: dict[str, int]) -> str:
    names = [KINDS[k] for k in KINDS if k in found]
    return (
        " and ".join(", ".join(names).rsplit(", ", 1)) if len(names) > 1 else names[0]
    )


def judge(raw: str) -> tuple[int, str]:
    """(exit code, reason) for what a hook was sent."""
    try:
        call = json.loads(raw)
    except ValueError:
        call = None
    if not isinstance(call, dict):
        return (
            2,
            "refused: the hook was sent something it can't read, so it can't say it is safe.",
        )
    tool = call.get("tool_name")
    if tool not in WRITES:
        return 0, ""
    found = leaks(strings(call.get("tool_input")))
    if not found:
        return 0, ""
    return 2, (f"refused: this {tool} holds {said(found)}; the value is not shown.\n"
               "Take it out, or leave it for the person to put there.")  # fmt: skip


def main(argv: list[str]) -> int:
    if argv == ["run"]:
        code, why = judge(sys.stdin.read())
        if why:
            print(why, file=sys.stderr)
        return code
    if len(argv) == 3 and argv[0] == "check" and argv[1] == "--from":
        path = Path(argv[2])
        if not path.is_file():
            print(f"refused: {path} isn't a file", file=sys.stderr)
            return kernel.REFUSED
        found = leaks([path.read_text(encoding="utf-8", errors="replace")])
        for kind, n in found.items():
            print(f"{kind}: {n}")
        if not found:
            print("No key, password or card number found.")
        return kernel.ESCALATE if found else kernel.ALIVE
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
