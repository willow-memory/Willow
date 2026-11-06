"""asciidoc.py: AsciiDoc documents as the text they show, line for line. Python 3.9+.

    python adapters/stdlib/asciidoc/asciidoc.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .adoc, .asciidoc and .asc files (hidden folders and files
skipped; an .asc file that is PGP armor, not AsciiDoc, is passed over without
being counted) and writes each as the text it shows, with the markup taken off.
The mirror has the same number of lines as the source and each line is the
source's line, so a passage found in the mirror is on that line of the file:

    == Tides                               ->   Tides
    :revdate: 2024-03-03                   ->   revdate: 2024-03-03
    *Bold* and link:https://x.org[a site]  ->   Bold and a site (https://x.org)
    | Leeds | 6 | 2024-03-03                ->   Leeds; 6; 2024-03-03

Titles keep their text. The document's own attributes (author, revdate,
version and the like) are kept as "name: value"; other attribute lines are
blank, and a `{name}` reference is replaced by the value set earlier in the
file (left as written when nothing set it). Listing, literal and source blocks
are kept as written; example, sidebar, quote and open blocks keep their text;
the delimiter and attribute lines are blank. Comments are blank. An admonition
is "note: ...", "warning: ...". Bold, italic, monospace and highlight lose
their marks, never inside a word. A link is its text, with the address after
it in brackets when it goes outside the folder; a cross reference is its text;
an image is its alt text; a footnote is its text in brackets; a list item is
"- " (a checklist item keeps its box, [ ] or [x]), a description "term: text".
A table's line is its cells joined by "; ", the header row kept once where
it is (written onto every row, a header would be a word in every passage); a
cell that runs on over several lines keeps its later lines as plain text. An
`include::` is blank and never followed.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no text, or that cannot be read, is skipped
and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: the document attributes a person asks about, kept as "name: value"
META = {
    "author", "authors", "email", "revnumber", "revdate", "revremark", "version",
    "description", "keywords", "organization", "copyright", "doctitle", "subtitle",
}  # fmt: skip
#: AsciiDoc's own character attributes
BUILTIN = {
    "nbsp": " ", "sp": " ", "empty": "", "blank": "", "zwsp": "", "wj": "",
    "plus": "+", "amp": "&", "lt": "<", "gt": ">", "startsb": "[", "endsb": "]",
    "vbar": "|", "caret": "^", "asterisk": "*", "tilde": "~", "backslash": "\\",
    "backtick": "`", "apos": "'", "quot": '"', "lsquo": "‘", "rsquo": "’",
    "ldquo": "“", "rdquo": "”", "deg": "°", "two-colons": "::", "two-semicolons": ";;",
    "cpp": "C++", "pp": "++", "brvbar": "¦", "amp;": "&",
}  # fmt: skip
ADMONITIONS = ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")

DELIM = re.compile(
    r"^(-{4,}|\.{4,}|={4,}|\*{4,}|_{4,}|/{4,}|\+{4,}|--|`{3}.*|[|!,:]={3,})$"
)
ATTR_ENTRY = re.compile(r"^:(!?\w[^:]*?!?):(?:\s+(.*?))?\s*$")
SECTION = re.compile(r"^(={1,6}|#{1,6})\s+(\S.*?)(?:\s+\1)?\s*$")
BLOCK_ATTRS = re.compile(r"^\[([^\[\]].*)?\]$|^\[\[[^\[\]]*\]\]$")
BLOCK_TITLE = re.compile(r"^\.([^\s.].*)$")
ADMONITION = re.compile(r"^(" + "|".join(ADMONITIONS) + r"):\s+(.*)$")
LIST = re.compile(r"^\s*(\*{1,5}|-|\.{1,5})\s+(\S.*)$")
NUMBERED = re.compile(r"^\s*(\d+)\.\s+(\S.*)$")
DLIST = re.compile(r"^\s*(\S.*?)(:{2,4}|;;)(?:\s+(.*))?$")
DIRECTIVE = re.compile(r"^(ifn?def|ifeval|endif)::.*\[.*\]$")
BLOCK_MACRO = re.compile(r"^([a-z][\w-]*)::(\S*?)\[(.*)\]$")
BREAK = re.compile(r"^('{3,}|<{3}|-{3}|\*{3}|- - -|\* \* \*)$")

SCHEME = r"(?:https?|ftp|irc|file)://"
URL_MACRO = re.compile(
    r"(?<![\w/])(?:link:)?((?:" + SCHEME + r"|mailto:)[^\s\[\]]+)\[([^\]]*)\]"
)
LINK_MACRO = re.compile(r"(?<![\w/])link:([^\s\[\]]+)\[([^\]]*)\]")
BARE_URL = re.compile(r"<?(" + SCHEME + r"[^\s\[\]<>]*[^\s\[\]<>.,;:!?)'\"])>?")
XREF = re.compile(r"(?<!\w)xref:([^\s\[\]]+)\[([^\]]*)\]")
ANGLE_XREF = re.compile(r"<<([^<>,]+?)(?:,\s*([^<>]*?))?>>")
IMAGE = re.compile(r"(?<!\w)image:([^\s\[\]:][^\s\[\]]*)\[([^\]]*)\]")
FOOTNOTE = re.compile(r"\s*footnote(?:ref)?:([\w-]*)\[([^\]]*)\]")
KBD = re.compile(r"(?<!\w)(?:kbd|btn):\[([^\]]*)\]")
MENU = re.compile(r"(?<!\w)menu:([^\s\[\]]+)\[([^\]]*)\]")
MATH = re.compile(r"(?<!\w)(?:stem|latexmath|asciimath):\[([^\]]*)\]")
ANCHOR = re.compile(r"\[\[[^\[\]]*\]\]|(?<!\w)anchor:[\w-]+\[([^\]]*)\]")
OPEN_MACRO = re.compile(
    r"(?<![\w/])(link:|xref:|image:|footnote:|kbd:|btn:)?"
    r"((?:" + SCHEME + r"|mailto:)[^\s\[\]]*|[^\s\[\]:]*)\[([^\[\]]*)$"
)
INDEX = re.compile(r"\({3}.*?\){3}|(?<!\w)indexterm:\[[^\]]*\]")
INDEX_SHOWN = re.compile(r"\(\(([^()]+)\)\)|(?<!\w)indexterm2:\[([^\]]*)\]")
ROLE = re.compile(r"\[[.#%]?[\w .#%-]*\](?=[#*_`])")
PASS = re.compile(
    r"(?<!\w)\+\+\+(.+?)\+\+\+|pass:[a-z,]*\[(.*?)\]|(?<![\w+])\+\+(\S.*?)\+\+(?!\+)"
    r"|`\+(.+?)\+`|(?<![\w+`])\+(\S|\S.*?\S)\+(?![\w+])"
)
ESCAPE = re.compile(r"\\([*_`#^~+{\[<(]|link:|image:|footnote:|kbd:)")
ATTR_REF = re.compile(r"\{([\w][\w-]*)\}")
ENTITY = re.compile(r"&(?:[A-Za-z]+\d*|#\d+|#[xX][0-9A-Fa-f]+);")
CELL_SPEC = re.compile(
    r"(?:\d+\*)?(?:\d*(?:\.\d+)?\+)?(?:[<^>])?(?:\.[<^>])?[adehlmsv]?"
)
TAIL_SPEC = re.compile(
    r"\s((?:\d+\*)|(?:\d*(?:\.\d+)?\+)[<^>]?(?:\.[<^>])?[adehlmsv]?)$"
)


def constrained(c: str) -> re.Pattern:
    e = re.escape(c)
    return re.compile(rf"(?<![\w{e}\\]){e}(\S|\S.*?\S){e}(?![\w{e}])")


def unconstrained(c: str) -> re.Pattern:
    e = re.escape(c)
    return re.compile(rf"{e}{e}(\S|\S.*?\S){e}{e}")


QUOTES = [unconstrained(c) for c in "*_#"] + [constrained(c) for c in "*_#"]
MONO = (unconstrained("`"), constrained("`"))
SUPSUB = re.compile(r"(?<![\w^])\^(\S+?)\^|(?<![\w~])~([^\s~/]+?)~(?![\w~])")


def link_text(raw: str) -> str:
    """The shown text of a macro's brackets: `text,window=_blank` or `"a, b",role=x`."""
    raw = raw.strip()
    if raw.startswith('"'):
        end = raw.find('"', 1)
        if end > 0:
            return raw[1:end]
    m = re.match(r"^(.*?)(?:,\s*\w+=.*)?$", raw)
    return m.group(1).rstrip("^").strip() if m else raw


