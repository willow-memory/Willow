"""kept_clash.py: sealed answers other people sent you, read side by side.

    python adapters/stdlib/kept-clash/kept_clash.py PATH [PATH ...]

Each PATH is a package someone sent you (a file), or a folder of them (every
.pkg file under it). Each package that `share check` says holds has its
answers read: the text, the reason, the passages it cites, and the key of the
one who sent it. Two answers from different packages (or two of one package)
that say the same thing about a date, a time or an amount, but give a
different one, are shown side by side, and so are two that define the same
word as different kinds of thing. Neither is picked.

    DATE    integration, day, began
            package:395adab752a3… key 8f81cbe42a8d…  2026-06-12  ...
            package:9a04ad57e06f… key 4d5d8190b177…  2026-06-19  ...

It only reads. It never reads a key, never writes a seal, writes nothing,
and goes nowhere: a kept answer is its sender's seal, never yours.

Exit codes, the kernel's: 0 found some; 42 none; 2 refused.
"""

from __future__ import annotations

import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "share"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "contradictions"))
import contradictions  # noqa: E402
import share  # noqa: E402

USAGE = (
    "usage: kept_clash.py PATH [PATH ...]   (a package file, or a folder of .pkg files)"
)
#: a clock time: 9:05, 09:05, 9:05pm, 9pm. One digit run either side of the colon
TIME = re.compile(
    r"(?<![\d:.])(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s?(?P<ap>[ap]m)\b(?!\d)"
    r"|(?<![\d:.])(?P<h2>[01]?\d|2[0-3]):(?P<m2>[0-5]\d)(?![\d:])",
    re.I,
)
SENTENCE = re.compile(r"(?<=[.!?])\s+")
#: "An operator is a process that ...": a word defined as a kind of thing
DEFINE = re.compile(
    r"^\W*(?:(?:an?|the)\s+)?(?P<term>[a-z][\w'-]*(?:\s+[a-z][\w'-]*){0,2}?)"
    r"\s+(?:is|are|means|refers to)\s+(?:an?|the)\s+(?P<rest>.+)$",
    re.I,
)
#: where a definition's kind of thing ends: "a person who ...", "a process of ..."
ENDS = set(
    "who whom whose that which of for in on with to where when from by and or at as".split()
)
FIELD = contradictions.FIELD


def clock(m: re.Match) -> str | None:
    """A time as 24-hour HH:MM, or None for one that isn't a time of day."""
    h = int(m["h"] or m["h2"])
    mins = int(m["m"] or m["m2"] or 0)
    if m["ap"]:
        if not 1 <= h <= 12:
            return None
        h = h % 12 + (12 if m["ap"].lower() == "pm" else 0)
    return f"{h:02d}:{mins:02d}" if h < 24 and mins < 60 else None


def facts(text: str) -> dict:
    """What one sentence states: its one date, its one time, an amount per
    unit, and its words. Two different dates (or times) is no one date."""
    times = {t for m in TIME.finditer(text) if (t := clock(m))}
    bare = TIME.sub(" ", text)
    toks = [t for t in bare.split() if t]
    dates = {d for t in toks if (d := kernel.newest(t))}
    rest = " ".join(t for t in toks if not kernel.newest(t))
    words = contradictions.subject(text)
    return {
        "date": contradictions.day(dates.copy().pop()) if len(dates) == 1 else "",
        "time": times.copy().pop() if len(times) == 1 else "",
        "amounts": contradictions.amounts(rest),
        "words": words,
        "stems": {kernel.stem(w) for w in words},
    }


