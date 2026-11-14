"""stack.py: one document from a stack of add-on steps over a box. Python 3.9+.

    python adapters/stdlib/stack/stack.py --box DIR --stack FILE [--to FOLDER [--resume]]

FILE is a markdown stack: a `##` heading opens a pool, and each `- NAME -- ARGS`
line under it is a step -- the add-on NAME run with the ARGS after the lone
`--`. `{box}` anywhere in a step's args is replaced with --box, so a step that
reads the box names it and a step that doesn't (a `git` or `pgp` step) leaves
it out. Blank lines, lines beginning `#` (but not `##`), and any other prose
are skipped, so a stack file reads as markdown; a step before any pool is
refused.

stack runs every step and composes one markdown document: a `##` section per
pool, each step's output under it in a fenced block. The steps run in the order
the stack file lists them, pool by pool; the document is then stacked peaks
first: pools, and the steps within them, printed tallest first, by how many
lines of output stack up, because that is what a reader meets first.
A step whose card says `output: report` is asked for its report as JSON and
printed in the report's one shape (ci/README.md, the report contract); its
height is its rows, not its lines, and it is flagged by its exit code alone,
since a report's 42 never means "found nothing".

A step can take what an earlier step made. `{01}` in a step's args is the
file step 01's output was kept in, and `{01.json}` its report as data, 01
being its place in the stack file. It is the earlier step handing on: so it
needs the run kept (--to), the number must be a step before this one, and
`.json` a step that prints a report; each of those is refused before
anything runs. A step whose earlier step kept nothing is not run, and says
so.

--to FOLDER keeps the run as it happens, for following while it goes and for
reading after: `00-stack.txt` gets a line as each step starts and a line as it
ends (its exit code, and how many lines it made), and each step's output is
`NN-NAME.txt`, NN its place in the stack file. A step that prints as it goes
is written as it prints; a step asked for a report is written once, when its
report is whole, and its report is kept as data too, in `reports/NN-NAME.json`,
for a page to draw (browse's --run). FOLDER must be there and empty: a run is one folder, and a
second run in it would read as part of the first. Without --to nothing is
kept but the page, as before.

--resume goes on with the run that is in FOLDER, one that was cut off or one
whose stack has had steps added. From the top of the stack, each step the
earlier run finished, asked the very same way, with its output still there,
is kept and not run again. From the first step that isn't, every step runs,
finished before or not: a later step may need what an earlier one makes.
The page is the one a whole run would give. It doesn't know whether your
folder changed in between: it is for going on, not for refreshing.

It only reads and composes, and with --to writes that one folder. It runs add-ons, and each is held to its own card
by the guard, so stack writes no box, reads no key and approves nothing -- the
one-way arrow, a box to a document. The step list is open: any add-on can be a
step, so stack names network:none for its own run and leaves each step's reach
to the step's own card. Exit codes, the kernel's: 0 nothing in the stack waits
on you; 42 a step flagged something (or refused); 2 refused (a bad command
line, a box that isn't a kernel box, an unreadable or empty stack, or a step
whose add-on isn't here). For add-ons whose 42 means "none found", that is
shown but not flagged.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

NONE_FOUND = {"amounts", "contradictions", "duplicates", "said"}
FLAGS_ON_ALIVE = {"contradictions"}


def bare_backslash(argstr: str) -> bool:
    """Whether a step's args hold a backslash before a letter or digit,
    outside quotes. The shell's rule drops it without a word, so a pattern
    written `INV-\\d+` would run as `INV-d+` and match nothing."""
    quote = ""
    chars = iter(enumerate(argstr))
    for i, c in chars:
        if quote:
            if c == "\\" and quote == '"':
                next(chars, None)  # in double quotes it stays, or escapes a quote
            elif c == quote:
                quote = ""
        elif c in "'\"":
            quote = c
        elif c == "\\":
            if argstr[i + 1 : i + 2].isalnum():
                return True
            next(chars, None)
    return False


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
            if bare_backslash(argstr):
                return [], (
                    f"line {n}: a backslash outside quotes would be dropped; "
                    "put that option in quotes"
                )
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


def run_step(
    script: Path, args: list[str], box: str, live: Path | None = None
) -> tuple[int, str]:
    """Run one step; (its exit code, the text it made). `{box}` in an arg is
    the box. stdin is inherited (not opened here): a step reads no input, and
    opening /dev/null would itself be a write the card doesn't allow. With
    `live`, what the step prints goes to that file as it prints it, so the
    run can be followed; what it said on stderr is put there only when it
    printed nothing, as it is for the page."""
    filled = [a.replace("{box}", box) for a in args]
    if live is None:
        got = subprocess.run(
            [sys.executable, str(script), *filled],
            capture_output=True,
            text=True,
        )
        return got.returncode, (got.stdout or got.stderr).rstrip()
    # unbuffered, or a Python step's lines sit in its own buffer till it ends
    with open(live, "w", encoding="utf-8") as f:
        got = subprocess.run(
            [sys.executable, str(script), *filled],
            stdout=f,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    out = live.read_text(encoding="utf-8", errors="replace")
    if not out and got.stderr:
        out = got.stderr
        live.write_text(out, encoding="utf-8")
    return got.returncode, out.rstrip()


def mark(name: str, args: list[str]) -> str:
    """Eight characters that are this step and no other: the same add-on
    asked another way is another step, and what it made before is not its."""
    return kernel.h256(json.dumps([name, args]))[:8]


#: `{03}` or `{03.json}` in a step's args: an earlier step's kept output
HANDS = re.compile(r"\{(\d+)(\.json)?\}")


def hands(args: list[str]) -> list[tuple[int, bool]]:
    """(the step named, whether its report is asked for) for each earlier
    step a step's args name, in the order named."""
    return [(int(n), bool(j)) for a in args for n, j in HANDS.findall(a)]


