"""A pipeline for one real (demo) person, from the add-ons a model picked, then run.

    python forperson.py URL MODEL ASSEMBLE.json PERSON OUT.json

PERSON is a demo folder (teodora, hollis, odile, bernadette). The model gets
their CHARACTER.md and the cards of the add-ons it kept in the map step, with
each card's usage line, and builds 3 to 5 steps for that person. Each step
names an add-on and, when its usage ends in a quoted example, the words to
use. Then each step is run for real on the person's files, in a fresh box,
and what it did is kept: exit code and output.
"""

import json
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from assemble import BY, SYSTEM, ask, card_line, parse  # noqa: E402

PROMPT = (
    "This is someone's life, as their files would show it:\n\n{who}\n\n"
    "These willow add-ons are on offer, each with its card and how it is run:\n"
    "{cards}\n\nBuild a pipeline of 3 to 5 steps from these add-ons only, that would"
    " be genuinely useful to THIS person, given what is in their life. For a step"
    " whose usage ends in quoted example words, give the words to use for this person."
    ' Reply as JSON: {{"why": "one sentence on what it does for them",'
    ' "steps": [{{"name": "exact-name", "words": "or empty",'
    ' "does": "what it does for them"}}, ...]}}'
)


def command(card, box, scratch, words, life=Path("/LIFE")):
    """The card's usage line made runnable, or None and why not."""
    u = card["usage"]
    if not u:
        return None, "no usage line on the card"
    u = u.replace("python ", "", 1)
    try:
        parts = shlex.split(u)
    except ValueError:
        return None, "usage line doesn't parse"
    out, quoted = [], re.search(r'"[^"]*"\s*$', u)
    i = 0
    while i < len(parts):
        p = parts[i]
        if p.startswith("[") or p.endswith("]"):
            i += 1
            continue  # an optional part: left out
        if p in ("DIR", "BOX") and out and out[-1] == "--box":
            out.append(str(box))
        elif p in ("FOLDER", "DIR", "PILE") and out and out[-1] in ("--from", "--pile"):
            out.append(str(life))
        elif (
            p in ("FILE", "OUT", "MIRROR", "DIR")
            and out
            and out[-1] in ("--to", "--out")
        ):
            out.append(str(scratch / f"{card['name']}.out"))
        elif p in ("TEXT", "QUESTION", "WORDS", "QUERY", "PATTERN") and words:
            out.append(words)
        elif re.fullmatch(r"[A-Z][A-Z_]+", p):
            return None, f"needs {p}, which the plan can't give"
        else:
            out.append(p)
        i += 1
    if quoted:
        if not words:
            return None, "needs words and the plan gave none"
        out[-1] = words
    return [sys.executable, str(ROOT / out[0]), *out[1:]], None


def main(url, model, assembled, person, outp):
    picked = json.loads(Path(assembled).read_text())
    pool = sorted({n for m in picked["map"] for n in m["kept"]})
    who = (ROOT / "demo" / person / "CHARACTER.md").read_text(encoding="utf-8")[:3000]
    cards = "\n".join(f"{card_line(BY[n])}\n    run: {BY[n]['usage']}" for n in pool)
    text, secs = ask(url, model, SYSTEM, PROMPT.format(who=who, cards=cards), 900)
    plan = parse(text) or {}
    steps = [s for s in plan.get("steps", []) if isinstance(s, dict)]
    print(f"[plan] {secs}s for {person}: {plan.get('why')}")
    life = ROOT / "demo" / person / "life"
    res = {
        "model": model,
        "person": person,
        "pool": pool,
        "raw": text,
        "plan": plan,
        "steps": [],
    }
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
            n = s.get("name")
            r = {"name": n, "words": s.get("words"), "does": s.get("does")}
            if n not in pool:
                r.update(ran=False, why="not on offer: thrown out")
            else:
                cmd, why = command(
                    BY[n], box, tmp, (s.get("words") or "").strip(), life
                )
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
                    except subprocess.TimeoutExpired as e:
                        got = subprocess.CompletedProcess(
                            cmd,
                            "still running after 60s",
                            (e.stdout or b"").decode(errors="replace"),
                            "",
                        )
                    out = got.stdout
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
                        exit=got.returncode,
                        cmd=" ".join(shlex.quote(c) for c in cmd[1:]).replace(
                            str(tmp), "<tmp>"
                        ),
                        lines=len(out.splitlines()),
                        head=out[:1500],
                        stderr=got.stderr[-400:],
                    )
            res["steps"].append(r)
            state = (
                f"exit {r['exit']}, {r['lines']} lines" if r.get("ran") else r["why"]
            )
            print(f"  - {n} [{r.get('words') or ''}]: {state}")
    Path(outp).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:6])
