"""grid.py: every stack the pools study runs, written from the cards and the
command tables, never by hand, with a manifest of their hashes for the freeze.

    python demo/pools/grid/grid.py write --to DIR
    python demo/pools/grid/grid.py fill  --stack FILE --pile PILE --tmp TMP --to FILE

`write` reads, and nothing else: each add-on's card header (adapters/*/*/README.md),
COMMANDS and DEPS_COMMANDS in adapters/stdlib/ci/test_contract.py (a step for
each add-on a person runs over a box and pile), readme's week.json (each
card's `near:`), the static reading in demo/pools/static/static.json, and
plan.json beside this file (the seed and the sizes). It writes DIR/stacks/,
one stack file a row of the grid, and DIR/manifest.json: each stack's
SHA-256, its way and why it is there, the bridges, and the SHA-256 of
everything it read. Run twice over the same sources it writes the same bytes.

The ways, each a kind of row:

    single        one step alone (stage 0, the fire matrix)
    bridge        two steps, the giver first, for each bridge (stage 1)
    section       every step of a card section
    role          every step of a card role
    cell          every step of a section and a role, where there are cell_min or more
    near          a card and its near: entries, those that have steps
    leans         a card and everything its uses: reaches
    random        seeded draws of each of random_sizes, random_draws of each
    all           every step, in name order and all_shuffles running orders
    all-but-one   every step but one, for each step
    kind          a step that wrote kinds of row alone in stage 0, then each
                  reader of the record: what each kind does to each reader
                  (added after the first report, from stage 0's rows)

A stack runs its steps in the order its file lists them (stack.py goes pool
by pool, step by step; only the document it prints is sorted tallest
first), so a shuffle of the listed order is a shuffle of the running order.

A bridge is frozen here, before any run, from code and cards: B takes a kind
of record row that A writes (the static reading), or B's card names A in
uses:, looks-for: or hands:. A run tests it; a run doesn't make one.

A record bridge is the third kind, frozen the same way: a step whose code
reads the record at all (the static reading's reads_record) is reached by
any step that adds a row to it (its code writes a kind, appends one whose
kind it can't read, or asks for a bite, since the kernel writes a bite row
for each; or its own command line is a bite). It
is too wide to give each pair a stack of its own, so it is kept apart in
the manifest's record_bridges, as two lists: the null reads it as it reads
the others, and a step that changes in a stack with nothing but this to
reach it is expected, not a broken null.

Steps keep COMMANDS' `{box}`, `{pile}` and `{tmp}`, each step's `{tmp}` its
own folder under it. `fill` writes a stack for one pile: `{pile}` and `{tmp}`
filled in, each step's folder made under TMP; `{box}` is stack.py's.

Exit codes: 0 written; 2 refused (a bad command line, a source missing, DIR
not empty).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import re
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTRACT = ROOT / "adapters" / "stdlib" / "ci" / "test_contract.py"
WEEK = ROOT / "adapters" / "stdlib" / "readme" / "week.json"
STATIC = HERE.parent / "static" / "static.json"
PLAN = HERE / "plan.json"
STAGE0 = HERE.parent / "runs" / "stage0"
HEADER = re.compile(r"\A<!-- willow-addon\n(.*?)\n-->", re.S)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cards() -> dict[str, dict]:
    """Each built add-on's card header, by name."""
    out = {}
    for readme in sorted(ROOT.glob("adapters/*/*/README.md")):
        m = HEADER.match(readme.read_text(encoding="utf-8"))
        if m:
            head = dict(line.split(":", 1) for line in m[1].splitlines() if ":" in line)
            out[readme.parent.name] = {k.strip(): v.strip() for k, v in head.items()}
    return out


def names(field: str | None) -> list[str]:
    return [x.strip() for x in (field or "").split(",") if x.strip()]


