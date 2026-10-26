"""stack.py: one document from a stack of add-on steps over a box. Python 3.9+.

    python adapters/stdlib/stack/stack.py --box DIR --stack FILE

FILE is a markdown stack: a `##` heading opens a pool, and each `- NAME -- ARGS`
line under it is a step -- the add-on NAME run with the ARGS after the lone
`--`. `{box}` anywhere in a step's args is replaced with --box, so a step that
reads the box names it and a step that doesn't (a `git` or `pgp` step) leaves
it out. Blank lines, lines beginning `#` (but not `##`), and any other prose
are skipped, so a stack file reads as markdown; a step before any pool is
refused.

stack runs every step and composes one markdown document: a `##` section per
pool, each step's output under it in a fenced block. The order is the stacking
order -- peaks first: pools, and the steps within them, run tallest first, by
how many lines of output stack up, because that is what a reader meets first.

It only reads and composes. It runs add-ons, and each is held to its own card
by the guard, so stack writes no box, reads no key and approves nothing -- the
one-way arrow, a box to a document. The step list is open: any add-on can be a
step, so stack names network:none for its own run and leaves each step's reach
to the step's own card. Exit codes, the kernel's: 0 nothing in the stack waits
on you; 42 a step flagged something (or refused); 2 refused (a bad command
line, a box that isn't a kernel box, an unreadable or empty stack, or a step
whose add-on isn't here).
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402


def parse_stack(text: str) -> tuple[list, str | None]:
    """The pools a stack file names: a list of (heading, [steps]), each step a
    (name, args). Returns (pools, error); error is a message or None. A `##`
    line opens a pool; a `- ` line is a step in the open pool; a step before
    any pool, or a line that is neither, is an error."""
    pools: list = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or (line.startswith("#") and not line.startswith("##")):
            continue
        if line.startswith("##"):
            pools.append((line.lstrip("#").strip(), []))
        elif line.startswith("- "):
            if not pools:
                return [], f"line {n}: a step before any ## pool"
            name, sep, argstr = line[2:].strip().partition(" -- ")
            name = name.strip()
            if not name or "/" in name:
                return [], f"line {n}: a step names no add-on"
            try:
                args = shlex.split(argstr) if sep else []
            except ValueError as e:
                return [], f"line {n}: {e}"
            pools[-1][1].append((name, args))
        # any other line is prose in the markdown stack, and is skipped
    if not any(steps for _, steps in pools):
        return [], "the stack names no steps"
    return pools, None


def resolve(name: str) -> Path | None:
    """The one runnable script in the add-on's folder, or None if the add-on
    isn't here or its folder holds no single `__main__` script (ambiguous, so
    refused rather than guessed)."""
    for base in (STDLIB, STDLIB.parent / "deps"):
        folder = base / name
        if not folder.is_dir():
            continue
        mains = [
            p
            for p in sorted(folder.glob("*.py"))
            if not p.name.startswith("test_")
            and "__main__" in p.read_text(encoding="utf-8")
        ]
        return mains[0] if len(mains) == 1 else None
    return None


def run_step(script: Path, args: list[str], box: str) -> tuple[int, str]:
    """Run one step; (its exit code, the text it made). `{box}` in an arg is
    the box; stdin is closed so a step never waits on a person."""
    filled = [a.replace("{box}", box) for a in args]
    got = subprocess.run(
        [sys.executable, str(script), *filled],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    return got.returncode, (got.stdout or got.stderr).rstrip()


def mass(text: str) -> int:
    """How tall a stack is: its non-blank lines. Mass decides attention."""
    return sum(1 for ln in text.splitlines() if ln.strip())


def compose(ran: list, box: str) -> str:
    """The one markdown document: a `##` per pool, peaks first; each step's
    output fenced under it, with its exit flagged when it isn't clean."""
    nsteps = sum(len(done) for _, done in ran)
    out = [
        f"# stack over {box}: {nsteps} step{'' if nsteps == 1 else 's'} "
        f"in {len(ran)} pool{'' if len(ran) == 1 else 's'}, peaks first",
        "",
    ]
    for heading, done in ran:
        out.append(f"## {heading}")
        out.append("")
        for _, _, name, args, code, text in done:
            label = f"{name} -- {' '.join(args)}" if args else name
            flag = "" if code == kernel.ALIVE else f"  (exit {code})"
            out.append(f"- `{label}`{flag}")
            out.append("  ```")
            out += ["  " + ln for ln in (text.splitlines() or ["(nothing)"])]
            out.append("  ```")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    extra: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--box", "--stack"):
            opts[a] = next(it, "")
        else:
            extra.append(a)
    if extra or not opts.get("--box") or not opts.get("--stack"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        text = Path(opts["--stack"]).read_text(encoding="utf-8")
    except OSError:
        print(f"refused: can't read the stack {opts['--stack']}", file=sys.stderr)
        return kernel.REFUSED
    pools, err = parse_stack(text)
    if err:
        print(f"refused: {err}", file=sys.stderr)
        return kernel.REFUSED
    scripts: dict[str, Path] = {}
    for _, steps in pools:
        for name, _ in steps:
            if name not in scripts:
                script = resolve(name)
                if script is None:
                    print(f"refused: the {name} add-on isn't here", file=sys.stderr)
                    return kernel.REFUSED
                scripts[name] = script

    worst, flagged, nsteps = kernel.ALIVE, 0, 0
    ran: list = []
    for heading, steps in pools:
        done: list = []
        for idx, (name, args) in enumerate(steps):
            nsteps += 1
            code, out = run_step(scripts[name], args, str(box))
            done.append((mass(out), idx, name, args, code, out))
            if code != kernel.ALIVE:
                flagged += 1
                worst = kernel.ESCALATE
        done.sort(key=lambda s: (-s[0], s[1]))
        ran.append((heading, done))
    ran.sort(key=lambda p: (-sum(s[0] for s in p[1]), p[0]))

    doc = compose(ran, str(box))
    print(doc, end="")
    print(f"\n{flagged} of {nsteps} steps flagged (exit 42).")
    return worst


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
