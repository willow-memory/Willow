"""digest.py: one page of what your folder needs from you. Python 3.9+.

    python adapters/stdlib/digest/digest.py --box DIR [--days N] [--now TS]

Four sections, each in one of three states, never collapsed: something to
show, nothing (said as nothing), or couldn't look (said with why):

    Waiting for you     suggestions passed the kernel's door, not yet approved
    Gone stale          approved answers whose cited passage changed or went
                        (the stale add-on's check)
    Coming up           dates in your files in the next N days, 14 unless
                        --days says (the coming-up add-on's)
    Asked again         questions asked more than once that your folder
                        never answered: counted, not shown, since the record
                        keeps no words; a words list may help

It writes nothing, not even the row `kernel.py out` appends, so the record's
tip doesn't move while you read it (willow-bot's `peek`, the morning screen's
NEEDS YOU, read-only). A section whose add-on was deleted says so and the
rest still show.

Exit codes, the kernel's: 0 nothing waits on you; 42 a suggestion waits, or
an approval went stale; 2 refused (a record that doesn't verify, a bad
command line).
"""

from __future__ import annotations

import json
import sys
import types
from datetime import date
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

POPULATED, EMPTY, UNREACHABLE = "populated", "empty", "unreachable"


def sibling(folder: str, module: str):
    """Another add-on's module, or None when its folder was deleted."""
    path = STDLIB / folder / f"{module}.py"
    if not path.is_file():
        return None
    mod = types.ModuleType(f"digest_{module}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def section(items: list, why: str = "") -> dict:
    if why:
        return {"state": UNREACHABLE, "why": why, "items": []}
    return {"state": POPULATED if items else EMPTY, "items": items}


def waiting(box: Path, rows: list[dict]) -> dict:
    done = {**kernel.sealed(box, rows), **kernel.declined(box, rows)}
    items = []
    for r in rows:
        subj = r.get("subject", "")
        if r["kind"] == "proposal" and r.get("verdict") == "pass" and subj not in done:
            try:
                prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
            except (OSError, ValueError):
                prop = {"data": "", "claim": "its file in the box couldn't be read"}
            items.append({"subject": subj, "answer": prop.get("data", ""),
                          "why": prop.get("claim", "")})  # fmt: skip
    return section(items)


def gone_stale(box: Path) -> dict:
    stale = sibling("stale", "stale")
    if stale is None:
        return section([], "the stale add-on isn't here")
    _, entries = stale.check(box)
    return section([e for e in entries if e.get("gone")])


def coming_up(box: Path, today: date, days: int) -> dict:
    cu = sibling("coming-up", "coming_up")
    if cu is None:
        return section([], "the coming-up add-on isn't here")
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    return section([{"date": d.isoformat(), "where": where, "line": line}
                    for d, where, line in cu.coming(pile, today, days)])  # fmt: skip


def asked_again(rows: list[dict]) -> dict:
    """Questions (by fingerprint) asked twice or more, never served an
    answer and never answered by an approval."""
    asked: dict[str, int] = {}
    answered = set()
    for r in rows:
        if r["kind"] != "bite":
            continue
        k = r.get("bite_key", "")
        asked[k] = asked.get(k, 0) + 1
        if r.get("answered_by") or any(not s.get("echo") for s in r.get("served", [])):
            answered.add(k)
    return section(sorted(n for k, n in asked.items() if n > 1 and k not in answered))


def digest(box: Path, today: date, days: int = 14) -> dict:
    """The four sections, or {"refused": why} for a record that doesn't verify."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return {"refused": "; ".join(breaks)}
    return {
        "waiting": waiting(box, rows),
        "stale": gone_stale(box),
        "coming": coming_up(box, today, days),
        "again": asked_again(rows),
    }


def code_of(doc: dict) -> int:
    if "refused" in doc:
        return kernel.REFUSED
    needs = doc["waiting"]["items"] or doc["stale"]["items"]
    return kernel.ESCALATE if needs else kernel.ALIVE


def short(text: str, n: int = 100) -> str:
    one = " ".join(str(text).split())
    return one if len(one) <= n else one[: n - 1] + "…"


def render(doc: dict, days: int) -> str:
    out = []

    def head(title: str, s: dict, nothing: str) -> bool:
        out.append(f"{title}\n")
        if s["state"] == UNREACHABLE:
            out.append(f"  couldn't look: {s['why']}\n")
        elif s["state"] == EMPTY:
            out.append(f"  {nothing}\n")
        return s["state"] == POPULATED

    if head("Waiting for you", doc["waiting"], "Nothing is waiting for your approval."):
        for w in doc["waiting"]["items"]:
            out.append(f"  {short(w['answer'])}\n    why: {short(w['why'])}\n"
                       f"    approve: python kernel.py seal --box BOX {w['subject']}\n")  # fmt: skip
    if head("Gone stale", doc["stale"], "Every approved answer's sources still hold."):
        for e in doc["stale"]["items"]:
            places = ", ".join(g["was"] for g in e["gone"])
            out.append(
                f"  {short(e['data'])}\n    its source changed or went: {places}\n"
            )
    if head(
        f"Coming up (next {days} days)", doc["coming"], "Nothing dated in that window."
    ):
        for c in doc["coming"]["items"]:
            out.append(f"  {c['date']}  {c['where']}  {short(c['line'])}\n")
    if head("Asked again", doc["again"], "No question has gone unanswered twice."):
        n = len(doc["again"]["items"])
        out.append(f"  {n} question{'s' if n > 1 else ''} asked more than once still "
                   "found nothing. Your files may call it something else: a words "
                   "list (adapters/stdlib/starter-words) teaches it your words.\n")  # fmt: skip
    return "\n".join(out)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--days", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    days = opts.get("--days", "14")
    if not opts.get("--box") or args or not days.isdigit():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    try:
        today = date(int(ts[:4]), int(ts[5:7]), int(ts[8:10]))
    except ValueError:
        print(f"refused: --now {ts!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    doc = digest(box, today, int(days))
    if "refused" in doc:
        print(f"refused: {doc['refused']}", file=sys.stderr)
        return kernel.REFUSED
    print(render(doc, int(days)), end="")
    return code_of(doc)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