def unhandable(flat: list, scripts: dict, kept: bool) -> str | None:
    """Why a stack's hand-ons can't be, or None: said before anything runs.
    `flat` is every step in the stack file's order."""
    for at, (name, args) in enumerate(flat, 1):
        for n, as_json in hands(args):
            tag = f"{{{n:02d}{'.json' if as_json else ''}}}"
            if not kept:
                return (
                    f"step {at} ({name}) takes {tag}, an earlier step's output; "
                    "that needs the run kept: add --to FOLDER"
                )
            if not 1 <= n < at:
                return f"step {at} ({name}) takes {tag}, which isn't a step before it"
            if as_json and not prints_a_report(scripts[flat[n - 1][0]]):
                return (
                    f"step {at} ({name}) takes {tag}, but step {n} "
                    f"({flat[n - 1][0]}) prints no report; {{{n:02d}}} is what it said"
                )
    return None


def fed(args: list[str], box: str) -> str:
    """Eight characters that are the files a step is given, as they are now:
    each arg that names a file, by its bytes. The file after `--to` is what
    the step makes, not what it is given, and an earlier step's output
    (`{01}`) is that step's to answer for; neither counts. A folder isn't
    read: a step over a folder is asked again only when its line changes.
    "" when it is given no file."""
    seen = []
    for before, a in zip([""] + args, args):
        if before == "--to" or HANDS.search(a):
            continue
        path = Path(a.replace("{box}", box))
        try:
            if path.is_file():
                seen.append([a, hashlib.sha256(path.read_bytes()).hexdigest()])
        except OSError:
            pass
    return kernel.h256(json.dumps(seen))[:8] if seen else ""


STARTED = re.compile(r"(\d+) (\S+): started \((\w+)(?:, fed (\w+))?\)")
ENDED = re.compile(r"(\d+) (\S+): exit (\d+), (\d+) lines?((?:, [^,]+)*)")


def ended(log: str) -> dict[int, dict]:
    """The steps an earlier run finished, read from its log: for each step's
    number, its name, its mark, its exit code, and how it was weighed and
    flagged. A step is finished when the last thing the log says of it is
    that it ended: one started again and not ended is not, whatever came
    before, since its file may be half of a second go."""
    out: dict[int, dict] = {}
    marks: dict[int, tuple[str, str, str | None]] = {}
    for line in log.splitlines():
        if m := STARTED.fullmatch(line):
            marks[int(m.group(1))] = (m.group(2), m.group(3), m.group(4))
            out.pop(int(m.group(1)), None)
        elif m := ENDED.fullmatch(line):
            n, name = int(m.group(1)), m.group(2)
            if marks.get(n, ("", "", None))[0] != name:
                continue  # an end with no start of its own says nothing
            said = [x for x in m.group(5).split(", ") if x]
            size = next((int(x[5:]) for x in said if x.startswith("mass ") and x[5:].isdigit()), int(m.group(4)))  # fmt: skip
            out[n] = {
                "name": name,
                "mark": marks[n][1],
                "fed": marks[n][2],  # None: a log from before this was kept
                "code": int(m.group(3)),
                "size": size,
                "flagged": "flagged" in said,
                "note": next(
                    (x for x in said if x != "flagged" and not x.startswith("mass ")),
                    "",
                ),  # fmt: skip
            }
    return out


