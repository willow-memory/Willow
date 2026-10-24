"""clauses.py: a long document as one sentence a passage, and what changed.

    python adapters/stdlib/clauses/clauses.py mirror --from FOLDER --to MIRROR
    python adapters/stdlib/clauses/clauses.py diff --old FILE --new FILE [--to FOLDER]

A policy, a contract or a set of terms is read by the kernel a paragraph at
a time, and a paragraph of a policy can hold ten promises. Asked "do they use
my email for ads?", the answer should be the one sentence that says so.

`mirror` writes, for each .txt, .md, .html or .htm under FOLDER,
`MIRROR/<same relative path>.txt` with one sentence a paragraph. A web page
is read as its blocks (paragraphs, headings, list items); the pdf add-on's
mirror (`== page N` headings over lines wrapped at the page's width) is read
as wrapped lines, each `== page N` kept as a paragraph of its own so an
answer still says which page. A heading or a paragraph's last line is a
short line, and ends its block, unless the next line goes on in lower case.
A sentence ends at . ! or ? (a closing quote or bracket may follow) before
a capital, a digit or an opening quote, but not after a short abbreviation
(e.g., Inc., U.S.) or a single initial.

`diff` reads two versions, splits each the same way, and says what changed,
sentence by sentence:

    reworded  old.txt:58 -> new.txt:60   (8 of 9 words kept)
      - We don't show you personalized ads based on your content ...
      + We don't show you personalized ads based on your content ..., unless ...
    added     new.txt:55   For example, Search may process ...
    removed   old.txt:54   ...
    same      312 sentences (4 differ only in spacing or punctuation)

Two sentences are the same when they hold the same words in the same order
(split the kernel's way, case aside). Of what's left, a removed and an
added sentence are paired as reworded when they share at least half their
words, the closest pair first. `--to FOLDER` also writes the new version's
added and reworded sentences, as FOLDER/<the new file's name>, so the
kernel can be asked about only what changed.

The contract every reader shares: hidden files and folders are skipped;
nothing is written inside FOLDER; the same folder gives the same bytes; a
file that isn't UTF-8 text is skipped and counted. Exit codes: mirror, 0
wrote at least one file, 42 nothing to read; diff, 0 the same, 42 something
changed; 2 refused.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

READS = (".txt", ".md", ".html", ".htm")
PAGE = re.compile(r"== page \d+")
SHORT = 0.75  # a line under this share of the file's wide lines ends its block
WIDE = 0.9  # which line is "wide": the 90th in a hundred, by length
SEP = "\0"  # where a block tag stood; splitlines() would cut at \x1c-\x1e
KEEP = 0.5  # the share of words a removed and an added sentence share, to pair
BLOCK = re.compile(
    r"</?(?:p|div|li|ul|ol|h[1-6]|br|tr|td|th|table|section|article|header|"
    r"footer|blockquote|title|main|nav|figure|figcaption|dd|dt|dl|aside|pre|hr)\b[^>]*>",
    re.I,
)
#: words that end in a full stop and don't end a sentence, lower case
ABBREV = {"e.g", "i.e", "etc", "inc", "ltd", "corp", "co", "mr", "mrs", "ms",
          "dr", "st", "vs", "no", "jr", "sr", "u.s", "u.k", "approx", "fig"}  # fmt: skip
STOP = re.compile(r"[.!?:][\"'”’)\]]*$")  # a line that ends a sentence
END = re.compile(r"[.!?][\"'”’)\]]*\s+(?=[A-Z0-9\"'“‘(])")


def blocks_of_html(text: str) -> list[tuple[int, str]]:
    """A page's blocks, each with the line it starts on."""
    text = kernel._HIDDEN.sub(kernel._lines_kept, text)
    text = BLOCK.sub(lambda m: SEP + "\n" * m.group(0).count("\n"), text)
    text = html.unescape(kernel._TAG.sub(kernel._lines_kept, text))
    out, para, start = [], [], 0
    for i, line in enumerate(text.splitlines() + [SEP], 1):
        for k, part in enumerate(line.split(SEP)):
            if k:  # a block's edge
                if para:
                    out.append((start, " ".join(para)))
                para = []
            if part := " ".join(part.split()):
                if not para:
                    start = i
                para.append(part)
        if not line.strip() and para:  # a blank line ends a block too
            out.append((start, " ".join(para)))
            para = []
    return out


def blocks_of_text(text: str, wrapped: bool) -> list[tuple[int, str]]:
    """Paragraphs (and, for wrapped lines, short-line breaks), each with the
    line it starts on; a `== page N` line is a block of its own."""
    lines = text.splitlines()
    wide = 0
    if wrapped:
        sizes = sorted(
            len(s.strip()) for s in lines if s.strip() and not PAGE.fullmatch(s.strip())
        )
        wide = sizes[int(WIDE * (len(sizes) - 1))] if sizes else 0
    out: list[tuple[int, str]] = []
    para: list[str] = []
    start = 0
    held: list[tuple[int, str]] = []  # a page heading met mid-sentence

    def close() -> None:
        nonlocal para
        if para:
            out.append((start, " ".join(para)))
            para = []
        out.extend(held)
        held.clear()

    for i, raw in enumerate(lines, 1):
        line = " ".join(raw.split())
        if not line:
            if not wrapped:
                close()
            continue
        if PAGE.fullmatch(line):
            if para and not STOP.search(para[-1]):
                held.append((i, line))  # the sentence may go on over the page
            else:
                close()
                out.append((i, line))
            continue
        if not para:
            start = i
        para.append(line)
        if wrapped and len(line) < SHORT * wide:
            nxt = next(
                (
                    s.strip()
                    for s in lines[i:]
                    if s.strip() and not PAGE.fullmatch(s.strip())
                ),
                "",
            )
            if not nxt[:1].islower() or STOP.search(line):
                close()
    close()
    return out


