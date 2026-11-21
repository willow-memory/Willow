"""latent.py: rank a scan index's passages by meaning, not just words.

    python adapters/deps/latent/latent.py rank --index INDEX
        [--changed-from INDEX] [--only FILE] [--top N] [--to SPACE]
        ("your question" | --questions FILE)

The kernel, and scan's BM25, match words: a question that says "memory
exhausted" misses code that says "out of memory". This ranks a scan index by
latent semantic analysis instead — TF-IDF over the passages, then a
truncated SVD, so words that keep the same company (a synonym pair, a term
and its abbreviation) sit close, and a question reaches a passage that shares
its sense without sharing its words. Offline: it downloads no model.

It reads an index that [batch-ask](../../stdlib/batch-ask/) built; it never reads a
folder itself. With `--changed-from INDEX`, it ranks only the passages that
index lacks (a release against its fix), as scan's own `--changed-from` does.
With `--only FILE`, it ranks only the passages FILE names: another add-on's
output (scan's or latent's JSON lines, or ripgrep's and code-shape's
`path:line  id  text` lines, or one id a line), so a word search can pick the
few hundred to rank by meaning. Each answer is a JSON line like scan's, each
passage with its rank, file and line:

    {"state": "populated", "served": [{"rank": 1, "where": "main/rfc1867.c:849",
      "id": "5731…", "text": "…"}]}

`--questions FILE` asks each question of FILE (scan's format: one a line, or
`name<TAB>question`) and builds the space once for them all, one JSON line
each with its `question` name.

`--to SPACE` keeps the built space in the file SPACE, and the next run that
ranks the very same passages reads it there instead of building it again. It
is the build that takes the minutes, so a folder that hasn't changed is asked
in the time a question takes. A space is kept for one set of passages: the
index's, less what `--changed-from` and `--only` leave out. Any other set
builds again and replaces it. Standard error says which happened.

It is not the kernel's answer: ranked by meaning, it serves passages a `bite`
would not, so nothing it prints can be cited into an approval. On willow's
own PHP2Shell demo it placed the fix's code in the top three more often than
BM25 (demo/php2shell): 84% against 80%, and 94% against 88% on the two CVEs
no model had seen.

Needs numpy. Exit codes, the kernel's: 0 something ranked (for one question
of FILE, at least), 42 nothing did (no shared sense, or the index held
nothing), 2 refused (a bad command line, not an index, numpy missing, an
`--only` FILE that names no passage of the index, or an index past LIMIT's
matrix: it says the passage count and the memory it would need; or a `--to`
that is there and is not a space latent kept, or whose folder is not there).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "batch-ask"))
import kernel  # noqa: E402
import scan  # noqa: E402

COMPONENTS = 200  # SVD dimensions kept; capped by the passages and terms there are
#: The most the dense TF-IDF matrix may take (passages x terms x 8 bytes). Past
#: it a question is refused before anything is allocated: the SVD's time grows
#: past minutes and its memory to several times the matrix (the card's numbers).
LIMIT = 2**29  # 512 MiB: about 8,000 passages of code, 85 s and 3.8 GiB a question


def gib(b: int) -> str:
    return f"{b / 2**30:.1f} GiB"


#: A passage id, whole (64 hex) or cut as ripgrep and code-shape print it (12)
HEX = re.compile(r"[0-9a-f]{12,64}")


def ids_in(text: str) -> tuple[int, list[str]]:
    """The passage ids another add-on printed, and how many of its lines were
    ones latent reads: JSON lines with `served` (scan's, latent's), lines
    whose second field is an id (`path:line  id  text`, ripgrep's and
    code-shape's), or a bare id a line. Any other line (a summary) is skipped."""
    rows, ids = 0, []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("{"):
            row = json.loads(s)
            if not isinstance(row, dict) or "served" not in row:
                raise ValueError("a JSON line in it names no served passages")
            rows += 1
            ids += [x["id"] for x in row["served"]]
            continue
        f = s.split()
        hit = f[0] if len(f) == 1 else f[1] if len(f) > 1 else ""
        if HEX.fullmatch(hit):
            rows += 1
            ids.append(hit)
    return rows, ids


def resolve(ix: "scan.Index", ids: list[str]) -> tuple[set, int]:
    """The whole ids of the index's passages `ids` name (each a whole id or
    its first 12 or more characters), and how many named none."""
    by12: dict[str, list[str]] = {}
    for c in ix.pile:
        by12.setdefault(c["id"][:12], []).append(c["id"])
    got, missed = set(), 0
    for i in ids:
        hits = [w for w in by12.get(i[:12], []) if w.startswith(i)]
        got.update(hits)
        missed += not hits
    return got, missed


def chosen(ix: "scan.Index", lacked: set | None, only: set | None) -> list[int]:
    """Which of the index's passages are ranked: those `lacked` doesn't hold,
    and only those in `only`, if given."""
    return [i for i, c in enumerate(ix.pile)
            if (lacked is None or c["id"] not in lacked)
            and (only is None or c["id"] in only)]  # fmt: skip


def space(ix: "scan.Index", lacked: set | None, only: set | None = None):
    """The LSA space of the index's passages (those `lacked` doesn't hold, and
    only those in `only`, if given): the kept passages, each term's column,
    its idf, the right factor V and the passages projected into the reduced
    space."""
    import numpy as np

    idxs = chosen(ix, lacked, only)
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
    if n * m * 8 > LIMIT:
        raise ValueError(
            f"{n} passages and {m} terms need a {gib(n * m * 8)} matrix, and its "
            f"SVD several times that; latent's bound is {gib(LIMIT)}. Rank fewer "
            "passages: --changed-from, --only, or an index of less"
        )
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


#: What a kept space is called inside its file. A space kept under another
#: name was laid out another way, and is built again.
FORMAT = "latent-space-1"


def key_of(ix: "scan.Index", idxs: list[int]) -> str:
    """What a space was built from, as one hash: these passages in this
    order (a passage's id is the hash of its words), read into words by this
    kernel.py, and kept to this many dimensions. The same key, the same space."""
    h = hashlib.sha256(f"{FORMAT} {COMPONENTS}\n".encode())
    h.update(hashlib.sha256(Path(kernel.__file__).read_bytes()).digest())
    for i in idxs:
        h.update(ix.pile[i]["id"].encode())
    return h.hexdigest()


def load(to: Path, key: str):
    """The space kept in `to`, when it was built from `key`; None when it was
    built from something else. A file that isn't a kept space is a ValueError:
    it is someone's file, and is never written over."""
    import numpy as np

    try:
        with np.load(to, allow_pickle=False) as z:
            if str(z["format"]) != FORMAT:
                return None
            if str(z["key"]) != key:
                return None
            terms = z["terms"].tolist()
            return (z["idxs"].tolist(), {w: j for j, w in enumerate(terms)},
                    z["idf"], z["vt"], z["docz"])  # fmt: skip
    except Exception as e:  # numpy raises several kinds for a file that isn't its own
        raise ValueError(f"{to} is there and is not a space latent kept") from e


def save(to: Path, key: str, sp: tuple) -> None:
    """Keep the space in `to`, whole or not at all: written beside it first."""
    import numpy as np

    idxs, col, idf, vt, docz = sp
    fd, tmp = tempfile.mkstemp(dir=to.parent, prefix=".latent-")
    try:
        with os.fdopen(fd, "wb") as f:
            np.savez(f, format=np.array(FORMAT), key=np.array(key),
                     idxs=np.array(idxs, dtype=np.int64),
                     terms=np.array(sorted(col, key=col.get)),
                     idf=idf, vt=vt, docz=docz)  # fmt: skip
        os.replace(tmp, to)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def kept(ix: "scan.Index", lacked: set | None, only: set | None, to: Path | None):
    """The space, and what was done about `to`: read from it ("kept"), built
    and written to it ("built"), or nothing (no `to`, or too few passages to
    have a space worth keeping)."""
    if to is None:
        return space(ix, lacked, only), ""
    if to.is_dir() or not to.parent.is_dir():
        raise ValueError(f"--to {to}: a file, in a folder that is there")
    key = key_of(ix, chosen(ix, lacked, only))
    sp = load(to, key) if to.exists() else None
    if sp is not None:
        return sp, "kept"
    sp = space(ix, lacked, only)
    if sp[3] is None:
        return sp, ""
    save(to, key, sp)
    return sp, "built"


def rank(
    ix: "scan.Index",
    question: str,
    top: int,
    lacked: set | None = None,
    only: set | None = None,
) -> list[dict]:
    """The index's passages most like `question` by meaning, best first."""
    return ranked(ix, space(ix, lacked, only), question, top)


def ranked(ix: "scan.Index", sp: tuple, question: str, top: int) -> list[dict]:
    """`rank` in a space `space` already built, so many questions share it."""
    import numpy as np

    idxs, col, idf, vt, docz = sp
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
        if a in ("--index", "--changed-from", "--top", "--questions", "--only", "--to"):
            opts[a] = next(it, "")
            if not opts[a]:
                return usage()
        elif a.startswith("--"):
            return usage()
        else:
            args.append(a)
    top = opts.get("--top", "3")
    if "--index" not in opts or len(args) != ("--questions" not in opts):
        return usage()
    if not top.isdigit() or int(top) < 1:
        return usage()
    try:
        import numpy  # noqa: F401
    except ImportError:
        print("refused: latent needs numpy (pip install numpy)", file=sys.stderr)
        return kernel.REFUSED
    try:
        ix = scan.Index(Path(opts["--index"]))
        lacked = only = None
        if "--changed-from" in opts:
            lacked = {c["id"] for c in scan.passages(Path(opts["--changed-from"]))}
        if "--only" in opts:
            rows, ids = ids_in(Path(opts["--only"]).read_text(encoding="utf-8"))
            if not rows:
                raise ValueError(f"{opts['--only']} names no passage: no line of it is "
                                 "scan's, latent's, ripgrep's or code-shape's, or an id")  # fmt: skip
            only, missed = resolve(ix, ids)
            if missed and not only:
                raise ValueError(f"none of the {missed} ids in {opts['--only']} is a "
                                 f"passage of {opts['--index']}; was it made from another folder?")  # fmt: skip
            if missed:
                print(f"latent: {missed} of the {len(ids)} ids in {opts['--only']} "
                      f"are no passage of {opts['--index']}; ranked the rest", file=sys.stderr)  # fmt: skip
        if "--questions" in opts:
            qs = scan.questions(Path(opts["--questions"]).read_text(encoding="utf-8"))
        else:
            qs = [("", args[0])]
        to = Path(opts["--to"]) if "--to" in opts else None
        sp, did = kept(ix, lacked, only, to)
        if did == "kept":
            print(f"latent: the space kept in {to} is of these {len(sp[0])} passages; "
                  "not built again", file=sys.stderr)  # fmt: skip
        elif did == "built":
            print(f"latent: built the space of {len(sp[0])} passages and kept it in {to}",
                  file=sys.stderr)  # fmt: skip
    except (OSError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    held = False
    for name, q in qs:
        served = ranked(ix, sp, q, int(top))
        held = held or bool(served)
        row = {"question": name} if "--questions" in opts else {}
        row.update(state="populated" if served else "empty", served=served)
        print(json.dumps(row, ensure_ascii=False))
    return kernel.ALIVE if held else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
