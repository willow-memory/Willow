"""alone.py: each add-on's tests, in a copy holding only what its card says
it uses. Python 3.9+.

    python adapters/stdlib/ci/alone.py [NAME ...] [--jobs N]

An add-on is a folder anyone can copy beside the kernel. This holds it to
that: for each add-on in adapters/stdlib, a scratch copy gets kernel.py, the
law (CONSTITUTION.md) and the kernel's vectors (vectors/cases.json), the
add-on, and every add-on its card `uses`, and theirs, and nothing else.
Its own tests then run there. One that fails reached something its card
doesn't name, or assumed an add-on it only `looks-for`.

Left out: an add-on with no tests, and one whose card says `runs-in: repo`
(it works on willow's own repository, and isn't copied out). The deps
add-ons have gates of their own, with their installs.

It writes only its scratch copies, made with tempfile and removed. What it
prints is the same for the same repo: each add-on that failed, with pytest's
summary line. Exit codes, the kernel's: 0 every one held; 2 one didn't; 42
pytest isn't here.
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STDLIB = ROOT / "adapters" / "stdlib"
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "alone_readme", STDLIB / "readme" / "readme.py"
)
readme = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(readme)

#: beside kernel.py in every copy: the kernel's own, not an add-on's
KERNEL_FILES = ("kernel.py", "CONSTITUTION.md", "vectors/cases.json")
#: pytest's own timing, which differs run to run, kept out of what is printed
TIMING = re.compile(r" in [0-9.]+s(?: \([0-9:]+\))?")


def cards() -> dict[str, dict]:
    return {a["name"]: a for a in readme.addons() if a["built"]}


def needed(name: str, every: dict[str, dict]) -> list[str]:
    """The add-on and everything its card uses, and theirs, in order."""
    seen, todo = [], [name]
    while todo:
        n = todo.pop(0)
        if n in seen:
            continue
        seen.append(n)
        todo += readme.split_tags(every[n].get("uses", ""))
    return seen


def held(name: str, every: dict[str, dict]) -> tuple[str, str]:
    """(name, "" when its tests held alone, else pytest's summary line)."""
    with tempfile.TemporaryDirectory(prefix=f"willow-alone-{name}-") as tmp:
        here = Path(tmp)
        for f in KERNEL_FILES:
            (here / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / f, here / f)
        for n in needed(name, every):
            kind = every[n]["kind"]
            shutil.copytree(ROOT / "adapters" / kind / n, here / "adapters" / kind / n,
                            ignore=shutil.ignore_patterns("__pycache__"))  # fmt: skip
        got = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             str(here / "adapters" / "stdlib" / name)],
            cwd=here, capture_output=True, text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )  # fmt: skip
    if got.returncode == 0:
        return name, ""
    tail = (got.stdout.strip().splitlines() or [got.stderr.strip()[:200]])[-1]
    return name, TIMING.sub("", tail.replace(tmp, "<copy>"))


def main(argv: list[str]) -> int:
    jobs, names, it = os.cpu_count() or 2, [], iter(argv)
    for a in it:
        if a == "--jobs":
            got = next(it, "")
            if not got.isdigit() or int(got) < 1:
                print(__doc__.split("\n\n")[1], file=sys.stderr)
                return kernel.REFUSED
            jobs = int(got)
        elif a.startswith("-"):
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return kernel.REFUSED
        else:
            names.append(a)
    if importlib.util.find_spec("pytest") is None:
        print("unreachable: pytest isn't installed for this Python")
        return kernel.ESCALATE
    try:
        every = cards()
    except readme.Refused as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    unknown = [n for n in names if n not in every or every[n]["kind"] != "stdlib"]
    if unknown:
        print(
            f"refused: no add-on in adapters/stdlib named {unknown[0]!r}",
            file=sys.stderr,
        )
        return kernel.REFUSED
    todo = [
        n for n in (names or sorted(every))
        if every[n]["kind"] == "stdlib" and every[n].get("runs-in") != "repo"
        and any((STDLIB / n).glob("test_*.py"))
    ]  # fmt: skip
    with ThreadPoolExecutor(jobs) as pool:
        failed = [
            (n, why) for n, why in pool.map(lambda n: held(n, every), todo) if why
        ]
    for n, why in failed:
        print(f"{n}: {why}")
    print(f"{len(todo) - len(failed)} of {len(todo)} add-ons' tests held alone")
    return kernel.REFUSED if failed else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
