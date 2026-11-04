"""bot_venv.py: where your venvs are, and whether one has what CI needs. Python 3.9+.

    python adapters/stdlib/bot-venv/bot_venv.py [--bot] [--venv DIR ...] [--find DIR ...]
                                                [--needs NAME[==VERSION] ...]

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

`--find DIR` is the other half, willow-bot's own venv inventory: every venv
under DIR (a folder holding pyvenv.cfg, three levels down, and one behind a
symlink counted once under its real path, the link named), each with:

    /box/willow-bot/venvs/willow-bot
      inside the bot
      67 packages; lock: none
      runs: willow-bot.service, willow-bot-steward.service
      python 3.14.4

Inside means under the box's willow-bot/ folder, where the bot keeps its
venvs (its seal D2: all the venvs live in the bot); outside, anywhere else.
Packages are counted from site-packages' *.dist-info, nothing run. The lock
is the one the bot reads, <box>/willow-bot/locks/<name>.requirements.lock
(pip-compile's), the name a checkout's for its .venv: none, holds, or
drifted with what's missing, changed and extra. Without a box, inside and
lock aren't said. Runs names each service a process of runs from the
venv's bin/, read from /proc (its command line, and the unit its cgroup
names), so a child process counts for the service that started it; where
there's no /proc, it's unknown. A found venv's Python is read from its
pyvenv.cfg; asking it what it has takes `--needs`.

It only reads and prints: it writes nothing, runs CI for no one, moves or
deletes no venv, touches no box or key, and reaches no network. Exit codes, the kernel's: 0 some venv is
ready (with only `--find`: some venv found); 42 none is (none found); 2 refused (a bad command line, no box for `--bot`, or a
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


#: how deep under a --find folder a pyvenv.cfg is looked for, and what's skipped
DEPTH = 3
SKIP = frozenset(
    {".git", "node_modules", "__pycache__", ".ruff_cache", ".pytest_cache"}
)
#: a checkout's own venv folder, named for its checkout in the bot's locks
CHECKOUT = (".venv", "venv")
DIST = re.compile(r"(.+)-([^-]+)\.dist-info")
PIN = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*==\s*([^\s;\\#]+)")
#: put in by the venv itself, never pinned by pip-compile: not drift
TOOLING = frozenset({"pip", "setuptools", "wheel", "distribute"})


def norm(name: str) -> str:
    """A package's name as PEP 503 compares it: runs of -_. one -, lowercase."""
    return re.sub(r"[-_.]+", "-", name).lower()


def find(root: Path) -> list[Path]:
    """Every venv under `root`, DEPTH down, and one behind a symlinked folder."""
    found = []
    for here, dirs, files in os.walk(root):
        here = Path(here)
        if "pyvenv.cfg" in files:
            found.append(here)
            dirs[:] = []
            continue
        found += [here / d for d in sorted(dirs)
                  if (here / d).is_symlink() and (here / d / "pyvenv.cfg").is_file()]  # fmt: skip
        depth = len(here.relative_to(root).parts)
        dirs[:] = [] if depth >= DEPTH else sorted(d for d in dirs if d not in SKIP)
    return found


def packages(venv: Path) -> dict[str, str] | None:
    """What's installed, by site-packages' *.dist-info names, nothing run; or
    None when there's no site-packages to read."""
    sites = sorted(venv.glob("lib/python*/site-packages")) + sorted(
        venv.glob("Lib/site-packages")
    )
    if not sites:
        return None
    out = {}
    for site in sites:
        for entry in sorted(site.iterdir()):
            if m := DIST.fullmatch(entry.name):
                out[norm(m[1])] = m[2]
    return out


def editable(venv: Path) -> set[str]:
    """The packages installed with -e, which a lock can't pin."""
    out = set()
    for direct in venv.glob("lib/python*/site-packages/*.dist-info/direct_url.json"):
        try:
            if (
                json.loads(direct.read_text(encoding="utf-8")).get("dir_info") or {}
            ).get("editable"):
                out.add(norm(DIST.fullmatch(direct.parent.name)[1]))
        except (OSError, ValueError, TypeError):
            continue
    return out


