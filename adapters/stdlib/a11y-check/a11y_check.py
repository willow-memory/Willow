"""a11y_check.py: your documents read as a screen reader will meet them.

    python adapters/stdlib/a11y-check/a11y_check.py --box DIR
    python adapters/stdlib/a11y-check/a11y_check.py --from FOLDER

Every Markdown and HTML document of your folder, checked for what trips a
screen reader, each problem with its file and line:

    notes/trip.md:12   image without a description: ![](beach.jpg)
    notes/trip.md:30   heading jumps from h1 to h3: ### Day two
    2 problems in 1 of 14 documents

Two things are checked, and nothing else is guessed at:

- **an image without a description.** A Markdown image whose brackets are
  empty, and an HTML `img` tag with no alt attribute at all. An HTML
  `alt=""` is left alone: it is the author saying the image is decoration,
  which Markdown has no way to say.
- **a heading out of order.** One more than a level deeper than the heading
  before it (h1 to h3), which a screen reader's outline renders as a hole.
  A document's first heading may be any level: notes often start at h2 on
  purpose. Markdown headings are the `#` kind; a line underlined with equals
  signs is not read.

Lines inside fenced code blocks are code, not document, and are not checked.
Other kinds of files are other jobs: this reads `.md`, `.markdown`, `.html`
and `.htm`, by their own bytes, never a mirror's text, which has no tags
left to check. Hidden files and folders are never read.

It only reads. Exit codes, the kernel's, as the audits use them: 0 no
problems; 42 problems found, or nothing there to check; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KINDS = (".md", ".markdown", ".html", ".htm")
MD_IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\([^)]*\)")
HTML_IMAGE = re.compile(r"<img\b[^>]*>", re.IGNORECASE | re.DOTALL)
ALT = re.compile(r"""\balt\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", re.IGNORECASE)
MD_HEADING = re.compile(r"^(#{1,6})\s")
HTML_HEADING = re.compile(r"<h([1-6])\b", re.IGNORECASE)
FENCE = re.compile(r"^(```|~~~)")


def shown(text: str) -> str:
    return " ".join(text.split())[:60]


def md_problems(lines: list[str]):
    """(line, problem) for a Markdown document: empty image brackets, and a
    heading more than a level deeper than the one before. A fenced code
    block is code, not document."""
    level, fenced = 0, False
    for n, line in enumerate(lines, 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for m in MD_IMAGE.finditer(line):
            if not m.group("alt").strip():
                yield n, f"image without a description: {shown(m.group())}"
        got = MD_HEADING.match(line)
        if got:
            deep = len(got.group(1))
            if level and deep > level + 1:
                yield n, f"heading jumps from h{level} to h{deep}: {shown(line)}"
            level = deep


def html_problems(text: str):
    """(line, problem) for an HTML document: an img tag with no alt attribute
    at all (alt="" is the author's say that it is decoration), and a heading
    more than a level deeper than the one before."""
    marks = []
    for m in HTML_IMAGE.finditer(text):
        if not ALT.search(m.group()):
            marks.append(
                (m.start(), f"image without a description: {shown(m.group())}")
            )
    level = 0
    for m in HTML_HEADING.finditer(text):
        deep = int(m.group(1))
        if level and deep > level + 1:
            marks.append((m.start(), f"heading jumps from h{level} to h{deep}"))
        level = deep
    for at, problem in sorted(marks):
        yield text.count("\n", 0, at) + 1, problem


def documents(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in KINDS
        and not any(part.startswith(".") for part in p.relative_to(folder).parts)
    )


def audit(folder: Path) -> tuple[list[tuple[str, int, str]], int]:
    """((path, line, problem) in file order, documents checked)."""
    docs = documents(folder)
    out = []
    for p in docs:
        text = p.read_text(encoding="utf-8", errors="ignore")
        rel = p.relative_to(folder).as_posix()
        if p.suffix.lower() in (".md", ".markdown"):
            found = list(md_problems(text.splitlines()))
            found += [
                (n, why)
                for n, why in html_problems(text)
                if "image" in why  # raw img tags appear in Markdown too
            ]
        else:
            found = list(html_problems(text))
        out += [(rel, n, why) for n, why in sorted(found)]
    return out, len(docs)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    given = [k for k in ("--box", "--from") if opts.get(k)]
    if len(given) != 1 or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if given == ["--box"]:
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        folder = Path(kernel.config(box)["pile"])
    else:
        folder = Path(opts["--from"])
        if not folder.is_dir():
            print(f"refused: {folder} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    found, checked = audit(folder)
    if not checked:
        print("No documents (.md or .html) to check.")
        return kernel.ESCALATE
    if not found:
        print(f"No screen-reader problems in {checked}"
              f" document{'s' if checked != 1 else ''}.")  # fmt: skip
        return kernel.ALIVE
    width = max(len(f"{p}:{n}") for p, n, _ in found)
    for p, n, why in found:
        print(f"{f'{p}:{n}':<{width}}  {why}")
    files = len({p for p, _, _ in found})
    print(f"{len(found)} problem{'s' if len(found) > 1 else ''}"
          f" in {files} of {checked} documents")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
