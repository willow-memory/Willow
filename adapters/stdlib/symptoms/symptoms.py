"""symptoms.py: one symptom's diary from your files, ready to show a doctor.

    python adapters/stdlib/symptoms/symptoms.py --box DIR "knee" [--json]

Every line of your folder that names the symptom, oldest first, each dated,
its turn marked where the line says one, and cited, so a doctor can see the
course of it and check any line against your files:

    symptoms: populated, 3 lines name "knee", 2026-03-01 to 2026-03-09: 1 worse, 1 better, 1 scored
    ## 2026-03
      Daily/2026-03-01.md:4  2026-03-01  worse   Knee bad on the stairs. Voltaren and a hot pack.
      Daily/2026-03-04.md:2  2026-03-04  better  Walked the lake loop, 6.2km, knee held up.
      Health/physio.md:7     2026-03-09  5/10    Physio: knee pain 5/10 after the stairs test.

It prints a report (ci/README.md, "The report contract"): each line is a row,
its place and then its date, turn and words, in groups by month, the undated
last; `--json` prints the same report as one JSON object.

You name the symptom with words, as a question is asked: "knee", "lower
back", "migraine". A line counts when it itself holds every one of your
content words, each read the kernel's way (your words list, and a word's
plain form). The line has to say it: a folder named knee/ holds the word for
asking, but writes no diary line.

**A turn is marked only where the line says one.** Worse is worse,
worsening, bad, badly, flare, flared, flaring, swollen, agony or worst;
better is better, easing, eased, improved, improving, settled, fine, or
held up. A line saying both is marked mixed, and a score the line gives as
N/10 is shown as written. Nothing is averaged, trended or diagnosed: the
course of it is yours and your doctor's to read.

A line's date is the latest it says, read as the kernel reads one (its
`newest`), else the nearest date written above it in its file, else the date
its file is named for, and the diary says which; undated lines come last.
The whole story of a matter, passages and all, written to a file to hand
over, is the timeline add-on's job; this is the quick dated diary of one
symptom's own lines.

It only reads. Exit codes, the kernel's: 0 the symptom is named somewhere (populated) or
nowhere (empty); 42 only common words were asked, which it can't look for
(unreachable); 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WORSE = re.compile(
    r"\b(?:worse|worsening|bad|badly|flares?|flared|flaring|swollen|agony|worst)\b",
    re.IGNORECASE,
)
BETTER = re.compile(
    r"\b(?:better|easing|eased|improved|improving|settled|fine|held up)\b",
    re.IGNORECASE,
)
SCORE = re.compile(r"\b(\d{1,2})\s*/\s*10\b")


NAME = "symptoms"


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


def turn_of(line: str) -> str:
    """The turn the line says: worse, better, mixed when it says both, a
    score it gives as N/10, or nothing."""
    worse, better = bool(WORSE.search(line)), bool(BETTER.search(line))
    score = SCORE.search(line)
    if worse and better:
        return "mixed"
    if worse:
        return "worse"
    if better:
        return "better"
    return f"{score.group(1)}/10" if score else ""


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def diary(pile: list[dict], want: set[str], alias: dict) -> list[dict]:
    """A row per line that itself holds every word of `want` (the kernel's
    `held_by`: the words list, and a word's plain form), dated by the line,
    the nearest date above it in its file, or its file's name, each saying
    so; dated rows oldest first, undated after, by file and line."""
    out = []
    for path, rows in file_lines(pile).items():
        above, filed = None, kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            toks = kernel.forms(kernel.words(line))
            if all(kernel.held_by(w, toks, alias) for w in want):
                if said:
                    when, note = said, ""
                elif above:
                    when, note = above[0], f"date from line {above[1]}"
                elif filed:
                    when, note = filed, "date from file name"
                else:
                    when, note = "", ""
                out.append({"when": when, "note": note, "turn": turn_of(line),
                            "path": path, "line": n, "text": line.strip()})  # fmt: skip
            if said:
                above = (said, n)
    return sorted(out, key=lambda r: (r["when"] == "", r["when"], r["path"], r["line"]))


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def show(asked: str, rows: list[dict]) -> list[str]:
    wt = max(len(r["turn"]) for r in rows)
    wp = max(len(f"{r['path']}:{r['line']}") for r in rows)
    out = []
    for r in rows:
        where = f"{r['path']}:{r['line']}"
        tail = f"  ({r['note']})" if r["note"] else ""
        out.append(f"{day(r['when']):<10}  {r['turn']:<{wt}}  {r['text'][:90]:<90}"
                   f"  {where:<{wp}}{tail}")  # fmt: skip
    dated = [r["when"] for r in rows if r["when"]]
    span = f", {day(dated[0])} to {day(dated[-1])}" if dated else ""
    worse = sum(r["turn"] == "worse" for r in rows)
    better = sum(r["turn"] == "better" for r in rows)
    scored = sum(r["turn"].endswith("/10") for r in rows)
    one = len(rows) == 1
    out.append(f'{len(rows)} line{"" if one else "s"} name{"s" if one else ""}'
               f' "{asked}"{span}: {worse} worse, {better} better, {scored} scored')  # fmt: skip
    return out


def groups_of(rows: list[dict]) -> list[tuple]:
    """The diary's rows (where, what) grouped by the month they are dated,
    in the diary's order, the undated last."""
    wt = max(len(r["turn"]) for r in rows)
    out: dict = {}
    for r in rows:
        month = f"{r['when'][:4]}-{r['when'][4:6]}" if r["when"] else "undated"
        note = f"  ({r['note']})" if r["note"] else ""
        what = f"{day(r['when']):<10}  {r['turn']:<{wt}}  {r['text'][:90]}{note}"
        out.setdefault(month, []).append((f"{r['path']}:{r['line']}", what))
    return list(out.items())


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) != 1 or args[0].startswith("-"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias: dict = {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    want = set(kernel.words(args[0])) - kernel.FUNCTION
    if not want:
        said = f'"{args[0]}" is only common words, held by everything; say more'
        say(report(NAME, "unreachable", said, []), as_json)
        return kernel.ESCALATE
    rows = diary(kernel.chunks(Path(cfg["pile"])), want, alias)
    if not rows:
        say(
            report(NAME, "empty", f'no line of your folder names "{args[0]}"', []),
            as_json,
        )
        return kernel.ALIVE
    say(report(NAME, "populated", show(args[0], rows)[-1], groups_of(rows)), as_json)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
