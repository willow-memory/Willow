"""ci.py: this repo's checks as verdict rows on a kernel record. Python 3.9+.

    python adapters/stdlib/ci/ci.py run    [PART ...] [--box DIR] [--now TS]
    python adapters/stdlib/ci/ci.py verify [--box DIR]
    python adapters/stdlib/ci/ci.py show   [--box DIR]

PART is lint, tests, ports, demo or deps; none means all five. --box defaults to
.ci-record (ignored by git), and its key to the same name plus `.key`, beside
it, never in it.

Each gate runs one fixed command and is written as one `verdict` row, through
the kernel's own `append`, so the record is a kernel record and the kernel's
`verify` checks its chain. A row says:

    gate          which check, in a fixed order (GATES below)
    state         satisfied, failing or unreachable, never collapsed: a tool
                  that isn't installed is unreachable, not failing, and
                  neither is a pass
    files_sha256  every file of the repo it ran on, hashed together
    said_sha256   what the command printed, less durations and this
                  machine's paths
    python        the major.minor it ran under
    why           for a gate that didn't pass: the reason, in one line

A verdict is code's record of what happened, never a seal: its kind is always
`verdict`, it is written as `ci`, and nothing here writes a `seal` row. CI's
verdicts are draft. The merge is the person saying the tree is good enough.

It is deterministic. The time on every row is the commit's (`--now` sets it),
and nothing the commands print that changes from run to run (how long they
took) reaches a row, so the same files run the same way give the same record,
byte for byte. `test_ci.py` holds it to that.

Exit codes, the kernel's: 0 every gate satisfied; 42 a gate unreachable and
none failing; 2 a gate failing, or a record that doesn't verify.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

SATISFIED, FAILING, UNREACHABLE = "satisfied", "failing", "unreachable"
WHO = "ci"
PORTS = ("java", "ts", "csharp")
TOOLS = {"java": ("javac", "java"), "ts": ("node", "npm", "npx"), "csharp": ("dotnet",)}
PY = sys.executable
PYTEST = (PY, "-m", "pytest", "-q", "-p", "no:cacheprovider")
#: what changes between two runs of the same command on the same files
TIMING = re.compile(r"\b\d+(?:\.\d+)?\s*(?:s|ms|sec|seconds)\b")


TEMP = os.path.realpath(tempfile.gettempdir())


def steady(said: str) -> str:
    """What a command printed, less what changes from run to run: how long it
    took, where the repo sits on this machine, and the temporary folders a
    run makes (pytest numbers its own: pytest-412, pytest-413), and where
    this Python lives, which a throwaway environment changes every run."""
    said = said.replace(str(ROOT), "<repo>").replace(sys.prefix, "<python>")
    said = said.replace(TEMP, "<tmp>")
    return re.sub(r"pytest-\d+", "pytest-N", TIMING.sub("", said))


# ── gates ────────────────────────────────────────────────────────────────────
def run(argv: tuple, cwd: Path = ROOT, env: dict | None = None) -> tuple[int, str]:
    got = subprocess.run(
        argv, cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )  # fmt: skip
    print(got.stdout, end="", flush=True)
    return got.returncode, got.stdout


def missing_module(name: str) -> str | None:
    found = subprocess.run([PY, "-c", f"import {name}"], capture_output=True)
    return None if found.returncode == 0 else f"{name} is not installed"


def missing_tools(*names: str) -> str | None:
    gone = [n for n in names if shutil.which(n) is None]
    return f"{', '.join(gone)} not on PATH" if gone else None


def command(*argv: str, needs=None, judge=None):
    """A gate that runs one command: unreachable when `needs` says why,
    failing on a non-zero exit or when `judge` says why."""

    def gate() -> tuple[str, str, str | None]:
        why = needs() if needs else None
        if why:
            return UNREACHABLE, "", why
        code, said = run(argv)
        if code != 0:
            return FAILING, said, f"exit {code}"
        why = judge(said) if judge else None
        return (FAILING, said, why) if why else (SATISFIED, said, None)

    return gate


GUARD = Path(__file__).resolve().parent / "guard"


def guarded(log: Path) -> dict:
    """The environment the add-on tests run in: the guard (guard/
    sitecustomize.py) loaded into every process they start, its breaches
    written to `log`, and no bytecode written, which is the import system's
    doing and not the add-on's."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (str(GUARD), env.get("PYTHONPATH", "")) if p
    )
    env["WILLOW_GUARD_LOG"] = str(log)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def breaches(log: Path) -> str | None:
    """The guard's log, one line per distinct breach, or None when clean. A
    breach the add-on caught and swallowed is on it all the same."""
    if not log.is_file():
        return None
    lines = sorted(
        {steady(line) for line in log.read_text(encoding="utf-8").splitlines()}
    )
    return "; ".join(lines)[:400] if lines else None


