"""plain.py: the kernel's answer as sentences instead of JSON. Python 3.9+.

    python adapters/stdlib/plain/plain.py bite --box DIR [--now TS] "your words"

It runs the kernel's own bite, so the record and the exit code are exactly the
kernel's, and prints what came back for a person to read:

    From mail/2026-03-20-county.txt, line 12:
        The proposed determination limits the above well to in-house
        ...

An approved answer is printed as yours; a passage that only asks the question
back is said to; when nothing holds the question, it says so, then the
kernel's notes on where to look. A refusal passes through as the kernel wrote
it.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INDENT = "    "


def where(place: str) -> str:
    """`mail/x.txt:12` as "mail/x.txt, line 12"."""
    path, _, line = place.rpartition(":")
    return f"{path}, line {line}" if line.isdigit() else place


def sentences(doc: dict) -> str:
    """The bite's JSON, as text a person reads."""
    if doc.get("state") == "sealed":
        return f"You approved this answer:\n{INDENT}{doc['answer']}"
    out = []
    for s in doc.get("served", []):
        if s["echo"]:
            out.append(f"{where(s['where'])} only asks your question back.")
            continue
        body = "\n".join(INDENT + line for line in s["text"].splitlines())
        out.append(f"From {where(s['where'])}:\n{body}")
    if not out:
        out.append("Nothing in your folder says this.")
    for note in doc.get("look", []):
        line = f"Note: {note['why']}."
        if note.get("where"):
            line += f" {note['where'][:1].upper()}{note['where'][1:]}."
        if note.get("next"):
            line += f" Next: {note['next']}."
        out.append(line)
    return "\n\n".join(out)


def bite(argv: list[str]) -> int:
    got = io.StringIO()
    with contextlib.redirect_stdout(got):
        code = kernel.main(["bite", *argv])
    out = got.getvalue()
    try:
        doc = json.loads(out)
    except ValueError:  # a refusal, or nothing: the kernel's words, untouched
        print(out, end="")
        return code
    print(sentences(doc))
    return code


if __name__ == "__main__":
    if sys.argv[1:2] != ["bite"]:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        raise SystemExit(kernel.REFUSED)
    raise SystemExit(bite(sys.argv[2:]))
