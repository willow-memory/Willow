"""truth.py: what the pools study may say, and only from its runs. Python 3.9+.

    python demo/pools/truth/truth.py cards   --to CARDS
    python demo/pools/truth/truth.py shape   --pile PILE --name NAME --salt SALT --to SHAPE
    python demo/pools/truth/truth.py pairs   --grid MANIFEST --to MANIFEST
    python demo/pools/truth/truth.py measure --rows ROWS... --shapes SHAPE... --cards CARDS
                                             --grid MANIFEST --to RESULT
    python demo/pools/truth/truth.py report  --result RESULT --to REPORT
    python demo/pools/truth/truth.py probe   --probes PROBES --pile PILE --to RESULTS
    python demo/pools/truth/truth.py dry     --box BOX

The trace (demo/pools/trace) runs each add-on on a pile and writes one
row a step: how it ended, its report's state, its output's hash, and
the places in the pile it names, hashed with the pile's salt and taken
back through a mirror's map. This reads those rows and nothing else,
by the rules in rules.json beside it, which the study's freeze holds.

`cards` keeps what the rules read from the cards: each add-on's section,
role, the kinds of file it reads, and its line, for an idea that might
fill a gap. `shape` keeps what a pile is without its words: how many
files of each kind, and each file's salted hash with its kind, so a
cited file can be told by kind and by nothing else. `pairs` writes the
seeded pairs of steps no bridge joins, as a grid manifest the trace can
run. `measure` applies every rule. `report` writes the one report, every
claim with the rows it stands on, and nothing typed by hand. `probe`
asks a pile the known-answer questions. `dry` runs the measure on three
made-up sets of rows that it must get right, and writes each verdict as
a kernel row named study:dry, never the study's.

What fires: exit 0 or 42, not timed out, nothing the guard refused, and
a report's state "populated", or no report state and a line printed.
Empty is silence. Anything else is "refused", counted and listed, never
read as silence.

Exit codes, the kernel's: 0 done (dry: every dry run held); 42 dry: a
dry run didn't hold, so the measure can't be trusted yet; 2 refused (a
bad command line, a file that isn't there or isn't what it should be).
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

RULES = json.loads((HERE / "rules.json").read_text(encoding="utf-8"))
USAGE = __doc__.split("\n\n")[1]
HEADER = re.compile(r"\A<!-- willow-addon\n(.*?)\n-->\n", re.S)
KINDS = ("stdlib", "deps")


class Refused(Exception):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def salted(salt: str, text: str) -> str:
    """The trace's own: so a shape's hashes are the rows' hashes."""
    return sha(f"{salt}\0{text}".encode())[:16]


def row_id(row: dict) -> str:
    """A row's name in the report: the SHA-256 of its canonical JSON."""
    return sha(json.dumps(row, sort_keys=True, separators=(",", ":")).encode())[:12]


def kind_of(path: str) -> str:
    name = path.rsplit("/", 1)[-1].lower()
    return name[name.rfind(".") :] if "." in name[1:] else name


# ── cards and shapes ─────────────────────────────────────────────────────────
def cards(root: Path = ROOT) -> dict:
    """{name: {section, role, reads, line, built}} for every card and idea."""
    out = {}
    for kind in KINDS:
        for card in sorted((root / "adapters" / kind).glob("*/README.md")):
            m = HEADER.match(card.read_text(encoding="utf-8"))
            if not m:
                continue
            head = {}
            for line in m.group(1).splitlines():
                key, sep, value = line.partition(":")
                if sep:
                    head[key.strip()] = value.strip()
            out[card.parent.name] = _card(head, True)
    planned = root / "adapters" / "planned.json"
    if planned.is_file():
        for idea in json.loads(planned.read_text(encoding="utf-8")):
            out.setdefault(idea["name"], _card(idea, False))
    return dict(sorted(out.items()))


def _card(head: dict, built: bool) -> dict:
    reads = [r.strip().lower() for r in str(head.get("reads", "")).split(",")]
    reads = [r for r in reads if r and r != "none"]
    return {"section": head.get("section", ""), "role": head.get("role", ""),
            "reads": reads, "line": head.get("line", ""), "built": built}  # fmt: skip


