"""thesis.py: a document's claims, each against your sources, and the ones
no passage holds.

    python adapters/stdlib/thesis/thesis.py --box DIR FILE [--top N] [--json]

Every sentence of FILE is a claim. Each is put to claim-check, part by part,
against the folder the box points at. It prints a report (ci/README.md, the
report contract), the claims with no passage holding every part first:

    thesis: populated, 3 claims; 1 held, 1 short; 1 skipped
    ## short
      thesis.md:9     Gmail is read by people.  nearest: policy.txt:203 lacks scans  no file has: scans, people
    ## held
      policy.txt:12   line 4 (+1)  Google scans Gmail for ads.

A short claim is placed at its own line in FILE, with the nearest passage
(`--top`) and the parts no file has; a held one at the first passage holding
every part, with the claim's line in FILE. `--json` prints the same report as
one JSON object.

**Held is where to read, not a verdict.** A passage holding every part may
deny the claim; one holding only some may back it in other words. Only
"no file has" is a hard fact: nothing in your folder names that part.

A sentence with fewer than two parts (its words less the common ones) is not
put to the sources, only counted as skipped. Headings and code fences are
not claims. Lines are the document's own.

It only reads. Exit codes: 0 `empty` (no claim to check) or every claim has a
passage holding all its parts; 42 `populated` with some claim short, waiting
for you; 2 refused.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

CHECK = Path(__file__).resolve().parents[1] / "claim-check" / "claim_check.py"
spec = importlib.util.spec_from_file_location("willow_claim_check_for_thesis", CHECK)
claim_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claim_check)

TOP = 1
SHOWN = 70  # characters of a claim shown
END = re.compile(r"(?<=[.!?])\s+")
ABBREVIATIONS = frozenset(
    "co dr mr mrs ms st vs etc eg ie no fig approx".split()
)  # a full stop after these ends no sentence
LACKS = 8  # missing parts named for one short claim
LEAD = re.compile(r"^\s*(?:[-*+>]\s+|\d+[.)]\s+)+")


NAME = "thesis"


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


def claims(text: str) -> list[tuple[int, str]]:
    """(line, sentence) for each sentence outside headings and code fences. A
    sentence runs across the lines of a paragraph and is placed at the line
    it starts on."""
    out, para, fenced = [], [], False

    def flush() -> None:
        if not para:
            return
        flat, at = "", []  # the paragraph as one string, and each char's line
        for n, line in para:
            piece = line + " "
            flat += piece
            at += [n] * len(piece)
        start = 0
        for m in [*END.finditer(flat), None]:
            end = m.start() if m else len(flat)
            word = re.sub(r"\W", "", flat[start:end].split(" ")[-1]).lower()
            if m and word in ABBREVIATIONS and flat[end - 1] == ".":
                continue  # "Co. Clare": the stop ends no sentence
            piece = flat[start:end]
            if piece.strip():
                first = start + len(piece) - len(piece.lstrip())
                out.append((at[first], " ".join(piece.split())))
            start = m.end() if m else end
        para.clear()

    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            flush()
            fenced = not fenced
        elif fenced or not line.strip() or line.lstrip().startswith("#"):
            flush()
        elif line.startswith(("    ", "\t")) and not para:
            continue  # an indented block is code, not prose
        else:
            bullet = LEAD.match(line)
            if bullet:
                flush()
            para.append((n, LEAD.sub("", line)))
    flush()
    return out


def lacking(ws: list[str]) -> str:
    more = f" (+{len(ws) - LACKS} more)" if len(ws) > LACKS else ""
    return ", ".join(ws[:LACKS]) + more


def short(s: str) -> str:
    return s if len(s) <= SHOWN else s[: SHOWN - 1].rstrip() + "…"


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    top = TOP
    if len(argv) == 5 and argv[3] == "--top" and argv[4].isdigit() and int(argv[4]) > 0:
        top, argv = int(argv[4]), argv[:3]
    if len(argv) != 3 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, doc = Path(argv[1]), Path(argv[2])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if not doc.is_file():
        print(f"refused: {doc} is not a file", file=sys.stderr)
        return kernel.REFUSED
    if doc.stat().st_size > kernel.MAX_FILE:
        print(f"refused: {doc} is over {kernel.MAX_FILE} bytes", file=sys.stderr)
        return kernel.REFUSED
    try:
        text = doc.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        print(f"refused: {doc} is not UTF-8 text", file=sys.stderr)
        return kernel.REFUSED
    cfg, alias = kernel.config(box), {}
    if "words" in cfg:
        alias, _, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            print(f"refused: {why}", file=sys.stderr)
            return kernel.REFUSED
    pile = kernel.chunks(Path(cfg["pile"]))
    held, unheld, skipped = [], [], 0
    for line, sentence in claims(text):
        want = claim_check.parts(sentence)
        if len(want) < 2:
            skipped += 1
            continue
        got = claim_check.check(pile, want, alias, top)
        if got["all"]:
            c = got["all"][0][0]
            more = f" (+{len(got['all']) - 1})" if len(got["all"]) > 1 else ""
            held.append(
                (f"{c['path']}:{c['line']}", f"line {line}{more}  {short(sentence)}")
            )
        else:
            near = "; ".join(
                f"{c['path']}:{c['line']} lacks "
                + lacking([w for w in want if w not in h])
                for c, h in got["some"]
            )
            what = f"{short(sentence)}  nearest: {near or 'no part held'}"
            what += (f"  no file has: {', '.join(got['absent'])}" if got["absent"]
                     else "  every part is somewhere, none in one place")  # fmt: skip
            unheld.append((f"{doc}:{line}", what))
    total = len(held) + len(unheld)
    if not total:
        say(
            report(NAME, "empty", f"no claims to check; {skipped} skipped", []), as_json
        )
        return kernel.ALIVE
    said = f"{total} claims; {len(held)} held, {len(unheld)} short; {skipped} skipped"
    say(report(NAME, "populated", said, [("short", unheld), ("held", held)]), as_json)
    return kernel.ESCALATE if unheld else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
