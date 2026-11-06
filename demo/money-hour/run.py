"""The money hour, judged: python run.py --mirror MIRROR --work WORK

Takes the slice of the markets mirror the table talks about (questions.json
names it) into WORK/slice, with any line longer than the kernel reads
written as its sentences, one a line, every word kept (bug #89). Then five
boxes, each over one folder and each with a key made for this run under
WORK/keys: `sources` over the slice, and one for each person over their own
folder in life/. Every rule in questions.json is judged by the add-on named
for it, run by its own command line, and the outcomes go to
WORK/results.json and, without anything a source says, results/run-N.json.

Freeze 2 adds two wider boxes, every line folded: `fed` (the FOMC's
statements and minutes, 2023 to 2026) and `filings` (the 55 10-Ks), with
`fed-unfolded` beside the first to show what folding changes. On them:
first-mention, timeline, sort by Hollis's themes, thesis on Teo's letter,
across over the four records, and the three stacks.

It stops where a person would take over. Each market call's close is
proposed from the slice's own SP500 rows, and the outcome waits on that
person's seal, which is theirs to give with their key; nothing here seals.

WORK must be outside the repository. make_life.py must have written life/.
"""

from __future__ import annotations

import glob
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STD = ROOT / "adapters" / "stdlib"
KERNEL = ROOT / "kernel.py"
LIFE = HERE / "life"
Q = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
PEOPLE = ["teodora", "bernadette", "hollis", "marisol"]
MAX_LINE = 500  # characters of a line the kernel reads


def next_run() -> int:
    """The next run's number: results/run-N.json are kept as they were, never rewritten."""
    done = [int(p.stem.split("-")[1]) for p in (HERE / "results").glob("run-*.json")]
    return max(done, default=0) + 1


SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"“$])")


def sh(*argv: str | Path) -> tuple[int, str]:
    got = subprocess.run(
        [sys.executable, *map(str, argv)], capture_output=True, text=True
    )
    return got.returncode, (got.stdout + got.stderr).strip()


def tool(name: str) -> Path:
    return next(p for p in (STD / name).glob("*.py") if not p.name.startswith("test_"))


def fold(text: str) -> str:
    """A line past the kernel's 500th character, as its sentences, one a line."""
    out = []
    for ln in text.splitlines():
        out += SENTENCE.split(ln) if len(ln) > MAX_LINE else [ln]
    return "\n".join(out) + "\n"


def make_slice(mirror: Path, work: Path) -> list[str]:
    dst = work / "slice"
    taken = []
    for pattern in Q["slice"]["from_mirror"]:
        for src in sorted(glob.glob(str(mirror / pattern))):
            rel = Path(src).relative_to(mirror)
            rel = (
                Path(*rel.parts[1:])
                if rel.parts[0] in ("web", "pdf", "csv", "parts")
                else rel
            )
            rel = (
                Path(*rel.parts[1:]) if rel.parts[0] == "csv" else rel
            )  # parts/csv/...
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                fold(Path(src).read_text(encoding="utf-8")), encoding="utf-8"
            )
            taken.append(rel.as_posix())
    return taken


def box(work: Path, name: str, pile: Path) -> Path:
    b, key = work / "boxes" / name, work / "keys" / f"{name}.key"
    key.parent.mkdir(parents=True, exist_ok=True)
    code, out = sh(KERNEL, "init", "--box", b, "--pile", pile, "--key", key)
    if code != 0:
        raise SystemExit(f"init {name}: {out}")
    return b


def claim(b: Path, words: str) -> list[tuple[str, str]]:
    """(kind, place) for every passage claim-check lists: 'all' or 'some'."""
    _, out = sh(tool("claim-check"), "--box", b, words, "--top", "50")
    rows = []
    for ln in out.splitlines():
        m = re.match(r"(all|some) parts\s+(\S+)", ln)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


def whole_in(b: Path, words: str, file: str) -> list[str]:
    return [place for kind, place in claim(b, words) if kind == "all" and file in place]


def closes(slice_: Path) -> dict[str, str]:
    """date -> close, from the slice's SP500 rows."""
    text = (slice_ / "fred/markets/SP500.csv.txt").read_text(encoding="utf-8")
    return dict(re.findall(r"\]\s*(\d{4}-\d\d-\d\d);\s*([\d.]+)", text))


