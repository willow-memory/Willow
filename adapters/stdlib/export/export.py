"""export.py: your approved answers, and your question log, as Markdown or CSV.

    python adapters/stdlib/export/export.py --box DIR [--format md|csv] [--log]

The approved answers, oldest approval first: what was approved, the reason
the suggestion gave, the passages it cited and where they were, and when.
Only approvals whose proof holds under your key are exported (the kernel's
`sealed`); a forged one never is.

With `--log`, instead, one line per day of questions: how many were asked,
how many were answered by your approval, how many from your files, how many
found nothing. Counts only: the record never held a question's words, so
neither can this.

It only reads, and writes to standard output. Exit codes, the kernel's: 0
done; 2 refused (a record that doesn't verify).
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def approved(box: Path, rows: list[dict]) -> list[dict]:
    places = {}
    for r in rows:
        for s in r.get("served", []):
            places.setdefault(s["id"], s["where"])
    out = []
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
        out.append({
            "approved": row["ts"],
            "answer": prop["data"],
            "reason": prop["claim"],
            "cites": [places.get(c, c[:12]) for c in prop["cites"]],
            "subject": subj,
        })  # fmt: skip
    return out


def log(rows: list[dict]) -> list[dict]:
    days: dict[str, dict] = {}
    for r in rows:
        if r["kind"] != "bite":
            continue
        d = days.setdefault(r["ts"][:10], {"day": r["ts"][:10], "asked": 0,
                                           "approved": 0, "files": 0, "nothing": 0})  # fmt: skip
        d["asked"] += 1
        if r.get("answered_by"):
            d["approved"] += 1
        elif any(not s.get("echo") for s in r.get("served", [])):
            d["files"] += 1
        else:
            d["nothing"] += 1
    return [days[k] for k in sorted(days)]


def as_md(items: list[dict], is_log: bool) -> str:
    if is_log:
        out = ["| Day | Asked | By your approval | From your files | Nothing |",
               "|---|---|---|---|---|"]  # fmt: skip
        out += [f"| {d['day']} | {d['asked']} | {d['approved']} | {d['files']} | {d['nothing']} |"
                for d in items]  # fmt: skip
        return "\n".join(out) + "\n"
    out = ["# Approved answers", ""]
    for a in items:
        out += [f"## {a['answer']}", "", f"- approved {a['approved']}",
                f"- reason: {a['reason']}", f"- cites: {', '.join(a['cites'])}",
                f"- {a['subject']}", ""]  # fmt: skip
    return "\n".join(out)


def as_csv(items: list[dict], is_log: bool) -> str:
    f = io.StringIO()
    keys = ["day", "asked", "approved", "files", "nothing"] if is_log else [
        "approved", "answer", "reason", "cites", "subject"]  # fmt: skip
    w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for item in items:
        w.writerow(
            {k: "; ".join(v) if isinstance(v, list) else v for k, v in item.items()}
        )
    return f.getvalue()


def main(argv: list[str]) -> int:
    opts, flags, it = {}, set(), iter(argv)
    for a in it:
        if a in ("--box", "--format"):
            opts[a] = next(it, "")
        else:
            flags.add(a)
    fmt = opts.get("--format", "md")
    if not opts.get("--box") or flags - {"--log"} or fmt not in ("md", "csv"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    is_log = "--log" in flags
    items = log(rows) if is_log else approved(box, rows)
    sys.stdout.write((as_md if fmt == "md" else as_csv)(items, is_log))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
