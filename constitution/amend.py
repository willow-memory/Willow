#!/usr/bin/env python3
"""amend.py — how an amendment enters CONSTITUTION.md, and the check that
holds it there.

The constitution is never closed (CONST-VIII-4). Each amendment is a file in
constitution/amendments/, numbered 0001, 0002, ..., and each one makes the
next draft: 0.9 was the last draft that came from willows-grove, so the first
amendment here makes 0.10. A pull request that amends the law carries the
amendment file and the law's new text together; merging it is what enters
it. Nothing writes to the law after the merge.

`write` fills in what follows from the amendment files: the draft number at
the top of the law, a row in its Amendment History, and a step in its draft
lineage. The clause text itself is written by hand, in its article and in the
amendment file, and `check` holds the two together.

`check` refuses:

  * any change to the Preamble or Article 0, which are fixed: Article 0 is
    beyond the reach of any amendment (CONST-VIII-3);
  * an amendment that names an Article 0 clause;
  * an amendment file that doesn't hold together: a field missing, a number
    out of order, a draft that isn't the next one, a supersession of one
    that doesn't come before it;
  * an amendment whose clause text isn't in the law word for word, unless a
    later amendment has superseded it, or whose history row is missing: an
    amendment takes effect only upon recording (CONST-VIII-1);
  * a history row, a lineage step or a draft number that isn't the one the
    amendment files make, and any edit to the rows that came before them.

That every clause an amendment adds or changes is enforced, cited by code
and attacked by a test, is checked by test_docs.py, beside the rest of the
law's coverage.

What it can't see: an amendment file deleted along with its row, its
lineage step and its draft number, which leaves a law that holds together.
Git keeps every amendment that was merged, and review is what catches one
taken out.

    python constitution/amend.py check
    python constitution/amend.py write
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAW = ROOT / "CONSTITUTION.md"
AMENDMENTS = ROOT / "constitution" / "amendments"

#: the draft that came from willows-grove; the first amendment makes the next
BASE = "0.9"
#: the parts no amendment may change (CONST-VIII-3), and the record before
#: the first amendment here, which is kept, never edited: sha256 of each
FIXED = {
    "the Preamble": "3d493fc7302a50fedfae2c6c6356ac01d3987e90676040267ef7cc293bbe3833",
    "Article 0": "3c423235f1effde273cfe221bef0b67af5f3b8d9c72c8674e50f48e3f5b71016",
}
BASE_ROWS = "f7bf1e2b42b34e94fba13d815a005de595879d872b070878b01cf797f02089df"
BASE_LINEAGE = "d1441e2c3193d58307d1d18af81ab6b3045d2a3666c0a1a40dfae8e778979205"

FIELDS = ("draft", "date", "pr", "articles", "clauses", "summary")
HEADER = re.compile(r"\A<!-- willow-amendment\n(.*?)\n-->\n(.*)\Z", re.S)
DRAFT_LINE = re.compile(r"^> Draft (\d+\.\d+)\. ", re.M)
TRACE = re.compile(r"CONST-(?:0|[IVX]+)-[0-9A-Za-z]+")
CLAUSE = re.compile(r"\*\*§?(0|[IVX]+)\.([0-9A-Za-z]+)\s")


class Refused(Exception):
    """The law and its amendments don't hold together."""


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def section(text: str, heading: str) -> str:
    """From the `## heading` line up to the next `## ` line."""
    out: list[str] = []
    for line in text.split("\n"):
        if line.startswith("## "):
            if out:
                break
            if not line.startswith(heading):
                continue
        if out or line.startswith(heading):
            out.append(line)
    return "\n".join(out)


def history(text: str) -> list[str]:
    """The Amendment History's rows, below its header and separator."""
    rows = section(text, "## Amendment History").split("\n")
    sep = next((i for i, r in enumerate(rows) if r.startswith("|---")), None)
    if sep is None:
        raise Refused("CONSTITUTION.md has no Amendment History table")
    out = []
    for r in rows[sep + 1 :]:
        if not r.startswith("|"):
            break
        out.append(r)
    return out


def lineage(text: str) -> str:
    found = [ln for ln in text.split("\n") if ln.startswith("*Draft lineage:")]
    if len(found) != 1:
        raise Refused("CONSTITUTION.md needs one '*Draft lineage:' line")
    return found[0]


def next_draft(draft: str) -> str:
    major, minor = draft.split(".")
    return f"{major}.{int(minor) + 1}"


