"""life_box.py: the game box, with a person's life for its binder. Python 3.9+.

    python demo/life-box/life_box.py open   --who NAME --table DIR [--read] [--dates day-first|month-first]
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
- `--read` reads the life through willow's readers first, as a person
  with mail, calendars, chats, notes, spreadsheets, books and scans would:
  each reader mirrors what it reads into DIR/NAME-read, the files no reader
  took are copied beside them as they are, and the box is laid over that.
  Without it, the box is laid over the life as written, which suits a life
  of plain files; a scan or a spreadsheet is never read raw.
- `--dates day-first` (or month-first) says the order the life's dates
  are written in, which only its writer knows: the life is mirrored through
  that add-on, each date given its ISO form beside it, and the box laid over
  the mirror, so 03/11/2026 is the 3rd of November to every reader of dates.
  Without it, a date that reads both ways is left unread.
- `week` runs week.md, a week's prep over the life, at NAME's own today
  (the TODAY their make_life.py writes them at), kept in DIR/week/NNN,
  beside NNN.md, the stack as it ran.
- `ask` asks each of NAME's own questions (demo/NAME/QUESTIONS.md) and
  hands in every passage served as a suggested answer, citing it. Nothing
  is an answer yet: each waits on the seal. First the route add-on reads
  what kind each question is, and names the steps whose job that kind is
  ("has kirsty paid me yet" is money owed: debts and invoices) with the
  file the latest week kept each one's output in, kept in DIR/route.json.
  A sum over many passages is a step's to give, not one passage's.
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
ROUTE = ROOT / "adapters" / "stdlib" / "route" / "route.py"
ORDERS = {  # a folder's date order, which only its writer knows, and the add-on that marks it
    "day-first": ROOT / "adapters" / "stdlib" / "day-first" / "day_first.py",
    "month-first": ROOT / "adapters" / "stdlib" / "month-first" / "month_first.py",
}
#: The readers --read runs, each by its own command line; pdf is a deps add-on,
#: read where pypdf is installed and said to be unreachable where it isn't
STD = ROOT / "adapters" / "stdlib"
READERS = [STD / "mail" / "mail.py", STD / "calendar" / "cal.py", STD / "chats" / "chats.py",
           STD / "notes" / "notes.py", STD / "office" / "office.py", STD / "books" / "books.py",
           ROOT / "adapters" / "deps" / "pdf" / "pdf.py"]  # fmt: skip
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


def read_life(life: Path, to: Path) -> list[str]:
    """Every reader over the life into one mirror, then the files no reader
    took copied beside them; what each reader said, one line each."""
    said = []
    for script in READERS:
        got = py(script, "mirror", "--from", life, "--to", to)
        if got.returncode == 2 and ("pip install" in got.stderr or "ModuleNotFoundError" in got.stderr):  # fmt: skip
            said.append(f"{script.parent.name}: unreachable, {script.parent.name}'s package isn't installed")  # fmt: skip
        elif got.returncode == 2:
            raise ValueError(f"{script.parent.name}: {got.stderr.strip()}")
        else:
            said.append(f"{script.parent.name}: {(got.stdout.strip().splitlines() or ['read nothing'])[-1].replace(str(to), to.name)}")  # fmt: skip
    left = 0
    for f in sorted(life.rglob("*")):
        rel = f.relative_to(life)
        if f.is_file() and not any(p.startswith(".") for p in rel.parts) and not (to / f"{rel}.txt").exists():  # fmt: skip
            (to / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, to / rel)
            left += 1
    said.append(f"copied: {left} files no reader took, as they are")
    return said


def cmd_open(who: str, table: Path, dates: str = "", read: bool = False) -> int:
    if not re.fullmatch(r"[a-z][a-z-]*", who) or not (DEMO / who / "make_life.py").is_file():  # fmt: skip
        return fail(
            f"{who!r} isn't one of willow's made-up lives (demo/NAME/make_life.py)"
        )
    if not (DEMO / who / "QUESTIONS.md").is_file():
        return fail(f"demo/{who} has no QUESTIONS.md of their own")
    if dates and dates not in ORDERS:
        return fail(f"--dates is {' or '.join(ORDERS)}: the order the life's dates are written in")  # fmt: skip
    if table.exists():
        return fail(f"{table} is there already: a life box is laid in a new folder")
    table.mkdir(parents=True)
    shutil.copytree(DEMO / who, table / who, ignore=shutil.ignore_patterns("life", "__pycache__"))  # fmt: skip
    made = py(table / who / "make_life.py", cwd=table / who)
    if made.returncode != 0:
        return fail(f"{who}'s make_life.py: {made.stderr.strip()}")
    pile = table / who / "life"
    if read:
        try:
            said = read_life(pile, table / f"{who}-read")
        except ValueError as e:
            return fail(f"reading the life: {e}")
        pile = table / f"{who}-read"
        print("read:\n" + "".join(f"  {s}\n" for s in said), end="")
    if (
        dates
    ):  # each date given its ISO form beside it, so every reader of dates can place it
        marked = py(
            ORDERS[dates], "mirror", "--from", pile, "--to", table / f"{who}-{dates}"
        )
        if marked.returncode != 0:
            return fail(f"{dates}: {marked.stderr.strip()}")
        pile = table / f"{who}-{dates}"
    now = today_of(who)
    words = py(STARTER, "copy", "--to", table / "words.txt")
    if words.returncode != 0:
        return fail(f"the starter words list: {words.stderr.strip()}")
    init = py(ROOT / "kernel.py", "init", "--box", box_of(table), "--pile", pile,
              "--key", table / f"{who}.key", "--words", table / "words.txt", "--now", now)  # fmt: skip
    if init.returncode != 0:
        return fail(f"the record: {init.stderr.strip()}")
    (table / "who.txt").write_text(who + "\n", encoding="utf-8")
    files = sum(1 for p in pile.rglob("*") if p.is_file())
    print(
        f"{who}'s life is laid at {table}: {files} files, read through the starter words list,"
    )
    if dates:
        print(f"its dates read {dates}, each given its ISO form beside it by the {dates} add-on, at {pile}.")  # fmt: skip
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


def routes(table: Path, asked: list[str]) -> dict[int, dict]:
    """Each question's kind, and the steps whose job it is, with the file the
    latest week kept that step's output in: route's own reading, kept."""
    weeks = sorted((table / "week").glob("[0-9][0-9][0-9]")) if (table / "week").is_dir() else []  # fmt: skip
    qfile = table / "questions.txt"
    qfile.write_text("".join(q + "\n" for q in asked), encoding="utf-8")
    got = py(ROUTE, "--questions", qfile, *(["--run", weeks[-1]] if weeks else []), "--json")  # fmt: skip
    qfile.unlink()
    out: dict[int, dict] = {}
    for g in json.loads(got.stdout).get("groups", []) if got.stdout.strip() else []:
        kind = g["name"].rsplit(":", 1)[0]
        steps = []
        for r in g["rows"]:
            if r["where"].startswith("-> "):
                kept = r["what"].rsplit("   ", 1)[-1] if str(table) in r["what"] else ""
                steps.append({"step": r["where"][3:], "kept": str(Path(kept).relative_to(table)) if kept else ""})  # fmt: skip
            elif r["where"].isdigit():
                out[int(r["where"])] = {"kind": kind, "steps": [x for x in steps if x["step"] != "ask"]}  # fmt: skip
    (table / "route.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def sent_to(route: dict) -> str:
    return "".join(f"      see       {x['step']}: {x['kept'] or 'not in this week'}\n" for x in route.get("steps", []))  # fmt: skip


def cmd_ask(table: Path) -> int:
    who, box = who_of(table), box_of(table)
    now = today_of(who)
    handed = 0
    routed = routes(table, questions(who))
    for i, q in enumerate(questions(who), 1):
        kind = f"  ({routed[i]['kind']})" if i in routed else ""
        bite = py(ROOT / "kernel.py", "bite", "--box", box, "--now", now, q)
        served = (
            json.loads(bite.stdout).get("served", []) if bite.stdout.strip() else []
        )
        props = [json.dumps({"path": f"answers/q{i:02d}-{k}.txt", "data": s["text"], "cites": [s["id"]],
                             "claim": f"answers question {i}, \"{q}\", from {s['where']}"})  # fmt: skip
                 for k, s in enumerate(served, 1)]  # fmt: skip
        if not props:
            print(f"{i:>2}. {q}{kind}\n      nothing in the life holds it\n" + sent_to(routed.get(i, {})), end="")  # fmt: skip
            continue
        sugg = table / "suggestions.jsonl"
        sugg.write_text("\n".join(props) + "\n", encoding="utf-8")
        got = py(
            ROOT / "kernel.py", "propose", "--box", box, "--now", now, "--file", sugg
        )
        sugg.unlink()
        passed = got.stdout.count("pass ")
        handed += passed
        print(f"{i:>2}. {q}{kind}\n      {passed} suggested: " + "; ".join(s["where"] for s in served) + "\n" + sent_to(routed.get(i, {})), end="")  # fmt: skip
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
    routed = json.loads((table / "route.json").read_text(encoding="utf-8")) if (table / "route.json").is_file() else {}  # fmt: skip
    print(f"# What {who} made true\n")
    for i, q in enumerate(asked, 1):
        got = by_q.get(i)
        see = sent_to(routed.get(str(i), {}))
        if got is None:
            print(f"{i:>2}. {q}\n      nothing in the life holds it\n{see}", end="")
            continue
        line = f"{i:>2}. {q}\n"
        line += "".join(f"      sealed    {w}\n" for w in got["seal"])
        line += "".join(f"      declined  {w}\n" for w in got["decline"])
        line += "".join(f"      waiting   {w}\n" for w in got["wait"])
        print(line + see, end="")
    answered = sum(1 for g in by_q.values() if g["seal"])
    print(f"\n{answered} of {len(asked)} questions have an answer {who} sealed.")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--read":
            opts[a] = "yes"
        elif a in ("--who", "--table", "--dates"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if len(args) == 1 else ""
    if verb not in ("open", "week", "ask", "decide", "recap") or not opts.get("--table") or (verb == "open") != bool(opts.get("--who")):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    table = Path(opts["--table"])
    if verb == "open":
        return cmd_open(opts["--who"], table, opts.get("--dates", ""), "--read" in opts)
    if not (table / "who.txt").is_file():
        return fail(f"{table} isn't a life box laid by open")
    return {"week": cmd_week, "ask": cmd_ask, "decide": cmd_decide, "recap": cmd_recap}[
        verb
    ](table)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
