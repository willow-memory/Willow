"""opml.py: OPML files, feed lists and outlines, as plain lines. Python 3.9+.

    python adapters/stdlib/opml/opml.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .opml files, and .xml files whose root is <opml> (hidden
folders and files skipped), and writes each as lines a person would read.
Only the file's own words are written: no label of this reader's sits in
passage after passage, since a word in every passage would answer a question
about something the file doesn't hold.

The head's title, dates and owner come first, as written, in a passage of
their own:

    Garden notebook
    Mon, 02 Mar 2026 09:14:00 GMT

A feed or podcast list (outlines with an xmlUrl, as feed readers and podcast
apps export them) is one line per feed: its title, its feed's address and its
site's. Each folder is a passage that starts with the folder's name:

    Gardening
    Hedgerow Diaries <https://example.org/feed.xml> <https://example.org/>

Episodes kept under a podcast (an Overcast export) are a line each under it,
with their date as written and their audio's address; a podcast with episodes
is a passage of its own, not headed by its folder, and one too long for a
passage is cut, each piece starting again with the podcast's line.

An outline (OmniOutliner, Workflowy, Dynalist, Logseq, Bike) is each item on its
own line, indented by depth with "- ", and its note under it. An item's created
date follows it in brackets, as written; a completed item is ticked, "✓", a
mark that is no word, so a list of done items doesn't answer "done". A
top-level item with children is a passage of its own, set apart by blank lines.
One too long for a passage of the kernel's (MAX_CHUNK characters) is cut at its
children, which keep their indent. A cut piece doesn't repeat the items above
it: an export of one item holding everything would put that item's words in
every passage, and so answer a question about something the file doesn't hold.

    - Garden plans
      - Spring beds
        - Tomatoes (Sun, 01 Mar 2026 10:00:00 GMT)
          Sungold and San Marzano, against the south fence.

A file that declares a DTD or entities is never parsed: it is skipped and
counted, so an entity bomb is never expanded.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with nothing to say, or that cannot be read, is
skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import html
import os
import re
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

LIMIT = kernel.MAX_CHUNK  # characters in one passage, as the kernel counts them
WRAP = 200  # a long note is wrapped at words, so the kernel never cuts a line short
HEAD = ("title", "dateCreated", "dateModified", "ownerName")
DECLARES = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)", re.I)
ROOT = re.compile(r"<opml[\s>/]")
INLINE = re.compile(r"</?(?:b|i|u|s|em|strong|span|code|mark|a|br)\b[^<>]*>", re.I)
DONE = (("_complete", "true"), ("checked", "true"), ("_status", "checked"))
TICK = "✓"  # a completed item's mark: no letters, so the kernel reads no word in it


class Declares(ValueError):
    """The file declares a DTD or entities; it is never parsed."""


def _text(data: bytes) -> str:
    """The file as text, enough to look for a declaration or the root."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "replace")
    return data.decode("latin-1")


def _tag(el: ET.Element) -> str:
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def _kids(el: ET.Element) -> list[ET.Element]:
    return [c for c in el if _tag(c) == "outline"]


def _one(value: str | None) -> str:
    """An attribute as one line: inline markup taken off, spaces joined."""
    return " ".join(html.unescape(INLINE.sub("", value or "")).split())


def _name(el: ET.Element) -> str:
    return _one(el.get("text")) or _one(el.get("title"))


def _wrap(text: str, indent: str) -> list[str]:
    return textwrap.wrap(
        text,
        WRAP,
        initial_indent=indent,
        subsequent_indent=indent,
        break_on_hyphens=False,
    )


def _item(el: ET.Element, depth: int) -> list[str]:
    """One outline item's own line, without its note, wrapped at its indent."""
    done = any((el.get(k) or "").lower() == v for k, v in DONE)
    line = "- " + (f"{TICK} " if done else "") + _name(el)
    if el.get("type") == "link" and el.get("url"):
        line += f" <{_one(el.get('url'))}>"
    if el.get("created"):
        line += f" ({_one(el.get('created'))})"
    return _wrap(line, "  " * depth)


def _lines(el: ET.Element, depth: int) -> list[str]:
    """An item's line and its note under it; blank note lines are dropped,
    since a blank line ends a passage."""
    out = _item(el, depth)
    for para in (el.get("_note") or "").splitlines():
        out += _wrap(_one(para), "  " * (depth + 1))
    return out


def _tree(el: ET.Element, depth: int) -> list[str]:
    out = _lines(el, depth) if (_name(el) or el.get("_note") or _kids(el)) else []
    for c in _kids(el):
        out += _tree(c, depth + 1)
    return out


def _size(lines: list[str]) -> int:
    return sum(len(x) + 1 for x in lines)