def shape(pile: Path, name: str, salt: str) -> dict:
    """A pile without its words: kinds counted, and each file's salted
    hash with its kind. The trace's file hashes are these."""
    kinds: dict[str, int] = {}
    files = {}
    for p in sorted(x for x in pile.rglob("*") if x.is_file()):
        rel = p.relative_to(pile).as_posix()
        if any(part.startswith(".") for part in Path(rel).parts):
            continue  # the kernel skips hidden files, so the study does
        k = kind_of(rel)
        kinds[k] = kinds.get(k, 0) + 1
        files[salted(salt, rel)] = k
    return {"pile": name, "kinds": dict(sorted(kinds.items())), "files": dict(sorted(files.items()))}  # fmt: skip


def applies(card: dict, pile_kinds: dict) -> bool:
    """A card that names what it reads applies where that kind is; one
    that names none applies everywhere."""
    want = card.get("reads", [])
    return not want or any(kind_of(w) in pile_kinds for w in want)


# ── bridges ──────────────────────────────────────────────────────────────────
def bridge_map(manifest: dict) -> dict[str, set[str]]:
    """{taker: givers}: frozen in the grid's manifest from code and cards."""
    out: dict[str, set[str]] = {}
    for b in manifest.get("bridges", []):
        out.setdefault(b["to"], set()).add(b["from"])
    return out


def reached(stack: list[str], at: int, givers: dict[str, set[str]]) -> bool:
    """Whether an earlier step of the stack bridges to the step at `at`,
    directly or through earlier steps."""
    before = set(stack[:at])
    seen, todo = set(), [stack[at]]
    while todo:
        step = todo.pop()
        for g in givers.get(step, ()):
            if g in before:
                return True
            if g not in seen:
                seen.add(g)
                todo.append(g)
    return False


def no_bridge_pairs(manifest: dict, n: int, seed: int) -> list[list[str]]:
    """`n` pairs of steps, drawn by `seed`, joined by no bridge either way."""
    steps = sorted(manifest["steps"])
    givers = bridge_map(manifest)
    joined = {(g, t) for t, gs in givers.items() for g in gs}
    pool = [(a, b) for i, a in enumerate(steps) for b in steps[i + 1 :]
            if (a, b) not in joined and (b, a) not in joined]  # fmt: skip
    rnd = random.Random(seed)
    return [list(p) for p in sorted(rnd.sample(pool, min(n, len(pool))))]


def pairs_manifest(manifest: dict) -> dict:
    """The grid's manifest with its stacks replaced by the seeded pairs,
    each run in both orders, so the trace can run them as it runs any."""
    rows = []
    for a, b in no_bridge_pairs(manifest, RULES["no_bridge_pairs"], RULES["seed"]):
        for first, second in ((a, b), (b, a)):
            body = json.dumps([first, second]).encode()
            rows.append({"id": f"pair-{sha(body)[:12]}", "way": "no-bridge",
                         "why": f"no bridge joins {a} and {b}", "steps": [first, second]})  # fmt: skip
    return {**manifest, "stacks": rows, "ways": {"no-bridge": len(rows)}}


# ── the measure ──────────────────────────────────────────────────────────────
def verdict(row: dict) -> str:
    """fires, silent, or refused, by the rules' own words."""
    if row.get("timed_out") or row.get("breaches") or row.get("exit") not in (0, 42):
        return "refused"
    state = row.get("state")
    if state == "populated" or (state is None and row.get("lines", 0) > 0):
        return "fires"
    return "silent"


def tail_p(k: int, n: int, a: int, b: int) -> float:
    """P(at least k of n piles hold both, by chance), when one fires on a
    of them and the other on b: the hypergeometric tail, exactly."""
    total = math.comb(n, b)
    return sum(math.comb(a, i) * math.comb(n - a, b - i) for i in range(k, min(a, b) + 1)) / total  # fmt: skip


