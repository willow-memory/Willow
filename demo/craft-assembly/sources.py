"""sources.py: the study's sources, fetched by their pins and checked without git.

    python demo/craft-assembly/sources.py --to DIR            (online, with git)
    python demo/craft-assembly/sources.py --to DIR --check    (offline)

Each source in sources.json is fetched at its commit, shallow, into
DIR/sources/<name>. `--check` hashes each folder the way git hashes a tree
(leaving out its .git) and holds it to the pinned tree, so a copy made any
other way checks the same. Nothing of theirs is kept in this repo.

Exit codes: 0 every source holds; 42 one doesn't; 2 refused.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pieces  # noqa: E402

PINS = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]


def fetch(to: Path) -> None:
    for name, pin in PINS.items():
        d = to / "sources" / name
        if d.exists():
            continue
        tmp = d.with_name(name + ".part")
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        for argv in (["init", "-q"], ["fetch", "-q", "--depth", "1", pin["url"], pin["commit"]],
                     ["checkout", "-q", "FETCH_HEAD"]):  # fmt: skip
            subprocess.run(["git", "-C", str(tmp), *argv], check=True)
        tmp.rename(d)
        print(f"fetched {name}")


def check(to: Path) -> dict[str, bool]:
    return {name: (to / "sources" / name).is_dir() and pieces.tree(to / "sources" / name) == pin["tree"]
            for name, pin in PINS.items()}  # fmt: skip


def main(argv: list[str]) -> int:
    if (
        len(argv) not in (2, 3)
        or argv[0] != "--to"
        or (len(argv) == 3 and argv[2] != "--check")
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    to = Path(argv[1])
    if len(argv) == 2:
        if shutil.which("git") is None:
            print("refused: fetching needs the git program", file=sys.stderr)
            return 2
        fetch(to)
    held = check(to)
    for name, ok in held.items():
        print(f"{'holds' if ok else 'BROKEN'}  {name}")
    return 0 if all(held.values()) else 42


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
