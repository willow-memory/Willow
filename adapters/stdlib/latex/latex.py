r"""latex.py: LaTeX sources as plain prose, line for line. Python 3.9+.

    python adapters/stdlib/latex/latex.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .tex files (hidden folders and files skipped) and writes each
as the prose it holds, with the commands taken off. The mirror has the same
number of lines as the source and each line is the source's line, so a passage
found in the mirror is on that line of the .tex file:

    \section{Method}                 ->   Method
    We use \emph{two} \cite{smith}.  ->   We use two [smith].

What is dropped: comments, the preamble (but a `\title` and `\author` are kept
as "title:" and "author:"), math (inline, display and the equation, align and
similar environments), verbatim, listings and pictures, and the commands that
only lay a page out or name a thing (`\label`, `\ref`, `\usepackage`,
`\includegraphics`, `\vspace`, `\newcommand` and their kind) with their
arguments. What is kept: the text of a command's argument (`\section`,
`\textbf`, `\emph`, `\caption`, `\footnote`, `\href`), a citation as [key],
an `\item` as "- ", escaped characters as themselves, `--` and `---` as dashes,
and accents (an umlaut, an acute, a cedilla) as the letters they make.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no prose, or that cannot be read, is skipped
and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import unicodedata
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

ACCENTS = {
    '"': "\u0308",
    "'": "\u0301",
    "`": "\u0300",
    "^": "\u0302",
    "~": "\u0303",
    "=": "\u0304",
    ".": "\u0307",
    "c": "\u0327",
    "v": "\u030c",
}
ENVS = ("equation|align|gather|multline|eqnarray|displaymath|math|verbatim|lstlisting|tikzpicture|minted|filecontents|"
        "flalign|alignat|split|array|picture|pgfpicture|algorithmic|algorithm2e|comment")  # fmt: skip
KILL_ENV = re.compile(r"\\begin\{(" + ENVS + r")\*?\}.*?\\end\{\1\*?\}", re.S)
KILL_MATH = re.compile(
    r"\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\\)\$[^$]*?(?<!\\)\$", re.S
)
DROP_ARG = ("label|ref|eqref|pageref|autoref|cref|Cref|usepackage|documentclass|bibliographystyle|bibliography|includegraphics|input|include|"
            "vspace|hspace|vspace\\*|hspace\\*|setlength|addtolength|pagestyle|thispagestyle|newcommand|renewcommand|providecommand|def|"
            "newtheorem|setcounter|addcontentsline|graphicspath|DeclareMathOperator|geometry|hypersetup|bibitem|index|glossary|color|"
            "begin|end|newenvironment|renewenvironment|lstset|captionsetup|pgfplotsset|tikzset|usetikzlibrary|usetheme|usecolortheme")  # fmt: skip
DROP = re.compile(
    r"\\(?:"
    + DROP_ARG
    + r")\*?(?:\s*\[[^\]]*\])*(?:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})*"
)
CITE = re.compile(
    r"\\(?:cite[a-z]*|parencite|textcite|footcite|autocite)\*?(?:\s*\[[^\]]*\])*\s*\{([^{}]*)\}"
)
HREF = re.compile(r"\\href\s*\{[^{}]*\}\s*\{([^{}]*)\}")
FOOT = re.compile(r"\\footnote\s*\{([^{}]*)\}")
META = re.compile(r"\\(title|author|date)\s*(?:\[[^\]]*\])?\s*\{(.*)\}\s*$")
WORD = re.compile(r"\\([A-Za-z]+)\*?")


def keep_lines(m: re.Match) -> str:
    return "\n" * m.group(0).count("\n")


def accent(m: re.Match) -> str:
    return unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)])


def line_text(text: str) -> str:
    """One line's commands taken off, its prose kept."""
    text = CITE.sub(lambda m: "[" + m.group(1).replace(" ", "") + "]", text)
    text = HREF.sub(r"\1", text)
    text = DROP.sub("", text)
    text = FOOT.sub(lambda m: " (" + m.group(1) + ")", text)
    text = re.sub(
        r"\\item\b\s*(?:\[([^\]]*)\])?",
        lambda m: "- " + (m.group(1) + " " if m.group(1) else ""),
        text,
    )
    text = re.sub(r"\\([\"'`^~=.])\s*\{?\\?([A-Za-z])\}?", accent, text)
    text = re.sub(
        r"\\([cv])(?:\s*\{([A-Za-z])\}|\s+([A-Za-z])(?![A-Za-z]))",
        lambda m: unicodedata.normalize(
            "NFC", (m.group(2) or m.group(3)) + ACCENTS[m.group(1)]
        ),
        text,
    )
    for tex, ch in (
        (r"\ss", "ß"),
        (r"\o", "ø"),
        (r"\O", "Ø"),
        (r"\ae", "æ"),
        (r"\AE", "Æ"),
        (r"\aa", "å"),
        (r"\AA", "Å"),
        (r"\l", "ł"),
        (r"\L", "Ł"),
        (r"\i", "ı"),
    ):
        text = re.sub(re.escape(tex) + r"(?![A-Za-z])\s*", ch, text)
    text = text.replace("\\\\", " ")
    for esc in "&%$_#{}":
        text = text.replace("\\" + esc, esc)
    text = WORD.sub("", text)
    text = (
        text.replace("---", "—")
        .replace("--", "–")
        .replace("``", "“")
        .replace("''", "”")
        .replace("~", " ")
    )
    text = text.replace("{", "").replace("}", "")
    return " ".join(text.split())


def convert(data: bytes) -> str | None:
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    text = re.sub(r"(?<!\\)%[^\n]*", "", text)
    text = KILL_ENV.sub(keep_lines, text)
    text = KILL_MATH.sub(keep_lines, text)
    lines = text.split("\n")
    start = next((i for i, raw in enumerate(lines) if "\\begin{document}" in raw), None)
    out = []
    for i, raw in enumerate(lines):
        if start is not None and i < start:  # the preamble: a title and an author only
            m = META.search(raw.strip())
            out.append(f"{m.group(1)}: {line_text(m.group(2))}" if m else "")
        else:
            out.append(line_text(raw))
    result = "\n".join(out)
    return result.rstrip("\n") + "\n" if result.strip() else None


EXTS = (".tex",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: latex.py mirror --from FOLDER --to MIRROR"


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
