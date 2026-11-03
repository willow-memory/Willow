"""suggest.py: the Forge's matchmaker over this willow's add-on cards.
Python 3.11+ (forge-play's floor), forge-play 0.10 or newer.

    python adapters/deps/forge/suggest.py suggest --box DIR "what you want done" [--json | --plan]
    python adapters/deps/forge/suggest.py propose --box DIR "what you want done"
                                                  --choose WORD=NAME ... [--why WORD=REASON ...] [--json]
    python adapters/deps/forge/suggest.py build   --box DIR "what you want done" --to STACK [--json]

A sentence in, the add-ons it names or means out. The Forge's card box reads
every card beside this script (built, and the ideas in adapters/planned.json)
as rows for its keyword scan: a card's name, and the lines of
ui/search-words.txt that point at it, are what a sentence can hit. `suggest`
says what comes out as a report (adapters/stdlib/ci/README.md, the report
contract), a group per kind of thing:

    forge: populated, 2 forks wait on you
    ## fork “email”
      adapters/stdlib/apple-mail/README.md  apple-mail: Apple Mail's .emlx ...
      adapters/stdlib/mail/README.md        mail: Email in .eml and mbox ...

    steps   an add-on the sentence reaches and nothing else does, one line
            for a stack file; or a fork you settled before, read from your
            record: the kernel serves it only while its seal proves under
            your key, so it is a step, not a question, and you are not asked
            twice
    fork    one word that reaches several add-ons ("email": mail, apple-mail):
            a decision with the cards as options and their lines as tradeoffs
    stale   a seal whose card no longer does that word here; said, and the
            fork asked again
    ideas   an add-on the sentence names that isn't built yet

A stack you sealed for these very words is served first, as the kernel
serves any sealed answer, and nothing else is asked.

`propose` settles the open forks with `--choose WORD=NAME` (and a reason with
`--why WORD=...`) and hands the result to the kernel's door, nothing more:
one proposal per settled fork, under the words `forge decision willow-WORD`,
and one for the stack, under your sentence. Each waits on your seal
(`python kernel.py seal --box DIR proposal:...`); nothing is an answer before
that, and nothing runs. It carries the card's name, line, path and SHA-256,
so what you sealed is what you were shown. Its report is one row per
proposal: where it will be written, and what waits.

`build` runs the stack you sealed for these words, and nothing else: it
reads the sealed stack from the record (never a file you could edit), puts
each step's add-on into STACK with ui/assemble.py (every file hashed onto the
stack's own record, each contract checked), writes the stack file beside it,
and runs the stack add-on over your box, keeping the page at STACK/page.md.
Its report is one row per step: copied or not, its contract, and how it ran.
A step that can't be copied (a deps add-on, one that works only in this
repository) is said and left out, never guessed at. It refuses while no
stack is sealed for these words: the seal is the one gate between a
suggestion and a run. STACK's parent must exist; it never makes one.

--json prints the same report as one JSON object. --plan prints the whole as
the Forge reads it: the cards counted, the steps, the forks, what is sealed,
the ideas, and `plan`, a document forge.plan_shape validates,
forge.decision_extract turns into decisions and forge.build_loop resolves.
No model, no ranking: a card is here because it was named or an alias line
names it, and the report says which.

What is sealed is read through the kernel's own `sealed` and `standing`: a
seal counts only while its proof holds under the key and the proposal still
hashes to what was sealed; the key is the kernel's to read, never this
script's. The first standing seal for a decision is the one kept, as the
kernel's bite serves the first for a question, so the Forge (which asks the
kernel) and this read the same answer; a later seal waits its turn until the
first no longer stands. Decisions are keyed by decision type, `willow-WORD`,
the words the Forge asks for, so one it proposed is read the same as one this
script proposed.

Exit codes, the report's: 0 steps found and nothing waits on you, a stack
sealed for these words, nothing named (`empty`), or a stack built with every
step run clean; 42 a fork waits on you, your seal is waited on, a built
stack with a step flagged or left out (`populated`), or forge-play missing
or older than 0.10 (`unreachable`, said); 2 refused (a bad command line, a
folder that isn't a box or whose record doesn't verify, a fork left
unsettled or settled with an option not on offer, a stack sealed for these
words already, no stack sealed for these words to build, a STACK whose
parent is missing, a card beside this script that won't read).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

NAME = "forge"
APP = "willow-stack"
STACK_PATH = "forge/stack.md"
NEEDS = "forge-play 0.10 or newer is not installed: pip install -r adapters/deps/forge/requirements.txt"


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


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


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def forge():
    """The Forge's card box, plan shape and record naming, or None when
    forge-play is missing or too old to have them. Imported here, not at the
    top, so a bad command line is refused the same with or without it."""
    try:
        from forge import card_box, card_table, plan_shape, willow_record
    except ImportError:
        return None
    return card_box, card_table, plan_shape, willow_record


def quiet(fn, *args) -> tuple[int, str]:
    """A kernel verb run with its printing caught: (exit code, what it said)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def is_box(box: Path) -> str | None:
    """Why `box` can't be used, or None: not a box, or a record that
    doesn't verify. Nothing is read past a break."""
    if not (box / "kernel.json").is_file():
        return f"{box} is not a box (no kernel.json)"
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return "the record doesn't verify: " + "; ".join(breaks)
    return None


