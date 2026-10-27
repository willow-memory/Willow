"""bot_venv.py: does willow-bot's venv have what CI needs? Python 3.9+.

    python adapters/stdlib/bot-venv/bot_venv.py [--bot] [--venv DIR ...] [--needs NAME[==VERSION] ...]

adapters/stdlib/ci/ci.py calls pytest and ruff through the Python that runs
it, so run with a Python that lacks them, every lint, tests and mutants row
comes back unreachable. willow-bot keeps its tools in a venv of its own, and
its one script runs CI's tools from there, never whatever is first on the
path. This asks the same venv, or any you name, which Python it holds and
which of the packages CI needs it has, and for one that has them all, prints
the line that runs CI with its Python:

    ~/venvs/willow
      python 3.14.4
      pytest 9.1.1
      ruff 0.16.7
      ready: ~/venvs/willow/bin/python adapters/stdlib/ci/ci.py run --box BOX

`--bot` finds the bot's venv by the bot's own rule: the box is
`$WILLOW_HOME`, else `$WILLOW_VAULT_BOX` (absolute, and an existing folder),
and the venv is `<box>/willow-bot/venvs/willow-bot`, or the old
`<box>/venvs/willow-bot` while only that one exists. With no box it refuses
and says so; it never guesses one. `--venv DIR` names any other venv.

It always asks for pytest and ruff. `--needs` asks for one more package, or
holds one to a version: `--needs ruff==0.16.7` holds ruff to the one CI
pins. Each venv's own Python
is asked, isolated (`-I`), so nothing in the folder you run it from is
imported. Three answers are kept apart: a folder with no Python in it, a
Python that didn't answer, and a Python that answered without what CI needs.

It only reads and prints: it writes nothing, runs CI for no one, touches no
box or key, and reaches no network. Exit codes, the kernel's: 0 some venv is
ready; 42 none is; 2 refused (a bad command line, no box for `--bot`, or a
venv that is not a folder).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: what adapters/stdlib/ci/ci.py imports through its Python
NEEDS = ("pytest", "ruff")
#: the oldest Python kernel.py and CI run on
OLDEST = (3, 9)
#: where a venv keeps its Python: POSIX, then Windows
PYTHONS = ("bin/python", "Scripts/python.exe")
#: where the box is named, first set wins: willow-bot's `paths.BOX_ENV`
BOX_ENV = ("WILLOW_HOME", "WILLOW_VAULT_BOX")
NEED = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)(?:==([A-Za-z0-9.+!-]+))?")
#: run by the venv's own Python: its version, and each package's, or null
ASK = """
import json, sys
from importlib import metadata
have = {}
for name in sys.argv[1:]:
    try:
        have[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        have[name] = None
print(json.dumps({"python": list(sys.version_info[:3]), "have": have}))
"""


def python_of(venv: Path) -> str | None:
    """The venv's Python, as a path relative to it, or None if it has none."""
    for rel in PYTHONS:
        if (venv / rel).is_file():
            return rel
    return None


def bot_venv(environ) -> tuple[Path | None, str]:
    """The bot's venv by the bot's own rule (willow-bot `paths.env_box`, and
    `_bot_venv` in its one script), or None and why there is no box."""
    for name in BOX_ENV:
        raw = environ.get(name, "").strip()
        if not raw:
            continue
        box = Path(raw).expanduser()
        if not box.is_absolute():
            return None, f"{name}={raw} is not an absolute path"
        if not box.is_dir():
            return None, f"{name}={box} is not an existing folder"
        new = box / "willow-bot" / "venvs" / "willow-bot"
        old = box / "venvs" / "willow-bot"
        return (old if not new.is_dir() and old.is_dir() else new), ""
    return None, f"no box: set {' or '.join(BOX_ENV)}, or name the venv with --venv"


def ask(python: Path, names: list[str]) -> dict | None:
    """What the Python says it is and has, or None if it didn't answer."""
    try:
        got = subprocess.run([str(python), "-I", "-c", ASK, *names],
                             capture_output=True, text=True)  # fmt: skip
    except OSError:
        return None
    if got.returncode != 0:
        return None
    try:
        return json.loads(got.stdout)
    except ValueError:
        return None


def verdict(
    answer: dict, needs: list[tuple[str, str | None]]
) -> tuple[list[str], bool]:
    """The lines said about one venv's answer, and whether it is ready."""
    version = tuple(answer["python"])
    lines = [f"python {'.'.join(map(str, version))}"]
    ok = version >= OLDEST
    if not ok:
        lines[0] += f", older than {'.'.join(map(str, OLDEST))}"
    for name, wanted in needs:
        have = answer["have"].get(name)
        if have is None:
            lines.append(f"{name} not installed")
            ok = False
        elif wanted is not None and have != wanted:
            lines.append(f"{name} {have}, but {name}=={wanted} wanted")
            ok = False
        else:
            lines.append(f"{name} {have}")
    return lines, ok


def main(argv: list[str]) -> int:
    venvs: list[str | None] = []  # None: the bot's, found by its rule
    needs: list[tuple[str, str | None]] = []
    bad = False
    it = iter(argv)
    for a in it:
        if a == "--bot":
            venvs.append(None)
        elif a == "--venv":
            v = next(it, "")
            bad = bad or not v
            venvs.append(v)
        elif a == "--needs":
            m = NEED.fullmatch(next(it, ""))
            bad = bad or m is None
            if m:
                needs.append((m.group(1), m.group(2)))
        else:
            bad = True
    if bad or not venvs:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    for i, v in enumerate(venvs):
        if v is None:
            found, why = bot_venv(os.environ)
            if found is None:
                print(f"refused: willow-bot's venv: {why}", file=sys.stderr)
                return kernel.REFUSED
            venvs[i] = v = str(found)
        if not Path(v).is_dir():
            print(f"refused: {v} is not a folder", file=sys.stderr)
            return kernel.REFUSED
    named = {name for name, _ in needs}
    needs = [(name, None) for name in NEEDS if name not in named] + needs
    ready = 0
    for v in venvs:
        print(v)
        rel = python_of(Path(v))
        if rel is None:
            print(f"  no Python in it ({' or '.join(PYTHONS)})")
            continue
        answer = ask(Path(v) / rel, [name for name, _ in needs])
        if answer is None:
            print(f"  its Python ({rel}) didn't answer")
            continue
        lines, ok = verdict(answer, needs)
        for line in lines:
            print(f"  {line}")
        if ok:
            ready += 1
            print(
                f"  ready: {v.rstrip('/')}/{rel} adapters/stdlib/ci/ci.py run --box BOX"
            )
        else:
            print("  not ready")
    print(f"{ready} of {len(venvs)} ready")
    return kernel.ALIVE if ready else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