def alt_text(raw: str) -> str:
    """An image's alt text: the first of `Alt, width, height` or `"A, b",role=x`."""
    raw = raw.strip()
    if raw.startswith('"'):
        return link_text(raw)
    return raw.split(",")[0].strip()


def subst_attrs(text: str, attrs: dict[str, str]) -> str:
    """`{name}` as the value set earlier in the file, or as written."""

    def ref(m: re.Match) -> str:
        name = m.group(1).lower()
        if name in attrs:
            return attrs[name]
        return BUILTIN.get(name, m.group(0))

    return ATTR_REF.sub(ref, text)


OPENS = {c: re.compile(rf"(?<![\w*_\\]){re.escape(c)}(?=[^\s*_])") for c in "*_"}
CLOSES = {c: re.compile(rf"(?<=[^\s*_\\]){re.escape(c)}(?![\w*_])") for c in "*_"}


class Span:
    """A paragraph's bold or italic still open, and the lines still to come."""

    def __init__(self) -> None:
        self.opened: set[str] = set()
        self.later = lambda: ""


def paragraph_after(lines: list[str], at: int) -> list[str]:
    """The rest of the paragraph after line `at`: up to the next blank line."""
    out = []
    for line in lines[at + 1 :]:
        if not line.strip():
            break
        out.append(line)
    return out


