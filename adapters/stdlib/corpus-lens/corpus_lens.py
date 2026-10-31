"""corpus_lens.py: corpus-lens process reports as passages. Python 3.9+.

    python adapters/stdlib/corpus-lens/corpus_lens.py \\
        mirror --from FOLDER --to MIRROR

Walks FOLDER for corpus-lens reports (the markdown that starts
`# corpuslens report`, or the JSON `{schema_version, audit, results}`).
Each report becomes passages: where your intent arrives, who writes the
code, and the other headline findings. No session text is read; only the
report.

    wrote 1 files to MIRROR; skipped 0

A file that is not a report is skipped and counted. Hidden folders and
files are skipped. Exit codes, the kernel's: 0 wrote some; 42 nothing
readable; 2 refused.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: corpus_lens.py mirror --from FOLDER --to MIRROR"

HEAD = "# corpuslens report"


def _one_line(value) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def _audit_of(obj: dict) -> str:
    audit = obj.get("audit")
    if isinstance(audit, str) and audit.strip():
        return audit.strip()
    if isinstance(audit, dict):
        return _one_line(audit.get("sentence") or audit.get("text") or "")
    return ""


def _findings(obj: dict) -> list[str]:
    results = obj.get("results")
    if not isinstance(results, dict):
        return []
    lines = []
    for name in sorted(results):
        got = results[name]
        if isinstance(got, dict):
            said = got.get("sentence") or got.get("text")
            if said:
                lines.append(f"{name}: {_one_line(said)}")
                continue
            parts = []
            for key in sorted(got):
                if key == "reference":
                    continue
                val = got[key]
                if isinstance(val, (int, float, str)) and val != "":
                    parts.append(f"{key}={val}")
            if parts:
                lines.append(f"{name}: " + ", ".join(parts))
        elif got is not None and got != "":
            lines.append(f"{name}: {_one_line(got)}")
    return lines


def report_text(raw: bytes) -> str | None:
    """The mirror text for a corpus-lens report, or None if it isn't one."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if "\0" in text:
        return None
    stripped = text.lstrip("\ufeff").lstrip()
    if stripped.startswith(HEAD):
        body = stripped.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
        return body
    try:
        obj = json.loads(text)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    if not {"schema_version", "audit", "results"} <= set(obj):
        return None
    lines = [HEAD, ""]
    audit = _audit_of(obj)
    if audit:
        lines.append(audit)
        lines.append("")
    found = _findings(obj)
    if found:
        lines.append("## What this run found")
        lines.extend(f"- {row}" for row in found)
        lines.append("")
    return "\n".join(lines) + "\n"


def _sources(folder: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if name.startswith("."):
                continue
            if not name.endswith((".md", ".json")):
                continue
            p = Path(dirpath) / name
            if p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    wrote = skipped = 0
    for path in _sources(src):
        text = None
        try:
            text = report_text(path.read_bytes())
            if text is not None:
                rel = path.relative_to(src)
                target = dst.joinpath(rel.parent, rel.name + ".txt")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(text.encode("utf-8"))
        except OSError:
            text = None
        if text is None:
            skipped += 1
        else:
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


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
