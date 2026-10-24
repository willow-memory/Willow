"""stack.py: one person's files through the whole of willow. Python 3.9+.

    python stack.py run   --to DIR [--life DIR] [--now TS]
    python stack.py after --to DIR [--now TS]

`run` takes the files make_life.py wrote (life/, or --life) through every layer, each
add-on run by its own command line, as a person would type it:

    read      every reader mirrors what it reads into one folder, and the
              plain files the readers leave are copied beside them
    start     start sets up the box on that folder: the kernel's init, a key
              under --to, the starter words list
    look      secrets-audit, todo, coming-up, on-this-day and xref, before
              a question is asked
    ask       every question in QUESTIONS.md through readings' bite on the
              box, and the kernel's bite on the raw files, as the earlier
              demos ran; a question nothing holds is asked again of scan's
              bm25, which only points at where to look
    hide      privacy scrubs everything served, and says what it hid
    assist    an assistant asks and suggests through mcp-lite, by the
              protocol, and can't approve
    view      again, digest and history

It stops there, waiting on the person: the seal is theirs, with their key
(`kernel.py seal`), never this script's. `after` is the rest, once they've
sealed or chosen not to: stale, export, backup, diverge (the box against its
backup), changed, session-seal, and the kernel's verify.

Everything goes under --to, which must be outside the repo; the person's
files are only read. Each step's command, exit and state go in
--to/stack.json, the record of the run.
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
LIFE = HERE / "life"
STD = ROOT / "adapters" / "stdlib"
KERNEL = ROOT / "kernel.py"
READERS = [
    STD / "mail" / "mail.py",
    STD / "calendar" / "cal.py",
    STD / "chats" / "chats.py",
    STD / "notes" / "notes.py",
    STD / "office" / "office.py",
    STD / "books" / "books.py",
    ROOT / "adapters" / "deps" / "pdf" / "pdf.py",
]
#: The kernel's exits, said for a person: 42 is what waits on them, or
#: nothing found; never a pass.
STATE = {0: "said", 42: "for you", 2: "refused"}
NOW = "2026-10-24T09:00:00Z"


class Run:
    """The steps, as they ran, kept for stack.json."""

    def __init__(self, to: Path, now: str, life: Path = LIFE):
        self.to, self.now, self.life, self.steps = to, now, life, []

    def __call__(self, part: str, script: Path, *args: str, stdin: str = "") -> str:
        name = script.parent.name if script != KERNEL else "kernel"
        if not script.is_file():
            self.steps.append({"part": part, "piece": name, "state": "unreachable",
                               "why": "not in this willow"})  # fmt: skip
            return ""
        got = subprocess.run([sys.executable, str(script), *args], input=stdin,
                             capture_output=True, text=True, cwd=ROOT)  # fmt: skip
        state = STATE.get(got.returncode, f"exit {got.returncode}")
        if "ModuleNotFoundError" in got.stderr:  # a deps add-on, not installed
            state = "unreachable"
        said = summary(name, got.stdout, got.stderr)
        self.steps.append({"part": part, "piece": name, "args": [
            a.replace(str(self.to), "<to>").replace(str(self.life), "<life>")
            .replace(str(ROOT), "<willow>")
            for a in args], "exit": got.returncode, "state": state,
            "said": said.replace(str(self.to), "<to>")[:200]})  # fmt: skip
        return got.stdout

    def show(self, part: str) -> None:
        for s in self.steps:
            if s["part"] == part:
                print(
                    f"  {s['state']:<12} {s['piece']:<14} {s.get('said') or s.get('why')}"
                )


def summary(name: str, out: str, err: str) -> str:
    """What a step said, in one line: its own summary line where it prints
    one, else how many lines it listed."""
    lines = [x for x in out.splitlines() if x.strip()]
    if name == "privacy":
        hid = json.loads(err.strip().splitlines()[-1])["withheld"]
        return "hid " + (", ".join(f"{n} {k}" for k, n in hid.items()) or "nothing")
    if name == "export":
        return (
            f"{sum(x.startswith('## ') for x in lines)} approved answers, as Markdown"
        )
    if name in ("start", "kernel", "backup", "session-seal") and lines:
        return lines[0]
    if name in ("todo", "coming-up", "on-this-day", "again", "history") and lines:
        if len(lines) == 1:
            return lines[0]
        return f"{len(lines)} lines, first: {lines[0].strip()}"
    if name == "mcp-lite":
        return "an mcp session"
    return (lines or err.strip().splitlines() or [""])[-1]


def questions() -> list[str]:
    text = (HERE / "QUESTIONS.md").read_text(encoding="utf-8")
    return [m.group(1).strip() for m in re.finditer(r"(?m)^\d+\.\s+(.+)$", text)]


def bite_doc(out: str) -> dict:
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"state": "refused"}


def read(go: Run, mirror: Path) -> None:
    for script in READERS:
        go("read", script, "mirror", "--from", str(go.life), "--to", str(mirror))
    left = 0
    for f in sorted(go.life.rglob("*")):
        rel = f.relative_to(go.life)
        if not f.is_file() or any(p.startswith(".") for p in rel.parts):
            continue
        if not (mirror / f"{rel}.txt").exists():
            (mirror / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, mirror / rel)
            left += 1
    go.steps.append({"part": "read", "piece": "copied", "state": "populated",
                     "said": f"{left} files no reader took, copied as they are"})  # fmt: skip


def ask(go: Run, box: Path, raw: Path) -> list[dict]:
    out = []
    for i, q in enumerate(questions(), 1):
        doc = bite_doc(go("ask", STD / "readings" / "readings.py", "bite", "--box",
                          str(box), "--now", go.now, q))  # fmt: skip
        was = bite_doc(go("ask", KERNEL, "bite", "--box", str(raw), "--now", go.now, q))
        out.append({
            "n": i, "question": q, "state": doc.get("state"),
            "served": [s["where"] for s in doc.get("served", []) if not s.get("echo")],
            "raw_state": was.get("state"),
            "raw_served": [s["where"] for s in was.get("served", [])
                           if not s.get("echo")],
            "text": [s["text"] for s in doc.get("served", [])],
        })  # fmt: skip
    empty = [a for a in out if a["state"] != "populated"]
    if empty:
        qs = go.to / "empty-questions.txt"
        qs.write_text("".join(f"{a['n']}\t{a['question']}\n" for a in empty))
        lines = go("ask", STD / "scan" / "scan.py", "scan", "--index",
                   str(go.to / "index"), "--questions", str(qs), "--rank", "bm25",
                   "--top", "3")  # fmt: skip
        for line in lines.splitlines():
            d = bite_doc(line)
            for a in empty:
                if str(a["n"]) == d.get("question"):
                    a["look"] = [s["where"] for s in d.get("served", [])]
    return out


def mcp(go: Run, box: Path, *calls: tuple[str, dict]) -> list[dict]:
    """One mcp-lite session: initialize, then each tool call; their results."""
    msgs = [{"jsonrpc": "2.0", "id": 0, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18"}}]  # fmt: skip
    for i, (name, args) in enumerate(calls, 1):
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                     "params": {"name": name, "arguments": args}})  # fmt: skip
    out = go("assist", STD / "mcp-lite" / "server.py", "--box", str(box),
             stdin="".join(json.dumps(m) + "\n" for m in msgs))  # fmt: skip
    return [json.loads(x)["result"] for x in out.splitlines()[1:]]


def assist(go: Run, box: Path, asked: list[dict]) -> None:
    """A stand-in assistant: asks the first question the folder answered, and
    suggests that passage's first line, citing it. Two sessions, as a client
    would: the suggestion is written once the ask's passages are read, and
    the kernel checks its cite against that ask, the last bite."""
    first = next((a for a in asked if a["state"] == "populated"), None)
    if first is None:
        go.steps.append({"part": "assist", "piece": "mcp-lite", "state": "empty",
                         "said": "no question was answered, so nothing to suggest"})  # fmt: skip
        return
    [got] = mcp(go, box, ("ask", {"question": first["question"]}))
    passage = got["structuredContent"]["served"][0]
    line = next(x for x in passage["text"].splitlines() if x.strip()).strip()
    suggested, waiting = mcp(go, box, ("suggest", {
        "path": f"answers/question-{first['n']}.md", "answer": line,
        "cites": [passage["id"]], "reason": f"the passage at {passage['where']} says it",
    }), ("waiting", {}))  # fmt: skip
    go.steps[-1]["said"] = (
        f"asked question {first['n']}, suggested a line of {passage['where']}: "
        + ("refused, " + suggested["content"][0]["text"] if suggested["isError"]
           else f"{len(waiting['structuredContent']['waiting'])} waiting")
    )  # fmt: skip
    go.steps[-1]["waiting"] = waiting["structuredContent"]["waiting"]


def run(to: Path, now: str, life: Path) -> int:
    if to.resolve().is_relative_to(ROOT):
        print("refused: --to must be outside the repo", file=sys.stderr)
        return 2
    if to.exists():
        print(f"refused: {to} already exists; give a new folder", file=sys.stderr)
        return 2
    to.mkdir(parents=True)
    go = Run(to, now, life)
    mirror = to / "pile"
    read(go, mirror)
    go("start", STD / "start" / "start.py", "--pile", str(mirror), "--to",
       str(to / "willow"))  # fmt: skip
    box = to / "willow" / "box"
    go("start", KERNEL, "init", "--box", str(to / "raw"), "--pile", str(life),
       "--key", str(to / "raw.key"), "--now", now)  # fmt: skip
    go("start", STD / "scan" / "scan.py", "index", "--from", str(mirror), "--to",
       str(to / "index"))  # fmt: skip
    for script, *more in (
        (STD / "secrets-audit" / "secrets_audit.py",),
        (STD / "todo" / "todo.py",),
        (STD / "coming-up" / "coming_up.py", "--days", "30", "--now", now),
        (STD / "on-this-day" / "on_this_day.py", "--now", now),
        (STD / "xref" / "xref.py",),
        (STD / "changed" / "changed.py", "--now", now),
    ):
        go("look", script, "--box", str(box), *more)
    asked = ask(go, box, to / "raw")
    served = "\n\n".join(t for a in asked for t in a.pop("text"))
    go("hide", STD / "privacy" / "privacy.py", "scrub", stdin=served)
    assist(go, box, asked)
    go("view", STD / "again" / "again.py", "--box", str(box))
    go("view", STD / "digest" / "digest.py", "--box", str(box), "--now", now)
    go("view", STD / "history" / "history.py", "--box", str(box))
    doc = {"now": now, "steps": go.steps, "asked": asked}
    (to / "stack.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    report(doc)
    waiting = next((s.get("waiting") for s in go.steps if "waiting" in s), [])
    print("\nWAITING ON THE PERSON")
    for w in waiting:
        print(f"  python kernel.py seal --box {box} {w}")
    print(f"  then: python {Path(__file__).name} after --to {to}")
    return 42 if waiting else 0


def after(to: Path, now: str) -> int:
    doc = json.loads((to / "stack.json").read_text(encoding="utf-8"))
    go = Run(to, now)
    box = to / "willow" / "box"
    for part, script, *more in (
        ("trust", STD / "stale" / "stale.py"),
        ("trust", STD / "export" / "export.py", "--format", "md"),
        ("trust", STD / "changed" / "changed.py", "--now", now),
        ("trust", STD / "session-seal" / "session_seal.py", "--now", now),
        ("trust", STD / "session-seal" / "session_seal.py", "check"),
        ("trust", STD / "backup" / "backup.py", "--to", str(to / "backups"),
         "--now", now),
    ):  # fmt: skip
        go(part, script, "--box", str(box), *more)
    zips = sorted((to / "backups").glob("*.zip"))
    if zips:
        go("trust", STD / "diverge" / "diverge.py", str(box), str(zips[-1]))
    go("trust", KERNEL, "verify", "--box", str(box))
    doc["after"] = go.steps
    (to / "stack.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    print("AFTER")
    go.show("trust")
    return 2 if any(s["state"] == "refused" for s in go.steps) else 0


def report(doc: dict) -> None:
    steps = Run(Path(), "")
    steps.steps = doc["steps"]
    for part in ("read", "start", "look"):
        print(part.upper())
        steps.show(part)
    print("ASK")
    for a in doc["asked"]:
        look = ", ".join(a.get("look", [])[:2])
        where = ", ".join(a["served"][:2]) or (
            f"nothing; bm25 points at {look}" if look else "nothing, anywhere"
        )
        raw = "raw: same" if a["raw_state"] == a["state"] else f"raw: {a['raw_state']}"
        print(f"  {a['n']:>2} {a['state']:<10} {a['question'][:44]:<44} {where[:70]}"
              f"  ({raw})")  # fmt: skip
    for part in ("hide", "assist", "view"):
        print(part.upper())
        steps.show(part)


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv[1:])
    for a in it:
        if a in ("--to", "--now", "--life"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if argv[:1] not in (["run"], ["after"]) or args or not opts.get("--to"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    life = Path(opts.get("--life") or LIFE)
    if argv[0] == "run" and not life.is_dir():
        print("refused: no life/ yet; run make_life.py first", file=sys.stderr)
        return 2
    to, now = Path(opts["--to"]), opts.get("--now") or NOW
    return run(to, now, life) if argv[0] == "run" else after(to, now)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