class Run:
    """A run kept in a folder as it happens: a line in 00-stack.txt as each
    step starts and ends, and each step's output in a file of its own. With
    `again`, the folder is an earlier run's: its log is added to, not begun."""

    def __init__(self, folder: Path, steps: int, again: bool = False):
        self.folder = folder
        self.width = max(2, len(str(steps)))
        self.log = folder / f"{'0' * self.width}-stack.txt"
        self.before = ended(self.log.read_text(encoding="utf-8")) if again else {}
        if not again:
            self.log.write_text("", encoding="utf-8")

    def say(self, line: str) -> None:
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def file(self, n: int, name: str) -> Path:
        return self.folder / f"{n:0{self.width}d}-{name}.txt"

    def data(self, n: int, name: str) -> Path:
        """Where a report step's report is kept as data, for a page to draw:
        in a folder of its own, so what follows the run reads words only."""
        return self.folder / "reports" / f"{n:0{self.width}d}-{name}.json"

    def keep_report(self, n: int, name: str, doc: dict | None) -> None:
        """The step's report as JSON beside its words, or nothing there when
        it printed no report this time (an earlier go's would be a lie)."""
        path = self.data(n, name)
        if doc is None:
            if path.exists():
                path.unlink()
            return
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")

    def kept(self, n: int, name: str, args: list[str], box: str) -> dict | None:
        """What the earlier run made of this very step, if it finished it,
        its output is still there, and the files it was given are as they
        were; None if it must be run. A log from before a step's files were
        noted says nothing of them, and is taken at its word."""
        was = self.before.get(n)
        if was is None or (was["name"], was["mark"]) != (name, mark(name, args)):
            return None
        if was["fed"] is not None and was["fed"] != fed(args, box):
            return None
        try:
            text = self.file(n, name).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        return {**was, "out": text.rstrip()}

    def handed(self, flat: list, args: list[str]) -> tuple[list[str], str]:
        """(a step's args with each earlier step named put in as its kept
        file, "") or ([], which step kept nothing to hand on)."""
        missing: list[str] = []

        def path(m) -> str:
            n = int(m.group(1))
            name = flat[n - 1][0]
            p = self.data(n, name) if m.group(2) else self.file(n, name)
            if not p.is_file() or not p.stat().st_size:
                missing.append(f"step {n} ({name})")
            return str(p)

        filled = [HANDS.sub(path, a) for a in args]
        return ([], missing[0]) if missing else (filled, "")

    def start(self, n: int, name: str, args: list[str], box: str) -> Path:
        given = fed(args, box)
        self.say(
            f"{n:0{self.width}d} {name}: started ({mark(name, args)}"
            f"{', fed ' + given if given else ''})"
        )
        return self.file(n, name)

    def end(self, n: int, name: str, code: int, out: str, size: int, note: str, flagged: bool) -> None:  # fmt: skip
        """`size` is said when it isn't the lines (a report weighs its rows),
        and `note` when the exit code alone doesn't give it (a report's
        state): with those, a later run can put this step on its page as this
        one did, without running it."""
        lines = mass(out)
        said = [f"exit {code}", f"{lines} line{'s' * (lines != 1)}"]
        said += [f"mass {size}"] * (size != lines) + [note] * bool(note)
        said += ["flagged"] * flagged
        self.say(f"{n:0{self.width}d} {name}: {', '.join(said)}")


def prints_a_report(script: Path) -> bool:
    """Whether the step's card says `output: report` (ci/README.md, the
    report contract): then stack asks it for --json and prints the report."""
    try:
        card = (script.parent / "README.md").read_text(encoding="utf-8")
    except OSError:  # no card: no promise of a report
        return False
    head = re.search(r"<!--\s*willow-addon\s*\n(.*?)-->", card, re.S)
    return bool(
        head
        and re.search(r"^output:(?:.*,)?\s*report\s*(?:,.*)?$", head.group(1), re.M)
    )


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def as_report(code: int, out: str) -> tuple[dict | None, str]:
    """(the report, its text) from a --json run; (None, what it said) for a
    refusal or output that isn't one report."""
    if code == kernel.REFUSED:
        return None, out
    try:
        doc = json.loads(out)
        return doc, report_text(doc)
    except (ValueError, KeyError, TypeError):
        return None, f"not a report: {out[:200]}"


def mass(text: str) -> int:
    """How tall a stack is: its non-blank lines. Mass decides attention."""
    return sum(1 for ln in text.splitlines() if ln.strip())