def inline(text: str, attrs: dict[str, str], span: Span | None = None) -> str:
    """One line of prose with its marks taken off and its words kept. With
    `span`, a bold or italic that opens here and closes on a later line of the
    paragraph loses its marks too, one on each line."""
    held: list[str] = []

    def hold(s: str) -> str:
        held.append(s)
        return f"\0{len(held) - 1}\0"

    text = PASS.sub(lambda m: hold(next(g for g in m.groups() if g is not None)), text)
    text = ESCAPE.sub(lambda m: hold(m.group(1)), text)
    text = subst_attrs(text, attrs)

    def url(m: re.Match) -> str:
        target, shown = m.group(1), link_text(m.group(2))
        bare = target[7:] if target.startswith("mailto:") else target
        if not shown or shown == bare:
            return hold(bare)
        return f"{shown} ({hold(bare)})"

    def link(m: re.Match) -> str:  # a link to a file in the folder: its text
        return link_text(m.group(2)) or hold(m.group(1))

    text = URL_MACRO.sub(url, text)
    text = LINK_MACRO.sub(link, text)
    text = BARE_URL.sub(lambda m: hold(m.group(1)), text)
    text = XREF.sub(lambda m: link_text(m.group(2)) or hold(m.group(1)), text)
    text = ANGLE_XREF.sub(
        lambda m: (m.group(2) or "").strip() or hold(m.group(1)), text
    )
    text = IMAGE.sub(lambda m: alt_text(m.group(2)), text)
    text = FOOTNOTE.sub(
        lambda m: f" ({m.group(2).strip()})" if m.group(2).strip() else "", text
    )
    text = KBD.sub(lambda m: m.group(1).strip(), text)
    text = MENU.sub(
        lambda m: " > ".join(
            [m.group(1)] + [p.strip() for p in m.group(2).split(">") if p.strip()]
        ),
        text,
    )
    text = MATH.sub(lambda m: hold(m.group(1)), text)
    text = ANCHOR.sub(lambda m: m.group(1) or "", text)
    text = INDEX.sub("", text)
    text = INDEX_SHOWN.sub(lambda m: m.group(1) or m.group(2), text)
    text = re.sub(r'"`(.+?)`"', r"“\1”", text)
    text = re.sub(r"'`(.+?)`'", r"‘\1’", text)
    for pattern in MONO:
        text = pattern.sub(lambda m: hold(m.group(1)), text)
    text = ROLE.sub("", text)
    for _ in range(2):  # *_both_* takes two passes
        for pattern in QUOTES:
            text = pattern.sub(r"\1", text)
    text = SUPSUB.sub(lambda m: m.group(1) or m.group(2), text)
    text = text.replace("(C)", "©").replace("(R)", "®").replace("(TM)", "™")
    text = re.sub(
        r"(?<=\w)--(?=\w)| -- ", lambda m: " — " if m.group(0) == " -- " else "—", text
    )
    text = ENTITY.sub(lambda m: html.unescape(m.group(0)), text)
    text = re.sub(r"\s\+$", "", text)
    if span is not None:
        for c in "*_":
            if c in span.opened and CLOSES[c].search(text):
                text = CLOSES[c].sub("", text, count=1)
                span.opened.discard(c)
            m = OPENS[c].search(text)
            if m and c not in span.opened and CLOSES[c].search(span.later()):
                text = text[: m.start()] + text[m.end() :]
                span.opened.add(c)
    while "\0" in text:
        text = re.sub(r"\0(\d+)\0", lambda m: held[int(m.group(1))], text)
    return " ".join(text.split())