def on_record(box: Path, rec) -> tuple[dict, dict]:
    """What the person sealed, through the kernel: ({decision_type: {chose,
    word, row, subject}}, {bite_key: {row, subject, text}}). The first
    standing seal for a decision is the one kept, as the kernel keeps it."""
    rows, _ = kernel.read(box / "record.jsonl")
    decisions, stacks = {}, {}
    for subj, row in kernel.sealed(box, rows).items():
        prop, asked, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            continue
        if prop["path"] == STACK_PATH:
            stacks.setdefault(
                asked, {"row": row["n"], "subject": subj, "text": prop["data"]}
            )
        elif prop["path"].startswith(rec.DECISION_PATH.split("{")[0]):
            try:
                data = json.loads(prop["data"])
            except ValueError:
                continue
            if isinstance(data, dict) and isinstance(data.get("chose"), str):
                dt = data.get("decision_type")
                if not isinstance(dt, str) and isinstance(data.get("word"), str):
                    dt = rec.decision_type(data["word"])
                if isinstance(dt, str):
                    decisions.setdefault(
                        dt,
                        {"chose": data["chose"], "word": data.get("word", ""),
                         "row": row["n"], "subject": subj},
                    )  # fmt: skip
    return decisions, stacks


def promises(card) -> str:
    bits = [f"writes {card.writes or '?'}", f"network {card.network or '?'}"]
    if card.needs:
        bits.append(f"needs {card.needs}")
    if not card.built:
        bits.append("an idea, not built")
    return "; ".join(bits)


def tradeoff(card) -> str:
    return f"{card.line} ({promises(card)})"


#: each add-on's step line, `NAME -- ARGS`, filled by `commands`; the default
#: when the contract's rows can't be read is the one every page add-on takes
STEPS: dict[str, str] = {}
CONTRACT = ROOT / "adapters/stdlib/ci/test_contract.py"


def commands(pile: str) -> tuple[dict[str, str], str]:
    """Each add-on's own good command line, from the ci add-on's contract
    (test_contract.py's COMMANDS: the argv its contract test runs against a
    fresh box), as a step's args: `{box}` kept for the stack add-on to fill,
    `{pile}` filled with this box's folder, `{tmp}` kept for `build` to fill
    with a folder of its own, and the test's pinned `--now` taken off so the
    add-on runs at the real now. ({name: args}, where they came from); the
    ci add-on absent, or pytest (which its test file imports) missing, is
    said, and every step then takes the default `--box {box}`."""
    if not CONTRACT.is_file():
        return {}, "the ci add-on isn't here; steps take --box {box}"
    try:
        spec = importlib.util.spec_from_file_location("willow_contract", CONTRACT)
        tc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tc)
    except Exception as e:  # noqa: BLE001  the reason is the message (pytest, say)
        return (
            {},
            f"the ci add-on's contract couldn't be read ({type(e).__name__}: {e}); steps take --box {{box}}",
        )
    out = {}
    for name, (_, argv) in tc.COMMANDS.items():
        args, skip = [], False
        for a in argv:
            if skip:
                skip = False
                continue
            if a == "--now":
                skip = True
                continue
            a = a.replace("{pile}", pile)
            args.append(shlex.quote(a) if re.search(r"[\s'\"]", a) else a)
        out[name] = " ".join(args)
    return out, "from the ci add-on's contract, each add-on's own good command line"