def step_result(name: str, code: int) -> tuple[bool, str]:
    """(flagged, note) for a step's exit code, by that add-on's card."""
    if code == kernel.ALIVE and name in FLAGS_ON_ALIVE:
        return True, "flagged"
    if code == kernel.ESCALATE and name in NONE_FOUND:
        return False, "none found"
    if code == kernel.ALIVE:
        return False, ""
    return True, f"exit {code}"


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
        for _, _, name, args, _code, text, note in done:
            label = f"{name} -- {' '.join(args)}" if args else name
            flag = f"  ({note})" if note else ""
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
        if a in ("--box", "--stack", "--to"):
            opts[a] = next(it, "")
        elif a == "--resume":
            opts[a] = "yes"
        else:
            extra.append(a)
    if (
        extra
        or not opts.get("--box")
        or not opts.get("--stack")
        or ("--to" in opts and not opts["--to"])
        or ("--resume" in opts and "--to" not in opts)
    ):
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

    flat = [step for _, steps in pools for step in steps]
    if why := unhandable(flat, scripts, "--to" in opts):
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED

    run = None
    if "--to" in opts:
        to = Path(opts["--to"])
        if not to.is_dir():
            # a new run's own folder is made here; the folder it goes in
            # never is, so a mistyped path is refused, not built
            if to.exists() or not to.parent.is_dir():
                print(
                    f"refused: {to} can't be a run's folder: "
                    + ("it is a file" if to.exists() else f"{to.parent} isn't there"),
                    file=sys.stderr,
                )
                return kernel.REFUSED
            to.mkdir()
        total = sum(len(steps) for _, steps in pools)
        again = "--resume" in opts and any(to.iterdir())
        if again and not (to / f"{'0' * max(2, len(str(total)))}-stack.txt").is_file():
            print(
                f"refused: {to} isn't a run of a stack this long; it has no log to resume from",
                file=sys.stderr,
            )
            return kernel.REFUSED
        if not again and any(to.iterdir()):
            print(
                f"refused: {to} isn't empty; a run wants a folder of its own "
                "(--resume goes on with the run that's in it)",
                file=sys.stderr,
            )
            return kernel.REFUSED
        run = Run(to, total, again)
        if again:
            run.say(f"resumed: {len(run.before)} of {total} steps had finished")

    worst, flagged, nsteps = kernel.ALIVE, 0, 0
    fresh = False  # once a step runs, every step after it runs: it may need it
    ran: list = []
    for heading, steps in pools:
        done: list = []
        for idx, (name, args) in enumerate(steps):
            nsteps += 1
            report = prints_a_report(scripts[name])  # its rows decide its mass
            was = run.kept(nsteps, name, args, str(box)) if run and not fresh else None
            if was is not None:
                code, out, size, is_flagged = was["code"], was["out"], was["size"], was["flagged"]  # fmt: skip
                note = was["note"] if report else step_result(name, code)[1]
                run.say(f"{nsteps:0{run.width}d} {name}: kept from before")
            elif hands(args) and not (given := run.handed(flat, args))[0]:
                # the step before kept nothing: nothing to take, so not run
                fresh = True
                code, size, is_flagged, note = kernel.ESCALATE, 1, True, "not run"
                out = f"not run: {given[1]} kept nothing to hand on"
                run.say(f"{nsteps:0{run.width}d} {name}: {out}")
            else:
                fresh = True
                live = run.start(nsteps, name, args, str(box)) if run else None
                if hands(args):
                    args = run.handed(flat, args)[0]
                if report:
                    code, out = run_step(scripts[name], [*args, "--json"], str(box))
                    doc, out = as_report(code, out)
                    if live is not None:  # whole, once: its JSON is nothing to follow
                        live.write_text(out + "\n" if out else "", encoding="utf-8")
                        run.keep_report(nsteps, name, doc)
                    if doc is None:
                        is_flagged, note, size = True, f"exit {code}", mass(out)
                    else:
                        is_flagged = code != kernel.ALIVE
                        note = doc["state"] if is_flagged else ""
                        size = 1 + sum(len(g["rows"]) for g in doc["groups"])
                else:
                    code, out = run_step(scripts[name], args, str(box), live)
                    is_flagged, note = step_result(name, code)
                    size = mass(out)
                if run:
                    run.end(nsteps, name, code, out, size, note if report else "", is_flagged)  # fmt: skip
            done.append((size, idx, name, args, code, out, note))
            if is_flagged:
                flagged += 1
                worst = kernel.ESCALATE
        done.sort(key=lambda s: (-s[0], s[1]))
        ran.append((heading, done))
    ran.sort(key=lambda p: (-sum(s[0] for s in p[1]), p[0]))

    doc = compose(ran, str(box))
    print(doc, end="")
    print(f"\n{flagged} of {nsteps} steps flagged (exit {worst}).")
    if run:
        run.say(f"done: {flagged} of {nsteps} steps flagged")
    return worst


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
