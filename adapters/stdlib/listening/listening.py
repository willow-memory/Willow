r"""listening.py: Spotify's data download: what you listened to, one dated line per play. Python 3.9+.

    python adapters/stdlib/listening/listening.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are a Spotify streaming history (hidden
folders and files skipped; any other JSON skipped and counted) and writes each
play, oldest first, as a dated line:

    2024-03-02 08:15  Nina Simone - Sinnerman (10:20)
    2024-03-02 09:02  Garden Radio: Staking tomatoes (24:10)

Both shapes of the download are read: the account-data files
(StreamingHistory_music_0.json, with endTime, artistName, trackName and
msPlayed) and the extended history (Streaming_History_Audio_*.json, with ts,
master_metadata_track_name and ms_played, podcasts by episode_name and show).
The time is when the play ended (UTC as the file gives it); the length in
brackets is how much was played, minutes and seconds. A play of under 30
seconds is a skip and is not written. IP addresses, device names and the other
fields of the extended history are not copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

SKIP = 30_000  # milliseconds under which a play is a skip


def words(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def length(ms: int) -> str:
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


def play(item: dict) -> tuple[str, str] | None:
    """(when, the line) of a play, or None when it isn't a play or is a skip."""
    ms = item.get("msPlayed", item.get("ms_played"))
    if isinstance(ms, bool) or not isinstance(ms, int) or ms < SKIP:
        return None
    stamp = item.get("endTime", item.get("ts"))
    when = (
        f"{stamp[:10]} {stamp[11:16]}".strip()
        if isinstance(stamp, str) and len(stamp) >= 10
        else ""
    )
    artist = words(
        item.get("artistName") or item.get("master_metadata_album_artist_name")
    )
    track = words(item.get("trackName") or item.get("master_metadata_track_name"))
    if track:
        what = f"{artist} - {track}" if artist else track
    elif words(item.get("episode_name")):
        show = words(item.get("episode_show_name"))
        what = (
            f"{show}: {words(item['episode_name'])}"
            if show
            else words(item["episode_name"])
        )
    else:
        return None
    return when, f"{when}  {what} ({length(ms)})" if when else f"{what} ({length(ms)})"


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (
        isinstance(doc, list)
        and any(
            isinstance(i, dict) and ("msPlayed" in i or "ms_played" in i) for i in doc
        )
    ):
        return None
    plays = [p for i in doc if isinstance(i, dict) and (p := play(i))]
    return (
        "\n".join(t for _w, t in sorted(plays, key=lambda p: p[0])) + "\n"
        if plays
        else None
    )


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: listening.py mirror --from FOLDER --to MIRROR"


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