def run_on(line: str, carry: list[str]) -> tuple[str, list[str]]:
    """A macro whose brackets run on to the next line, one line at a time:
    `link:x.adoc[the long` / `name]` is "the long" / "name", an address or a
    footnote's closing bracket put after the text on the line that closes it.
    `carry` holds what each open bracket closes with, the innermost last."""
    carry = list(carry)
    while carry:
        m = re.match(r"^([^\[\]]*)\](.*)$", line)
        if not m:
            break
        line = m.group(1) + carry.pop() + m.group(2)
    opened: list[str] = []  # innermost first, as they are found
    while True:
        m = OPEN_MACRO.search(line)
        if not m or not (m.group(1) or re.match(SCHEME + "|mailto:", m.group(2))):
            break
        macro, target, shown = m.group(1) or "link:", m.group(2), m.group(3)
        if macro == "footnote:":
            shown, close = " (" + shown, ")"
        elif macro == "link:" and re.match(SCHEME + "|mailto:", target):
            close = f" (+++{target.removeprefix('mailto:')}+++)"
        else:
            close = ""
        opened.append(close)
        line = line[: m.start()] + shown
    return line, carry + opened[::-1]


def block_attrs(inner: str) -> tuple[str, list[str], dict[str, str]]:
    """A `[style,pos,name=value]` line: its style, positionals and named values."""
    parts = re.findall(r'(?:[^,"]|"[^"]*")+', inner) if inner else []
    style, positional, named = "", [], {}
    for n, part in enumerate(parts):
        part = part.strip()
        key, eq, value = part.partition("=")
        if eq and re.fullmatch(r"[\w-]+", key.strip()):
            named[key.strip().lower()] = value.strip().strip('"')
            continue
        if n == 0:  # `source%linenums`, `#id.role`: the style is before them
            style = re.split(r"[#.%]", part)[0].strip().lower()
        positional.append(part)
    return style, positional, named


def table(
    lines: list[str], named: dict[str, str], delim: str, attrs: dict[str, str]
) -> list[str]:
    """A table's lines, each as its cells' text joined by "; ".

    The header row stays where it is, once, as the source wrote it: a header
    written onto every row would be a word in every row's passage, and a
    question pairing it with anything the folder lacks would be served a row.
    A line that only continues a cell is that text alone."""
    fmt = named.get("format", {",": "csv", ":": "dsv"}.get(delim[0], "psv"))
    sep = named.get("separator") or {"csv": ",", "dsv": ":", "tsv": "\t"}.get(
        fmt, delim[0]
    )
    out = []
    for raw in lines:
        line = raw.strip()
        if fmt == "dsv":
            cells = [c.replace("\\:", ":") for c in re.split(r"(?<!\\):", line)]
        elif fmt in ("csv", "tsv"):
            cells = next(csv.reader([line], delimiter=sep), [])
        else:
            parts = re.split(r"(?<!\\)" + re.escape(sep), line)
            # a line that starts cells, or one whose first part runs a cell on
            if len(parts) > 1 and CELL_SPEC.fullmatch(parts[0].strip()):
                parts = parts[1:]
            cells = []
            for k, cell in enumerate(parts):
                m = TAIL_SPEC.search(cell) if k < len(parts) - 1 else None
                cells.append(
                    (cell[: m.start()] if m else cell).replace("\\" + sep, sep)
                )
        out.append("; ".join(v for v in (inline(c, attrs) for c in cells) if v))
    return out