def make_desk(mirror: Path, work: Path, name: str, folded: bool = True) -> Path:
    """One of freeze 2's wider piles, by questions.json's globs, every line folded."""
    dst = work / ("desk-" + name + ("" if folded else "-unfolded"))
    for pattern in Q["desk"][name]:
        for src in sorted(glob.glob(str(mirror / pattern))):
            kind = (
                "statements"
                if "/statements/" in src
                else "minutes"
                if "/minutes/" in src
                else "10-k"
            )
            out = dst / kind / Path(src).name
            out.parent.mkdir(parents=True, exist_ok=True)
            text = Path(src).read_text(encoding="utf-8")
            out.write_text(fold(text) if folded else text, encoding="utf-8")
    return dst


DECISION = re.compile(r"decided to (raise|lower|maintain) the target range")


def judge_desk(mirror: Path, work: Path, boxes: dict[str, Path], src: Path) -> dict:
    r: dict = {}
    fed = box(work, "fed", make_desk(mirror, work, "fed"))
    fed_raw = box(work, "fed-unfolded", make_desk(mirror, work, "fed", folded=False))
    filings = box(work, "filings", make_desk(mirror, work, "filings"))

    # fold: when did the minutes first say tariff?
    direct = next((p.name[:8] for p in sorted((work / "desk-fed" / "minutes").glob("*.txt"))
                   if "tariff" in p.read_text(encoding="utf-8").lower()), None)  # fmt: skip

    def first(b: Path) -> str | None:
        _, out = sh(tool("first-mention"), "--box", b, "tariffs")
        m = re.search(r"first mention of \"tariffs\": (\d{4}-\d\d-\d\d)", out)
        return m.group(1).replace("-", "") if m else None

    r["fold"] = {"held": first(fed) == direct, "direct": direct, "folded": first(fed),
                 "unfolded": first(fed_raw)}  # fmt: skip

    # timeline: the Fed's decisions, as Marisol would hand them to Lupe
    tl = work / "marisol-timeline.txt"
    sh(
        tool("timeline"),
        "--box",
        fed,
        "--to",
        tl,
        "Committee decided target range federal funds rate",
    )
    told: dict[str, str] = {}
    for ln in tl.read_text(encoding="utf-8").splitlines():
        m = re.search(r"statements/(\d{8})\.html\.txt:\d+\s+(.*)", ln)
        d = DECISION.search(m.group(2)) if m else None
        if d:
            told.setdefault(m.group(1), d.group(1))
    read = {}
    for p in sorted((work / "desk-fed" / "statements").glob("*.txt")):
        d = DECISION.search(p.read_text(encoding="utf-8"))
        if d:
            read[p.name[:8]] = d.group(1)
    raises_2026 = [k for k, v in told.items() if k.startswith("2026") and v == "raise"]
    r["timeline"] = {"held": told == read and raises_2026 == ["20260916"],
                     "meetings": len(read), "in_timeline": len(told),
                     "path": {y: " ".join(told[k][0] for k in sorted(told) if k.startswith(y))
                              for y in ("2023", "2024", "2025", "2026")}}  # fmt: skip

    # sort: Hollis's themes over the 55 10-Ks
    _, out = sh(
        tool("sort"), "--box", filings, "--categories", HERE / "themes.txt", "--json"
    )
    rep = json.loads(out)
    placed: dict[str, set[str]] = {}
    for g in rep["groups"]:
        for row in g["rows"]:
            placed.setdefault(g["name"], set()).add(
                row["where"].split("/")[-1].split("-20")[0]
            )
    companies = {
        p.name.split("-20")[0] for p in (work / "desk-filings" / "10-k").glob("*.txt")
    }
    seen = set().union(*placed.values()) if placed else set()
    r["sort"] = {"held": len(companies) == 55 and companies <= seen,
                 "themes": {k: sorted(v) for k, v in placed.items()}}  # fmt: skip

    # thesis: Teo's letter, draft and final
    def thesis(file: Path) -> dict:
        _, out = sh(tool("thesis"), "--box", src, file, "--json")
        return json.loads(out)

    letter = LIFE / "teodora" / "letter" / "2026-11.md"
    first_line = 3  # the heading, a blank line, then one sentence a line
    final = thesis(letter)
    short = sorted(int(row["where"].rsplit(":", 1)[1]) - first_line + 1
                   for g in final["groups"] if g["name"] == "short" for row in g["rows"])  # fmt: skip
    blur = Q["letter"]["blur"]
    blur_line = Q["letter"]["final"][blur["line"] - 1]
    first_named = next((row["where"] for g in final["groups"] if g["name"] == "held"
                        for row in g["rows"] if row["what"].startswith(f"line {blur['line'] + first_line - 1} ")),
                       None)  # fmt: skip
    oct_holds = whole_in(src, blur_line, blur["file"])
    draft = thesis(LIFE / "teodora" / "letter" / "2026-11-draft.md")
    r["thesis"] = {"held": short == [Q["letter"]["slip"]] and bool(oct_holds),
                   "final": final["said"], "short_sentences": short,
                   "line_2_first_named": first_named, "line_2_also": oct_holds[:1],
                   "draft": draft["said"]}  # fmt: skip
    r["T6"] = {"held": Q["letter"]["slip"] in short}

    # across: one page over the four records
    _, out = sh(tool("across"), *[a for p in PEOPLE for a in ("--box", boxes[p])],
                "digest", "--", "--now", "2026-11-05T12:00:00Z")  # fmt: skip
    (work / "across.txt").write_text(out + "\n", encoding="utf-8")
    waiting = re.findall(r"digest: populated, (\d+) waiting", out)
    r["across"] = {"held": waiting == ["1"] * 4, "waiting": waiting}

    # the stacks
    codes = {}
    for name, b in (
        ("fed.md", fed),
        ("filings.md", filings),
        ("money-hour.md", boxes["teodora"]),
    ):
        code, out = sh(tool("stack"), "--box", b, "--stack", HERE / name)
        (work / f"stack-{name}.txt").write_text(out + "\n", encoding="utf-8")
        codes[name] = code
    r["stacks"] = {"held": all(c in (0, 42) for c in codes.values()), "exits": codes}
    return r


