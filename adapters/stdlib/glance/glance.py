"""glance.py: what a scan found, a line a question. Python 3.9+.

    python adapters/stdlib/glance/glance.py --of SCANNED --questions FILE [--words FILE] [--json]

    glance: populated, 18 questions: 4 held whole, 12 in part, 2 found nothing
    ## found nothing
      run-pause       how do I pause a task
    ## held in part
      switch-history  1 of 3, lacks open, session: plans/redesign.md:601  You are Jeles, conducting an oral history
    ## held whole
      hand-export     ui_page.py:2543  function portableCard() { const card = h("div", { class: "card" },

scan answers a list of questions in one pass, and what it prints is for a
program: a line of JSON a question, every passage whole. This is the same,
for a person: each question's best passage as one line, where it is and how
it opens, so a wrong answer is seen without opening a file.

A passage is served when it holds half a question's words, so a short
question is served by a passage holding one of two. That is where a wrong
answer comes from, and it is said here: "1 of 3, lacks open, session". The
thinnest come first. It can't tell you the answer is wrong; it shows you
the ones to look at.

SCANNED is the lines scan printed (in a stack, the earlier step's output:
`--of {01}`); FILE the questions it was asked, for their words. --words is
the words list scan was given, if it was, so a word your list reads another
way isn't said to be lacking.

It reads two or three files and writes nothing. It prints a report
(ci/README.md, "The report contract"); --json gives the same as one object.
Exit codes, the kernel's: 0 every question was served; 42 one found
nothing (that waits on you); 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: glance.py --of SCANNED --questions FILE [--words FILE] [--json]"
NAME = "glance"
#: how much of a passage's opening is shown
SHOWN = 90


def questions(text: str) -> dict[str, str]:
    """{name: question} for a questions file, as scan reads one."""
    out = {}
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, tab, q = line.partition("\t")
        out[name.strip() if tab else str(n)] = q.strip() if tab else line.strip()
    return out


def scanned(text: str) -> tuple[list[dict] | None, str]:
    """(scan's lines as rows, "") or (None, why they aren't scan's)."""
    rows = []
    for n, ln in enumerate(text.splitlines(), 1):
        if not ln.strip():
            continue
        try:
            row = json.loads(ln)
            row["question"], row["state"]
            # each passage served has a place and a text, both words
            [(s["where"] + "", s["text"] + "") for s in row["served"]]
        except (ValueError, KeyError, TypeError):
            return (
                None,
                f"line {n} has no question, state and served, as scan's lines do",
            )
        rows.append(row)
    if not rows:
        return None, "it is empty: the step before said nothing to hand on"
    return rows, ""


def want_of(question: str) -> list[str]:
    """The words that count, once each, in the order asked."""
    return list(
        dict.fromkeys(w for w in kernel.words(question) if w not in kernel.FUNCTION)
    )


def opening(text: str) -> str:
    """A passage's first words on one line."""
    flat = " ".join(text.split())
    return flat if len(flat) <= SHOWN else flat[:SHOWN].rsplit(" ", 1)[0] + "…"


def short(where: str) -> str:
    """A place by its last two folders and its line: enough to know it."""
    path, _, line = where.rpartition(":")
    return "/".join(path.split("/")[-2:]) + ":" + line


def look(rows: list[dict], asked: dict[str, str], alias: dict):
    """(found nothing, held in part, held whole): each a list of (name, what).
    In part is thinnest first: the fewest of its words held."""
    nothing, part, whole = [], [], []
    for row in rows:
        name = str(row["question"])
        q = asked.get(name, "")
        if not row["served"]:
            nothing.append((name, q or "(not in the questions file)"))
            continue
        top = row["served"][0]
        place = f"{short(top['where'])}  {opening(top['text'])}"
        want = want_of(q)
        toks = kernel.toks(
            {"text": top["text"], "path": top["where"].rpartition(":")[0]}
        )
        lacks = [w for w in want if not kernel.held_by(w, toks, alias)]
        if not want or not lacks:
            whole.append((name, place))
        else:
            held = len(want) - len(lacks)
            what = f"{held} of {len(want)}, lacks {', '.join(lacks)}: {place}"
            part.append((held / len(want), name, what))
    part.sort(key=lambda p: p[0])
    return nothing, [(n, w) for _, n, w in part], whole


def report(nothing: list, part: list, whole: list) -> dict:
    n = len(nothing) + len(part) + len(whole)
    said = f"{n} question{'s' * (n != 1)}: {len(whole)} held whole, {len(part)} in part"
    said += f", {len(nothing)} found nothing"
    groups = [("found nothing", nothing), ("held in part", part), ("held whole", whole)]
    return {
        "addon": NAME,
        "state": "populated" if n else "empty",
        "said": said,
        "groups": [
            {"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
            for g, rows in groups
            if rows
        ],
    }


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    lines = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        lines.append(f"## {g['name']}")
        lines += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    as_json = False
    it = iter(argv)
    for a in it:
        if a in ("--of", "--questions", "--words"):
            opts[a] = next(it, "")
        elif a == "--json":
            as_json = True
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
    if not opts.get("--of") or not opts.get("--questions") or opts.get("--words") == "":
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        rows, why = scanned(Path(opts["--of"]).read_text(encoding="utf-8"))
        asked = questions(Path(opts["--questions"]).read_text(encoding="utf-8"))
        alias: dict = {}
        if "--words" in opts:
            alias, bad = kernel.parse_words(
                Path(opts["--words"]).read_text(encoding="utf-8")
            )
            if bad:
                print(f"refused: {bad}", file=sys.stderr)
                return kernel.REFUSED
    except (OSError, ValueError) as e:
        print(f"refused: a file could not be read: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    if rows is None:
        print(f"refused: {opts['--of']} can't be taken: {why}", file=sys.stderr)
        return kernel.REFUSED
    nothing, part, whole = look(rows, asked, alias)
    doc = report(nothing, part, whole)
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))
    return kernel.ESCALATE if nothing else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