def guarded_tests(*target: str):
    """pytest over `target` under the guard: failing on a failed test, or on
    any breach of a card's promises."""

    def gate() -> tuple[str, str, str | None]:
        why = missing_module("pytest")
        if why:
            return UNREACHABLE, "", why
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "guard.log"
            code, said = run((*PYTEST, *target), env=guarded(log))
            broke = breaches(log)
        if broke:  # first: a breach is why the tests failed, if they did
            return FAILING, said, f"broke its card's promises: {broke}"
        if code != 0:
            return FAILING, said, f"exit {code}"
        return SATISFIED, said, None

    return gate


def port_ran(port: str):
    """compare.py skips a port it can't build and still exits 0: here that
    port's own session line must be there, every check ok."""

    def judge(said: str) -> str | None:
        if not re.search(rf"^  {port} +(\d+)/\1 session checks ok$", said, re.M):
            return f"{port}: no full session line"
        if not re.search(r"^unexplained differences: 0$", said, re.M):
            return "unexplained differences"
        return None

    return judge


def demo(name: str):
    """Make the person's files in a temporary copy, then hold them to PLANTED."""

    def gate() -> tuple[str, str, str | None]:
        with tempfile.TemporaryDirectory() as tmp:
            here = Path(tmp) / name
            shutil.copytree(ROOT / "demo" / name, here)
            make = str(here / "make_life.py")
            code, made = run((PY, make), cwd=here)
            if code != 0:
                return FAILING, made.replace(tmp, "<tmp>"), f"make_life.py: exit {code}"
            code, said = run((PY, make, "--check"), cwd=here)
            said = (made + said).replace(tmp, "<tmp>")  # a new folder every run
            if code != 0:
                return FAILING, said, f"make_life.py --check: exit {code}"
            return SATISFIED, said, None

    return gate


def deps_add_on(name: str, pins: str = "requirements.txt"):
    """A deps add-on's tests in a fresh virtual environment of its own, with
    `pins` and pytest installed there, so one add-on's packages never decide
    whether another's tests pass. Run once at its pins and once at its floor
    (requirements-floor.txt). An install that can't be done (no network, a
    pin that won't resolve) is unreachable, not a pass; only the tests' own
    output is hashed, never the installer's."""

    def gate() -> tuple[str, str, str | None]:
        here = ROOT / "adapters" / "deps" / name
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / "env"
            got = subprocess.run(
                [PY, "-m", "venv", str(env)], capture_output=True, text=True
            )
            if got.returncode != 0:
                return UNREACHABLE, "", "couldn't make a virtual environment"
            py = str(env / ("Scripts" if os.name == "nt" else "bin") / "python")
            got = subprocess.run(
                [py, "-m", "pip", "install", "-q", "--disable-pip-version-check",
                 "-r", str(here / pins), "pytest"],
                capture_output=True, text=True,
            )  # fmt: skip
            if got.returncode != 0:
                tail = (got.stderr or got.stdout).strip().splitlines()[-1:] or [""]
                return (
                    UNREACHABLE,
                    "",
                    f"couldn't install its requirements: {tail[0][:120]}",
                )
            log = Path(tmp) / "guard.log"
            code, said = run(
                (py, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(here)),
                env=guarded(log),
            )
            said = said.replace(tmp, "<tmp>")
            broke = breaches(log)
            if broke:
                return FAILING, said, f"broke its card's promises: {broke}"
            if code != 0:
                return FAILING, said, f"exit {code}"
            return SATISFIED, said, None

    return gate


#: the floor rule: a dependency is also tested at its last release on or
#: before this day, or at its first release if it had none by then
FLOOR_DAY = "2021-01-01"
PYPI = "https://pypi.org/pypi/{}/json"


