r"""code_comments.py: A codebase's comments and docstrings, line for line. Python 3.9+.

    python adapters/stdlib/code-comments/code_comments.py mirror --from FOLDER --to MIRROR

Walks FOLDER for source files (hidden folders and files skipped) and writes, for
each, a file of **the same number of lines** whose line N holds the comment text
that was on line N of the source, and is blank where the source had none. The
kernel cites a passage by its file and line, so a hit in the mirror is the
source's own line number:

    # A cache of parsed answers, kept for a minute.
    <blank>
    The seconds an entry lives before it is parsed again.

Comments are found by what each language writes them as: Python's `#` comments
and its docstrings (read by the language's own tokenizer and parser, so a `#`
inside a string is not a comment); `//`, `///` and `/* ... */` in C, C++, Java,
JavaScript, TypeScript, Go, Rust, C#, Kotlin, Swift and PHP (strings, template
strings and character literals are stepped over); and `#` in shell and Ruby (a
`#!` line is not a comment). The comment marks are taken off. A file with no
comment, or a Python file that does not parse, is skipped and counted.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import ast
import io
import re
import tokenize
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

C_LIKE = (
    ".c",
    ".h",
    ".cc",
    ".cpp",
    ".hpp",
    ".java",
    ".js",
    ".mjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".cs",
    ".kt",
    ".swift",
    ".php",
)
HASH_LIKE = (".sh", ".rb")
CHAR = re.compile(r"'(?:\\.[^'\n]*|[^\\'\n])'")
SINGLE_QUOTED = (".js", ".mjs", ".ts", ".tsx", ".jsx", ".php", ".rb", ".sh")


def python_comments(text: str) -> dict[int, list[str]]:
    found: dict[int, list[str]] = {}
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            body = tok.string.lstrip("#").strip()
            if body and not tok.string.startswith("#!"):
                found.setdefault(tok.start[0], []).append(body)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if (
            isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            )
            and node.body
        ):
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                for offset, line in enumerate(first.value.value.split("\n")):
                    if line.strip():
                        found.setdefault(first.value.lineno + offset, []).append(
                            line.strip()
                        )
    return found


def c_like_comments(text: str, ext: str) -> dict[int, list[str]]:
    found: dict[int, list[str]] = {}
    i, n, line = 0, len(text), 1
    quotes = (
        "\"'`"
        if ext in SINGLE_QUOTED
        else '"`'
        if ext
        in (
            ".go",
            ".rs",
            ".cs",
            ".kt",
            ".swift",
            ".c",
            ".h",
            ".cc",
            ".cpp",
            ".hpp",
            ".java",
        )
        else '"'
    )

    def add(line_no: int, raw: str) -> None:
        body = (
            raw.strip().lstrip("*/").strip()
            if raw.strip().startswith(("*", "/"))
            else raw.strip()
        )
        if body and body != "*":
            found.setdefault(line_no, []).append(body)

    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            end = n if end == -1 else end
            add(line, text[i:end].lstrip("/").strip())
            i = end
        elif text.startswith("/*", i):
            close = text.find("*/", i + 2)
            end, body_end = (n, n) if close == -1 else (close + 2, close)
            for k, part in enumerate(text[i + 2 : body_end].split("\n")):
                add(line + k, part.strip().lstrip("*").strip())
            line += text.count("\n", i, end)
            i = end
        elif (
            ext == ".php"
            and c == "#"
            or ext in HASH_LIKE
            and c == "#"
            and not (text.startswith("#!", i) and line == 1)
        ):
            end = text.find("\n", i)
            end = n if end == -1 else end
            add(line, text[i:end].lstrip("#").strip())
            i = end
        elif c == "'" and ext not in SINGLE_QUOTED:
            m = CHAR.match(text, i)
            i = m.end() if m else i + 1
        elif c in quotes:
            j = i + 1
            while j < n and text[j] != c and not (text[j] == "\n" and c != "`"):
                j += 2 if text[j] == "\\" else 1
            line += text.count("\n", i, min(j, n))
            i = j + 1
        else:
            i += 1
    return found


def convert(data: bytes, name: str = "") -> str | None:
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    ext = Path(name).suffix.lower()
    if ext == ".py":
        found = python_comments(text)
    elif ext in C_LIKE or ext in HASH_LIKE:
        found = c_like_comments(text, ext)
    else:
        return None
    if not found:
        return None
    count = len(text.split("\n")) - (1 if text.endswith("\n") else 0)
    return "\n".join(" ".join(found.get(k, [])) for k in range(1, count + 1)) + "\n"


EXTS = (
    ".py",
    ".c",
    ".h",
    ".cc",
    ".cpp",
    ".hpp",
    ".java",
    ".js",
    ".mjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".cs",
    ".kt",
    ".swift",
    ".php",
    ".sh",
    ".rb",
)
ERRORS = (OSError, UnicodeDecodeError, ValueError, SyntaxError, tokenize.TokenError)

USAGE = "usage: code_comments.py mirror --from FOLDER --to MIRROR"


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
            text = convert(path.read_bytes(), path.name)
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
