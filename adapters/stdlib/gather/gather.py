"""gather.py: folders and files you name, copied into your pile. Python 3.9+.

    python adapters/stdlib/gather/gather.py --from PATH [--from PATH ...] --to FOLDER
        [--keep .py,.md] [--skip tests,data,test_*.py] [--json]

    gather: populated, 148 files copied from 3 places, 212 left out
      panes        61 files
      widgets      74 files
      app.py       1 file
    ## left out
      not a kind you keep   170 files
      a name you skip       41 files
      looks like a key      1 file

A pile is what the kernel reads. This makes one from places you name: each
folder is copied to FOLDER under its own name, each single file straight
into FOLDER. Your places are only read. One line of a stack per source, so
the list of what a project is made of is the top of its stack.

`--keep` is the file endings that go in (every kind when you give none);
`--skip` is names left out, a folder or a file, `*` standing for anything.
Three things never go in whatever you ask: a file that looks like a key
(.key, .pem, .env, a name holding "secret", an SSH key), a file over 1 MB
(the kernel wouldn't read it), and a hidden folder or one of the kinds no
one reads (.git, node_modules, a virtual environment, caches).

Run it again to refresh: a file gone from a folder you named goes from its
copy too. Only inside the copies it made: FOLDER's other contents are left.

It writes under --to and nowhere else. Exit codes, the kernel's: 0 copied;
42 a place you named isn't there (the rest is copied), or nothing was
copied; 2 refused.
"""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    "usage: gather.py --from PATH [--from PATH ...] --to FOLDER "
    "[--keep .py,.md] [--skip tests,data] [--json]"
)
#: the kernel reads no file bigger than this
BIGGEST = 1_000_000
#: folders no one reads, whatever is asked
NEVER = ("node_modules", "venv", "__pycache__", "dist", "build")
#: names that look like a key: never copied anywhere
KEYS = ("*.key", "*.pem", ".env*", "*secret*", "id_rsa*", "id_ed25519*", "*.p12")
#: why a file was left out, in the order said
WHY = ("not a kind you keep", "a name you skip", "looks like a key", "over 1 MB")


def named(name: str, patterns) -> bool:
    """Whether a file or folder name matches one of the patterns."""
    return any(fnmatch.fnmatch(name.lower(), p.lower()) for p in patterns)


def why_not(path: Path, keep: list[str], skip: list[str]) -> str | None:
    """Why a file stays out, or None when it goes in. A key is said first."""
    if named(path.name, KEYS):
        return "looks like a key"
    if named(path.name, skip):
        return "a name you skip"
    if keep and path.suffix.lower() not in keep:
        return "not a kind you keep"
    try:
        if path.stat().st_size > BIGGEST:
            return "over 1 MB"
    except OSError:
        return "a name you skip"
    return None


def files_of(folder: Path, skip: list[str]):
    """(each file under a folder, as a path from it), hidden folders, the
    ones no one reads, the ones skipped and links left out; sorted."""
    for top, dirs, names in os.walk(folder):
        dirs[:] = sorted(
            d
            for d in dirs
            if not d.startswith(".") and d not in NEVER and not named(d, skip)
        )
        for n in sorted(names):
            p = Path(top) / n
            if not p.is_symlink() and p.is_file():
                yield p, p.relative_to(folder)


def copy(src: Path, dst: Path) -> None:
    """One file copied, unless the copy already holds the same bytes."""
    if dst.is_file() and dst.read_bytes() == src.read_bytes():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def sweep(root: Path, kept: set[Path]) -> int:
    """Files under a copy that the source no longer gives, removed, and the
    folders that leaves empty; how many files went."""
    gone = 0
    for top, dirs, names in os.walk(root, topdown=False):
        for n in names:
            p = Path(top) / n
            if p not in kept:
                p.unlink()
                gone += 1
        if Path(top) != root and not os.listdir(top):
            os.rmdir(top)
    return gone


def gather(sources: list[Path], to: Path, keep: list[str], skip: list[str]):
    """(files copied by source, files left out by reason, the sources that
    aren't there, files removed as gone)."""
    took: list[tuple[str, int]] = []
    out = dict.fromkeys(WHY, 0)
    missing: list[str] = []
    gone = 0
    for src in sources:
        if src.is_dir():
            root = to / src.name
            kept: set[Path] = set()
            for p, rel in files_of(src, skip):
                why = why_not(p, keep, skip)
                if why:
                    out[why] += 1
                    continue
                copy(p, root / rel)
                kept.add(root / rel)
            if root.is_dir():
                gone += sweep(root, kept)
            took.append((src.name, len(kept)))
        elif src.is_file():
            why = why_not(src, [], skip)  # a file named by hand is a kind kept
            if why:
                out[why] += 1
                took.append((src.name, 0))
            else:
                copy(src, to / src.name)
                took.append((src.name, 1))
        else:
            missing.append(str(src))
    return took, out, missing, gone


def count(n: int, word: str = "file") -> str:
    return f"{n} {word}{'s' * (n != 1)}"


def report(took, out, missing, gone) -> dict:
    """The report every report add-on prints: state, one line, rows."""
    n = sum(c for _, c in took)
    left = sum(out.values())
    said = f"{count(n)} copied from {count(len(took), 'place')}"
    if left:
        said += f", {left} left out"
    if gone:
        said += f", {gone} removed as gone"
    if missing:
        said += f", {count(len(missing), 'place')} not there"
    groups = [
        (None, [(name, count(c)) for name, c in took]),
        ("left out", [(w, count(out[w])) for w in WHY if out[w]]),
        ("not there", [(m, "named, and not a file or folder") for m in missing]),
    ]
    return {
        "addon": "gather",
        "state": "populated",  # every place named is a row, copied from or not
        "said": said,
        "groups": [
            {"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
            for g, rows in groups
            if rows
        ],
    }


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    lines = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            lines.append(f"## {g['name']}")
        lines += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(lines)


def listed(text: str) -> list[str]:
    return [x.strip() for x in text.split(",") if x.strip()]


def main(argv: list[str]) -> int:
    froms: list[str] = []
    opts: dict[str, str] = {}
    as_json = False
    it = iter(argv)
    for a in it:
        if a == "--from":
            froms.append(next(it, ""))
        elif a in ("--to", "--keep", "--skip"):
            opts[a] = next(it, "")
        elif a == "--json":
            as_json = True
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
    if not froms or not all(froms) or not opts.get("--to"):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    to = Path(opts["--to"]).expanduser().resolve()
    sources = [Path(f).expanduser().resolve() for f in froms]
    for s in sources:
        if s == to or s in to.parents or to in s.parents:
            print(
                f"refused: {s} and {to} hold one another; a copy inside its "
                "own source would copy itself",
                file=sys.stderr,
            )
            return kernel.REFUSED
    names = [s.name for s in sources]
    twice = sorted({n for n in names if names.count(n) > 1})
    if twice:
        print(
            f"refused: two places are both named {twice[0]}; one would "
            "overwrite the other. Give each its own --to",
            file=sys.stderr,
        )
        return kernel.REFUSED
    keep = [k if k.startswith(".") else "." + k for k in listed(opts.get("--keep", ""))]
    keep = [k.lower() for k in keep]
    to.mkdir(parents=True, exist_ok=True)
    took, out, missing, gone = gather(sources, to, keep, listed(opts.get("--skip", "")))
    doc = report(took, out, missing, gone)
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))
    copied = sum(c for _, c in took)
    return kernel.ESCALATE if missing or not copied else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
