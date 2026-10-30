r"""discord.py: Discord's data package: your messages, one dated line each, by server and channel. Python 3.9+.

    python adapters/stdlib/discord/discord.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .zip files that are a Discord data package (a zip holding
`messages/c<id>/messages.json` or `messages.csv` for each channel; hidden
folders and files skipped; any other zip skipped and counted) and writes the
messages you sent, oldest first, as dated lines:

    2024-03-02 08:15  Garden Club #garden  Six hours of sun.
    2024-03-02 08:16  Direct Message with ben  See you Saturday.

The package is read as the zip it is, without unpacking it to disk. The channel
is named from its `channel.json` (the server, then #channel) or, for a direct
message, from the package's `messages/index.json`; one with neither is "channel"
and its id. Both the older JSON and the newer CSV message files are read. A
message with no text (an attachment alone) is written as "[attachment]". The
package holds only your own messages, so there is no author on a line. Times are
as the package gives them (UTC). A member over 5 MB is left out.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import csv
import io
import json
import re
import zipfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BIGGEST = 5 * 1024 * 1024
MEMBERS = 20_000
MESSAGES = re.compile(r"^(?:.*/)?messages/(c?\d+)/messages\.(json|csv)$", re.I)


def text(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def stamp(v: object) -> str:
    s = text(v)
    return f"{s[:10]} {s[11:16]}".rstrip() if re.match(r"\d{4}-\d{2}-\d{2}", s) else ""


def channel_name(info: dict | None, listed: str, cid: str) -> str:
    if isinstance(info, dict):
        guild = info.get("guild") if isinstance(info.get("guild"), dict) else {}
        if text(info.get("name")):
            return " ".join(
                x for x in (text(guild.get("name")), "#" + text(info["name"])) if x
            )
    return listed or f"channel {cid.lstrip('c')}"


def convert(data: bytes) -> str | None:
    rows = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = z.infolist()
        if len(infos) > MEMBERS:
            return None
        found = [
            (i, m)
            for i in infos
            if (m := MESSAGES.match(i.filename)) and i.file_size <= BIGGEST
        ]
        if not found:
            return None
        names = {i.filename.lower(): i for i in infos}
        index = {}
        for key, i in names.items():
            if key.endswith("messages/index.json") and i.file_size <= BIGGEST:
                loaded = json.loads(z.read(i).decode("utf-8-sig"))
                index = (
                    {str(k): text(v) for k, v in loaded.items()}
                    if isinstance(loaded, dict)
                    else {}
                )
        for info, m in found:
            cid, kind = m.group(1), m.group(2).lower()
            folder = info.filename[: info.filename.rfind("/") + 1]
            meta_info = names.get((folder + "channel.json").lower())
            meta = (
                json.loads(z.read(meta_info).decode("utf-8-sig"))
                if meta_info and meta_info.file_size <= BIGGEST
                else None
            )
            label = channel_name(meta, index.get(cid.lstrip("c"), ""), cid)
            body = z.read(info).decode("utf-8-sig")
            if kind == "json":
                loaded = json.loads(body)
                items = (
                    [
                        (i.get("Timestamp"), i.get("Contents"), i.get("Attachments"))
                        for i in loaded
                        if isinstance(i, dict)
                    ]
                    if isinstance(loaded, list)
                    else []
                )
            else:
                items = [
                    (r.get("Timestamp"), r.get("Contents"), r.get("Attachments"))
                    for r in csv.DictReader(io.StringIO(body))
                ]
            for ts, contents, attachments in items:
                said = text(contents) or ("[attachment]" if text(attachments) else "")
                if said:
                    when = stamp(ts)
                    rows.append(
                        (
                            when,
                            f"{when}  {label}  {said}" if when else f"{label}  {said}",
                        )
                    )
    return (
        "\n".join(t for _s, t in sorted(rows, key=lambda r: r[0])) + "\n"
        if rows
        else None
    )


EXTS = (".zip",)
ERRORS = (
    OSError,
    UnicodeDecodeError,
    ValueError,
    zipfile.BadZipFile,
    RuntimeError,
    csv.Error,
)

USAGE = "usage: discord.py mirror --from FOLDER --to MIRROR"


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
