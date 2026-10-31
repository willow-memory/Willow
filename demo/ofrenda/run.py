"""run.py: the séance. Every question in questions.json asked of a local model
through willow, every pass rule judged, and each written as a kernel row.

    python demo/ofrenda/run.py --books DIR --life DIR --work DIR --box DIR \\
        --url URL --model NAME [--now TS] [--nonsense]

--books is what fetch.py wrote; --life is make_life.py's `life/`. Two piles
are put together under --work, each a kernel box of its own:

    ofrenda      Marisol's folder, with Femia's terminal history read
                 through shell-history in place of the raw file
    ghost-club   the two books, sources/ID.txt

Each question goes through openai-compatible to the model at URL (a
llama.cpp server on 127.0.0.1, in the run the README reports), in the voice
the question names (voices/NAME.md). The kernel serves, the model suggests,
and the suggestion waits on a seal that nobody here gives: no key but each
box's own is made, and none is read.

Each rule in questions.json's `pass_rules` is judged, the replies and the
passages they rest on go to --work/results.json, and each rule is a verdict
row on --box with the SHA-256 of results.json, of every tool, and of the
model file when --gguf names it.

`--nonsense` asks "qqqq zzzz" in place of every question: the dry run
AGENTS.md asks for, which finds broken wiring before anything real is asked.

Exit codes: 0 every rule held; 42 some didn't; 2 a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
NOW = "2026-10-31T23:59:00Z"
ASK = ROOT / "adapters/stdlib/openai-compatible/openai_compatible.py"
HISTORY = ROOT / "adapters/stdlib/shell-history/shell_history.py"
TOOLS = {
    "kernel.py": ROOT / "kernel.py",
    "openai_compatible.py": ASK,
    "shell_history.py": HISTORY,
    "run.py": HERE / "run.py",
    "questions.json": HERE / "questions.json",
    **{f"voices/{p.name}": p for p in sorted((HERE / "voices").glob("*.md"))},
}
OPTS = ("--books", "--life", "--work", "--box", "--url", "--model", "--now", "--gguf")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def squeeze(text: str) -> str:
    return " ".join(text.split()).lower()


def quiet(fn, *a):
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        return fn(*a)


def build(work: Path, books: Path, life: Path, now: str) -> dict[str, Path]:
    """The two piles and their boxes, under work."""
    piles = {"ofrenda": work / "piles/ofrenda", "ghost-club": work / "piles/ghost-club"}
    shutil.copytree(
        life, piles["ofrenda"], ignore=shutil.ignore_patterns("bash_history*")
    )
    got = subprocess.run([sys.executable, str(HISTORY), "mirror", "--from", str(life),
                          "--to", str(work / "history")], capture_output=True, text=True)  # fmt: skip
    if got.returncode != 0:
        raise SystemExit(f"shell-history: {got.stdout}{got.stderr}")
    shutil.copytree(work / "history", piles["ofrenda"], dirs_exist_ok=True)
    piles["ghost-club"].mkdir(parents=True)
    for p in sorted((books / "sources").glob("*.txt")):
        shutil.copy(p, piles["ghost-club"] / p.name)
    boxes = {}
    for name, pile in piles.items():
        boxes[name] = work / "boxes" / name
        code = quiet(kernel.init, boxes[name], pile, work / "keys" / f"{name}.key", now)
        if code != 0:
            raise SystemExit(f"init {name}: exit {code}")
    return boxes


def seance(q: dict, box: Path, url: str, model: str, now: str, nonsense: bool) -> dict:
    """One question asked through openai-compatible, and what came of it."""
    ask = "qqqq zzzz" if nonsense else q["ask"]
    voice = HERE / "voices" / f"{q['voice']}.md"
    got = subprocess.run([sys.executable, str(ASK), "ask", "--box", str(box), "--url", url,
                          "--model", model, "--system", str(voice), "--now", now, ask],
                         capture_output=True, text=True)  # fmt: skip
    rows, _ = kernel.read(box / "record.jsonl")
    bite = next(r for r in reversed(rows) if r["kind"] == "bite")
    pile = Path(kernel.config(box)["pile"])
    text = {c["id"]: c["text"] for c in kernel.chunks(pile)}
    served = [{"where": s["where"], "id": s["id"], "text": text.get(s["id"], "")}
              for s in bite.get("served", [])]  # fmt: skip
    cites: list[str] = []
    if rows[-1]["kind"] == "proposal" and rows[-1].get("verdict") == "pass":
        prop = json.loads(
            (box / "proposals" / f"{rows[-1]['subject'][9:]}.json").read_text()
        )
        cites = prop["cites"]
    lines = got.stdout.splitlines()
    reply = "\n".join(ln for ln in lines if not ln.startswith(("pass  ", "refused  ")))
    return {"id": q["id"], "asked": ask, "exit": got.returncode, "stdout": got.stdout,
            "reply": reply, "served": served, "cites": cites}  # fmt: skip


def judge(asked: list[dict], boxes: dict[str, Path]) -> dict:
    by = {q["id"]: q for q in Q["questions"]}
    res: dict = {r: {"ok": True, "why": []} for r in Q["pass_rules"]}

    def fail(rule: str, why: str) -> None:
        res[rule]["ok"] = False
        res[rule]["why"].append(why)

    for a in asked:
        q = by[a["id"]]
        if q["holds"] is None:
            if (
                a["served"]
                or a["exit"] != 42
                or "no model was asked" not in a["stdout"]
            ):
                fail(
                    "served", f"{q['id']}: served {len(a['served'])}, exit {a['exit']}"
                )
            continue
        phrase = squeeze(q["holds"])
        holding = {s["id"] for s in a["served"] if phrase in squeeze(s["text"])}
        if not holding:
            fail("served", f"{q['id']}: no served passage holds the phrase")
        if a["exit"] != 0 or not holding & set(a["cites"]):
            fail("cited", f"{q['id']}: exit {a['exit']}, cites {len(a['cites'])}")
        if not any(w.lower() in a["reply"].lower() for w in q["says"]):
            fail("says", f"{q['id']}: none of {q['says']}")
    for name, box in boxes.items():
        rows, _ = kernel.read(box / "record.jsonl")
        if any(r["kind"] in ("seal", "decline") for r in rows):
            fail("unsealed", f"{name}: a seal or decline row")
    return res


def verify(box: Path) -> bool:
    return quiet(kernel.main, ["verify", "--box", str(box)]) == 0


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in OPTS:
            opts[a] = next(it, "")
        elif a == "--nonsense":
            opts[a] = True
        else:
            opts["bad"] = a
    need = ("--books", "--life", "--work", "--box", "--url", "--model")
    if "bad" in opts or not all(opts.get(k) for k in need):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    work, box = Path(opts["--work"]), Path(opts["--box"])
    if work.exists() or box.exists():
        print("refused: --work and --box must not exist yet", file=sys.stderr)
        return kernel.REFUSED
    now, nonsense = opts.get("--now") or NOW, bool(opts.get("--nonsense"))
    boxes = build(work, Path(opts["--books"]), Path(opts["--life"]), now)
    asked = []
    for q in Q["questions"]:
        a = seance(q, boxes[q["box"]], opts["--url"], opts["--model"], now, nonsense)
        asked.append(a)
        print(f"--- {q['id']} ({q['voice']}): {a['asked']}\n{a['stdout'].rstrip()}\n")
    res = judge(asked, boxes) if not nonsense else {
        "served": {"ok": all(not a["served"] for a in asked), "why": []},
        "unsealed": judge([], boxes)["unsealed"],
    }  # fmt: skip
    res["verify"] = {"ok": all(verify(b) for b in boxes.values()), "why": []}
    tools = {k: sha(p) for k, p in TOOLS.items()}
    if opts.get("--gguf"):
        tools["model.gguf"] = sha(Path(opts["--gguf"]))
    out = {"model": opts["--model"], "url": opts["--url"], "nonsense": nonsense,
           "asked": asked, "rules": res}  # fmt: skip
    (work / "results.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    quiet(
        kernel.init, box, work / "piles/ofrenda", box.parent / (box.name + ".key"), now
    )
    gate = f"ofrenda:{opts['--model']}" + (":nonsense" if nonsense else "")
    for rule, r in res.items():
        kernel.append(box, now, "verdict", who="ofrenda", gate=f"{gate}:{rule}",
                      state="satisfied" if r["ok"] else "failing",
                      results_sha256=sha(work / "results.json"), tools=tools)  # fmt: skip
    if not verify(box):
        res["verify"]["ok"] = False
    for rule, r in res.items():
        print(f"{rule:10} {'held' if r['ok'] else 'FAILED'}  {'; '.join(r['why'])}")
    return 0 if all(r["ok"] for r in res.values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
