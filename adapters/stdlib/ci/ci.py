"""ci.py: this repo's checks as verdict rows on a kernel record. Python 3.9+.

    python adapters/stdlib/ci/ci.py run    [PART|GATE ...] [--without GATE ...] [--shard K/N]
                                            [--box DIR] [--now TS]
    python adapters/stdlib/ci/ci.py verify [--box DIR]
    python adapters/stdlib/ci/ci.py show   [--box DIR]

PART is lint, tests, ports, demo, deps, mutants or tools; none means all seven.
A GATE (tests:strip) runs that one gate; --without leaves one out of what was
named; --shard K/N runs the Kth of N parts of it, so N jobs run it all between
them, each gate once. --box defaults to
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
verdicts are draft. The merge is the person saying the tree is good enough:
the witness is not the actor (CONSTITUTION.md, CONST-0-1).

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
import importlib.util
import io
import json
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
PORTS = ("java", "ts", "csharp", "go", "rust")
TOOLS = {
    "java": ("javac", "java"),
    "ts": ("node", "npm", "npx"),
    "csharp": ("dotnet",),
    "go": ("go",),
    "rust": ("cargo",),
}
PY = sys.executable
#: -rs: each skipped test's reason is printed, for `skipped` to read
PYTEST = (PY, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider")
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


#: pytest -rs's line for skipped tests: how many, and where and why
SKIPPED = re.compile(r"^SKIPPED \[(\d+)\] (.+)$", re.M)


def skipped(said: str) -> str | None:
    """How many tests a gate's pytest skipped, and why, from -rs's lines;
    None when it skipped none. A skip is no failure, and no pass of that
    test either: the gate's state stays what it was, and its row says this
    beside it, so a check that never ran is never mistaken for one that
    held. Only what pytest was asked to report: a gate that runs pytest
    inside another program (alone, mutants) says none."""
    got = SKIPPED.findall(steady(said))
    if not got:
        return None
    reasons = "; ".join(dict.fromkeys(why.strip() for _, why in got))
    return f"{sum(int(k) for k, _ in got)} skipped: {reasons}"[:300]


def verdict_line(gate: str, state: str, why: str | None, skips: str | None) -> str:
    """One gate's verdict as `run`, `show` and cores.py print it."""
    return (
        f"{gate:<18} {state}"
        + (f"  ({why})" if why else "")
        + (f"  [{skips}]" if skips else "")
    )


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


def command(*argv: str, needs=None, judge=None, env: dict | None = None):
    """A gate that runs one command: unreachable when `needs` says why,
    failing on a non-zero exit or when `judge` says why. `env` is added to
    the environment it runs in."""

    def gate() -> tuple[str, str, str | None]:
        why = needs() if needs else None
        if why:
            return UNREACHABLE, "", why
        code, said = run(argv, env={**os.environ, **env} if env else None)
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
                (py, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", str(here)),
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


def mutant_targets() -> list[str]:
    """The stdlib add-ons mutants.py breaks: every one but itself."""
    return sorted(
        p.name
        for p in (ROOT / "adapters" / "stdlib").iterdir()
        if p.is_dir() and not p.name.startswith(("_", ".")) and p.name != "mutants"
    )


SHARDS = ROOT / "adapters" / "stdlib" / "test-shards" / "shards.py"
#: one pytest over every add-on took eight minutes, and tests:strip ran it
#: again, so each is cut into gates a job runs a few of: tests:adapters-1 to
#: -8, tests:strip-1 to -4 (--shard then spreads them over jobs)
ADAPTER_CHUNKS = 8
STRIP_CHUNKS = 4


def load_shards():
    spec = importlib.util.spec_from_file_location("willow_shards_for_ci", SHARDS)
    shards = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shards)
    return shards


#: seconds each add-on test file took in one run, for cutting them by time.
#: Only the balance depends on it, never what runs: a file it doesn't list
#: counts as the median, one it lists that's gone is ignored. Made by
#: `pytest adapters/stdlib --junitxml=RUN.xml`, each testcase's time summed
#: under its file.
TIMES = Path(__file__).resolve().parent / "test-times.json"


