"""pipe.py: questions in on standard input, answers out one per line. Python 3.9+.

    python adapters/stdlib/pipe/pipe.py --box DIR [--now TS] [--grep] [QUESTION ...]

Each line read is one question (or each QUESTION given, instead of reading:
an editor's task can pass words but not type them), asked with the kernel's own bite, so every
question is on the record as if you'd typed it. Each answer comes out on its
own line:

    JSON lines (the default): {"question": ..., "exit": 0, ...the bite...}
    --grep: file:line: text, one line per passage, the way grep prints a
            match, with the file's full path, so fzf, Vim's quickfix, Emacs's
            compilation buffer and an editor's problem list can jump to it.
            An answer you approved comes out as `approved: text`.

Blank lines are skipped. The exit code is the worst of the questions': 2 if
the kernel refused one, else 42 if one found nothing, else 0.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def ask(box: Path, question: str, now: str | None) -> tuple[int, dict | None, str]:
    """One bite: its exit code, its JSON (None on a refusal), and what it said
    on stderr."""
    out, err = io.StringIO(), io.StringIO()
    args = ["bite", "--box", str(box), question] + (["--now", now] if now else [])
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = kernel.main(args)
    try:
        doc = json.loads(out.getvalue())
    except ValueError:
        doc = None
    return code, doc, err.getvalue() or out.getvalue()


def grep_lines(doc: dict, pile: Path) -> list[str]:
    """A bite as grep prints matches: path:line: the passage's first line."""
    if doc.get("state") == "sealed":
        return [f"approved: {doc['answer']}"]
    out = []
    for s in doc.get("served", []):
        path, _, line = s["where"].rpartition(":")
        first = (s["text"].splitlines() or [""])[0].strip()
        echo = " (only asks your question back)" if s["echo"] else ""
        out.append(f"{pile / path}:{line}: {first}{echo}")
    return out


def worst(codes: list[int]) -> int:
    if kernel.REFUSED in codes:
        return kernel.REFUSED
    return kernel.ESCALATE if kernel.ESCALATE in codes else kernel.ALIVE


def parse(argv: list[str]) -> dict | None:
    opts, it = {"grep": False, "now": None, "asked": []}, iter(argv)
    for a in it:
        if a == "--box":
            opts["box"] = next(it, "")
        elif a == "--now":
            opts["now"] = next(it, "")
        elif a == "--grep":
            opts["grep"] = True
        elif a.startswith("--"):
            return None
        else:
            opts["asked"].append(a)
    return opts if opts.get("box") and opts["now"] != "" else None


def main(argv: list[str], stdin=None, stdout=None) -> int:
    opts = parse(argv)
    if opts is None:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["box"])
    try:
        pile = Path(
            json.loads((box / "kernel.json").read_text(encoding="utf-8"))["pile"]
        )
    except (OSError, ValueError, KeyError):
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    codes = []
    for raw in opts["asked"] or stdin:
        question = raw.strip()
        if not question:
            continue
        code, doc, said = ask(box, question, opts["now"])
        codes.append(code)
        if opts["grep"]:
            lines = grep_lines(doc, pile) if doc else [f"refused: {said.strip()}"]
            for ln in lines:
                print(ln, file=stdout)
        else:
            row = {
                "question": question,
                "exit": code,
                **(doc or {"refused": said.strip()}),
            }
            print(json.dumps(row, ensure_ascii=False), file=stdout)
    return worst(codes)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
