r"""equations.py: each displayed equation in LaTeX sources as a passage of its
own, with the sentences around it and its label. Python 3.9+.

    python adapters/stdlib/equations/equations.py mirror --from FOLDER --to MIRROR

The latex add-on drops math to keep a paper's prose; this keeps what it
drops. Walks FOLDER for .tex files (hidden folders and files skipped) and
writes, for each one that has a displayed equation, one passage per
equation, a blank line between them:

    main.tex line 120, label eq:oz
    The Ornstein-Zernike relation reads
    h(r) = c(r) + \rho \int c(|\mathbf{r}-\mathbf{r}'|) h(r') d\mathbf{r}'
    where $c(r)$ is the direct correlation function.

The first line cites the equation's own line in the .tex file and its
labels; then the end of the prose before it, the equation as its source
writes it (whitespace collapsed, `\label`, `\nonumber` and `\notag` taken
out), and the start of the prose after it. The math is never rewritten, so
a passage can be quoted back against the paper. Context is trimmed so a
passage fits in one of the kernel's chunks (`kernel.MAX_CHUNK`); an
equation longer than that alone is kept whole, and the kernel cuts it.

Displayed means the equation, align, gather, multline, eqnarray,
displaymath, flalign and alignat environments (starred or not), `\[ ... \]`
and `$$ ... $$`, after `\begin{document}` when there is one. A macro the
file defines without arguments as one of those openings or closings
(`\def\be{\begin{equation}}`, `\newcommand{\ee}{\end{equation}}`) is read
as what it stands for. Inline math stays in the prose around it.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no displayed equation, or that cannot be
read, is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

ENVS = "equation|align|gather|multline|eqnarray|displaymath|flalign|alignat"
DISPLAY = re.compile(
    r"\\begin\{(?P<env>"
    + ENVS
    + r")(?P<star>\*?)\}(?:\{[^{}]*\})?(?P<a>.*?)\\end\{(?P=env)(?P=star)\}"
    r"|(?<!\\)\\\[(?P<b>.*?)(?<!\\)\\\]"
    r"|(?<!\\)\$\$(?P<c>.*?)(?<!\\)\$\$",
    re.S,
)
OPENS = r"\\begin\{(?:" + ENVS + r")\*?\}|\\end\{(?:" + ENVS + r")\*?\}|\\\[|\\\]"
MACRO = re.compile(
    r"\\(?:def\s*\\(?P<d>[A-Za-z]+)|(?:re)?newcommand\*?\s*\{?\\(?P<n>[A-Za-z]+)\}?)"
    r"\s*\{\s*(?P<body>" + OPENS + r")\s*\}"
)
LABEL = re.compile(r"\\label\s*\{([^{}]*)\}")
NONUMBER = re.compile(r"\\(?:nonumber|notag)\b")
COMMENT = re.compile(r"(?<!\\)%[^\n]*")
SENTENCE_END = re.compile(r"[.!?:](?=\s)")
SKIP_ENVS = re.compile(
    r"\\begin\{(comment|verbatim|lstlisting|minted)\}.*?\\end\{\1\}", re.S
)

AFTER = 160  # characters of prose after an equation, at most
EXTS = (".tex",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)
USAGE = "usage: equations.py mirror --from FOLDER --to MIRROR"


def _blank(m: re.Match) -> str:
    """A match replaced by its newlines only, so every line keeps its number."""
    return "\n" * m.group(0).count("\n")


def _flat(text: str) -> str:
    return " ".join(text.split())


def expand(text: str) -> str:
    """The file's argument-less macros for a display's opening or closing read
    as what they stand for; their definitions blanked, line count kept."""
    names = {}
    for m in MACRO.finditer(text):
        names[m.group("d") or m.group("n")] = m.group("body")
    if not names:
        return text
    text = MACRO.sub(_blank, text)
    pattern = re.compile(
        r"\\(" + "|".join(sorted(names, key=len, reverse=True)) + r")(?![A-Za-z])"
    )
    return pattern.sub(lambda m: names[m.group(1)], text)


def _before(prose: str, room: int) -> str:
    """The end of the prose before an equation: its last paragraph, cut on the
    left at a sentence's start so it fits in `room` characters."""
    para = _flat(re.split(r"\n\s*\n", prose)[-1])
    if len(para) <= room:
        return para
    tail = para[len(para) - room :]
    m = SENTENCE_END.search(tail)
    if m and m.end() < len(tail) - 1:
        return tail[m.end() :].strip()
    if para[len(para) - room - 1] == " ":  # the cut fell between two words
        return tail
    cut = tail.find(" ")
    return tail[cut + 1 :] if cut >= 0 else ""


