"""braille.py: answers as a braille-ready file (BRF). Python 3.9+.

    python adapters/stdlib/braille/braille.py --box DIR --to FILE [--cells N] [--lines N]
    python adapters/stdlib/braille/braille.py --from TEXTFILE --to FILE [--cells N] [--lines N]

A braille display or an embosser reads a BRF: plain ASCII in which each
character stands for one braille cell (North American Braille ASCII), laid out
in lines of a fixed number of cells and pages of a fixed number of lines. This
writes one from your approved answers (--box), each with the reason it was
given and the places it cites, or from any text file (--from).

    ,six hours of sun4
    ,why3 the garden notes
    ,from3 garden4md #c

That is uncontracted English braille, grade 1, letter for letter: a capital
letter is ',', a word in capitals ',,', a number is '#' and the digits a to j
(1 is a, 0 is j), a letter a to j straight after a digit is marked ';', and
punctuation is the cell the standard gives it (the period '4', the comma '1',
the question mark '8', parentheses '"<' and '">'). It is not contracted
(grade 2) braille, which is a different and longer table and is best checked by
a braille reader; a person who reads grade 2 will read this slowly but
correctly. Letters with accents, other scripts, and signs the table doesn't
have (such as the currency signs) have no cell: each is replaced by a space and
counted at the end ("12 characters have no braille cell here").

Lines are 40 cells (--cells N) and pages 25 lines (--lines N), words never cut
unless one is longer than a line. Lines end with a carriage return and a line
feed, and a page ends with a form feed, as embossers expect. Each answer starts
on a new paragraph.

An approval is used only while its proof holds under your key (the kernel's
`sealed`, so the key is read there and nowhere here) and its proposal file still
holds the bytes you approved; one that doesn't is left out and said. FILE is
written once, readable only by you, never over a file that exists, and the same
input gives the same bytes. Nothing is sent to a display or an embosser.

Exit codes, the kernel's: 0 written; 42 written, but an approval was left out
and waits on you, or there was nothing to write (no approved answer; nothing
written); 2 refused (a record that doesn't verify, a bad command line).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

DIGITS = "jabcdefghi"  # 0 to 9 are the cells for a to j
PUNCT = {".": "4", ",": "1", ";": "2", ":": "3", "!": "6", "?": "8", "'": "'", "-": "-", "(": '"<', ")": '">', "/": "_/", "&": "@&", "@": "@a",
         "%": ".0", "+": '"6', "=": '"7', "*": '"9', "[": ".<", "]": ".>", "$": "@s", "’": "'", "‘": "'", "–": "-", "—": "--"}  # fmt: skip
WORD = re.compile(r"[A-Za-z0-9]+")


def word_cells(word: str) -> str:
    """A run of letters and digits as cells: capitals, number signs and letter signs."""
    letters = [c for c in word if c.isalpha()]
    whole = len(letters) > 1 and all(c.isupper() for c in letters)
    out, in_number = [",," if whole else ""], False
    for c in word:
        if c.isdigit():
            if not in_number:
                out.append("#")
            in_number = True
            out.append(DIGITS[int(c)])
        else:
            if in_number and c.lower() in "abcdefghij":
                out.append(";")
            in_number = False
            out.append(("," if c.isupper() and not whole else "") + c.lower())
    return "".join(out)


def cells(text: str) -> tuple[str, int]:
    """(the text as cells with its words and spaces, how many characters have no cell)."""
    out, missing, quote_open = [], 0, True
    i = 0
    while i < len(text):
        c = text[i]
        m = WORD.match(text, i)
        if m:
            word = m.group(0)
            out.append(word_cells(word))
            i = m.end()
            # a decimal point or a thousands comma inside a number keeps the number going
            while (
                i + 1 < len(text)
                and text[i] in ".,"
                and text[i + 1].isdigit()
                and word[-1].isdigit()
            ):
                nxt = WORD.match(text, i + 1)
                out.append(
                    ("." if text[i] == "." else "1")
                    + "".join(
                        DIGITS[int(d)] if d.isdigit() else d for d in nxt.group(0)
                    )
                )
                word, i = nxt.group(0), nxt.end()
            continue
        if c.isspace():
            out.append("\n" if c == "\n" else " ")
        elif c in '"“”':
            closing = c == "”" or (c == '"' and not quote_open)
            out.append("0" if closing else "8")
            quote_open = closing if c == '"' else quote_open
        elif c in PUNCT:
            out.append(PUNCT[c])
        else:
            out.append(" ")
            missing += 1
        i += 1
    return "".join(out), missing


def layout(paragraphs: list[str], width: int, height: int) -> str:
    """Paragraphs of cells set in lines of `width` and pages of `height`, CR LF and form feeds."""
    lines: list[str] = []
    for n, para in enumerate(paragraphs):
        if n:
            lines.append("")
        for block in para.split("\n"):
            cur = ""
            for word in block.split():
                while len(word) > width:
                    if cur:
                        lines.append(cur)
                        cur = ""
                    lines.append(word[:width])
                    word = word[width:]
                if not cur:
                    cur = word
                elif len(cur) + 1 + len(word) <= width:
                    cur += " " + word
                else:
                    lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
    pages = [
        "\r\n".join(lines[i : i + height]) + "\r\n"
        for i in range(0, len(lines), height)
    ]
    return "\f".join(pages)


def answers(box: Path, rows: list[dict]) -> tuple[list[str], int]:
    """(each approved answer as plain text, how many approvals were left out)."""
    where = {}
    for r in rows:
        for s in r.get("served", []):
            where.setdefault(s["id"], s["where"])
    out, left = [], 0
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            left += 1
            continue
        places = ", ".join(where.get(c, c[:12]) for c in prop["cites"])
        out.append(
            f"{prop['data'].strip()}\nWhy: {prop['claim']}"
            + (f"\nFrom: {places}" if places else "")
        )
    return out, left


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from", "--to", "--cells", "--lines"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    width, height = opts.get("--cells", "40"), opts.get("--lines", "25")
    bad = not (
        width.isdigit() and height.isdigit() and int(width) >= 10 and int(height) >= 1
    )
    if (
        not opts.get("--to")
        or args
        or bad
        or bool(opts.get("--box")) == bool(opts.get("--from"))
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    to, left = Path(opts["--to"]), 0
    if opts.get("--box"):
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        rows, breaks = kernel.read(box / "record.jsonl")
        if breaks:
            print("refused:", *breaks, sep="\n  ", file=sys.stderr)
            return kernel.REFUSED
        texts, left = answers(box, rows)
    else:
        src = Path(opts["--from"])
        if not src.is_file():
            print(f"refused: {src} isn't a file", file=sys.stderr)
            return kernel.REFUSED
        try:
            body = src.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            print(f"refused: could not read {src} as text", file=sys.stderr)
            return kernel.REFUSED
        texts = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if left:
        print(
            f"{left} approval{'s' if left != 1 else ''} left out: its proposal file is not what you approved (python kernel.py verify says which)",
            file=sys.stderr,
        )
    if not texts:
        print(
            "Nothing to write: no approved answer."
            if opts.get("--box")
            else "Nothing to write: the file has no text."
        )
        return kernel.ESCALATE
    made = [cells(t) for t in texts]
    text = layout([c for c, _ in made], int(width), int(height))
    missing = sum(m for _, m in made)
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="ascii", newline="") as f:
        f.write(text)
    pages = text.count("\f") + 1
    print(
        f"wrote {to}: {len(texts)} paragraph{'s' if len(texts) != 1 else ''}, {pages} page{'s' if pages != 1 else ''}"
    )
    if missing:
        print(
            f"{missing} character{'s' if missing != 1 else ''} {'has' if missing == 1 else 'have'} no braille cell here and {'was' if missing == 1 else 'were'} left as a space",
            file=sys.stderr,
        )
    return kernel.ESCALATE if left else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