def bh(pvalues: dict, q: float) -> set:
    """Benjamini-Hochberg: the keys kept at false discovery rate q."""
    ranked = sorted(pvalues.items(), key=lambda kv: (kv[1], kv[0]))
    m, cut = len(ranked), 0
    for i, (_, p) in enumerate(ranked, 1):
        if p <= q * i / m:
            cut = i
    return {k for k, _ in ranked[:cut]}


def jaccard(a: dict, b: dict, piles: list[str], field: str) -> float:
    """Overlap within each pile, summed over the piles: a place hash is
    its pile's own, so two piles never share one."""
    inter = union = 0
    for p in piles:
        x, y = set(a[p][field]), set(b[p][field])
        inter, union = inter + len(x & y), union + len(x | y)
    return inter / union if union else 0.0


def measure(rows: list[dict], shapes: list[dict], cards_: dict, manifest: dict, rules: dict = RULES) -> dict:  # fmt: skip
    """Every rule, over the rows. Only built add-ons with a step can fire."""
    kinds = {s["pile"]: s["kinds"] for s in shapes}
    file_kind = {h: k for s in shapes for h, k in s["files"].items()}
    single: dict[str, dict[str, dict]] = {}
    outs: dict[tuple[str, str], set[str]] = {}
    refused = []
    for r in rows:
        if "stack" in r:
            continue
        outs.setdefault((r["step"], r["pile"]), set()).add(r["out"])
        if r["pile"] not in single.get(
            r["step"], {}
        ):  # the first run alone is the one read
            single.setdefault(r["step"], {})[r["pile"]] = {**r, "verdict": verdict(r), "id": row_id(r)}  # fmt: skip
    # what each step named on each pile, over all its runs there, alone and
    # in stacks: alone a step is never given another's mirror, so a taker
    # meets its reader's places only in a stack, through the map
    named: dict[str, dict[str, dict[str, set]]] = {}
    for r in rows:
        at = named.setdefault(r["step"], {}).setdefault(
            r["pile"], {"places": set(), "files": set()}
        )
        at["places"] |= set(r.get("places", []))
        at["files"] |= set(r.get("files", []))
    # a step whose own runs alone disagree draws at random or tells the
    # time: no stack can be held to it, so it is listed, not checked
    unsteady = sorted({s for (s, _), o in outs.items() if len(o) > 1})
    steps = sorted(single)
    piles = sorted(kinds)
    for s in steps:
        for p, r in sorted(single[s].items()):
            if r["verdict"] == "refused":
                refused.append(
                    {"step": s, "pile": p, "row": r["id"], "exit": r.get("exit")}
                )
    can = {s: [p for p in piles if p in single[s] and applies(cards_.get(s, {}), kinds[p])] for s in steps}  # fmt: skip
    fire = {s: {p for p in can[s] if single[s][p]["verdict"] == "fires"} for s in steps}
    tested, stats = {}, {}
    for i, a in enumerate(steps):
        for b in steps[i + 1 :]:
            both = sorted(set(can[a]) & set(can[b]))
            n = len(both)
            fa, fb = fire[a] & set(both), fire[b] & set(both)
            k = len(fa & fb)
            if n < rules["min_piles"] or k < rules["min_piles"]:
                continue
            on = sorted(fa & fb)
            jp = jaccard(named[a], named[b], on, "places")
            jf = jaccard(named[a], named[b], on, "files")
            tested[(a, b)] = tail_p(k, n, len(fa), len(fb))
            stats[(a, b)] = {"n": n, "k": k, "fa": len(fa), "fb": len(fb), "jp": round(jp, 4), "jf": round(jf, 4),
                             "rows": sorted(single[a][p]["id"] for p in on) + sorted(single[b][p]["id"] for p in on)}  # fmt: skip
    kept = bh(tested, rules["fdr_q"])
    pairs = []
    for key in sorted(kept):
        st = stats[key]
        if st["jp"] >= rules["pair_jaccard"]:
            level = "acts on the same thing"
        elif st["jf"] >= rules["pair_jaccard"]:
            level = "shares files"
        else:
            continue
        pairs.append({"a": key[0], "b": key[1], "p": tested[key], "level": level, **st})
    dups = []
    for (a, b), st in sorted(stats.items()):
        on = sorted(fire[a] & fire[b])
        each = [jaccard(named[a], named[b], [p], "places") for p in on]
        if (
            len(on) >= rules["min_piles"]
            and each
            and min(each) >= rules["duplicate_jaccard"]
        ):
            dups.append({"a": a, "b": b, "piles": len(on), "least": round(min(each), 4), "rows": st["rows"]})  # fmt: skip
    never = [s for s in steps if can[s] and not fire[s]]
    no_pile = [s for s in steps if not can[s]]
    cited = set()
    for r in rows:
        cited |= {file_kind[h] for h in r.get("files", []) if h in file_kind}
    present = sorted({k for ks in kinds.values() for k in ks})
    gaps = []
    for k in present:
        if k in cited:
            continue
        ideas = sorted(n for n, c in cards_.items() if not c["built"] and k.strip(".") and k.strip(".") in c["line"].lower())  # fmt: skip
        gaps.append(
            {"kind": k, "piles": sum(1 for p in piles if k in kinds[p]), "ideas": ideas}
        )
    partners: dict[str, list[dict]] = {}
    for pr in pairs:
        for me, other in ((pr["a"], pr["b"]), (pr["b"], pr["a"])):
            partners.setdefault(me, []).append({"name": other, **pr})
    order = {"acts on the same thing": 0, "shares files": 1}
    neighbours, sections = {}, []
    for s in steps:
        mine = sorted(partners.get(s, []), key=lambda x: (order[x["level"]], -x["jp"], -x["jf"], x["p"], x["name"]))  # fmt: skip
        neighbours[s] = [x["name"] for x in mine[: rules["neighbours"]]]
        here = cards_.get(s, {}).get("section", "")
        if mine:
            counts: dict[str, int] = {}
            for x in mine:
                sec = cards_.get(x["name"], {}).get("section", "")
                counts[sec] = counts.get(sec, 0) + 1
            best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
            if best[0] != here and best[1] / len(mine) >= rules["section_share"]:
                sections.append({"step": s, "section": here, "partners_in": best[0], "of": len(mine), "there": best[1]})  # fmt: skip
    order_breaks = order_check(rows, single, manifest, set(unsteady))
    level_counts = {lv: sum(1 for p in pairs if p["level"] == lv) for lv in order}
    return {"rules": sha(json.dumps(rules, sort_keys=True).encode()), "steps": len(steps), "piles": len(piles),
            "rows": len(rows), "pairs_tested": len(tested), "pairs": pairs, "levels": level_counts,
            "duplicates": dups, "never_fires": never, "no_pile": no_pile, "gaps": gaps,
            "sections": sections, "neighbours": {s: n for s, n in neighbours.items() if n},
            "no_partner": [s for s in steps if not neighbours[s]], "refused": refused,
            "order_breaks": order_breaks, "unsteady": unsteady}  # fmt: skip


