"""arms.py: the study's reported arms, beside the pass rules. None is scored.

    python demo/percus-yevick/arms.py --work WORK --out FILE
        [--questions NAME ...] [--model-text FILE ...]
        [--url URL] [--models NAME,NAME] [--dry]

WORK is pipeline.py's --work, after it has built the pile and the index. This
adds a kernel box over that pile (WORK/box, with words.txt as its words list,
its key beside it) and runs, on the same questions (author and null unless
named):

- **rankers:** each question's top three by the kernel, the kernel through
  words.txt, scan's BM25, pile-rungs (words, then the folder's phrases) and
  latent (meaning; needs numpy, else said not run), each scored by score.py;
- **why-not:** for each author question the kernel found nothing for, which
  words found nothing and what kind of file would have answered;
- **predict:** before each author question's bite on the box, what the box's
  record says it will come to, graded after;
- **contradictions:** once over the box, two passages giving a different
  date or amount for the same thing;
- **claims:** for each --model-text (a model's derivation, as text), each
  sentence through claim-check and each line holding "=" through misquote:
  what the stack backs, almost backs, or has no part of;
- **found, then arranged:** each author question through local-model, a
  model on this machine answering only from the passages the kernel served,
  for each of --models at --url; and same-way, each asked three times. An
  entry MODEL@none (or @low, @medium, @high) asks that model with that
  reasoning, so qwen3:8b,qwen3:8b@none sets its reasoning beside none;
- **model cards:** every card in models/ added to the box's record;
- **expectations:** expectations.json graded against the kernel's finds.

--dry asks every question as nonsense and passes nonsense for each model
text, as pipeline.py's --dry does: the wiring, not the results. Since
nonsense finds nothing, no model would be asked; a dry run's arranged arm
asks two of its questions of a box holding one nonsense passage instead, so
the models are really called, about nothing. A runner,
not an add-on: it calls the add-ons' own command lines, writes only under
WORK and to --out, and is not part of CI. Exit 0 always; it reports.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STDLIB = ROOT / "adapters" / "stdlib"
sys.path[:0] = [
    str(ROOT),
    str(STDLIB / "scan"),
    str(ROOT / "adapters" / "deps" / "latent"),
    str(HERE),
]
import kernel  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402

TOP = 3
CLAIMS_AT_MOST = (
    60  # sentences of a model text checked, and lines holding "=": the first ones
)
USAGE = ("usage: arms.py --work WORK --out FILE [--questions NAME ...] [--model-text FILE ...]"
         " [--url URL] [--models NAME,NAME] [--dry]")  # fmt: skip


def tool(script: str, *args: str, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(STDLIB / script), *args],
                          capture_output=True, text=True, timeout=timeout)  # fmt: skip


def questions(sets: list[str], dry: bool) -> list[dict]:
    out = []
    for name in sets:
        qs = scan.questions(
            (HERE / "questions" / f"{name}.txt").read_text(encoding="utf-8")
        )
        for n, (qid, q) in enumerate(qs, 1):
            out.append({"set": name, "id": qid, "step": qid.split(".")[0],
                        "asked": f"qqqq zzzz {n}" if dry else q})  # fmt: skip
    return out


def box_for(work: Path) -> Path:
    box = work / "box"
    if not (box / "kernel.json").exists():
        # the kernel reads a words list only its owner can read, which git
        # can't keep: a copy under WORK, made private
        wl = work / "words.txt"
        wl.write_bytes((HERE / "words.txt").read_bytes())
        wl.chmod(0o600)
        with contextlib.redirect_stdout(io.StringIO()):
            made = kernel.init(box, work / "pile", work / "box.key", kernel.now(), wl)
        if made != kernel.ALIVE:
            raise SystemExit(f"refused: couldn't make a box at {box}")
    return box


def found_by(q: dict, texts: list[str]) -> dict:
    return {"hit": q["step"] in score.BY_ID and any(score.hit(q["step"], t) for t in texts),
            "steps": sorted({s for t in texts for s in score.steps_held(t)})}  # fmt: skip


def rankers(idx, qs: list[dict], pile: Path) -> dict:
    alias, _ = kernel.parse_words((HERE / "words.txt").read_text(encoding="utf-8"))
    try:
        import latent
        import numpy  # noqa: F401

        # latent builds its space (an SVD over every passage) on each call;
        # built once here and reused for every question, the add-on unchanged
        built = latent.space(idx, None)
        latent.space = lambda ix, lacked: built
        by_meaning = lambda q: [c["text"] for c in latent.rank(idx, q, TOP)]  # noqa: E731
    except ImportError:
        by_meaning = None
    out: dict[str, list] = {
        "kernel": [],
        "kernel+words": [],
        "bm25": [],
        "pile-rungs": [],
        "latent": [],
    }
    for q in qs:
        a = q["asked"]
        out["kernel"].append(found_by(q, [c["text"] for c in idx.rank(a, {}, TOP)]))
        out["kernel+words"].append(
            found_by(q, [c["text"] for c in idx.rank(a, alias, TOP)])
        )
        out["bm25"].append(found_by(q, [c["text"] for c in idx.bm25(a, TOP)]))
        got = tool(
            "pile-rungs/pile_rungs.py", "--from", str(pile), "--top", str(TOP), a
        )
        try:
            ans = json.loads(got.stdout.strip().splitlines()[-1])
            out["pile-rungs"].append({**found_by(q, [c["text"] for c in ans.get("served", [])]),
                                      "rung": ans.get("rung")})  # fmt: skip
        except (ValueError, IndexError):
            out["pile-rungs"].append({"hit": False, "steps": [], "rung": None,
                                      "error": (got.stderr or got.stdout).strip()[-200:]})  # fmt: skip
        out["latent"].append(
            found_by(q, by_meaning(a))
            if by_meaning
            else {"hit": False, "steps": [], "not run": "numpy"}
        )
    return out


def summary(qs: list[dict], ranked: dict) -> dict:
    out = {}
    for name, rows in ranked.items():
        per = {}
        for set_name in sorted({q["set"] for q in qs}):
            pairs = [(q, r) for q, r in zip(qs, rows) if q["set"] == set_name]
            if set_name == "null":
                per[set_name] = (
                    f"{sum(bool(r['steps']) for _, r in pairs)} of {len(pairs)} served a chain step"
                )
            else:
                hit = {q["step"] for q, r in pairs if r["hit"]}
                chain = sorted(hit & set(score.CHAIN))
                ext = sorted(hit & set(score.EXTENDED))
                per[set_name] = (
                    f"{len(chain)} of {len(score.CHAIN)} steps found: {', '.join(chain) or 'none'}"
                )
                if any(q["step"] in score.EXTENDED for q, _ in pairs):
                    per[set_name + " extended"] = (
                        f"{len(ext)} of {len(score.EXTENDED)} found: {', '.join(ext) or 'none'}"
                    )
        if any("not run" in r for r in rows):
            per = {"not run": "latent needs numpy"}
        out[name] = per
    return out


def why_not(box: Path, qs: list[dict], ranked: dict) -> list[dict]:
    out = []
    for q, r in zip(qs, ranked["kernel"]):
        if q["set"] == "null" or r["hit"]:
            continue
        got = tool("why-not/why_not.py", "--box", str(box), q["asked"], "--json")
        try:
            out.append({"id": q["id"], "report": json.loads(got.stdout)})
        except ValueError:
            out.append(
                {"id": q["id"], "error": (got.stderr or got.stdout).strip()[-200:]}
            )
    return out


def predict(box: Path, qs: list[dict]) -> dict:
    for q in qs:
        if q["set"] != "null":
            tool("predict/predict.py", "ask", "--box", str(box), q["asked"])
    got = tool("predict/predict.py", "score", "--box", str(box), "--json")
    try:
        return json.loads(got.stdout)
    except ValueError:
        return {"error": (got.stderr or got.stdout).strip()[-200:]}


def contradictions(box: Path) -> dict:
    got = tool("contradictions/contradictions.py", "--box", str(box))
    lines = got.stdout.strip().splitlines()
    return {"exit": got.returncode, "last": lines[-1] if lines else got.stderr.strip()[-200:],
            "disagreements": [x for x in lines if x.startswith(("AMOUNT", "DATE"))]}  # fmt: skip


def claims(box: Path, text: str) -> dict:
    """A model text, sentence by sentence through claim-check, and its lines
    holding "=" through misquote."""
    flat = " ".join(text.split())
    sentences = [
        s for s in re.split(r"(?<=[.!?])\s+", flat) if len(kernel.words(s)) >= 3
    ][:CLAIMS_AT_MOST]
    formulas = [
        x.strip() for x in text.splitlines() if "=" in x and len(x.strip()) > 3
    ][:CLAIMS_AT_MOST]
    kinds = {"all parts": 0, "some parts": 0, "no part": 0, "refused": 0}
    for s in sentences:
        got = tool("claim-check/claim_check.py", "--box", str(box), s)
        if got.returncode == 2:
            kinds["refused"] += 1
        elif "all parts" in got.stdout:
            kinds["all parts"] += 1
        elif "some parts" in got.stdout:
            kinds["some parts"] += 1
        else:
            kinds["no part"] += 1
    near = []
    for f in formulas:
        got = tool("misquote/misquote.py", "--box", str(box), f, "--json")
        try:
            rep = json.loads(got.stdout)
            near.append(
                {
                    "formula": f[:160],
                    "state": rep.get("state"),
                    "line": rep.get("line", ""),
                }
            )
        except ValueError:
            near.append(
                {"formula": f[:160], "error": (got.stderr or got.stdout).strip()[-200:]}
            )
    return {
        "sentences": len(sentences),
        "claim-check": kinds,
        "formulas": len(formulas),
        "misquote": near,
    }


def variant(entry: str) -> tuple[str, str]:
    """A --models entry: a model, or a model and its reasoning, MODEL@none.
    The reasoning goes to the server as reasoning_effort; none given, none is
    sent, and the model reasons as it does by default."""
    model, _, reasoning = entry.partition("@")
    if reasoning not in ("", "none", "low", "medium", "high"):
        raise SystemExit(f"refused: {entry}: reasoning is none, low, medium or high")
    return model, reasoning


def arranged(
    box: Path, qs: list[dict], url: str, models: list[str], work: Path
) -> dict:
    out: dict = {}
    asked = [q for q in qs if q["set"] != "null"]
    qfile = work / "arranged-questions.txt"
    qfile.write_text("".join(q["asked"] + "\n" for q in asked), encoding="utf-8")
    for entry in models:
        m, reasoning = variant(entry)
        extra = ["--reasoning", reasoning] if reasoning else []
        rows = []
        for q in asked:
            got = tool("local-model/local_model.py", "ask", "--box", str(box), "--url", url, "--model", m,
                       *extra, q["asked"], timeout=1800)  # fmt: skip
            rows.append({"id": q["id"], "exit": got.returncode,
                         "said": (got.stdout or got.stderr).strip()[-400:]})  # fmt: skip
        same = tool("same-way/same_way.py", "--box", str(box), "--url", url, "--model", m,
                    *extra, "--questions", str(qfile), timeout=3600)  # fmt: skip
        out[entry] = {
            "local-model": rows,
            "same-way": (same.stdout or same.stderr).strip().splitlines()[-1:],
        }
    return out


def plumbing_box(work: Path) -> Path:
    """The dry run's box for the models: one passage holding the nonsense the
    dry run asks, so the kernel serves it and the model is really called."""
    pile, box = work / "plumbing-pile", work / "plumbing-box"
    if not (box / "kernel.json").exists():
        pile.mkdir(parents=True, exist_ok=True)
        (pile / "nonsense.txt").write_text(
            # the words, not in the question's order: a passage that repeats
            # the question back is an echo, and the kernel serves no echo
            "Here zzzz comes before qqqq, numbered 2 and then 1, as nonsense.\n",
            encoding="utf-8",
        )  # fmt: skip
        with contextlib.redirect_stdout(io.StringIO()):
            if (
                kernel.init(box, pile, work / "plumbing-box.key", kernel.now())
                != kernel.ALIVE
            ):
                raise SystemExit(f"refused: couldn't make a box at {box}")
    return box


def cards(box: Path) -> list[str]:
    out = []
    for card in sorted((HERE / "models").glob("*.md")):
        got = tool(
            "model-card/model_card.py", "add", "--box", str(box), "--from", str(card)
        )
        out.append((got.stdout or got.stderr).strip())
    return out


def expectations(qs: list[dict], ranked: dict) -> dict:
    exp = json.loads((HERE / "expectations.json").read_text(encoding="utf-8"))["steps"]
    found = {
        q["step"]
        for q, r in zip(qs, ranked["kernel"])
        if q["set"] == "author" and r["hit"]
    }
    held = [s for s, e in exp.items() if e["found"] == (s in found)]
    return {
        "held": f"{len(held)} of {len(exp)}",
        "missed": sorted(set(exp) - set(held)),
    }


def say(arm: str) -> None:
    print(f"{kernel.now()}  {arm}", file=sys.stderr, flush=True)


def main(argv: list[str]) -> int:
    opts, sets, texts, dry, i = {}, [], [], False, 0
    while i < len(argv):
        if argv[i] == "--dry":
            dry, i = True, i + 1
        elif argv[i] in ("--questions", "--model-text") and i + 1 < len(argv):
            (sets if argv[i] == "--questions" else texts).append(argv[i + 1])
            i += 2
        elif argv[i] in ("--work", "--out", "--url", "--models") and i + 1 < len(argv):
            opts[argv[i]], i = argv[i + 1], i + 2
        else:
            break
    if i != len(argv) or not {"--work", "--out"} <= set(opts):
        print(USAGE, file=sys.stderr)
        return 2
    work = Path(opts["--work"])
    if not (work / "index" / "index.json").exists():
        print("refused: run pipeline.py with this --work first", file=sys.stderr)
        return 2
    qs = questions(sets or ["author", "null"], dry)
    idx = scan.Index(work / "index")
    box = box_for(work)
    say("cards")
    report: dict = {"dry": dry, "cards": cards(box)}
    say("rankers")
    ranked = rankers(idx, qs, work / "pile")
    report["rankers"] = summary(qs, ranked)
    say("why-not")
    report["why-not"] = why_not(box, qs, ranked)
    say("predict")
    report["predict"] = predict(box, qs)
    say("contradictions")
    report["contradictions"] = contradictions(box)
    say("claims")
    report["claims"] = {}
    for t in texts:
        body = (
            "qqqq zzzz yyyy xxxx. vvvv = wwww.\n"
            if dry
            else Path(t).read_text(encoding="utf-8")
        )
        report["claims"][Path(t).name] = claims(box, body)
    say("arranged")
    if "--url" in opts and "--models" in opts and dry:
        # nonsense finds nothing in the stack, so no model would be asked: two
        # of its questions, asked of a box holding one nonsense passage
        first = [q for q in qs if q["set"] != "null"][:2]
        report["arranged"] = arranged(plumbing_box(work), first, opts["--url"],
                                      opts["--models"].split(","), work)  # fmt: skip
    elif "--url" in opts and "--models" in opts:
        report["arranged"] = arranged(
            box, qs, opts["--url"], opts["--models"].split(","), work
        )
    else:
        report["arranged"] = "not run: no --url and --models"
    report["expectations"] = expectations(qs, ranked)
    report["verify"] = tool(
        "../../kernel.py", "verify", "--box", str(box)
    ).stdout.strip()
    Path(opts["--out"]).write_text(
        json.dumps(report, indent=1) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ("why-not", "rankers")},
            indent=1,
        )[:4000]
    )
    print(json.dumps(report["rankers"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