def convert(data: bytes) -> str | None:
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    lines = text.split("\n")
    out: list[str] = []
    attrs: dict[str, str] = {}
    stack: list[tuple[str, str]] = []  # (delimiter, kind) of the blocks we are in
    pending: tuple[str, list[str], dict[str, str]] = ("", [], {})
    prefix = ""  # an admonition's label, for the next line of text
    header = 0  # lines of the document header still to come: author, revision
    seen_text = False
    literal = False  # inside a paragraph kept as written
    table_buf: list[str] = []
    table_open: tuple[dict[str, str], str] | None = None
    cont_meta = ""  # an attribute value running on with " \"
    prev_blank = True
    carry: list[str] = []  # macros' brackets left open on the lines above

    span = Span()
    for at, raw in enumerate(lines):
        line = raw.rstrip()
        kind = stack[-1][1] if stack else ""
        span.later = lambda at=at: "\n".join(paragraph_after(lines, at))
        if table_open is not None:
            if line == stack[-1][0]:
                out.extend(table(table_buf, *table_open, attrs))
                out.append("")
                stack.pop()
                table_buf, table_open = [], None
            else:
                table_buf.append(line)
            continue
        if kind in ("verbatim", "comment"):
            if line == stack[-1][0] or (
                stack[-1][0].startswith("```") and line == "```"
            ):
                stack.pop()
                out.append("")
            else:
                out.append(raw.rstrip() if kind == "verbatim" else "")
            continue
        if cont_meta:
            more = line.rstrip("\\+ ").strip()
            out.append(subst_attrs(more, attrs) if cont_meta == "meta" else "")
            cont_meta = cont_meta if re.search(r"\s[\\+]$", line) else ""
            continue
        if not line.strip():
            out.append("")
            literal, header, prev_blank, carry = False, 0, True, []
            span.opened.clear()
            continue
        if literal:
            out.append(raw.rstrip())
            continue
        was_blank, prev_blank = prev_blank, False
        if line.startswith("//") and not re.fullmatch(r"/{4,}", line):
            out.append("")
            continue
        line, carry = run_on(line, carry)
        m = ATTR_ENTRY.match(line)
        if m:
            name, value = m.group(1), (m.group(2) or "")
            cont = bool(re.search(r"\s[\\+]$", value))
            value = re.sub(r"\s[\\+]$", "", value).strip()
            if name.startswith("!") or name.endswith("!"):
                attrs.pop(name.strip("!").lower(), None)
                out.append("")
                continue
            value = subst_attrs(value, attrs)
            attrs[name.lower()] = value
            is_meta = name.lower() in META and value
            out.append(f"{name}: {value}" if is_meta else "")
            cont_meta = ("meta" if is_meta else "other") if cont else ""
            continue
        if header:  # the author and revision lines under the document title
            header -= 1
            out.append(line)
            if header == 1:
                who = line.split(";")[0]
                attrs.setdefault("author", re.sub(r"\s*<[^>]*>", "", who).strip())
                em = re.search(r"<([^>]+)>", who)
                if em:
                    attrs.setdefault("email", em.group(1))
            else:
                rev = re.match(r"^(?:v?([^,\s]+),\s*)?([^:]*)(?::\s*(.*))?$", line)
                if rev:
                    for key, val in zip(
                        ("revnumber", "revdate", "revremark"), rev.groups()
                    ):
                        if val:
                            attrs.setdefault(key, val.strip())
            continue
        m = DELIM.match(line)
        if m:
            style, positional, named = pending
            pending = ("", [], {})
            if stack and line == stack[-1][0]:
                stack.pop()
                out.append("")
                continue
            c = line[0]
            if c in "|!,:" and line[1:2] == "=":
                stack.append((line, "table"))
                table_open = (named, line)
                out.append("")
                continue
            if (
                c in "-.`+"
                and line != "--"
                or style in ("source", "listing", "literal", "pass")
            ):
                kind = "verbatim"
            elif c == "/" or style == "comment":
                kind = "comment"
            else:
                kind = "prose"
            stack.append((line, kind))
            if style.upper() in ADMONITIONS:
                prefix = style.lower()
            out.append("")
            continue
        m = BLOCK_ATTRS.match(line)
        if m:
            pending = (
                block_attrs(m.group(1) or "") if m.group(1) is not None else pending
            )
            style, positional, _named = pending
            who = ", ".join(p.strip().strip('"') for p in positional[1:3] if p.strip())
            out.append(
                f"— {inline(who, attrs)}" if style in ("quote", "verse") and who else ""
            )
            continue
        if DIRECTIVE.match(line) or BREAK.match(line):
            out.append("")
            continue
        m = BLOCK_MACRO.match(line)
        if m:
            out.append(alt_text(m.group(3)) if m.group(1) == "image" else "")
            continue
        style = pending[0]
        if style in ("source", "listing", "literal") or (
            was_blank
            and raw[:1] in (" ", "\t")
            and not LIST.match(line)
            and not NUMBERED.match(line)
        ):
            pending = ("", [], {})
            literal = True
            out.append(raw.rstrip())
            seen_text = True
            continue
        if style.upper() in ADMONITIONS:
            prefix = style.lower()
        pending = ("", [], {})
        m = SECTION.match(line)
        if m:
            out.append(inline(m.group(2), attrs))
            if not seen_text and m.group(1) == "=":
                header = 2
            seen_text = True
            continue
        seen_text = True
        m = BLOCK_TITLE.match(line)
        if m:
            out.append(inline(m.group(1), attrs))
            continue
        if line.strip() == "+":
            out.append("")
            continue
        m = ADMONITION.match(line)
        if m:
            out.append(f"{m.group(1).lower()}: {inline(m.group(2), attrs)}")
            continue
        m = LIST.match(line)
        if m:
            # a checklist's box stays as written, [ ] or [x]: no word added
            text_line = f"- {inline(m.group(2), attrs, span)}"
        elif NUMBERED.match(line):
            n = NUMBERED.match(line)
            text_line = f"{n.group(1)}. {inline(n.group(2), attrs)}"
        elif DLIST.match(line) and not line.lstrip().startswith(("link:", "image:")):
            d = DLIST.match(line)
            term, rest = (
                inline(d.group(1), attrs, span),
                inline(d.group(3) or "", attrs, span),
            )
            text_line = f"{term}: {rest}" if rest else f"{term}:"
        else:
            text_line = inline(line, attrs, span)
        if prefix and text_line:
            text_line = f"{prefix}: {text_line}"
            prefix = ""
        out.append(text_line)
    if table_open is not None:
        out.extend(table(table_buf, *table_open, attrs))
    result = "\n".join(out)
    return result.rstrip("\n") + "\n" if result.strip() else None


