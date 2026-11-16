"""life_box.py: the game box, with a person's life for its binder. Python 3.9+.

    python demo/life-box/life_box.py open   --who NAME --table DIR
    python demo/life-box/life_box.py week   --table DIR
    python demo/life-box/life_box.py ask    --table DIR
    python demo/life-box/life_box.py decide --table DIR
    python demo/life-box/life_box.py recap  --table DIR

The game box lays a game master's binder, reads it through the game
master's words, preps a night with a stack, and lets nothing stand until
the one who holds the key seals it. This lays the same over one of
willow's made-up lives (demo/NAME, made by its make_life.py), read through
the starter words list a person begins with:

- `open` makes NAME's life at DIR/NAME/life, copies the starter words list
  to DIR/words.txt, and starts the record over the life at DIR/record,
  with a key made for NAME at DIR/NAME.key. NAME is made up, and so is the
  key: this demo seals for them. A real person's key is never made, read
  or used here.
- `week` runs week.md, a week's prep over the life, at NAME's own today
  (the TODAY their make_life.py writes them at), kept in DIR/week/NNN,
  beside NNN.md, the stack as it ran.
- `ask` asks each of NAME's own questions (demo/NAME/QUESTIONS.md) and
  hands in every passage served as a suggested answer, citing it. Nothing
  is an answer yet: each waits on the seal.
- `decide` is NAME, deciding: every suggestion is sealed with NAME's key if
  NAME's answer key (NAME.json, beside this) names its file, and what it
  must say, for that question; every other is declined. It runs only for a
  made-up person with an answer key.
- `recap` prints what NAME sealed as their answers, and what they said no
  to, each question with the passage it rests on.

Exit codes, the kernel's: 0 done; 42 waiting on the seal; 2 refused.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

DEMO = ROOT / "demo"
STARTER = ROOT / "adapters" / "stdlib" / "starter-words" / "starter.py"
STACK = ROOT / "adapters" / "stdlib" / "stack" / "stack.py"
WEEK = HERE / "week.md"
TODAY = re.compile(r"^TODAY = date\((\d{4}), (\d{1,2}), (\d{1,2})\)", re.M)
QUESTION = re.compile(r"^\d+\. (.+)$", re.M)


def py(*argv, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True, text=True, check=False, **kw)  # fmt: skip


def fail(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def today_of(who: str) -> str:
    """NAME's own today, as their make_life.py writes them."""
    m = TODAY.search((DEMO / who / "make_life.py").read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"demo/{who}/make_life.py names no TODAY")
    y, mo, d = (int(g) for g in m.groups())
    return f"{y:04d}-{mo:02d}-{d:02d}T09:00:00Z"


def questions(who: str) -> list[str]:
    return QUESTION.findall((DEMO / who / "QUESTIONS.md").read_text(encoding="utf-8"))


def who_of(table: Path) -> str:
    return (table / "who.txt").read_text(encoding="utf-8").strip()


def box_of(table: Path) -> Path:
    return table / "record"


def cmd_open(who: str, table: Path) -> int:
    if not re.fullmatch(r"[a-z][a-z-]*", who) or not (DEMO / who / "make_life.py").is_file():  # fmt: skip
        return fail(
            f"{who!r} isn't one of willow's made-up lives (demo/NAME/make_life.py)"
        )
    if not (DEMO / who / "QUESTIONS.md").is_file():
        return fail(f"demo/{who} has no QUESTIONS.md of their own")
    if table.exists():
        return fail(f"{table} is there already: a life box is laid in a new folder")
    table.mkdir(parents=True)
    shutil.copytree(DEMO / who, table / who, ignore=shutil.ignore_patterns("life", "__pycache__"))  # fmt: skip
    made = py(table / who / "make_life.py", cwd=table / who)
    if made.returncode != 0:
        return fail(f"{who}'s make_life.py: {made.stderr.strip()}")
    now = today_of(who)
    words = py(STARTER, "copy", "--to", table / "words.txt")
    if words.returncode != 0:
        return fail(f"the starter words list: {words.stderr.strip()}")
    init = py(ROOT / "kernel.py", "init", "--box", box_of(table), "--pile", table / who / "life",
              "--key", table / f"{who}.key", "--words", table / "words.txt", "--now", now)  # fmt: skip
    if init.returncode != 0:
        return fail(f"the record: {init.stderr.strip()}")
    (table / "who.txt").write_text(who + "\n", encoding="utf-8")
    files = sum(1 for p in (table / who / "life").rglob("*") if p.is_file())
    print(
        f"{who}'s life is laid at {table}: {files} files, read through the starter words list,"
    )
    print(f"the record started at {now[:10]}, their today. {table / f'{who}.key'} is a key made for {who}, who is made up.")  # fmt: skip
    return kernel.ALIVE


def cmd_week(table: Path) -> int:
    who = who_of(table)
    n = len(list((table / "week").glob("[0-9][0-9][0-9]"))) + 1 if (table / "week").is_dir() else 1  # fmt: skip
    run = table / "week" / f"{n:03d}"
    run.parent.mkdir(parents=True, exist_ok=True)
    stack = (
        run.parent / f"{n:03d}.md"
    )  # the week at their today; the run's folder is the stack's own
    now = today_of(who)  # the steps' {today} only: the prose naming it stays as written
    text = "".join(ln.replace("{today}", now) if ln.startswith("- ") else ln for ln in WEEK.read_text(encoding="utf-8").splitlines(keepends=True))  # fmt: skip
    stack.write_text(text, encoding="utf-8")  # fmt: skip
    got = py(STACK, "--box", box_of(table), "--stack", stack, "--to", run)
    print(got.stdout, end="")
    print(got.stderr, end="", file=sys.stderr)
    return got.returncode


