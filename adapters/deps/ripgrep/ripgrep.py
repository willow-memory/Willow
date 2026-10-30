"""ripgrep.py: exact search through ripgrep, each hit checked against the kernel.

    python adapters/deps/ripgrep/ripgrep.py --box DIR [--ignore-case] "TEXT"

Needs the ripgrep program (MIT or Unlicense), from the PyPI wheel pinned in
requirements.txt beside this file, or an `rg` already on your PATH:

    pip install -r adapters/deps/ripgrep/requirements.txt

ripgrep finds every line of your pile that holds TEXT, as written (not a
pattern; --ignore-case for any case), far faster than reading every file in
Python on a big folder. It reads what the kernel reads: hidden files and
folders are skipped, and .gitignore is not obeyed, since the kernel doesn't.

Each hit is then checked against the kernel: the files holding one are cut
into passages by the kernel's own `chunks`, and a hit is shown with the id
(SHA-256) of the passage that holds it, the one the kernel would serve and
cite. A hit the kernel doesn't read as written (in a binary, a file not
UTF-8 or too big, a page's markup, or past where it cuts a long line) is
counted, never shown as a passage:

    letters/county.txt:4  3f2a9c1b04de  You may file a response within 180 days
    2 hits in 2 passages; 1 not as the kernel reads it

It reads only, and writes nothing but a scratch folder of links it removes.
Without ripgrep it refuses and names the install; it never skips quietly.
Exit codes, the kernel's: 0 a hit in a passage; 42 none; 2 refused.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/ripgrep/requirements.txt"


def program(name: str) -> str | None:
    """`name` beside this Python (a virtual environment's wheel), else on PATH."""
    here = Path(sys.executable).parent / (name + (".exe" if os.name == "nt" else ""))
    return str(here) if here.is_file() else shutil.which(name)


def hits(rg: str, pile: Path, text: str, fold: bool) -> list[tuple[str, int, str]]:
    """[(path relative to the pile, line number, the line)], sorted."""
    argv = [rg, "--json", "--fixed-strings", "--no-ignore", "--no-messages"]
    argv += ["--ignore-case"] if fold else ["--case-sensitive"]
    got = subprocess.run(argv + ["--", text, "."], cwd=pile, capture_output=True)
    if got.returncode not in (0, 1):  # 1 is "nothing found"
        raise RuntimeError(got.stderr.decode("utf-8", "replace").strip() or "rg failed")
    out = []
    for line in got.stdout.splitlines():
        msg = json.loads(line)
        if msg["type"] != "match":
            continue
        d = msg["data"]
        path = d["path"].get("text")
        said = d["lines"].get("text")
        if path is None or said is None:  # a name or line not UTF-8
            continue
        rel = Path(path).as_posix().removeprefix("./")
        out.append((rel, d["line_number"], said.rstrip("\r\n")))
    return sorted(set(out))


def passages(pile: Path, paths: set[str]) -> dict[str, list[dict]]:
    """The kernel's passages of just these files, by path: the kernel's own
    `chunks`, run on a scratch folder of links to them at the same paths."""
    with tempfile.TemporaryDirectory() as tmp:
        for rel in paths:
            link = Path(tmp) / rel
            link.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(pile / rel, link)
        out: dict[str, list[dict]] = {}
        for c in kernel.chunks(Path(tmp)):
            out.setdefault(c["path"], []).append(c)
    return out


def holder(chunks: list[dict], line: int, said: str, fold: bool) -> dict | None:
    """The passage holding `line`, if its text holds the line as the kernel
    kept it."""
    for c in chunks:
        n = c["text"].count("\n") + 1
        if c["line"] <= line < c["line"] + n:
            kept = c["text"].split("\n")[line - c["line"]]
            want = said.strip()
            ok = want.lower() in kept.lower() if fold else want in kept
            return c if ok and want else None
    return None


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    args: list[str] = []
    fold = False
    it = iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        elif a == "--ignore-case":
            fold = True
        else:
            args.append(a)
    if not opts.get("--box") or len(args) != 1 or not args[0].strip():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    rg = program("rg")
    if rg is None:
        print(f"refused: ripgrep needs the rg program: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    _, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    pile = Path(kernel.config(box)["pile"]).resolve()
    try:
        found = hits(rg, pile, args[0], fold)
    except RuntimeError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return kernel.REFUSED
    found = [h for h in found if not any(p.startswith(".") for p in h[0].split("/"))]
    chunks = passages(pile, {p for p, *_ in found})
    shown, outside, ids = 0, 0, set()
    for path, line, said in found:
        c = holder(chunks.get(path, []), line, said, fold)
        if c is None:
            outside += 1
            continue
        shown += 1
        ids.add(c["id"])
        print(f"{path}:{line}  {c['id'][:12]}  {' '.join(said.split())}")
    tail = (
        f"; {outside} not as the kernel reads {'it' if outside == 1 else 'them'}"
        if outside
        else ""
    )
    print(f"{shown} hit{'s' * (shown != 1)} in {len(ids)} "
          f"passage{'s' * (len(ids) != 1)}{tail}")  # fmt: skip
    return kernel.ALIVE if shown else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
