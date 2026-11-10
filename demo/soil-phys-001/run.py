"""run.py: can willow's tools stand in for reading? One run of the study.

    python demo/soil-phys-001/run.py --keep DIR --work DIR --out FILE [--box DIR] [--dry]

SOIL-PHYS-001's ledger was checked line by line by reading its sources: 35
lines, each with a verdict and the source's deciding words (key.json). This
asks three of willow's tools the same thing, and scores them against that
answer key:

- misquote: is each deciding quote in its source, as written or nearly?
- claim-check: does a passage in the right source hold every part of each
  line's claim?
- the kernel: asked a plain question for each line, does it serve (top 3) a
  passage from the right source?

--keep holds the 28 kept files, each held to its SHA-256 in sources.json;
a missing or changed file is refused before anything is asked. The pile is
made in --work by the repo's readers: pdf (adapters/deps/pdf, which needs
pypdf) for the PDFs, web-pages for the HTML, and the text of the Newton
Project's TEI transcriptions (their tags taken out here: there is no TEI
reader). A box over that pile serves misquote and claim-check.

`--dry` asks nonsense in place of every quote, claim and question, over the
same pile plus one nonsense passage the nonsense finds, so the wiring after
each tool is exercised and no result is seen. --out is a JSON file; with
--box, each pass rule's verdict is a kernel row (soil-phys-001:R1 and on,
soil-phys-001:dry:R1 for a dry run). A runner, not an add-on: it calls the
add-ons' command lines. Exit 0, or 2 on a bad command line or a kept file
that isn't the one frozen.
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

TOP = 3
SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]
KEY = json.loads((HERE / "key.json").read_text(encoding="utf-8"))
HOLDS = ("holds", "holds with a change")
R1_AT_LEAST, R2_AT_LEAST, R3_AT_LEAST = 0.9, 0.6, 0.5
R4_CLAIMS_AT_MOST, R4_QUESTIONS_AT_MOST = 1, 2
USAGE = "usage: run.py --keep DIR --work DIR --out FILE [--box DIR] [--dry]"
NONSENSE = "Here qqqq comes after zzzz and before xxxx, a passage of plumbing only."


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def held(keep: Path) -> list[str]:
    """Every kept file, as frozen: what is missing or changed, else nothing."""
    bad = []
    for s in SOURCES:
        p = keep / s["file"]
        if not p.is_file():
            bad.append(f"{s['file']}: missing")
        elif sha(p) != s["sha256"]:
            bad.append(f"{s['file']}: changed (sha256 {sha(p)[:16]})")
    return bad


def tei_text(raw: str) -> str:
    """A TEI transcription's text: the body's words, one paragraph a line."""
    parts = re.split(r"<text\b[^>]*>", raw, maxsplit=1)
    body = parts[-1]  # after the whole opening tag, its attributes too
    body = re.sub(r"<(p|head|lg|l)\b[^>]*>", "\n\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    paras = [" ".join(x.split()) for x in body.split("\n\n")]
    return "\n\n".join(x for x in paras if x) + "\n"


def build(keep: Path, work: Path, dry: bool) -> Path:
    pile = work / "pile"
    if pile.exists():
        shutil.rmtree(pile)
    stage = {k: work / "stage" / k for k in ("pdf", "html")}
    for d in stage.values():
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    (pile / "tei").mkdir(parents=True)
    for s in SOURCES:
        f = s["file"]
        if f.endswith(".pdf"):
            shutil.copyfile(keep / f, stage["pdf"] / f)
        elif f.endswith(".html"):
            shutil.copyfile(keep / f, stage["html"] / f)
        else:  # the Newton Project's TEI, kept without an extension
            raw = (keep / f).read_text(encoding="utf-8")
            (pile / "tei" / (f + ".txt")).write_text(tei_text(raw), encoding="utf-8")
    for part, script in (
        ("pdf", "deps/pdf/pdf.py"),
        ("html", "stdlib/web-pages/web_pages.py"),
    ):
        got = subprocess.run([sys.executable, str(ROOT / "adapters" / script), "mirror",
                              "--from", str(stage[part]), "--to", str(pile / part)],
                             capture_output=True, text=True)  # fmt: skip
        print(
            f"{part:<5} {(got.stdout.strip().splitlines() or [got.stderr.strip()])[-1]}"
        )
    if dry:
        (pile / "plumbing.txt").write_text(NONSENSE + "\n", encoding="utf-8")
    return pile


def box_for(work: Path, pile: Path) -> Path:
    box = work / "box"
    if box.exists():
        shutil.rmtree(box)
    key = work / "box.key"
    if key.exists():
        key.unlink()
    with contextlib.redirect_stdout(io.StringIO()):
        if kernel.init(box, pile, key, kernel.now()) != kernel.ALIVE:
            raise SystemExit(f"refused: couldn't make a box at {box}")
    return box


def stem(f: str) -> str:
    return f.split(".")[0]


def tool(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "adapters/stdlib" / script), *args],
                          capture_output=True, text=True, timeout=900)  # fmt: skip


def misquote(box: Path, quote: str, f: str) -> dict:
    got = tool("misquote/misquote.py", "--box", str(box), quote, "--json")
    try:
        rep = json.loads(got.stdout)
    except ValueError:
        return {"found": False, "said": (got.stderr or got.stdout).strip()[-200:]}
    wheres = [
        r.get("where", "") for g in rep.get("groups", []) for r in g.get("rows", [])
    ]
    return {"found": rep.get("state") == "populated" and any(stem(f) in w for w in wheres),
            "exact": got.returncode == 0 and rep.get("state") == "populated",
            "said": rep.get("said"), "where": wheres[:3]}  # fmt: skip


def claim_check(box: Path, claim: str, f: str) -> dict:
    got = tool("claim-check/claim_check.py", "--box", str(box), claim)
    rows = [x.split() for x in got.stdout.splitlines()]
    alls = [r[2] for r in rows if r[:2] == ["all", "parts"] and len(r) > 2]
    return {"all_parts": bool(alls), "right_file": any(stem(f) in a for a in alls) if f else False,
            "where": alls[:3], "exit": got.returncode}  # fmt: skip


def ask(chunks: list, question: str, f: str) -> dict:
    served = kernel.rank(chunks, question, top=TOP)
    paths = [c["path"] for c in served]
    return {"served": len(paths), "right_file": any(stem(f) in p for p in paths) if f else False,
            "where": paths}  # fmt: skip


def rule(n: int, of: int, at_least: float) -> dict:
    share = n / of if of else 0.0
    return {"state": "satisfied" if of and share >= at_least else "failing",
            "number": f"{n} of {of}", "needed": f"at least {at_least:.0%}"}  # fmt: skip


def tally(rows: list[dict], nulls: list[dict]) -> dict:
    text = {s["file"] for s in SOURCES if s["text_layer"]}
    readable = [r for r in rows if r["file"] in text]
    hold = [r for r in readable if r["verdict"] in HOLDS]
    false = [r for r in rows if r["verdict"] == "does not hold"]
    out = {
        "R1": rule(
            sum(r["misquote"]["found"] for r in readable), len(readable), R1_AT_LEAST
        ),
        "R2": rule(sum(r["claim"]["right_file"] for r in hold), len(hold), R2_AT_LEAST),
        "R3": rule(sum(r["ask"]["right_file"] for r in hold), len(hold), R3_AT_LEAST),
    }
    nc = sum(n["claim"]["all_parts"] for n in nulls)
    nq = sum(n["ask"]["served"] > 0 for n in nulls)
    out["R4"] = {"state": "satisfied" if nc <= R4_CLAIMS_AT_MOST and nq <= R4_QUESTIONS_AT_MOST else "failing",
                 "number": f"{nc} of {len(nulls)} off-topic claims given all parts; {nq} of {len(nulls)} off-topic questions served",
                 "needed": f"at most {R4_CLAIMS_AT_MOST} and at most {R4_QUESTIONS_AT_MOST}"}  # fmt: skip
    out["P1"] = {"state": "reported",
                 "number": f"{sum(r['claim']['all_parts'] for r in false)} of {len(false)} false claims given all parts by claim-check",
                 "needed": "predicted at least 1: claim-check finds where to read, and never reads"}  # fmt: skip
    scans = [r for r in rows if r["file"] not in text]
    out["P2"] = {"state": "reported",
                 "number": f"{sum(r['misquote']['found'] for r in scans)} of {len(scans)} quotes from scans found by misquote",
                 "needed": "predicted 0: no text layer"}  # fmt: skip
    return out


def verdicts(box: Path, result: dict, dry: bool, answers: str) -> None:
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):
            if (
                kernel.init(box, HERE, box.parent / (box.name + ".key"), kernel.now())
                != kernel.ALIVE
            ):
                raise SystemExit(f"refused: couldn't start a record at {box}")
    tools = {rel: sha(ROOT / rel) for rel in (
        "kernel.py", "adapters/stdlib/misquote/misquote.py", "adapters/stdlib/claim-check/claim_check.py",
        "adapters/deps/pdf/pdf.py", "adapters/stdlib/web-pages/web_pages.py", "demo/soil-phys-001/run.py")}  # fmt: skip
    for name, v in result.items():
        kernel.append(box, kernel.now(), "verdict", who="soil-phys-001",
                      gate=f"soil-phys-001:{'dry:' if dry else ''}{name}", state=v["state"],
                      number=v["number"], needed=v["needed"], answers_sha256=answers, tools=tools)  # fmt: skip


def main(argv: list[str]) -> int:
    opts, dry, i = {}, False, 0
    while i < len(argv):
        if argv[i] == "--dry":
            dry, i = True, i + 1
        elif argv[i] in ("--keep", "--work", "--out", "--box") and i + 1 < len(argv):
            opts[argv[i]], i = argv[i + 1], i + 2
        else:
            break
    if i != len(argv) or not {"--keep", "--work", "--out"} <= set(opts):
        print(USAGE, file=sys.stderr)
        return 2
    keep, work = Path(opts["--keep"]), Path(opts["--work"])
    bad = held(keep)
    if bad:
        print(
            "refused: the kept files aren't the frozen ones:\n  " + "\n  ".join(bad),
            file=sys.stderr,
        )
        return 2
    work.mkdir(parents=True, exist_ok=True)
    pile = build(keep, work, dry)
    box = box_for(work, pile)
    chunks = kernel.chunks(pile)
    rows, nulls = [], []
    for n, line in enumerate(KEY["lines"], 1):
        q, c, a = line["quote"], line["claim"], line["question"]
        if dry:  # nonsense, in an order the plumbing passage holds, never an echo of it
            q = c = a = "zzzz before xxxx qqqq"
        rows.append({**line, "asked": {"quote": q, "claim": c, "question": a},
                     "misquote": misquote(box, q, line["file"]),
                     "claim": claim_check(box, c, line["file"]),
                     "ask": ask(chunks, a, line["file"])})  # fmt: skip
        print(f"{n:>2} {line['id']}", file=sys.stderr)
    for line in KEY["null"]:
        c, a = (
            (("zzzz before xxxx qqqq",) * 2)
            if dry
            else (line["claim"], line["question"])
        )
        nulls.append(
            {**line, "claim": claim_check(box, c, ""), "ask": ask(chunks, a, "")}
        )
    result = tally(rows, nulls)
    record = {"dry": dry, "verdicts": result, "rows": rows, "null": nulls}
    text = json.dumps(record, indent=1, ensure_ascii=False) + "\n"
    Path(opts["--out"]).write_text(text, encoding="utf-8")
    for name, v in result.items():
        print(f"{name}  {v['state']:<10} {v['number']}  (needed: {v['needed']})")
    if "--box" in opts:
        verdicts(
            Path(opts["--box"]),
            result,
            dry,
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )
        print(
            f"verdicts appended to {opts['--box']}: kernel.py verify --box {opts['--box']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
