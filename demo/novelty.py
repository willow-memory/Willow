"""novelty.py: have this demo's pieces been put together before? Asks willow's
own search, the same way a new idea is vetted. Reusable by every demo.

    python demo/novelty.py "a sentence describing the demo or combination"
    python demo/novelty.py "..." --as DEMO   # a demo checking its own novelty

Two checks, both offline:

  1. the idea pile, through `similar`: is a planned idea close to this?
  2. every demo's README, through `scan` and the kernel's own rank: does an
     existing demo already hold half of this description's words?

A demo that has shipped holds its own description, so when a demo checks
itself it passes `--as DEMO` to leave its own README out: the question is
whether any *other* demo, or the idea pile, already holds the combination.

The kernel's rank serves a demo only when it holds half the description's
content words -- the same promise that it never answers what a folder doesn't
have. So if it serves nothing and `similar` finds nothing close, these pieces
have not been assembled before. BM25 names the nearest demo either way, as a
pointer to read, never a verdict.

It only reads, and writes nothing but its own scratch. Exit codes, the
kernel's: 0 novel (nothing close); 42 something close, look at it; 2 refused.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
import kernel  # noqa: E402
import scan  # noqa: E402

CLEAR = "Nothing on the list is close"  # similar's own words when the pile has none


def pile(desc: str) -> str:
    """What `similar near` says about the idea pile, verbatim."""
    got = subprocess.run(
        [sys.executable, str(ROOT / "adapters" / "stdlib" / "similar" / "similar.py"),
         "near", desc], capture_output=True, text=True)  # fmt: skip
    return got.stdout.strip()


def demos(desc: str, exclude: str | None = None):
    """(what the kernel's rank serves over the demo READMEs, the nearest by
    BM25). Serving nothing means no demo holds half of this description. With
    `exclude`, that demo's own README is left out (a demo checking itself)."""
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "readmes"
        src.mkdir()
        for r in sorted(ROOT.glob("demo/*/README.md")):
            if r.parent.name == exclude:
                continue
            (src / f"{r.parent.name}.md").write_text(
                r.read_text(encoding="utf-8", errors="replace")
            )
        idx = Path(d) / "idx"
        scan.build(src, idx)
        ix = scan.Index(idx)
        return ix.rank(desc, {}, 3, None), ix.bm25(desc, 1, None)


def main(argv: list[str]) -> int:
    exclude = None
    if len(argv) >= 2 and argv[-2] == "--as":
        exclude, argv = argv[-1], argv[:-2]
    if len(argv) != 1 or not argv[0].strip():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    desc = argv[0]
    said = pile(desc)
    served, nearest = demos(desc, exclude)
    print(f"idea pile (similar): {said.splitlines()[0] if said else '(no output)'}")
    if served:
        print("a demo already holds half of this description:")
        for c in served:
            print(f"    {c['path']}:{c['line']}  {c['text'].strip()[:70]}")
    else:
        print("demos (kernel rank): nothing holds half of this description")
    if nearest:
        print(f"nearest demo (bm25, a pointer, not a match): {nearest[0]['path']}")
    novel = not served and CLEAR in said
    print("\nnovel: these pieces have not been put together before" if novel
          else "\nnot clearly novel -- read what came up above before you build")  # fmt: skip
    return kernel.ALIVE if novel else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
