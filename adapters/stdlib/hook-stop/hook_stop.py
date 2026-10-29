"""hook_stop.py: a Stop hook that won't let an assistant's turn end while the
record doesn't verify or its changes aren't committed, and says which.
Python 3.9+.

    python adapters/stdlib/hook-stop/hook_stop.py run --box DIR [--repo DIR]
    python adapters/stdlib/hook-stop/hook_stop.py check --box DIR [--repo DIR]

`run` is a Stop hook: it runs when an assistant is about to end its turn. It
reads the JSON the assistant sends on standard input and looks at two things,
by rule:

    the record   the box's chain must verify (the kernel's own check);
    the work     the repository must have nothing uncommitted: no modified,
                 deleted or untracked file, as `git status` counts them.

If either fails, the turn is not allowed to end: exit 2, and a reason on
standard error that says which and what:

    Not done yet: the record does not verify (row 12 breaks the chain).
    Not done yet: 3 files have changes that are not committed: kernel.py,
    notes/a.md, notes/b.md. Commit them, or say why they stay.

The repository is --repo, else the `cwd` the hook is sent, else the current
folder; a folder that isn't a git repository (or no git at all) is not
checked, and said nothing of. When the hook is sent `stop_hook_active` true,
it has already stopped the turn once this round and is allowed to let it end,
so a rule it cannot satisfy can never trap an assistant in a loop. Input that
is not a JSON object is allowed: a Stop hook that blocked on what it can't
read could not be left running.

`check` is the same look for a person: both results, and exit 42 when
either fails.

It reads git's status (with `--no-optional-locks`, so even git writes nothing)
and the record; it never reads the key and writes nothing. Exit codes: 0 the
turn may end (or `check` is clean); 42 `check` found a failure; 2 a Stop that
must not end, or a bad command line.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

SHOWN = 5  # files named; the count says the rest


def chain(box: Path) -> str:
    """Why the record does not verify, or "" when it does."""
    _, breaks = kernel.read(box / "record.jsonl")
    return breaks[0] if breaks else ""


def uncommitted(repo: Path) -> list[str] | None:
    """The paths git counts as changed or untracked in repo, or None when repo
    is not a repository (or git can't be run)."""
    try:
        got = subprocess.run(
            ["git", "--no-optional-locks", "status", "--porcelain"],
            cwd=repo, capture_output=True, text=True, timeout=30,
        )  # fmt: skip
    except (OSError, subprocess.SubprocessError):
        return None
    if got.returncode != 0:
        return None
    return sorted(line[3:].strip() for line in got.stdout.splitlines() if line.strip())


def reasons(box: Path, repo: Path) -> list[str]:
    out = []
    why = chain(box)
    if why:
        out.append(f"Not done yet: the record does not verify ({why}).")
    files = uncommitted(repo)
    if files:
        n = len(files)
        named = ", ".join(files[:SHOWN]) + (
            f" and {n - SHOWN} more" if n > SHOWN else ""
        )
        count = "1 file has" if n == 1 else f"{n} files have"
        out.append(
            f"Not done yet: {count} changes that are not committed: {named}. "
            "Commit them, or say why they stay."
        )
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv[1:])
    for a in it:
        if a in ("--box", "--repo"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    bad_repo = "--repo" in opts and not opts["--repo"]
    if (
        argv[:1] not in (["run"], ["check"])
        or not opts.get("--box")
        or args
        or bad_repo
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if argv[0] == "check":
        found = reasons(box, Path(opts.get("--repo", ".")))
        print(
            "\n".join(found)
            if found
            else "The record verifies and nothing is uncommitted."
        )
        return kernel.ESCALATE if found else kernel.ALIVE
    try:
        call = json.loads(sys.stdin.read())
    except ValueError:
        call = None
    if not isinstance(call, dict) or call.get("stop_hook_active") is True:
        return kernel.ALIVE
    cwd = (
        call.get("cwd") if isinstance(call.get("cwd"), str) and call.get("cwd") else "."
    )
    repo = Path(opts.get("--repo", cwd))
    found = reasons(box, repo)
    if found:
        print("\n".join(found), file=sys.stderr)
        return kernel.REFUSED
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
