"""decisions.py: what you decided and what you ruled out, with the reasons,
so a new question finds the old answers. Python 3.9+.

    python adapters/stdlib/decisions/decisions.py chose  --box DIR --question Q --answer A --reason R [--replaces ROW] [--now TS]
    python adapters/stdlib/decisions/decisions.py no     --box DIR --question Q --option O --reason R (--never | --reopen-when CONDITION) [--now TS]
    python adapters/stdlib/decisions/decisions.py reopen --box DIR --row ROW --because R [--now TS]
    python adapters/stdlib/decisions/decisions.py ask    --box DIR QUESTION...

`chose` writes a `chose` row: a question, the answer, and the reason. With
`--replaces ROW` the row before is kept, and this one stands after it: the
lineage is the chain of rows, each with its own reason.

`no` writes a `no` row: an option ruled out, with its reason, and which kind
of no it is, said at the time. `--never` is a closed door. `--reopen-when`
is a not-yet, and carries the condition that would make it worth asking
again. One of the two is required; a no with neither is refused.

`reopen` writes a `reopen` row for a not-yet whose condition has come true,
with why. The no stays on the record beside it.

`ask` reads the rows back for a new question: the answer that stands and the
ones it replaced, every no with its reason, and each not-yet's condition for
you to check. A row is about the question when it holds half of the shorter
text's content words (the kernel's `HOLD`, counted against the shorter one).
Nothing here evaluates a condition; it shows you the words.

Every row stands unattested, and this says so: code records and looks up, and
only you approve, with `kernel.py seal`.

Exit codes, the kernel's: 0 written, or `ask` found something; 42 `ask`
found nothing on the record about the question; 2 refused: a record that
doesn't verify, a no with neither or both kinds, a missing reason, a row that
can't be replaced or reopened, a bad command line.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

WHO = "decisions"
CHOSE, NO, REOPEN = "chose", "no", "reopen"
NEVER, NOT_YET = "never", "not yet"
VALUE_OPTS = (
    "--box", "--now", "--question", "--answer", "--option", "--reason",
    "--reopen-when", "--replaces", "--row", "--because",
)  # fmt: skip


# ── reading the rows back ───────────────────────────────────────────────────
def text_of(v: object) -> bool:
    return isinstance(v, str) and bool(v.strip())


def number(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def decode(rows: list[dict]) -> dict:
    """Our rows, checked. `chose` and `no` by row number; `replaced_by` and
    `reopened_by` say what came after. A row of ours that can't be read, or
    that names a row it can't (one already replaced, one that is a never, one
    that comes later), is put in `skipped` with why, and not used."""
    chose: dict[int, dict] = {}
    no: dict[int, dict] = {}
    replaced_by: dict[int, int] = {}
    reopened_by: dict[int, dict] = {}
    skipped: list[tuple[int, str]] = []
    for r in rows:
        k, n = r["kind"], r["n"]
        if k == CHOSE:
            ok = all(text_of(r.get(f)) for f in ("question", "answer", "reason"))
            back = r.get("replaces")
            if not ok:
                skipped.append(
                    (n, "a chose row missing its question, answer or reason")
                )
            elif back is not None and back not in chose:
                skipped.append((n, "replaces a row that is not an earlier decision"))
            elif back is not None and back in replaced_by:
                skipped.append((n, f"replaces row {back}, already replaced"))
            else:
                chose[n] = r
                if back is not None:
                    replaced_by[back] = n
        elif k == NO:
            ok = all(text_of(r.get(f)) for f in ("question", "option", "reason"))
            door, when = r.get("door"), r.get("reopen_when")
            if not ok:
                skipped.append((n, "a no row missing its question, option or reason"))
            elif not (
                (door == NEVER and when is None) or (door == NOT_YET and text_of(when))
            ):
                skipped.append(
                    (n, "a no that is neither a never nor a not-yet with its condition")
                )
            else:
                no[n] = r
        elif k == REOPEN:
            of = r.get("of")
            if not text_of(r.get("because")):
                skipped.append((n, "a reopen row without its reason"))
            elif of not in no or no[of]["door"] != NOT_YET:
                skipped.append((n, "reopens a row that is not an earlier not-yet"))
            elif of in reopened_by:
                skipped.append((n, f"reopens row {of}, already reopened"))
            else:
                reopened_by[of] = r
    return {"chose": chose, "no": no, "replaced_by": replaced_by,
            "reopened_by": reopened_by, "skipped": skipped}  # fmt: skip


def content(text: str) -> list[str]:
    """A text's content words: the kernel's, without its function words."""
    return [w for w in kernel.words(text) if w not in kernel.FUNCTION]


def about(question: str, stored: str) -> list[str]:
    """The question's content words the stored text holds, when they are at
    least half of the shorter text's content words; else none. Counted
    against the shorter one, so a long line doesn't hide a short one it
    contains."""
    a, b = content(question), content(stored)
    if not a or not b:
        return []
    held = kernel.forms(b)
    shared = sorted({w for w in a if kernel.holds(w, held)})
    return shared if shared and 2 * len(shared) >= min(len(set(a)), len(set(b))) else []


def standing_of(d: dict, n: int) -> str:
    row = d["no"][n]
    if row["door"] == NEVER:
        return "closed"
    return "reopened" if n in d["reopened_by"] else "waiting"


def lineage(d: dict, head: int) -> list[int]:
    """The rows a decision replaced, nearest first."""
    out, n = [], d["chose"][head].get("replaces")
    while n is not None:
        out.append(n)
        n = d["chose"][n].get("replaces")
    return out


def lookup(d: dict, question: str) -> tuple[list[tuple], list[tuple]]:
    """(decisions, nos) about the question, in row order: each a row number
    and the words that matched. A decision is reported once, at the head of
    its chain, whichever row of the chain matched."""
    heads: dict[int, list[str]] = {}
    for n, r in d["chose"].items():
        hit = about(question, r["question"])
        if hit:
            h = n
            while h in d["replaced_by"]:
                h = d["replaced_by"][h]
            heads[h] = sorted(set(heads.get(h, [])) | set(hit))
    nos = [(n, about(question, r["question"])) for n, r in d["no"].items()]
    return sorted(heads.items()), [(n, w) for n, w in nos if w]


# ── the verbs ───────────────────────────────────────────────────────────────
def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def chose(box: Path, d: dict, o: dict, ts: str) -> int:
    back = o.get("--replaces")
    if back is not None:
        if back not in d["chose"]:
            return refuse(f"row {back} is not a decision on the record")
        if back in d["replaced_by"]:
            return refuse(
                f"row {back} was replaced already, by row {d['replaced_by'][back]}"
            )
    row = kernel.append(box, ts, CHOSE, who=WHO, question=o["--question"],
                        answer=o["--answer"], reason=o["--reason"], replaces=back)  # fmt: skip
    print(
        f"chose row {row['n']}: {o['--answer']}"
        + (f" (replaces row {back})" if back is not None else "")
    )
    print("it stands unattested; only your seal approves anything")
    return kernel.ALIVE


def rule_out(box: Path, o: dict, ts: str) -> int:
    never, when = "--never" in o, o.get("--reopen-when")
    if never == (when is not None):
        return refuse("say which no it is: --never, or --reopen-when and the condition")
    row = kernel.append(box, ts, NO, who=WHO, question=o["--question"],
                        option=o["--option"], reason=o["--reason"],
                        door=NEVER if never else NOT_YET, reopen_when=when)  # fmt: skip
    print(f"no row {row['n']}: {o['--option']} ({row['door']})")
    if when is not None:
        print(f"  ask again when: {when}")
    print("it stands unattested; only your seal approves anything")
    return kernel.ALIVE


def reopen(box: Path, d: dict, o: dict, ts: str) -> int:
    n = o["--row"]
    if n not in d["no"]:
        return refuse(f"row {n} is not a no on the record")
    if d["no"][n]["door"] == NEVER:
        return refuse(f"row {n} is a never, and names no condition to reopen on; "
                      "if you've changed your mind, write the decision with chose")  # fmt: skip
    if n in d["reopened_by"]:
        return refuse(
            f"row {n} was reopened already, by row {d['reopened_by'][n]['n']}"
        )
    row = kernel.append(box, ts, REOPEN, who=WHO, of=n, because=o["--because"])
    print(f"reopen row {row['n']}: no row {n} stays on the record, reopened")
    print("it stands unattested; only your seal approves anything")
    return kernel.ALIVE


def ask(d: dict, question: str) -> int:
    if not content(question):
        return refuse("a question of function words alone matches nothing; say more")
    for n, why in d["skipped"]:
        print(f"skipped row {n}: {why}", file=sys.stderr)
    heads, nos = lookup(d, question)
    if not heads and not nos:
        print(f"nothing on the record is about: {question}")
        print("that is not the same as free to decide: nothing was written down")
        return kernel.ESCALATE
    print(f"on the record about: {question}")
    print("every row stands unattested; none is approved by this")
    for head, hit in heads:
        r = d["chose"][head]
        print(f"chose, row {head} ({r['ts']}): {r['answer']}")
        print(f"  because: {r['reason']}")
        print(f"  asked as: {r['question']} (matched: {', '.join(hit)})")
        for n in lineage(d, head):
            old = d["chose"][n]
            print(f"  replaced row {n}: {old['answer']} (because: {old['reason']})")
    for n, hit in nos:
        r, state = d["no"][n], standing_of(d, n)
        print(f"no, {r['door']}, row {n} ({r['ts']}): {r['option']}")
        print(f"  because: {r['reason']}")
        print(f"  asked as: {r['question']} (matched: {', '.join(hit)})")
        if r["door"] == NOT_YET:
            if state == "reopened":
                back = d["reopened_by"][n]
                print(f"  reopened, row {back['n']}: {back['because']}")
            else:
                print(f"  reopen when: {r['reopen_when']}  (yours to check)")
    return kernel.ALIVE


def parse(argv: list[str]) -> tuple[str, dict, list[str]] | None:
    """(verb, options, words), or None for a bad command line. Numbers are
    read as digits only."""
    if not argv or argv[0] not in (CHOSE, NO, REOPEN, "ask"):
        return None
    verb, opts, words = argv[0], {}, []
    it = iter(argv[1:])
    for a in it:
        if a in VALUE_OPTS:
            v = next(it, None)
            if v is None or a in opts:
                return None
            opts[a] = v
        elif a == "--never":
            opts[a] = True
        elif a.startswith("--"):
            return None
        else:
            words.append(a)
    for a in ("--replaces", "--row"):
        if a in opts:
            if not (opts[a].isascii() and opts[a].isdigit()):
                return None
            opts[a] = int(opts[a])
    return verb, opts, words


NEED = {
    CHOSE: {"--question", "--answer", "--reason"},
    NO: {"--question", "--option", "--reason"},
    REOPEN: {"--row", "--because"},
    "ask": set(),
}
MAY = {
    CHOSE: {"--replaces"},
    NO: {"--never", "--reopen-when"},
    REOPEN: set(),
    "ask": set(),
}


def main(argv: list[str]) -> int:
    got = parse(argv)
    if got is None:
        return usage()
    verb, o, words = got
    given = set(o) - {"--box", "--now"}
    if "--box" not in o or not NEED[verb] <= given or given - NEED[verb] - MAY[verb]:
        return usage()
    if bool(words) != (verb == "ask") or (verb == "ask" and "--now" in o):
        return usage()
    for f in NEED[verb] | {"--reopen-when"}:
        if f in o and not text_of(o[f]) and not isinstance(o[f], int):
            return refuse(f"{f} can't be empty: a decision keeps its reason")
    box = Path(o["--box"])
    if not (box / "kernel.json").exists():
        return refuse("not a kernel box; init first")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse(f"the record doesn't verify ({breaks[0]}); a person looks first")
    d = decode(rows)
    ts = o.get("--now") or kernel.now()
    if verb == "ask":
        return ask(d, " ".join(words))
    if verb == CHOSE:
        return chose(box, d, o, ts)
    if verb == NO:
        return rule_out(box, o, ts)
    return reopen(box, d, o, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
