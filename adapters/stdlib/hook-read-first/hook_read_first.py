"""hook_read_first.py: a PreToolUse hook that refuses an edit until the file
was read this session as the bytes still on disk. Python 3.9+.

    python adapters/stdlib/hook-read-first/hook_read_first.py run --box DIR [--now TS]
    python adapters/stdlib/hook-read-first/hook_read_first.py check --box DIR FILE

`run` is a PreToolUse hook. It reads what the assistant is about to do (the
JSON Claude Code, Gemini CLI and Cursor send on standard input):

    Read, NotebookRead
        the file's SHA-256 is written as a `hook-read-first` row through the
        kernel's append (path, hash, and the call's `session_id` when sent).
        The call is allowed.

    Write, Edit, MultiEdit, NotebookEdit
        an existing file must have a read row for this session whose hash
        still matches the bytes on disk; else exit 2 and say why. A Write
        that creates a file (nothing there yet) is allowed without a read.
        After an edit, the old read no longer matches, so the next edit
        needs a fresh Read.

    anything else
        allowed; the hook writes nothing.

`check` is the same look for a person: each FILE is `read` (row named),
`changed` since that row, or `never read` (exit 42 unless every file is
read and unchanged).

It never reads the key. Exit codes: 0 allowed (or `check` every file read);
42 `check` found a gap; 2 refused or blocked.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "hook-read-first"
EDITS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READS = {"Read", "NotebookRead"}
FIELDS = ("file_path", "notebook_path", "path")


def sha(path: Path) -> str | None:
    """SHA-256 of the file's bytes, or None when it can't be read."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def resolved(path: str, cwd: str = "") -> Path | None:
    try:
        return (Path(cwd) / Path(path).expanduser()).resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def target_of(call: dict) -> Path | None:
    """The file a Read or edit call is about, or None."""
    given = call.get("tool_input")
    if not isinstance(given, dict):
        return None
    cwd = call.get("cwd") if isinstance(call.get("cwd"), str) else ""
    for f in FIELDS:
        v = given.get(f)
        if isinstance(v, str) and v:
            return resolved(v, cwd)
    return None


def session_of(call: dict) -> str:
    s = call.get("session_id")
    return s if isinstance(s, str) else ""


def latest_reads(rows: list[dict], session: str) -> dict[str, dict]:
    """Each path's latest read row for this session."""
    out: dict[str, dict] = {}
    for r in rows:
        if r["kind"] != KIND or r.get("session", "") != session:
            continue
        out[r["path"]] = r
    return out


def state(path: Path, latest: dict[str, dict]) -> tuple[str, str]:
    """(read | changed | never read, what to say)."""
    row = latest.get(str(path.resolve()))
    if row is None:
        return "never read", f"never read  {path}"
    got = sha(path)
    if got is None or got != row["sha256"]:
        return "changed", f"changed     {path} (read at row {row['n']})"
    return "read", f"read        {path} (row {row['n']})"


def judge(raw: str, box: Path, ts: str) -> tuple[int, str]:
    """(exit code, reason on stderr) for what a hook was sent."""
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
    if tool in READS:
        path = target_of(call)
        if path is None or not path.is_file():
            return 0, ""  # a missing Read is the tool's problem, not ours
        digest = sha(path)
        if digest is None:
            return 0, ""
        kernel.append(
            box,
            ts,
            KIND,
            who="hook-read-first",
            path=str(path.resolve()),
            sha256=digest,
            session=session_of(call),
        )
        return 0, ""
    if tool not in EDITS:
        return 0, ""
    path = target_of(call)
    if path is None:
        return 0, ""
    if not path.exists():
        return 0, ""  # creating a file: nothing to have read
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return 2, "refused: the record doesn't verify: " + "; ".join(breaks)
    said = state(path, latest_reads(rows, session_of(call)))
    if said[0] != "read":
        return 2, f"blocked: {said[1]}"
    return 0, ""


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            args = []
            break
        else:
            args.append(a)
    verb = args[0] if args else ""
    if not opts.get("--box") or verb not in ("run", "check"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if verb == "run" and len(args) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if verb == "check" and len(args) < 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if verb == "run":
        code, why = judge(sys.stdin.read(), box, opts.get("--now") or kernel.now())
        if why:
            print(why, file=sys.stderr)
        return code
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    # check has no session on the command line: every session's latest per path
    latest: dict[str, dict] = {}
    for r in rows:
        if r["kind"] == KIND:
            latest[r["path"]] = r
    files = [Path(f) for f in args[1:]]
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        print(f"refused: not a file: {', '.join(missing)}", file=sys.stderr)
        return kernel.REFUSED
    said = [state(f, latest) for f in files]
    for _, line in said:
        print(line)
    return kernel.ALIVE if all(s == "read" for s, _ in said) else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
