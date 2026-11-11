"""same.py: two kept runs of one stack, step by step: was each step asked
the same way, and did it print the same thing?

    python demo/shared-runs/same.py PROJECT PROJECT

Each PROJECT is a folder demo/kept's rebuild.sh ran the stack into. For
each step both runs ended, it says four things:

    asked       whether the stack's own mark of the step is the same in
                both: the add-on and its arguments, hashed, as they ran
    as written  whether a mark made from the step as the stack file writes
                it, before any folder is filled in, is the same
    printed     whether what the step printed is the same bytes
    placeless   whether it is the same once each run's own folders are
                written the way the stack file writes them

and for a step that still differs, the first line that does, from each.
It reads the two projects and writes nothing. Exit codes, the kernel's:
0 compared; 2 a bad command line, or a folder that is not such a project.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
STARTED = re.compile(r"^(\d+) ([a-z0-9-]+): started \((\w+)")
ENDED = re.compile(r"^(\d+) ([a-z0-9-]+): exit (\d+)")
STEP = re.compile(r"^- ([a-z0-9-]+) -- (.*)$", flags=re.M)


def placeless(text: str, project: Path) -> str:
    """The text with this run's folders written as the stack file writes them."""
    return (
        text.replace(str(project / "pile"), "<pile>")
        .replace(str(project / "box"), "{box}")
        .replace(str(project), "<scratch>")
        .replace(str(ROOT), "<repo>")
    )


def steps(project: Path) -> dict[int, dict]:
    """{a step's place: its add-on, its mark as run, its exit, what it
    printed}, for each step the run's log says ended."""
    out: dict[int, dict] = {}
    for line in (
        (project / "run" / "00-stack.txt").read_text(encoding="utf-8").splitlines()
    ):
        m = STARTED.match(line)
        if m:
            out[int(m.group(1))] = {"addon": m.group(2), "mark": m.group(3)}
        m = ENDED.match(line)
        if m and int(m.group(1)) in out:
            out[int(m.group(1))]["exit"] = int(m.group(3))
    for n in list(out):
        files = sorted((project / "run").glob(f"{n:02d}-*.txt"))
        if "exit" not in out[n] or not files:
            del out[n]
            continue
        out[n]["text"] = files[0].read_text(encoding="utf-8", errors="replace")
    return out


def written_marks(project: Path) -> dict[int, str]:
    """{a step's place: a mark made as stack makes one, from the step as it
    is written once this run's folders are taken back out}."""
    text = placeless((project / "stack.md").read_text(encoding="utf-8"), project)
    import shlex

    return {
        n: kernel.h256(json.dumps([name, shlex.split(args)]))[:8]
        for n, (name, args) in enumerate(STEP.findall(text), 1)
    }


def first_difference(a: str, b: str) -> tuple[str, str]:
    for x, y in zip(a.splitlines(), b.splitlines()):
        if x != y:
            return x, y
    return f"({len(a.splitlines())} lines)", f"({len(b.splitlines())} lines)"


def compare(a: Path, b: Path) -> list[dict]:
    one, two = steps(a), steps(b)
    wa, wb = written_marks(a), written_marks(b)
    out = []
    for n in sorted(set(one) & set(two)):
        x, y = one[n], two[n]
        px, py = placeless(x["text"], a), placeless(y["text"], b)
        row = {
            "n": n,
            "addon": x["addon"],
            "asked": x["mark"] == y["mark"],
            "as_written": wa.get(n) == wb.get(n) and wa.get(n) is not None,
            "printed": x["text"] == y["text"],
            "placeless": px == py,
            "exit": x["exit"] == y["exit"],
        }
        if not row["placeless"]:
            row["differs"] = [line[:160] for line in first_difference(px, py)]
            row["sha256"] = [
                hashlib.sha256(t.encode()).hexdigest()[:12] for t in (px, py)
            ]
        out.append(row)
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not all(
        (Path(p) / "run" / "00-stack.txt").is_file() for p in argv
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    rows = compare(Path(argv[0]).resolve(), Path(argv[1]).resolve())
    for row in rows:
        print(json.dumps(row, ensure_ascii=False))
    n = len(rows)
    counts = {
        k: sum(1 for r in rows if r[k])
        for k in ("asked", "as_written", "printed", "placeless", "exit")
    }
    print(
        f"{n} steps: asked the same {counts['asked']}, the same as written {counts['as_written']}, "
        f"printed the same {counts['printed']}, the same without the place {counts['placeless']}, "
        f"ended the same {counts['exit']}"
    )
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