def judge(mirror: Path, work: Path) -> dict:
    taken = make_slice(mirror, work)
    src = box(work, "sources", work / "slice")
    boxes = {p: box(work, p, LIFE / p) for p in PEOPLE}
    r: dict[str, dict] = {"slice": {"files": len(taken)}}

    for f in Q["facts"]:
        found = whole_in(src, f["claim"], f["file"])
        r[f["id"]] = {"held": bool(found), "where": found[:3], "who": f["who"]}
    q = Q["quote"]
    code, out = sh(tool("quote-check"), "--box", src, q["text"])
    r["V1"] = {"held": code == 0 and q["file"] in out, "where": out.split()[-1:]}

    for t in Q["traps"]:
        if t["id"] in ("T1", "T4"):
            wrong = [p for k, p in claim(src, t["wrong"]) if k == "all"]
            right = whole_in(src, t["right"], t["file"])
            r[t["id"]] = {"held": not wrong and bool(right), "wrong_whole_in": wrong,
                          "right_whole_in": right[:3]}  # fmt: skip
        elif t["id"] == "T3":
            wrong = whole_in(src, t["wrong"], t["file"])
            right = whole_in(src, t["right"], t["file"])
            r["T3"] = {"held": not wrong and bool(right), "wrong_whole_in": wrong,
                       "right_whole_in": right}  # fmt: skip
        elif t["id"] == "T2":
            _, out = sh(tool("misquote"), "--box", src, t["quote"])
            named = [f"{a} -> {b}" for a, b in t["changed"] if f"{a} -> {b}" in out]
            r["T2"] = {"held": t["file"] in out and len(named) == len(t["changed"]),
                       "named": named}  # fmt: skip
        elif t["id"] == "T5":
            _, out = sh(tool("pair-drift"), "--box", boxes["hollis"],
                        "--full", "10-k-paragraph.md", "--summary", "summary.md")  # fmt: skip
            only = re.findall(r"summary\.md:\d+\s+(\S+)", out)
            want = t["drifted"].replace(
                " billion", "B"
            )  # pair-drift's own form: $95.8B
            r["T5"] = {
                "held": only == [want],
                "only_in_summary": only,
                "expected": [want],
            }

    sp = closes(work / "slice")
    days = sorted(sp)
    r["calls"] = []
    for c in Q["calls"]:
        b = boxes[c["who"]]
        made, _ = sh(tool("market-calls"), "call", "--box", b, "--p", str(c["p"]),
                     "--now", c["made"], c["symbol"], c["kind"], c["date"])  # fmt: skip
        close, prev = sp[c["date"]], sp[days[days.index(c["date"]) - 1]]
        _, out = sh(tool("market-calls"), "close", "--box", b, "--now", c["closed"],
                    c["symbol"], c["date"], close, prev)  # fmt: skip
        happened = (float(close) > float(prev) if c["kind"] == "up"
                    else float(close) > float(c["kind"].split(":")[1]))  # fmt: skip
        verdict = (
            "even"
            if c["p"] == 0.5
            else "right"
            if (c["p"] > 0.5) == happened
            else "wrong"
        )
        r["calls"].append({"who": c["who"], "call": f"{c['symbol']} {c['kind']} {c['date']} p {c['p']}",
                           "made": made == 0, "close": close, "before": prev,
                           "happened": happened, "once_sealed": verdict,
                           "waiting": "waiting on your seal" in out})  # fmt: skip
    r["calls-made"] = {"held": all(c["made"] for c in r["calls"])}
    r["calls-closed"] = {"held": all(c["waiting"] for c in r["calls"])}

    code, _ = sh(HERE / "make_life.py", "--mirror", mirror, "--check")
    r["lines"] = r["after"] = {"held": code == 0}

    code, out = sh(
        tool("stack"), "--box", boxes["teodora"], "--stack", HERE / "money-hour.md"
    )
    (work / "stack.txt").write_text(out + "\n", encoding="utf-8")
    _, said = sh(tool("said"), "--box", boxes["teodora"])
    speakers = sorted(set(re.findall(r"^\S+\s+(Marisol|Bernie|Hollis)\b", said, re.M)))
    r["stack"] = {"held": code in (0, 42) and speakers == ["Bernie", "Hollis", "Marisol"],
                  "exit": code, "said_speakers": speakers}  # fmt: skip

    r.update(judge_desk(mirror, work, boxes, src))

    verified = {}
    for name in ["sources", *PEOPLE, "fed", "fed-unfolded", "filings"]:
        code, out = sh(KERNEL, "verify", "--box", work / "boxes" / name)
        verified[name] = out.splitlines()[-1] if out else ""
    r["verify"] = {"held": all("holds" in v and " 0 sealed" in v for v in verified.values()),
                   "boxes": verified}  # fmt: skip
    return r


