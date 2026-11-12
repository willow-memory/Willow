"""run.py: Marisol's folder asked its questions, every pass rule judged, and
each written as a kernel row.

    python demo/marisol/run.py --life DIR --sources DIR --work DIR --box DIR \\
        [--now TS] [--nonsense]

--life is make_life.py's `life/`; --sources is what `sources.py fetch` wrote
(checked against sources.json first). One pile is put together under --work,
a kernel box of its own: her folder without grants/ (whose claims are what is
checked), each file read through the add-on that reads it, with the saved real
sources beside it. No model is asked. The kernel serves, the tools find where
to read, and a person decides: no key but the box's own is made, and none is
read.

Each rule in questions.json's `pass_rules` is judged, the answers and the
passages they rest on go to --work/results.json, and each rule is a verdict
row on --box with the SHA-256 of results.json and of every tool.

`--nonsense` asks "qqqq zzzz" in place of every question: the dry run
AGENTS.md asks for, which finds broken wiring before anything real is asked.

Exit codes: 0 every rule held; 42 some didn't; 2 a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
NOW = "2026-11-12T23:59:00Z"
STD = ROOT / "adapters/stdlib"
SCRIPTS = {
    "mail": STD / "mail/mail.py",
    "subtitles": STD / "subtitles/subtitles.py",
    "csv-rows": STD / "csv-rows/csv_rows.py",
    "web-pages": STD / "web-pages/web_pages.py",
    "json-paths": STD / "json-paths/json_paths.py",
    "words-es": STD / "words-es/words_es.py",
    "claim-check": STD / "claim-check/claim_check.py",
    "amounts": STD / "amounts/amounts.py",
    "quotes": STD / "quotes/quotes.py",
    "contradictions": STD / "contradictions/contradictions.py",
}
TOOLS = {
    "kernel.py": ROOT / "kernel.py",
    **{f"{k}.py": v for k, v in SCRIPTS.items()},
    "run.py": HERE / "run.py",
    "questions.json": HERE / "questions.json",
    "make_life.py": HERE / "make_life.py",
    "sources.json": HERE / "sources.json",
    "PLANTED.md": HERE / "PLANTED.md",
}
OPTS = ("--life", "--sources", "--work", "--box", "--now")
READERS = ("mail", "subtitles", "csv-rows")  # read from life/
SOURCE_READERS = ("web-pages", "json-paths")  # read from the saved sources
NONSENSE = "qqqq zzzz"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def squeeze(text: str) -> str:
    return " ".join(text.split()).lower()


def quiet(fn, *a):
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        return fn(*a)


def run(script: Path, *args: str) -> tuple[int, str]:
    got = subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True
    )
    return got.returncode, got.stdout


def copy_visible(src: Path, dst: Path) -> None:
    """The mirror's files, never its hidden .places."""
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if p.is_file() and not any(part.startswith(".") for part in rel.parts):
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dst / rel)


def build(work: Path, life: Path, sources: Path, now: str) -> tuple[Path, Path]:
    """The evidence pile and its box."""
    pile = work / "piles/evidence"
    tmp = work / "mirrors"
    for name in READERS:
        run(SCRIPTS[name], "mirror", "--from", str(life), "--to", str(tmp / name))
        copy_visible(tmp / name, pile / "life")
    for name in SOURCE_READERS:
        run(SCRIPTS[name], "mirror", "--from", str(sources), "--to", str(tmp / name))
        copy_visible(tmp / name, pile / "sources")
    for rel in ("log", "lessons"):
        for p in sorted((life / rel).rglob("*")):
            if p.is_file():
                (pile / "life" / p.relative_to(life)).parent.mkdir(
                    parents=True, exist_ok=True
                )
                shutil.copyfile(p, pile / "life" / p.relative_to(life))
    shutil.copyfile(
        life / "notes/nota-credito-936.md", pile / "life/nota-credito-936.md"
    )
    box = work / "box-evidence"
    quiet(kernel.init, box, pile, work / "evidence.key", now)
    return pile, box


def passages(pile: Path) -> dict[str, str]:
    return {f"{c['path']}:{c['line']}": c["text"] for c in kernel.chunks(pile)}


ROW = re.compile(r"^(?:all parts|some parts)\s+(\S+:\d+)\s")


def ask(q: dict, box: Path, pile: Path, life: Path, nonsense: bool, text: dict) -> dict:
    kind, said = q["kind"], (NONSENSE if nonsense else q["ask"])
    if kind == "bite":
        rc, out = run(ROOT / "kernel.py", "bite", "--box", str(box), said)
    elif kind == "words-es":
        rc, out = run(SCRIPTS["words-es"], "bite", "--box", str(box), said)
    elif kind == "claim":
        rc, out = run(SCRIPTS["claim-check"], "--box", str(box), said, "--top", "3")
    elif kind == "amounts":
        rc, out = run(SCRIPTS["amounts"], "--box", str(box))
    elif kind == "quotes":
        rc, out = run(
            SCRIPTS["quotes"], "--box", str(box), "--in", str(life / "grants/draft.md")
        )
    else:
        rc, out = run(SCRIPTS["contradictions"], "--box", str(box))
    served: list[dict] = []
    if kind in ("bite", "words-es"):
        try:
            served = [
                {"where": s["where"], "text": s["text"]}
                for s in json.loads(out)["served"]
            ]
        except (ValueError, KeyError):
            served = []
    elif kind == "claim":
        for line in out.splitlines():
            m = ROW.match(line)
            if m and m.group(1) in text:
                served.append({"where": m.group(1), "text": text[m.group(1)]})
    return {"id": q["id"], "kind": kind, "asked": said, "exit": rc,
            "served": served[:3], "stdout": out}  # fmt: skip


