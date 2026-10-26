"""parallel.py: run a reader over several folders at once, across cores. 3.9+.

    python adapters/stdlib/parallel/parallel.py --reader NAME \\
        --from FOLDER [--from FOLDER ...] --to MIRROR [--jobs auto|N]

A reader turns one folder of files into a mirror of plain-text passages
(`NAME mirror --from FOLDER --to MIRROR`). Reading a big collection is the slow
step, and a collection is usually many folders -- vaults, exports, inboxes.
This runs the reader on each folder at once, one worker per core, into
`MIRROR/<folder name>`, so the whole mirror builds in a fraction of the time.

Each folder is mirrored whole, by the reader itself, so the bytes are exactly
the reader's own -- a reader that looks across a folder (backlinks, say) still
sees all of it. The folders must have distinct names, since each is a
sub-mirror under `MIRROR`. `--jobs` is `auto` (one worker per core, the
default) or a positive number.

It runs the readers and sums what they wrote; it writes only under `--to`
(through the readers), reads no box or key, and reaches no network. The output
is the readers' own, so the same folders give the same bytes. Exit codes, the
kernel's: 0 some folder had something to read; 42 none did; 2 refused (a bad
command line, an unknown reader, a `--from` that is not a folder, two folders
with the same name, a folder and mirror that hold each other, or a reader that
refused).
"""

from __future__ import annotations

import concurrent.futures
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

WROTE = re.compile(r"wrote (\d+) files? to .+; skipped (\d+)")


def resolve(name: str) -> Path | None:
    """The one runnable script in the reader's folder (stdlib or deps), or None
    when the reader isn't here or its folder holds no single `__main__`
    script."""
    if "/" in name or not name:
        return None
    for base in (STDLIB, STDLIB.parent / "deps"):
        folder = base / name
        if not folder.is_dir():
            continue
        mains = [
            p
            for p in sorted(folder.glob("*.py"))
            if not p.name.startswith("test_")
            and "__main__" in p.read_text(encoding="utf-8")
        ]
        return mains[0] if len(mains) == 1 else None
    return None


def parse(argv: list[str]) -> dict | None:
    opts: dict = {"reader": "", "from": [], "to": "", "jobs": "auto"}
    it = iter(argv)
    for a in it:
        if a == "--reader":
            opts["reader"] = next(it, "")
        elif a == "--from":
            opts["from"].append(next(it, ""))
        elif a == "--to":
            opts["to"] = next(it, "")
        elif a == "--jobs":
            opts["jobs"] = next(it, "")
        else:
            return None
    if not opts["reader"] or not opts["to"] or not opts["from"] or "" in opts["from"]:
        return None
    if opts["jobs"] != "auto" and not (
        opts["jobs"].isdigit() and int(opts["jobs"]) > 0
    ):
        return None
    return opts


def run_one(script: Path, folder: Path, target: Path) -> tuple[Path, int, str, str]:
    got = subprocess.run(
        [
            sys.executable,
            str(script),
            "mirror",
            "--from",
            str(folder),
            "--to",
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    return folder, got.returncode, got.stdout, got.stderr


def main(argv: list[str]) -> int:
    opts = parse(argv)
    if opts is None:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    script = resolve(opts["reader"])
    if script is None:
        print(f"refused: no reader {opts['reader']} here", file=sys.stderr)
        return kernel.REFUSED
    froms = [Path(f).resolve() for f in opts["from"]]
    for f in froms:
        if not f.is_dir():
            print(f"refused: {f} is not a folder", file=sys.stderr)
            return kernel.REFUSED
    names = [f.name for f in froms]
    if len(set(names)) != len(names):
        print("refused: two folders share a name; each is a sub-mirror",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    to = Path(opts["to"]).resolve()
    for f in froms:
        if to.is_relative_to(f) or f.is_relative_to(to):
            print(f"refused: {f} and the mirror can't hold each other",
                  file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
    if not to.parent.is_dir():
        print(f"refused: {to.parent} is not a folder; make it first", file=sys.stderr)
        return kernel.REFUSED
    # parallel owns the mirror and each sub-mirror, so a reader only ever writes
    # under the --to it is given, never has to make that folder's parent
    to.mkdir(exist_ok=True)
    for f in froms:
        (to / f.name).mkdir(exist_ok=True)

    jobs = os.cpu_count() or 1 if opts["jobs"] == "auto" else int(opts["jobs"])
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(jobs, len(froms))
    ) as pool:
        results = sorted(
            pool.map(lambda f: run_one(script, f, to / f.name), froms),
            key=lambda r: str(r[0]),
        )

    wrote = skipped = 0
    for folder, code, out, err in results:
        if code == kernel.REFUSED:
            why = (err or out).strip().splitlines()[-1] if (err or out).strip() else "?"
            print(f"refused: {opts['reader']} on {folder}: {why}", file=sys.stderr)
            return kernel.REFUSED
        m = WROTE.search(out)
        if not m:
            print(f"refused: {opts['reader']} on {folder} did not report a mirror",
                  file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        wrote += int(m.group(1))
        skipped += int(m.group(2))

    print(f"wrote {wrote} file{'' if wrote == 1 else 's'} to {to}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