def order_check(rows: list[dict], single: dict, manifest: dict, unsteady: set = frozenset()) -> list[dict]:  # fmt: skip
    """Each step in a stack that printed other than it did alone on the
    same pile, with no earlier step bridging to it: the null broken. An
    unsteady step, one that differs from itself alone, is not held."""
    givers = bridge_map(manifest)
    stacks = {s["id"]: s["steps"] for s in manifest.get("stacks", [])}
    out = []
    for r in rows:
        if "stack" not in r or r["stack"] not in stacks or r["step"] in unsteady:
            continue
        alone = single.get(r["step"], {}).get(r["pile"])
        if alone is None or alone["out"] == r["out"]:
            continue
        if not reached(stacks[r["stack"]], r["at"], givers):
            out.append({"stack": r["stack"], "step": r["step"], "pile": r["pile"], "row": row_id(r), "alone": alone["id"]})  # fmt: skip
    return sorted(out, key=lambda x: (x["stack"], x["step"], x["pile"]))


# ── the report ───────────────────────────────────────────────────────────────
def _rows(ids: list[str]) -> str:
    """A claim's rows: how many, the first six by name, and where all are."""
    more = f", and {len(ids) - 6} more, all in the result" if len(ids) > 6 else ""
    return f"{len(ids)} rows: {', '.join(ids[:6])}{more}"