def kind_of(text: str) -> tuple[tuple[str, ...], set[str]] | None:
    """(the word defined, the kind of thing it's said to be) from a sentence
    like "An operator is a process that ...", else None."""
    m = DEFINE.match(text.strip())
    if not m:
        return None
    term = tuple(
        sorted(
            kernel.stem(w) for w in kernel.words(m["term"]) if w not in kernel.FUNCTION
        )
    )
    kind: set[str] = set()
    for tok in re.split(r"[\s,;:()]+", m["rest"].lower()):
        if tok in ENDS:
            break  # "a person who ...": the kind of thing is said by here
        kind |= {kernel.stem(w) for w in kernel.words(tok) if w not in kernel.FUNCTION}
    # an adjective before the noun is no other kind: "a human person" and
    # "a person" share "person", so they agree
    return (term, kind) if term and kind else None


def sentences(answer: dict) -> list[dict]:
    """The answer's text and its reason, a sentence at a time."""
    out = []
    for part, field in (("answer", "data"), ("reason", "claim")):
        for line in str(answer[field]).splitlines():
            for s in SENTENCE.split(line):
                s = s.strip()
                if not s:
                    continue
                out.append({"part": part, "text": s, **facts(s),
                            "defines": kind_of(s)})  # fmt: skip
    return out


def gather(paths: list[str]) -> tuple[list[tuple[str, Path]], str | None]:
    """Every file named, and every .pkg file under a folder named, in order;
    or why it can't."""
    found: list[tuple[str, Path]] = []
    for arg in paths:
        p = Path(arg)
        if p.is_dir():
            for f in sorted(p.rglob("*.pkg")):
                rel = f.relative_to(p)
                if f.is_file() and not any(x.startswith(".") for x in rel.parts):
                    found.append((f"{arg.rstrip('/')}/{rel.as_posix()}", f))
        elif p.is_file():
            found.append((arg, p))
        else:
            return [], f"{arg} is not a file or a folder"
    return found, None


def read(files: list[tuple[str, Path]]) -> tuple[list[dict], list[str]]:
    """The packages that hold, and a line for each that is left out."""
    held, left, seen = [], [], set()
    for label, f in files:
        pkg, why = share.read_package(f)
        if why:
            left.append(f"{label}: left out, {why}")
            continue
        found = share.problems(pkg)
        pid = share.package_id(pkg)
        if found:
            left.append(f"{pid[:20]}… ({label}): left out, does not hold")
            left += [f"  {p}" for p in found]
        elif pid not in seen:
            seen.add(pid)
            held.append({"id": pid, "pkg": pkg, "label": label})
    held.sort(key=lambda h: h["id"])
    return held, left


def answers_of(held: list[dict]) -> tuple[list[dict], list[str]]:
    """Each distinct answer a package holds at its core, with its sender; and
    the packages a kept package says it replaces, left out."""
    replaced = {
        layer["replaces"]
        for h in held
        for layer in share.layers(h["pkg"])
        if layer["replaces"]
    }
    out, gone, once = [], [], set()
    for h in held:
        chain = share.layers(h["pkg"])
        if any(share.package_id(layer) in replaced for layer in chain):
            gone.append(h["id"])
            continue
        core = chain[-1]
        for a in core["answers"]:
            sid = (core["from"], kernel.subject_of(a))
            if sid in once:
                continue
            once.add(sid)
            out.append({
                "pkg": h["id"], "from": core["from"], "hops": len(chain) - 1,
                "ts": core["ts"], "text": a["data"], "why": a["claim"],
                "cites": [a["places"].get(c) or c[:12] for c in a["cites"]],
                "lines": sentences(a), "n": len(out),
            })  # fmt: skip
    return out, gone


