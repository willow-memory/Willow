"""run.py: every pass rule in questions.json, judged, and written as kernel rows.

    python demo/stewart-crossover/run.py --mirror DIR --wren DIR --work DIR --box DIR [--now TS] [--nonsense]

--mirror is what fetch.py wrote; --wren is Wren's life (make_life.py's
`life/`). Three piles are put together under --work, each a kernel box:

    sources   the sources' text, sources/ID.txt
    wren      her files, wren/...
    all       both, and the parody line, parody/gerald.txt

Each rule in questions.json's `pass_rules` is judged with the add-on or the
code it names, from this repo or one beside it (willows-grove, willow-mcp,
willow-bot, Forge, at the commits FROZEN.json names). Its answer and the
outputs it rests on go to --work/results.json, and each rule is a verdict
row on --box, with the SHA-256 of results.json and of every tool. Nothing
here seals, and no key but the box's own is made or read.

`--nonsense` asks "qqqq zzzz" in place of every claim, quote, question and
line, and plants nothing: the dry run AGENTS.md asks for, which finds broken
wiring before anything real is asked.

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
REPOS = ROOT.parent
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

A = ROOT / "adapters" / "stdlib"
NONSENSE = "qqqq zzzz"
NOW = "2026-10-30T00:00:00Z"
TOOLS = {
    "kernel.py": ROOT / "kernel.py",
    "claim_check.py": A / "claim-check" / "claim_check.py",
    "quote_check.py": A / "quote-check" / "quote_check.py",
    "misquote.py": A / "misquote" / "misquote.py",
    "contradictions.py": A / "contradictions" / "contradictions.py",
    "words_tlh.py": A / "words-tlh" / "words_tlh.py",
    "make_it_so.py": A / "make-it-so" / "make_it_so.py",
    "willows-grove/grove/seat_say.py": REPOS / "willows-grove" / "grove" / "seat_say.py",
    "willows-grove/grove/seat_boxes.py": REPOS / "willows-grove" / "grove" / "seat_boxes.py",
    "willow-mcp/src/willow_mcp/web_search.py": REPOS / "willow-mcp" / "src" / "willow_mcp" / "web_search.py",
    "willow-bot/one-script/kernel.py": REPOS / "willow-bot" / "one-script" / "kernel.py",
    "Forge/forge/measure_panel.py": REPOS / "Forge" / "forge" / "measure_panel.py",
}  # fmt: skip
Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
SOURCES = {
    s["id"]: s for s in json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
}
FICTION = re.compile(r"\bfiction", re.I)
DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tool(name: str, *argv: str) -> tuple[int, str]:
    got = subprocess.run(
        [sys.executable, str(TOOLS[name]), *argv], capture_output=True, text=True
    )
    return got.returncode, got.stdout + got.stderr


def rows(out: str, label: str) -> list[str]:
    """The file:line of each line of a tool's output that opens with label."""
    return [
        ln.split()[len(label.split())]
        for ln in out.splitlines()
        if ln.startswith(label + " ")
    ]


def source_of(where: str) -> str | None:
    """sources/ID.txt:N -> ID; a passage of no source -> None."""
    m = re.match(r"(?:sources/)?([\w-]+)\.txt:\d+$", where)
    return m.group(1) if m and m.group(1) in SOURCES else None


def passage(box: Path, where: str) -> str:
    """The text a file:line names, from the box's pile."""
    meta = json.loads((box / "kernel.json").read_text(encoding="utf-8"))
    path, line = where.rsplit(":", 1)
    lines = (Path(meta["pile"]) / path).read_text(encoding="utf-8").splitlines()
    return lines[int(line) - 1]


def build(work: Path, mirror: Path, wren: Path) -> dict[str, Path]:
    piles = {"sources": [("sources", mirror / "sources")], "wren": [("wren", wren)]}
    piles["all"] = [*piles["sources"], *piles["wren"], ("parody", mirror / "parody")]
    boxes = {}
    for name, parts in piles.items():
        pile = work / f"pile-{name}"
        for sub, src in parts:
            shutil.copytree(
                src, pile / sub if name == "all" else pile, dirs_exist_ok=True
            )
        boxes[name] = work / f"box-{name}"
        with contextlib.redirect_stdout(io.StringIO()):
            kernel.init(boxes[name], pile, work / f"box-{name}.key", NOW)
    return boxes


