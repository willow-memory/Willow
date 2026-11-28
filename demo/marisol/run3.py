"""run3.py: freeze 3's three strands, each on a box of its own, each judged
into a verdict box of its own.

    python demo/marisol/run3.py --life DIR --more DIR --sources DIR \\
        --work DIR --box DIR [--strand life|claims|misses] [--now TS] [--nonsense]

--life is make_life.py's `life/`, --more is make_life_3.py's `life-more/`,
--sources is what `sources.py fetch` wrote. For each strand (all three, or
the one --strand names) it builds an evidence box under --work/STRAND and a
verdict box at --box/STRAND, asks the strand's questions from
questions-3.json, judges each pass rule, writes --work/STRAND/results.json,
and writes each rule as a verdict row (gate `marisol3-STRAND:RULE`) with the
SHA-256 of results.json and of every tool.

The 'claims' and 'misses' boxes are freeze 2's, built by run.py's own build,
unchanged. The 'life' box reads the same sources and, beside them, each new
reader's mirror of life-more/ as a source of its own (VI.9): nothing is
copied to make a pile. No model is asked; no key but each box's own is made,
and none is read.

`--nonsense` asks "qqqq zzzz" in place of every question and skips the kinds
that take none (count, amounts), so a dry run sees no answer: it finds broken
wiring before anything real is asked.

Exit codes: 0 every rule held; 42 some didn't; 2 a bad command line.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("marisol_run", HERE / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
kernel, ROOT, STD = run.kernel, run.ROOT, run.STD

Q3 = json.loads((HERE / "questions-3.json").read_text(encoding="utf-8"))
NOW = run.NOW
MORE_READERS = {
    "calendar": STD / "calendar/cal.py",
    "sms": STD / "sms/sms.py",
    "office": STD / "office/office.py",
    "home-sensors": STD / "home-sensors/home_sensors.py",
}
POINTERS = {
    "all-passages": STD / "all-passages/all_passages.py",
    "pile-rank": STD / "pile-rank/pile_rank.py",
}
TOOLS = {
    **{k: v for k, v in run.TOOLS.items() if k != "questions.json"},
    **{f"{k}.py": v for k, v in {**MORE_READERS, **POINTERS}.items()},
    "run3.py": HERE / "run3.py",
    "questions-3.json": HERE / "questions-3.json",
    "make_life_3.py": HERE / "make_life_3.py",
}
OPTS = ("--life", "--more", "--sources", "--work", "--box", "--strand", "--now")
NONSENSE = run.NONSENSE
NO_QUESTION = ("count", "amounts")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_life(work: Path, life: Path, more: Path, sources: Path, now: str):
    """Freeze 2's box, and each new reader's mirror of life-more/ beside it."""
    tmp = work / "mirrors"
    froms = []
    for name in run.READERS:
        run.run(
            run.SCRIPTS[name], "mirror", "--from", str(life), "--to", str(tmp / name)
        )
        froms.append(f"{name}={tmp / name}")
    for name in run.SOURCE_READERS:
        run.run(
            run.SCRIPTS[name], "mirror", "--from", str(sources), "--to", str(tmp / name)
        )
        froms.append(f"{name}={tmp / name}")
    for name, script in MORE_READERS.items():
        run.run(script, "mirror", "--from", str(more), "--to", str(tmp / name))
        froms.append(f"{name}={tmp / name}")
    froms += [f"log={life / 'log'}", f"lessons={life / 'lessons'}"]
    notes = work / "notes.txt"
    notes.write_text(
        f"{(life / 'notes/nota-credito-936.md').resolve()}\n", encoding="utf-8"
    )
    froms.append(f"notes=@{notes}")
    box = work / "box-evidence"
    run.quiet(kernel.init, box, None, work / "evidence.key", now, None, froms)
    return box, froms


def served_of(out: str) -> list[dict]:
    try:
        return [
            {k: s[k] for k in ("rank", "where", "text") if k in s}
            for s in json.loads(out)["served"]
        ]
    except (ValueError, KeyError, TypeError):
        return []


def ask(q: dict, box: Path, work: Path, nonsense: bool, text: dict) -> dict:
    kind, said = q["kind"], (NONSENSE if nonsense else q["ask"])
    out, rc, served, extra = "", 0, [], {}
    if kind == "words-es":
        rc, out = run.run(run.SCRIPTS["words-es"], "bite", "--box", str(box), said)
        served = served_of(out)
    elif kind == "claim":
        rc, out = run.run(
            run.SCRIPTS["claim-check"], "--box", str(box), said, "--top", "3"
        )
        for line in out.splitlines():
            m = run.ROW.match(line)
            if m and m.group(1) in text:
                served.append({"where": m.group(1), "text": text[m.group(1)]})
    elif kind == "all-passages":
        rc, out = run.run(POINTERS["all-passages"], "--box", str(box), "--top",
                          str(q["within"]), said)  # fmt: skip
        served = served_of(out)
        _, bite = run.run(ROOT / "kernel.py", "bite", "--box", str(box), said)
        extra["kernel_served"] = [s["where"] for s in served_of(bite)]
    elif kind == "pile-rank":
        rc, out = run.run(POINTERS["pile-rank"], "--from", str(work / "mirrors" / q["from"]),
                          "--top", "3", said)  # fmt: skip
        served = served_of(out)
    elif kind == "amounts" and not nonsense:
        rc, out = run.run(run.SCRIPTS["amounts"], "--box", str(box))
    elif kind == "count" and not nonsense:
        held = sorted(
            w for w, t in text.items() if run.squeeze(q["holds"]) in run.squeeze(t)
        )
        extra["holding"] = held
        out = f"{len(held)} passages hold {q['holds']!r}\n"
    else:
        said = None  # a kind that takes no question, skipped in a dry run
    keep = served if kind == "all-passages" else served[:3]
    return {"id": q["id"], "kind": kind, "asked": said, "exit": rc,
            "served": keep, **extra, "stdout": out}  # fmt: skip


def hit(q: dict, a: dict) -> bool:
    return run.hit(q, {"served": a["served"][:3]})


def within(q: dict, a: dict) -> int | None:
    """The best rank of a passage holding the phrase, or None."""
    for i, s in enumerate(a["served"], 1):
        if run.squeeze(q["holds"]) in run.squeeze(s["text"]):
            return s.get("rank", i)
    return None


def judge(strand: str, asked: list[dict], box: Path, text: dict) -> dict:
    spec = Q3["strands"][strand]
    by = {q["id"]: q for q in spec["questions"]}
    res: dict = {r: {"ok": True, "why": []} for r in spec["pass_rules"]}

    def fail(rule: str, why: str) -> None:
        res[rule]["ok"] = False
        res[rule]["why"].append(why)

    for a in asked:
        q = by[a["id"]]
        k, e = q["kind"], q["expect"]
        if k in ("claim", "words-es"):
            if e == "hit" and not hit(q, a):
                fail("served", f"{q['id']}: no served passage holds {q['holds']!r}")
            if e == "silent" and a["served"]:
                fail("served", f"{q['id']}: served {len(a['served'])}")
            if e == "miss" and hit(q, a):
                fail("gap", f"{q['id']}: hit, the predicted gap is not there")
        if k == "count":
            n = len(a.get("holding", []))
            if n != q["n"] or n == q["claimed"]:
                fail("count", f"{q['id']}: {n} passages hold {q['holds']!r}")
        if k == "amounts":
            budget = set()
            for line in a["stdout"].splitlines():
                parts = line.split()
                if (
                    len(parts) > 2
                    and parts[1].startswith("$")
                    and "presupuesto" in line
                ):
                    budget.add(round(float(parts[1][1:].replace(",", "")) * 100))
            want = set(spec["budget"]["lines_cents"])
            if not want <= budget:
                fail(
                    "budget", f"{q['id']}: the budget's sums read were {sorted(budget)}"
                )
            if any(spec["budget"]["claimed"] in t for t in text.values()):
                fail("budget", f"{q['id']}: a passage says {spec['budget']['claimed']}")
        if k == "all-passages":
            r = within(q, a)
            if r is None or r > q["within"]:
                fail(
                    "reach",
                    f"{q['id']}: no passage holding {q['holds']!r} in the first {q['within']}",
                )
            first = [s["where"] for s in a["served"][:3]]
            if first != a.get("kernel_served"):
                fail("reach", f"{q['id']}: its first three are not the kernel's")
        if k == "pile-rank" and not hit(q, a):
            fail(
                "phrases", f"{q['id']}: pile-rank's first three hold no {q['holds']!r}"
            )
    if "rank" in res and sha(ROOT / "kernel.py") != spec["kernel_at_freeze_2"]:
        fail("rank", "kernel.py is not the file freeze 2 ran")
    rows, _ = kernel.read(box / "record.jsonl")
    if any(r["kind"] in ("seal", "decline") for r in rows):
        fail("unsealed", "a seal or decline row")
    return res


def one(strand: str, opts: dict, nonsense: bool, now: str) -> bool:
    life, more, sources = (Path(opts[k]) for k in ("--life", "--more", "--sources"))
    work = Path(opts["--work"]) / strand
    vbox = Path(opts["--box"]) / strand
    work.mkdir(parents=True)
    if strand == "life":
        box, froms = build_life(work, life, more, sources, now)
    else:
        box, froms = run.build(work, life, sources, now)
    text = run.passages(box)
    asked = []
    for q in Q3["strands"][strand]["questions"]:
        a = ask(q, box, work, nonsense, text)
        asked.append(a)
        print(f"--- {strand} {q['id']} ({q['claim']}): {a['asked']}  "
              f"[exit {a['exit']}, served {len(a['served'])}]")  # fmt: skip
    if nonsense:
        silent = all(not a["served"] for a in asked)
        res = {"served": {"ok": silent, "why": [] if silent else ["nonsense served a passage"]},
               "unsealed": judge(strand, [], box, text)["unsealed"]}  # fmt: skip
    else:
        res = judge(strand, asked, box, text)
    res["verify"] = {"ok": run.verify(box), "why": []}
    tools = {k: sha(p) for k, p in TOOLS.items()}
    out = {"strand": strand, "nonsense": nonsense, "asked": asked, "rules": res}
    (work / "results.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    vbox.parent.mkdir(parents=True, exist_ok=True)
    run.quiet(
        kernel.init, vbox, None, vbox.parent / (vbox.name + ".key"), now, None, froms
    )
    gate = f"marisol3-{strand}" + (":nonsense" if nonsense else "")
    for rule, r in res.items():
        kernel.append(vbox, now, "verdict", who="marisol", gate=f"{gate}:{rule}",
                      state="satisfied" if r["ok"] else "failing",
                      results_sha256=sha(work / "results.json"), tools=tools)  # fmt: skip
    if not run.verify(vbox):
        res["verify"]["ok"] = False
    for rule, r in res.items():
        print(
            f"{strand:7} {rule:9} {'held' if r['ok'] else 'FAILED'}  {'; '.join(r['why'])}"
        )
    return all(r["ok"] for r in res.values())


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in OPTS:
            opts[a] = next(it, "")
        elif a == "--nonsense":
            opts[a] = True
        else:
            opts["bad"] = a
    need = ("--life", "--more", "--sources", "--work", "--box")
    strands = [opts["--strand"]] if opts.get("--strand") else list(Q3["strands"])
    if ("bad" in opts or not all(opts.get(k) for k in need)
            or not set(strands) <= set(Q3["strands"])):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if Path(opts["--work"]).exists() or Path(opts["--box"]).exists():
        print("refused: --work and --box must not exist yet", file=sys.stderr)
        return kernel.REFUSED
    gone = [s["file"] for s in json.loads((HERE / "sources.json").read_text())["sources"]
            if not (Path(opts["--sources"]) / s["file"]).is_file()]  # fmt: skip
    if gone:
        print(f"refused: sources missing from --sources: {gone}", file=sys.stderr)
        return kernel.REFUSED
    now, nonsense = opts.get("--now") or NOW, bool(opts.get("--nonsense"))
    held = [one(s, opts, nonsense, now) for s in strands]
    return 0 if all(held) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
