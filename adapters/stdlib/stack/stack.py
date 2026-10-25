"""stack.py: one document across a stack of boxes, not just one. Python 3.9+.

    python adapters/stdlib/stack/stack.py --stack LIST   DOC [-- ARG ...]
    python adapters/stdlib/stack/stack.py --box DIR [--box DIR ...] DOC [-- ARG ...]

DOC is one of the document-making add-ons: `digest`, `export`, `timeline` or
`readings`. stack runs that add-on over every box in the stack and composes
what each prints into one document, under a heading per box, every line still
cited by its own box, file and line. Anything after a lone `--` is passed to
the add-on unchanged (per box), so:

    stack --stack boxes.txt digest -- --days 7
    stack --box a --box b timeline -- "mould landlord"
    stack --box a --box b readings -- "when is the meeting"

A `--stack LIST` file names one box folder a line; blank lines and lines
beginning `#` are skipped, and a relative path is read from the list's own
folder. `--box DIR` names boxes directly instead, and repeats; give one way
or the other, not both.

It only reads and composes: it runs add-ons that each promise writes:nothing
and network:none, so the whole pass does too. It never writes a box, never
reads a key, and approves nothing -- the one-way arrow holds, a box to a
document. Exit codes, the kernel's: 0 nothing across the stack waits on you;
42 a box has something for you (or an add-on said so); 2 refused (a bad
command line, a listed folder that isn't a kernel box, or an unknown DOC).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

#: DOC -> (folder, script, the argv before a box's own, whether it writes to a
#: file given with --to rather than printing). The forwarded args and the box
#: are added by `run_doc`.
DOCS = {
    "digest": ("digest", "digest.py", ["--box"], False),
    "export": ("export", "export.py", ["--box"], False),
    "readings": ("readings", "readings.py", ["bite", "--box"], False),
    "timeline": ("timeline", "timeline.py", ["--box"], True),
}


def parse(argv: list[str]) -> dict | None:
    """The command line, or None to refuse. One source of boxes (a --stack
    file or one-or-more --box), one DOC, and the args after a lone `--`."""
    boxes: list[str] = []
    stack_file: str | None = None
    doc: str | None = None
    forwarded: list[str] = []
    i, n = 0, len(argv)
    while i < n:
        a = argv[i]
        if doc is None:
            if a == "--box":
                i += 1
                if i >= n:
                    return None
                boxes.append(argv[i])
            elif a == "--stack":
                i += 1
                if i >= n or stack_file is not None:
                    return None
                stack_file = argv[i]
            elif a.startswith("--") or not a:
                return None  # an unknown flag, or an empty DOC
            else:
                doc = a
        elif a == "--":
            forwarded = argv[i + 1 :]
            break
        else:
            return None  # junk after DOC that isn't the `--` passthrough
        i += 1
    if doc not in DOCS:
        return None
    if (stack_file is None) == (not boxes):  # neither, or both
        return None
    return {"doc": doc, "boxes": boxes, "stack": stack_file, "forwarded": forwarded}


def read_stack(path: Path) -> list[str] | None:
    """The box folders a --stack file names, each kept as written; None if the
    file can't be read."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    out = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line if Path(line).is_absolute() else str(path.parent / line))
    return out


def run_doc(doc: str, box: str, forwarded: list[str]) -> tuple[int, str]:
    """Run DOC over one box; (its exit code, the text it made). timeline
    writes a file, so it is given scratch to write and read back; the rest
    print, so their output is taken as it comes."""
    folder, script, before, to_file = DOCS[doc]
    path = STDLIB / folder / script
    if to_file:
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "doc.txt"
            got = _run(path, [*before, box, "--to", str(out), *forwarded])
            if out.exists():
                return got.returncode, out.read_text(encoding="utf-8")
            return got.returncode, (got.stdout or got.stderr).rstrip()
    got = _run(path, [*before, box, *forwarded])
    return got.returncode, (got.stdout or got.stderr).rstrip()


def _run(script: Path, argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *argv], capture_output=True, text=True
    )


def main(argv: list[str]) -> int:
    cfg = parse(argv)
    if cfg is None:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    folder, script, _, _ = DOCS[cfg["doc"]]
    if not (STDLIB / folder / script).is_file():
        print(f"refused: the {cfg['doc']} add-on isn't here", file=sys.stderr)
        return kernel.REFUSED
    if cfg["stack"] is not None:
        boxes = read_stack(Path(cfg["stack"]))
        if boxes is None:
            print(f"refused: can't read the stack list {cfg['stack']}", file=sys.stderr)
            return kernel.REFUSED
    else:
        boxes = cfg["boxes"]
    if not boxes:
        print("refused: the stack names no boxes", file=sys.stderr)
        return kernel.REFUSED
    for box in boxes:
        if not (Path(box) / "kernel.json").exists():
            print(f"refused: {box} isn't a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED

    print(f"stack of {len(boxes)} box{'es' if len(boxes) != 1 else ''}, {cfg['doc']}")
    flagged, worst = 0, kernel.ALIVE
    for box in boxes:
        code, text = run_doc(cfg["doc"], box, cfg["forwarded"])
        print(f"\n══ {box} ══")
        print(text if text.strip() else "    (nothing)")
        if code != kernel.ALIVE:
            flagged += 1
            worst = kernel.ESCALATE
    print(f"\n{flagged} of {len(boxes)} boxes flagged by {cfg['doc']} (exit 42).")
    return worst


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
