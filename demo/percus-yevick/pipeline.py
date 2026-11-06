"""pipeline.py: the finding half of the study, in one command.

    python demo/percus-yevick/pipeline.py --stack DIR --work DIR --out FILE
        [--questions NAME ...] [--box DIR] [--dry [--seed N]]

Builds the pile from fetch.py's --to (DIR/<slug>/src/ and export.xml) with
the repo's own readers: latex for each paper's prose, equations for its
math, mediawiki for each Wikipedia revision, pdf (which needs pypdf) for
a scanned paper's text, and bibtex for references/, the paywalled originals
by reference only. Indexes it once with scan, asks
each question set in questions/ (author, null and every blind set unless
named), takes the
kernel's top three passages, and scores each against steps.json with
score.py. Writes every question's served passages, the steps they hold, the
traps and the Wertheim flag to --out, and prints the table.

R4's random passages are drawn by tally.SEED, frozen; `--seed` takes
another only with `--dry`. `--box` appends each pass rule's verdict to a
box outside the repo as a kernel row.

`--dry` asks every question as nonsense ("qqqq zzzz" and its number) in its
place: the dry run, which shows wiring breaks before anything is frozen and
sees no result. A dry run that serves anything is itself a finding.

--work holds the pile and the index; --out is a JSON file. Neither belongs
in the repo. A runner, not an add-on: it calls the add-ons' own command
lines and is not part of CI. Exit 0, or 2 on a bad command line; it
reports, it does not judge.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STDLIB = ROOT / "adapters" / "stdlib"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(STDLIB / "scan"))
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402
import kernel  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402
import tally  # noqa: E402

TOP = 3
#: the question sets asked unless --questions names others: blind-prompt.txt
#: is the prompt the blind set was written from, not a set
SETS = ["author", "null"] + sorted(
    p.stem for p in (HERE / "questions").glob("blind-*.txt") if p.stem != "blind-prompt"
)
#: each kind of source, the readers that make its text, under adapters/
READERS = {
    "arxiv": [
        ("prose", "stdlib/latex/latex.py"),
        ("math", "stdlib/equations/equations.py"),
    ],
    "wikipedia": [("wiki", "stdlib/mediawiki/mediawiki.py")],
    "pdf": [("scan", "deps/pdf/pdf.py")],
}


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(stack: Path, work: Path) -> Path:
    """The pile, one folder per reader and source, and its index."""
    pile = work / "pile"
    for s in json.loads(fetch.LIST.read_text(encoding="utf-8"))["sources"]:
        here = stack / fetch.slug(s["id"])
        src = here if s["kind"] == "wikipedia" else here / "src"
        for part, script in READERS[s["kind"]]:
            to = pile / part / fetch.slug(s["id"])
            if to.exists():
                continue
            got = subprocess.run([sys.executable, str(ROOT / "adapters" / script), "mirror",
                                  "--from", str(src), "--to", str(to)],
                                 capture_output=True, text=True)  # fmt: skip
            line = (got.stdout.strip().splitlines() or [got.stderr.strip()])[-1]
            print(f"{part:<6} {s['id']}: {line}")
    refs = pile / "refs"  # the paywalled originals, by reference only
    if not refs.exists():
        got = subprocess.run([sys.executable, str(STDLIB / "bibtex" / "bibtex.py"), "mirror",
                              "--from", str(HERE / "references"), "--to", str(refs)],
                             capture_output=True, text=True)  # fmt: skip
        print(
            f"refs   references/: {(got.stdout.strip().splitlines() or [got.stderr.strip()])[-1]}"
        )
    index = work / "index"
    if not (index / "index.json").exists():
        index.mkdir(parents=True, exist_ok=True)
        scan.build(pile, index)
    return index


def ask(idx: "scan.Index", sets: list[str], dry: bool) -> list[dict]:
    rows = []
    for name in sets:
        qs = scan.questions(
            (HERE / "questions" / f"{name}.txt").read_text(encoding="utf-8")
        )
        for n, (qid, q) in enumerate(qs, 1):
            asked = f"qqqq zzzz {n}" if dry else q
            served = idx.rank(asked, {}, TOP)
            step = qid.split(".")[0]
            rows.append({
                "set": name, "id": qid, "asked": asked,
                "served": [{"path": c["path"], "line": c["line"], "id": c["id"],
                            "steps": score.steps_held(c["text"]),
                            "traps": score.traps(c["text"])} for c in served],
                "hit": step in score.BY_ID and any(score.hit(step, c["text"]) for c in served),
                "wertheim": step in score.BY_ID and score.through_wertheim(
                    [c["text"] for c in served if score.hit(step, c["text"])]),
            })  # fmt: skip
    return rows


def table(rows: list[dict]) -> str:
    out = []
    for r in rows:
        held = sorted({s for c in r["served"] for s in c["steps"]})
        traps = sorted({t for c in r["served"] for t in c["traps"]})
        mark = "HIT " if r["hit"] else "    "
        out.append(f"{mark}{r['set']:<7}{r['id']:<7}served {len(r['served'])}  "
                   f"steps {','.join(held) or '-'}  traps {','.join(traps) or '-'}"
                   + ("  WERTHEIM" if r["wertheim"] else ""))  # fmt: skip
    return "\n".join(out)


def verdicts(
    box: Path, ts: str, result: dict, dry: bool, answers: str, tools: dict
) -> None:
    """Each rule's verdict, one kernel row each, on a box outside the repo; a
    dry run's are named dry so they are never read as the study's."""
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):  # its own "ready" line
            if (
                kernel.init(box, HERE, box.parent / (box.name + ".key"), ts)
                != kernel.ALIVE
            ):
                raise SystemExit(f"refused: couldn't start a record at {box}")
    for rule, v in result.items():
        kernel.append(box, ts, "verdict", who="percus-yevick",
                      gate=f"percus-yevick:{'dry:' if dry else ''}{rule}", state=v["state"],
                      number=v["number"], needed=v["needed"],
                      answers_sha256=answers, tools=tools)  # fmt: skip


def main(argv: list[str]) -> int:
    opts, sets, dry, i = {}, [], False, 0
    while i < len(argv):
        if argv[i] == "--dry":
            dry, i = True, i + 1
        elif argv[i] == "--questions" and i + 1 < len(argv):
            sets.append(argv[i + 1])
            i += 2
        elif argv[i] in (
            "--stack",
            "--work",
            "--out",
            "--seed",
            "--box",
        ) and i + 1 < len(argv):
            opts[argv[i]], i = argv[i + 1], i + 2
        else:
            break
    need = {"--out", "--stack", "--work"}
    seed = opts.get("--seed", str(tally.SEED))
    if seed != str(tally.SEED) and not dry:
        print(f"pipeline.py: R4's seed is frozen at {tally.SEED}; another is for a dry run",
              file=sys.stderr)  # fmt: skip
        return 2
    if i != len(argv) or not need <= set(opts) or not seed.isdigit():
        print("usage: pipeline.py --stack DIR --work DIR --out FILE [--questions NAME ...]"
              " [--seed N] [--box DIR] [--dry]", file=sys.stderr)  # fmt: skip
        return 2
    idx = scan.Index(build(Path(opts["--stack"]), Path(opts["--work"])))
    rows = ask(idx, sets or SETS, dry)
    text_of = {c["id"]: c["text"] for c in idx.pile}
    authors = sum(r["set"] == "author" for r in rows)
    # a dry run draws, but its passages hold nothing: the wiring, not the count
    hit = (lambda s, t: False) if dry else score.hit
    drawn = tally.draw(idx.pile, authors, int(seed), hit)
    result = tally.tally(rows, text_of, drawn)
    record = {
        "dry": dry,
        "seed": int(seed),
        "verdicts": result,
        "tools": {rel: sha_file(ROOT / rel) for rel in (
            "kernel.py", "adapters/stdlib/scan/scan.py", "adapters/stdlib/latex/latex.py",
            "adapters/stdlib/equations/equations.py", "adapters/stdlib/mediawiki/mediawiki.py",
            "adapters/deps/pdf/pdf.py", "adapters/stdlib/bibtex/bibtex.py",
            "demo/percus-yevick/score.py", "demo/percus-yevick/steps.json",
            "demo/percus-yevick/tally.py", "demo/percus-yevick/pipeline.py")},
        "rows": rows,
    }  # fmt: skip
    Path(opts["--out"]).write_text(
        json.dumps(record, indent=1) + "\n", encoding="utf-8"
    )
    print(table(rows))
    print()
    for rule, v in result.items():
        print(
            f"{rule}  {v['state']:<15} {v['number']}"
            + (f"  (needed: {v['needed']})" if v["needed"] else "")
        )
    if "--box" in opts:
        answers = sha_file(Path(opts["--out"]))
        verdicts(
            Path(opts["--box"]), kernel.now(), result, dry, answers, record["tools"]
        )
        print(
            f"verdicts appended to {opts['--box']}: kernel.py verify --box {opts['--box']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