def report(result: dict) -> str:
    """The one report: made only from a measure's result, every claim with
    the rows it stands on, the same bytes for the same result."""
    r = result
    out = ["# The pools study: what the runs said", "",
           f"Made by demo/pools/truth/truth.py from {r['rows']} rows: {r['steps']} steps on {r['piles']} piles, "
           f"by rules {r['rules'][:12]}. Nothing here is typed by hand; each claim names the rows it stands on.", ""]  # fmt: skip
    out += ["## What could not be trusted", ""]
    if r["order_breaks"]:
        out += [f"- {len(r['order_breaks'])} step runs in stacks printed other than alone with no bridge to them: "
                "the null is broken, and no pair below should be read until this is explained."]  # fmt: skip
        out += [f"  - `{b['step']}` in `{b['stack']}` on {b['pile']} (rows {b['row']}, alone {b['alone']})" for b in r["order_breaks"]]  # fmt: skip
    else:
        out += ["- No step printed other than alone without a bridge to it."]
    out += [f"- {len(r['refused'])} step runs were refused, timed out or breached the guard; they are neither silence nor firing."]  # fmt: skip
    out += [f"- {len(r['unsteady'])} steps print differently run alone twice, so no stack is held to them"
            + (f": {', '.join(r['unsteady'])}." if r["unsteady"] else ".")]  # fmt: skip
    out += ["", "## Pairs", "",
            f"{r['pairs_tested']} pairs fired together on at least the rules' piles; {len(r['pairs'])} held at the "
            f"false discovery rate, {r['levels'].get('acts on the same thing', 0)} acting on the same places, "
            f"{r['levels'].get('shares files', 0)} sharing only files.", ""]  # fmt: skip
    out += [f"- `{p['a']}` and `{p['b']}`: {p['level']}; both fired on {p['k']} of {p['n']} piles, p = {p['p']:.3g}, "
            f"places {p['jp']}, files {p['jf']} ({_rows(p['rows'])})"
            for p in r["pairs"]] or ["- None."]  # fmt: skip
    out += ["", "## Duplicates", ""]
    out += [f"- `{d['a']}` and `{d['b']}`: the same places on all {d['piles']} piles both fired, the least {d['least']} "
            f"({_rows(d['rows'])})" for d in r["duplicates"]] or ["- None."]  # fmt: skip
    out += ["", "## Never fired, on piles it applies to", ""]
    out += [f"- `{s}`" for s in r["never_fires"]] or ["- None."]
    out += ["", "## Had no pile it applies to", ""]
    out += [f"- `{s}`" for s in r["no_pile"]] or ["- None."]
    out += ["", "## Gaps: kinds of file no add-on named", ""]
    out += [
        f"- `{g['kind']}`, in {g['piles']} piles"
        + (
            f"; ideas whose line names it: {', '.join(g['ideas'])}"
            if g["ideas"]
            else ""
        )  # fmt: skip
        for g in r["gaps"]
    ] or ["- None."]
    out += ["", "## Sections the runs disagree with", ""]
    out += [f"- `{s['step']}` is under {s['section']}; {s['there']} of its {s['of']} partners are under {s['partners_in']}"
            for s in r["sections"]] or ["- None."]  # fmt: skip
    out += ["", "## The neighbours each card should list", ""]
    out += [f"- `{s}`: {', '.join(n)}" for s, n in sorted(r["neighbours"].items())] or [
        "- None."
    ]
    out += [
        "",
        f"No partner found for {len(r['no_partner'])} steps; their cards keep what they say.",
    ]
    return "\n".join(out) + "\n"


