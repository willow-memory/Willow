"""rules_study.py: does the kernel serve the right rule to a worker's question?

    python demo/blackout/rules_study.py run --pile PILE --to DIR [--dry] [--box STUDYBOX]

PILE is what fetch.py kept (the rules, by the hashes in sources.json, which a run
checks first and refuses on). The eCFR sections in it, as plain text, are the
one box this asks: seven files of Rule 10b-5, 10b5-1, 10b5-2 and Regulation FD.
The Federal Register release and the sec.gov files are pinned too, but a PDF has
no reader here and the study asks only the rules themselves.

It asks the questions in questions/ (a worker's own words, each with the rule file
it should reach and the words a served passage must hold; some that no rule
answers; some that are nonsense) and scores three pass rules, which are frozen
before any is asked:

- S1: at least 8 of the 12 worker's questions are served, among their first three
  passages, one from the right file that holds its words;
- S2: at most 2 of the 6 questions no rule answers are served anything;
- S3: none of the 6 nonsense questions is served anything.

Every miss is written down with what was served. The kernel's rank is the
kernel's: nothing here loosens it. `--dry` asks every question as nonsense over
the pile plus one nonsense passage, to see the wiring after the kernel run (a
passage is served, the hit rule reads it) and scores nothing; `--box STUDYBOX`
appends one kernel row a rule to a box outside the repo. Exit 0 when the run ran
and a rule or two failed is still 0 only if all passed; 42 when a rule failed;
2 when refused.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import make_life  # noqa: E402
from kernel import canon, h256  # noqa: E402

KERNEL = ROOT / "kernel.py"
QUESTIONS = HERE / "questions"
TOP = 3  # the first passages looked at
RULES = {
    "S1": ("at least 8 of the 12 worker's questions are served, among their first three "
           "passages, one from the right file that holds its words", 8),
    "S2": ("at most 2 of the 6 questions no rule answers are served anything", 2),
    "S3": ("none of the 6 nonsense questions is served anything", 0),
}  # fmt: skip
TOOLS = ["kernel.py", "demo/blackout/rules_study.py", "demo/blackout/fetch.py",
         "demo/blackout/make_life.py", "demo/blackout/sources.json"]  # fmt: skip
DRY = "qqqq zzzz"


def lines_of(path: Path) -> list[list[str]]:
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            out.append([x.strip() for x in ln.split("|")])
    return out


def norm(text: str) -> str:
    """Case, quotes and runs of space set aside, so a phrase is found as it reads."""
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    return re.sub(r"\s+", " ", text).lower()


def held(pile: Path) -> list[str]:
    """What of the pile is not as pinned: [] when every source holds."""
    bad = []
    for s in json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]:
        p = pile / s["folder"] / s["file"]
        if not p.is_file():
            bad.append(f"{s['folder']}/{s['file']}: missing")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != s["sha256"]:
            bad.append(f"{s['folder']}/{s['file']}: differs")
    return bad


def hit(served: list[dict], want_file: str, phrase: str) -> bool:
    """Among the first three passages, one from the right file that holds the words."""
    return any(
        s["where"].split(":")[0].endswith(want_file + ".txt") and norm(phrase) in norm(s["text"])
        for s in served[:TOP]
    )  # fmt: skip


def score(asked: dict) -> dict:
    """The three pass rules, from what each question was served."""
    s1 = sum(a["hit"] for a in asked["workers"])
    s2 = sum(bool(a["served"]) for a in asked["offtopic"])
    s3 = sum(bool(a["served"]) for a in asked["nonsense"])
    return {
        "S1": {
            "state": "pass" if s1 >= RULES["S1"][1] else "fail",
            "number": s1,
            "needed": f">= {RULES['S1'][1]} of {len(asked['workers'])}",
        },  # fmt: skip
        "S2": {
            "state": "pass" if s2 <= RULES["S2"][1] else "fail",
            "number": s2,
            "needed": f"<= {RULES['S2'][1]} of {len(asked['offtopic'])}",
        },  # fmt: skip
        "S3": {
            "state": "pass" if s3 <= RULES["S3"][1] else "fail",
            "number": s3,
            "needed": f"<= {RULES['S3'][1]} of {len(asked['nonsense'])}",
        },  # fmt: skip
    }


def bite(box: Path, question: str) -> tuple[int, list[dict]]:
    got = subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(box), question,
                          "--now", "2026-11-19T09:00:00Z"], capture_output=True, text=True)  # fmt: skip
    doc = json.loads(got.stdout)
    return got.returncode, [
        {"where": s["where"], "text": s["text"]} for s in doc["served"]
    ]


def build(pile: Path, to: Path, dry: bool) -> Path:
    mirror = to / "mirror"
    mirror.mkdir(parents=True)
    for p in sorted((pile / "ecfr").glob("*.xml")):
        (mirror / f"{p.stem}.txt").write_text(
            make_life.rules_text(p.read_text(encoding="utf-8")), encoding="utf-8"
        )
    if dry:
        (mirror / "dry.txt").write_text(
            "qqqq is not zzzz, says the one dry passage.\n", encoding="utf-8"
        )
    box = to / "box"
    with contextlib.redirect_stdout(io.StringIO()):
        made = kernel.init(box, mirror, to / "key", kernel.now())
    if made != kernel.ALIVE:
        raise SystemExit(f"refused: couldn't start a box at {box}")
    return box


def ask(box: Path, dry: bool) -> dict:
    asked: dict[str, list[dict]] = {"workers": [], "offtopic": [], "nonsense": []}
    for qid, q, want, phrase in lines_of(QUESTIONS / "workers.txt"):
        code, served = bite(box, DRY if dry else q)
        h = hit(served, "dry" if dry else want, "dry passage" if dry else phrase)
        asked["workers"].append({"id": qid, "question": q, "code": code, "served": served,
                                 "hit": h, "want": want})  # fmt: skip
    for kind in ("offtopic", "nonsense"):
        for qid, q in lines_of(QUESTIONS / f"{kind}.txt"):
            code, served = bite(box, DRY if dry else q)
            asked[kind].append(
                {"id": qid, "question": q, "code": code, "served": served}
            )
    return asked


def verdict_rows(study: Path, results: dict, dry: bool) -> None:
    if not (study / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):
            made = kernel.init(
                study, HERE, study.parent / (study.name + ".key"), kernel.now()
            )
        if made != kernel.ALIVE:
            raise SystemExit(f"refused: couldn't start a record at {study}")
    tools = {rel: h256((ROOT / rel).read_text(encoding="utf-8")) for rel in TOOLS}
    brief = {k: [{x: v for x, v in a.items() if x in ("id", "hit", "code")}
                 | {"served": [s["where"] for s in a["served"]]} for a in rows]
             for k, rows in results["asked"].items()}  # fmt: skip
    answers = h256(canon(brief))
    for rule, v in results["scored"].items():
        gate = f"blackout-rules:{'dry:' if dry else ''}{rule}"
        kernel.append(study, kernel.now(), "verdict", who="blackout", gate=gate,
                      state=v["state"], number=v["number"], needed=v["needed"],
                      rule=RULES[rule][0], answers_sha256=answers, tools=tools)  # fmt: skip


def main(argv: list[str]) -> int:
    opts = {a: argv[i + 1] for i, a in enumerate(argv)
            if a in ("--pile", "--to", "--box") and i + 1 < len(argv)}  # fmt: skip
    dry = "--dry" in argv
    if (argv[:1] != ["run"] or not {"--pile", "--to"} <= opts.keys()
            or any(a.startswith("--") and a not in ("--pile", "--to", "--box", "--dry")
                   for a in argv)):  # fmt: skip
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    pile, to = Path(opts["--pile"]), Path(opts["--to"])
    bad = held(pile)
    if bad or to.exists():
        print(
            "refused: " + ("; ".join(bad) if bad else f"{to} is already there"),
            file=sys.stderr,
        )
        return 2
    box = build(pile, to, dry)
    asked = ask(box, dry)
    if dry:
        # wiring only: every question was nonsense, and a dry passage was served and read
        scored = {r: {"state": "wired" if all(a["served"] for a in asked["workers"]) else "broke",
                      "number": 0, "needed": "wiring"} for r in RULES}  # fmt: skip
    else:
        scored = score(asked)
    results = {"dry": dry, "asked": asked, "scored": scored}
    (to / "results.json").write_text(
        json.dumps(results, indent=1, sort_keys=True) + "\n"
    )
    for rule, v in scored.items():
        print(f"{rule}  {v['state']:6} {v['number']} ({v['needed']})  {RULES[rule][0]}")
    for a in asked["workers"]:
        if not dry and not a["hit"]:
            print(f"  MISS {a['id']}: {a['question']}\n       wanted {a['want']}; served "
                  f"{[s['where'] for s in a['served']] or 'nothing'}")  # fmt: skip
    if "--box" in opts:
        verdict_rows(Path(opts["--box"]), results, dry)
        print(
            f"verdicts appended to {opts['--box']}: kernel.py verify --box {opts['--box']}"
        )
    return 0 if all(v["state"] in ("pass", "wired") for v in scored.values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
