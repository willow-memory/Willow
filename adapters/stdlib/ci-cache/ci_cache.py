"""ci_cache.py: a cache key per ecosystem, from a repo's lockfiles. Python 3.9+.

    python adapters/stdlib/ci-cache/ci_cache.py --from FOLDER

CI reinstalls the same packages on every run; those downloads can be cached and
keyed on the files that pin them, so a run with unchanged pins restores the
cache instead of fetching again. This reads FOLDER's lockfiles, groups them by
ecosystem -- pip, npm, .NET, Maven -- and prints, for each one it finds, the
directory to cache and a key that is the SHA-256 of those files: the key a CI
cache step keys on. The same lockfiles give the same key, so the cache holds
until a pin changes.

    pip    ~/.cache/pip        <key>  (3 files)
    npm    ~/.npm              <key>  (1 file)

It only reads FOLDER -- hidden folders and `node_modules` are not walked -- and
prints; it writes nothing, touches no box or key, and reaches no network. Exit
codes, the kernel's: 0 some ecosystem's lockfiles were found; 42 none were; 2
refused (a bad command line, or a `--from` that is not a folder).
"""

from __future__ import annotations

import fnmatch
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: (ecosystem, the directory a CI run caches, the lockfile names that key it).
ECOSYSTEMS = [
    ("pip", "~/.cache/pip", ("requirements*.txt", "Pipfile.lock", "poetry.lock")),
    ("npm", "~/.npm", ("package-lock.json", "yarn.lock", "pnpm-lock.yaml")),
    (".NET", "~/.nuget/packages", ("packages.lock.json",)),
    ("Maven", "~/.m2/repository", ("pom.xml",)),
]


def lockfiles(folder: Path) -> dict[str, list[Path]]:
    """Each ecosystem's lockfiles under FOLDER, by ecosystem. Hidden folders
    and node_modules are not walked, so a dependency's own lockfiles never key
    the cache."""
    found: dict[str, list[Path]] = {eco: [] for eco, _, _ in ECOSYSTEMS}
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [
            d for d in dirnames if not d.startswith(".") and d != "node_modules"
        ]
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            for eco, _, globs in ECOSYSTEMS:
                if any(fnmatch.fnmatch(name, g) for g in globs):
                    found[eco].append(Path(dirpath) / name)
                    break
    return found


def key_of(folder: Path, paths: list[Path]) -> str:
    """The cache key for an ecosystem: the SHA-256 over each lockfile's
    relative path and the SHA-256 of its bytes, sorted by path -- so the same
    pins give the same key on any machine, and a changed pin a new one."""
    rows = sorted(
        (
            p.relative_to(folder).as_posix(),
            kernel.h256(p.read_bytes().decode("latin-1")),
        )
        for p in paths
    )
    return kernel.h256(kernel.canon(rows))


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    it = iter(argv)
    for a in it:
        if a == "--from":
            opts["--from"] = next(it, "")
        else:
            opts["bad"] = a
    if opts.get("bad") or "--from" not in opts:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    folder = Path(opts["--from"])
    if not folder.is_dir():
        print(f"refused: {opts['--from']} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    found = lockfiles(folder)
    any_found = False
    for eco, cache_dir, _ in ECOSYSTEMS:
        paths = found[eco]
        if not paths:
            continue
        any_found = True
        n = len(paths)
        print(f"{eco:6} {cache_dir:20} {key_of(folder, paths)}  "
              f"({n} file{'' if n == 1 else 's'})")  # fmt: skip
    if not any_found:
        print("no lockfiles found; nothing to cache")
        return kernel.ESCALATE
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
