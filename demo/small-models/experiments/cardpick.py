"""Willow picks the cards: a person's needs, asked of a pile of add-on cards.

    python cardpick.py URL MODEL PERSON OUT.json [--rank bm25|kernel] [--top N]

1. The model reads PERSON's CHARACTER.md and writes 4 to 6 needs, each a
   short plain question.
2. Each need is asked of an index of the 270 add-on cards (one card a file)
   with scan.py; only the cards it serves are on offer.
3. The model builds a 3 to 5 step pipeline from the served cards alone; a
   name it wasn't served is thrown out.
4. Each step is run on the person's files in a fresh box, as forperson.py does.
"""

import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from assemble import BY, SYSTEM, ask, card_line, parse  # noqa: E402
from forperson import PROMPT, command  # noqa: E402

USES = os.environ.get("CARD_USES") == "1"
from assemble import WORK  # noqa: E402

PILE = WORK / ("cardpile2" if USES else "cardpile")
INDEX = PILE.with_suffix(".index")
USE = json.loads((WORK / "uses.json").read_text(encoding="utf-8")) if USES else {}

NEEDS = (
    "This is someone's life, as their files would show it:\n\n{who}\n\n"
    "List 4 to 6 things this person needs that a tool reading their own files"
    " could help with. Write each as a short plain question of 4 to 8 words, in"
    ' the words they would use (the shape of "when is the dog due at the vet", but about their life).'
    ' Reply as JSON: {{"needs": ["...", ...]}}'
)


def build_pile():
    if INDEX.exists():
        return
    PILE.mkdir(exist_ok=True)
    for c in BY.values():
        (PILE / f"{c['name']}.txt").write_text(
            f"{c['name']}: {c['line']}\nsection: {c['section']}; writes {c['writes']};"
            f" network {c['network']}\nrun: {c['usage']}\n"
            + (f"what it is for: {USE.get(c['name'], '')}\n" if USES else ""),
            encoding="utf-8",
        )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters/stdlib/scan/scan.py"),
            "index",
            "--from",
            str(PILE),
            "--to",
            str(INDEX),
        ],
        check=True,
        capture_output=True,
    )


def serve(needs, rank, top):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("".join(f"n{i}\t{q}\n" for i, q in enumerate(needs)))
    got = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters/stdlib/scan/scan.py"),
            "scan",
            "--index",
            str(INDEX),
            "--questions",
            f.name,
            "--top",
            str(top),
            "--rank",
            rank,
        ],
        capture_output=True,
        text=True,
    )
    out = {}
    for line in got.stdout.splitlines():
        d = json.loads(line)
        names = [Path(s["where"].split(":")[0]).stem for s in d.get("served", [])]
        out[needs[int(d["question"][1:])]] = names
    return out


def run_steps(steps, pool, person):
    life = ROOT / "demo" / person / "life"
    res = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        box = tmp / "box"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "kernel.py"),
                "init",
                "--box",
                str(box),
                "--pile",
                str(life),
                "--key",
                str(tmp / "key"),
            ],
            capture_output=True,
            check=True,
        )
        for s in steps:
            n, words = s.get("name"), (s.get("words") or "").strip()
            r = {"name": n, "words": words, "does": s.get("does")}
            if n not in pool:
                r.update(ran=False, why="not served: thrown out")
            else:
                cmd, why = command(BY[n], box, tmp, words, life)
                if cmd is None:
                    r.update(ran=False, why=why)
                else:
                    try:
                        got = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=60,
                            cwd=ROOT,
                            stdin=subprocess.DEVNULL,
                        )
                        code, out = got.returncode, got.stdout
                    except subprocess.TimeoutExpired as e:
                        code, out = (
                            "still running after 60s",
                            (e.stdout or b"").decode(errors="replace"),
                        )
                    f = tmp / f"{n}.out"
                    if f.is_file():
                        out += f.read_text(encoding="utf-8", errors="replace")
                    elif f.is_dir():
                        made = sorted(p for p in f.rglob("*") if p.is_file())
                        out += f"[mirror: {len(made)} files]\n" + "".join(
                            p.read_text(encoding="utf-8", errors="replace")[:300]
                            for p in made[:3]
                        )
                    r.update(
                        ran=True,
                        exit=code,
                        lines=len(out.splitlines()),
                        head=out[:1500],
                        cmd=" ".join(shlex.quote(c) for c in cmd[1:]).replace(
                            str(tmp), "<tmp>"
                        ),
                    )
            res.append(r)
            state = (
                f"exit {r['exit']}, {r['lines']} lines" if r.get("ran") else r["why"]
            )
            print(f"  - {n} [{words}]: {state}", flush=True)
    return res


def main(url, model, person, outp, rank="bm25", top=4):
    build_pile()
    who = (ROOT / "demo" / person / "CHARACTER.md").read_text(encoding="utf-8")[:3000]
    text, secs = ask(url, model, SYSTEM, NEEDS.format(who=who), 400)
    needs = [q for q in ((parse(text) or {}).get("needs") or []) if isinstance(q, str)][
        :6
    ]
    print(f"[needs] {secs}s: {needs}", flush=True)
    served = serve(needs, rank, top)
    for q, names in served.items():
        print(f"  {q!r} -> {names}", flush=True)
    pool = sorted({n for names in served.values() for n in names if n in BY})
    cards = "\n".join(
        f"{card_line(BY[n])}\n    for: {USE.get(n, '')}\n    run: {BY[n]['usage']}"
        if USES
        else f"{card_line(BY[n])}\n    run: {BY[n]['usage']}"
        for n in pool
    )
    text2, secs2 = ask(url, model, SYSTEM, PROMPT.format(who=who, cards=cards), 900)
    plan = parse(text2) or {}
    steps = [s for s in plan.get("steps", []) if isinstance(s, dict)]
    print(f"[plan] {secs2}s ({len(pool)} cards served): {plan.get('why')}", flush=True)
    res = run_steps(steps, set(pool), person)
    Path(outp).write_text(
        json.dumps(
            {
                "model": model,
                "person": person,
                "rank": rank,
                "uses": USES,
                "needs": needs,
                "served": served,
                "pool": pool,
                "plan": plan,
                "raw": [text, text2],
                "steps": res,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n"
    )


if __name__ == "__main__":
    a = sys.argv[1:]
    rank = a[a.index("--rank") + 1] if "--rank" in a else "bm25"
    top = int(a[a.index("--top") + 1]) if "--top" in a else 4
    main(a[0], a[1], a[2], a[3], rank, top)