def clashes(found: list[dict]) -> tuple[list[dict], int]:
    """Each pair of sentences from two answers that say the same thing (the
    rule `contradictions` states: two words and half the shorter's) and give
    a different date, time or amount of one unit, or define the same word as
    unlike kinds of thing; and how many pairs were left alone as a form's
    field, a subject said in the same words on `FIELD` sentences or more."""
    flat = [(a, s) for a in found for s in a["lines"]]
    said: dict[frozenset, int] = {}
    for _, s in flat:
        said[frozenset(s["stems"])] = said.get(frozenset(s["stems"]), 0) + 1
    out, fields = [], 0
    for i, (a, x) in enumerate(flat):
        for b, y in flat[i + 1 :]:
            if a["n"] == b["n"]:
                continue
            about = [
                w for w in x["words"] if kernel.stem(w) in y["stems"]
            ]  # what they share
            sides = [(a, x), (b, y)]
            if x["defines"] and y["defines"] and x["defines"][0] == y["defines"][0]:
                if x["defines"][1].isdisjoint(y["defines"][1]):
                    term = ", ".join(x["defines"][0])
                    out.append({"kind": "WORD", "about": [term], "sides": sides,
                                "vals": [_kind(x), _kind(y)]})  # fmt: skip
                continue
            if not contradictions.same(x, y):
                continue
            if FIELD <= max(said[frozenset(x["stems"])], said[frozenset(y["stems"])]):
                fields += 1
                continue
            for k in ("date", "time"):
                if x[k] and y[k] and x[k] != y[k]:
                    out.append({"kind": k.upper(), "about": about, "sides": sides,
                                "vals": [x[k], y[k]]})  # fmt: skip
            for u in sorted(x["amounts"].keys() & y["amounts"].keys()):
                (vx, wx), (vy, wy) = x["amounts"][u], y["amounts"][u]
                if Decimal(vx).normalize() != Decimal(vy).normalize():
                    out.append({"kind": "AMOUNT", "about": about, "sides": sides,
                                "vals": [wx, wy]})  # fmt: skip
    return out, fields


def _kind(s: dict) -> str:
    """The kind of thing a defining sentence says, as it was written."""
    m = DEFINE.match(s["text"])
    return " ".join(m["rest"].split()[:3]).rstrip(".,;:") if m else ""


def show(x: dict) -> list[str]:
    where = [f"{a['pkg'][:20]}… key {a['from'][:12]}…" for a, _ in x["sides"]]
    w = max(map(len, where))
    v = max(len(val) for val in x["vals"])
    rows = [f"{x['kind']:<7} {', '.join(x['about'])}"]
    for (a, s), at, val in zip(x["sides"], where, x["vals"]):
        rows.append(f"{'':<7} {at:<{w}}  {val:<{v}}  ({s['part']}) {s['text'][:100]}")
    return rows


def list_answers(found: list[dict]) -> None:
    for a in found:
        via = (
            f", forwarded {a['hops']} time{'s' * (a['hops'] != 1)}" if a["hops"] else ""
        )
        print(f"{a['pkg']}  from key {a['from']}{via}, {a['ts']}")
        print(f"  answer: {a['text']}")
        print(f"    why: {a['why']}")
        for c in a["cites"]:
            print(f"    cites {c}")


def main(argv: list[str]) -> int:
    if not argv or any(a.startswith("-") for a in argv):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    files, why = gather(argv)
    if why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    if not files:
        print("No packages in what you gave: no .pkg file there.")
        return kernel.ESCALATE
    held, left = read(files)
    found, gone = answers_of(held)
    if found:
        list_answers(found)
    for line in left:
        print(line)
    for g in gone:
        print(f"{g[:20]}…: left out, a package you kept replaces it")
    read_ = (
        f"{len(files)} package{'s' * (len(files) != 1)} given, {len(held)} hold, "
        f"{len(found)} answer{'s' * (len(found) != 1)} read"
    )
    if not found:
        print(f"Nothing to set side by side: no answer to read; {read_}.")
        return kernel.ESCALATE
    pairs, fields = clashes(found)
    if fields:
        read_ += f", {fields} pair{'s' * (fields != 1)} in a form's field left alone"
    tail = "a kept answer is its sender's seal, never yours."
    if not pairs:
        print(f"No two answers saying the same thing disagree; {read_}; {tail}")
        return kernel.ESCALATE
    for x in pairs:
        print("\n".join(show(x)))
    n = len(pairs)
    print(f"{n} disagreement{'s' * (n != 1)}, {read_}; neither side is picked; {tail}")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
