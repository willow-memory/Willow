"""hook_ask_first.py: a PreToolUse hook that refuses reading by hand a file a
box already holds, until that box has been asked this session. Python 3.9+.

    python adapters/stdlib/hook-ask-first/hook_ask_first.py run --boxes FILE [--now TS]
    python adapters/stdlib/hook-ask-first/hook_ask_first.py check --boxes FILE PATH [PATH ...]

An assistant given a project with boxes and stacks will build them, run them,
and then read the files by hand anyway: `tail` on a log, Read on a document,
`grep` through a folder a reader already turned into passages. The box is
never asked, so nothing it was built for is tried. This is the rule that
stops that, held by code where asking in words did not hold.

FILE is a list of boxes, the one [boxes-here](../boxes-here/) keeps. What a
box holds is read from the stacks beside it, never from a list kept by hand:

- its pile, the folder its `kernel.json` names;
- every folder a step of a stack beside the box reads into that pile: a step
  whose `--to` is in the pile holds each of its `--from` folders, and so does
  a step that copies into one of those. The step's add-on, and its card's
  own line, are named when a read is refused.

`run` reads what the assistant is about to do (the JSON Claude Code sends a
PreToolUse hook on standard input) and finds the files it would read by hand:

    Read, NotebookRead      the file named
    Grep                    the path searched, when one is given
    Bash                    each file named to a program that prints files
                            (cat, head, tail, grep, sed, awk, cut, wc, jq ...),
                            the command split as the shell splits it by the
                            hook-shell add-on, a `cd` and a `P=...` followed

For a file some box holds, the box's record is looked at. The first time in
a session, a `hook-ask-first` row is written (the folder held and the
session, never a word of a file) and the read is refused, saying which box
holds it, by which step, and how to ask. Once that box's record has an ask
(a `bite` row) after that row, the session reads freely what the box holds:
it asked first. Each box is its own: asking one opens nothing of another.

It fails open. A list that isn't there, a box that has moved, a record that
doesn't verify, a command that can't be split, input that isn't a call:
each is let through with a line on standard error, since a PreToolUse hook
that exits 2 on its own trouble locks the assistant out of the machine.

`check` is the same look for a person: for each PATH, the box that holds it
and why, and how many asks that box's record has; or that no box listed
holds it.

Exit codes, the kernel's: `run` 0 allowed, 2 a read refused; `check` 0 no
path is held, 42 one is (its box is the place to ask), 2 a bad command line.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "stack"))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "hook-shell"))
import hook_shell  # noqa: E402
import kernel  # noqa: E402
import stack  # noqa: E402

KIND = "hook-ask-first"
READS = {"Read", "NotebookRead"}
#: Programs that print what a file says. A file named to one of these is read.
PRINTS = {
    "cat", "head", "tail", "less", "more", "grep", "egrep", "fgrep", "rg", "sed",
    "awk", "cut", "wc", "sort", "uniq", "nl", "tac", "strings", "jq", "bat", "view",
}  # fmt: skip


def boxes_of(file: Path) -> list[Path]:
    """The boxes a boxes-here list names that are there."""
    said = json.loads(file.read_text(encoding="utf-8"))
    out = []
    for row in said if isinstance(said, list) else []:
        box = Path(row["box"]) if isinstance(row, dict) and "box" in row else None
        if box is not None and (box / "kernel.json").is_file():
            out.append(box)
    return out


def card_line(name: str) -> str:
    """What an add-on's own card says it does, or nothing."""
    script = stack.resolve(name)
    card = script.parent / "README.md" if script else None
    if card is None or not card.is_file():
        return ""
    for line in card.read_text(encoding="utf-8").splitlines()[:20]:
        if line.startswith("line:"):
            return line[5:].strip()
    return ""


def under(path: Path, folder: Path) -> bool:
    return path == folder or folder in path.parents