def hit(q: dict, a: dict) -> bool:
    return bool(q["holds"]) and any(
        squeeze(q["holds"]) in squeeze(s["text"]) for s in a["served"]
    )


def judge(asked: list[dict], box: Path) -> dict:
    by = {q["id"]: q for q in Q["questions"]}
    res: dict = {r: {"ok": True, "why": []} for r in Q["pass_rules"]}

    def fail(rule: str, why: str) -> None:
        res[rule]["ok"] = False
        res[rule]["why"].append(why)

    for a in asked:
        q = by[a["id"]]
        if q["expect"] == "hit" and not hit(q, a):
            fail("served", f"{q['id']}: no served passage holds {q['holds']!r}")
        if q["expect"] == "silent" and a["served"]:
            fail("served", f"{q['id']}: served {len(a['served'])}")
        if q["expect"] == "miss" and hit(q, a):
            fail("gap", f"{q['id']}: hit, the predicted gap is not there")
        if q["kind"] == "contradictions":
            for block in re.split(r"\n(?=[A-Z]+\s)", a["stdout"]):
                if "ernesto-interview" in block and "nota-credito" in block:
                    fail(
                        "gap",
                        f"{q['id']}: contradictions joins the father and the note",
                    )
        if q["kind"] == "amounts":
            cents = []
            for line in a["stdout"].splitlines():
                parts = line.split()
                if (
                    len(parts) > 2
                    and "outage-costs" in line
                    and parts[1].startswith("$")
                ):
                    cents.append(round(float(parts[1][1:].replace(",", "")) * 100))
            if (
                sum(cents) != Q["totals"]["receipts_cents"]
                or Q["totals"]["claimed_cents"] in cents
            ):
                fail(
                    "amounts",
                    f"{q['id']}: {len(cents)} sums total {sum(cents) / 100:.2f}",
                )
        if q["kind"] == "quotes":
            out = a["stdout"]
            if "almost" not in out or Q["planted"]["drop"] not in out:
                fail("quotes", f"{q['id']}: no 'almost' with the dropped word")
    rows, _ = kernel.read(box / "record.jsonl")
    if any(r["kind"] in ("seal", "decline") for r in rows):
        fail("unsealed", "a seal or decline row")
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
    need = ("--life", "--sources", "--work", "--box")
    if "bad" in opts or not all(opts.get(k) for k in need):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    life, sources = Path(opts["--life"]), Path(opts["--sources"])
    work, vbox = Path(opts["--work"]), Path(opts["--box"])
    if work.exists() or vbox.exists():
        print("refused: --work and --box must not exist yet", file=sys.stderr)
        return kernel.REFUSED
    gone = [s["file"] for s in json.loads((HERE / "sources.json").read_text())["sources"]
            if not (sources / s["file"]).is_file()]  # fmt: skip
    if gone:
        print(f"refused: sources missing from --sources: {gone}", file=sys.stderr)
        return kernel.REFUSED
    now, nonsense = opts.get("--now") or NOW, bool(opts.get("--nonsense"))
    work.mkdir(parents=True)
    pile, box = build(work, life, sources, now)
    text = passages(pile)
    asked = []
    for q in Q["questions"]:
        a = ask(q, box, pile, life, nonsense, text)
        asked.append(a)
        print(
            f"--- {q['id']} ({q['claim']}): {a['asked']}  [exit {a['exit']}, served {len(a['served'])}]"
        )
    if nonsense:
        silent = all(not a["served"] for a in asked)
        res = {"served": {"ok": silent, "why": [] if silent else ["nonsense served a passage"]},
               "unsealed": judge([], box)["unsealed"]}  # fmt: skip
    else:
        res = judge(asked, box)
    res["verify"] = {"ok": verify(box), "why": []}
    tools = {k: sha(p) for k, p in TOOLS.items()}
    out = {"nonsense": nonsense, "asked": asked, "rules": res}
    (work / "results.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    quiet(kernel.init, vbox, pile, vbox.parent / (vbox.name + ".key"), now)
    gate = "marisol" + (":nonsense" if nonsense else "")
    for rule, r in res.items():
        kernel.append(vbox, now, "verdict", who="marisol", gate=f"{gate}:{rule}",
                      state="satisfied" if r["ok"] else "failing",
                      results_sha256=sha(work / "results.json"), tools=tools)  # fmt: skip
    if not verify(vbox):
        res["verify"]["ok"] = False
    for rule, r in res.items():
        print(f"{rule:10} {'held' if r['ok'] else 'FAILED'}  {'; '.join(r['why'])}")
    return 0 if all(r["ok"] for r in res.values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
