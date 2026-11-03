"""first_mention.py: when your files first mention something, and the line.

    python adapters/stdlib/first-mention/first_mention.py --box DIR "your words" [--json]

The thing is named by words, as a question is: "mould", "knee physio",
"solar quote". A line mentions it when the line itself holds every one of
your content words, each read the kernel's way (your words list, and a
word's plain form, so "owes" is "owe"). The line has to say it: a folder
named dad/ holds the word for asking, but writes no mention.

    first-mention: populated, first mention of "mould": 2026-03-01; 48 mentions in 5 files, 2026-03-01 to 2026-09-02; 3 undated, which could be earlier
      tenancy/log.md:3  2026-03-01 Reported the mould in the back bedroom.

A line's date is the latest it says, read as the kernel reads one (its
`newest`; 11/03/2026, either way round, is never guessed); a line that says
none takes the nearest date written above it in its file, else the date its
file is named for, and the answer says which. The first mention is the
earliest dated one, ties going to the first file and line in sorted order.
Undated mentions can't be placed, so they are counted beside the answer:
your files don't say when those were, and one of them could be earlier.
When no mention is dated at all, the first by file and line is shown, and
says that.

It prints a report (ci/README.md, "The report contract"): the first line
says the answer and the count, the row is the first mention's place and
line; `--json` gives the same as one object. It only reads. States and exit
codes: populated, 0, a first mention found; empty, 0, your files never
mention it; unreachable, 42, the words are only common ones and it couldn't
look (say more); 2 refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


NAME = "first-mention"


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


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def file_lines(pile: list[dict]) -> dict[str, list[tuple[int, str]]]:
    """Each file's lines with their numbers, put back together from its
    passages (the kernel cuts a long run of lines into passages of 500)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for c in pile:
        rows = out.setdefault(c["path"], [])
        rows += [(c["line"] + i, ln) for i, ln in enumerate(c["text"].splitlines())]
    return out


def mentions(pile: list[dict], want: set[str], alias: dict) -> list[dict]:
    """A row per line that holds every word of `want` in the line's own words
    (the kernel's `held_by`: the words list, and a word's plain form), dated
    by the line, the nearest date above it in its file, or its file's name,
    each saying so. Dated rows oldest first, undated after, by file and line."""
    out = []
    for path, rows in file_lines(pile).items():
        above, src, filed = "", 0, kernel.newest(path)
        for n, line in rows:
            said = kernel.newest(line)
            toks = kernel.forms(kernel.words(line))
            if all(kernel.held_by(w, toks, alias) for w in want):
                if said:
                    when, note = said, ""
                elif above:
                    when, note = above, f"date from line {src}"
                elif filed:
                    when, note = filed, "date from file name"
                else:
                    when, note = "", ""
                out.append({"when": when, "note": note, "path": path,
                            "line": n, "text": line.strip()})  # fmt: skip
            if said:
                above, src = said, n
    return sorted(out, key=lambda r: (r["when"] == "", r["when"], r["path"], r["line"]))


def tally(found: list[dict]) -> str:
    dated = [r["when"] for r in found if r["when"]]
    files = len({r["path"] for r in found})
    n = len(found)
    head = (
        f"{n} mention{'s' if n > 1 else ''} in {files} file{'s' if files > 1 else ''}"
    )
    if not dated:
        return f"{head}, none dated"
    span = (
        day(dated[0])
        if dated[0] == dated[-1]
        else f"{day(dated[0])} to {day(dated[-1])}"
    )
    undated = n - len(dated)
    tail = f"; {undated} undated, which could be earlier" if undated else ""
    return f"{head}, {span}{tail}"


def answer(asked: str, found: list[dict]) -> str:
    first = found[0]
    when = day(first["when"])
    if not first["when"]:
        when = "undated — your files don't say when"
    note = f"  ({first['note']})" if first["note"] else ""
    return "\n".join([
        f'first mention of "{asked}": {when}{note}',
        f"  {first['path']}:{first['line']}  {first['text'][:120]}",
        tally(found),
    ])  # fmt: skip


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or len(args) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    alias = {}
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
    found = mentions(kernel.chunks(Path(cfg["pile"])), want, alias)
    if not found:
        say(report(NAME, "empty", f'your files never mention "{args[0]}"', []), as_json)
        return kernel.ALIVE
    first = found[0]
    when = day(first["when"])
    if not first["when"]:
        when = "undated; your files don't say when"
    note = f" ({first['note']})" if first["note"] else ""
    said = f'first mention of "{args[0]}": {when}{note}; {tally(found)}'
    row = (f"{first['path']}:{first['line']}", first["text"][:120])
    say(report(NAME, "populated", said, [(None, [row])]), as_json)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