def holds(box: Path) -> list[tuple[Path, str]]:
    """(folder, why) for everything this box holds: its pile, and each folder
    a step of a stack beside it reads into that pile."""
    try:
        pile = Path(json.loads((box / "kernel.json").read_text())["pile"]).resolve()
    except (OSError, ValueError, KeyError, TypeError):
        return []
    out = [(pile, "it is the box's pile")]
    moves = []
    for file in sorted(box.parent.glob("*.md")):
        try:
            pools, bad = stack.parse_stack(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if bad:
            continue
        for _pool, steps in pools:
            for name, args in steps:
                args = [a.replace("{box}", str(box)) for a in args]
                froms = [args[i + 1] for i, a in enumerate(args[:-1]) if a == "--from"]
                tos = [args[i + 1] for i, a in enumerate(args[:-1]) if a == "--to"]
                if froms and tos:
                    moves.append((name, file.name, froms, tos))
    # A step holds its --from folders when its --to is in something held, so
    # a folder copied in and then read by a reader is held by both steps.
    grew = True
    while grew:
        grew = False
        for name, where, froms, tos in moves:
            if not any(under(Path(t).resolve(), h) for t in tos for h, _ in out):
                continue
            line = card_line(name)
            why = f"the {name} step of {where} reads it into the pile"
            if line:
                why += f" ({name}: {line})"
            for f in froms:
                folder = Path(f).resolve()
                if all(folder != h for h, _ in out):
                    out.append((folder, why))
                    grew = True
    return out


def resolved(word: str, cwd: Path) -> Path | None:
    try:
        p = Path(os.path.expanduser(word))
        return (p if p.is_absolute() else cwd / p).resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def read_by_hand(call: dict) -> list[Path]:
    """The files this call would read by hand."""
    tool, given = call.get("tool_name"), call.get("tool_input")
    if not isinstance(given, dict):
        return []
    cwd = Path(call.get("cwd") or os.getcwd())
    named = []
    if tool in READS:
        named = [given.get("file_path") or given.get("notebook_path")]
    elif tool == "Grep":
        named = [given.get("path")]
    elif tool == "Bash" and isinstance(given.get("command"), str):
        try:
            commands = hook_shell.split(given["command"])
        except Exception:  # a command it can't split is one it can't judge
            return []
        for c in commands:
            words = c.get("words") or []
            if len(words) > 1 and words[0] == "cd":
                cwd = resolved(words[1], cwd) or cwd
            elif words and Path(words[0]).name in PRINTS:
                for w in words[1:]:
                    p = resolved(w, cwd) if not w.startswith("-") else None
                    if p is not None and p.is_file():
                        named.append(str(p))
    out = []
    for n in named:
        p = resolved(n, cwd) if isinstance(n, str) and n else None
        if p is not None and p.exists():
            out.append(p)
    return out


def holder(path: Path, boxes: list[Path]) -> tuple[Path, Path, str] | None:
    """(box, folder, why) for the box that holds this path most closely."""
    best = None
    for box in boxes:
        for folder, why in holds(box):
            if under(path, folder) and (
                best is None or len(folder.parts) > len(best[1].parts)
            ):
                best = (box, folder, why)
    return best


def how_to_ask(box: Path) -> str:
    here = box.parent
    if (here / "ask.py").is_file():
        return f'python {here / "ask.py"} "your question"'
    if here.parent.name == "parts" and (here.parent.parent / "ask.py").is_file():
        ask = here.parent.parent / "ask.py"
        return f'python {ask} --part {here.name} "your question"'
    return f'python {ROOT / "kernel.py"} bite --box {box} "your question"'


def asked_since(rows: list[dict], session: str) -> tuple[bool, bool]:
    """(this session has met the box before, the box was asked since then)."""
    met = False
    for row in rows:
        if row.get("kind") == KIND and row.get("session") == session:
            met = True
        elif met and row.get("kind") == "bite":
            return True, True
    return met, False


def judge(raw: str, boxes: list[Path], ts: str) -> tuple[int, str]:
    """(exit code, what to say on standard error) for what the hook was sent."""
    try:
        call = json.loads(raw)
    except ValueError:
        call = None
    if not isinstance(call, dict):
        return 0, "hook-ask-first: not a call it can read; let through"
    session = call.get("session_id")
    session = session if isinstance(session, str) else ""
    for path in read_by_hand(call):
        held = holder(path, boxes)
        if held is None:
            continue
        box, folder, why = held
        rows, breaks = kernel.read(box / "record.jsonl")
        if breaks:
            return 0, f"hook-ask-first: {box}'s record doesn't verify; let through"
        met, asked = asked_since(rows, session)
        if asked:
            continue
        if not met:
            kernel.append(box, ts, KIND, who=KIND, held=str(folder), session=session)
        return 2, (
            f"blocked: ask first  {path}\n"
            f"  the box at {box} holds it: {why}\n"
            f"  ask the box, then read the place it names:  {how_to_ask(box)}"
        )
    return 0, ""


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[0] not in ("run", "check") or argv[1] != "--boxes":
        return usage()
    rest, ts = argv[3:], kernel.now()
    if argv[0] == "run":
        if rest[:1] == ["--now"] and len(rest) == 2:
            ts, rest = rest[1], []
        if rest:
            return usage()
        try:
            boxes = boxes_of(Path(argv[2]))
            code, said = judge(sys.stdin.read(), boxes, ts)
        except Exception as e:  # its own trouble never locks anyone out
            code, said = 0, f"hook-ask-first: {type(e).__name__}: {e}; let through"
        if said:
            print(said, file=sys.stderr)
        return code
    if not rest or any(a.startswith("--") for a in rest):
        return usage()
    try:
        boxes = boxes_of(Path(argv[2]))
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"refused: {argv[2]} is not a list of boxes: {e}", file=sys.stderr)
        return kernel.REFUSED
    any_held = False
    for word in rest:
        path = resolved(word, Path.cwd())
        held = holder(path, boxes) if path is not None else None
        if held is None:
            print(f"not held  {word}: no box listed holds it")
            continue
        any_held = True
        box, _folder, why = held
        rows, _ = kernel.read(box / "record.jsonl")
        asks = sum(1 for r in rows if r.get("kind") == "bite")
        print(f"held      {word}\n  by {box}: {why}\n  asked {asks} times; ask with:  {how_to_ask(box)}")  # fmt: skip
    return kernel.ESCALATE if any_held else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
