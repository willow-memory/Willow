"""route.py: a question sent to the step whose job it is. Python 3.9+.

    python adapters/stdlib/route/route.py "who still owes me money" [--run FOLDER] [--kinds FILE] [--json]
    python adapters/stdlib/route/route.py --questions FILE [--run FOLDER] [--kinds FILE] [--json]

    route: populated, "who still owes me money": money owed; that is the job of debts and invoices
      debts     What you owe and are owed, from the lines that say so.   mine/run/11-debts.txt
      invoices  Invoices you sent, held against your bank's payments.    mine/run/12-invoices.txt

One box takes every question, and the kernel answers it one way: the
passage holding the most of its words. That is right for a thing you wrote
down ("ruth's phone number") and wrong for "who still owes me money", which
no one passage says; it is a sum over many, and an add-on already does that
sum. This reads the question, says what kind it is, and names the steps
whose job that kind is.

The kinds are a file, `kinds.txt` beside this script, or your own with
--kinds: a line a kind, its cues, then the steps. A cue is a word in any of
its forms, or a few words together; `*` stands for one word. The first
line with a cue in the question wins. A question with no cue is a thing
you wrote down, and its step is the ask. It is rules you can read, not a
guess: the same question goes the same way every time, and a wrong turn is
a line to edit.

--run FOLDER is a stack's kept run (stack.py --to): each step named is
shown with the file its output was kept in, if that run has it, so the
question lands on what was already found. --questions FILE takes one a
line, or `name<TAB>question`, a group a kind.

It reads the kinds file, each named add-on's card for its one line, and
the run's log. Nothing is asked of your files and nothing is written.

It prints a report (ci/README.md, "The report contract"); --json gives the
same as one object. Exit codes, the kernel's: 0 routed; 42 a step it names
isn't an add-on here; 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
NAME = "route"
HERE = Path(__file__).resolve().parent
ADAPTERS = HERE.parents[1]
#: a question with no cue: a thing written down, and the ask's
PLAIN = "a thing you wrote down"
#: what the ask is called when a card has no line for it
ASK_LINE = "The kernel's own answer: the passage holding the most of your words."


def kinds(text: str) -> tuple[list[tuple[str, list[list[str]], list[str]]], str | None]:
    """([(kind, its cues as lists of words, its steps)], why not). `*` in a
    cue is kept as a word that matches any."""
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head, arrow, steps = line.partition("->")
        kind, colon, cues = head.partition(":")
        names = [s.strip() for s in steps.split(",") if s.strip()]
        cue_words = [
            [w if w == "*" else w.lower() for w in re.findall(r"\*|[\w']+", c)]
            for c in cues.split(",")
            if c.strip()
        ]
        if not arrow or not colon or not kind.strip() or not names or not cue_words:
            return [], f"line {n} isn't `kind: cue, cue -> step, step`"
        out.append((kind.strip(), cue_words, names))
    return out, None


def said(question: str) -> list[str]:
    """A question's words in order, lowercased, apostrophes kept."""
    return re.findall(r"[\w']+", question.lower())


def same(cue: str, word: str) -> bool:
    """A cue word and a question word are one word: equal, or one plain form."""
    return cue == "*" or cue == word or kernel.stem(cue) == kernel.stem(word)


def cue_in(cue: list[str], words: list[str]) -> bool:
    """Whether a cue's words come together, in order, in a question."""
    n = len(cue)
    return any(
        all(same(c, w) for c, w in zip(cue, words[i : i + n]))
        for i in range(len(words) - n + 1)
    )


def kind_of(question: str, table: list) -> tuple[str, list[str], str]:
    """(the kind, its steps, the cue that decided it) for one question."""
    words = said(question)
    for kind, cues, steps in table:
        for cue in cues:
            if cue_in(cue, words):
                return kind, steps, " ".join(cue)
    return PLAIN, ["ask"], ""


