r"""slack.py: Slack's export zip: one dated line per message, with channel and author. Python 3.9+.

    python adapters/stdlib/slack/slack.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .zip files that are a Slack workspace export (a zip holding
`users.json` or `channels.json` and, for each channel, a folder of
`YYYY-MM-DD.json` day files; hidden folders and files skipped; any other zip
skipped and counted) and writes each message, oldest first, as a dated line:

    2024-03-02 08:15  #garden  ana: Six hours of sun, <@ben>?
    2024-03-02 08:16  #garden  ben: See https://example.org/guide

The export is read as the zip it is, without unpacking it to disk. The author
is the user's display name (else the real name, else the name), the channel is
its folder name with a # in front. A user, channel or link written as Slack
writes it (`<@U1>`, `<#C1|garden>`, `<https://x.org|label>`, `<!here>`) is read
as @ben, #garden, label and @here, and the entities &amp; &lt; &gt; as the
characters. Messages that are joins, leaves, topic changes and the like are
left out; files, reactions and threads' replies' structure are not copied (a
reply is a message like the rest). A member over 5 MB is left out.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import io
import json
import re
import zipfile
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BIGGEST = 5 * 1024 * 1024
MEMBERS = 20_000
DAY = re.compile(r"^([^/]+)/(\d{4}-\d{2}-\d{2})\.json$")
TOKEN = re.compile(r"<([^<>]+)>")
KEPT = (None, "thread_broadcast", "me_message")


def names_of(users: object) -> dict[str, str]:
    out = {}
    for u in users if isinstance(users, list) else []:
        if isinstance(u, dict) and isinstance(u.get("id"), str):
            profile = u.get("profile") if isinstance(u.get("profile"), dict) else {}
            name = next(
                (
                    " ".join(v.split())
                    for v in (
                        profile.get("display_name"),
                        u.get("real_name"),
                        u.get("name"),
                    )
                    if isinstance(v, str) and v.strip()
                ),
                "",
            )
            if name:
                out[u["id"]] = name
    return out


def clean(text: str, users: dict[str, str]) -> str:
    def one(m: re.Match) -> str:
        body, _, label = m.group(1).partition("|")
        if body.startswith("@"):
            return "@" + (label or users.get(body[1:], body[1:]))
        if body.startswith("#"):
            return "#" + (label or body[1:])
        if body.startswith("!"):
            return "@" + (label or body[1:].split("^")[0])
        return label or body

    return " ".join(
        TOKEN.sub(one, text)
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .split()
    )


def when(ts: object) -> str:
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M"
        )  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError, OSError):
        return ""


def convert(data: bytes) -> str | None:
    rows = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = z.infolist()
        if len(infos) > MEMBERS:
            return None
        names = {i.filename: i for i in infos}
        if "users.json" not in names and "channels.json" not in names:
            return None
        users = {}
        if "users.json" in names and names["users.json"].file_size <= BIGGEST:
            users = names_of(json.loads(z.read("users.json").decode("utf-8-sig")))
        for info in infos:
            m = DAY.match(info.filename)
            if not m or info.file_size > BIGGEST:
                continue
            for msg in json.loads(z.read(info).decode("utf-8-sig")):
                if (
                    not isinstance(msg, dict)
                    or msg.get("subtype") not in KEPT
                    or not isinstance(msg.get("text"), str)
                ):
                    continue
                said = clean(msg["text"], users)
                if not said:
                    continue
                stamp = when(msg.get("ts")) or m.group(2)
                who = (
                    users.get(msg.get("user"), msg.get("user"))
                    if isinstance(msg.get("user"), str)
                    else "(unknown)"
                )
                rows.append((stamp, f"{stamp}  #{m.group(1)}  {who}: {said}"))
    return (
        "\n".join(t for _s, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".zip",)
ERRORS = (OSError, UnicodeDecodeError, ValueError, zipfile.BadZipFile, RuntimeError)

USAGE = "usage: slack.py mirror --from FOLDER --to MIRROR"


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