def step_line(name: str) -> str:
    return f"- {name} -- {STEPS.get(name, '--box {box}')}\n"


def plan(box, hits, shape, rec, sealed: dict) -> dict:
    """{cards, steps, forks, sealed, ideas, plan}: what the sentence reaches,
    what the record settled, and the Forge's plan document (or None when
    there is nothing to run)."""
    found = box.lookup(hits)
    forks = box.forks(hits)
    by_name = {c.name: c for c in box.cards}
    settled, open_forks = {}, {}
    for word, names in forks.items():
        got = sealed.get(rec.decision_type(word))
        if got and got["chose"] in names:
            settled[word] = {**got, "decision_type": rec.decision_type(word)}
        else:
            open_forks[word] = names
            if got:
                settled[word] = {**got, "decision_type": rec.decision_type(word),
                                 "stale": f"{got['chose']} no longer does “{word}” here"}  # fmt: skip
    in_fork = {n for names in open_forks.values() for n in names}
    chosen = {got["chose"]: word for word, got in settled.items() if "stale" not in got}
    in_any_fork = {n for names in forks.values() for n in names}
    steps, ideas, entries = [], [], []
    for cand in found:
        card = by_name[cand.name]
        if cand.name in in_fork:
            continue
        if cand.name in chosen:
            word = chosen[cand.name]
            why = f"you sealed it for “{word}” (row {settled[word]['row']})"
        elif card.name in in_any_fork:
            continue  # the other option of a settled fork
        else:
            why = cand.why
        if not card.built:
            ideas.append(
                {"name": cand.name, "line": card.line, "why": why, "where": card.where}
            )
            continue
        steps.append({"name": cand.name, "line": card.line, "why": why, "where": card.where,
                      "promises": promises(card)})  # fmt: skip
        entries.append(
            shape.FileWrite(
                dest_path=f"steps/{cand.name}.md", content=step_line(cand.name)
            )
        )
    fork_docs = {}
    for word, names in open_forks.items():
        options, resolves = [], {}
        for n in names:
            card = by_name[n]
            options.append(shape.ForkOption(label=n, tradeoff=tradeoff(card)))
            resolves[n] = (
                (shape.FileWrite(dest_path=f"steps/{n}.md", content=step_line(n)),)
                if card.built
                else ()
            )
        entries.append(
            shape.Fork(
                decision_type=rec.decision_type(word),
                surface=f"“{word}” could be {', '.join(names)}: which add-on?",
                options=tuple(options),
                recommended=None,
                confidence=None,
                resolves=resolves,
            )
        )
        fork_docs[word] = [
            {"name": n, "where": by_name[n].where, "tradeoff": o.tradeoff}
            for n, o in zip(names, options)
        ]
    doc = (
        shape.PlanDoc(app_name=APP, entries=tuple(entries)).to_dict()
        if entries
        else None
    )
    if doc is not None:
        shape.validate(doc)  # the Forge's own check, before anyone is told it is a plan
    built = sum(1 for c in box.cards if c.built)
    return {
        "cards": {"built": built, "ideas": len(box.cards) - built},
        "steps": steps,
        "forks": fork_docs,
        "sealed": settled,
        "ideas": ideas,
        "plan": doc,
    }


