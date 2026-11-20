"""hook_guard.py: a hook that refuses, by rule and never by judgment, a call
that would read the key or write a box outside the kernel. Python 3.9+.

    python adapters/stdlib/hook-guard/hook_guard.py run --box DIR [--also DIR]...
    python adapters/stdlib/hook-guard/hook_guard.py rules

`run` is a PreToolUse hook. It reads what the assistant is about to do (the
JSON Claude Code, Gemini CLI and Cursor send on standard input) and holds it to
its rules, each named when it refuses (exit 2, the reason on standard error):

    key        the call names the box's key file: a Read of it, a command that
               has its path in it. The key is the person's; no assistant opens
               it, whatever for.
    box-write  the call would change something inside the box other than through
               the kernel: a Write, Edit or MultiEdit of a file in it, a
               notebook edit, or a command that redirects into it or runs rm, mv,
               cp, tee, touch, mkdir, ln, truncate, chmod, install, dd or sed -i
               on it; find from it with -delete or -exec of one of those; git -C
               on it with a command that changes files; tar extracting, or
               unzip, into it. Reading the box is fine; `kernel.py` is how it is
               written.

    beside-write  with --also DIR (repeatable): the same as box-write, for a
               folder kept beside the box that only its own program writes in.
               The folder need not exist yet. Reading it is fine.

    refused: rule box-write: this Write is inside the box; only kernel.py writes there.

A rule is a test of paths and words, not a reading of the assistant's meaning:
the same call gets the same answer, and a call it cannot tell is allowed, not
guessed at. It catches the shapes above; a command that builds the path at run
time, or hides it in a script, gets through (that is what the kernel's own
checks, which never trust a file in the box, are for). A relative path is read
against the call's own working directory, `cwd`, when it sends one. Input that
is not a JSON object is refused: a hook that can't read the call can't say it is
safe (hook-fail-closed puts the same rule round any hook).

`rules` lists the rules. It never reads the key, only the path the box's
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
    "beside-write": "with --also DIR, the call would change a file inside that folder kept beside the box",
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
#: find's actions that run a command on each file found
FIND_RUNS = {"-exec", "-execdir", "-ok", "-okdir"}
#: git's commands that change the files of the tree they work on
GIT_CHANGES = {"clean", "checkout", "restore", "reset", "rm", "mv", "apply", "am",
               "pull", "merge", "rebase", "switch", "stash"}  # fmt: skip
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


def changes(cmd: list[str], box: Path, cwd: str) -> bool:
    """Whether one command, as words, names a file in `box` that it changes:
    by its last argument or every argument, as the CHANGES lists say."""
    head = Path(cmd[0]).name
    args = [a for a in cmd[1:] if not a.startswith("-")]
    if head in CHANGES_ALL and any(inside(a, box, cwd) for a in args):
        return True
    return head in CHANGES_LAST and bool(args) and inside(args[-1], box, cwd)


def finds_and_changes(cmd: list[str], box: Path, cwd: str) -> bool:
    """find with a root in `box` (the words before its first test) that
    deletes what it finds, or runs on it a command that changes files."""
    roots = []
    for w in cmd[1:]:
        if w.startswith(("-", "(", "!")):
            break
        roots.append(w)
    if not any(inside(r, box, cwd) for r in roots or ["."]):
        return False
    if "-delete" in cmd:
        return True
    for i, w in enumerate(cmd):
        if w in FIND_RUNS and i + 1 < len(cmd):
            run = Path(cmd[i + 1]).name
            if run in CHANGES_ALL | CHANGES_LAST | {"sed", "dd"}:
                return True
    return False


def option(cmd: list[str], short: str = "", long: str = "") -> str | None:
    """The value given an option, as `-C DIR`, `-CDIR`, `--long DIR` or
    `--long=DIR`; None when it isn't given."""
    for i, w in enumerate(cmd):
        if w and w in (short, long):
            return cmd[i + 1] if i + 1 < len(cmd) else None
        if long and w.startswith(long + "="):
            return w[len(long) + 1 :]
        if (
            short
            and w.startswith(short)
            and len(w) > len(short)
            and not w.startswith("--")
        ):
            return w[len(short) :]
    return None


