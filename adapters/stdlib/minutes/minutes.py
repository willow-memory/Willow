"""minutes.py: meeting minutes: who decided what and when, and which actions
are still open.

    python adapters/stdlib/minutes/minutes.py --box DIR [--open]

The lines of your minutes that record a decision or an action, in the order
they were made:

    decisions
      2026-03-02  board/march.md:4  Move the AGM to May.
    actions open
      2026-03-02  board/march.md:6  Ana  Send the figures  (due 2026-03-09)
    actions closed
      2026-03-02  board/march.md:7  (no owner)  Book the hall
    1 decision, 1 open action, 1 closed

**A decision** is a line that opens with Decision, Decided, Agreed or
Resolved. **An action** opens with Action (or Action item), AI or Todo.
Bullets, numbering, bold marks and a checkbox in front are ignored, so
"- **Action:** Ana to send the figures" is read.

**Its owner** is what the line says up front: "@ana", "(Ana)", "Ana to send",
"Ana will send", or "Ana: send". A line that names no one is "(no owner)";
none is guessed. A date it says ("by 2026-03-09") is its due date.

**Open or closed.** An action is closed when its own line says done,
completed, closed or finished, or has a checked box [x]; or when a later line
(in any file, on its day or after) opens with "Done" and says the same words
as the action. Anything else is open. Nothing is chased or reminded.

A line that shouts throughout, such as a calendar's ACTION:DISPLAY, is a
machine's and is never read. A line's day is the latest date it says before any "by", "due", "before" or
"until" (a due date is not the day of the meeting), else the nearest date
written above it in its file, else the date its file is named for; a line no
day reaches is left out. `--open` shows only the open actions. It only reads. Exit codes,
the kernel's: 0 something found; 42 no decision or action; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "habits"))
import habits  # noqa: E402
import kernel  # noqa: E402

DECISION = re.compile(
    r"(?:decisions?|decided|agreed|resolved)\b\s*[:\-–]?\s*(.+)", re.I
)
ACTION = re.compile(r"(?:action(?: items?)?|actions|ai|todo)\b\s*[:\-–]?\s*(.+)", re.I)
DONE_LINE = re.compile(r"done\b\s*[:\-–]?\s*(.+)", re.I)
CLOSED = re.compile(r"\b(?:done|completed|closed|finished)\b", re.I)
NAME = r"([A-Z][\w'’-]*(?: [A-Z][\w'’-]*)?)"
OWNERS = (
    re.compile(r"@(\w+)\b[\s:,\-–]*(.*)"),
    re.compile(r"\(([^)]{1,30})\)[\s:,\-–]*(.*)"),
    re.compile(NAME + r" (?:to|will|should|must|can)\s+(.*)"),
    re.compile(NAME + r"\s*[:\-–]\s+(.*)"),
)
NO_OWNER = "(no owner)"
DUE = re.compile(
    r"\b(?:by|due|before|until)\b.*", re.I
)  # a due date is not the meeting's day


def entries(pile: list[dict]) -> list[tuple[str, str, int, str]]:
    """(day, path, line number, text) for each line a day reaches: the latest
    date it says, else the nearest above it in its file, else its file's name."""
    out = []
    for path, rows in habits.file_lines(pile).items():
        above, filed = "", kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(DUE.sub("", line))
            if said:
                above = said
            day = said or above or filed
            if day and line.strip():
                out.append((day, path, n, line.strip()))
    return out


def clean(line: str) -> tuple[str, bool]:
    """(the line without its bullet, numbering, emphasis and checkbox, whether
    the checkbox was ticked)."""
    text = re.sub(r"[*_]{1,2}", "", line)
    text = re.sub(r"^[\s>\-•#]*(?:\d+[.)]\s+)?", "", text)
    box = re.match(r"\[([ xX])\]\s*", text)
    if box:
        text = text[box.end() :]
    return text.strip(), bool(box and box.group(1) in "xX")


def owner_of(text: str) -> tuple[str, str]:
    """(who, what) of an action's text; who is NO_OWNER when it names no one."""
    for rx in OWNERS:
        m = rx.match(text)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    return NO_OWNER, text


def read(pile: list[dict]) -> dict:
    """{'decisions': [...], 'open': [...], 'closed': [...]}, each a dict of day, where, who, what, due."""
    decisions, actions, dones = [], [], []
    for day, path, n, line in entries(pile):
        text, ticked = clean(line)
        if not any(c.islower() for c in text):
            continue  # a machine's line (a calendar's ACTION:DISPLAY), not yours
        where = f"{path}:{n}"
        if m := DONE_LINE.match(text):
            dones.append((day, tuple(kernel.words(m.group(1)))))
        elif m := DECISION.match(text):
            decisions.append({"day": day, "where": where, "what": m.group(1).strip()})
        elif m := ACTION.match(text):
            who, what = owner_of(m.group(1).strip())
            said = tuple(kernel.words(m.group(1)))
            due = kernel.newest(what) or ""
            actions.append(
                {
                    "day": day,
                    "where": where,
                    "who": who,
                    "what": what,
                    "due": due,
                    "closed": ticked or bool(CLOSED.search(what)),
                    "said": said,
                }  # fmt: skip
            )
    for a in actions:
        if not a["closed"] and any(d >= a["day"] and w == a["said"] for d, w in dones):
            a["closed"] = True
    return {
        "decisions": decisions,
        "open": [a for a in actions if not a["closed"]],
        "closed": [a for a in actions if a["closed"]],
    }


def dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def action_line(a: dict) -> str:
    due = f"  (due {dash(a['due'])})" if a["due"] else ""
    return f"  {dash(a['day'])}  {a['where']}  {a['who']}  {a['what']}{due}"


def show(got: dict, only_open: bool) -> list[str]:
    out = []
    if not only_open:
        out.append("decisions")
        out += [
            f"  {dash(d['day'])}  {d['where']}  {d['what']}" for d in got["decisions"]
        ]
    out.append("actions open")
    out += [action_line(a) for a in got["open"]]
    if not only_open:
        out.append("actions closed")
        out += [action_line(a) for a in got["closed"]]
    d, o, c = len(got["decisions"]), len(got["open"]), len(got["closed"])
    out.append(
        f"{d} decision{'s' if d != 1 else ''}, {o} open action{'s' if o != 1 else ''}, {c} closed"
    )
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        elif a == "--open":
            opts[a] = "1"
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    got = read(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not (got["decisions"] or got["open"] or got["closed"]):
        print("No line of your folder records a decision or an action.")
        return kernel.ESCALATE
    print("\n".join(show(got, "--open" in opts)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