def _first_para(prose: str) -> str:
    """The paragraph an equation's closing line goes on with: none when a
    blank line follows the equation."""
    if re.match(r"[ \t]*\n[ \t]*\n", prose):
        return ""
    return re.split(r"\n\s*\n", prose.lstrip(), maxsplit=1)[0]


def _after(prose: str, room: int) -> str:
    """The start of the prose after an equation: up to its first sentence's
    end, within its paragraph and `room` characters."""
    para = _flat(_first_para(prose))
    m = SENTENCE_END.search(para)
    if m:
        para = para[: m.end()]
    if len(para) <= room:
        return para
    cut = para.rfind(" ", 0, room + 1)
    return para[:cut] if cut > 0 else ""


def _said_after(prose: str) -> int:
    """How much of the prose after an equation `_after` serves with it: up to
    its first paragraph's first sentence end, so the next equation's lead-in
    doesn't serve it again. 0 when that paragraph has no sentence end."""
    para = _first_para(prose)
    m = SENTENCE_END.search(para)
    return len(prose) - len(prose.lstrip()) + m.end() if m else 0


def passages(data: bytes, name: str) -> list[str]:
    """One passage per displayed equation in a .tex file's bytes; `name` is
    the file's relative path, for the citation line."""
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    text = COMMENT.sub("", text)
    text = SKIP_ENVS.sub(_blank, text)
    text = expand(text)
    start = text.find("\\begin{document}")
    begin = start if start >= 0 else 0
    end = text.find("\\end{document}", begin)
    text = text[: end if end >= 0 else len(text)]
    found = list(DISPLAY.finditer(text, begin))
    out = []
    for i, m in enumerate(found):
        body = (
            m.group("a")
            if m.group("a") is not None
            else m.group("b")
            if m.group("b") is not None
            else m.group("c")
        )
        labels = LABEL.findall(body)
        eq = _flat(NONUMBER.sub("", LABEL.sub("", body)))
        if not eq:
            continue
        line = text.count("\n", 0, m.start()) + 1
        head = f"{name} line {line}" + (
            ", label " + ", ".join(x.strip() for x in labels) if labels else ""
        )
        prev_end = found[i - 1].end() if i else begin
        prev_end += _said_after(text[prev_end : m.start()]) if i else 0
        next_start = found[i + 1].start() if i + 1 < len(found) else len(text)
        room = kernel.MAX_CHUNK - len(head) - len(eq) - 4  # the newlines between
        after = _after(text[m.end() : next_start], min(AFTER, max(room // 2, 0)))
        room -= len(after)
        before = _before(
            text[prev_end : m.start()].replace("\\begin{document}", ""), max(room, 0)
        )
        out.append("\n".join(x for x in (head, before, eq, after) if x))
    return out


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


def mirror(src: Path, dst: Path) -> tuple[int, int, int]:
    """Write the passages of `src` into `dst`. Returns (files written,
    equations, files skipped)."""
    wrote = count = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            found = passages(path.read_bytes(), rel.as_posix())
            if not found:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("\n\n".join(found) + "\n").encode("utf-8"))
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
        count += len(found)
    return wrote, count, skipped


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
    wrote, count, skipped = mirror(src, dst)
    print(
        f"wrote {count} equations from {wrote} files to {opts['--to']}; skipped {skipped}"
    )
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