def to_report(out: dict, rec) -> tuple[dict, int]:
    """The plan as a report, and the exit code: a fork waits on you (42), or
    nothing does (0)."""
    if "stack" in out:
        s = out["stack"]
        rows = [
            (f"{STACK_PATH}:{i}", ln)
            for i, ln in enumerate(s["text"].splitlines(), 1)
            if ln.strip()
        ]
        said = f"a stack is sealed for these words (row {s['row']}); nothing to ask"
        return report(
            NAME,
            "populated",
            said,
            [(f"stack sealed for these words ({s['subject']})", rows)],
        ), kernel.ALIVE
    groups = [("steps", [(s["where"], f"{s['name']}: {s['line']} ({s['promises']})"
                          + (f"; {s['why']}" if s["why"].startswith("you sealed") else ""))
                         for s in out["steps"]])]  # fmt: skip
    for word, options in out["forks"].items():
        groups.append(
            (
                f"fork “{word}”",
                [(o["where"], f"{o['name']}: {o['tradeoff']}") for o in options],
            )
        )
    groups.append(("stale seals, asked again", [
        (rec.DECISION_PATH.format(got["decision_type"]), f"{got['stale']} (row {got['row']})")
        for got in out["sealed"].values() if "stale" in got]))  # fmt: skip
    groups.append(
        (
            "ideas",
            [
                (i["where"], f"{i['name']}: {i['line']} (not built)")
                for i in out["ideas"]
            ],
        )
    )
    n_forks, n_steps = len(out["forks"]), len(out["steps"])
    if n_forks:
        said = f"{n_forks} fork{'s wait' if n_forks != 1 else ' waits'} on you"
        return report(NAME, "populated", said, groups), kernel.ESCALATE
    if n_steps:
        said = f"{n_steps} step{'s' if n_steps != 1 else ''}, nothing waits on you"
        return report(NAME, "populated", said, groups), kernel.ALIVE
    if out["ideas"]:
        return report(
            NAME, "populated", "only ideas, nothing built to run", groups
        ), kernel.ALIVE
    said = "nothing named: no card or alias line matched; add a line to ui/search-words.txt if one should"
    return report(NAME, "empty", said, []), kernel.ALIVE


def steps_of(stack_text: str) -> list[str]:
    """The add-ons a sealed stack file names, in order: each `- NAME -- ARGS`
    line's NAME, as the stack add-on reads them."""
    out = []
    for raw in stack_text.splitlines():
        line = raw.strip()
        if line.startswith("- "):
            name = line[2:].partition(" -- ")[0].strip()
            if name and name not in out:
                out.append(name)
    return out


ASSEMBLED = re.compile(r"^\+ (\S+)\s+.*?contract (\S+)\s+tests (\S+)(?::\s*(.*))?$")


def assemble(to: Path, name: str) -> tuple[str, str]:
    """One add-on into the stack at `to` through ui/assemble.py, one at a
    time: ("copied", what assemble said of its contract and tests) or
    ("left out", why). A piece already there is left as it is."""
    stack = to / "stack"
    if (stack / "adapters" / "stdlib" / name).is_dir():
        return "copied", "already in the stack"
    got = subprocess.run(
        [
            sys.executable,
            str(ROOT / "ui" / "assemble.py"),
            "add",
            name,
            "--to",
            str(to),
        ],
        capture_output=True,
        text=True,
    )
    if got.returncode == kernel.REFUSED:
        why = (got.stderr or got.stdout).strip().splitlines()[-1:] or ["refused"]
        return "left out", why[0].removeprefix("refused: ")
    for line in got.stdout.splitlines():
        m = ASSEMBLED.match(line.strip())
        if m and m.group(1) == name:
            tests = m.group(3) + (f" ({m.group(4)})" if m.group(4) else "")
            return "copied", f"contract {m.group(2)}; tests {tests}"
    return "copied", "assemble said nothing of it"