def judge(boxes: dict[str, Path], wren: Path, nonsense: bool) -> dict[str, dict]:
    say = (lambda s: NONSENSE) if nonsense else (lambda s: s)
    src, res = str(boxes["sources"]), {}

    # facts: two publishers, one trusted host, grove's four checks
    sys.path[:0] = [str(REPOS / "willows-grove"), str(REPOS / "willow-mcp" / "src")]
    from grove import seat_say  # noqa: E402
    from grove.seat_boxes import Box  # noqa: E402
    from urllib.parse import urlparse  # noqa: E402
    from willow_mcp.web_search import _trusted_host  # noqa: E402

    two, trusted, grove = {}, {}, {}
    for f in Q["facts"]:
        code, out = tool("claim_check.py", "--box", src, say(f["claim"]))
        found = rows(out, "all parts")
        pubs = sorted({SOURCES[s]["publisher"] for w in found if (s := source_of(w))})
        two[f["id"]] = {"all_parts": found, "publishers": pubs, "ok": len(pubs) >= 2}
        hosts = sorted(
            {urlparse(SOURCES[s]["url"]).hostname for w in found if (s := source_of(w))}
        )
        trusted[f["id"]] = {"hosts": hosts, "ok": any(_trusted_host(h) for h in hosts)}
        bx = [Box(id=f"b{i + 1}", kind="fact", label=source_of(w) or w, value=passage(boxes["sources"], w))
              for i, w in enumerate(found[:6])]  # fmt: skip
        sentence = say(f["sentence"]) + " " + " ".join(f"[{b.id}]" for b in bx)
        checks = seat_say.run_checks(sentence, bx)
        grove[f["id"]] = {"checks": checks, "ok": bool(bx) and seat_say.passed(checks)}
    res["facts"] = {"ok": all(v["ok"] for v in two.values()), "each": two}
    res["facts-trusted"] = {
        "ok": all(v["ok"] for v in trusted.values()),
        "each": trusted,
    }
    res["facts-grove"] = {"ok": all(v["ok"] for v in grove.values()), "each": grove}

    quotes = {}
    for q in Q["quotes"]:
        code, out = tool("quote_check.py", "--box", src, say(q["quote"]))
        quotes[q["id"]] = {
            "verbatim": rows(out, "verbatim"),
            "ok": bool(rows(out, "verbatim")),
        }
    res["quotes"] = {"ok": all(v["ok"] for v in quotes.values()), "each": quotes}

    t = {x["id"]: x for x in Q["traps"]}
    code, out = tool("claim_check.py", "--box", src, say(t["T1"]["claim"]))
    res["T1"] = {"ok": code == 42, "claim_exit": code, "out": out}
    code, out = tool("claim_check.py", "--box", src, say(t["T5"]["claim"]))
    _, contra = tool("contradictions.py", "--box", str(boxes["all"]))
    groups = re.split(r"\n(?=(?:DATE|AMOUNT) )", contra)
    beside = [g for g in groups if say(t["T5"]["line"]) in g and "sources/" in g]
    res["T5"] = {
        "ok": code == 42 and bool(beside),
        "claim_exit": code,
        "beside": beside,
    }

    code, out = tool("quote_check.py", "--box", src, say(t["T2"]["quote"]))
    _, near = tool("misquote.py", "--box", src, say(t["T2"]["quote"]))
    closest = rows(near, "closest")
    holds_q2 = {w.rsplit(":", 1)[0] for w in quotes["quote2"]["verbatim"]}
    res["T2"] = {"ok": code == 42 and bool(closest) and closest[0].rsplit(":", 1)[0] in holds_q2,
                 "quote_exit": code, "closest": closest, "misquote": near}  # fmt: skip

    code, out = tool("claim_check.py", "--box", src, say(t["T3"]["claim"]))
    res["T3"] = {"ok": code == 42, "claim_exit": code, "out": out}

    code, out = tool("quote_check.py", "--box", src, say(t["T4"]["quote"]))
    same, verb = rows(out, "same words"), rows(out, "verbatim")
    blind = kernel.words(say(t["T4"]["quote"])) == kernel.words("Qapla'")
    res["T4"] = {"ok": bool(same) and not verb and all(source_of(w) == "boqwi-q" for w in same) and blind,
                 "same_words": same, "verbatim": verb, "kernel_blind": blind}  # fmt: skip

    b = {x["id"]: x for x in Q["beats"]}
    code, out = tool(
        "claim_check.py", "--box", str(boxes["wren"]), say(b["death"]["text"])
    )
    res["death"] = {"ok": code == 42, "claim_exit": code, "out": out}
    late = sorted({m.group(0) for p in wren.rglob("*") if p.is_file()
                   for m in DATE.finditer(p.read_text(encoding="utf-8", errors="replace"))
                   if m.group(0) > Q["wren_today"]})  # fmt: skip
    res["dates"] = {"ok": not late, "after_today": late}

    got = subprocess.run([sys.executable, str(TOOLS["kernel.py"]), "bite", "--box", str(boxes["all"]),
                          "--now", NOW, say(b["G1"]["text"])], capture_output=True, text=True)  # fmt: skip
    served = [s["where"] for s in json.loads(got.stdout or "{}").get("served", [])]
    res["G1"] = {"ok": any(w.startswith("parody/") for w in served), "served": served}
    code, out = tool("claim_check.py", "--box", src, say(b["G2"]["text"]))
    res["G2"] = {"ok": code == 42, "claim_exit": code, "out": out}

    code, out = tool(
        "words_tlh.py",
        "bite",
        "--box",
        str(boxes["all"]),
        "--now",
        NOW,
        say(b["K1"]["text"]),
    )
    served = [
        s["where"]
        for s in json.loads(out.split("\n", 1)[0] if out.startswith("{") else "{}").get(
            "served", []
        )
    ]
    res["K1"] = {
        "ok": code == 0 and any(w.startswith("sources/boqwi-q") for w in served),
        "exit": code,
        "served": served,
    }

    plan = boxes["all"].parent / "order" / "M1.json"
    plan.parent.mkdir(exist_ok=True)
    plan.unlink(missing_ok=True)
    c1, o1 = tool("make_it_so.py", "plan", "--box", str(boxes["all"]), "--to", str(plan),
                  "--cmd", b["M1"]["cmd"], "--now", NOW, say(b["M1"]["text"]))  # fmt: skip
    c2, o2 = (
        tool("make_it_so.py", "check", "--box", str(boxes["all"]), str(plan))
        if c1 == 0
        else (None, "")
    )
    res["M1"] = {
        "ok": c1 == 0 and c2 == 0,
        "plan_exit": c1,
        "check_exit": c2,
        "check": o2.strip(),
    }

    # unseen, never sound: every line naming him holds a frozen line verbatim
    names = re.compile(Q["names"])
    known = [*(f["sentence"] for f in Q["facts"]), *(q["line"] for q in Q["quotes"]),
             *(x["line"] for x in Q["traps"]), *Q["fiction_lines"]]  # fmt: skip
    unseen, unlabelled = [], []
    for p in sorted(x for x in wren.rglob("*") if x.is_file()):
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines or not FICTION.search(lines[0]):
            unlabelled.append(str(p.relative_to(wren)))
        for n, ln in enumerate(lines, 1):
            if names.search(ln) and not any(k in ln for k in known):
                unseen.append(f"{p.relative_to(wren)}:{n}")
    res["unseen"] = {"ok": not unseen, "unseen": unseen}
    res["fiction"] = {"ok": not unlabelled, "unlabelled": unlabelled}
    return res