def lock(box: Path, venv: Path, have: dict[str, str] | None) -> str:
    """The bot's lock for the venv, read: none, holds, or what drifted."""
    name = venv.parent.name if venv.name in CHECKOUT else venv.name
    path = box / "willow-bot" / "locks" / f"{name}.requirements.lock"
    if not path.is_file():
        return "none"
    try:
        pins = {norm(m[1]): m[2] for line in path.read_text(encoding="utf-8").splitlines()
                if (m := PIN.match(line))}  # fmt: skip
    except (OSError, UnicodeDecodeError):
        return "unreadable"
    if not pins:
        return "pins nothing"
    if have is None:
        return "can't be held: no site-packages to read"
    skip = editable(venv) | TOOLING
    missing = sorted(n for n in pins if n not in have)
    changed = sorted(n for n in pins if n in have and have[n] != pins[n])
    extra = sorted(n for n in have if n not in pins and n not in skip)
    if not (missing or changed or extra):
        return "holds"
    said = [f"{len(xs)} {what}" for what, xs in
            (("missing", missing), ("changed", changed), ("extra", extra)) if xs]  # fmt: skip
    return "drifted, " + ", ".join(said)


def services() -> dict[str, list[str]] | None:
    """Each venv a running process runs from (an argument under its bin/),
    real path to the services whose cgroup holds that process; None where
    there is no /proc to read."""
    proc = Path("/proc")
    if not (proc / "self" / "cmdline").is_file():
        return None
    out: dict[str, list[str]] = {}
    for pid in sorted(
        (d for d in proc.iterdir() if d.name.isdigit()), key=lambda d: int(d.name)
    ):
        try:
            args = (pid / "cmdline").read_bytes().split(b"\0")
            group = (pid / "cgroup").read_text()
        except OSError:
            continue
        # the unit itself, never the session manager (user@1000.service) that
        # every user unit and terminal sits under: a terminal's process is no service
        units = [part for part in group.strip().split("/")
                 if part.endswith(".service") and not part.startswith("user@")]  # fmt: skip
        if not units:
            continue
        for arg in args:
            path = Path(arg.decode(errors="replace"))
            if (
                path.parent.name == "bin"
                and (path.parent.parent / "pyvenv.cfg").is_file()
            ):
                seen = out.setdefault(str(path.parent.parent.resolve()), [])
                if units[-1] not in seen:
                    seen.append(units[-1])
                break
    return out


def where(venv: Path, box: Path | None, running: dict | None) -> list[str]:
    """The inventory's lines for one venv: inside or out, packages and lock,
    and what runs it."""
    have = packages(venv)
    real = venv.resolve()
    lines = []
    if box is not None:
        home = (box / "willow-bot").resolve()
        lines.append("inside the bot" if real == home or home in real.parents
                     else "outside the bot")  # fmt: skip
    count = "no site-packages" if have is None else f"{len(have)} packages"
    lines.append(
        count + (f"; lock: {lock(box, venv, have)}" if box is not None else "")
    )
    if running is None:
        lines.append("runs: unknown here (no /proc)")
    else:
        lines.append(
            "runs: "
            + (", ".join(sorted(running.get(str(real), []))) or "nothing running")
        )
    return lines


def cfg_python(venv: Path) -> str:
    """The Python a venv was made with, as its pyvenv.cfg says."""
    try:
        for line in (venv / "pyvenv.cfg").read_text(encoding="utf-8").splitlines():
            key, sep, val = line.partition("=")
            if sep and key.strip() in ("version_info", "version"):
                return val.strip()
    except OSError:
        pass
    return "not said in pyvenv.cfg"


def python_of(venv: Path) -> str | None:
    """The venv's Python, as a path relative to it, or None if it has none."""
    for rel in PYTHONS:
        if (venv / rel).is_file():
            return rel
    return None


