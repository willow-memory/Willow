"""agent_transcript.py: agent session files as numbered turns. Python 3.9+.

    python adapters/stdlib/agent-transcript/agent_transcript.py \\
        mirror --from FOLDER --to MIRROR

Walks FOLDER for `.jsonl` session files (Claude Code, Cursor, and others
that store one JSON object a line with a user or assistant message). Each
file becomes numbered turns of what you said and what the assistant said,
so the kernel can ask what an agent was told. Tool calls, tool results and
hidden thinking are left out: those are not what you were told.

    session f601db41-9cd9-44dd-9fee-6e7494413255
    2 turns

    1  you
    When is the dentist?

    2  assistant
    Tuesday at 3.

Each session is written to MIRROR at the same relative path with `.txt`
added. A file that is not a session (not JSONL, or no turns) is skipped
and counted. Hidden folders and files are skipped.

    wrote 2 files to MIRROR; skipped 1

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: agent_transcript.py mirror --from FOLDER --to MIRROR"


def _texts(content) -> list[str]:
    """Spoken text only: a string, or `text` parts. Not tools or thinking."""
    if isinstance(content, str) and content.strip():
        return [content]
    if not isinstance(content, list):
        return []
    out = []
    for part in content:
        if (
            isinstance(part, dict)
            and part.get("type") == "text"
            and str(part.get("text") or "").strip()
        ):
            out.append(str(part["text"]))
    return out


def _who(obj: dict, msg: dict) -> str | None:
    role = str(msg.get("role") or obj.get("role") or "")
    typ = str(obj.get("type") or "")
    if role == "user" or typ == "user":
        return "you"
    if role == "assistant" or typ == "assistant":
        return "assistant"
    return None


def turns_of(raw: bytes) -> tuple[str, list[tuple[str, str]]] | None:
    """(session id, [(who, text), ...]) or None if this is not a session."""
    sid, turns = "", []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            return None
        if not isinstance(obj, dict):
            return None
        sid = sid or str(obj.get("sessionId") or obj.get("session_id") or "")
        msg = obj.get("message")
        if not isinstance(msg, dict):
            continue
        who = _who(obj, msg)
        if who is None:
            continue
        spoken = _texts(msg.get("content"))
        if not spoken:
            continue
        turns.append((who, "\n".join(spoken).strip()))
    if not turns:
        return None
    return sid, turns


def session_text(raw: bytes) -> str | None:
    got = turns_of(raw)
    if got is None:
        return None
    sid, turns = got
    head = (f"session {sid}\n" if sid else "") + f"{len(turns)} turns\n"
    body = "\n\n".join(f"{n}  {who}\n{text}" for n, (who, text) in enumerate(turns, 1))
    return head + "\n\n" + body + "\n"


def _sources(folder: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name.startswith(".") or not name.endswith(".jsonl"):
                continue
            p = Path(dirpath) / name
            if p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    wrote = skipped = 0
    for path in _sources(src):
        try:
            text = session_text(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            rel = path.relative_to(src)
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except OSError:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = Path(opts["--from"]).resolve(), Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