def amendments(folder: Path = None) -> list[dict]:
    """Each amendment file, read and checked, in order."""
    folder = folder or AMENDMENTS
    out: list[dict] = []
    files = sorted(folder.glob("*.md")) if folder.is_dir() else []
    for i, path in enumerate(files, 1):
        name = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        if path.stem != f"{i:04d}":
            raise Refused(f"{name}: amendments are numbered 0001, 0002, ... in turn; this one should be {i:04d}.md")  # fmt: skip
        m = HEADER.match(path.read_text(encoding="utf-8"))
        if not m:
            raise Refused(f"{name}: doesn't open with a willow-amendment header")
        head = dict(ln.split(": ", 1) for ln in m.group(1).split("\n") if ": " in ln)
        missing = [f for f in FIELDS if not head.get(f)]
        if missing:
            raise Refused(f"{name}: missing {', '.join(missing)}")
        want = next_draft(out[-1]["draft"] if out else BASE)
        if head["draft"] != want:
            raise Refused(f"{name}: makes draft {head['draft']}, but the next draft is {want}")  # fmt: skip
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", head["date"]):
            raise Refused(f"{name}: date is YYYY-MM-DD")
        if "→" in head["summary"] or "|" in head["summary"]:
            raise Refused(f"{name}: a summary goes in a table row and the lineage, so it has no | or →")  # fmt: skip
        if not head["pr"].isdigit():
            raise Refused(f"{name}: pr is the pull request's number")
        clauses = [c.strip() for c in head["clauses"].split(",")]
        if not all(TRACE.fullmatch(c) for c in clauses):
            raise Refused(f"{name}: clauses are Trace IDs, like CONST-VIII-4")
        # CONST-VIII-3: Article 0 is beyond the reach of any amendment
        if any(c.split("-")[1] == "0" for c in clauses):
            raise Refused(f"{name}: names an Article 0 clause; Article 0 is beyond reach (VIII.3)")  # fmt: skip
        body = m.group(2).strip()
        named = [f"CONST-{a}-{b}" for a, b in CLAUSE.findall(body)]
        if sorted(named) != sorted(clauses):
            raise Refused(f"{name}: its text holds {named or 'no clause'}, but it names {clauses}")  # fmt: skip
        supersedes = [s.strip() for s in head.get("supersedes", "").split(",") if s.strip()]  # fmt: skip
        if not all(re.fullmatch(r"\d{4}", s) and int(s) < i for s in supersedes):
            raise Refused(f"{name}: supersedes only amendments before it, by number")
        out.append({**head, "n": i, "name": str(name), "clauses": clauses,
                    "body": body, "supersedes": supersedes})  # fmt: skip
    gone = {s for a in out for s in a["supersedes"]}
    for a in out:
        a["live"] = f"{a['n']:04d}" not in gone
    return out


def row(a: dict) -> str:
    return (f"| {a['date']} | {a['articles']} | Draft {a['draft']} — {a['summary']} "
            f"| *draft — by merge of #{a['pr']}* |")  # fmt: skip


def build(text: str, every: list[dict]) -> str:
    """The law with its draft number, history rows and lineage made from the
    amendment files. Everything else is left as it is."""
    latest = every[-1]["draft"] if every else BASE
    if not DRAFT_LINE.search(text):
        raise Refused("CONSTITUTION.md needs a '> Draft N.N. ' line at the top")
    text = DRAFT_LINE.sub(f"> Draft {latest}. ", text, count=1)
    rows = history(text)
    base = [r for r in rows if "*draft — by merge of #" not in r]
    new = [row(a) for a in every]
    text = text.replace("\n".join(rows), "\n".join(base + new), 1)
    line = lineage(text)
    steps = "".join(f" → {a['draft']} ({a['summary']})" for a in every)
    return text.replace(line, _base_lineage(line)[:-2] + steps + ".*", 1)


def _after(a: str, b: str) -> bool:
    return tuple(map(int, a.split("."))) > tuple(map(int, b.split(".")))


def problems(text: str = None, folder: Path = None) -> list[str]:
    text = LAW.read_text(encoding="utf-8") if text is None else text
    out: list[str] = []
    # CONST-VIII-3: the Preamble and Article 0 are fixed
    for part, digest in FIXED.items():
        heading = "## Preamble" if part == "the Preamble" else "## Article 0 "
        if sha(section(text, heading)) != digest:
            out.append(f"{part} has changed; it is fixed, and beyond the reach of any amendment (VIII.3)")  # fmt: skip
    try:
        every = amendments(folder)
    except Refused as why:
        return out + [str(why)]
    # CONST-VIII-1: an amendment takes effect only upon recording, its text
    # in the law and its row in the history
    for a in every:
        if a["live"] and a["body"] not in text:
            out.append(f"{a['name']}: its text isn't in CONSTITUTION.md word for word")
    try:
        rows = history(text)
        base = [r for r in rows if "*draft — by merge of #" not in r]
        if sha("\n".join(base)) != BASE_ROWS:
            out.append("the Amendment History's rows before the first amendment here were edited; they are kept as they are")  # fmt: skip
        line = lineage(text)
        if sha(_base_lineage(line)) != BASE_LINEAGE:
            out.append("the draft lineage up to 0.9 was edited; it is kept as it is")
        if build(text, every) != text:
            out.append("the draft number, history rows or lineage aren't what the amendments make: run python constitution/amend.py write")  # fmt: skip
    except Refused as why:
        out.append(str(why))
    return out


def _base_lineage(line: str) -> str:
    """The lineage line as it stood at BASE: our steps taken off."""
    head = line.rstrip("*").rstrip(".")
    while True:
        m = re.search(r" → (\d+\.\d+) \((?:(?! → ).)*\)$", head)
        if not m or not _after(m.group(1), BASE):
            break
        head = head[: m.start()]
    return head + ".*"


def main(argv: list[str]) -> int:
    if argv not in (["check"], ["write"]):
        print(__doc__.strip().splitlines()[-2].strip(), file=sys.stderr)
        print("usage: amend.py check | write", file=sys.stderr)
        return 2
    text = LAW.read_text(encoding="utf-8")
    if argv == ["write"]:
        try:
            LAW.write_text(build(text, amendments()), encoding="utf-8")
        except Refused as why:
            print(f"refused: {why}")
            return 2
        text = LAW.read_text(encoding="utf-8")
    found = problems(text)
    for p in found:
        print(f"refused: {p}")
    if found:
        return 2
    n = len(amendments())
    print(f"the law holds: draft {amendments()[-1]['draft'] if n else BASE}, {n} amendment{'s' * (n != 1)}")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
