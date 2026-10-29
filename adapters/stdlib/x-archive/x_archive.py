r"""x_archive.py: An X (Twitter) archive: your posts, replies and direct messages as dated lines. Python 3.9+.

    python adapters/stdlib/x-archive/x_archive.py mirror --from FOLDER --to MIRROR

An X archive keeps its data in .js files: JSON after an assignment, such as
`window.YTD.tweets.part0 = [ ... ]`. This walks FOLDER for .js files of that
shape (hidden folders and files skipped; any other .js, and the archive's other
data files such as likes and followers, skipped and counted) and writes the two
that are your words, oldest first, as dated lines:

    2022-03-02 08:15  Planted out the tomatoes. https://example.org/guide
    2022-03-03 19:40  @ana the slugs are winning. (reply)
    2022-03-04 09:00  dm 12-34: 12: are you coming on Saturday?

A post's text has its entities read (&amp; is &) and each shortened t.co link
replaced by the address it stood for. Times are UTC. A reply is marked. A direct
message line names the conversation and the sender's id (the archive keeps no
names). Retweets are your words only in part and are kept as the archive has
them. Media files and metrics are not copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import html
import json
import re
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WRAPPER = re.compile(
    r"\A\s*window\.YTD\.([A-Za-z0-9_-]+)\.part\d+\s*=\s*(.*?)\s*;?\s*\Z", re.S
)
KINDS = ("tweets", "tweet", "direct-messages", "direct_messages")


def text(v: object) -> str:
    return " ".join(html.unescape(v).split()) if isinstance(v, str) else ""


def tweet_time(v: object) -> str:
    try:
        return (
            datetime.strptime(v, "%a %b %d %H:%M:%S %z %Y")
            .astimezone(timezone.utc)
            .strftime("%Y-%m-%d %H:%M")
        )  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ""


def iso_time(v: object) -> str:
    return (
        f"{v[:10]} {v[11:16]}".rstrip()
        if isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}", v)
        else ""
    )


def tweet(t: dict) -> str:
    body = t.get("full_text") if isinstance(t.get("full_text"), str) else t.get("text")
    body = body if isinstance(body, str) else ""
    entities = t.get("entities") if isinstance(t.get("entities"), dict) else {}
    for u in entities.get("urls") if isinstance(entities.get("urls"), list) else []:
        if (
            isinstance(u, dict)
            and isinstance(u.get("url"), str)
            and isinstance(u.get("expanded_url"), str)
        ):
            body = body.replace(u["url"], u["expanded_url"])
    line = text(body)
    return (
        line + (" (reply)" if t.get("in_reply_to_status_id_str") else "")
        if line
        else ""
    )


def convert(data: bytes) -> str | None:
    m = WRAPPER.match(data.decode("utf-8-sig"))
    if not m or m.group(1) not in KINDS:
        return None
    items = json.loads(m.group(2))
    if not isinstance(items, list):
        return None
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("tweet"), dict):
            t = item["tweet"]
            when, line = tweet_time(t.get("created_at")), tweet(t)
            if line:
                rows.append((when, f"{when}  {line}" if when else line))
        elif isinstance(item.get("dmConversation"), dict):
            conv = item["dmConversation"]
            cid = text(conv.get("conversationId"))
            for msg in (
                conv.get("messages") if isinstance(conv.get("messages"), list) else []
            ):
                mc = msg.get("messageCreate") if isinstance(msg, dict) else None
                if isinstance(mc, dict) and text(mc.get("text")):
                    when = iso_time(mc.get("createdAt"))
                    line = f"dm {cid}: {text(mc.get('senderId'))}: {text(mc['text'])}"
                    rows.append((when, f"{when}  {line}" if when else line))
    return (
        "\n".join(t for _w, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".js",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: x_archive.py mirror --from FOLDER --to MIRROR"


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
            text = convert(path.read_bytes())
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
