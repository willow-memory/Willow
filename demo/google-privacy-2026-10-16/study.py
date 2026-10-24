"""study.py: what Google's privacy policy says, before and after 2026-10-16,
asked in the reporters' words. Frozen, with its rules, before it ran.

    python demo/google-privacy-2026-10-16/study.py --pile PILE --work DIR --box DIR --out FILE

PILE is fetch.py's `--to`, checked against sources.json first; nothing here
goes online. DIR is a scratch folder, outside the repo, for the mirrors,
indexes and kernel boxes it builds; --box is a kernel record, outside the
repo, that each pass rule's result is written to as a row; --out gets every
answer, scored, one JSON line each.

The pipeline, each step an add-on or the kernel's own command:

    pdf mirror           each version's PDF to text, a page a paragraph
    clauses mirror       that text to one sentence a passage; Google's pages too
    clauses diff --to    the new version's added and reworded sentences
    scan index / scan    each version indexed; questions asked of the whole
                         and --changed-from the other, by the kernel's rank
                         and by BM25, top 3
    kernel init / bite   the claims asked of boxes on each version and on the
                         changed sentences alone, for the kernel's own `look`
    quote-check          the reporters' quotes of the policy, against each

Before anything is asked, every line of reporters.txt, claims.txt and
policy-quotes.txt but `study-plain` (the study's own words) must be in the
saved reporting verbatim, by quote-check, or the run is refused.

The hit rule (targets.json): a question asked of the new version lands
when the opt-in exception's clause is among the 3 passages served; of the
old, when the default clause is. `opt-in` names the four other sentences
the change added about letting services share data; served alone they are
reported, never counted as landing.

The pass rules, every one decided before any question was asked:

| Rule | Asked | Passes when |
|---|---|---|
| changed-kernel | reporters.txt, new --changed-from old, the kernel's rank | the exception lands for at least 6 of 10, and above random draws of 3 from the changed set, one-sided binomial p < 0.01 |
| changed-bm25 | the same, BM25 | the same |
| whole-new | reporters.txt, the whole new version, kernel | the exception lands for at least 5 of 10, p < 0.01 against 3 of the whole |
| whole-old | reporters.txt, the whole old version, kernel | the default lands for at least 5 of 10, p < 0.01 likewise |
| blind-kernel | blind-reporters.txt, changed, kernel | lands for at least 15 of 30, p < 0.01 |
| blind-bm25 | the same, BM25 | the same |
| null-changed | null.txt, changed, kernel | the exception lands for at most 3 of 30, and its rate is below reporters.txt's |
| null-whole | null.txt, the whole new version, kernel | at most 3 of 30 |
| no-support | claims.txt and blind-claims.txt, kernel bite on the new version, the old and the changed sentences | no passage served supports a claim (targets.json's groups, by the kernel's `holds`) |
| names-it | claims.txt, kernel bite on the changed sentences alone | for every claim, the kernel's look says no file in the folder has its word (targets.json `absent`) |
| probe | targets.json's probe, kernel bite on each version | the analyze clause is served on both, and is the same sentence in both |
| renderings | the target clauses, against Google's own web page of each version | the default is in the old page and not the new; the exception and the four opt-in sentences are in the new and not the old; the analyze clause is in both (same words, by quote-check) |

Reported, not judged: quote-check's answer for each quote in
policy-quotes.txt, against each version (the author had read the reporting
before freezing); and how many of the clause diff's changed sentences are in
their own version's page (some are the PDF's labels joined to a sentence,
which no web page holds).

Exit 0 when every rule passes, 42 when one fails (a finding, not a bug), 2
for a bad command line or a pile that doesn't match sources.json.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "quote-check"))
import kernel  # noqa: E402
import quote_check  # noqa: E402

PDF = ROOT / "adapters" / "deps" / "pdf" / "pdf.py"
CLAUSES = ROOT / "adapters" / "stdlib" / "clauses" / "clauses.py"
SCAN = ROOT / "adapters" / "stdlib" / "scan" / "scan.py"
NOW = "2026-10-24T12:00:00Z"
TOP = 3
ALPHA = 0.01
TARGETS = json.loads((HERE / "targets.json").read_text(encoding="utf-8"))
PDF_NAME = "google_privacy_policy_en.pdf.txt.txt"
PAGE = {"old": "archive-20261001.html.txt", "new": "privacy-current.html.txt"}


def sh(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)], capture_output=True, text=True
    )


def step(*argv) -> None:
    """One building step, which must work: a refusal stops the run, said."""
    got = sh(*argv)
    if got.returncode not in (0, 42):
        raise SystemExit(
            f"refused: {Path(str(argv[0])).name} {argv[1]}: {got.stderr.strip()}"
        )


def questions(name: str) -> list[tuple[str, str]]:
    out = []
    for line in (HERE / "questions" / name).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            q, _, text = line.partition("\t")
            out.append((q, text))
    return out


# ── building: mirrors, the changed sentences, indexes, boxes ────────────────
def build(pile: Path, work: Path) -> None:
    for v, folder in (("old", "policy-old"), ("new", "policy-new")):
        if not (work / "clauses" / v).exists():
            step(PDF, "mirror", "--from", pile / folder, "--to", work / "text" / v)
            step(
                CLAUSES,
                "mirror",
                "--from",
                work / "text" / v,
                "--to",
                work / "clauses" / v,
            )
        if not (work / "ix" / v).exists():
            (work / "ix").mkdir(parents=True, exist_ok=True)
            step(SCAN, "index", "--from", work / "clauses" / v, "--to", work / "ix" / v)
    if not (work / "clauses" / "news").exists():
        step(
            CLAUSES,
            "mirror",
            "--from",
            pile / "news",
            "--to",
            work / "clauses" / "news",
        )
    if not (work / "clauses" / "pages").exists():
        step(
            CLAUSES,
            "mirror",
            "--from",
            pile / "google-pages",
            "--to",
            work / "clauses" / "pages",
        )
    if not (work / "changed").exists():
        step(CLAUSES, "diff", "--old", work / "clauses" / "old" / PDF_NAME,
             "--new", work / "clauses" / "new" / PDF_NAME, "--to", work / "changed")  # fmt: skip
    for v, pile_of in (("old", work / "clauses" / "old"), ("new", work / "clauses" / "new"),
                       ("changed", work / "changed")):  # fmt: skip
        box = work / "boxes" / v
        if not (box / "record.jsonl").exists():
            (work / "keys").mkdir(parents=True, exist_ok=True)
            with contextlib.redirect_stdout(io.StringIO()):
                kernel.init(box, pile_of, work / "keys" / f"{v}.key", NOW)


def ids(ix: Path) -> list[str]:
    return [
        json.loads(s)["id"]
        for s in (ix / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    ]


# ── asking ──────────────────────────────────────────────────────────────────
def scan(
    work: Path, side: str, qs: list[tuple[str, str]], changed: bool, rank: str
) -> list[dict]:
    qfile = work / "q.txt"
    qfile.write_text("".join(f"{n}\t{t}\n" for n, t in qs), encoding="utf-8")
    other = "old" if side == "new" else "new"
    argv = [SCAN, "scan", "--index", work / "ix" / side, "--questions", qfile, "--top", TOP,
            "--rank", rank]  # fmt: skip
    if changed:
        argv += ["--changed-from", work / "ix" / other]
    got = sh(*argv)
    if got.returncode not in (0, 42):
        raise SystemExit(f"refused: scan: {got.stderr.strip()}")
    return [json.loads(s) for s in got.stdout.splitlines() if s.strip()]


def level(served: list[dict], side: str) -> str:
    texts = [s["text"] for s in served]
    if side == "new":
        if TARGETS["exception"]["text"] in texts:
            return "exception"
        return "opt-in" if set(texts) & set(TARGETS["opt-in"]["texts"]) else "miss"
    return "default" if TARGETS["default"]["text"] in texts else "miss"


def tail(n: int, k: int, p: float) -> float:
    """P(X >= k), X binomial(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def test(rows: list[dict], want: str, at_least: int, pool: int) -> dict:
    hits = sum(r["level"] == want for r in rows)
    p0 = min(1.0, TOP / pool)
    p = tail(len(rows), hits, p0)
    return {"lands": hits, "of": len(rows), "random_rate": round(p0, 4), "p": p,
            "pass": hits >= at_least and p < ALPHA}  # fmt: skip


def bite(work: Path, box: str, text: str) -> dict:
    got = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "bite", "--box",
                          str(work / "boxes" / box), "--now", NOW, text],
                         capture_output=True, text=True)  # fmt: skip
    doc = json.loads(got.stdout) if got.stdout.strip() else {}
    return {"exit": got.returncode, **doc}