def bot_box(environ) -> tuple[Path | None, str]:
    """The box by the bot's own rule (willow-bot `paths.env_box`): the first
    of BOX_ENV set and not blank, absolute and an existing folder; or None
    and why there is none."""
    for name in BOX_ENV:
        raw = environ.get(name, "").strip()
        if not raw:
            continue
        box = Path(raw).expanduser()
        if not box.is_absolute():
            return None, f"{name}={raw} is not an absolute path"
        if not box.is_dir():
            return None, f"{name}={box} is not an existing folder"
        return box, ""
    return None, f"no box: set {' or '.join(BOX_ENV)}, or name the venv with --venv"


def bot_venv(environ) -> tuple[Path | None, str]:
    """The bot's venv by the bot's own rule (`_bot_venv` in its one script),
    or None and why there is no box."""
    box, why = bot_box(environ)
    if box is None:
        return None, why
    new = box / "willow-bot" / "venvs" / "willow-bot"
    old = box / "venvs" / "willow-bot"
    return (old if not new.is_dir() and old.is_dir() else new), ""


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


def readiness(v: str, needs: list[tuple[str, str | None]]) -> tuple[list[str], bool]:
    """What one venv's own Python says it has, as lines, and whether it is
    ready: a folder with no Python, a Python that didn't answer, and one
    that answered without what's needed are each said apart."""
    rel = python_of(Path(v))
    if rel is None:
        return [f"no Python in it ({' or '.join(PYTHONS)})"], False
    answer = ask(Path(v) / rel, [name for name, _ in needs])
    if answer is None:
        return [f"its Python ({rel}) didn't answer"], False
    lines, ok = verdict(answer, needs)
    if ok:
        return lines + [
            f"ready: {v.rstrip('/')}/{rel} adapters/stdlib/ci/ci.py run --box BOX"
        ], True
    return lines + ["not ready"], False


def main(argv: list[str]) -> int:
    venvs: list[str | None] = []  # None: the bot's, found by its rule
    roots: list[str] = []
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
        elif a == "--find":
            r = next(it, "")
            bad = bad or not r
            roots.append(r)
        elif a == "--needs":
            m = NEED.fullmatch(next(it, ""))
            bad = bad or m is None
            if m:
                needs.append((m.group(1), m.group(2)))
        else:
            bad = True
    if bad or not (venvs or roots):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    for r in roots:
        if not Path(r).is_dir():
            print(f"refused: {r} is not a folder", file=sys.stderr)
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
    asked = bool(needs)
    named = {name for name, _ in needs}
    needs = [(name, None) for name in NEEDS if name not in named] + needs
    box, _ = bot_box(os.environ)
    running = services()
    seen: dict[str, list[str]] = {}  # real path: each path it was found by
    for v in venvs:
        seen.setdefault(str(Path(v).resolve()), []).append(v)
    found: dict[str, list[str]] = {}
    for r in roots:
        for v in find(Path(r)):
            key = str(v.resolve())
            if key not in seen:
                found.setdefault(key, [])
                if str(v) not in found[key]:
                    found[key].append(str(v))
    inside = run_by = 0
    for key, paths in found.items():  # under its real path; a link is named
        print(key)
        for alias in sorted(p for p in paths if p != key):
            print(f"  also {alias}")
        lines = where(Path(key), box, running)
        inside += lines[0] == "inside the bot"
        run_by += bool(running and running.get(key))
        lines += (
            readiness(key, needs)[0] if asked else [f"python {cfg_python(Path(key))}"]
        )
        for line in lines:
            print(f"  {line}")
    if roots:
        print(f"found {len(found)} venv{'s' * (len(found) != 1)} under {', '.join(roots)}"
              + (f": {inside} inside the bot, {len(found) - inside} outside" if box else "")
              + (f"; {run_by} run by a service" if running is not None else ""))  # fmt: skip
    if not venvs:
        return kernel.ALIVE if found else kernel.ESCALATE
    ready = 0
    for v in venvs:
        print(v)
        lines, ok = readiness(v, needs)
        for line in where(Path(v), box, running) + lines:
            print(f"  {line}")
        ready += ok
    print(f"{ready} of {len(venvs)} ready")
    return kernel.ALIVE if ready else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
