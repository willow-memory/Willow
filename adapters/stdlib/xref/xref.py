"""xref.py: every reference in your files, checked. Python 3.9+.

    python adapters/stdlib/xref/xref.py --box DIR
    python adapters/stdlib/xref/xref.py --from FOLDER

Two kinds of reference, found in the text files of your folder:

    link       a Markdown link, [the trip](trips/2019.md), or a web page's
               href or src, to another file of yours
    file:line  a place written out, care/log.txt:12, as answers cite them

and each is checked: the linked file is there; the file named is there and
has that line. A link is followed from the folder its file is in; a
file:line from there, then from the top of your folder. What doesn't hold is
listed with where it's written:

    notes/index.md:4      link       trips/2019.md: not there
    letters/reply.txt:9   file:line  care/log.txt:40: past the end (31 lines)

A link to the web, an e-mail address or a place in the same page isn't a
file of yours and isn't checked; one that leads out of your folder is
counted as not checked, never followed; a file:line naming no file in your
folder may be somewhere else entirely and is left alone. The patterns are
willow-bot's own xref (onescript/xref.py), for one person's folder instead
of a set of repositories.

It only reads, and writes nothing. Exit codes, the kernel's: 0 every
reference holds; 42 one doesn't; 2 refused.
"""

from __future__ import annotations

import posixpath
import re
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: willow-bot's RE_LINK and RE_FILELINE, the extensions a person's files have
RE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
RE_HREF = re.compile(r"""(?i)\b(?:href|src)\s*=\s*["']([^"'#][^"']*)["']""")
_EXT = r"txt|md|markdown|html?|csv|tsv|ics|vcf|eml|log|json|ya?ml|org|tex|rst|py|sh|ini|conf"
RE_FILELINE = re.compile(
    r"(?<![\w/.\-])((?:[\w.\-]+/)*[\w.\-]+\.(?:" + _EXT + r")):(\d+)(?![\w:])", re.I
)
NOT_A_FILE = re.compile(r"(?i)^(?:[a-z][a-z0-9+.\-]*:|//|#)")


def text_files(pile: Path):
    """(relative path, lines) for each text file, as the kernel reads them."""
    for p in sorted(pile.rglob("*")):
        rel = p.relative_to(pile)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        try:
            raw = p.read_bytes()
            if len(raw) > kernel.MAX_FILE or b"\0" in raw[: kernel.SNIFF]:
                continue
            yield rel.as_posix(), raw.decode("utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue


def references(rel: str, lines: list[str]):
    """(line, kind, target, wanted line or None) for each reference."""
    html = rel.lower().endswith((".html", ".htm"))
    for n, line in enumerate(lines, 1):
        for m in (RE_HREF if html else RE_LINK).finditer(line):
            yield n, "link", m.group(1), None
        if not html:
            for m in RE_FILELINE.finditer(line):
                yield n, "file:line", m.group(1), int(m.group(2))


def inside(rel: str) -> bool:
    return not (rel == ".." or rel.startswith("../") or rel.startswith("/"))


def check(pile: Path) -> dict:
    """{"broken": [(where, kind, what, why)], "held": n, "outside": n}."""
    files = dict(text_files(pile))
    every = {p.relative_to(pile).as_posix() for p in pile.rglob("*") if p.is_file()}
    out = {"broken": [], "held": 0, "outside": 0}
    for rel, lines in files.items():
        here = posixpath.dirname(rel)
        for n, kind, target, want in references(rel, lines):
            where = f"{rel}:{n}"
            if kind == "link":
                if NOT_A_FILE.match(target):
                    continue
                path = posixpath.normpath(
                    posixpath.join(here, unquote(target.split("#")[0].split("?")[0]))
                )
                if not inside(path):
                    out["outside"] += 1
                elif path in every or (pile / path).is_dir():
                    out["held"] += 1
                else:
                    out["broken"].append((where, kind, target, "not there"))
                continue
            near = posixpath.normpath(posixpath.join(here, target))
            found = near if near in every else target if target in every else None
            if found is None:
                continue  # may name a file somewhere else entirely
            have = len(files[found]) if found in files else None
            if have is not None and want > have:
                out["broken"].append(
                    (where, kind, f"{target}:{want}", f"past the end ({have} lines)")
                )
            else:
                out["held"] += 1
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if args or len(opts) != 1 or not next(iter(opts.values()), ""):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if "--box" in opts:
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        pile = Path(kernel.config(box)["pile"])
    else:
        pile = Path(opts["--from"])
        if not pile.is_dir():
            print(f"refused: {pile} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    got = check(pile)
    broken = got["broken"]
    if broken:
        width = max(len(w) for w, *_ in broken)
        for where, kind, what, why in broken:
            print(f"{where:<{width}}  {kind:<9}  {what}: {why}")
        print()
    total = got["held"] + len(broken)
    outside = (
        f"; {got['outside']} leading out of your folder, not checked"
        if got["outside"]
        else ""
    )
    print(f"{total} reference{'s' if total != 1 else ''} checked, "
          f"{len(broken)} {'don' if len(broken) != 1 else 'doesn'}'t hold{outside}.")  # fmt: skip
    return kernel.ESCALATE if broken else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
