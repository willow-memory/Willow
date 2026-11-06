"""deep_links.py: each answer as a link that opens the file at the line. Python 3.9+.

    python adapters/stdlib/deep-links/deep_links.py --box DIR [--base URL] [--from FOLDER]
    python adapters/stdlib/deep-links/deep_links.py --box DIR [--base URL] [--from FOLDER] "your question"

An answer that says "garden.md, line 3" makes you find the file. This gives a
link to click instead, in the two forms a file can be pointed at:

    Six hours of sun.
      garden.md:3   file:///home/ana/notes/garden.md#line=2,3
                    https://example.org/notes/garden.md#:~:text=Tomatoes%20want%20six%20hours

- `file://` with an RFC 5147 fragment, `#line=2,3`: the lines of a plain-text
  file, counted from zero as that standard counts them, so a passage on lines
  3 and 4 is `line=2,4`. A viewer that understands it goes to the lines.
- with --base URL, the address the files are published under, a web link with a
  text fragment, `#:~:text=START` or `#:~:text=START,END`: a browser that
  supports it scrolls to and marks the words. START and END are the first and
  last few words of the passage's first line, percent-encoded as the
  standard asks (the comma, hyphen and ampersand too).

When the box's pile is a reader's mirror that keeps the mirror contract
(adapters/stdlib/ci/README.md), a passage is in its mirror file, and the map
beside it says where it came from: its tag says so too,
`notes/g.md.txt:3 (notes/g.md, line 3)`. With --from FOLDER, the folder the
mirror was made from, the links go to the original instead: a line place at
its lines, a named one (`cell 4`) to the file, and a web link to the
original's path. A passage of a mirror file with no map is linked as before.

With no question, it is each answer you approved: the answer, then a link for
every passage it cites. With a question, it is the passages your folder holds
for it, ranked the kernel's way, each with its links. Asking this way writes
nothing, not even a record row.

An approval is listed only while its proof holds under your key (the kernel's
`sealed`, so the key is read there and nowhere here) and its proposal file still
holds the bytes you approved. A cited passage no longer in your files has no
link and is said. Nothing is opened, served or sent.

Exit codes, the kernel's: 0 links given; 42 nothing to link (no approved answer,
or no passage holds the question), or an approval or citation left out; 2
refused (a record that doesn't verify, a bad command line).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

WORDS = 4  # words of a passage's first line a text fragment starts and ends with


def encode(text: str) -> str:
    """Text as a text fragment writes it: percent-encoded, with `-`, `,` and `&` too."""
    return quote(text, safe="").replace("-", "%2D")


def lines_fragment(passage: dict) -> str:
    start = passage["line"] - 1
    return f"line={start},{start + passage['text'].count(chr(10)) + 1}"


def text_fragment(passage: dict) -> str:
    first = next((x for x in passage["text"].splitlines() if x.strip()), "").split()
    if len(first) <= 2 * WORDS:
        return ":~:text=" + encode(" ".join(first))
    return (
        ":~:text="
        + encode(" ".join(first[:WORDS]))
        + ","
        + encode(" ".join(first[-WORDS:]))
    )


PLACE = re.compile(r"line (\d+)|lines (\d+)-(\d+)")


def place_of(passage: dict, pile: Path, maps: dict) -> tuple[str, str] | None:
    """(the source's path, the passage's place in it), from the mirror
    contract's map beside its mirror file: the last place at or before its
    line. None when the file has no map that reads."""
    path = passage["path"]
    if path not in maps:
        try:
            doc = json.loads(
                (pile / ".places" / (path + ".json")).read_text(encoding="utf-8")
            )
            ok = isinstance(doc, dict) and isinstance(doc.get("source"), str)
            ok = ok and isinstance(doc.get("places"), dict)
            maps[path] = doc if ok else None
        except (OSError, ValueError):
            maps[path] = None
    doc = maps[path]
    if doc is None:
        return None
    at = [int(k) for k in doc["places"] if k.isdigit() and int(k) <= passage["line"]]
    return (doc["source"], str(doc["places"][str(max(at))])) if at else None


def links(passage: dict, pile: Path, base: str | None, origin: Path | None = None,
          placed: tuple[str, str] | None = None) -> list[str]:  # fmt: skip
    if origin is not None and placed is not None:
        source, place = placed
        m = PLACE.fullmatch(place)
        if m:  # the original's lines: a line place for each line of the passage
            a = int(m[1] or m[2])
            b = int(m[3]) if m[3] else a + passage["text"].count(chr(10))
            frag = f"#line={a - 1},{b}"
        else:  # a named place, `cell 4`, has no fragment a viewer reads
            frag = ""
        out = [f"{(origin / source).resolve().as_uri()}{frag}"]
        if base:
            out.append(f"{base.rstrip('/')}/{quote(source)}#{text_fragment(passage)}")
        return out
    out = [f"{(pile / passage['path']).resolve().as_uri()}#{lines_fragment(passage)}"]
    if base:
        out.append(
            f"{base.rstrip('/')}/{quote(passage['path'])}#{text_fragment(passage)}"
        )
    return out


def show(passage: dict, pile: Path, base: str | None, origin: Path | None = None,
         maps: dict | None = None) -> list[str]:  # fmt: skip
    tag = f"{passage['path']}:{passage['line']}"
    placed = place_of(passage, pile, {} if maps is None else maps)
    if placed is not None:
        tag += f" ({placed[0]}, {placed[1]})"
    got = links(passage, pile, base, origin, placed)
    return [f"  {tag}   {got[0]}"] + [f"  {' ' * len(tag)}   {x}" for x in got[1:]]


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--base", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    base = opts.get("--base")
    if (
        not opts.get("--box")
        or len(args) > 1
        or (args and args[0].startswith("--"))
        or ("--base" in opts and not (base or "").startswith(("http://", "https://")))
        or ("--from" in opts and not opts["--from"])
    ):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    origin = Path(opts["--from"]) if "--from" in opts else None
    if origin is not None and not origin.is_dir():
        print(f"refused: --from {origin} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    cfg = kernel.config(box)
    pile_dir = Path(cfg["pile"])
    maps: dict = {}
    pile = kernel.chunks(pile_dir)
    by_id = {c["id"]: c for c in pile}
    if args:
        alias: dict = {}
        if "words" in cfg:
            alias, _, why = kernel.read_words(Path(cfg["words"]), box)
            if why is not None:
                print(f"refused: {why}", file=sys.stderr)
                return kernel.REFUSED
        found = kernel.rank(pile, args[0], alias or {})
        for c in found:
            print(" ".join(c["text"].split())[:100])
            print("\n".join(show(c, pile_dir, base, origin, maps)))
        if not found:
            print("No passage holds that, so there is nothing to link.")
        return kernel.ALIVE if found else kernel.ESCALATE
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    printed, left, gone = 0, 0, 0
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            left += 1
            continue
        print(" ".join(prop["data"].split())[:100])
        for cite in prop["cites"]:
            if cite in by_id:
                print("\n".join(show(by_id[cite], pile_dir, base, origin, maps)))
            else:
                gone += 1
        printed += 1
    if not printed:
        print("No approved answer to link.")
    if left:
        print(
            f"{left} approval{'s' if left != 1 else ''} left out: its proposal file is not what you approved (python kernel.py verify says which)",
            file=sys.stderr,
        )
    if gone:
        print(
            f"{gone} cited passage{'s' if gone != 1 else ''} no longer in your files, so without a link",
            file=sys.stderr,
        )
    return kernel.ALIVE if printed and not left and not gone else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