def line_of(step: str) -> str | None:
    """An add-on's one line, from its card; None when it isn't here."""
    if step == "ask":
        return ASK_LINE
    for base in ("stdlib", "deps"):
        card = ADAPTERS / base / step / "README.md"
        if card.is_file():
            for ln in card.read_text(encoding="utf-8").splitlines():
                if ln.startswith("line:"):
                    return ln[5:].strip()
            return ""
    return None


def kept(run: Path | None) -> dict[str, list[str]]:
    """{an add-on: the files a run kept its output in}, in step order."""
    out: dict[str, list[str]] = {}
    if run is None:
        return out
    for f in sorted(run.glob("[0-9]*-*.txt")):
        num, _, name = f.stem.partition("-")
        if num.strip("0"):  # not the log itself
            out.setdefault(name, []).append(str(f))
    return out


def where(step: str, found: dict[str, list[str]]) -> str:
    """Where a run kept a step's output; the ask's is the scan's or glance's."""
    for name in [step] if step != "ask" else ["glance", "scan"]:
        if name in found:
            return found[name][-1]
    return ""


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--questions", "--run", "--kinds"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (
        bool(opts.get("--questions")) == bool(args)
        or len(args) > 1
        or any(a.startswith("--") for a in args)
        or any(v == "" for v in opts.values())
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        table, why = kinds(Path(opts.get("--kinds", HERE / "kinds.txt")).read_text(encoding="utf-8"))  # fmt: skip
        if "--questions" in opts:
            asked = []
            for n, ln in enumerate(Path(opts["--questions"]).read_text(encoding="utf-8").splitlines(), 1):  # fmt: skip
                if ln.strip() and not ln.lstrip().startswith("#"):
                    name, tab, q = ln.partition("\t")
                    asked.append(
                        (name.strip() or str(n), q.strip())
                        if tab
                        else (str(n), ln.strip())
                    )
        else:
            asked = [("", args[0])]
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
    if not asked or not all(said(q) for _, q in asked):
        print("refused: a question with no words", file=sys.stderr)
        return kernel.REFUSED
    found = kept(run)
    missing: set[str] = set()

    def step_row(step: str) -> tuple[str, str]:
        line = line_of(step)
        if line is None:
            missing.add(step)
            return step, "not an add-on that is here"
        at = where(step, found)
        return step, f"{line}   {at}".rstrip() if at else line

    if len(asked) == 1 and not asked[0][0]:
        q = " ".join(asked[0][1].split())
        kind, steps, cue = kind_of(q, table)
        rows = [step_row(s) for s in steps]
        by = f' (by "{cue}")' if cue else ""
        said_ = f'"{q}": {kind}{by}; that is the job of {" and ".join(steps)}'
        groups = [(None, rows)]
    else:
        by_kind: dict[str, list] = {}
        steps_of: dict[str, list[str]] = {}
        for name, q in asked:
            kind, steps, cue = kind_of(q, table)
            mine = steps_of.setdefault(kind, [])
            # a kind on two lines is one group, with both lines' steps
            mine += [s for s in steps if s not in mine]
            by_kind.setdefault(kind, []).append((name, " ".join(q.split())))
        order = [
            k for k in dict.fromkeys([k for k, _, _ in table] + [PLAIN]) if k in by_kind
        ]
        groups = []
        for k in order:
            head = [(f"-> {s}", step_row(s)[1]) for s in steps_of[k]]
            groups.append((f"{k}: {len(by_kind[k])}", head + by_kind[k]))
        n = len(asked)
        said_ = f"{n} question{'' if n == 1 else 's'}: " + ", ".join(
            f"{len(by_kind[k])} {k}" for k in order
        )
    doc = {
        "addon": NAME,
        "state": "populated",
        "said": said_,
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
        print(f"{NAME}: {doc['state']}, {said_}")
        for g in doc["groups"]:
            if g["name"] is not None:
                print(f"## {g['name']}")
            for r in g["rows"]:
                print(f"  {r['where']:<{w}}  {r['what']}".rstrip())
    return kernel.ESCALATE if missing else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
