"""backup.py: your record copied somewhere safe, and checked. Python 3.9+.

    python adapters/stdlib/backup/backup.py --box DIR --to FOLDER [--now TS]

Writes one file, FOLDER/willow-backup-YYYYMMDD-HHMMSS.zip, holding the box
as it is: the record, the box's settings, the suggestions handed in and the
answers you approved. Then it checks the copy: every file's bytes match the
box's, and the copied record's chain holds, row by row, as the kernel's
own `read` checks it. A backup that doesn't check out is deleted and the
run fails, so a zip that's there is one that held.

Your key is not in it. It never reads your key: no add-on does. The key is
what approves an answer, so it belongs somewhere other than the backup:
copy it yourself, to a USB stick or a password manager. The output says
where it is and how. A FOLDER that is the key's own folder, or inside the
box or your files, is refused: a backup next to the key, or inside what it
backs up, isn't a backup.

To restore, unzip it where you want the box, and copy your key back where
the box's kernel.json says it lives.

Exit codes, the kernel's: 0 backed up and checked; 2 refused, or the copy
didn't check out.
"""

from __future__ import annotations

import hashlib
import io
import os
import shlex
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: what a box holds; anything else in it isn't the kernel's and isn't copied
KEEP = ("kernel.json", "record.jsonl", "proposals", "written")


def files(box: Path) -> list[Path]:
    out = []
    for name in KEEP:
        p = box / name
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out += sorted(q for q in p.rglob("*") if q.is_file())
    return out


def why_not(box: Path, to: Path) -> str | None:
    """Why FOLDER can't hold the backup, or None."""
    cfg = kernel.config(box)
    to = to.resolve()
    key_dir = Path(cfg["key"]).resolve().parent
    for inside, what in (
        (box.resolve(), "the box"),
        (Path(cfg["pile"]).resolve(), "your files"),
    ):
        if to == inside or inside in to.parents:
            return f"{to} is inside {what}; a backup inside what it backs up isn't one"
    if to == key_dir:
        return f"{to} is where your key is; keep the backup somewhere else"
    return None


def check(zip_path: Path, box: Path) -> str | None:
    """Why the backup doesn't hold, or None: every file's bytes, and the
    copied record's chain read by the kernel."""
    want = {p.relative_to(box).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files(box)}  # fmt: skip
    with zipfile.ZipFile(zip_path) as z:
        got = {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
        record = z.read("record.jsonl") if "record.jsonl" in got else b""
    if got != want:
        missing = sorted(set(want) - set(got)) + sorted(
            n for n in got if got[n] != want.get(n)
        )
        return f"the copy differs from the box: {', '.join(missing[:3])}"
    with tempfile.TemporaryDirectory() as tmp:  # a lone record, not a box
        copy = Path(tmp) / "record.jsonl"
        copy.write_bytes(record)
        rows, breaks = kernel.read(copy)
    if breaks:
        return "the copied record doesn't verify: " + "; ".join(breaks)
    return None


def how_to_copy(key: Path, system: str) -> str:
    """The line that copies the key, for the person to run themselves."""
    if system == "nt":
        return f'copy "{key}" E:\\'
    return f"cp {shlex.quote(str(key))} /path/to/your/usb/stick/"


def backup(box: Path, to: Path, ts: str) -> tuple[Path | None, str]:
    """(the zip, what to tell the person), or (None, why it failed)."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return None, "the record doesn't verify, so it isn't copied: " + "; ".join(
            breaks
        )
    stamp = ts[:19].replace("-", "").replace(":", "").replace("T", "-")
    to.mkdir(parents=True, exist_ok=True)
    out = to / f"willow-backup-{stamp}.zip"
    if out.exists():
        return None, f"{out} is already there; it isn't overwritten"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files(box):
            z.write(p, p.relative_to(box).as_posix())
    out.write_bytes(buf.getvalue())
    why = check(out, box)
    if why:
        out.unlink()
        return None, why
    copy_it = how_to_copy(Path(kernel.config(box)["key"]), os.name)
    n = len(files(box))
    return out, (f"backed up: {out} ({n} files, {len(rows)} rows; every byte and the "
                 f"chain checked)\n\nYour key isn't in it, and willow never reads it. "
                 f"Copy it yourself, somewhere other than the backup:\n\n    {copy_it}\n")  # fmt: skip


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--to", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or not opts.get("--to") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    to = Path(opts["--to"])
    why = why_not(box, to)
    if why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    out, said = backup(box, to, opts.get("--now") or kernel.now())
    if out is None:
        print(f"refused: {said}", file=sys.stderr)
        return kernel.REFUSED
    print(said, end="")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