# ── probes ───────────────────────────────────────────────────────────────────
def probe(probes: list[dict], pile: Path) -> list[dict]:
    """Each known-answer question asked of the pile as read (a mirror's
    pages, where a reader wrote them): a hit when the kernel serves the
    place its answer is, read back through the mirror's map."""
    out = []
    for pr in probes:
        folder = pile / pr["folder"] if pr.get("folder") else pile
        served = kernel.rank(kernel.chunks(folder), pr["question"])
        hit = any(_at(folder, c["path"], c["line"]) == (pr["answer"]["file"], pr["answer"]["line"]) for c in served)  # fmt: skip
        out.append({"id": pr["id"], "gap": pr["gap"], "reader": pr["reader"], "expect": pr["expect"], "hit": hit,
                    "question": sha(pr["question"].encode())[:12]})  # fmt: skip
    return out


def _at(folder: Path, path: str, line: int) -> tuple[str, int]:
    """A served passage's place in the original: through the mirror's map
    (MIRROR/.places/<path>.json) where there is one."""
    mapped = folder / ".places" / (path + ".json")
    if mapped.is_file():
        said = json.loads(mapped.read_text(encoding="utf-8"))
        at = [int(k) for k in said.get("places", {}) if k.isdigit() and int(k) <= line]
        where = said["places"][str(max(at))] if at else ""
        m = re.match(r"lines? (\d+)", where)
        return said.get("source", path), int(m.group(1)) if m else 0
    return path, line


def probes_held(results: list[dict]) -> list[dict]:
    """Per known gap: found when most of its probes miss and every control
    of its reader hits; a control that misses means the gap can't be read."""
    controls: dict[str, list[bool]] = {}
    gaps: dict[str, list[dict]] = {}
    for r in results:
        if r["gap"] == "control":
            controls.setdefault(r["reader"], []).append(r["hit"])
        else:
            gaps.setdefault(r["gap"], []).append(r)
    out = []
    for gap, rs in sorted(gaps.items()):
        reader = rs[0]["reader"]
        ok = bool(controls.get(reader)) and all(controls[reader])
        missed = sum(1 for r in rs if not r["hit"])
        enough = len(rs) >= RULES["probes_per_gap"]
        state = (
            ("found" if missed * 2 > len(rs) else "not found")
            if ok and enough
            else "can't be read"
        )
        out.append(
            {
                "gap": gap,
                "reader": reader,
                "probes": len(rs),
                "missed": missed,
                "state": state,
            }
        )
    return out


# ── dry runs ─────────────────────────────────────────────────────────────────
def _row(step, pile, fires, places=(), files=None, **more):
    return {"pile": pile, "step": step, "exit": 0, "timed_out": False, "breaches": 0,
            "state": "populated" if fires else "empty", "lines": 3 if fires else 0,
            "out": sha(f"{step}{pile}{fires}".encode()), "places": sorted(places),
            "files": sorted(files if files is not None else places), **more}  # fmt: skip


def _shapes(rows, extra=None):
    """Each pile's shape, from the rows' own file hashes, every one a
    .md; `extra` puts a kind of file in a pile that no row names."""
    out: dict[str, dict] = {}
    for r in rows:
        sh = out.setdefault(r["pile"], {"pile": r["pile"], "kinds": {}, "files": {}})
        for h in r["files"]:
            sh["files"][h] = ".md"
    for p, k in (extra or {}).items():
        out[p]["files"][sha(f"{p}{k}".encode())[:16]] = k
    for sh in out.values():
        for k in sh["files"].values():
            sh["kinds"][k] = sh["kinds"].get(k, 0) + 1
    return [out[p] for p in sorted(out)]


def _own(n, p, many=3):
    return {sha(f"{n}{p}{j}".encode())[:16] for j in range(many)}


def dry_nonsense(
    seed: int = 1, steps: int = 30, piles: int = 20
) -> tuple[list, list, dict]:
    """Rows with no structure: each step fires at its own rate, and names
    places of its own. Any pair or duplicate found here was invented."""
    rnd = random.Random(seed)
    names = [f"n{i:02d}" for i in range(steps)]
    pnames = [f"p{i:02d}" for i in range(piles)]
    rate = {n: rnd.uniform(0.3, 0.9) for n in names}
    rows = [
        _row(n, p, rnd.random() < rate[n], _own(n, p)) for n in names for p in pnames
    ]
    cards_ = {n: _card({"section": "S"}, True) for n in names}
    return rows, _shapes(rows), cards_


