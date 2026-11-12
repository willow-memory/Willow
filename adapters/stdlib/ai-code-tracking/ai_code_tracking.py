"""ai_code_tracking.py: which code Cursor's AI wrote, from its tracking database.

    python adapters/stdlib/ai-code-tracking/ai_code_tracking.py mirror --from FILE_OR_FOLDER --to MIRROR
    python adapters/stdlib/ai-code-tracking/ai_code_tracking.py report --from DB [--json]

Cursor keeps `~/.cursor/ai-tracking/ai-code-tracking.db`: a hash of each chunk
its AI wrote (where, by which model, in which conversation, when) and, for
each commit it scored, how many lines tab completion, the composer (agent)
and the person added and deleted.

mirror: each such database found is written to MIRROR at the same relative
path with `.txt` added: one paragraph per scored commit (hash, branch, date,
message, lines by tab, composer and human, AI percentage) and one per
conversation (id, models, first and last time, how many chunks, by file
extension). The hashes themselves and the file contents Cursor keeps in
`tracked_file_content` are never written. A file that is not such a database
is skipped and counted. A mirror past the kernel's read limit goes on in
`.2.txt`, `.3.txt`.

report: the report contract's shape (ci/README.md): `ai-code-tracking: STATE,
SAID`, then totals, chunks by model and lines by month. `empty` is 0, a file
that is not the database `unreachable` and 42.

The original is opened read-only (SQLite's `mode=ro`) and never written.
Exit codes, the kernel's: 0 wrote some or reported; 42 nothing readable;
2 refused.
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

NAME = "ai-code-tracking"
USAGE = (
    "usage: ai_code_tracking.py mirror --from FILE_OR_FOLDER --to MIRROR\n"
    "       ai_code_tracking.py report --from DB [--json]"
)
COMMIT_COLS = (
    "commitHash",
    "branchName",
    "scoredAt",
    "linesAdded",
    "linesDeleted",
    "tabLinesAdded",
    "tabLinesDeleted",
    "composerLinesAdded",
    "composerLinesDeleted",
    "humanLinesAdded",
    "humanLinesDeleted",
    "commitMessage",
    "commitDate",
    "v1AiPercentage",
    "v2AiPercentage",
)
HASH_COLS = ("fileExtension", "conversationId", "timestamp", "model")
PART = 900_000  # bytes a mirror file holds before it goes on; the kernel reads 1 MB
IN_CONV = "conversationId IS NOT NULL AND conversationId != ''"


def _one_line(value) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _when(ms) -> str:
    """A millisecond (or second) epoch as `YYYY-MM-DD HH:MM` in UTC."""
    n = _int(ms)
    if not n:
        return ""
    n = n / 1000 if n > 10**11 else n
    try:
        return datetime.fromtimestamp(n, timezone.utc).strftime("%Y-%m-%d %H:%M")
    except (OverflowError, OSError, ValueError):
        return ""


def load(path: Path) -> dict | None:
    """The commits and the per-conversation and per-model sums of one
    database, or None when it is not Cursor's tracking database."""
    try:
        con = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        tables = {
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

        def has(table: str, need: tuple) -> bool:
            if table not in tables:
                return False
            cols = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
            return set(need) <= cols

        commits_ok = has("scored_commits", COMMIT_COLS)
        hashes_ok = has("ai_code_hashes", HASH_COLS)
        if not (commits_ok or hashes_ok):
            return None
        data = {"commits": [], "convs": [], "models": [], "exts": [], "by_model": []}
        if commits_ok:
            data["commits"] = con.execute(
                "SELECT " + ", ".join(COMMIT_COLS) + " FROM scored_commits "
                "ORDER BY commitDate, commitHash"
            ).fetchall()
        if hashes_ok:
            data["convs"] = con.execute(
                "SELECT conversationId, COUNT(*), MIN(timestamp), MAX(timestamp) "
                f"FROM ai_code_hashes WHERE {IN_CONV} GROUP BY conversationId "
                "ORDER BY MIN(timestamp), conversationId"
            ).fetchall()
            data["models"] = con.execute(
                "SELECT conversationId, model, COUNT(*) FROM ai_code_hashes "
                f"WHERE {IN_CONV} GROUP BY conversationId, model "
                "ORDER BY conversationId, model"
            ).fetchall()
            data["exts"] = con.execute(
                "SELECT conversationId, fileExtension, COUNT(*) FROM ai_code_hashes "
                f"WHERE {IN_CONV} GROUP BY conversationId, fileExtension "
                "ORDER BY conversationId, COUNT(*) DESC, fileExtension"
            ).fetchall()
            data["by_model"] = con.execute(
                "SELECT model, COUNT(*), COUNT(DISTINCT conversationId) "
                "FROM ai_code_hashes GROUP BY model ORDER BY COUNT(*) DESC, model"
            ).fetchall()
    except sqlite3.Error:
        return None
    finally:
        con.close()
    return data


def commit_text(row) -> str:
    h, branch, scored, add, dele = row[:5]
    tab_a, tab_d, comp_a, comp_d, hum_a, hum_d = row[5:11]
    message, date, v1, v2 = row[11:15]
    lines = [f"commit {_one_line(h)} on {_one_line(branch) or '(no branch)'}"]
    day = _one_line(date)[:10] or _when(scored)[:10]
    if day:
        lines.append(f"date: {day}")
    if _one_line(message):
        lines.append(f"message: {_one_line(message)[:300]}")
    lines.append(f"lines added {_int(add)}, deleted {_int(dele)}")
    lines.append(f"by tab: added {_int(tab_a)}, deleted {_int(tab_d)}")
    lines.append(f"by composer: added {_int(comp_a)}, deleted {_int(comp_d)}")
    lines.append(f"by human: added {_int(hum_a)}, deleted {_int(hum_d)}")
    lines.append(f"AI percentage: v1 {_one_line(v1) or '?'}, v2 {_one_line(v2) or '?'}")
    return "\n".join(lines) + "\n"


def conversation_texts(data: dict) -> list[str]:
    models: dict = {}
    for cid, model, _n in data["models"]:
        models.setdefault(cid, []).append(_one_line(model) or "(no model)")
    exts: dict = {}
    for cid, ext, n in data["exts"]:
        exts.setdefault(cid, []).append(f"{_one_line(ext) or '(none)'} {n}")
    out = []
    for cid, n, first, last in data["convs"]:
        lines = [f"conversation {_one_line(cid)}: the AI wrote {n} chunks"]
        lines.append(f"models: {', '.join(models.get(cid, []))}")
        lines.append(f"first: {_when(first)}")
        lines.append(f"last: {_when(last)}")
        lines.append(f"by file extension: {', '.join(exts.get(cid, []))}")
        out.append("\n".join(lines) + "\n")
    return out


def database_texts(path: Path) -> list[str] | None:
    """The passages of one database, or None when it is not one or holds
    nothing to write."""
    data = load(path)
    if data is None:
        return None
    paras = [commit_text(r) for r in data["commits"]] + conversation_texts(data)
    if not paras:
        return None
    head = (
        f"ai-code-tracking: {len(data['commits'])} scored commits, "
        f"{len(data['convs'])} conversations\n"
    )
    return [head] + paras


def _split(paras: list[str]) -> list[str]:
    """Paragraphs joined into files of under PART bytes each."""
    files, cur, size = [], [], 0
    for p in paras:
        n = len(p.encode("utf-8")) + 1
        if cur and size + n > PART:
            files.append("\n".join(cur))
            cur, size = [], 0
        cur.append(p)
        size += n
    files.append("\n".join(cur))
    return files


def _sources(src: Path) -> list[Path]:
    if src.is_file():
        return [src]
    found = []
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name.startswith(".") or not name.endswith(".db"):
                continue
            p = Path(dirpath) / name
            if p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(src).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


# differs on purpose: database_texts skips what isn't a tracking database, so only OSError is left to catch
def mirror(src: Path, dst: Path) -> tuple[int, int]:
    wrote = skipped = 0
    for path in _sources(src):
        try:
            paras = database_texts(path)
            if paras is None:
                skipped += 1
                continue
            rel = Path(path.name) if src.is_file() else path.relative_to(src)
            for i, text in enumerate(_split(paras), 1):
                suffix = ".txt" if i == 1 else f".{i}.txt"
                target = dst.joinpath(rel.parent, rel.name + suffix)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(text.encode("utf-8"))
        except OSError:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def build_report(path: Path) -> dict:
    data = load(path)
    if data is None:
        return report(NAME, "unreachable", "not Cursor's ai-code-tracking database", [])
    commits = data["commits"]
    if not commits and not data["by_model"]:
        return report(NAME, "empty", "no commits scored and no AI-written code", [])
    sums = [0, 0, 0, 0]  # lines added: all, tab, composer, human
    months: dict = {}
    for r in commits:
        row = [_int(r[3]), _int(r[5]), _int(r[7]), _int(r[9])]
        sums = [a + b for a, b in zip(sums, row)]
        month = (_one_line(r[12]) or _when(r[2]))[:7] or "(no date)"
        m = months.setdefault(month, [0, 0, 0, 0, 0])
        m[0] += 1
        for i, v in enumerate(row):
            m[i + 1] += v
    totals = [
        ("commits scored", str(len(commits))),
        ("lines added", str(sums[0])),
        ("lines added by tab", str(sums[1])),
        ("lines added by composer", str(sums[2])),
        ("lines added by human", str(sums[3])),
        ("AI-written chunks", str(sum(n for _, n, _ in data["by_model"]))),
        ("conversations", str(len(data["convs"]))),
    ]
    by_model = [
        (_one_line(m) or "(no model)", f"{n} chunks in {c} conversations")
        for m, n, c in data["by_model"]
    ]
    by_month = [
        (
            k,
            f"{v[0]} commits; added: tab {v[2]}, composer {v[3]}, human {v[4]}, all {v[1]}",
        )
        for k, v in sorted(months.items())
    ]
    said = (
        f"{len(commits)} commits scored; lines added by tab {sums[1]}, "
        f"composer {sums[2]}, human {sums[3]}"
    )
    return report(
        NAME, "populated", said,
        [("totals", totals), ("by model", by_model), ("by month", by_month)],
    )  # fmt: skip


def main(argv: list[str]) -> int:
    args = list(argv)
    as_json = False
    if args[:1] in (["report"], ["mirror"]) and args[-1:] == ["--json"]:
        as_json, args = True, args[:-1]
    verb = args[:1]
    opts = dict(zip(args[1::2], args[2::2])) if verb in (["mirror"], ["report"]) else {}
    want = ["--from", "--to"] if verb == ["mirror"] else ["--from"]
    if len(args) != 1 + 2 * len(want) or sorted(opts) != want:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"])
    if verb == ["report"]:
        if not src.is_file():
            print(f"refused: not a file: {opts['--from']}", file=sys.stderr)
            return kernel.REFUSED
        doc = build_report(src)
        say(doc, as_json)
        return kernel.ESCALATE if doc["state"] == "unreachable" else kernel.ALIVE
    if not (src.is_file() or src.is_dir()):
        print(f"refused: not a file or folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = src.resolve(), Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FROM must not be inside one another",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    said = f"wrote {wrote} files to {opts['--to']}; skipped {skipped}"
    if as_json:  # a stack asks every step of an output: report card for --json
        say(report(NAME, "populated" if wrote else "empty", said, []), True)
    else:
        print(said)
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
