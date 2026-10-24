"""lending.py: things you lent, to whom and when, and which are still out.

    python adapters/stdlib/lending/lending.py --box DIR

Every line of your folder that says you lent something, or got it back:
"lent the ladder to Dev", "Mara borrowed the Foxfire set (3 volumes)",
"got the drill back from Dev", "Mara gave back volumes 1 and 3". Each loan
is listed with every line about it, in the order they happened, each with
its file and line; nothing is merged away.

    PART BACK  Foxfire set  to Mara  since 2026-10-01  parts out: 2 of 3
               2026-10-01  notes/2026-10-01.md:1   Mara borrowed the Foxfire set (3 volumes).
               2026-10-24  notes/2026-10-25.md:1   2026-10-24 Mara gave back volumes 1 and 3.  (filed 2026-10-25)
    BACK       ladder  to Dev  2026-08-02 to 2026-08-30

A thing lent in parts is out until every part is back. A loan with no line
saying it came back is "no return written", which is all your files can say:
not that it wasn't returned. A line's own date and the date its file is
named for are two facts, and when they differ both are shown. A return with
no loan before it is listed too, as "back, no loan written".

It only reads. Exit codes, the kernel's: 0 found some; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WHO = r"(?P<who>[A-Z][\w'-]*)"
THING = r"(?P<thing>[^.;!?]+?)"
END = r"\s*(?=[.;!?]|$)"
#: a name is capitalised and the verb isn't, so "lent Mara the set" and
#: "lent the set to Mara" read the same loan
LENT = [
    re.compile(rf"(?i:\b(?:lent|loaned))\s+{THING}\s+(?i:to)\s+{WHO}"),
    re.compile(rf"(?i:\b(?:lent|loaned))\s+{WHO}\s+{THING}{END}"),
    re.compile(rf"{WHO}\s+(?i:borrowed)\s+{THING}{END}"),
]
BACK = [
    re.compile(rf"(?i:\b(?:got|have))\s+{THING}\s+(?i:back\s+from)\s+{WHO}"),
    re.compile(rf"{WHO}\s+(?i:returned|gave\s+back|brought\s+back)\s+{THING}{END}"),
]
LEAD = re.compile(r"^(?:the|my|a|an|her|his|their|our)\s+", re.I)
PARTS = re.compile(r"\(?\b(\d+)[\s-]*(?:vols?|volumes?|parts?|pieces?)\b\.?\)?", re.I)
NUMBERED = re.compile(r"\b(?:vols?|volumes?|parts?)\.?\s+([\d\s,&and]+)", re.I)
SKIP = {"the", "my", "a", "an", "and", "of", "set", "back", "volume", "volumes", "vol",
        "vols", "part", "parts", "piece", "pieces"}  # fmt: skip


def day(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if d else "undated"


def thing_of(raw: str) -> tuple[str, int, set[int]]:
    """(name, parts it has, parts it names): "the Foxfire set (3 volumes)" is
    a three-part thing; "volumes 1 and 3" names parts 1 and 3."""
    name = LEAD.sub("", raw.strip())
    m = PARTS.search(name)
    total = int(m.group(1)) if m else 1
    named = set()
    if n := NUMBERED.search(name):
        named = {int(x) for x in re.findall(r"\d+", n.group(1))}
        name = name[: n.start()].strip()
    if m:
        name = (name[: m.start()] + name[m.end() :]).strip()
    return LEAD.sub("", name).strip(" ,"), total, named


def key(name: str) -> set[str]:
    return {w for w in kernel.words(name.lower()) if w not in SKIP}


def lines(pile: list[dict]) -> list[dict]:
    """Every lend or return line, with its own date and its file's."""
    out = []
    for c, d in zip(pile, kernel.dates(pile)):
        filed = kernel.newest(c["path"])
        for i, text in enumerate(c["text"].splitlines()):
            for kind, pats in (("lent", LENT), ("back", BACK)):
                m = next((x for p in pats if (x := p.search(text))), None)
                if m is None:
                    continue
                name, total, named = thing_of(m.group("thing"))
                said = kernel.newest(text) or str(d or "")
                out.append({"kind": kind, "who": m.group("who"), "name": name,
                            "total": total, "named": named, "said": said,
                            "filed": filed, "where": f"{c['path']}:{c['line'] + i}",
                            "text": text.strip()})  # fmt: skip
                break
    # in the order they happened; undated after dated, in file order
    return sorted(out, key=lambda r: (r["said"] == "", r["said"], r["where"]))


def loans(found: list[dict]) -> list[dict]:
    """Returns matched to the open loan they answer: same person, and a word
    of the thing in common, or a return that names only parts."""
    out: list[dict] = []
    for r in found:
        if r["kind"] == "lent":
            out.append({"who": r["who"], "name": r["name"], "total": r["total"],
                        "back": set(), "lines": [r], "lent": True})  # fmt: skip
            continue
        open_ = [
            x for x in out
            if x["who"] == r["who"] and x["lent"] and len(x["back"]) < x["total"]
            and (key(x["name"]) & key(r["name"]) or (r["named"] and not key(r["name"])))
        ]  # fmt: skip
        if not open_:
            out.append({"who": r["who"], "name": r["name"] or "parts", "total": 1,
                        "back": {1}, "lines": [r], "lent": False})  # fmt: skip
            continue
        x = open_[-1]
        x["lines"].append(r)
        x["back"] |= r["named"] or set(range(1, x["total"] + 1))
    return out


def state(x: dict) -> str:
    if not x["lent"]:
        return "BACK?"
    if len(x["back"]) >= x["total"]:
        return "BACK"
    return "PART BACK" if x["back"] else "OUT"


def show(x: dict) -> list[str]:
    first, last = x["lines"][0], x["lines"][-1]
    head = f"{state(x):<10} {x['name']}  to {x['who']}"
    if not x["lent"]:
        head = f"{state(x):<10} {x['name']}  from {x['who']}  back, no loan written"
    elif state(x) == "BACK":
        head += f"  {day(first['said'])} to {day(last['said'])}"
    else:
        head += f"  since {day(first['said'])}"
        out_ = sorted(set(range(1, x["total"] + 1)) - x["back"])
        if x["total"] > 1:
            head += f"  parts out: {', '.join(map(str, out_))} of {x['total']}"
        if not x["back"]:
            head += "  no return written"
    rows = [head]
    for r in x["lines"]:
        both = r["filed"] and r["said"] and r["filed"] != r["said"]
        tail = f"  (filed {day(r['filed'])})" if both else ""
        rows.append(
            f"{'':<10} {day(r['said'])}  {r['where']}   {r['text'][:100]}{tail}"
        )
    return rows


ORDER = {"OUT": 0, "PART BACK": 1, "BACK?": 2, "BACK": 3}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    found = loans(lines(kernel.chunks(Path(kernel.config(box)["pile"]))))
    if not found:
        print("Nothing in your folder says you lent something or got it back.")
        return kernel.ESCALATE
    for x in sorted(
        found, key=lambda x: ORDER[state(x)]
    ):  # stable: oldest first within
        print("\n".join(show(x)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