def dry_planted(map_on: bool = True) -> tuple[list, list, dict]:
    """Twenty piles with four things put in: a and b fire on the same half
    and name the same places; c names exactly d's places, on the other
    half; a kind of file, .zzz, that nothing names; and a reader r whose
    pages a taker t reads, which meet only through the mirror's map. r and
    t fire on a and b's half too, so firing together alone pairs a with r:
    the places must keep them apart. x, y and z are noise."""
    rows, pnames = [], [f"p{i:02d}" for i in range(20)]
    rnd = random.Random(7)
    for i, p in enumerate(pnames):
        first, second = i < 10, i >= 10
        shared = _own("ab", p, 4)
        rows.append(_row("a", p, first, shared | _own("a", p, 1)))
        rows.append(_row("b", p, first, shared | _own("b", p, 1)))
        cd = _own("cd", p, 5)
        rows.append(_row("c", p, second, cd))
        rows.append(_row("d", p, second, cd))
        source, mirror = _own("src", p), _own("page", p)
        rows.append(_row("r", p, first, source))
        rows.append(_row("t", p, first, _own("t", p, 2)))  # alone: no mirror to read
        if first:  # after r, in its bridge stack: r's pages, through the map
            rows.append(_row("r", p, True, source, stack="r-t", at=0))
            rows.append(_row("t", p, True, (source if map_on else mirror) | _own("t", p, 2),
                             stack="r-t", at=1, out="t-after-r"))  # fmt: skip
        for n in ("x", "y", "z"):
            rows.append(_row(n, p, rnd.random() < 0.5, _own(n, p)))
    cards_ = {n: _card({"section": "S"}, True) for n in "abcdrtxyz"}
    cards_["zz-reader"] = _card({"section": "S", "line": "Reads zzz files."}, False)
    return rows, _shapes(rows, {pnames[0]: ".zzz", pnames[3]: ".zzz"}), cards_


def dry_shuffled(seed: int = 3) -> tuple[list, list, dict]:
    """The planted rows with each step's rows moved to other piles at
    random: what fired together, and what overlapped, no longer meets."""
    rows, shapes, cards_ = dry_planted()
    rnd = random.Random(seed)
    piles = sorted({r["pile"] for r in rows})
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["step"], []).append(r)
    out = []
    for step, rs in sorted(by.items()):
        moved = piles[:]
        rnd.shuffle(moved)
        out += [{**r, "pile": moved[piles.index(r["pile"])]} for r in rs]
    return out, shapes, cards_


DRY_GRID = {"steps": {}, "bridges": [{"from": "r", "to": "t", "by": ["planted"]}],
            "stacks": [{"id": "r-t", "way": "bridge", "steps": ["r", "t"]}]}  # fmt: skip


