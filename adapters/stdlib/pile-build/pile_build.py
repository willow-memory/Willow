"""pile_build.py: the store built after each change, behind a lock, so your
next question finds it warm. Python 3.9+.

    python adapters/stdlib/pile-build/pile_build.py --from FOLDER --to STORE [--background]

pile-store builds a store when asked. This is what a hook or a timer calls
after a change, so that by the time a question comes the store is already
current:

- **one build at a time**: it takes a lock on the store's folder (the folder
  opened read-only, so the lock writes nothing). A second call waits for the
  first, then finds the store current and does nothing.
- **until it matches**: the folder can change while it is read. After each
  build it checks again, and builds again, up to `ROUNDS` times, so a change
  made mid-build is not left stale.
- **--background**: it starts itself detached and returns at once, saying
  the process it started; a hook doesn't wait for the build. The detached
  build is handed pipes its starter closes at once, and keeps what it would
  say to itself: no /dev/null is opened, and nothing holds the hook's
  output open. (`--detached` is how it starts itself; not for people.)

Without fcntl (Windows) there is no lock: two builds may both run, and each
still replaces the store whole, so no reader meets half of one.

It reads the folder and writes only `--to`, through pile-store; it writes no
box, reads no key, and reaches no network. Exit codes, the kernel's: 0 the
store is current, or a background build was started; 42 the folder has
nothing to read, or it still changed after `ROUNDS` builds; 2 refused.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None  # type: ignore[assignment]

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "pile-store"))
import kernel  # noqa: E402
import pile_store  # noqa: E402

ROUNDS = 3


def held(folder: Path) -> int | None:
    """A lock on `folder`, taken once it is free: its descriptor, or None
    where there is no flock. Said on stderr when it has to wait."""
    if fcntl is None:
        return None
    fd = os.open(folder, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("waiting: another build holds the lock", file=sys.stderr, flush=True)
        fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def ours(store: Path) -> bool:
    """Whether `store` is a pile store, by its own header alone."""
    db = pile_store.opened(store)
    if db is None:
        return False
    try:
        return pile_store.head(db) is not None
    finally:
        db.close()


def settle(folder: Path, store: Path) -> tuple[int, int | None, str | None]:
    """Build until the store matches: (builds made, passages in the last, why
    it is still stale after `ROUNDS`, or None)."""
    builds, n = 0, None
    while (why := pile_store.stale(store, folder)) is not None:
        if builds == ROUNDS:
            return builds, n, why
        n, _ = pile_store.build(folder, store)
        builds += 1
    return builds, n, None


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    it = iter(argv)
    for a in it:
        if a in ("--from", "--to"):
            opts[a] = next(it, "")
        elif a in ("--background", "--detached"):
            opts[a] = ""
        else:
            return usage()
    if (
        not opts.get("--from")
        or not opts.get("--to")
        or len({"--background", "--detached"} & set(opts)) > 1
    ):
        return usage()
    if "--detached" in opts:  # its starter has closed the pipes' other ends
        sys.stdout = sys.stderr = io.StringIO()
    folder, store = Path(opts["--from"]).resolve(), Path(opts["--to"]).resolve()
    if not folder.is_dir():
        print(f"refused: {opts['--from']} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if store.is_relative_to(folder):
        print("refused: the store can't live inside the folder it reads",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if not store.parent.is_dir():
        print(f"refused: {store.parent} is not a folder; make it first",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if store.exists() and not ours(store):
        print(f"refused: {opts['--to']} is there and is not a pile store; "
              "it is left as it is", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if "--background" in opts:
        child = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()),
             "--from", str(folder), "--to", opts["--to"],
             "--detached"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True,
        )  # fmt: skip
        for end in (child.stdin, child.stdout, child.stderr):
            end.close()
        print(f"started: building in the background, process {child.pid}")
        return kernel.ALIVE
    fd = held(store.parent)
    try:
        builds, n, why = settle(folder, store)
    finally:
        if fd is not None:
            os.close(fd)
    if why is not None:
        print(f"stale: the folder kept changing through {builds} builds ({why})")
        return kernel.ESCALATE
    if not builds:
        print(f"current: the store at {opts['--to']} already matches")
        return kernel.ALIVE
    print(f"built {n} passage{'' if n == 1 else 's'} to {opts['--to']}"
          f"{'' if builds == 1 else f' in {builds} builds'}")  # fmt: skip
    return kernel.ALIVE if n else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
