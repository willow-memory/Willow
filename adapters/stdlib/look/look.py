"""look.py: one question, answered by the step whose job it is. Python 3.9+.

    python adapters/stdlib/look/look.py "who still owes me money" --run FOLDER [--box BOX]
        [--kinds FILE] [--json]

    look: populated, "who still owes me money": money owed; 4 lines from debts and invoices
    ## debts: its 3 lines (none holds still, money)
      11-debts.txt:1     2024-05-22  $212.40  mail/sent/2024-05-22_fwd_letter.eml:7  Dana - got a letter saying I owe
    ## invoices: its 1 line (none holds still, money)
      12-invoices.txt:1  overdue  INV-2026-011  Larkfield Community Theatre  $640.00  due 2026-06-27

One box takes every question. The route add-on says what kind a question
is and which steps' job that kind is; this goes on and answers it, from
what a stack's kept run (stack.py --to) already found. "who still owes me
money" is no one passage: it is what the debts and invoices steps printed,
so those lines are the answer.

A step's lines that hold a word of the question come first, the ones
holding most of them first, then the rest as the step said them: "did
lakeside pay" puts the Lakeside lines of a long list on top. The words
that only said what kind of question it is (owes) aren't counted. Eight
lines a step; the rest are in the file each row names.

A thing you wrote down ("ruth's phone number"), or a kind that names the
ask beside its steps, is asked of your files with --box: the kernel's own
answer, the passages holding at least half the question's words, with the
words the best one lacks said. Without --box that part is left, and said.

It reads the kinds file, the run's kept files and, with --box, your files.
Nothing is written. It prints a report (ci/README.md, "The report
contract"); --json gives the same as one object. Exit codes, the kernel's:
0 answered, or your files hold nothing for it; 42 a step whose job it is
isn't in the run, or the ask was left for want of --box; 2 refused.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    'usage: look.py "a question" --run FOLDER [--box BOX] [--kinds FILE] [--json]\n'
    "       (one of --run and --box, or both)"
)
NAME = "look"
STDLIB = Path(__file__).resolve().parents[1]
#: how many of a step's lines, and of your files' passages, are shown
SHOWN = 8
PASSAGES = 3
#: how much of a line or a passage's opening is shown
WIDE = 160


def sibling(folder: str, module: str):
    """Another add-on's module, from its source beside this one."""
    path = STDLIB / folder / f"{module}.py"
    mod = types.ModuleType(f"look_{module}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def want_of(question: str, cue: str) -> list[str]:
    """The question's words that count, once each, in the order asked,
    without the ones that only said its kind."""
    cued = {kernel.stem(w) for w in kernel.words(cue)}
    return list(
        dict.fromkeys(
            w
            for w in kernel.words(question)
            if w not in kernel.FUNCTION and kernel.stem(w) not in cued
        )
    )


def clip(text: str) -> str:
    """A line or a passage on one line, no longer than is shown."""
    flat = " ".join(text.split())
    return flat if len(flat) <= WIDE else flat[:WIDE].rsplit(" ", 1)[0] + "…"


def lines_of(path: Path) -> list[tuple[int, str]]:
    """(line number, line) for each line of a kept file that says something."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return [(n, ln) for n, ln in enumerate(text.splitlines(), 1) if ln.strip()]


def from_step(path: Path, want: list[str], alias: dict):
    """(heading, rows) for one step's kept file: its lines holding a word of
    the question first, most held first, then the rest as the step said them."""
    lines = lines_of(path)
    held = []
    for n, ln in lines:
        toks = kernel.toks({"text": ln, "path": ""})
        has = sum(kernel.held_by(w, toks, alias) for w in want)
        if has:
            held.append((-has, n, ln))
    total = f"{len(lines)} line{'s' * (len(lines) != 1)}"
    first = [(n, ln) for _, n, ln in sorted(held)]
    rest = [x for x in lines if x not in first]
    shown = (first + rest)[:SHOWN]
    if held:
        head = f"{len(held)} of its {total} hold {', '.join(want)}, and come first"
    else:
        none = f" (none holds {', '.join(want)})" if want else ""
        head = f"its {total}{none}"
    if len(shown) < len(lines):
        head += f"; {len(shown)} shown"
    return head, [(f"{path.name}:{n}", clip(ln)) for n, ln in shown]


def from_files(box: Path, question: str):
    """(heading, rows, why not) for the kernel's own answer from a box."""
    if not (box / "kernel.json").exists():
        return "", [], f"{box} is not a kernel box; init first"
    cfg = kernel.config(box)
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            return "", [], why
        alias = alias or {}
    served = kernel.rank(kernel.chunks(Path(cfg["pile"])), question, alias, PASSAGES)
    if not served:
        return "your files hold nothing for it; why-not says why", [], None
    want = list(
        dict.fromkeys(w for w in kernel.words(question) if w not in kernel.FUNCTION)
    )
    lacks = [w for w in want if not kernel.held_by(w, kernel.toks(served[0]), alias)]
    head = "the passages holding the most of your words"
    if lacks:
        head += f"; the best holds {len(want) - len(lacks)} of {len(want)}"
        head += f", lacks {', '.join(lacks)}"
    rows = [(f"{c['path']}:{c['line']}", clip(c["text"])) for c in served]
    return head, rows, None


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--run", "--box", "--kinds"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (
        len(args) != 1
        or args[0].startswith("--")
        or any(v == "" for v in opts.values())
        or not ("--run" in opts or "--box" in opts)
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    route = sibling("route", "route")
    question = " ".join(args[0].split())
    if not route.said(question):
        print("refused: a question with no words", file=sys.stderr)
        return kernel.REFUSED
    try:
        kinds_file = Path(opts.get("--kinds", STDLIB / "route" / "kinds.txt"))
        table, why = route.kinds(kinds_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"refused: a file could not be read: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    if why:
        print(f"refused: the kinds file: {why}", file=sys.stderr)
        return kernel.REFUSED
    run = Path(opts["--run"]) if "--run" in opts else None
    if run is not None and not run.is_dir():
        print(f"refused: {run} isn't a folder", file=sys.stderr)
        return kernel.REFUSED
    kind, steps, cue = route.kind_of(question, table)
    want = want_of(question, cue)
    found = route.kept(run)
    groups: list[tuple[str, list]] = []
    answered: list[str] = []
    waits: list[tuple[str, str]] = []
    n = 0
    nothing = ""
    for step in steps:
        if step == "ask":
            if "--box" not in opts:
                waits.append(("ask", "not asked of your own files: add --box BOX"))
                continue
            head, rows, bad = from_files(Path(opts["--box"]), question)
            if bad:
                print(f"refused: {bad}", file=sys.stderr)
                return kernel.REFUSED
            if rows:
                groups.append((f"your files: {head}", rows))
                answered.append("your files")
                n += len(rows)
            else:
                nothing = head
            continue
        if run is None:
            waits.append((step, "its job, and no run was given: add --run FOLDER"))
        elif step not in found:
            waits.append((step, "its job, and not a step of this run"))
        else:
            try:
                head, rows = from_step(Path(found[step][-1]), want, {})
            except OSError as e:
                waits.append(
                    (step, f"its kept file could not be read: {type(e).__name__}")
                )
                continue
            if rows:
                groups.append((f"{step}: {head}", rows))
                answered.append(step)
                n += len(rows)
            else:
                waits.append((step, "ran, and said nothing"))
    if waits:
        groups.append(("left", waits))
    by = f' (by "{cue}")' if cue else ""
    if answered:
        said = f"{n} line{'s' * (n != 1)} from {' and '.join(answered)}"
    elif waits:
        said = "nothing to answer it from yet"
    else:
        said = nothing
    if nothing and (answered or waits):
        said += "; " + nothing
    doc = {
        "addon": NAME,
        "state": "populated" if groups else "empty",
        "said": f'"{question}": {kind}{by}; {said}',
        "groups": [
            {"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
            for g, rows in groups
        ],
    }
    if as_json:
        print(json.dumps(doc, ensure_ascii=False))
    else:
        rows = [r for g in doc["groups"] for r in g["rows"]]
        w = min(max((len(r["where"]) for r in rows), default=0), 60)
        print(f"{NAME}: {doc['state']}, {doc['said']}")
        for g in doc["groups"]:
            print(f"## {g['name']}")
            for r in g["rows"]:
                print(f"  {r['where']:<{w}}  {r['what']}".rstrip())
    return kernel.ESCALATE if waits else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
