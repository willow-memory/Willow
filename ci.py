"""ci.py: every check this repo has, in one script. Python 3.9+, stdlib only.

    python ci.py            all four parts
    python ci.py lint       ruff check and ruff format --check
    python ci.py tests      kernel.py test, then pytest: the kernel, the docs,
                            the add-ons, and the vectors being current
    python ci.py ports      vectors/compare.py: every port against every case
                            and every other implementation's logs
    python ci.py demo       each demo person's files, made in a temporary
                            folder and held to their PLANTED.md

CI runs exactly this (.github/workflows/ci.yml), so a green run here means
what a green run there means.

A missing tool fails its part and says what to install; nothing is skipped.
A check that skips still exits 0, and a part that checked nothing must not
pass. The tools: ruff for lint, pytest for tests, a JDK, Node and npm, and
the .NET 8 SDK for ports.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORTS = ("java", "ts", "csharp")
TOOLS = {"java": ("javac", "java"), "ts": ("node", "npm", "npx"), "csharp": ("dotnet",)}


class Failed(Exception):
    pass


def step(what: str, *argv: str, cwd: Path = ROOT) -> str:
    """Run one command, show its output, and fail the part if it fails."""
    print(f"\n── {what}\n$ {' '.join(argv)}", flush=True)
    got = subprocess.run(
        argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    print(got.stdout, end="", flush=True)
    if got.returncode != 0:
        raise Failed(f"{what}: exit {got.returncode}")
    return got.stdout


def need_module(name: str, part: str) -> None:
    if subprocess.run([sys.executable, "-c", f"import {name}"]).returncode != 0:
        raise Failed(f"{part} needs {name}: pip install {name}")


def lint() -> None:
    need_module("ruff", "lint")
    step("lint", sys.executable, "-m", "ruff", "check", ".")
    step("format", sys.executable, "-m", "ruff", "format", "--check", ".")


def tests() -> None:
    need_module("pytest", "tests")
    step("the kernel's eight beats", sys.executable, "kernel.py", "test")
    step(
        "the kernel, the docs, the add-ons, the vectors",
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
        "test_kernel.py", "test_docs.py", "adapters", "vectors/test_vectors.py",
        "-k", "not every_port",
    )  # fmt: skip


def ports() -> None:
    missing = [t for p in PORTS for t in TOOLS[p] if shutil.which(t) is None]
    if missing:
        raise Failed(
            f"ports needs {', '.join(missing)}: a JDK, Node and the .NET 8 SDK"
        )
    out = step("every port", sys.executable, "vectors/compare.py")
    for port in PORTS:  # compare.py skips a port it can't build: that's a fail here
        if not re.search(rf"^  {port} +(\d+)/\1 session checks ok$", out, re.M):
            raise Failed(
                f"ports: {port} didn't run, or didn't pass every session check"
            )
    if not re.search(r"^unexplained differences: 0$", out, re.M):
        raise Failed("ports: unexplained differences")


def demo() -> None:
    people = sorted(p.parent.name for p in (ROOT / "demo").glob("*/make_life.py"))
    if not people:
        raise Failed("demo: no demo/*/make_life.py found")
    with tempfile.TemporaryDirectory() as tmp:
        for name in people:
            here = Path(tmp) / name
            shutil.copytree(ROOT / "demo" / name, here)
            make = str(here / "make_life.py")
            step(f"{name}: make the files", sys.executable, make, cwd=here)
            step(
                f"{name}: held to PLANTED.md", sys.executable, make, "--check", cwd=here
            )


PARTS = {"lint": lint, "tests": tests, "ports": ports, "demo": demo}


def main(argv: list[str]) -> int:
    wanted = argv or list(PARTS)
    unknown = [a for a in wanted if a not in PARTS]
    if unknown:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    failed: dict[str, str] = {}
    for name in wanted:  # every part runs, so one red part doesn't hide another
        try:
            PARTS[name]()
        except Failed as e:
            failed[name] = str(e)
    print()
    for name in wanted:
        print(f"{name:<6} " + (f"FAILED  {failed[name]}" if name in failed else "ok"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
