r"""irc.py: IRC logs from WeeChat, irssi or ZNC: one dated line per message. Python 3.9+.

    python adapters/stdlib/irc/irc.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .log and .weechatlog files (hidden folders and files skipped)
and writes each message as a dated line with the channel it was said in:

    2024-03-02 08:15  #garden  ana: Six hours of sun, I read.
    2024-03-02 08:16  #garden  * ben waves
    2024-03-03 19:40  #garden  ben: The slugs are winning.

Three loggers are read, each told apart by its lines:

    WeeChat   2024-03-02 08:15:30<TAB>nick<TAB>message  (irc.libera.#garden.weechatlog)
    irssi     08:15 < nick> message, with "--- Day changed Sun Mar 03 2024"
              lines giving the date; "--- Log opened Sat Mar 02 08:00:00 2024"
    ZNC       [08:15:30] <nick> message  (the date is in the file name:
              #garden_20240302.log)

The channel is read from the file name (the network and the date parts are
dropped). Messages and actions ("* nick waves") are kept; joins, parts, quits,
mode and topic changes are not. A file that is none of the three, or that has
no message, is skipped and counted (a .log of something else is not an error).

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WEECHAT = re.compile(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}):\d{2}\t([^\t]*)\t(.*)$")
IRSSI = re.compile(r"^(\d{2}:\d{2})(?::\d{2})?\s+(?:<\s?([^>]+)>|\*\s+(\S+))\s?(.*)$")
ZNC = re.compile(r"^\[(\d{2}:\d{2})(?::\d{2})?\]\s+(?:<([^>]+)>|\*\s+(\S+))\s?(.*)$")
OPENED = re.compile(
    r"^--- (?:Log opened|Day changed) \w{3} (\w{3}) (\d{1,2})(?: \d{2}:\d{2}:\d{2})? (\d{4})"
)
MONTHS = {
    m: i
    for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)
}
STATUS = {"-->", "<--", "--", "=--", "-!-", "<==", "==>"}


def channel_of(name: str) -> str:
    """The channel a log file is for: the part of its name that starts at # or &."""
    stem = re.sub(r"\.(?:weechatlog|log)$", "", name)
    m = re.search(r"[#&][^#&]*$", stem)
    chan = m.group(0) if m else stem.rsplit(".", 1)[-1]
    return re.sub(r"_\d{8}$", "", chan)


def convert(data: bytes, name: str = "") -> str | None:
    text = data.decode("utf-8-sig", errors="replace")
    chan = channel_of(name)
    stamp = re.search(r"(\d{4})(\d{2})(\d{2})(?=\.log$)", name)
    znc_day = f"{stamp.group(1)}-{stamp.group(2)}-{stamp.group(3)}" if stamp else ""
    day, out = "", []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if m := WEECHAT.match(raw):
            d, t, nick, body = m.groups()
            if nick.strip() in STATUS or not nick.strip() or not body.strip():
                continue
            out.append(
                f"{d} {t}  {chan}  {nick.strip()}: {body.strip()}"
                if nick.strip() != "*"
                else f"{d} {t}  {chan}  * {body.strip()}"
            )
            continue
        if m := OPENED.match(raw):
            mon = MONTHS.get(m.group(1))
            if mon:
                day = f"{m.group(3)}-{mon:02d}-{int(m.group(2)):02d}"
            continue
        for rx, when in ((ZNC, znc_day), (IRSSI, day)):
            if m := rx.match(raw):
                t, nick, actor, body = m.groups()
                if when and (nick or actor):
                    line = (
                        f"{nick}: {body.strip()}"
                        if nick
                        else f"* {actor} {body.strip()}".rstrip()
                    )
                    if (nick and body.strip()) or actor:
                        out.append(f"{when} {t}  {chan}  {line}")
                break
    return "\n".join(out) + "\n" if out else None


EXTS = (".log", ".weechatlog")
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: irc.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
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
            text = convert(path.read_bytes(), path.name)
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
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