def build(box: Path, sentence: str, to: Path, stacks: dict) -> tuple[dict | None, int]:
    """The stack sealed for these words, assembled into `to` and run over
    the box: (the report, 0 clean or 42 flagged), or (None, 2) refused."""
    k = kernel.bite_key(sentence)
    if k not in stacks:
        print(
            "refused: no stack is sealed for these words; suggest, propose, then seal",
            file=sys.stderr,
        )
        return None, kernel.REFUSED
    if not to.parent.is_dir():
        print(
            f"refused: {to.parent} is missing; a folder to build in is yours to make",
            file=sys.stderr,
        )
        return None, kernel.REFUSED
    sealed = stacks[k]
    if not (to / "stack" / "STACK.json").is_file():
        got = subprocess.run(
            [sys.executable, str(ROOT / "ui" / "assemble.py"), "init", "--to", str(to)],
            capture_output=True,
            text=True,
        )
        if got.returncode != kernel.ALIVE:
            print(
                "refused:",
                (got.stderr or got.stdout).strip().splitlines()[-1],
                file=sys.stderr,
            )
            return None, kernel.REFUSED
    state, said = assemble(to, "stack")  # the runner, the one piece every stack has
    if state != "copied":
        print(f"refused: the stack add-on could not be put in: {said}", file=sys.stderr)
        return None, kernel.REFUSED
    names = steps_of(sealed["text"])
    rows, left = [], []
    for name in names:
        state, said = assemble(to, name)
        (rows if state == "copied" else left).append(
            (f"adapters/stdlib/{name}/", f"{name}: {said}")
        )
    stack_file = to / "forge-stack.md"
    scratch = to / "out"  # what the contract calls {tmp}: a folder of the build's own
    scratch.mkdir(exist_ok=True)
    stack_file.write_text(
        sealed["text"].replace("{tmp}", str(scratch)), encoding="utf-8"
    )
    runner = to / "stack" / "adapters" / "stdlib" / "stack" / "stack.py"
    got = subprocess.run(
        [sys.executable, str(runner), "--box", str(box), "--stack", str(stack_file)],
        capture_output=True,
        text=True,
    )
    page = to / "page.md"
    page.write_text(got.stdout, encoding="utf-8")
    ran = {}
    for line in got.stdout.splitlines():
        m = re.match(r"^- `(\S+)(?: --.*?)?`(?:\s+\((.*)\))?$", line)
        if m:
            ran[m.group(1)] = m.group(2) or "clean"
    rows = [(w, f"{x}; ran: {ran.get(x.split(':')[0], 'not run')}") for w, x in rows]
    flagged = sum(1 for n in names if ran.get(n, "") not in ("clean", "none found"))
    said = (f"{len(rows)} of {len(names)} step{'s' if len(names) != 1 else ''} built into {to}, "
            f"page at {page}; {flagged} flagged, {len(left)} left out")  # fmt: skip
    doc = report(NAME, "populated", said, [("built", rows), ("left out", left)])
    code = (
        kernel.ESCALATE
        if flagged or left or got.returncode == kernel.REFUSED
        else kernel.ALIVE
    )
    return doc, code


def pairs(items: list[str], what: str) -> tuple[dict[str, str], str | None]:
    """`WORD=VALUE` arguments as a dict, or why one isn't."""
    out = {}
    for it in items or []:
        word, sep, value = it.partition("=")
        if not sep or not word.strip() or not value.strip():
            return {}, f"{what} takes WORD=VALUE, not {it!r}"
        out[word.strip()] = value.strip()
    return out, None