def chunks(files: list[str], n: int, base: Path = ROOT) -> list[list[str]]:
    """`files` (paths under `base`) cut into n parts, each file in exactly
    one, by how long each took last time (TIMES), the cut test-shards makes,
    so the same files cut the same way everywhere."""
    times = json.loads(TIMES.read_text(encoding="utf-8"))
    known = sorted(times[f] for f in files if f in times)
    median = known[len(known) // 2] if known else 1.0
    return load_shards().split(
        {f: max(1, round(1000 * times.get(f, median))) for f in files}, n
    )


#: what a gate costs, in seconds on a CI runner, for the ones TIMES can't
#: price: from the last green main run (tests:alone ran with tests:adapters-1
#: in about 540 s, tests:docs with tests:adapters-5 in about 430). A gate it
#: doesn't list weighs DEFAULT_COST. Only the balance of the shards depends on
#: these, never which gate runs.
GATE_COST = {
    "tests:alone": 310,
    "tests:docs": 340,
    "tests:kernel": 30,
    "tests:beats": 20,
    "tests:ui": 60,
    "tests:vectors": 30,
    "tests:constitution": 30,
    "tests:coverage": 30,
    "lint:check": 10,
    "lint:format": 10,
}
DEFAULT_COST = 30
#: TIMES was taken on a busier box than a CI runner: about this much of a
#: second there is a second of a runner's
TIMES_TO_RUNNER = 0.5
#: a mutants gate copies the add-on, then runs its tests once per break, and
#: CI makes six breaks
MUTANT_BREAKS = 6
MUTANT_COPY = 10


def gate_weight(gate: str) -> int:
    """How long `gate` is expected to take, in whole seconds of at least one,
    for cutting gates into shards that end together. From committed data only
    (TIMES and GATE_COST), so the same gate weighs the same on every machine:
    tests:adapters-K is its chunk's test times; mutants:NAME is six runs of
    NAME's tests and a copy; a file TIMES doesn't list counts as the median,
    and a gate nothing prices as DEFAULT_COST."""
    times = json.loads(TIMES.read_text(encoding="utf-8"))
    known = sorted(times.values())
    median = known[len(known) // 2] if known else 1.0
    got = re.fullmatch(r"tests:adapters-(\d+)", gate)
    if got and 1 <= int(got.group(1)) <= ADAPTER_CHUNKS:
        part = chunks(adapter_tests(), ADAPTER_CHUNKS)[int(got.group(1)) - 1]
        seconds = TIMES_TO_RUNNER * sum(times.get(f, median) for f in part)
    elif gate.startswith("mutants:"):
        folder = f"adapters/stdlib/{gate[len('mutants:') :]}/"
        own = [t for f, t in times.items() if f.startswith(folder)]
        seconds = MUTANT_COPY + MUTANT_BREAKS * TIMES_TO_RUNNER * (sum(own) or median)
    else:
        seconds = GATE_COST.get(gate, DEFAULT_COST)
    return max(1, round(seconds))


def adapter_tests(base: Path = ROOT) -> list[str]:
    """Every add-on test file under `base`, as pytest collects them."""
    return sorted(
        p.relative_to(base).as_posix()
        for p in (base / "adapters" / "stdlib").rglob("test_*.py")
        if "__pycache__" not in p.parts
    )


LIVE = ROOT / "adapters" / "stdlib" / "live" / "live.py"


def live_check(name: str):
    """One of live.py's checks: its program run on the lines its add-on
    prints. A program that isn't installed is unreachable, never a pass."""

    def gate() -> tuple[str, str, str | None]:
        code, said = run((PY, str(LIVE), "run", name))
        said = re.sub(r"/[^ ]*/with space/", "<tmp>/", said)  # a new folder every run
        if code == kernel.ESCALATE:
            return UNREACHABLE, said, said.split(None, 3)[-1].strip()
        if code != kernel.ALIVE:
            return (
                FAILING,
                said,
                said.strip().split(None, 2)[-1][:300] or f"exit {code}",
            )
        return SATISFIED, said, None

    return gate


def live_checks() -> list[str]:
    """live.py's checks, by name, as `live.py list` prints them."""
    got = subprocess.run([PY, str(LIVE), "list"], capture_output=True, text=True)
    return [line.split()[0] for line in got.stdout.splitlines() if line.strip()]


#: (gate, pytest target, programs it needs) for each demo whose tests CI
#: runs, in the one fixed order. Every test file under demo/ is under one of
#: these targets: test_ci.py fails on one that isn't, since a test no gate
#: runs is a test that never fails.
DEMO_TESTS = (
    # PHP2Shell's runs fetch PHP's source; CI holds only what they froze
    ("demo:php2shell", "demo/php2shell", ()),
    # the Google privacy study fetched its sources once; CI holds what it froze
    ("demo:google-privacy-2026-10-16", "demo/google-privacy-2026-10-16", ()),
    # Bernadette's files through every layer: readers to the trust add-ons
    ("demo:stack", "demo/bernadette", ()),
    # the Johnson report passed between five people's willows, with share
    ("demo:share", "demo/johnson", ()),
    # Teodora's whole folder against the starter words list
    ("demo:teodora-words", "demo/teodora", ()),
    # the Craft apps taken apart and assembled: CI holds what was frozen, and
    # the tools on sources it makes, which git commits and Cargo builds
    ("demo:craft-assembly", "demo/craft-assembly", ("git", "cargo")),
    # a frozen recon composition over a planted target; its intel is committed
    ("demo:redteam", "demo/redteam", ()),
    # the fleet's own known gaps asked of the code their fixes changed; the
    # runs read the fleet's repositories, CI holds only what they froze
    ("demo:known-gaps", "demo/known-gaps", ()),
    # five repositories through the stacks: the stacks, the words list and the
    # records are committed; the runs read the repositories, CI holds the rest
    ("demo:five-repos", "demo/five-repos", ()),
    # the reusable novelty check every demo can run, over the idea pile and demos
    ("demo:novelty", "demo/test_novelty.py", ()),
    # Marisol's ofrenda: what was frozen is here, her folder made the same way
    ("demo:ofrenda-frozen", "demo/ofrenda", ()),
    # the Stewart crossover: its freeze, and the parts that need no network
    ("demo:stewart-crossover-frozen", "demo/stewart-crossover", ()),
    # the small local models' runs, read from the box built from what's committed
    ("demo:small-models", "demo/small-models", ()),
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
    pytest = lambda *target, **kw: command(  # noqa: E731
        *PYTEST, *target, needs=lambda: missing_module("pytest"), **kw
    )
    out += [
        ("tests", "tests:kernel", pytest("test_kernel.py")),
        ("tests", "tests:docs", pytest("test_docs.py", "test_docs_fires.py")),
    ]
    for k, part in enumerate(chunks(adapter_tests(), ADAPTER_CHUNKS), 1):
        out.append(("tests", f"tests:adapters-{k}", guarded_tests(*part)))
    # each add-on's tests again, in a copy holding only what its card uses
    out.append(("tests", "tests:alone", command(PY, "adapters/stdlib/ci/alone.py",
                needs=lambda: missing_module("pytest"))))  # fmt: skip
    out.append(
        ("tests", "tests:ui", pytest("ui"))
    )  # willow's own UI, over a scratch stack
    out.append(("tests", "tests:vectors",
                pytest("vectors/test_vectors.py", "-k", "as_it_is_now")))  # fmt: skip
    for k in range(1, STRIP_CHUNKS + 1):
        out.append(("tests", f"tests:strip-{k}", pytest(
            "test_strip.py", env={"WILLOW_STRIP_CHUNK": f"{k}/{STRIP_CHUNKS}"})))  # fmt: skip
    out.append(("tests", "tests:constitution", pytest("constitution")))
    # the coverage report, generated each run: it fails only on a clause the
    # person declared failing, and says why for each one it found nothing for
    out.append(("tests", "tests:coverage", command(PY, "constitution/coverage.py")))
    for port in PORTS:
        how = command(
            PY, "vectors/compare.py", "--port", port,
            needs=lambda p=port: missing_tools(*TOOLS[p]), judge=port_ran(port),
        )  # fmt: skip
        out.append(("ports", f"ports:{port}", how))
    out += [("demo", f"demo:{name}", demo(name)) for name in people()]
    for gate, target, tools in DEMO_TESTS:
        out.append(("demo", gate, command(*PYTEST, target, needs=lambda t=tools: (
            missing_module("pytest") or missing_tools(*t)))))  # fmt: skip
    for name in deps_add_ons():
        out.append(("deps", f"deps:{name}", deps_add_on(name)))
        out.append(("deps", f"deps:{name}@floor",
                    deps_add_on(name, "requirements-floor.txt")))  # fmt: skip
    out.append(("deps", "deps:floors", floors))
    for name in mutant_targets():
        how = command(PY, "adapters/stdlib/mutants/mutants.py", "run", name,
                      needs=lambda: missing_module("pytest"))  # fmt: skip
        out.append(("mutants", f"mutants:{name}", how))
    out += [("tools", f"tools:{name}", live_check(name)) for name in live_checks()]
    return out


PARTS = ("lint", "tests", "ports", "demo", "deps", "mutants", "tools")


def select(names: list[str], without: list[str], shard: str | None) -> list[str]:
    """The gates `run` runs, in GATES' order: each named one and each of a
    named part's (all of them when none is named), less the ones `without`
    names; with `shard` K/N, the Kth of N parts of those, cut by test-shards'
    own split with each gate weighing what `gate_weight` expects it to take,
    so the N parts end about together. Every gate is in exactly one of the N.
    Anything it doesn't know is refused, so a name spelled wrong never runs
    nothing."""
    every = [(part, gate) for part, gate, _ in gates()]
    known = set(PARTS) | {g for _, g in every}

    def group(name: str) -> set[str]:
        """tests:strip is its chunks, tests:strip-1 to -4, when no gate has
        that name itself."""
        if name in known:
            return {name}
        return {g for _, g in every if re.fullmatch(re.escape(name) + r"-\d+", g)}

    for name in names + without:
        if not group(name):
            raise ValueError(f"{name} isn't a part or a gate of ci.py")
    for name in without:
        if name in PARTS:
            raise ValueError(f"--without takes a gate, and {name} is a part")
    named = set().union(*map(group, names)) if names else set()
    left_out = set().union(*map(group, without)) if without else set()
    picked = [
        g
        for p, g in every
        if (not names or p in named or g in named) and g not in left_out
    ]
    if shard is None:
        return picked
    got = re.fullmatch(r"([1-9]\d*)/([1-9]\d*)", shard)
    if not got or int(got.group(1)) > int(got.group(2)):
        raise ValueError(f"--shard {shard} isn't K/N with K from 1 to N")
    shards = load_shards()
    # each gate weighs its expected seconds, from data committed with the
    # code: the record keeps no times, and the clock would cut differently
    # on every machine
    part = shards.split({g: gate_weight(g) for g in picked}, int(got.group(2)))[
        int(got.group(1)) - 1
    ]
    return [g for g in picked if g in part]


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
    `files_sha256` and in FILES.md's tree."""
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


def do_run(box: Path, chosen: list[str], ts: str) -> int:
    open_box(box, ts)
    files = files_sha256()
    python = "{}.{}".format(*sys.version_info[:2])
    states = []
    for _, gate, how in gates():
        if gate not in chosen:
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
        skips = skipped(said)
        if skips:
            row["skipped"] = skips
        kernel.append(box, ts, "verdict", who=WHO, **row)
        states.append((gate, state, why, skips))
    print()
    for gate, state, why, skips in states:
        print(verdict_line(gate, state, why, skips))
    return code_of([s for _, s, _, _ in states])


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
        print(
            f"{gate:<18} {r['state']:<12} python {r['python']}  row {r['n']}"
            + (f"  [{r['skipped']}]" if "skipped" in r else "")
        )
    return code_of([r["state"] for r in latest.values()])


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    opts, args, without, it = {}, [], [], iter(rest)
    for a in it:
        if a in ("--box", "--now", "--shard"):
            opts[a] = next(it, "")
        elif a == "--without":
            without.append(next(it, ""))
        else:
            args.append(a)
    box = Path(opts.get("--box") or ROOT / ".ci-record")
    if verb == "run" and not any(a.startswith("-") for a in args + without):
        try:
            chosen = select(args, without, opts.get("--shard"))
        except ValueError as e:
            print(f"refused: {e}", file=sys.stderr)
            return kernel.REFUSED
        return do_run(box, chosen, opts.get("--now") or commit_time())
    if verb == "verify" and not args:
        return do_verify(box)
    if verb == "show" and not args:
        return do_show(box)
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
