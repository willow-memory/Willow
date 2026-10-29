r"""sarif.py: SARIF reports from code scanners: each finding as a passage. Python 3.9+.

    python adapters/stdlib/sarif/sarif.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .sarif and .sarif.json files (hidden folders and files skipped;
a file that is not a SARIF report is skipped and counted) and writes each
finding as a short passage, by file and line:

    CodeQL: py/sql-injection (error) at src/db.py:42
    SQL injection: This query depends on a user-provided value.

The first line is the scanner (the tool's name), the rule, its level (warning
when the report gives none) and where it was found. The second is the rule's
short description, when the report has one, and the finding's message. Findings
come in order of file, line and rule. A finding with no location is written
without "at". Fixes, code flows, fingerprints and the rules' long help are not
copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

def text(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def message(m: object) -> str:
    return text(m.get("text") or m.get("markdown")) if isinstance(m, dict) else ""


def place(result: dict) -> tuple[str, int]:
    """(file, line) of a finding's first location, ("", 0) when it has none."""
    for loc in result.get("locations") if isinstance(result.get("locations"), list) else []:
        phys = loc.get("physicalLocation") if isinstance(loc, dict) else None
        if not isinstance(phys, dict):
            continue
        art = phys.get("artifactLocation")
        uri = text(art.get("uri")) if isinstance(art, dict) else ""
        region = phys.get("region")
        line = region.get("startLine") if isinstance(region, dict) else 0
        return uri, line if isinstance(line, int) and not isinstance(line, bool) and line > 0 else 0
    return "", 0


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not (isinstance(doc, dict) and isinstance(doc.get("runs"), list) and isinstance(doc.get("version"), str)):
        return None
    rows = []
    for run in doc["runs"]:
        if not isinstance(run, dict):
            continue
        driver = (run.get("tool") or {}).get("driver") if isinstance(run.get("tool"), dict) else None
        driver = driver if isinstance(driver, dict) else {}
        tool = text(driver.get("name")) or "scanner"
        shorts = {}
        for rule in driver.get("rules") if isinstance(driver.get("rules"), list) else []:
            if isinstance(rule, dict) and text(rule.get("id")):
                short = rule.get("shortDescription")
                shorts[text(rule["id"])] = message(short)
        for result in run.get("results") if isinstance(run.get("results"), list) else []:
            if not isinstance(result, dict):
                continue
            rule = text(result.get("ruleId")) or "(no rule)"
            level = text(result.get("level")) or "warning"
            uri, line = place(result)
            where = f" at {uri}" + (f":{line}" if line else "") if uri else ""
            first = f"{tool}: {rule} ({level}){where}"
            short, msg = shorts.get(rule, ""), message(result.get("message"))
            second = ": ".join(x for x in (short, msg) if x)
            rows.append(((uri, line, rule), first + ("\n" + second if second else "")))
    return "\n\n".join(t for _k, t in sorted(rows, key=lambda r: r[0])) + "\n" if rows else None

EXTS = ('.sarif', '.sarif.json')
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: sarif.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
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
            text = convert(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
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
        print("refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr)
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
