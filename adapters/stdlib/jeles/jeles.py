"""jeles.py: Jeles' nuggets as passages, and your approved answers as nuggets.

    python adapters/stdlib/jeles/jeles.py mirror --from FOLDER --to MIRROR
    python adapters/stdlib/jeles/jeles.py export --box DIR --questions FILE --to OUT.json

Jeles (github.com/hornbook-knowledge/jeles) keeps verified question-and-answer
pairs, nuggets, each with its sources and who verified it.

**mirror** reads them as passages. It walks FOLDER, skipping hidden folders and
files, for Jeles' two shapes: a seed file (`*.json`, a `pairs` list of
`source_text` and `target_text`, or a list of them) and a corpus store
(`*.db`, the SQLite `records` table whose rows hold a question and an answer).
Each nugget becomes one paragraph:

    What is a black hole?
    A region of spacetime where gravity is so strong nothing escapes.
    sources: https://science.nasa.gov/universe/black-holes/
    verified: human, by ada, 2026-10-01

A seed pair with no signature says so: `verified: unsigned seed pair (Jeles sets
its rung when it installs the seed)`. Jeles installs most such pairs at its
`asserted` rung, but cited commons pairs at `human`, so the rung is Jeles' to say. A signature is never copied; a deleted record
and a logged gap (a question with no answer) are left out. Each file is written
to MIRROR at the same relative path with .txt added; FOLDER is only read.

**export** writes your approved answers as a Jeles seed file. willow's record
never holds a question's words, only their hash, so you give the questions,
one per line, in FILE. A question is paired with an approval only when its
words hash to the key the approval was sealed under; nothing is matched by
guessing. Each pair carries the answer, the reason the suggestion gave, the
passages it cited, and when it was sealed. Jeles installs it at its `asserted`
rung: a willow seal is your key's proof, not a Nestor seal, and Jeles can't
check it. Only approvals whose proof holds under your key are exported (the
kernel's `sealed`).

Exit codes, the kernel's: mirror 0 wrote some, 42 nothing readable; export 0
wrote some, 42 no question matched an approval; 2 refused.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

USAGE = (
    "usage: jeles.py mirror --from FOLDER --to MIRROR\n"
    "       jeles.py export --box DIR --questions FILE --to OUT.json"
)
UNSIGNED = "unsigned seed pair (Jeles sets its rung when it installs the seed)"


def _one_line(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_one_line(v) for v in value if _one_line(v))
    return " ".join(str(value).split())


def nugget_text(question, answer, reason=None, sources=None, verified=None) -> str:
    lines = [_one_line(question), _one_line(answer)]
    if _one_line(reason):
        lines.append(f"reason: {_one_line(reason)}")
    if _one_line(sources):
        lines.append(f"sources: {_one_line(sources)}")
    lines.append(f"verified: {verified or UNSIGNED}")
    return "\n".join(lines) + "\n\n"


def _verified(kind, who, when) -> str:
    parts = [_one_line(kind) or "unknown"]
    if _one_line(who):
        parts.append(f"by {_one_line(who)}")
    if _one_line(when):
        parts.append(_one_line(when)[:10])
    return ", ".join(parts)


def seed_text(raw: bytes) -> str | None:
    """A Jeles seed file as passages, or None if it isn't one."""
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        return None
    pairs = data.get("pairs") if isinstance(data, dict) else data
    if not isinstance(pairs, list):
        return None
    pairs = [
        p
        for p in pairs
        if isinstance(p, dict) and p.get("source_text") and p.get("target_text")
    ]
    if not pairs:
        return None
    located: dict[str, list[str]] = {}
    for ev in data.get("evidence", []) if isinstance(data, dict) else []:
        if isinstance(ev, dict) and ev.get("locator"):
            located.setdefault(_one_line(ev.get("pair_source")), []).append(
                ev["locator"]
            )
    out = []
    for p in pairs:
        sources = located.get(_one_line(p["source_text"]), []) + list(
            p.get("evidence_urls") or []
        )
        who = p.get("verified_by") or (
            data.get("verified_by") if isinstance(data, dict) else None
        )
        verified = _verified("signed", who, None) if p.get("seal_sig") else None
        out.append(
            nugget_text(
                p["source_text"], p["target_text"], p.get("reason"), sources, verified
            )
        )
    name = _one_line(data.get("domain")) if isinstance(data, dict) else ""
    n = len(out)
    head = (
        f"jeles seed{': ' + name if name else ''}, {n} pair{'s' if n != 1 else ''}\n\n"
    )
    return head + "".join(out)


