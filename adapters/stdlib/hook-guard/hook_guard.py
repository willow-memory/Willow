"""hook_guard.py: a hook that refuses, by rule and never by judgment, a call
that would read the key or write a box outside the kernel. Python 3.9+.

    python adapters/stdlib/hook-guard/hook_guard.py run --box DIR
    python adapters/stdlib/hook-guard/hook_guard.py rules

`run` is a PreToolUse hook. It reads what the assistant is about to do (the
JSON Claude Code, Gemini CLI and Cursor send on standard input) and holds it to
two rules, each named when it refuses (exit 2, the reason on standard error):

    key        the call names the box's key file: a Read of it, a command that
               has its path in it. The key is the person's; no assistant opens
               it, whatever for.
    box-write  the call would change something inside the box other than through
               the kernel: a Write, Edit or MultiEdit of a file in it, a
               notebook edit, or a command that redirects into it or runs rm, mv,
               cp, tee, touch, mkdir, ln, truncate, chmod, install, dd or sed -i
               on it. Reading the box is fine; `kernel.py` is how it is written.

    refused: rule box-write: this Write is inside the box; only kernel.py writes there.

A rule is a test of paths and words, not a reading of the assistant's meaning:
the same call gets the same answer, and a call it cannot tell is allowed, not
guessed at. It catches the shapes above; a command that builds the path at run
time, or hides it in a script, gets through (that is what the kernel's own
checks, which never trust a file in the box, are for). A relative path is read
against the call's own working directory, `cwd`, when it sends one. Input that
is not a JSON object is refused: a hook that can't read the call can't say it is
safe (hook-fail-closed puts the same rule round any hook).

`rules` lists the two rules. It never reads the key, only the path the box's
config names for it, and writes nothing. Exit codes: 0 allowed (or `rules`);
2 refused, or a bad command line.
"""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

RULES = {
    "key": "the call names the box's key file",
    "box-write": "the call would change a file inside the box other than through kernel.py",
}
WRITERS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READERS = {"Read", "NotebookRead"}
PATH_FIELDS = ("file_path", "notebook_path", "path")
#: commands whose every argument is something they change
CHANGES_ALL = {
    "rm",
    "tee",
    "touch",
    "mkdir",
    "truncate",
    "chmod",
    "chown",
    "rmdir",
    "unlink",
    "shred",
}
#: commands whose last argument is where they put something
CHANGES_LAST = {"mv", "cp", "ln", "install", "rsync"}
SEPARATORS = {";", "&&", "||", "|", "&", "|&"}
REDIRECTS = {">", ">>", ">|", "1>", "2>", "&>", "1>>", "2>>", "&>>"}


def resolved(path: str, cwd: str = "") -> Path | None:
    """A path read against cwd (an absolute path ignores it), with ~, .. and
    links resolved; None when it can't be."""
    try:
        return (Path(cwd) / Path(path).expanduser()).resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def inside(path: str, box: Path, cwd: str = "") -> bool:
    """Whether a path (read against cwd) is the box or something in it."""
    p = resolved(path, cwd)
    return p is not None and (p == box or box in p.parents)


def words(command: str) -> list[list[str]]:
    """A command line as its commands, each a list of words. A line shlex can't
    read is split on blanks, which sees less but never raises."""
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        toks = command.split()
    out: list[list[str]] = [[]]
    for t in toks:
        if t in SEPARATORS:
            out.append([])
        else:
            out[-1].append(t)
    return [c for c in out if c]


def names_key(command: str, key: Path, cwd: str) -> bool:
    """Whether the command has the key's path in it, or a word that is it."""
    if str(key) in command:
        return True
    return any(_same(w, key, cwd) for cmd in words(command) for w in cmd)


def writes_box(command: str, box: Path, cwd: str) -> bool:
    for cmd in words(command):
        for i, w in enumerate(cmd):
            target = cmd[i + 1] if i + 1 < len(cmd) else ""
            if w in REDIRECTS and target and inside(target, box, cwd):
                return True
            for r in REDIRECTS:  # ">file" written together
                if (
                    w.startswith(r)
                    and len(w) > len(r)
                    and w != r
                    and inside(w[len(r) :], box, cwd)
                ):
                    return True
        head = Path(cmd[0]).name
        args = [a for a in cmd[1:] if not a.startswith("-")]
        if head in CHANGES_ALL and any(inside(a, box, cwd) for a in args):
            return True
        if head in CHANGES_LAST and args and inside(args[-1], box, cwd):
            return True
        if head == "sed" and any(
            a.startswith("-i") or a == "--in-place" for a in cmd[1:]
        ):
            if any(inside(a, box, cwd) for a in args):
                return True
        if head == "dd" and any(
            a.startswith("of=") and inside(a[3:], box, cwd) for a in cmd[1:]
        ):
            return True
    return False


def judge(raw: str, box: Path, key: Path) -> tuple[int, str]:
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
    tool, given = call.get("tool_name"), call.get("tool_input")
    given = given if isinstance(given, dict) else {}
    cwd = call.get("cwd") if isinstance(call.get("cwd"), str) else ""
    paths = [given[f] for f in PATH_FIELDS if isinstance(given.get(f), str)]
    if tool in READERS | WRITERS or tool in ("Grep", "Glob"):
        if any(_same(p, key, cwd) for p in paths):
            return (
                2,
                f"refused: rule key: this {tool} names the key file; the key is the person's.",
            )
    if tool in WRITERS and any(inside(p, box, cwd) for p in paths):
        return (
            2,
            f"refused: rule box-write: this {tool} is inside the box; only kernel.py writes there.",
        )
    if tool == "Bash" and isinstance(given.get("command"), str):
        command = given["command"]
        if names_key(command, key, cwd):
            return (
                2,
                "refused: rule key: this command names the key file; the key is the person's.",
            )
        if writes_box(command, box, cwd):
            return (
                2,
                "refused: rule box-write: this command changes something inside the box; only kernel.py writes there.",
            )
    return 0, ""


def _same(path: str, key: Path, cwd: str) -> bool:
    return resolved(path, cwd) == key


def main(argv: list[str]) -> int:
    if argv == ["rules"]:
        for name, what in RULES.items():
            print(f"{name:<10} {what}")
        return kernel.ALIVE
    if len(argv) == 3 and argv[0] == "run" and argv[1] == "--box":
        box = Path(argv[2])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        key = Path(kernel.config(box)["key"]).expanduser()
        try:
            code, why = judge(sys.stdin.read(), box.resolve(), key.resolve())
        except OSError:
            return kernel.REFUSED
        if why:
            print(why, file=sys.stderr)
        return code
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