def supports(text: str, needs: list[str]) -> bool:
    toks = kernel.forms(w.lower() for w in kernel.words(text))
    groups = TARGETS["support"]["groups"]
    return all(any(kernel.holds(w, toks) for w in groups[g]) for g in needs)


# ── the run ─────────────────────────────────────────────────────────────────
def run(pile: Path, work: Path, out: Path) -> dict:
    build(pile, work)
    news = kernel.chunks(work / "clauses" / "news")
    for file in ("reporters.txt", "claims.txt", "policy-quotes.txt"):
        for name, q in questions(file):
            if name != "study-plain" and not any(
                k == "verbatim" for k, _ in quote_check.find(news, q)
            ):
                raise SystemExit(
                    f"refused: {file} {name} is not in the reporting verbatim"
                )
    old_ids, new_ids = ids(work / "ix" / "old"), ids(work / "ix" / "new")
    pool = {
        "changed": len(set(new_ids) - set(old_ids)),
        "new": len(new_ids),
        "old": len(old_ids),
    }
    answers: list[dict] = []

    def ask(tag: str, file: str, side: str, changed: bool, rank: str) -> list[dict]:
        rows = []
        for a in scan(work, side, questions(file), changed, rank):
            r = {"test": tag, "set": file, "side": side, "changed": changed, "rank": rank,
                 "question": a["question"], "state": a["state"],
                 "served": [{"where": s["where"], "text": s["text"]} for s in a["served"]]}  # fmt: skip
            r["level"] = level(a["served"], side)
            rows.append(r)
        answers.extend(rows)
        return rows

    rep_ck = ask("changed-kernel", "reporters.txt", "new", True, "kernel")
    rep_cb = ask("changed-bm25", "reporters.txt", "new", True, "bm25")
    rep_wn = ask("whole-new", "reporters.txt", "new", False, "kernel")
    rep_wo = ask("whole-old", "reporters.txt", "old", False, "kernel")
    bl_ck = ask("blind-kernel", "blind-reporters.txt", "new", True, "kernel")
    bl_cb = ask("blind-bm25", "blind-reporters.txt", "new", True, "bm25")
    nu_c = ask("null-changed", "null.txt", "new", True, "kernel")
    nu_w = ask("null-whole", "null.txt", "new", False, "kernel")
    ask("reported:whole-new-bm25", "reporters.txt", "new", False, "bm25")
    ask("reported:old-changed-kernel", "reporters.txt", "old", True, "kernel")

    t = {
        "changed-kernel": test(rep_ck, "exception", 6, pool["changed"]),
        "changed-bm25": test(rep_cb, "exception", 6, pool["changed"]),
        "whole-new": test(rep_wn, "exception", 5, pool["new"]),
        "whole-old": test(rep_wo, "default", 5, pool["old"]),
        "blind-kernel": test(bl_ck, "exception", 15, pool["changed"]),
        "blind-bm25": test(bl_cb, "exception", 15, pool["changed"]),
    }
    rate = t["changed-kernel"]["lands"] / max(t["changed-kernel"]["of"], 1)
    for tag, rows in (("null-changed", nu_c), ("null-whole", nu_w)):
        hits = sum(r["level"] == "exception" for r in rows)
        t[tag] = {"lands": hits, "of": len(rows),
                  "pass": hits <= 3 and (tag == "null-whole" or hits / len(rows) < rate)}  # fmt: skip

    # the absence: claims asked of the kernel itself, for its own look
    needs, absent = TARGETS["support"]["needs"], TARGETS["support"]["absent"]
    claims = [(n, q, n) for n, q in questions("claims.txt")]
    claims += [(n, q, n.rsplit("-v", 1)[0]) for n, q in questions("blind-claims.txt")]
    supported, named = [], []
    for name, text, base in claims:
        for box in ("new", "old", "changed"):
            b = bite(work, box, text)
            served = b.get("served", [])
            sup = [s["where"] for s in served if supports(s["text"], needs[base])]
            looks = [h["why"] for h in b.get("look", [])]
            r = {"test": "claims", "question": name, "box": box, "exit": b["exit"],
                 "state": b.get("state"), "served": [{"where": s["where"], "text": s["text"]}
                 for s in served], "supports": sup, "look": looks}  # fmt: skip
            answers.append(r)
            supported += [(name, box, w) for w in sup]
            if box == "changed" and name == base:
                word = absent[base]
                says = any(w.startswith("no file in your folder has") and
                           word in w.split("has", 1)[1].replace(",", " ").split() for w in looks)  # fmt: skip
                named.append((name, says))
    t["no-support"] = {
        "supported": supported,
        "asked": len(claims) * 3,
        "pass": not supported,
    }
    t["names-it"] = {"said": sum(s for _, s in named), "of": len(named),
                     "missing": [n for n, s in named if not s], "pass": all(s for _, s in named)}  # fmt: skip

    # the probe: the test can find support where the policy gives it
    probe = {}
    for box in ("new", "old"):
        b = bite(work, box, TARGETS["probe"])
        probe[box] = [s["text"] for s in b.get("served", [])]
        answers.append(
            {"test": "probe", "box": box, "exit": b["exit"], "served": probe[box]}
        )
    an = TARGETS["analyze"]["text"]
    t["probe"] = {"pass": an in probe["new"] and an in probe["old"] and
                  an not in (work / "changed" / PDF_NAME).read_text(encoding="utf-8")}  # fmt: skip

    # the renderings: Google's own page of each version holds the same clauses
    pages = {v: [c for c in kernel.chunks(work / "clauses" / "pages") if c["path"] == PAGE[v]]
             for v in ("old", "new")}  # fmt: skip

    def holds_in(v: str, text: str) -> bool:
        return bool(quote_check.find(pages[v], text))

    only_new = [TARGETS["exception"]["text"], *TARGETS["opt-in"]["texts"]]
    judged = {"default: old page, not new": holds_in("old", TARGETS["default"]["text"])
              and not holds_in("new", TARGETS["default"]["text"]),
              "exception and opt-in: new page, not old": all(holds_in("new", x) and not
              holds_in("old", x) for x in only_new),
              "analyze: both pages": holds_in("old", TARGETS["analyze"]["text"])
              and holds_in("new", TARGETS["analyze"]["text"])}  # fmt: skip
    diff = sh(CLAUSES, "diff", "--old", work / "clauses" / "old" / PDF_NAME,
              "--new", work / "clauses" / "new" / PDF_NAME).stdout.splitlines()  # fmt: skip
    old_side = [x[4:] for x in diff if x.startswith("  - ")]
    old_side += [x.split("   ", 2)[2] for x in diff if x.startswith("removed ")]
    new_side = [x[4:] for x in diff if x.startswith("  + ")]
    new_side += [x.split("   ", 2)[2] for x in diff if x.startswith("added ")]
    t["renderings"] = {**judged, "pass": all(judged.values()),
                       "reported: changed sentences in their own page": f"old {sum(map(lambda x: holds_in('old', x), old_side))} of {len(old_side)}, new {sum(map(lambda x: holds_in('new', x), new_side))} of {len(new_side)}"}  # fmt: skip

    # reported, not judged: the reporters' quotes of the policy
    quotes = {}
    for name, q in questions("policy-quotes.txt"):
        quotes[name] = {v: [f"{k} {p}" for k, p in quote_check.find(
            kernel.chunks(work / "clauses" / v), q)] or ["not there"] for v in ("old", "new")}  # fmt: skip
        answers.append({"test": "quotes", "question": name, **quotes[name]})

    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for a in answers:
            f.write(json.dumps(a, sort_keys=True, ensure_ascii=False) + "\n")
    return {"pool": pool, "tests": t, "quotes": quotes,
            "passes": {k: v["pass"] for k, v in t.items()}}  # fmt: skip


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if len(argv) != 8 or set(opts) != {"--pile", "--work", "--box", "--out"}:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    pile, work, box, out = (
        Path(opts[k]) for k in ("--pile", "--work", "--box", "--out")
    )
    if sh(HERE / "fetch.py", "--to", pile, "--check").returncode != 0:
        print("refused: the pile doesn't match sources.json; fetch.py --check says how",
              file=sys.stderr)  # fmt: skip
        return 2
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):
            if (
                kernel.init(box, HERE, box.parent / (box.name + ".key"), NOW)
                != kernel.ALIVE
            ):
                print(f"refused: couldn't start a record at {box}", file=sys.stderr)
                return 2
    result = run(pile, work, out)
    tools = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
        "kernel.py", "adapters/stdlib/scan/scan.py", "adapters/stdlib/clauses/clauses.py",
        "adapters/deps/pdf/pdf.py", "adapters/stdlib/quote-check/quote_check.py",
        "demo/google-privacy-2026-10-16/study.py")}  # fmt: skip
    answers_sha = hashlib.sha256(out.read_bytes()).hexdigest()
    for test, passed in result["passes"].items():
        kernel.append(box, NOW, "verdict", who="google-privacy", gate=f"study:{test}",
                      state="satisfied" if passed else "failing",
                      answers_sha256=answers_sha, tools=tools)  # fmt: skip
    print(json.dumps(result, indent=1, ensure_ascii=False))
    return 0 if all(result["passes"].values()) else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
