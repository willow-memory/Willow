"""realdata.py: an add-on run on every demo person's real folder, by a script. Python 3.9+.

    python adapters/stdlib/ci/realdata.py run NAME [NAME ...]
    python adapters/stdlib/ci/realdata.py run --base REF

An add-on can pass every test on hand-made files and still be wrong on a
real folder (AGENTS.md, an add-on step by step, 8). That step was done by
hand in each session, and said in the pull request as "Real data: ...".

`run` makes each demo person's files (demo/PERSON/make_life.py writes
demo/PERSON/life/, which git leaves out) and a box over them, then runs the
add-on's line in test_contract.py's COMMANDS on each, as the contract test
fills it in ({box} the person's box, {pile} their folder, {tmp} scratch); a
reader runs `mirror` over the folder. Every run is under the guard, held to
its card, and to 60 seconds. `--base REF` runs every stdlib add-on whose
files the branch changed since it left REF.

A run fails on a traceback, a breach of its card's promises, a hang, an
exit other than 0, 2 and 42, or, for a reader, a mirror line longer than one
of the kernel's chunks: the kernel keeps only a line's first `MAX_CHUNK`
characters, so the rest of it is never read, and nothing says so (clauses
lost a chat's every message after the first few this way). A refusal (2) is said, not failed: some lines
name a file only the contract's pile has. What each run printed is shown,
for the pull request to say.

Exit codes, the kernel's: 0 every run held; 42 no add-on to run; 2 a run
failed, or refused.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STDLIB = ROOT / "adapters" / "stdlib"
USAGE = "usage: realdata.py run NAME [NAME ...] | realdata.py run --base REF"
NOW = ["--now", "2026-10-23T00:00:00Z"]
WAIT = 60


class Refused(Exception):
    pass


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def changed_add_ons(base: str) -> list[str]:
    """The stdlib add-ons whose files this branch changed since it left REF."""

    def git(*argv):
        got = subprocess.run(["git", *argv], cwd=ROOT, capture_output=True, text=True)
        if got.returncode != 0:
            raise Refused(f"git {argv[0]}: {got.stderr.strip()[:200]}")
        return got.stdout

    start = git("merge-base", base, "HEAD").strip()
    names = set()
    for p in git("diff", "--name-only", start).splitlines():
        parts = p.split("/")
        if (
            p.startswith("adapters/stdlib/")
            and len(parts) > 3
            and (STDLIB / parts[2]).is_dir()
        ):
            names.add(parts[2])
    return sorted(names)


def people(ci) -> list[str]:
    return ci.people()


def life_of(person: str) -> Path:
    """The person's files, made by their make_life.py (deterministic)."""
    got = subprocess.run([sys.executable, str(ROOT / "demo" / person / "make_life.py")],
                         cwd=ROOT, capture_output=True, text=True)  # fmt: skip
    life = ROOT / "demo" / person / "life"
    if got.returncode != 0 or not life.is_dir():
        raise Refused(
            f"demo/{person}/make_life.py: {(got.stderr or got.stdout).strip()[-200:]}"
        )
    return life


def row_of(contract, name: str) -> tuple[str, list[str]]:
    if name in contract.READERS:
        return contract.READERS[name][0], [
            "mirror",
            "--from",
            "{pile}",
            "--to",
            "{tmp}/mirror",
        ]
    if name not in contract.COMMANDS:
        raise Refused(f"{name} has no line in COMMANDS: a person doesn't run it")
    return contract.COMMANDS[name]


def long_lines(mirror: Path) -> list[tuple[str, int, int]]:
    """(file, line, length) for each line of a reader's mirror longer than one
    of the kernel's chunks, which the kernel cuts without a word."""
    out = []
    for p in sorted(mirror.rglob("*")) if mirror.is_dir() else []:
        if p.is_file():
            text = p.read_bytes().decode("utf-8", "replace")
            for i, line in enumerate(text.splitlines(), 1):
                if len(line) > kernel.MAX_CHUNK:
                    out.append((p.relative_to(mirror).as_posix(), i, len(line)))
    return out


def run_one(
    ci, name: str, script: Path, argv: list[str], life: Path, tmp: Path
) -> tuple[str, str]:
    """(verdict, what it printed): verdict '' when it held, else why not."""
    box = tmp / "box"
    subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(box),
                    "--pile", str(life), "--key", str(tmp / "key"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    fill = {"box": str(box), "pile": str(life), "tmp": str(tmp)}
    good = [a.format(**fill) for a in argv]
    log = tmp / "guard.log"
    try:
        got = subprocess.run([sys.executable, str(script), *good], input="", cwd=ROOT,
                             capture_output=True, text=True, timeout=WAIT,
                             env=ci.guarded(log))  # fmt: skip
    except subprocess.TimeoutExpired:
        return f"still running after {WAIT}s", ""
    said = (got.stdout + got.stderr).strip()
    broke = ci.breaches(log)
    if broke:
        return f"broke its card's promises: {broke}", said
    if "Traceback (most recent call last)" in got.stderr:
        return "a traceback", said
    if got.returncode not in (0, 2, 42):
        return f"exit {got.returncode}", said
    cut = long_lines(tmp / "mirror")
    if cut:
        where, line, size = cut[0]
        return (f"{len(cut)} mirror line(s) longer than the kernel's {kernel.MAX_CHUNK}"
                f" characters, which it cuts unread (first: {where}:{line}, {size})"), said  # fmt: skip
    return "", said


def run(
    names: list[str], lives: dict | None = None, contract=None, stdlib: Path = STDLIB
) -> tuple[list[tuple[str, str, str, int, str]], bool]:
    """([(add-on, person, verdict, lines printed, first lines)], every run
    held). Each person's files are made once, before any run: two runs never
    make a folder while another reads it."""
    ci = _load("willow_ci_for_realdata", HERE / "ci.py")
    if contract is None:
        contract = _load("willow_contract_for_realdata", HERE / "test_contract.py")
    if lives is None:
        lives = {p: life_of(p) for p in people(ci)}
    out, held = [], True
    for name in names:
        script_name, argv = row_of(contract, name)
        script = stdlib / name / script_name
        for person, life in lives.items():
            with tempfile.TemporaryDirectory() as tmp:
                why, said = run_one(ci, name, script, argv, life, Path(tmp))
            held = held and not why
            lines = said.splitlines()
            out.append((name, person, why, len(lines), " | ".join(lines[:2])[:160]))
    return out, held


def main(argv: list[str]) -> int:
    if argv[:1] != ["run"] or len(argv) < 2 or (argv[1] == "--base" and len(argv) != 3):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        names = changed_add_ons(argv[2]) if argv[1] == "--base" else argv[1:]
        if any(n.startswith("-") or not (STDLIB / n).is_dir() for n in names):
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
        ci = _load("willow_ci_for_realdata_people", HERE / "ci.py")
        contract = _load("willow_contract_for_realdata_rows", HERE / "test_contract.py")
        names = [n for n in names if n in contract.COMMANDS or n in contract.READERS]
        if not names:
            print("no add-on a person runs changed: nothing to run on real data")
            return kernel.ESCALATE
        print(f"real data: {', '.join(names)} on {', '.join(people(ci))}")
        rows, held = run(names)
    except Refused as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    for name, person, why, n, first in rows:
        print(
            f"  {name} on {person}: {why or 'held'}, {n} line(s){': ' + first if first else ''}"
        )
    if not held:
        print("a run on real data failed: fix it before the pull request opens")
        return kernel.REFUSED
    print("every run on real data held")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