def sentences(block: str) -> list[str]:
    """A block cut at each sentence's end."""
    out, last = [], 0
    for m in END.finditer(block):
        before = block[last : m.start()].split()
        word = before[-1].lower().rstrip(".") if before else ""
        if word in ABBREV or (len(word) == 1 and word.isalpha()):
            continue
        out.append(block[last : m.end()].strip())
        last = m.end()
    tail = block[last:].strip()
    return out + ([tail] if tail else [])


def clauses(text: str, name: str) -> list[tuple[int, str]]:
    """Every sentence of a document, each with the line its block starts on."""
    if Path(name).suffix.lower() in (".html", ".htm"):
        blocks = blocks_of_html(text)
    else:
        wrapped = any(PAGE.fullmatch(s.strip()) for s in text.splitlines())
        blocks = blocks_of_text(text, wrapped)
    return [(n, s) for n, b in blocks for s in sentences(b)]


def as_text(found: list[tuple[int, str]]) -> str:
    return "".join(s + "\n\n" for _, s in found).rstrip("\n") + "\n" if found else ""


def inside(a: Path, b: Path) -> bool:
    return a == b or b in a.parents


def read(p: Path) -> str | None:
    try:
        raw = p.read_bytes()
        return None if b"\0" in raw[: kernel.SNIFF] else raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def mirror(src: Path, dst: Path) -> int:
    src, dst = src.resolve(), dst.resolve()
    if not src.is_dir():
        print(f"refused: {src} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if inside(dst, src) or inside(src, dst):
        print("refused: the mirror and the folder can't be inside each other",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    wrote = skipped = 0
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if not p.is_file() or p.suffix.lower() not in READS:
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        text = read(p)
        if text is None:
            skipped += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(as_text(clauses(text, p.name)))
        wrote += 1
    print(f"wrote {wrote} files to {dst}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def key(s: str) -> tuple[str, ...]:
    return tuple(w.lower() for w in kernel.words(s))


def compare(old: list[tuple[int, str]], new: list[tuple[int, str]]) -> dict:
    """What changed between two versions' sentences: same, removed, added and
    reworded (a removed and an added sentence sharing at least KEEP of their
    words, the closest first)."""
    left: dict[tuple, list] = {}
    for c in old:
        left.setdefault(key(c[1]), []).append(c)
    same = spacing = 0
    added = []
    for c in new:
        k = key(c[1])
        if left.get(k):
            o = left[k].pop(0)
            same += 1
            spacing += o[1] != c[1]
        else:
            added.append(c)
    removed = sorted((c for cs in left.values() for c in cs), key=lambda c: c[0])
    pairs = []
    for i, o in enumerate(removed):
        ow = set(key(o[1]))
        for j, a in enumerate(added):
            aw = set(key(a[1]))
            kept = len(ow & aw)
            share = kept / max(len(ow | aw), 1)
            if ow and aw and share >= KEEP:
                pairs.append((-share, o[0], a[0], i, j, kept, len(ow | aw)))
    reworded, used_o, used_a = [], set(), set()
    for _, _, _, i, j, kept, of in sorted(pairs):
        if i not in used_o and j not in used_a:
            used_o.add(i)
            used_a.add(j)
            reworded.append((removed[i], added[j], kept, of))
    return {
        "same": same,
        "spacing": spacing,
        "reworded": sorted(reworded, key=lambda r: (r[1][0], r[0][0])),
        "added": [a for j, a in enumerate(added) if j not in used_a],
        "removed": [o for i, o in enumerate(removed) if i not in used_o],
    }


def diff(old: Path, new: Path, to: Path | None) -> int:
    texts = []
    for p in (old, new):
        if not p.is_file() or (t := read(p)) is None:
            print(f"refused: {p} is not a text file", file=sys.stderr)
            return kernel.REFUSED
        texts.append(t)
    if to is not None and (inside(to.resolve(), old.resolve().parent)
                           or inside(to.resolve(), new.resolve().parent)):  # fmt: skip
        print("refused: --to can't be beside or inside the versions", file=sys.stderr)
        return kernel.REFUSED
    got = compare(clauses(texts[0], old.name), clauses(texts[1], new.name))
    for o, a, kept, of in got["reworded"]:
        print(
            f"reworded  {old.name}:{o[0]} -> {new.name}:{a[0]}   ({kept} of {of} words kept)"
        )
        print(f"  - {o[1]}\n  + {a[1]}")
    for a in got["added"]:
        print(f"added     {new.name}:{a[0]}   {a[1]}")
    for o in got["removed"]:
        print(f"removed   {old.name}:{o[0]}   {o[1]}")
    print(f"same      {got['same']} sentences ({got['spacing']} differ only in "
          "spacing or punctuation)")  # fmt: skip
    changed = [a for _, a, _, _ in got["reworded"]] + got["added"]
    if to is not None:
        to.mkdir(parents=True, exist_ok=True)
        with open(to / new.name, "w", encoding="utf-8", newline="\n") as f:
            f.write(as_text(sorted(changed)))
    return kernel.ESCALATE if changed or got["removed"] else kernel.ALIVE


def main(argv: list[str]) -> int:
    if (
        len(argv) == 5
        and argv[0] == "mirror"
        and argv[1] == "--from"
        and argv[3] == "--to"
    ):
        return mirror(Path(argv[2]), Path(argv[4]))
    if (
        len(argv) in (5, 7)
        and argv[0] == "diff"
        and argv[1] == "--old"
        and argv[3] == "--new"
    ):
        if len(argv) == 5 or argv[5] == "--to":
            return diff(
                Path(argv[2]), Path(argv[4]), Path(argv[6]) if len(argv) == 7 else None
            )
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