def contract():
    spec = importlib.util.spec_from_file_location("contract_for_grid", CONTRACT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def steps(mod) -> dict[str, list[str]]:
    """Each add-on's step: its argv, `{tmp}` made its own folder."""
    out = {}
    for table in (mod.COMMANDS, mod.DEPS_COMMANDS):
        for name, (_, argv) in table.items():
            out[name] = [a.replace("{tmp}", "{tmp}/" + name) for a in argv]
    return dict(sorted(out.items()))


def bridges(card: dict[str, dict], static: dict, have: set[str]) -> list[dict]:
    """(giver, taker, why), each between two add-ons that have steps."""
    found = set()
    makers: dict[str, set[str]] = {}
    for name, seen in static.items():
        for kind in seen.get("writes", []):
            makers.setdefault(kind, set()).add(name)
    for name, seen in static.items():
        for kind in seen.get("takes", []):
            for maker in makers.get(kind, ()):
                if maker != name:
                    found.add((maker, name, f"record: {kind} rows"))
    for name, head in card.items():
        for field in ("uses", "looks-for", "hands"):
            for other in names(head.get(field)):
                if other != name:
                    found.add((other, name, f"card: {name}'s {field}"))
    pairs: dict[tuple[str, str], list[str]] = {}
    for a, b, why in sorted(found):
        if a in have and b in have:
            pairs.setdefault((a, b), []).append(why)
    return [{"from": a, "to": b, "by": whys} for (a, b), whys in sorted(pairs.items())]


def record_bridges(static: dict, step: dict[str, list[str]]) -> dict:
    """The record's readers and the steps that add rows to it, each with a
    step: by the static reading, or a step whose own command line bites."""
    readers = sorted(
        n for n, s in static.items() if n in step and s.get("reads_record")
    )
    givers = sorted(n for n in step if "bite" in step[n] or any(
        static.get(n, {}).get(k) for k in ("writes", "writes_unread", "bites")))  # fmt: skip
    why = "record: a reader of the record, after a step that adds rows to it"
    return {"by": why, "readers": readers, "givers": givers}


def kind_writers(stage0: Path) -> dict[str, list[str]]:
    """{writer: the kinds it wrote}: for each kind of row a step wrote alone in
    stage 0 on the public piles, the step that wrote it on the most piles
    (the first by name on a tie). Read from the committed rows, so the
    same rows give the same writers."""
    counts: dict[str, dict[str, int]] = {}
    for f in sorted(stage0.glob("*/rows-a.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            for k in r.get("rows", {}):
                counts.setdefault(k, {}).setdefault(r["step"], 0)
                counts[k][r["step"]] += 1
    out: dict[str, list[str]] = {}
    for k, c in sorted(counts.items()):
        w = sorted(c.items(), key=lambda x: (-x[1], x[0]))[0][0]
        out.setdefault(w, []).append(k)
    return out


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def stack_text(
    title: str, why: str, order: list[str], step: dict[str, list[str]]
) -> str:
    lines = [f"# {title}", "", why, "", f"## {title}"]
    lines += [f"- {n} -- {shlex.join(step[n])}" for n in order]
    return "\n".join(lines) + "\n"


def grid(
    plan: dict,
    card: dict,
    step: dict,
    near: dict,
    links: list[dict],
    writers: dict[str, list[str]] | None = None,
    readers: list[str] | None = None,
) -> list[dict]:
    """Every row: {id, way, why, steps}, steps in running order."""
    have = sorted(step)
    rows: list[dict] = []

    def add(way: str, key: str, why: str, members) -> None:
        order = [n for n in members if n in step]
        if order:
            rid = f"{way}/{key if way in ('bridge', 'kind') else slug(key)}"
            if any(r["id"] == rid for r in rows):
                raise ValueError(f"two rows are {rid}")
            rows.append({"id": rid, "way": way, "why": why, "steps": order})

    for n in have:
        add("single", n, f"{n} alone", [n])
    for b in links:
        add("bridge", f"{b['from']}--{b['to']}", f"{b['from']} then {b['to']}: {'; '.join(b['by'])}",
            [b["from"], b["to"]])  # fmt: skip
    by: dict[str, dict[str, list[str]]] = {"section": {}, "role": {}, "cell": {}}
    for n in have:
        head = card.get(n, {})
        sec, role = head.get("section", "none"), head.get("role", "none")
        by["section"].setdefault(sec, []).append(n)
        by["role"].setdefault(role, []).append(n)
        by["cell"].setdefault(f"{sec} / {role}", []).append(n)
    for way in ("section", "role", "cell"):
        for key, members in sorted(by[way].items()):
            if way != "cell" or len(members) >= plan["cell_min"]:
                add(way, key, f"every step whose card's {way} is {key}", members)
    for n in have:
        add("near", n, f"{n} and its near: entries", [n, *near.get(n, [])])
    for n in have:
        reach, todo = [], names(card.get(n, {}).get("uses"))
        while todo:
            m = todo.pop(0)
            if m not in reach and m != n:
                reach.append(m)
                todo += names(card.get(m, {}).get("uses"))
        if reach:
            add(
                "leans", n, f"{n} and everything its uses: reaches", [*sorted(reach), n]
            )
    rng = random.Random(plan["seed"])
    for size in plan["random_sizes"]:
        for k in range(plan["random_draws"]):
            pick = rng.sample(have, min(size, len(have)))
            add(
                "random",
                f"{size}-{k}",
                f"draw {k} of {size}, seed {plan['seed']}",
                pick,
            )
    add("all", "in-name-order", "every step, in name order", have)
    for k in range(plan["all_shuffles"]):
        order = list(have)
        random.Random(plan["seed"] + 1 + k).shuffle(order)
        add(
            "all",
            f"shuffle-{k}",
            f"every step, running order {k}, seed {plan['seed'] + 1 + k}",
            order,
        )
    for n in have:
        add("all-but-one", n, f"every step but {n}", [m for m in have if m != n])
    for w, kinds in sorted((writers or {}).items()):
        for r in readers or []:
            if r != w and w in step and r in step:
                add("kind", f"{w}--{r}", f"{w} writes {', '.join(kinds)} alone in stage 0; then {r} reads the record",
                    [w, r])  # fmt: skip
    return rows


def do_write(to: Path) -> int:
    if to.exists() and (not to.is_dir() or any(to.iterdir())):
        print(f"refused: {to} isn't an empty folder", file=sys.stderr)
        return 2
    missing = [p for p in (CONTRACT, WEEK, STATIC, PLAN) if not p.is_file()]
    if missing:
        print(f"refused: {missing[0]} isn't there", file=sys.stderr)
        return 2
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    card, mod = cards(), contract()
    step = steps(mod)
    near = {
        n: v.get("near", []) for n, v in json.loads(WEEK.read_text())["worked"].items()
    }
    static = json.loads(STATIC.read_text())
    links = bridges(card, static, set(step))
    record = record_bridges(static, step)
    writers = kind_writers(STAGE0)
    rows = grid(plan, card, step, near, links, writers, record["readers"])
    (to / "stacks").mkdir(parents=True)
    for row in rows:
        path = to / "stacks" / f"{row['id']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        text = stack_text(row["id"], row["why"], row["steps"], step)
        path.write_text(text, encoding="utf-8")
        row["sha256"] = sha(text.encode())
    cards_bytes = b"".join(
        p.read_bytes() for p in sorted(ROOT.glob("adapters/*/*/README.md"))
    )
    ways: dict[str, int] = {}
    for row in rows:
        ways[row["way"]] = ways.get(row["way"], 0) + 1
    manifest = {
        "sources": {"cards": sha(cards_bytes), "contract": sha(CONTRACT.read_bytes()),
                    "stage0": sha(b"".join(f.read_bytes() for f in sorted(STAGE0.glob("*/rows-a.jsonl")))),
                    "week": sha(WEEK.read_bytes()), "static": sha(STATIC.read_bytes()),
                    "plan": sha(PLAN.read_bytes()), "grid": sha(Path(__file__).read_bytes())},
        "plan": plan,
        "steps": {n: {"args": a, "card": n in card,
                      "takes_from_pile": [x for x in a if x.startswith("{pile}/")]}
                  for n, a in step.items()},
        "no_step": sorted(n for n in card if n not in step),
        "bridges": links,
        "kind_writers": writers,
        "record_bridges": record,
        "ways": ways,
        "stacks": rows,
    }  # fmt: skip
    text = json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    (to / "manifest.json").write_text(text, encoding="utf-8")
    print(f"wrote {len(rows)} stacks of {len(step)} steps, {len(links)} bridges, "
          f"{len(record['readers'])} record readers after {len(record['givers'])} row adders; "
          f"manifest {sha(text.encode())}")  # fmt: skip
    for way, n in ways.items():
        print(f"  {way:12} {n}")
    print(
        f"  {len(manifest['no_step'])} cards have no step: no command line over a box or pile"
    )
    return 0


def do_fill(stack: Path, pile: Path, tmp: Path, to: Path) -> int:
    if to.exists():
        print(f"refused: {to} is there already", file=sys.stderr)
        return 2
    if not pile.is_dir() or not tmp.is_dir():
        print("refused: --pile and --tmp are folders that are there", file=sys.stderr)
        return 2
    text = stack.read_text(encoding="utf-8")
    for name in sorted(set(re.findall(r"\{tmp\}/([a-z0-9-]+)", text))):
        (tmp / name).mkdir(exist_ok=True)
    text = text.replace("{pile}", str(pile.resolve())).replace(
        "{tmp}", str(tmp.resolve())
    )
    to.write_text(text, encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    opts = dict(zip(rest[::2], rest[1::2]))
    want = {"write": {"--to"}, "fill": {"--stack", "--pile", "--tmp", "--to"}}.get(cmd)
    if (
        want is None
        or len(rest) % 2
        or set(opts) != want
        or len(opts) != len(rest) // 2
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    if cmd == "write":
        return do_write(Path(opts["--to"]))
    return do_fill(Path(opts["--stack"]), Path(opts["--pile"]), Path(opts["--tmp"]),
                   Path(opts["--to"]))  # fmt: skip


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