def propose(
    box: Path, sentence: str, out: dict, cards, choose: dict, why: dict, rec
) -> tuple[dict | None, int]:
    """Each settled fork, and the stack, to the kernel's door: (the report,
    exit 42), or (None, 2) refused before writing anything, when a fork is
    left open or settled with an option not on offer. After the refusals,
    every write is the kernel's."""
    for word, options in out["forks"].items():
        names = [o["name"] for o in options]
        if word not in choose:
            print(
                f"refused: “{word}” is not settled: --choose {word}={'|'.join(names)}",
                file=sys.stderr,
            )
            return None, kernel.REFUSED
        if choose[word] not in names:
            print(f"refused: {choose[word]} is not an option for “{word}”: {', '.join(names)}", file=sys.stderr)  # fmt: skip
            return None, kernel.REFUSED
    for word in choose:
        if word not in out["forks"]:
            print(f"refused: nothing to choose for “{word}”", file=sys.stderr)
            return None, kernel.REFUSED
    by_name = {c.name: c for c in cards}
    run = [s["name"] for s in out["steps"]] + [
        n for n in choose.values() if by_name[n].built
    ]
    if not run:
        print(
            "refused: nothing to propose: no step and no settled fork", file=sys.stderr
        )
        return None, kernel.REFUSED
    ts = kernel.now()
    rows = []
    for word, name in choose.items():
        card = by_name[name]
        others = [o["name"] for o in out["forks"][word] if o["name"] != name]
        dt = rec.decision_type(word)
        pinned = hashlib.sha256((ROOT / card.where).read_bytes()).hexdigest()
        data = {
            "word": word,
            "decision_type": dt,
            "chose": name,
            "over": others,
            "why": why.get(word, ""),
            "card": {
                "name": card.name,
                "line": card.line,
                "where": card.where,
                "sha256": pinned,
            },
        }
        prop = {
            "path": rec.DECISION_PATH.format(dt),
            "data": json.dumps(data, sort_keys=True, ensure_ascii=False),
            "cites": [],
            "claim": f"for “{word}”: {name} over {', '.join(others)}; {why.get(word) or 'no reason given'}",
        }
        code, said = quiet(kernel.bite, box, rec.question(dt), ts)
        if code == kernel.REFUSED:
            print("refused:", said.strip(), file=sys.stderr)
            return None, kernel.REFUSED
        code, said = quiet(
            kernel.propose, box, [json.dumps(prop, ensure_ascii=False)], ts
        )
        if not said.startswith("pass "):
            print("refused:", said.strip(), file=sys.stderr)
            return None, kernel.REFUSED
        rows.append((prop["path"], f"{said.split()[1]}  {name} for “{word}”"))
    text = f"# {sentence}\n\n## for “{sentence}”\n" + "".join(step_line(n) for n in run)
    prop = {
        "path": STACK_PATH,
        "data": text,
        "cites": [],
        "claim": f"a stack for “{sentence}”: {', '.join(run)}",
    }
    code, said = quiet(kernel.bite, box, sentence, ts)
    if code == kernel.REFUSED:
        print("refused:", said.strip(), file=sys.stderr)
        return None, kernel.REFUSED
    code, said = quiet(kernel.propose, box, [json.dumps(prop, ensure_ascii=False)], ts)
    if not said.startswith("pass "):
        print("refused:", said.strip(), file=sys.stderr)
        return None, kernel.REFUSED
    rows.append((STACK_PATH, f"{said.split()[1]}  a stack: {', '.join(run)}"))
    said = f"{len(rows)} waiting on your seal: python kernel.py seal --box DIR proposal:..."
    return report(NAME, "populated", said, [(None, rows)]), kernel.ESCALATE


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    p = argparse.ArgumentParser(prog="suggest.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="verb", required=True)
    for verb in ("suggest", "propose", "build"):
        s = sub.add_parser(verb)
        s.add_argument("sentence", help="what you want done, in your own words")
        s.add_argument("--box", required=True, help="your record")
        if verb == "suggest":
            s.add_argument(
                "--plan",
                action="store_true",
                help="the plan as the Forge reads it, as JSON",
            )
        elif verb == "build":
            s.add_argument(
                "--to",
                required=True,
                help="the folder to build in; its parent must exist",
            )
        else:
            s.add_argument(
                "--choose", action="append", metavar="WORD=NAME", help="settle a fork"
            )
            s.add_argument(
                "--why", action="append", metavar="WORD=REASON", help="your reason"
            )
    a = p.parse_args(argv)
    box = Path(a.box)
    why = is_box(box)
    if why:
        print("refused:", why, file=sys.stderr)
        return kernel.REFUSED
    got = forge()
    if got is None:
        say(report(NAME, "unreachable", NEEDS, []), as_json)
        return kernel.ESCALATE
    card_box, card_table, shape, rec = got
    try:
        cards = card_box.CardBox(ROOT)
    except card_table.CardTableError as e:  # a card beside this script that won't read
        print("refused:", e, file=sys.stderr)
        return kernel.REFUSED
    sealed, stacks = on_record(box, rec)
    lines, where_from = commands(str(kernel.config(box)["pile"]))
    STEPS.update(lines)
    out = plan(cards, cards.scan(a.sentence), shape, rec, sealed)
    out["cards"]["commands"] = where_from
    if (k := kernel.bite_key(a.sentence)) in stacks:
        out["stack"] = stacks[k]
    if a.verb == "build":
        doc, code = build(box, a.sentence, Path(a.to), stacks)
        if doc is not None:
            say(doc, as_json)
        return code
    if a.verb == "propose":
        if "stack" in out:
            print(f"refused: a stack is sealed for these words already (row {out['stack']['row']})", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        choose, bad = pairs(a.choose, "--choose")
        reasons, worse = pairs(a.why, "--why")
        if bad or worse:
            print("refused:", bad or worse, file=sys.stderr)
            return kernel.REFUSED
        doc, code = propose(box, a.sentence, out, cards.cards, choose, reasons, rec)
        if doc is not None:
            say(doc, as_json)
        return code
    doc, code = to_report(out, rec)
    if a.plan:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        say(doc, as_json)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
