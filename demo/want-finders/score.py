"""demo/want-finders/score.py: the ways into willow's add-on cards, scored on
wants whose right card was written down before any finder was asked.

    python demo/want-finders/score.py run --box DIR [--dry] [--json]

The finders, each given one want at a time and taken at its word:

    suggest  the forge add-on's `suggest`: the Forge's keyword scan over card
             names and the lines of ui/search-words.txt (needs forge-play
             0.10 or newer; without it the finder is unreachable)
    similar  similar's `near`: the kernel's own search over each card's line
    canvas   the canvas's search: BM25 over each whole card, a card you named
             first, then a card a word of yours usually means. It lives on
             ui/canvas.py's Canvas, made here without a stack, which the
             search doesn't read

A finder's offer is the add-on names it gives, in its own order, the first
`TOP` of them. For suggest that is its steps, then each fork's options, then
its ideas, as its report lists them.

The hit rule: a want with right cards hits at k when one of them is among the
first k offered; a want whose `right` is empty hits when nothing is offered.
The rules scored, for each finder:

    R1  hits at 1, over the wants with right cards
    R5  hits at TOP, over the same wants
    R0  the wants with no right card that were offered nothing

Each finder's three verdicts are rows on DIR's record (kind `verdict`, rule
`want-finders:R1:suggest` and so on), each with the SHA-256 of wants.json and
of the files the finder ran. An unreachable finder's rows say so and count no
hit: unreachable never reads as a pass. `--dry` asks nonsense in place of
every want, names its rows `want-finders:dry:...`, and is how the wiring was
checked before the freeze.

It prints each want's offers and ranks, then the scores; `--json` the same as
one object. Exit codes, the kernel's: 0 scored; 2 refused (DIR is not a box,
its record doesn't verify, or wants.json doesn't hold together).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

TOP = 5
WANTS = HERE / "wants.json"
SUGGEST = ROOT / "adapters/deps/forge/suggest.py"
SIMILAR = ROOT / "adapters/stdlib/similar/similar.py"
CANVAS = ROOT / "ui/canvas.py"
WORDS = ROOT / "ui/search-words.txt"
RULES = ("R1", "R5", "R0")
#: the files each finder runs on, hashed onto its verdicts
SOURCES = {
    "suggest": (SUGGEST, WORDS),
    "similar": (SIMILAR,),
    "canvas": (CANVAS, WORDS, SIMILAR),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_wants(path: Path = WANTS) -> list[dict]:
    """The wants, or ValueError naming what doesn't hold."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    wants = doc.get("wants")
    if not isinstance(wants, list) or not wants:
        raise ValueError("wants.json holds no wants")
    ids = set()
    for w in wants:
        if not (isinstance(w.get("id"), str) and isinstance(w.get("want"), str)):
            raise ValueError(f"a want without an id or words: {w!r}")
        if not w["want"].strip() or w["id"] in ids:
            raise ValueError(f"{w['id']}: empty, or its id used twice")
        right = w.get("right")
        if not (isinstance(right, list) and all(isinstance(r, str) for r in right)):
            raise ValueError(f"{w['id']}: right is not a list of names")
        ids.add(w["id"])
    return wants


def hits(offered: list[str], right: list[str], k: int) -> bool:
    """The hit rule: a right card among the first k offered, or, with no
    right card, nothing offered at all."""
    if not right:
        return not offered
    return any(n in right for n in offered[:k])


def rank(offered: list[str], right: list[str]) -> int | None:
    return next((i for i, n in enumerate(offered, 1) if n in right), None)


# ── the finders: the names offered, or None when the finder can't run ───────
def by_suggest(want: str, box: Path) -> list[str] | None:
    got = subprocess.run(
        [sys.executable, str(SUGGEST), "suggest", want, "--box", str(box), "--json"],
        capture_output=True,
        text=True,
    )
    if got.returncode == kernel.REFUSED:
        raise RuntimeError(f"suggest refused: {got.stderr.strip()}")
    doc = json.loads(got.stdout)
    if doc["state"] == "unreachable":
        return None
    return offers(doc)


def offers(doc: dict) -> list[str]:
    """The add-ons a suggest report offers, in its order: its steps, each
    fork's options, its ideas; never a stale seal's path."""
    out = []
    for g in doc["groups"]:
        name = g["name"] or ""
        if name in ("steps", "ideas") or name.startswith("fork "):
            for r in g["rows"]:
                card = r["what"].split(":", 1)[0]
                if card not in out:
                    out.append(card)
    return out[:TOP]