def verify_both(box: Path) -> dict:
    a = subprocess.run([sys.executable, str(TOOLS["kernel.py"]), "verify", "--box", str(box)],
                       capture_output=True, text=True)  # fmt: skip
    b = subprocess.run([sys.executable, str(TOOLS["willow-bot/one-script/kernel.py"]), "verify",
                        "--box", str(box)], capture_output=True, text=True)  # fmt: skip
    return {"ok": a.returncode == 0 and b.returncode == 0, "willow": a.returncode, "willow_bot": b.returncode,
            "willow_bot_said": (b.stdout + b.stderr).strip()[-400:]}  # fmt: skip


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        if a in ("--mirror", "--wren", "--work", "--box", "--now"):
            opts[a] = next(it, "")
        elif a == "--nonsense":
            opts[a] = True
        else:
            opts["bad"] = a
    if "bad" in opts or not all(
        opts.get(k) for k in ("--mirror", "--wren", "--work", "--box")
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    work, box, wren = Path(opts["--work"]), Path(opts["--box"]), Path(opts["--wren"])
    if work.exists() or box.exists():
        print("refused: --work and --box must not exist yet", file=sys.stderr)
        return kernel.REFUSED
    now = opts.get("--now") or NOW
    boxes = build(work, Path(opts["--mirror"]), wren)
    res = judge(boxes, wren, bool(opts.get("--nonsense")))
    with contextlib.redirect_stdout(io.StringIO()):
        kernel.init(box, work / "pile-all", box.parent / (box.name + ".key"), now)
    tools = {k: sha(p) if p.exists() else "missing" for k, p in TOOLS.items()}
    gate = "stewart-crossover" + (":nonsense" if opts.get("--nonsense") else "")
    for rule in Q["pass_rules"]:
        if rule == "verify":
            continue
        (work / "results.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        kernel.append(box, now, "verdict", who="stewart-crossover", gate=f"{gate}:{rule}",
                      state="satisfied" if res[rule]["ok"] else "failing",
                      results_sha256=sha(work / "results.json"), tools=tools)  # fmt: skip
    res["verify"] = verify_both(box)
    (work / "results.json").write_text(
        json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    kernel.append(box, now, "verdict", who="stewart-crossover", gate=f"{gate}:verify",
                  state="satisfied" if res["verify"]["ok"] else "failing",
                  results_sha256=sha(work / "results.json"), tools=tools)  # fmt: skip
    for rule in Q["pass_rules"]:
        print(f"{rule:14} {'held' if res[rule]['ok'] else 'FAILED'}")
    return 0 if all(r["ok"] for r in res.values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