EXTS = (".adoc", ".asciidoc", ".asc")
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: asciidoc.py mirror --from FOLDER --to MIRROR"


def _armor(path: Path) -> bool:
    """An .asc file that is a PGP key, signature or message, not AsciiDoc."""
    if not path.name.lower().endswith(".asc"):
        return False
    try:
        with path.open("rb") as f:
            head = f.read(64)
    except OSError:
        return False  # read again, then skipped and counted
    return head.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"-----BEGIN PGP")


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed; an .asc file
    that is PGP armor is not AsciiDoc and is passed over."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if (
                not name.startswith(".")
                and name.lower().endswith(EXTS)
                and p.is_file()
                and not _armor(p)
            ):
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def places(text: str) -> dict[str, str]:
    """The mirror contract's places (adapters/stdlib/ci/README.md): the
    mirror is line for line, so the line each passage starts on is the
    source's same line."""
    lines = text.splitlines()
    return {str(i): f"line {i}" for i, s in enumerate(lines, 1)
            if s.strip() and (i == 1 or not lines[i - 2].strip())}  # fmt: skip


def write_places(dst: Path, rel: str, found: dict[str, str]) -> None:
    """The map, hidden beside the mirror, where the kernel never reads."""
    out = dst / ".places" / (rel + ".txt.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = {"source": rel, "places": found}
    out.write_bytes((json.dumps(doc, ensure_ascii=False) + "\n").encode("utf-8"))


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
            write_places(dst, rel.as_posix(), places(text))
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