def dry(box: Path) -> int:
    """The three dry runs, each held to what it must say, written as
    kernel rows named study:dry, never the study's."""
    found = []
    m = measure(*dry_nonsense(), DRY_GRID)
    found.append(("study:dry:nonsense", not m["pairs"] and not m["duplicates"],
                  f"{len(m['pairs'])} pairs and {len(m['duplicates'])} duplicates from rows with none"))  # fmt: skip
    m = measure(*dry_planted(), DRY_GRID)
    pairs = {(p["a"], p["b"]) for p in m["pairs"]}
    want = {("a", "b"), ("c", "d"), ("r", "t")}
    ok = want <= pairs and not pairs - want and ("c", "d") in {(d["a"], d["b"]) for d in m["duplicates"]}  # fmt: skip
    ok = (
        ok
        and [g["kind"] for g in m["gaps"]] == [".zzz"]
        and m["gaps"][0]["ideas"] == ["zz-reader"]
    )
    found.append(("study:dry:planted", ok, f"pairs {sorted(pairs)}, gaps {[g['kind'] for g in m['gaps']]}"))  # fmt: skip
    off = measure(*dry_planted(map_on=False), DRY_GRID)
    lost = ("r", "t") not in {(p["a"], p["b"]) for p in off["pairs"] if p["level"] == "acts on the same thing"}  # fmt: skip
    found.append(("study:dry:map-off", lost, "with no map, the reader and its taker don't act on the same places"))  # fmt: skip
    m = measure(*dry_shuffled(), DRY_GRID)
    found.append(("study:dry:shuffled", len(m["pairs"]) <= max(1, int(RULES["fdr_q"] * max(m["pairs_tested"], 1)))
                  and not {(p["a"], p["b"]) for p in m["pairs"]} & want,
                  f"{len(m['pairs'])} pairs of {m['pairs_tested']} tested, after the piles were shuffled"))  # fmt: skip
    me = sha(Path(__file__).read_bytes())
    for rule, held, said in found:
        kernel.append(box, kernel.now(), "verdict", who="pools-truth", gate=rule,
                      verdict="pass" if held else "fail", said=said, code=me, rules=sha((HERE / "rules.json").read_bytes()))  # fmt: skip
        print(f"{rule:22} {'held' if held else 'DID NOT HOLD'}: {said}")
    return kernel.ALIVE if all(h for _, h, _ in found) else kernel.ESCALATE


# ── the command line ─────────────────────────────────────────────────────────
def _read_rows(paths: list[str]) -> list[dict]:
    out = []
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def _write(path: str, doc) -> None:
    text = (
        doc
        if isinstance(doc, str)
        else json.dumps(doc, indent=1, sort_keys=True) + "\n"
    )
    Path(path).write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    opts: dict[str, list[str]] = {}
    key = None
    for a in rest:
        if a.startswith("--"):
            key = a[2:]
            opts.setdefault(key, [])
        elif key:
            opts[key].append(a)
        else:
            key = "?"
            break
    one = {k: v[0] for k, v in opts.items() if len(v) == 1}
    need = {"cards": ["to"], "shape": ["pile", "name", "salt", "to"], "pairs": ["grid", "to"],
            "measure": ["rows", "shapes", "cards", "grid", "to"], "report": ["result", "to"],
            "probe": ["probes", "pile", "to"], "dry": ["box"]}  # fmt: skip
    if verb not in need or key == "?" or not all(opts.get(k) for k in need[verb]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        if verb == "cards":
            _write(one["to"], cards())
        elif verb == "shape":
            pile = Path(one["pile"])
            if not pile.is_dir():
                raise Refused(f"{pile} isn't a folder")
            _write(one["to"], shape(pile, one["name"], one["salt"]))
        elif verb == "pairs":
            _write(
                one["to"],
                pairs_manifest(
                    json.loads(Path(one["grid"]).read_text(encoding="utf-8"))
                ),
            )
        elif verb == "measure":
            shapes = [
                json.loads(Path(p).read_text(encoding="utf-8")) for p in opts["shapes"]
            ]
            _write(one["to"], measure(_read_rows(opts["rows"]), shapes,
                                      json.loads(Path(one["cards"]).read_text(encoding="utf-8")),
                                      json.loads(Path(one["grid"]).read_text(encoding="utf-8"))))  # fmt: skip
        elif verb == "report":
            _write(
                one["to"],
                report(json.loads(Path(one["result"]).read_text(encoding="utf-8"))),
            )
        elif verb == "probe":
            res = probe(
                json.loads(Path(one["probes"]).read_text(encoding="utf-8")),
                Path(one["pile"]),
            )
            _write(one["to"], {"probes": res, "gaps": probes_held(res)})
        else:
            box = Path(one["box"])
            if not (box / "kernel.json").is_file():
                raise Refused(
                    f"{box} isn't a kernel box; make one with kernel.py init, outside the repo"
                )
            return dry(box)
    except (OSError, ValueError, KeyError, Refused) as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