def main(argv: list[str]) -> int:
    if len(argv) != 4 or argv[0] != "--mirror" or argv[2] != "--work":
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    mirror, work = Path(argv[1]).resolve(), Path(argv[3]).resolve()
    if ROOT in work.parents or work == ROOT:
        print("refused: WORK must be outside the repository", file=sys.stderr)
        return 2
    if not LIFE.is_dir():
        print("refused: run make_life.py first", file=sys.stderr)
        return 2
    if work.exists():
        shutil.rmtree(work)
    r = judge(mirror, work)
    (work / "results.json").write_text(json.dumps(r, indent=1) + "\n", encoding="utf-8")
    rules = [k for k, v in r.items() if isinstance(v, dict) and "held" in v]
    held = [k for k in rules if r[k]["held"]]
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    n = next_run()
    (out / f"run-{n}.json").write_text(
        json.dumps(r, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    for k in rules:
        print(f"{'held  ' if r[k]['held'] else 'FAILED'} {k}")
    for c in r["calls"]:
        print(f"  {c['who']:<10} {c['call']:<34} closed {c['close']} (before {c['before']}): "
              f"once sealed, {c['once_sealed']}")  # fmt: skip
    print(f"run {n}: {len(held)} of {len(rules)} rules held")
    return 0 if len(held) == len(rules) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
