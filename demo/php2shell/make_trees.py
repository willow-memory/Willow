"""PHP's source at the pinned releases, and the PHP2Shell fix commits' diffs.

    python demo/php2shell/make_trees.py --to DIR           # fetch, then check
    python demo/php2shell/make_trees.py --to DIR --check   # check only

Writes DIR/trees/<version>/ (each release's files, as `git archive` gives
them) and DIR/fixes/<branch>.diff (each security commit against its parent),
from https://github.com/php/php-src, and DIR/php-src, the clone it read them
from. Goes online, and needs the git program; this is not part of CI.

`--check` needs neither: it hashes each tree the way git hashes a tree (blob
and tree objects, SHA-1) and each diff by SHA-256, and holds them to
releases.json. A tree that doesn't match is named, and the exit is 2. Every
version releases.json lists is checked; one not fetched yet is "missing".

Exit codes, the kernel's: 0 everything there and matching; 42 something is
missing; 2 something doesn't match, or a bad command line.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / "releases.json").read_text(encoding="utf-8"))
#: the diff's exact form, so the same commit gives the same bytes on any git
DIFF = ["diff", "--no-color", "--no-ext-diff", "--no-renames", "--full-index", "-U3"]


def git_tree(folder: Path) -> str:
    """The git tree hash of `folder`'s files, the way `git write-tree` would
    give it for those files staged: modes 100644, 100755 and 120000, no empty
    folders, entries in git's order (a folder sorts as its name and a /)."""
    entries = []
    for p in folder.iterdir():
        st = p.lstat()
        if stat.S_ISLNK(st.st_mode):
            mode, sha = b"120000", obj(b"blob", os.readlink(p).encode())
        elif stat.S_ISDIR(st.st_mode):
            sub = git_tree(p)
            if sub == EMPTY:
                continue
            mode, sha = b"40000", sub
        else:
            mode = b"100755" if st.st_mode & stat.S_IXUSR else b"100644"
            sha = blob(p.read_bytes())
        key = p.name.encode() + (b"/" if mode == b"40000" else b"")
        entries.append(
            (key, mode + b" " + p.name.encode() + b"\0" + bytes.fromhex(sha))
        )
    return obj(b"tree", b"".join(e for _, e in sorted(entries)))


def obj(kind: bytes, body: bytes) -> str:
    return hashlib.sha1(
        kind + b" " + str(len(body)).encode() + b"\0" + body
    ).hexdigest()


IDENT = re.compile(rb"\$Id: ([0-9a-f]{40}) \$")


def blob(data: bytes) -> str:
    """A file's blob hash, as git stored it. `git archive` writes a file with
    the `ident` attribute (PHP gives six of them it) with `$Id$` filled in as
    `$Id: <its blob hash> $`; that is put back only when the hash written is
    the hash of the file put back, so other text that looks like it stays."""
    if IDENT.search(data):
        stored = IDENT.sub(rb"$Id$", data)
        sha = obj(b"blob", stored)
        if {m.group(1).decode() for m in IDENT.finditer(data)} == {sha}:
            return sha
    return obj(b"blob", data)


EMPTY = obj(b"tree", b"")


def git(*argv: str, cwd: Path | None = None) -> bytes:
    return subprocess.run(
        ["git", *argv], cwd=cwd, check=True, capture_output=True
    ).stdout


def fetch(to: Path) -> None:
    src = to / "php-src"
    if not (src / ".git").exists():
        git(
            "clone",
            "--quiet",
            "--filter=blob:none",
            "--no-checkout",
            PINS["source"],
            str(src),
        )
    tags = [f"refs/tags/php-{v}:refs/tags/php-{v}" for v in PINS["releases"]]
    git("fetch", "--quiet", "origin", *tags, cwd=src)
    for v, pin in PINS["releases"].items():
        tree = to / "trees" / v
        if tree.exists() and git_tree(tree) == pin["tree"]:
            continue
        got = git("rev-parse", f"php-{v}^{{commit}}", cwd=src).decode().strip()
        if got != pin["commit"]:
            raise SystemExit(
                f"refused: php-{v} is {got} now, not the pinned {pin['commit']}"
            )
        tree.mkdir(parents=True, exist_ok=True)
        archive = to / "trees" / f"{v}.tar"
        archive.write_bytes(git("archive", "--format=tar", pin["commit"], cwd=src))
        with tarfile.open(archive) as t:  # git's own archive of a pinned commit
            safe = {"filter": "tar"} if hasattr(tarfile, "tar_filter") else {}
            t.extractall(tree, **safe)
        archive.unlink()
    (to / "fixes").mkdir(exist_ok=True)
    for branch, fix in PINS["fixes"].items():
        diff = git(*DIFF, fix["parent"], fix["commit"], cwd=src)
        (to / "fixes" / f"{branch}.diff").write_bytes(diff)


def check(to: Path) -> int:
    """Each tree and diff against its pin: 0 all match, 42 some missing, 2 a mismatch."""
    bad = missing = 0
    for v, pin in PINS["releases"].items():
        tree = to / "trees" / v
        if not tree.is_dir():
            print(f"missing   {v}")
            missing += 1
        elif git_tree(tree) != pin["tree"]:
            print(f"DIFFERS   {v}: its files aren't php-{v}'s")
            bad += 1
        else:
            print(f"matches   {v}")
    for branch, fix in PINS["fixes"].items():
        d = to / "fixes" / f"{branch}.diff"
        if not d.is_file():
            print(f"missing   fix {branch}")
            missing += 1
        elif hashlib.sha256(d.read_bytes()).hexdigest() != fix["diff_sha256"]:
            print(f"DIFFERS   fix {branch}: not {fix['commit'][:10]}'s diff")
            bad += 1
        else:
            print(f"matches   fix {branch}")
    return 2 if bad else 42 if missing else 0


def main(argv: list[str]) -> int:
    if (
        len(argv) not in (2, 3)
        or argv[0] != "--to"
        or argv[2:] not in ([], ["--check"])
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    to = Path(argv[1])
    if not argv[2:]:
        to.mkdir(parents=True, exist_ok=True)
        fetch(to)
    return check(to)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
