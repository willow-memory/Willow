"""shell_history.py: your bash, zsh and fish history, each command a dated line.

    python adapters/stdlib/shell-history/shell_history.py mirror --from FOLDER --to MIRROR

Walks FOLDER for history files, skipping hidden folders and files, so copy
yours in without the leading dot (`cp ~/.bash_history FOLDER/bash_history`).
A file is known by its name, never by guessing at what it holds:

    bash_history...   bash: a `#1709460900` line dates the command under it
    zsh_history...    zsh: `: 1709460900:0;git push`, extended or plain
    histfile...       zsh, under the name its own docs suggest
    fish_history...   fish: `- cmd: git push` with `when: 1709460900`

Each command becomes one line, in the order the shell wrote it, with the time
the shell recorded it, in UTC so the same file gives the same bytes on any
machine. A day's commands are one paragraph, so one passage holds a day:

    2024-03-03 10:15:00 UTC  git push
    2024-03-03 10:16:40 UTC  rsync -a photos/ /mnt/backup/

A command the shell kept no time for is written bare, never given a time it
doesn't have. A multi-line command keeps its lines; blank ones close up. zsh's
own escaping of bytes past ASCII is undone, and fish's `\\n` and `\\\\` are.

Each history is written to MIRROR at the same relative path with `.txt`
added. FOLDER is only read: originals are never modified and nothing is
written inside it. A file that cannot be read, or holds no command, is skipped
and counted, never a crash.

    wrote 2 files to MIRROR; skipped 0

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: shell_history.py mirror --from FOLDER --to MIRROR"
BASH_STAMP = re.compile(r"^#(\d+)$")
ZSH_LINE = re.compile(r"^: *(\d+):\d+;(.*)$", re.DOTALL)
FISH_CMD = re.compile(r"^- cmd: ?(.*)$")
FISH_WHEN = re.compile(r"^  when: *(\d+)$")
META = 0x83  # zsh writes a byte it keeps for itself as META, then the byte ^ 32

Command = Tuple[Optional[int], str]  # when the shell recorded it, the command


def shell_of(name: str) -> str | None:
    """Which shell wrote a file, from its name alone, or None."""
    low = name.lower()
    for prefix, shell in (
        ("bash_history", "bash"),
        ("zsh_history", "zsh"),
        ("histfile", "zsh"),
        ("fish_history", "fish"),
    ):
        if low.startswith(prefix):
            return shell
    return None


def unmetafy(raw: bytes) -> bytes:
    """zsh's history bytes as they were typed: META and the next byte ^ 32."""
    if META not in raw:
        return raw
    out, i = bytearray(), 0
    while i < len(raw):
        if raw[i] == META and i + 1 < len(raw):
            out.append(raw[i + 1] ^ 32)
            i += 2
        else:
            out.append(raw[i])
            i += 1
    return bytes(out)


def bash(text: str) -> list[Command]:
    """bash: each line a command, unless `#EPOCH` lines say where each starts."""
    lines = text.splitlines()
    if not any(BASH_STAMP.match(ln) for ln in lines):
        return [(None, ln) for ln in lines if ln.strip()]
    out: list[Command] = []
    when: int | None = None
    body: list[str] = []
    for line in lines + ["#0"]:
        m = BASH_STAMP.match(line)
        if m:
            if body:
                out.append((when, "\n".join(body)))
            when, body = int(m.group(1)), []
        elif line.strip():
            if when is None and not body:
                out.append((None, line))  # before the first stamp: undated
            else:
                body.append(line)
    return out


def zsh(text: str) -> list[Command]:
    """zsh: `: EPOCH:SECONDS;command`, a line ending in a backslash going on."""
    out: list[Command] = []
    lines = iter(text.splitlines())
    for line in lines:
        while line.endswith("\\"):
            nxt = next(lines, None)
            if nxt is None:
                break
            line = line[:-1] + "\n" + nxt
        m = ZSH_LINE.match(line)
        when, cmd = (int(m.group(1)), m.group(2)) if m else (None, line)
        if cmd.strip():
            out.append((when, cmd))
    return out


def _fish_unescape(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] in "\\n":
            out.append("\n" if s[i + 1] == "n" else "\\")
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def fish(text: str) -> list[Command]:
    """fish: `- cmd:` starts a command, its `  when:` dates it."""
    out: list[Command] = []
    for line in text.splitlines():
        m = FISH_CMD.match(line)
        if m:
            out.append((None, _fish_unescape(m.group(1))))
            continue
        w = FISH_WHEN.match(line)
        if w and out and out[-1][0] is None:
            out[-1] = (int(w.group(1)), out[-1][1])
    return [(when, cmd) for when, cmd in out if cmd.strip()]


def _stamp(when: int | None) -> str:
    """`YYYY-MM-DD HH:MM:SS UTC`, or "" for no time or one past any calendar."""
    if when is None:
        return ""
    try:
        t = datetime.fromtimestamp(when, timezone.utc)
    except (OverflowError, ValueError, OSError):
        return ""
    return t.strftime("%Y-%m-%d %H:%M:%S UTC")


def history_text(raw: bytes, shell: str) -> str | None:
    """The mirror text for one history file, or None when it holds no command."""
    if shell == "zsh":
        raw = unmetafy(raw)
    text = raw.decode("utf-8-sig", errors="replace")
    commands = {"bash": bash, "zsh": zsh, "fish": fish}[shell](text)
    if not commands:
        return None
    paras: list[list[str]] = []
    day = None
    for when, cmd in commands:
        stamp = _stamp(when)
        lines = [ln.rstrip() for ln in cmd.split("\n") if ln.strip()]
        if not lines:
            continue
        lines[0] = f"{stamp}  {lines[0]}" if stamp else lines[0]
        if not paras or stamp[:10] != day:
            paras.append([])
            day = stamp[:10]
        paras[-1].extend(lines)
    return "".join("\n".join(p) + "\n\n" for p in paras)


def _sources(folder: Path) -> list[Path]:
    """History files under `folder`, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and shell_of(name) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = history_text(path.read_bytes(), shell_of(path.name))
            if text is None:
                skipped += 1
                continue
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
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
