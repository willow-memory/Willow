"""oakenscroll.py: Oakenscroll's Office calibration ledger, as dated passages.

    python adapters/stdlib/oakenscroll/oakenscroll.py mirror --from FOLDER --to MIRROR

Oakenscroll's Office keeps what a person believed, how hard, and how it
resolved in one SQLite file, office.db: a `predictions` table (one row per
claim as first stated) and an append-only `events` table (revised, resolved,
voided, reopened). Walks FOLDER for files named office.db (in any
capitalisation), skipping hidden folders and files, and opens each read-only.

Each claim becomes one paragraph, oldest statement first, opening with the
date it was stated, then every event in the order it was appended, then the
state the events fold to (the same fold the office itself uses: the latest
revision stands, a resolution or void closes it, a reopening opens it again):

    2026-10-01: the PR merges this week (a1b2c3d4)
    said 70% on 2026-10-01; due 2026-10-08; tags: work, review
    2026-10-03: revised to 80%
    2026-10-09: graded true; note: merged Thursday; evidence: kind=almanac-data
    now: resolved true, at 80%

The first line names the ledger and counts its claims by state. This does not
score anything: Brier and log scores belong to `forecasts` (the office's own
log score is the same one-script calibration), and a claim's confidence is
shown as stated, never judged. Absence is written down: a claim with no due
date says "open-ended", one with no tags says "no tags".

Each ledger is written to MIRROR at the same relative path with `.txt` added:
`home/office.db` becomes `MIRROR/home/office.db.txt`. FOLDER is only read (the
database is opened immutable, so not even a lock file appears). A file that is
not a ledger (not SQLite, or no predictions and events tables) is skipped and
counted, never a crash.

    wrote 1 files to MIRROR; skipped 0

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: oakenscroll.py mirror --from FOLDER --to MIRROR"


def _one_line(value) -> str:
    """A field as one line: lists joined, whitespace collapsed, None as ''."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_one_line(v) for v in value if v is not None)
    return " ".join(str(value).split())


def _day(stamp) -> str:
    """A unix time as its UTC date, or 'an unknown date'."""
    try:
        return datetime.fromtimestamp(int(stamp), timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OverflowError, OSError):
        return "an unknown date"


def _pct(confidence) -> str:
    """0.7 as '70%'; a missing or odd value as 'no confidence recorded'."""
    try:
        return f"{round(float(confidence) * 100, 4):g}%"
    except (TypeError, ValueError, OverflowError):
        return "no confidence recorded"


def _evidence(raw) -> str:
    """A citation record as key=value pairs in key order; odd JSON as one line."""
    if raw is None:
        return ""
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return _one_line(raw)
    if isinstance(data, dict):
        return ", ".join(f"{_one_line(k)}={_one_line(data[k])}" for k in sorted(data))
    return _one_line(data)


def _outcome(value) -> str:
    return {1: "true", 0: "false"}.get(value, "with no outcome recorded")


def _tags(raw) -> str:
    try:
        tags = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        return _one_line(raw)
    return _one_line(tags) if isinstance(tags, list) else _one_line(raw)


def _fold(stated, events: list[dict]) -> tuple[str, str]:
    """(state, said): the events folded in order, as the office itself does."""
    state, confidence = "open", stated
    outcome = None
    for e in events:
        kind = e["kind"]
        if kind == "revised":
            confidence = e["confidence"]
        elif kind == "resolved":
            state, outcome = "resolved", e["outcome"]
        elif kind == "voided":
            state, outcome = "voided", None
        elif kind == "reopened":
            state, outcome = "open", None
    if state == "resolved":
        state = f"resolved {_outcome(outcome)}"
    return state, _pct(confidence)


def _event_line(e: dict) -> str:
    kind = _one_line(e["kind"]) or "unnamed event"
    when = f"{_day(e['at'])}: "
    if kind == "revised":
        text = f"revised to {_pct(e['confidence'])}"
    elif kind == "resolved":
        text = f"graded {_outcome(e['outcome'])}"
    elif kind == "voided":
        text = "voided"
    elif kind == "reopened":
        text = "reopened"
    else:
        text = kind
    if _one_line(e["note"]):
        text += f"; note: {_one_line(e['note'])}"
    if _evidence(e["evidence"]):
        text += f"; evidence: {_evidence(e['evidence'])}"
    return when + text


def claim_text(pred: dict, events: list[dict]) -> str:
    """One claim as one paragraph: statement, every event, then where it stands."""
    claim = _one_line(pred["claim"]) or "(no claim text)"
    due = "open-ended" if pred["due"] is None else _day(pred["due"])
    tags = _tags(pred["tags"]) or "no tags"
    lines = [
        f"{_day(pred['stated_at'])}: {claim} ({_one_line(pred['id'])})",
        f"said {_pct(pred['confidence'])} on {_day(pred['stated_at'])}; "
        f"due {due}; tags: {tags}",
    ]
    lines += [_event_line(e) for e in events]
    state, said = _fold(pred["confidence"], events)
    lines.append(f"now: {state}, at {said}")
    return "\n".join(lines) + "\n\n"


def _rows(con: sqlite3.Connection, table: str, want: tuple[str, ...]) -> list[dict]:
    """Every row of `table`, with the wanted columns (one a v0.1 ledger lacks
    reads None). A table with no id column is not the office's."""
    have = [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]
    if "id" not in have:
        raise sqlite3.DatabaseError(f"no {table} table")
    cols = [c for c in want if c in have]
    rows = con.execute(f"SELECT {', '.join(cols)} FROM {table}").fetchall()
    return [{c: r[cols.index(c)] if c in cols else None for c in want} for r in rows]


def ledger_text(path: Path) -> str | None:
    """The mirror text for an office.db, or None if it is not a ledger."""
    try:
        con = sqlite3.connect(
            f"{path.resolve().as_uri()}?mode=ro&immutable=1", uri=True
        )
    except (sqlite3.Error, ValueError):
        return None
    try:
        preds = _rows(
            con,
            "predictions",
            ("id", "claim", "confidence", "stated_at", "due", "tags"),
        )
        events = _rows(
            con,
            "events",
            ("id", "prediction_id", "kind", "confidence", "outcome", "note",
             "evidence", "at"),
        )  # fmt: skip
    except (sqlite3.Error, ValueError):
        return None
    finally:
        con.close()
    # the events table is appended in id order; that order is the history
    events.sort(key=lambda e: e["id"])
    by_claim: dict[str, list[dict]] = {}
    for e in events:
        by_claim.setdefault(e["prediction_id"], []).append(e)
    preds.sort(
        key=lambda p: (p["stated_at"] is None, p["stated_at"] or 0, str(p["id"]))
    )
    counts: dict[str, int] = {}
    body = []
    for p in preds:
        mine = by_claim.get(p["id"], [])
        body.append(claim_text(p, mine))
        state = _fold(p["confidence"], mine)[0].split()[0]
        counts[state] = counts.get(state, 0) + 1
    n = len(preds)
    said = ", ".join(
        f"{counts[s]} {s}" for s in ("open", "resolved", "voided") if s in counts
    )
    head = f"oakenscroll: {n} claim{'' if n == 1 else 's'}" + (
        f" ({said})" if said else ""
    )
    return head + "\n\n" + "".join(body)


def _sources(folder: Path) -> list[Path]:
    """office.db files under `folder`, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower() == "office.db" and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = ledger_text(path)
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except OSError:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