def pins_of(path: Path) -> dict[str, str]:
    """{package: version} from a file of `name==version` lines."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            name, version = line.split("==")
            out[name.strip().lower()] = version.strip()
    return out


def releases(package: str) -> dict[str, str]:
    """{version: first upload time} for each release with a file not yanked."""
    import json
    import urllib.request

    with urllib.request.urlopen(PYPI.format(package), timeout=30) as got:
        doc = json.load(got)
    out = {}
    for version, files in doc["releases"].items():
        times = [f["upload_time_iso_8601"] for f in files if not f.get("yanked")]
        if times:
            out[version] = min(times)
    return out


def rule_floor(uploaded: dict[str, str]) -> str:
    """The version the floor rule names, by upload time, not version order."""
    by_time = sorted(uploaded, key=uploaded.get)
    before = [v for v in by_time if uploaded[v] < FLOOR_DAY]
    return before[-1] if before else by_time[0]


def floor_line(name: str) -> str:
    card = (ROOT / "adapters" / "deps" / name / "README.md").read_text(encoding="utf-8")
    got = re.search(r"^floor: (.*)$", card.split("-->")[0], re.M)
    return got.group(1).strip() if got else ""


def floors() -> tuple[str, str, str | None]:
    """Each deps add-on's floor against the rule, from PyPI's upload dates: a
    floor at the rule's version passes; one above it passes only when its
    card's `floor:` line says why; one below it is fine (older than asked).
    PyPI out of reach is unreachable."""
    said, wrong = [], []
    for name in deps_add_ons():
        here = ROOT / "adapters" / "deps" / name
        for package, version in sorted(
            pins_of(here / "requirements-floor.txt").items()
        ):
            try:
                uploaded = releases(package)
            except (OSError, ValueError) as exc:
                return UNREACHABLE, "", f"couldn't read PyPI for {package}: {exc}"[:200]
            rule = rule_floor(uploaded)
            if version not in uploaded:
                wrong.append(f"{name}: {package}=={version} is not on PyPI")
                continue
            line = f"{name}: {package} floor {version}, rule {rule}"
            if uploaded[version] > uploaded[rule]:
                reason = floor_line(name).replace(f"{package} {version}", "")
                if len(reason.strip(" ;,.:")) < 20:
                    wrong.append(f"{name}: {package} {version} is above the rule's "
                                 f"{rule} and its card's floor: line gives no reason")  # fmt: skip
                    continue
                line += ", raised with a reason"
            said.append(line)
    said = "\n".join(said) + "\n"
    print(said, end="")
    if wrong:
        return FAILING, said, "; ".join(wrong)
    return SATISFIED, said, None


def deps_add_ons() -> list[str]:
    return sorted(
        p.name
        for p in (ROOT / "adapters" / "deps").glob("*")
        if p.is_dir() and not p.name.startswith(("_", "."))
    )


def people() -> list[str]:
    return sorted(p.parent.name for p in (ROOT / "demo").glob("*/make_life.py"))


def gates() -> list[tuple[str, str, object]]:
    """(part, gate, how), in the one fixed order."""
    out = [
        ("lint", "lint:check", command(PY, "-m", "ruff", "check", ".",
                                       needs=lambda: missing_module("ruff"))),
        ("lint", "lint:format", command(PY, "-m", "ruff", "format", "--check", ".",
                                        needs=lambda: missing_module("ruff"))),
        ("tests", "tests:beats", command(PY, "kernel.py", "test")),
    ]  # fmt: skip
    for gate, *target in (
        ("kernel", "test_kernel.py"),
        ("docs", "test_docs.py"),
        ("adapters", "adapters/stdlib"),
        ("vectors", "vectors/test_vectors.py", "-k", "as_it_is_now"),
    ):
        how = command(*PYTEST, *target, needs=lambda: missing_module("pytest"))
        if gate == "adapters":
            how = guarded_tests(*target)
        out.append(("tests", f"tests:{gate}", how))
    for port in PORTS:
        how = command(
            PY, "vectors/compare.py", "--port", port,
            needs=lambda p=port: missing_tools(*TOOLS[p]), judge=port_ran(port),
        )  # fmt: skip
        out.append(("ports", f"ports:{port}", how))
    out += [("demo", f"demo:{name}", demo(name)) for name in people()]
    for name in deps_add_ons():
        out.append(("deps", f"deps:{name}", deps_add_on(name)))
        out.append(("deps", f"deps:{name}@floor",
                    deps_add_on(name, "requirements-floor.txt")))  # fmt: skip
    out.append(("deps", "deps:floors", floors))
    return out


PARTS = ("lint", "tests", "ports", "demo", "deps")


# ── the record ───────────────────────────────────────────────────────────────
def files_sha256() -> str:
    """Every file git tracks or would track, path and bytes, hashed together:
    the tree as it is on disk, edits included."""
    names = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")
    h = hashlib.sha256()
    for name in sorted(n for n in names if n and (ROOT / n.decode()).is_file()):
        h.update(
            name + b"\0" + hashlib.sha256((ROOT / name.decode()).read_bytes()).digest()
        )
    return h.hexdigest()


def commit_time() -> str:
    got = subprocess.run(
        ["git", "log", "-1", "--format=%ct"], cwd=ROOT, capture_output=True, text=True
    )
    if got.returncode != 0 or not got.stdout.strip():
        raise SystemExit("refused: no commit to take the time from; pass --now")
    t = datetime.fromtimestamp(int(got.stdout), timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def quiet(fn, *a):
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        return fn(*a)


def counted(path: Path) -> bool:
    """Whether `path` sits in the repo where git would track it, and so in
    `files_sha256` and in the README's tree."""
    path = path.resolve()
    if not path.is_relative_to(ROOT):
        return False
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(path)], cwd=ROOT, capture_output=True
    )
    return ignored.returncode != 0


