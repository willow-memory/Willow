"""git_history.py: commit messages and diffs as a dated pile. Python 3.9+.

    python adapters/stdlib/git-history/git_history.py \\
        mirror --from FOLDER --to MIRROR

Calls the git program (never linked) for each commit in FOLDER: its day,
its subject, its body, and its diff. Each commit is written to MIRROR as
<hash>.txt. Hidden folders are left to git; this add-on does not walk them.

    wrote 2 files to MIRROR; skipped 0

It only reads. A folder that is not a git history, or that has no commit,
is nothing there. Exit codes, the kernel's: 0 wrote some; 42 nothing there;
2 refused (no git program, FOLDER is not a folder, or MIRROR and FOLDER
are inside one another).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: git_history.py mirror --from FOLDER --to MIRROR"

GIT_ENV = {"LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0"}


def _git(folder: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, **GIT_ENV}
    return subprocess.run(
        [
            "git",
            "-C",
            str(folder),
            "-c",
            "i18n.logOutputEncoding=utf-8",
            "-c",
            "log.showSignature=false",
            "-c",
            "core.quotepath=false",
            *args,
        ],
        capture_output=True,
        text=True,
        env=env,
    )


def hashes_of(folder: Path) -> list[str] | None:
    """Commit hashes oldest first, or None if FOLDER is not a git history."""
    got = _git(folder, "rev-parse", "--is-inside-work-tree")
    if got.returncode != 0 or got.stdout.strip() != "true":
        return None
    got = _git(folder, "log", "--reverse", "--format=%H")
    if got.returncode != 0:
        return None
    return [h for h in got.stdout.splitlines() if h]


def commit_text(folder: Path, hexhash: str) -> str | None:
    got = _git(
        folder,
        "show",
        "--no-color",
        "--date=format:%Y-%m-%d",
        "--pretty=format:commit %H%ndate: %ad%nsubject: %s%n%n%b",
        hexhash,
        "--",
    )
    if got.returncode != 0:
        return None
    text = got.stdout.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
    return text


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    hashes = hashes_of(src)
    if hashes is None:
        return 0, 0
    wrote = skipped = 0
    for hexhash in hashes:
        text = commit_text(src, hexhash)
        if text is None:
            skipped += 1
            continue
        target = dst / f"{hexhash}.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if shutil.which("git") is None:
        print("refused: the git program is not installed", file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = Path(opts["--from"]).resolve(), Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