def _branch(el: ET.Element, depth: int) -> list[list[str]]:
    """The passages of one item and what is under it. It fits, or it is cut at
    its children: those that fit together stay together, and one with
    children of its own that doesn't fit is cut the same way."""
    whole = _tree(el, depth)
    if _size(whole) <= LIMIT or not _kids(el):
        return [whole]
    passages: list[list[str]] = []
    current = _lines(el, depth)
    for c in _kids(el):
        piece = _tree(c, depth + 1)
        if _size(current + piece) <= LIMIT:
            current += piece
            continue
        if current:
            passages.append(current)
        if _kids(c):
            passages += _branch(c, depth + 1)
            current = []
        else:
            current = piece
    if current:
        passages.append(current)
    return passages


def _packed(top: list[str], lines: list[str]) -> list[list[str]]:
    """`lines` in passages that fit, each starting with `top`."""
    passages, current = [], list(top)
    for line in lines:
        if len(current) > len(top) and _size(current + [line]) > LIMIT:
            passages.append(current)
            current = list(top)
        current.append(line)
    return [*passages, current]


def _feed(el: ET.Element) -> tuple[list[str], list[str]]:
    """A feed's own lines (title, addresses, description) and its episodes'."""
    line = " ".join(
        x
        for x in (
            _name(el),
            f"<{_one(el.get('xmlUrl'))}>",
            f"<{_one(el.get('htmlUrl'))}>" if el.get("htmlUrl") else "",
        )
        if x
    )
    own = [line, *_wrap(_one(el.get("description")), "  ")]
    episodes = []
    for ep in _kids(el):
        url = ep.get("enclosureUrl") or ep.get("url")
        bits = (
            _name(ep),
            f"({_one(ep.get('pubDate'))})" if ep.get("pubDate") else "",
            f"<{_one(url)}>" if url else "",
        )
        episodes += _wrap(" ".join(x for x in bits if x), "  ")
    return own, episodes


def _feeds(els: list[ET.Element], folders: list[str]) -> list[list[str]]:
    """A feed list's passages: one for each folder, headed by its name, and
    one for each feed that holds episodes, headed by the feed."""
    top = [" / ".join(folders)] if folders else []
    passages: list[list[str]] = []
    run = list(top)
    for el in els:
        if el.get("xmlUrl"):
            own, episodes = _feed(el)
            if episodes:
                passages.append(run)
                # not headed by its folder: an export that keeps episodes keeps
                # them for every podcast, all in one folder ("feeds"), whose
                # name would then be in every passage
                passages += _packed(own, episodes)
                run = list(top)
            else:
                run += own
        elif _kids(el):
            passages.append(run)
            passages += _feeds(_kids(el), [*folders, _name(el)])
            run = list(top)
        else:
            run += _tree(el, 0)
    return [p for p in [*passages, run] if len(p) > len(top)]


def _is_feed_list(body: ET.Element) -> bool:
    """More feeds than plain items with nothing under them, outside a feed."""
    feeds = items = 0
    stack = _kids(body)
    while stack:
        el = stack.pop()
        if el.get("xmlUrl"):
            feeds += 1
        elif _kids(el):
            stack += _kids(el)
        else:
            items += 1
    return feeds > 0 and feeds >= items


def convert(data: bytes) -> str | None:
    if DECLARES.search(_text(data)):
        raise Declares("declares a DTD or entities")
    root = ET.fromstring(data)
    if _tag(root) != "opml":
        return None
    head = next((c for c in root if _tag(c) == "head"), None)
    body = next((c for c in root if _tag(c) == "body"), None)
    passages: list[list[str]] = []
    if body is not None and _is_feed_list(body):
        passages += _feeds(_kids(body), [])
    elif body is not None:
        run: list[str] = []
        for el in _kids(body):
            if _kids(el):
                passages += [run, *_branch(el, 0)]
                run = []
            else:
                run += _tree(el, 0)
        passages.append(run)
    kept = ["\n".join(p) for p in passages if p]
    if not kept:
        return None
    if head is not None:
        found = {_tag(c): _one(c.text) for c in head}
        top = [found[k] for k in HEAD if found.get(k)]
        if top:
            kept.insert(0, "\n".join(top))
    return "\n\n".join(kept) + "\n"


EXTS = (".opml", ".xml")
ERRORS = (OSError, UnicodeDecodeError, ValueError, ET.ParseError)

USAGE = "usage: opml.py mirror --from FOLDER --to MIRROR"


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


def _ours(path: Path, data: bytes) -> bool:
    """An .opml file always; an .xml file only when it holds an <opml> root."""
    return path.name.lower().endswith(".opml") or bool(ROOT.search(_text(data)))


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            data = path.read_bytes()
            if not _ours(path, data):
                continue
            text = convert(data)
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except Declares:
            print(
                f"skipped {rel.as_posix()}: it declares a DTD or entities, "
                "which opml.py never reads",
                file=sys.stderr,
            )
            skipped += 1
            continue
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