def open_box(box: Path, ts: str) -> None:
    """A kernel box whose pile is this repo. Its key is made beside it; no
    seal is ever written with it. Neither may sit where git would count it:
    the record would be hashed into the files it records, and change them."""
    key = box.parent / (box.name + ".key")
    for path in (box, key):
        if counted(path):
            raise SystemExit(
                f"refused: {path} is in the repo and not ignored by git;"
                " put the record outside the repo, or under .ci-record"
            )
    if (box / "record.jsonl").exists():
        return
    if quiet(kernel.init, box, ROOT, key, ts) != kernel.ALIVE:
        raise SystemExit(f"refused: couldn't start a record at {box}")


def do_run(box: Path, parts: list[str], ts: str) -> int:
    open_box(box, ts)
    files = files_sha256()
    python = "{}.{}".format(*sys.version_info[:2])
    states = []
    for part, gate, how in gates():
        if part not in parts:
            continue
        print(f"\n── {gate}", flush=True)
        state, said, why = how()
        row = {
            "gate": gate,
            "state": state,
            "files_sha256": files,
            "said_sha256": kernel.h256(steady(said)),
            "python": python,
        }
        if why:
            row["why"] = why
        kernel.append(box, ts, "verdict", who=WHO, **row)
        states.append((gate, state, why))
    print()
    for gate, state, why in states:
        print(f"{gate:<18} {state}" + (f"  ({why})" if why else ""))
    return code_of([s for _, s, _ in states])


def code_of(states: list[str]) -> int:
    if FAILING in states:
        return kernel.REFUSED
    return kernel.ESCALATE if UNREACHABLE in states or not states else kernel.ALIVE


#: what every verdict row carries, and what none may carry (a seal reader's)
VERDICT = {"gate", "state", "files_sha256", "said_sha256", "python"}
NEVER = {"proof", "subject"}


def do_verify(box: Path) -> int:
    """The kernel's verify, then: every row after the first is a well-formed
    verdict written as ci, and none is or looks like a seal."""
    code = kernel.verify(box)
    if code == kernel.REFUSED:
        return code
    rows, _ = kernel.read(box / "record.jsonl")
    bad = []
    for r in rows[1:]:
        if r["kind"] != "verdict" or r["who"] != WHO or r["standing"] != "unattested":
            bad.append(f"row {r['n']}: not a ci verdict")
        elif not VERDICT <= r.keys() or NEVER & r.keys():
            bad.append(f"row {r['n']}: not a verdict's fields")
        elif r["state"] not in (SATISFIED, FAILING, UNREACHABLE):
            bad.append(f"row {r['n']}: state {r['state']!r}")
    for b in bad:
        print(b)
    return kernel.REFUSED if bad else code


def do_show(box: Path) -> int:
    """Each gate's latest verdict."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ")
        return kernel.REFUSED
    latest = {r["gate"]: r for r in rows if r["kind"] == "verdict"}
    for gate, r in latest.items():
        print(f"{gate:<18} {r['state']:<12} python {r['python']}  row {r['n']}")
    return code_of([r["state"] for r in latest.values()])


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    opts, args, it = {}, [], iter(rest)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    box = Path(opts.get("--box") or ROOT / ".ci-record")
    if verb == "run" and all(a in PARTS for a in args):
        return do_run(box, args or list(PARTS), opts.get("--now") or commit_time())
    if verb == "verify" and not args:
        return do_verify(box)
    if verb == "show" and not args:
        return do_show(box)
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