class Similar:
    def __init__(self):
        self.mod = load(SIMILAR, "want_finders_similar")
        self.every = self.mod.entries()

    def __call__(self, want: str, box: Path) -> list[str]:
        return [a["name"] for a, _ in self.mod.near(self.every, want)][:TOP]


class Canvas:
    def __init__(self):
        sys.path.insert(0, str(CANVAS.parent))
        mod = load(CANVAS, "want_finders_canvas")
        c = mod.Canvas.__new__(mod.Canvas)  # search reads no stack
        c.willow, c._search = ROOT, None
        c.similar = c._load_similar()
        self.c = c

    def __call__(self, want: str, box: Path) -> list[str]:
        return [f["name"] for f in self.c.search(want, top=TOP)["found"]]


def finders() -> dict:
    return {"suggest": by_suggest, "similar": Similar(), "canvas": Canvas()}


def nonsense(i: int) -> str:
    return f"qqqq zzzz xv{i:02d} kkwq"


def tally(wants: list[dict], offered: dict[str, list[str]], k: int) -> dict:
    hit = [w["id"] for w in wants if hits(offered[w["id"]], w["right"], k)]
    missed = [w["id"] for w in wants if w["id"] not in hit]
    return {"state": "scored", "hits": len(hit), "of": len(wants), "missed": missed}


def score(box: Path, wants: list[dict], dry: bool) -> dict:
    found: dict[str, list[dict] | None] = {}
    for name, find in finders().items():
        rows: list[dict] | None = []
        for i, w in enumerate(wants, 1):
            offered = find(nonsense(i) if dry else w["want"], box)
            if offered is None:
                rows = None
                break
            rows.append(
                {"id": w["id"], "offered": offered, "rank": rank(offered, w["right"])}
            )
        found[name] = rows
    scores = {}
    with_right = [w for w in wants if w["right"]]
    with_none = [w for w in wants if not w["right"]]
    for name, rows in found.items():
        if rows is None:
            scores[name] = {r: {"state": "unreachable", "hits": 0} for r in RULES}
            continue
        offered = {f["id"]: f["offered"] for f in rows}
        scores[name] = {
            "R1": tally(with_right, offered, 1),
            "R5": tally(with_right, offered, TOP),
            "R0": tally(with_none, offered, TOP),
        }
    return {"dry": dry, "found": found, "scores": scores}


def record(box: Path, out: dict) -> list[dict]:
    """One verdict row per finder and rule, on the box's chain."""
    ts = kernel.now()
    wants_sha = sha(WANTS)
    rows = []
    for name, by_rule in out["scores"].items():
        sources = {p.relative_to(ROOT).as_posix(): sha(p) for p in SOURCES[name]}
        for rule, v in by_rule.items():
            tag = f"want-finders:{'dry:' if out['dry'] else ''}{rule}:{name}"
            fields = dict(rule=tag, wants_sha256=wants_sha, sources=sources, **v)
            rows.append(
                kernel.append(box, ts, "verdict", who="demo:want-finders", **fields)
            )
    return rows


def text(wants: list[dict], out: dict) -> str:
    lines = []
    for w in wants:
        lines.append(f"{w['id']}  {'(nonsense)' if out['dry'] else w['want']}")
        lines.append(f"      right: {', '.join(w['right']) or '(no card here)'}")
        for name, rows in out["found"].items():
            got = next((f for f in rows or [] if f["id"] == w["id"]), None)
            if got is None:
                lines.append(f"      {name:<8} unreachable")
                continue
            at = f"rank {got['rank']}" if got["rank"] else "-"
            said = ", ".join(got["offered"]) or "(nothing)"
            lines.append(f"      {name:<8} {at:<7} {said}")
    lines.append("")
    for name, by_rule in out["scores"].items():
        bits = [
            f"{rule} {v['hits']}/{v['of']}"
            if v["state"] == "scored"
            else f"{rule} unreachable"
            for rule, v in by_rule.items()
        ]
        lines.append(f"{name:<8} " + "  ".join(bits))
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="score.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="verb", required=True)
    r = sub.add_parser("run")
    r.add_argument("--box", required=True)
    r.add_argument("--dry", action="store_true")
    r.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    box = Path(a.box)
    if not (box / "kernel.json").is_file():
        print(f"refused: {box} is not a box", file=sys.stderr)
        return kernel.REFUSED
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify: " + "; ".join(breaks), file=sys.stderr
        )
        return kernel.REFUSED
    try:
        wants = read_wants()
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    out = score(box, wants, a.dry)
    out["rows"] = [row["n"] for row in record(box, out)]
    print(json.dumps(out, indent=1) if a.json else text(wants, out))
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
