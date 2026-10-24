"""latent.py: rank a scan index's passages by meaning, not just words.

    python adapters/deps/latent/latent.py rank --index INDEX
        [--changed-from INDEX] [--top N] "your question"

The kernel, and scan's BM25, match words: a question that says "memory
exhausted" misses code that says "out of memory". This ranks a scan index by
latent semantic analysis instead — TF-IDF over the passages, then a
truncated SVD, so words that keep the same company (a synonym pair, a term
and its abbreviation) sit close, and a question reaches a passage that shares
its sense without sharing its words. Offline: it downloads no model.

It reads an index that [scan](../../stdlib/scan/) built; it never reads a
folder itself. With `--changed-from INDEX`, it ranks only the passages that
index lacks (a release against its fix), as scan's own `--changed-from` does.
Each answer is a JSON line like scan's, each passage with its rank, file and
line:

    {"state": "populated", "served": [{"rank": 1, "where": "main/rfc1867.c:849",
      "id": "5731…", "text": "…"}]}

It is not the kernel's answer: ranked by meaning, it serves passages a `bite`
would not, so nothing it prints can be cited into an approval. On willow's
own PHP2Shell demo it placed the fix's code in the top three more often than
BM25 (demo/php2shell): 84% against 80%, and 94% against 88% on the two CVEs
no model had seen.

Needs numpy. Exit codes, the kernel's: 0 something ranked, 42 nothing did
(no shared sense, or the index held nothing), 2 refused (a bad command line,
not an index, or numpy missing).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
import kernel  # noqa: E402
import scan  # noqa: E402

COMPONENTS = 200  # SVD dimensions kept; capped by the passages and terms there are


def space(ix: "scan.Index", lacked: set | None):
    """The LSA space of the index's passages (those `lacked` doesn't hold, if
    given): the kept passages, each term's column, its idf, the right factor
    V and the passages projected into the reduced space."""
    import numpy as np

    idxs = [i for i, c in enumerate(ix.pile) if lacked is None or c["id"] not in lacked]
    toks = [kernel.words(ix.pile[i]["text"]) for i in idxs]
    df: dict[str, int] = {}
    for t in toks:
        for w in set(t):
            df[w] = df.get(w, 0) + 1
    terms = sorted(df)
    col = {w: j for j, w in enumerate(terms)}
    n, m = len(idxs), len(terms)
    if n < 2 or m < 2:
        return idxs, col, None, None, None
    idf = np.array([np.log((n + 1) / (df[w] + 1)) + 1.0 for w in terms])
    tfidf = np.zeros((n, m), dtype=np.float64)
    for r, t in enumerate(toks):
        for w in t:
            tfidf[r, col[w]] += 1.0
    tfidf *= idf
    norm = np.linalg.norm(tfidf, axis=1, keepdims=True)
    tfidf /= np.where(norm == 0, 1.0, norm)
    k = max(2, min(COMPONENTS, n - 1, m - 1))
    _, s, vt = np.linalg.svd(tfidf, full_matrices=False)
    return idxs, col, idf, vt[:k], tfidf @ vt[:k].T


def rank(
    ix: "scan.Index", question: str, top: int, lacked: set | None = None
) -> list[dict]:
    """The index's passages most like `question` by meaning, best first."""
    import numpy as np

    idxs, col, idf, vt, docz = space(ix, lacked)
    if vt is None:
        return []
    qv = np.zeros(len(col))
    for w in kernel.words(question):
        if w in col:
            qv[col[w]] += 1.0
    qv *= idf
    if np.linalg.norm(qv) == 0:
        return []
    qz = qv @ vt.T
    qn = np.linalg.norm(qz)
    dn = np.linalg.norm(docz, axis=1)
    if qn == 0:
        return []
    sims = (docz @ qz) / np.where(dn == 0, 1.0, dn) / qn
    order = np.argsort(-sims, kind="stable")
    out = []
    for j in order[:top]:
        if sims[j] <= 1e-9:
            break
        c = ix.pile[idxs[j]]
        out.append({"rank": len(out) + 1, "where": f"{c['path']}:{c['line']}",
                    "id": c["id"], "echo": kernel.echo(question, c["text"]),
                    "text": c["text"]})  # fmt: skip
    return out


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "rank":
        return usage()
    opts, args, it = {}, [], iter(argv[1:])
    for a in it:
        if a in ("--index", "--changed-from", "--top"):
            opts[a] = next(it, "")
            if not opts[a]:
                return usage()
        elif a.startswith("--"):
            return usage()
        else:
            args.append(a)
    top = opts.get("--top", "3")
    if "--index" not in opts or len(args) != 1 or not top.isdigit() or int(top) < 1:
        return usage()
    try:
        import numpy  # noqa: F401
    except ImportError:
        print("refused: latent needs numpy (pip install numpy)", file=sys.stderr)
        return kernel.REFUSED
    try:
        ix = scan.Index(Path(opts["--index"]))
        lacked = None
        if "--changed-from" in opts:
            lacked = {c["id"] for c in scan.passages(Path(opts["--changed-from"]))}
        served = rank(ix, args[0], int(top), lacked)
    except (OSError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    print(json.dumps({"state": "populated" if served else "empty", "served": served},
                     ensure_ascii=False))  # fmt: skip
    return kernel.ALIVE if served else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