def cmd_ask(table: Path) -> int:
    who, box = who_of(table), box_of(table)
    now = today_of(who)
    handed = 0
    for i, q in enumerate(questions(who), 1):
        bite = py(ROOT / "kernel.py", "bite", "--box", box, "--now", now, q)
        served = (
            json.loads(bite.stdout).get("served", []) if bite.stdout.strip() else []
        )
        props = [json.dumps({"path": f"answers/q{i:02d}-{k}.txt", "data": s["text"], "cites": [s["id"]],
                             "claim": f"answers question {i}, \"{q}\", from {s['where']}"})  # fmt: skip
                 for k, s in enumerate(served, 1)]  # fmt: skip
        if not props:
            print(f"{i:>2}. {q}\n      nothing in the life holds it")
            continue
        sugg = table / "suggestions.jsonl"
        sugg.write_text("\n".join(props) + "\n", encoding="utf-8")
        got = py(
            ROOT / "kernel.py", "propose", "--box", box, "--now", now, "--file", sugg
        )
        sugg.unlink()
        passed = got.stdout.count("pass ")
        handed += passed
        print(
            f"{i:>2}. {q}\n      {passed} suggested: "
            + "; ".join(s["where"] for s in served)
        )
    print(f"\n{handed} answers wait on {who}'s seal; nothing is an answer until then.")
    return kernel.ESCALATE if handed else kernel.ALIVE


def waiting(box: Path) -> list[tuple[str, dict]]:
    """Each suggestion that passed and has no seal or decline yet, with its claim."""
    rows, _ = kernel.read(box / "record.jsonl")
    done = {r.get("subject") for r in rows if r["kind"] in ("seal", "decline")}
    out = []
    for r in rows:
        if (
            r["kind"] == "proposal"
            and r.get("verdict") == "pass"
            and r["subject"] not in done
        ):
            prop = json.loads((box / "proposals" / f"{r['subject'][9:]}.json").read_text(encoding="utf-8"))  # fmt: skip
            out.append((r["subject"], prop))
    return out


CLAIM = re.compile(r'^answers question (\d+), "(.*)", from (.+?):(\d+)$')


def accepted(key: dict, prop: dict) -> bool:
    m = CLAIM.match(prop["claim"])
    if not m:
        return False
    q, where = m.group(1), m.group(3)
    for a in key["answers"].get(q, []):
        f = a["file"]
        if (where == f or (f.endswith("/") and where.startswith(f))) and a.get("says", "") in prop["data"]:  # fmt: skip
            return True
    return False


def cmd_decide(table: Path) -> int:
    who, box = who_of(table), box_of(table)
    keyfile = HERE / f"{who}.json"
    if not keyfile.is_file():
        return fail(
            f"{who} has no answer key beside this ({keyfile.name}): only they can decide"
        )
    key = json.loads(keyfile.read_text(encoding="utf-8"))
    now = today_of(who)
    sealed = declined = 0
    for subj, prop in waiting(box):
        verb = "seal" if accepted(key, prop) else "decline"
        got = py(ROOT / "kernel.py", verb, "--box", box, "--now", now, subj)
        if got.returncode not in (0, 42):
            return fail(f"{verb} {subj}: {got.stderr.strip()}")
        sealed, declined = (
            (sealed + 1, declined) if verb == "seal" else (sealed, declined + 1)
        )
    print(
        f"{who} sealed {sealed} answers and declined {declined}, with the key made for them."
    )
    return kernel.ALIVE


def cmd_recap(table: Path) -> int:
    who, box = who_of(table), box_of(table)
    rows, _ = kernel.read(box / "record.jsonl")
    verdict = {
        r["subject"]: r["kind"] for r in rows if r["kind"] in ("seal", "decline")
    }
    by_q: dict[int, dict] = {}
    for r in rows:
        if r["kind"] == "proposal" and r.get("verdict") == "pass":
            prop = json.loads((box / "proposals" / f"{r['subject'][9:]}.json").read_text(encoding="utf-8"))  # fmt: skip
            m = CLAIM.match(prop["claim"])
            if m:
                q = by_q.setdefault(int(m.group(1)), {"q": m.group(2), "seal": [], "decline": [], "wait": []})  # fmt: skip
                q[verdict.get(r["subject"], "wait")].append(
                    f"{m.group(3)}:{m.group(4)}"
                )
    asked = questions(who)
    print(f"# What {who} made true\n")
    for i, q in enumerate(asked, 1):
        got = by_q.get(i)
        if got is None:
            print(f"{i:>2}. {q}\n      nothing in the life holds it")
            continue
        line = f"{i:>2}. {q}\n"
        line += "".join(f"      sealed    {w}\n" for w in got["seal"])
        line += "".join(f"      declined  {w}\n" for w in got["decline"])
        line += "".join(f"      waiting   {w}\n" for w in got["wait"])
        print(line, end="")
    answered = sum(1 for g in by_q.values() if g["seal"])
    print(f"\n{answered} of {len(asked)} questions have an answer {who} sealed.")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--who", "--table"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if len(args) == 1 else ""
    if verb not in ("open", "week", "ask", "decide", "recap") or not opts.get("--table") or (verb == "open") != bool(opts.get("--who")):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    table = Path(opts["--table"])
    if verb == "open":
        return cmd_open(opts["--who"], table)
    if not (table / "who.txt").is_file():
        return fail(f"{table} isn't a life box laid by open")
    return {"week": cmd_week, "ask": cmd_ask, "decide": cmd_decide, "recap": cmd_recap}[
        verb
    ](table)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
