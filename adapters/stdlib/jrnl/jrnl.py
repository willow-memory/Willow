"""jrnl.py: your jrnl journals, each dated entry a passage the kernel reads.

    python adapters/stdlib/jrnl/jrnl.py mirror --from FOLDER --to MIRROR

Walks FOLDER for jrnl journals, skipping hidden folders and files: a .txt
file whose first line that says anything opens with jrnl's own stamp,
`[YYYY-MM-DD HH:MM]`. Each entry becomes one dated paragraph, the stamp's
brackets taken off so the kernel reads the date, the title on the date's
line and the body under it, blank lines inside an entry closed up so the
entry stays one passage:

    2024-03-03 10:15  Fixed the gate.
    The hinge wanted oil, not force.

    2024-03-04 09:00  Rain all day.

Entries keep their order in the file. A stamp with seconds is kept as
written; a .txt file that doesn't open with a stamp is someone else's and is
skipped, counted, never guessed at.

Each journal is written to MIRROR at the same relative path with `.txt`
added: `diary/journal.txt` becomes `MIRROR/diary/journal.txt.txt`. FOLDER is
only read. Originals are never modified and nothing is written inside it. A
file that cannot be read is skipped and counted, never a crash.

    wrote 1 files to MIRROR; skipped 0

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).

Point the kernel at MIRROR (`kernel.py init --pile MIRROR ...`) to ask
questions of your journal.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: jrnl.py mirror --from FOLDER --to MIRROR"
STAMP = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)\]\s*(.*)$")


def journal_text(raw: bytes) -> str | None:
    """The mirror text for a jrnl journal, or None when the first line that
    says anything wears no stamp (the file is someone else's)."""
    lines = raw.decode("utf-8-sig").splitlines()
    first = next((ln for ln in lines if ln.strip()), "")
    if not STAMP.match(first):
        return None
    out: list[list[str]] = []
    for line in lines:
        m = STAMP.match(line)
        if m:
            head = f"{m.group(1)}  {m.group(2)}".rstrip()
            out.append([head])
        elif out and line.strip():
            out[-1].append(line.rstrip())
    return "".join("\n".join(entry) + "\n\n" for entry in out)


def _sources(folder: Path) -> list[Path]:
    """The .txt files under `folder`, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if (
                not name.startswith(".")
                and name.lower().endswith(".txt")
                and p.is_file()
            ):
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
            text = journal_text(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except (OSError, UnicodeDecodeError):
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
