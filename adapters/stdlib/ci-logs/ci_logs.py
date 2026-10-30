r"""ci_logs.py: CI run logs you downloaded: each failing step as a passage. Python 3.9+.

    python adapters/stdlib/ci-logs/ci_logs.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .log and .txt files that are a CI run log (hidden folders and
files skipped; any other file skipped and counted) and writes each step that
failed as a short passage: the step's name, the time of its error, the last
lines it printed and the error itself:

    failed step: Run pytest (2026-10-29 03:28)
      FAILED tests/test_garden.py::test_sun - assert 5 == 6
      ===== 1 failed, 40 passed in 2.31s =====
      ##[error]Process completed with exit code 1.

Three logs are read, told apart by their lines: GitHub Actions and Forgejo
Actions (a timestamp on every line, `##[group]` steps, `##[error]` lines), the
same as `gh run view --log-failed` prints it (a job name, a step name and a
timestamp, separated by tabs), and GitLab CI (`section_start:` markers and
`ERROR:` lines). A step keeps its last 15 lines before the error. A log with no
failing step is skipped and counted: a run that passed has nothing to find.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KEEP = 15  # lines of a failing step shown before its error
STAMP = re.compile(
    r"^((?:[^\t\n]*\t){0,2})(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})[\d:.]*Z ?(.*)$"
)
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
SECTION = re.compile(r"section_(start|end):\d+:([\w.\-]+)")


def github(lines: list[str]) -> list[str]:
    out: list[str] = []
    step, body = "(job)", []
    for raw in lines:
        m = STAMP.match(raw)
        if not m:
            continue
        prefix, day, hm, text = m.groups()
        fields = prefix.split("\t")
        if len(fields) >= 3 and fields[1].strip():
            step = fields[
                1
            ].strip()  # gh run view --log-failed names the step on every line
        text = ANSI.sub("", text).rstrip()
        if text.startswith("##[group]"):
            step, body = text[len("##[group]") :].strip() or step, []
        elif text.startswith("##[endgroup]"):
            body = []
        elif text.startswith("##[error]"):
            tail = body[-KEEP:] + [text]
            out.append(
                f"failed step: {step} ({day} {hm})\n"
                + "\n".join("  " + t for t in tail)
            )
            body = []
        else:
            body.append(text)
    return out


def gitlab(lines: list[str]) -> list[str]:
    out, name, body = [], "(job)", []
    for raw in lines:
        text = ANSI.sub("", raw.replace("\r", "\n")).rstrip()
        for part in text.split("\n"):
            m = SECTION.search(part)
            if m:
                if m.group(1) == "start":
                    name, body = m.group(2), []
                continue
            clean = part.strip()
            if clean.startswith("ERROR:") and "Job failed" in clean:
                out.append(
                    f"failed step: {name}\n"
                    + "\n".join("  " + t for t in (body[-KEEP:] + [clean]))
                )
                body = []
            elif clean:
                body.append(clean)
    return out


def convert(data: bytes) -> str | None:
    text = data.decode("utf-8-sig", errors="replace").replace("\r\n", "\n")
    lines = text.split("\n")
    if sum(1 for ln in lines[:200] if STAMP.match(ln)) >= 2:
        found = github(lines)
    elif "section_start:" in text or "Running with gitlab-runner" in text:
        found = gitlab(lines)
    else:
        return None
    return "\n\n".join(found) + "\n" if found else None


EXTS = (".log", ".txt")
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: ci_logs.py mirror --from FOLDER --to MIRROR"


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
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
