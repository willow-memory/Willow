"""code_shape.py: search code by its shape, not its words, through ast-grep.

    python adapters/deps/code-shape/code_shape.py --box DIR --lang LANG "PATTERN"

Needs the ast-grep program (MIT), from the PyPI wheel pinned in
requirements.txt beside this file (`ast-grep-cli`), or an `ast-grep` already
on your PATH:

    pip install -r adapters/deps/code-shape/requirements.txt

PATTERN is code with holes: `$NAME` matches one piece, `$$$` any number. So
`requests.get($$$)` is every call of it, however its arguments are written
and whatever the line around it says, and `subprocess.run($$$, shell=True)`
every call that hands a shell its command:

    python adapters/deps/code-shape/code_shape.py --box DIR --lang python "requests.get($$$)"
    app/fetch.py:12  5b0d7e21a9c4  requests.get(url, timeout=3)
    app/sync.py:40  e1f04c6b2d88  requests.get(f"{base}/items")
    2 matches in 2 passages

LANG is one ast-grep parses: python, javascript, typescript, tsx, go, rust,
java, c, cpp, csharp, ruby, kotlin, swift, html, css and more; a file is
read as LANG by its extension. It reads what the kernel reads: hidden files
and folders are skipped, and .gitignore is not obeyed.

Each match is checked against the kernel, as the ripgrep add-on checks its
hits: shown with the id of the kernel's passage that holds its first line,
the one the kernel would serve and cite; one the kernel doesn't read as
written (a file too big, past where it cuts a long line) is counted, never
shown. A match is shown as its first line.

It reads only, and writes nothing but a scratch folder of links it removes.
Without ast-grep it refuses and names the install; it never skips quietly.
Exit codes, the kernel's: 0 a match in a passage; 42 none; 2 refused (a
pattern or language ast-grep refused, among them).
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

INSTALL = "pip install -r adapters/deps/code-shape/requirements.txt"
#: every ignore file but the hidden-file rule, which the kernel keeps too
NO_IGNORE = ["dot", "exclude", "global", "parent", "vcs"]


def program(name: str) -> str | None:
    """`name` beside this Python (a virtual environment's wheel), else on PATH."""
    here = Path(sys.executable).parent / (name + (".exe" if os.name == "nt" else ""))
    return str(here) if here.is_file() else shutil.which(name)


def matches(sg: str, pile: Path, pattern: str, lang: str) -> list[tuple[str, int, str]]:
    """[(path relative to the pile, first line number, that line)], sorted."""
    argv = [sg, "run", "--pattern", pattern, "--lang", lang, "--json=stream"]
    for kind in NO_IGNORE:
        argv += ["--no-ignore", kind]
    got = subprocess.run(argv + ["."], cwd=pile, capture_output=True)
    if got.returncode not in (0, 1):  # 1 is "nothing found"
        raise RuntimeError(
            got.stderr.decode("utf-8", "replace").strip() or "ast-grep failed"
        )
    out = []
    for line in got.stdout.decode("utf-8", "replace").splitlines():
        m = json.loads(line)
        rel = Path(m["file"]).as_posix().removeprefix("./")
        first = m["lines"].split("\n")[0]
        out.append((rel, m["range"]["start"]["line"] + 1, first))
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


def holder(chunks: list[dict], line: int, said: str) -> dict | None:
    """The passage holding `line`, if it holds the line as the kernel kept it."""
    for c in chunks:
        n = c["text"].count("\n") + 1
        if c["line"] <= line < c["line"] + n:
            kept = c["text"].split("\n")[line - c["line"]]
            return c if said.strip() and said.strip() in kept else None
    return None


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    args: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--box", "--lang"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (not opts.get("--box") or not opts.get("--lang") or len(args) != 1
            or not args[0].strip()):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    sg = program("ast-grep")
    if sg is None:
        print(
            f"refused: code-shape needs the ast-grep program: {INSTALL}",
            file=sys.stderr,
        )
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
        found = matches(sg, pile, args[0], opts["--lang"])
    except RuntimeError as exc:
        print(f"refused: {' '.join(str(exc).split())[:300]}", file=sys.stderr)
        return kernel.REFUSED
    found = [m for m in found if not any(p.startswith(".") for p in m[0].split("/"))]
    chunks = passages(pile, {p for p, *_ in found})
    shown, outside, ids = 0, 0, set()
    for path, line, said in found:
        c = holder(chunks.get(path, []), line, said)
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
    print(f"{shown} match{'es' * (shown != 1)} in {len(ids)} "
          f"passage{'s' * (len(ids) != 1)}{tail}")  # fmt: skip
    return kernel.ALIVE if shown else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