def store_text(path: Path) -> str | None:
    """A Jeles corpus store's nuggets as passages, or None if it isn't one."""
    try:
        con = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        tables = {
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "records" not in tables:
            return None
        cols = {r[1] for r in con.execute("PRAGMA table_info(records)")}
        if not {"id", "data"} <= cols:
            return None
        where = " WHERE deleted = 0" if "deleted" in cols else ""
        rows = con.execute(
            f"SELECT id, data FROM records{where} ORDER BY id"
        ).fetchall()
    except sqlite3.Error:
        return None
    finally:
        con.close()
    out = []
    for _, data in rows:
        try:
            n = json.loads(data)
        except (TypeError, ValueError):
            continue
        if not isinstance(n, dict) or not n.get("question") or not n.get("answer"):
            continue  # a logged gap, or not a nugget
        verified = _verified(
            n.get("verification_kind"), n.get("verified_by"), n.get("verified_at")
        )
        out.append(
            nugget_text(n["question"], n["answer"], None, n.get("sources"), verified)
        )
    if not out:
        return None
    k = len(out)
    return f"jeles store, {k} nugget{'s' if k != 1 else ''}\n\n" + "".join(out)


def _sources(folder: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if (
                not name.startswith(".")
                and name.lower().endswith((".json", ".db"))
                and p.is_file()
            ):
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    wrote = skipped = 0
    for path in _sources(src):
        try:
            text = (
                store_text(path)
                if path.suffix.lower() == ".db"
                else seed_text(path.read_bytes())
            )
            if text is None:
                skipped += 1
                continue
            rel = path.relative_to(src)
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except OSError:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def approvals(box: Path) -> list[dict]:
    """Every sealed answer whose proof holds and whose proposal still holds the
    bytes sealed: the answer, its reason, where it cited, when, and the key of
    the question it was sealed under."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        raise ValueError("the record doesn't verify")
    places = {}
    for r in rows:
        for s in r.get("served", []):
            places.setdefault(s["id"], s["where"])
    out = []
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, key, why = kernel.standing(box, rows, subj, row)
        if why is None:
            out.append({"key": key, "answer": prop["data"], "reason": prop["claim"],
                        "cites": [places.get(c, c[:12]) for c in prop["cites"]],
                        "sealed": row["ts"], "subject": subj})  # fmt: skip
    return out


def export(box: Path, questions: list[str], out: Path) -> tuple[int, int, int]:
    """Write the seed file. Returns (pairs written, approvals with no question, questions unused)."""
    by_key = {}
    for q in questions:
        k = kernel.bite_key(q)
        if k and k not in by_key:
            by_key[k] = " ".join(q.split())
    pairs, evidence, used = [], [], set()
    found = approvals(box)
    for a in found:
        q = by_key.get(a["key"])
        if q is None:
            continue
        used.add(a["key"])
        pairs.append({"source_text": q, "target_text": a["answer"], "reason": a["reason"],
                      "verified_by": "willow seal (the box's key holder; not a Nestor seal)",
                      "willow": {"sealed": a["sealed"], "subject": a["subject"], "cites": a["cites"]}})  # fmt: skip
        evidence += [{"pair_source": q, "locator": c} for c in a["cites"]]
    if pairs:
        doc = {"domain": "willow-export", "pairs": pairs, "evidence": evidence}
        out.write_text(
            json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return len(pairs), len(found) - len(pairs), len(by_key) - len(used)


def main(argv: list[str]) -> int:
    verb, opts = (argv[0] if argv else ""), dict(zip(argv[1::2], argv[2::2]))
    if verb == "mirror" and len(argv) == 5 and sorted(opts) == ["--from", "--to"]:
        if not Path(opts["--from"]).is_dir():
            print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
            return kernel.REFUSED
        src, dst = Path(opts["--from"]).resolve(), Path(opts["--to"]).resolve()
        if _within(dst, src) or _within(src, dst):
            print(
                "refused: MIRROR and FOLDER must not be inside one another",
                file=sys.stderr,
            )
            return kernel.REFUSED
        wrote, skipped = mirror(src, dst)
        print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
        return kernel.ALIVE if wrote else kernel.ESCALATE
    if (
        verb == "export"
        and len(argv) == 7
        and sorted(opts) == ["--box", "--questions", "--to"]
    ):
        box, out = Path(opts["--box"]), Path(opts["--to"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        if out.exists() or not out.parent.is_dir():
            print(f"refused: {out} exists, or its folder doesn't", file=sys.stderr)
            return kernel.REFUSED
        try:
            questions = (
                Path(opts["--questions"]).read_text(encoding="utf-8").splitlines()
            )
        except (OSError, UnicodeDecodeError):
            print(
                f"refused: can't read {opts['--questions']} as UTF-8 text",
                file=sys.stderr,
            )
            return kernel.REFUSED
        try:
            wrote, unasked, unused = export(box, questions, out)
        except ValueError as e:
            print(f"refused: {e}", file=sys.stderr)
            return kernel.REFUSED
        print(f"wrote {wrote} pairs to {out}; {unasked} approvals had no question here; "
              f"{unused} questions matched no approval")  # fmt: skip
        return kernel.ALIVE if wrote else kernel.ESCALATE
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
