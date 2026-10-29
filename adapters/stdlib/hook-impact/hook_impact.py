"""hook_impact.py: before an edit, a hook hands the assistant every place in
your files that names what it is about to change. Python 3.9+.

    python adapters/stdlib/hook-impact/hook_impact.py run --box DIR
    python adapters/stdlib/hook-impact/hook_impact.py check --box DIR FILE

`run` is a PreToolUse hook. It reads what the assistant is about to do (the
JSON Claude Code, Gemini CLI and Cursor send on standard input). For a Write,
Edit, MultiEdit or notebook edit of a file, it looks through the box's files
for the lines that name that file, by its name, and says where:

    Before editing kernel.py, these places in the person's files name it:
      docs/notes.md:12  see kernel.py for the rules
      README.md:40  kernel.py is the one file that writes a box
    Check they still say what is true after the edit.

It prints the JSON a PreToolUse hook reads, with those sentences as its
`additionalContext`, and allows the call: it never blocks, and an edit it
finds nothing for prints nothing at all. A name is matched as a whole word with
its extension (kernel.py, not kernel.pyc or my-kernel.py), case as written; the
file's own lines don't count, and ten places are listed, then a count. Any
other tool passes untouched.

`check` is the same look for a person: the places that name FILE, one to a
line, and exit 42 when there are some.

It reads the box's folder only, never the key, and writes nothing, not even
the row `kernel.py out` appends. Exit codes: 0 allowed (or `check` found
nothing); 42 `check` found places; 2 refused (a bad command line, not a box).
A hook should fail open here: a refusal prints its reason on standard error
and adds nothing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

EDITS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
FIELDS = ("file_path", "notebook_path")
SHOWN = 10  # places listed; the count says the rest
WIDTH = 100  # characters of a line shown


def places(
    pile: list[dict], target: Path, pile_dir: Path
) -> list[tuple[str, int, str]]:
    """(file, line number, line) for each line of the pile that names target's
    file name, other than the target's own lines."""
    name = target.name
    rx = re.compile(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])")
    own = None
    try:
        own = target.resolve()
    except (OSError, RuntimeError):
        pass
    out = []
    for path, rows in sorted(habits.file_lines(pile).items()):
        try:
            if own is not None and (pile_dir / path).resolve() == own:
                continue
        except (OSError, RuntimeError):
            pass
        for n, line in rows:
            if rx.search(line):
                out.append((path, n, " ".join(line.split())))
    return out


def sentences(name: str, found: list[tuple[str, int, str]]) -> str:
    lines = [f"Before editing {name}, these places in the person's files name it:"]
    for path, n, line in found[:SHOWN]:
        text = line if len(line) <= WIDTH else line[: WIDTH - 1] + "…"
        lines.append(f"  {path}:{n}  {text}")
    if len(found) > SHOWN:
        lines.append(f"  and {len(found) - SHOWN} more")
    lines.append("Check they still say what is true after the edit.")
    return "\n".join(lines)


def target_of(raw: str) -> Path | None:
    """The file a hook's call is about to change, or None for any other call."""
    try:
        call = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(call, dict) or call.get("tool_name") not in EDITS:
        return None
    given = call.get("tool_input")
    if not isinstance(given, dict):
        return None
    cwd = call.get("cwd") if isinstance(call.get("cwd"), str) else ""
    for f in FIELDS:
        v = given.get(f)
        if isinstance(v, str) and v:
            p = Path(v).expanduser()
            return Path(cwd) / p if cwd and not p.is_absolute() else p
    return None


def look(box: Path, target: Path) -> list[tuple[str, int, str]]:
    pile_dir = Path(kernel.config(box)["pile"])
    return places(kernel.chunks(pile_dir), target, pile_dir)


def main(argv: list[str]) -> int:
    ok = len(argv) >= 3 and argv[1] == "--box"
    if (
        ok
        and argv[0] == "run"
        and len(argv) == 3
        or ok
        and argv[0] == "check"
        and len(argv) == 4
    ):
        box = Path(argv[2])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        if argv[0] == "check":
            target = Path(argv[3])
            found = look(box, target)
            for path, n, line in found:
                print(f"{path}:{n}  {line}")
            if not found:
                print(f"Nothing in your files names {target.name}.")
            return kernel.ESCALATE if found else kernel.ALIVE
        target = target_of(sys.stdin.read())
        found = look(box, target) if target is not None else []
        if found:
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": sentences(target.name, found),
                }
            }
            print(json.dumps(out, ensure_ascii=False))
        return kernel.ALIVE
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