def unpacks_into(cmd: list[str], box: Path, cwd: str) -> bool:
    """tar extracting, or unzip, into `box`: the folder its option names
    (tar's -C or --directory, unzip's -d), else the folder it runs in."""
    head = Path(cmd[0]).name
    if head == "tar":
        flags = [w for w in cmd[1:2] if not w.startswith("-")] + [
            w for w in cmd[1:] if w.startswith("-") and not w.startswith("--")
        ]
        if not ("--extract" in cmd or "--get" in cmd or any("x" in f for f in flags)):
            return False
        to = option(cmd, "-C", "--directory")
    elif head == "unzip":
        if any(w in ("-l", "-t", "-v", "-Z", "-p") for w in cmd[1:]):
            return False  # it lists, tests or prints: nothing is written
        to = option(cmd, "-d")
    else:
        return False
    return inside(to if to is not None else ".", box, cwd)


def git_changes(cmd: list[str], box: Path, cwd: str) -> bool:
    """git working on a tree in `box` (-C DIR or --work-tree=DIR) with a
    command that changes its files."""
    tree = option(cmd, "-C") or option(cmd, long="--work-tree")
    if tree is None or not inside(tree, box, cwd):
        return False
    rest = cmd[1:]
    while rest and rest[0].startswith("-"):  # git's own options, and -C's value
        rest = (
            rest[2:]
            if rest[0] in ("-C", "-c", "--work-tree", "--git-dir")
            else rest[1:]
        )
    return bool(rest) and rest[0] in GIT_CHANGES


def writes_box(command: str, box: Path, cwd: str) -> bool:
    """Whether the command would change something in the folder `box`."""
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
        if changes(cmd, box, cwd):
            return True
        if head == "find" and finds_and_changes(cmd, box, cwd):
            return True
        if head == "git" and git_changes(cmd, box, cwd):
            return True
        if unpacks_into(cmd, box, cwd):
            return True
        if head == "mv" and any(inside(a, box, cwd) for a in args[:-1]):
            return True  # a file moved out of the folder changes it too
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


def judge(
    raw: str, box: Path, key: Path, also: tuple[Path, ...] = ()
) -> tuple[int, str]:
    """(exit code, reason) for what a hook was sent. `also` are folders held
    from change like the box (rule beside-write)."""
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
    if tool in WRITERS and any(inside(p, f, cwd) for p in paths for f in also):
        return (
            2,
            f"refused: rule beside-write: this {tool} is inside a folder kept beside the box; only the runtime writes there.",
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
        if any(writes_box(command, f, cwd) for f in also):
            return (
                2,
                "refused: rule beside-write: this command changes something inside a folder kept beside the box; only the runtime writes there.",
            )
    return 0, ""


def _same(path: str, key: Path, cwd: str) -> bool:
    return resolved(path, cwd) == key


def main(argv: list[str]) -> int:
    if argv == ["rules"]:
        for name, what in RULES.items():
            print(f"{name:<10} {what}")
        return kernel.ALIVE
    also: list[str] = []
    rest = argv[3:]
    while len(rest) >= 2 and rest[0] == "--also":
        also.append(rest[1])
        rest = rest[2:]
    if len(argv) >= 3 and argv[:2] == ["run", "--box"] and not rest:
        box = Path(argv[2])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        key = Path(kernel.config(box)["key"]).expanduser()
        try:
            code, why = judge(
                sys.stdin.read(),
                box.resolve(),
                key.resolve(),
                tuple(Path(a).expanduser().resolve() for a in also),
            )
        except OSError:
            return kernel.REFUSED
        if why:
            print(why, file=sys.stderr)
        return code
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
