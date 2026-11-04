"""sort.py: your files sorted into your own categories, by the phrases you
gave each. Python 3.9+, stdlib only.

    python adapters/stdlib/sort/sort.py --box DIR --categories FILE [--json]

FILE is yours: one category a line, its name, a colon, and the phrases that
mean it, commas between. Lines beginning # are notes.

    money:  invoice, receipt, bank statement
    health: prescription, appointment, blood test

Each file the kernel reads is sorted by its passages: a phrase counts where
its words come in order, each word matched as the kernel matches (its own
words and stems, so "invoices" is "invoice"). A file goes to the category
whose phrases it holds most; one that holds two categories as much is said
as both, for you to choose; one that holds none is unsorted. Nothing is
guessed: what a phrase doesn't reach stays unsorted, for a person, or a
model's suggestion that a person seals, to place.
A file whose category you sealed (a sort-ask suggestion, kept on your
record) goes where your seal says, before any phrase, "sealed by you".

    sort: populated, 4 files: 2 sorted into 2 categories, 1 in more than one, 1 unsorted
    ## health
      letters/clinic.txt  2 hits: appointment, prescription
    ## money
      bank/may.txt        3 hits: bank statement 2, invoice
    ## more than one
      notes/june.md       money 1, health 1
    ## unsorted
      ideas.md            no phrase of yours

It prints a report, as every report add-on does (adapters/stdlib/ci/README.md,
the report contract), and `--json` gives the same report as one JSON object.

It only reads: the box's pile, through the kernel's own `chunks`, and FILE.
Exit codes, the kernel's: 0 every file sorted (populated) or none to sort
(empty); 42 a file is in more than one or unsorted, which waits on you; 2
refused (a bad command line, no box, a FILE with no category in it).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NAME = "sort"


def tokens(text: str) -> list[str]:
    """Words as the kernel matches them: its words, each stemmed."""
    return [kernel.stem(w) for w in kernel.words(text)]


def categories(text: str) -> dict[str, list[tuple[str, list[str]]]]:
    """FILE's categories in its order: each name and its phrases, each phrase
    as written and as tokens. A line with no colon, or no phrase, is left out."""
    out: dict[str, list[tuple[str, list[str]]]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        name, _, said = line.partition(":")
        phrases = [(p.strip(), tokens(p)) for p in said.split(",") if tokens(p)]
        if name.strip() and phrases:
            out.setdefault(name.strip(), []).extend(phrases)
    return out


def hits(words: list[str], phrase: list[str]) -> int:
    """How many times the phrase's words come in order in `words`."""
    n = len(phrase)
    return sum(1 for i in range(len(words) - n + 1) if words[i : i + n] == phrase)


def sort(pile: list[dict], cats: dict) -> dict[str, dict[str, dict[str, int]]]:
    """Each file: each category it holds, and each phrase's hits in it."""
    found: dict[str, dict[str, dict[str, int]]] = {}
    for c in pile:
        ws = tokens(c["text"])
        here = found.setdefault(c["path"], {})
        for name, phrases in cats.items():
            for said, toks in phrases:
                if k := hits(ws, toks):
                    here.setdefault(name, {})[said] = (
                        here.get(name, {}).get(said, 0) + k
                    )
    return found


def labels(box: Path) -> dict[str, str]:
    """The category the person sealed for each file, by its place: a sealed
    suggestion under sort/<the file>.txt (sort-ask's), while its proof and
    its proposal's bytes still hold. A seal is the correction kept."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return {}
    out = {}
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, _, why = kernel.standing(box, rows, subj, row)
        p = prop.get("path", "") if prop and why is None else ""
        if p.startswith("sort/") and p.endswith(".txt"):
            out[p[5:-4]] = prop["data"].strip()
    return out


def placed(
    found: dict, order: list[str], sealed: dict | None = None
) -> tuple[dict, list, list]:
    """(category: [(file, its hits)]), files in more than one, files unsorted."""
    by = {n: [] for n in order}
    more, none = [], []
    for path in sorted(found):
        held = found[path]
        if (sealed or {}).get(path) in by:  # your seal, before any phrase
            by[sealed[path]].append((path, "sealed by you"))
            continue
        if not held:
            none.append((path, "no phrase of yours"))
            continue
        totals = {n: sum(held[n].values()) for n in held}
        top = max(totals.values())
        best = [n for n in order if totals.get(n) == top]
        if len(best) > 1:
            more.append((path, ", ".join(f"{n} {totals[n]}" for n in best)))
            continue
        said = held[best[0]]
        by[best[0]].append(
            (
                path,
                f"{top} hit{'s' if top != 1 else ''}: "
                + ", ".join(
                    f"{p} {k}" if k > 1 else p
                    for p, k in sorted(said.items(), key=lambda x: (-x[1], x[0]))
                ),
            )
        )
    return by, more, none


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


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    opts = dict(zip(argv[::2], argv[1::2]))
    if len(argv) != 4 or sorted(opts) != ["--box", "--categories"]:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        cats = categories(Path(opts["--categories"]).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        print(f"refused: can't read {opts['--categories']}", file=sys.stderr)
        return kernel.REFUSED
    if not cats:
        print(
            "refused: no category in it: a line is `name: phrase, phrase`",
            file=sys.stderr,
        )
        return kernel.REFUSED
    found = sort(kernel.chunks(Path(kernel.config(box)["pile"])), cats)
    if not found:
        say(report(NAME, "empty", "no file here the kernel reads", []), as_json)
        return kernel.ALIVE
    by, more, none = placed(found, list(cats), labels(box))
    n = sum(len(r) for r in by.values())
    used = sum(1 for r in by.values() if r)
    said = (
        f"{len(found)} file{'s' if len(found) != 1 else ''}: {n} sorted into "
        f"{used} categor{'ies' if used != 1 else 'y'}"
    )
    said += f", {len(more)} in more than one" if more else ""
    said += f", {len(none)} unsorted" if none else ""
    groups = [(name, rows) for name, rows in by.items()]
    groups += [("more than one", more), ("unsorted", none)]
    say(report(NAME, "populated", said, groups), as_json)
    return kernel.ESCALATE if more or none else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
