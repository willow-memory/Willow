r"""notation.py: each displayed equation in LaTeX sources with the words its
paper gives for its symbols, so a question in words finds the equation.
Python 3.9+.

    python adapters/stdlib/notation/notation.py mirror --from FOLDER --to MIRROR

The equations add-on makes each displayed equation a passage of its own,
with the prose around it. But an equation is mostly symbols, and a question
is asked in words: "what is the structure factor in terms of the direct
correlation function?" shares no word with `S(q) = 1/(1 - \rho \hat{c}(q))`.
A paper says what its symbols mean, once, somewhere: "where $\eta$ is the
packing fraction", "the structure factor $S(q)$", "$c(r)$ denotes the
direct correlation function". This reads those sentences into a glossary
for each folder of .tex files (one paper), and writes each equation as the
equations add-on does, with one more line naming the words for the symbols
it uses:

    main.tex line 120, label eq:oz
    symbols: S structure factor; \rho number density; c direct correlation function
    so the Ornstein-Zernike equation also gives
    S(q) = \frac{1}{1 - \rho \hat{c}(q)}
    where $c(r)$ is the direct correlation function.

A definition is read in two shapes, in the prose and never inside math:

- a noun phrase of up to four words, after an article, right before a
  symbol: "the packing fraction $\eta$", "a form factor $P(q)$";
- a symbol, then "is", "denotes", "stands for", "represents" or "being",
  an article and a noun phrase: "where $\eta$ is the packing fraction".

A symbol is one letter or a Greek letter (`\eta`, `\rho`), with any accent
(`\hat{c}` is c), subscript, superscript or argument: `S(q)` and `c(r)` are
S and c. Math holding more than one symbol (`\rho\sigma^3`, `x = 1`) defines
nothing, and so does a lone generic word ("the coefficient $a$"). A symbol
given different words keeps the first two. A symbols line holds at most 200
characters; past that, the symbols it reaches last are left out. An equation
names each symbol once, in the order it first uses them; a symbol its
paper never defines is left out, and an equation using none it defines gets
no symbols line.

The passage keeps the equations add-on's shape and its limit: the symbols
line takes its room from the prose before the equation, so a passage still
fits in one of the kernel's chunks (`kernel.MAX_CHUNK`). The math is never
rewritten.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file is read as the equations add-on reads it
(UTF-8, else Windows-1252, else Latin-1). A file with no displayed equation,
or that cannot be read, is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused
(FOLDER is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "equations"))
import equations  # noqa: E402
import kernel  # noqa: E402

GREEK = (
    "alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa "
    "lambda mu nu xi pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi "
    "psi omega Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega ell"
).split()
ACCENT = re.compile(
    r"\\(?:hat|tilde|bar|widehat|widetilde|overline|vec|mathbf|boldsymbol|bm"
    r"|mathcal|mathrm)\s*\{([^{}]*)\}"
)
#: one symbol: a letter or a Greek letter, then any subscript, superscript
#: or argument, and nothing else
SYMBOL = re.compile(
    r"^\s*(?P<head>\\(?:" + "|".join(GREEK) + r")(?![A-Za-z])|[A-Za-z])"
    r"(?:\s*[_^]\s*(?:\{[^{}]*\}|\\?[A-Za-z0-9]+))*"
    r"\s*(?:\([^()]*\))?\s*$"
)
TOKEN = re.compile(r"\\([A-Za-z]+)|([A-Za-z])")
INLINE = re.compile(r"(?<![\\$])\$(?!\$)([^$]{1,40}?)(?<!\\)\$")
WORD = r"[A-Za-z][A-Za-z\-]*"
#: "the packing fraction $\eta$": up to four words after an article
BEFORE = re.compile(
    r"\b(?:the|a|an|its|our|their)\s+((?:" + WORD + r"\s+){0,3}" + WORD + r")\s*,?\s*$",
    re.I,
)
#: "$\eta$ is the packing fraction"
AFTER = re.compile(
    r"^\s*,?\s*(?:is|denotes|stands\s+for|represents|being)\s+(?:the|a|an)\s+"
    r"((?:" + WORD + r"\s+){0,4}" + WORD + r")"
)
#: words a phrase doesn't end on, and words that show it isn't a name
TRAIL = {"of", "and", "or", "which", "that", "in", "at", "for", "with", "to",
         "by", "on", "is", "are", "as", "from", "we", "where", "when", "then"}  # fmt: skip
NOT_NAMES = {"is", "are", "was", "were", "be", "we", "it", "this", "that", "these",
             "which", "where", "when", "with", "and", "or", "if", "then", "so",
             "same", "following", "above", "below", "case", "limit", "equation",
             "eq", "eqs", "expression", "relation", "result", "value", "values"}  # fmt: skip
#: one word that names nothing on its own
GENERIC = {"coefficient", "coefficients", "factor", "function", "functions",
           "parameter", "quantity", "expression", "expressions", "order", "form",
           "term", "terms", "constant", "region", "behavior", "behaviour",
           "simple", "link", "element", "group", "importance", "evaluation",
           "determination", "system", "approximate", "roots", "variable",
           "number", "integer", "fluid", "particles", "particle", "model"}  # fmt: skip
#: words a name doesn't hold: verbs and judgements around a symbol
VERBS = {"represents", "denotes", "stands", "gives", "given", "defined", "called",
         "known", "involved", "more", "less", "small", "large", "good", "quality",
         "consistency", "condition", "expanding", "crucial", "standard", "one"}  # fmt: skip
#: a name starts after the last of these inside a phrase ("of" stays: "number
#: of particles" is one name)
CUT = {"the", "a", "an", "at", "in", "on", "for", "with", "by", "from", "to", "as"}
NAMES_KEPT = 2  # different words for one symbol, at most
LINE_AT_MOST = 200  # characters of a symbols line: the prose keeps its room
USAGE = "usage: notation.py mirror --from FOLDER --to MIRROR"


def _unaccent(math: str) -> str:
    for _ in range(3):  # accents inside accents
        math = ACCENT.sub(r"\1", math)
    return math


def symbol(math: str) -> str | None:
    """The one symbol inline math names, or None when it names none or several."""
    m = SYMBOL.match(_unaccent(math))
    return m.group("head") if m else None


def _phrase(words: str, before: bool = False) -> str | None:
    """A noun phrase; None if it isn't one. Right `before` a symbol it must
    end on its name ("the density and $x$" names nothing); after one, its
    trailing small words are dropped ("is the density of" is the density)."""
    parts = words.split()
    if before and parts and parts[-1].lower() in TRAIL:
        return None
    inner = [i for i, p in enumerate(parts) if p.lower() in CUT]
    if inner:  # "a fluid at packing fraction": the name is after the last cut
        parts = parts[inner[-1] + 1 :]
    while parts and parts[-1].lower() in TRAIL:
        parts.pop()
    if not parts or any(p.lower() in NOT_NAMES | VERBS for p in parts):
        return None
    if len(parts) == 1 and (len(parts[0]) < 4 or parts[0].lower() in GENERIC):
        return None
    return " ".join(p.lower() for p in parts)


def _prose(data: bytes) -> str:
    """A .tex file's prose with its inline math, on one line: comments,
    verbatim and displayed equations taken out."""
    text = equations.decode(data).replace("\r\n", "\n")
    text = equations.COMMENT.sub("", text)
    text = equations.SKIP_ENVS.sub(equations._blank, text)
    text = equations.DISPLAY.sub(" ", equations.expand(text))
    return " ".join(text.split())


def glossary(files: list[bytes]) -> dict[str, list[str]]:
    """Each symbol a paper defines, with the words it defines it by, in the
    order they come: read from the prose around its inline math."""
    out: dict[str, list[str]] = {}
    for data in files:
        flat = _prose(data)
        for m in INLINE.finditer(flat):
            sym = symbol(m.group(1))
            if not sym:
                continue
            b = BEFORE.search(flat[max(0, m.start() - 80) : m.start()])
            a = AFTER.match(flat[m.end() : m.end() + 120])
            for words in (_phrase(b.group(1), before=True) if b else None,
                          _phrase(a.group(1)) if a else None):  # fmt: skip
                names = out.setdefault(sym, [])
                if words and words not in names and len(names) < NAMES_KEPT:
                    names.append(words)
    return {s: n for s, n in out.items() if n}


def used(eq: str) -> list[str]:
    """The symbols an equation uses, each once, in the order it first does."""
    seen: list[str] = []
    for m in TOKEN.finditer(_unaccent(eq)):
        if m.group(1) and m.group(1) not in GREEK:
            continue  # \frac, \int, \left: not a symbol
        sym = "\\" + m.group(1) if m.group(1) else m.group(2)
        if sym not in seen:
            seen.append(sym)
    return seen


def line_for(eq: str, words: dict[str, list[str]]) -> str:
    """The symbols line for an equation, or "" when it uses none defined."""
    line = ""
    for s in used(eq):
        if s in words:
            more = f"{'; ' if line else 'symbols: '}{s} {' / '.join(words[s])}"
            if len(line) + len(more) > LINE_AT_MOST:
                break
            line += more
    return line


def passages(data: bytes, name: str, words: dict[str, list[str]]) -> list[str]:
    """One passage per displayed equation, as the equations add-on makes them,
    with a line naming the words for the symbols it uses."""
    text = equations.decode(data).replace("\r\n", "\n")
    text = equations.COMMENT.sub("", text)
    text = equations.SKIP_ENVS.sub(equations._blank, text)
    text = equations.expand(text)
    start = text.find("\\begin{document}")
    begin = start if start >= 0 else 0
    end = text.find("\\end{document}", begin)
    text = text[: end if end >= 0 else len(text)]
    found = list(equations.DISPLAY.finditer(text, begin))
    out = []
    for i, m in enumerate(found):
        body = next(m.group(g) for g in "abc" if m.group(g) is not None)
        labels = equations.LABEL.findall(body)
        eq = equations._flat(equations.NONUMBER.sub("", equations.LABEL.sub("", body)))
        if not eq:
            continue
        line = text.count("\n", 0, m.start()) + 1
        head = f"{name} line {line}" + (
            ", label " + ", ".join(x.strip() for x in labels) if labels else ""
        )
        names = line_for(eq, words)
        prev_end = found[i - 1].end() if i else begin
        next_start = found[i + 1].start() if i + 1 < len(found) else len(text)
        room = kernel.MAX_CHUNK - len(head) - len(names) - len(eq) - 5
        after = equations._after(
            text[m.end() : next_start], min(equations.AFTER, max(room // 2, 0))
        )
        room -= len(after)
        before = equations._before(
            text[prev_end : m.start()].replace("\\begin{document}", ""), max(room, 0)
        )
        out.append("\n".join(x for x in (head, names, before, eq, after) if x))
    return out


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int, int, int]:
    """Write the passages of `src` into `dst`. Returns (files written,
    equations, equations given a symbols line, files skipped). A folder's
    .tex files are one paper, and share one glossary."""
    wrote = count = named = skipped = 0
    by_folder: dict[Path, list[Path]] = {}
    for p in equations._sources(src):
        by_folder.setdefault(p.parent, []).append(p)
    for files in by_folder.values():
        held = {}
        for p in files:
            try:
                held[p] = p.read_bytes()
            except OSError:
                pass
        words = glossary(list(held.values()))
        for path in files:
            rel = path.relative_to(src)
            try:
                if path not in held:
                    raise OSError(path)
                found = passages(held[path], rel.as_posix(), words)
                if not found:
                    skipped += 1
                    continue
                target = dst.joinpath(rel.parent, rel.name + ".txt")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(("\n\n".join(found) + "\n").encode("utf-8"))
            except equations.ERRORS:
                skipped += 1
                continue
            wrote += 1
            count += len(found)
            named += sum("\nsymbols: " in p for p in found)
    return wrote, count, named, skipped


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
    wrote, count, named, skipped = mirror(src, dst)
    print(f"found {count} equations; {named} given the words for their symbols")
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
