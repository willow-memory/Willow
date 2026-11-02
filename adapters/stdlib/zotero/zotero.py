"""zotero.py: your Zotero library, from a copy of zotero.sqlite. Python 3.9+.

    python adapters/stdlib/zotero/zotero.py mirror --from FOLDER --to MIRROR

Walks FOLDER for `.sqlite` files that hold Zotero's tables (items, itemData,
itemDataValues, fields, itemTypes, creators, itemCreators, creatorTypes,
itemNotes, deletedItems), the library Zotero 6 and 7 keep, or a copy of it.
Any other .sqlite file is skipped and counted. Each item, note and PDF
annotation becomes one passage that begins with the item's citation, so a
question about a paper, a note or a highlight finds which paper it was:

    Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides.
    journal article, added 2021-03-04 10:22 UTC
    date: March 2020
    creators: Ada Example (author); Cy Sample (author); Bo Lee (author)
    doi: 10.1000/xyz123
    tags: tides, estuaries
    collections: Thesis / Chapter 2

    Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides, p. 12:
    "the tide turns twice a day" — check this against Lee
    highlight, yellow, made 2023-05-01 09:00 UTC

Only regular items are passages (not attachments, notes or annotations as
items), and nothing in the trash. A year is read from the item's date field
alone, never guessed: an item without one is "(n.d.)". A note's HTML is read
as the words it shows; a standalone note starts with "note:". An ink or image
annotation with no text is left out and counted on the last line. Times are
Zotero's own, in UTC. A long note or abstract is cut into passages that each
start with the citation again.

The file is opened read-only and immutable, so SQLite writes no journal
beside it and FOLDER is unchanged. Each library is written to MIRROR at the
same relative path with `.txt` added.

    wrote 1 files to MIRROR; skipped 0

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
import textwrap
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: zotero.py mirror --from FOLDER --to MIRROR"

#: the tables that make a file a Zotero library
TABLES = {"items", "itemData", "itemDataValues", "fields", "itemTypes", "creators",
          "itemCreators", "creatorTypes", "itemNotes", "deletedItems"}  # fmt: skip
#: item types that are not references of their own
NOT_ITEMS = ("attachment", "note", "annotation")
TITLE = ("title", "caseName", "nameOfAct", "subject")
#: where it appeared, the first one an item has
PUBLISHED = ("publicationTitle", "bookTitle", "proceedingsTitle", "websiteTitle", "blogTitle",
             "forumTitle", "encyclopediaTitle", "dictionaryTitle", "programTitle", "conferenceName",
             "publisher", "university", "institution", "repository", "company", "label", "studio",
             "network", "distributor", "court", "reporter", "code")  # fmt: skip
SHOWN = (("volume", "volume"), ("issue", "issue"), ("pages", "pages"), ("place", "place"),
         ("ISBN", "isbn"), ("ISSN", "issn"), ("DOI", "doi"), ("url", "url"))  # fmt: skip
#: Zotero's annotation types, and its eight colours
KINDS = {1: "highlight", 2: "note", 3: "image", 4: "ink", 5: "underline", 6: "text"}
COLOURS = {"#ffd400": "yellow", "#ff6666": "red", "#5fb236": "green", "#2ea8e5": "blue",
           "#a28ae5": "purple", "#e56eee": "magenta", "#f19837": "orange", "#aaaaaa": "gray"}  # fmt: skip
SQLDATE = re.compile(r"(\d{4})-\d\d-\d\d(?: (.*))?$", re.S)
BLOCK = re.compile(r"<(?:br|/p|/h[1-6]|/li|/div|/blockquote|/pre|/tr)\b[^>]*>", re.I)
INLINE = re.compile(r"</?(?:b|i|u|s|em|strong|span|a|sub|sup|code|mark)\b[^>]*>", re.I)
ROOM = kernel.MAX_CHUNK - 1  # a passage, its newlines counted, stays one chunk
WIDTH = 160  # a line is wrapped here, so the kernel never cuts one short
HEAD = 240  # a citation longer than this is cut, with an ellipsis
CITED = 5  # names in a citation before "et al."; every name is on "creators:"


def one(value) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def words_of(type_name: str) -> str:
    """journalArticle -> journal article."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", type_name).lower()


def stamp(value) -> str:
    """Zotero's 'YYYY-MM-DD HH:MM:SS' (UTC) to the minute, else as written."""
    text = one(value)
    return (
        f"{text[:16]} UTC"
        if re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", text)
        else text
    )


def year_of(date: str) -> tuple[str, str]:
    """The year and the date as written, from Zotero's date field, which it
    keeps as an SQL date and the original ('2020-03-00 March 2020'). No year
    there is no year: never one guessed from anything else."""
    m = SQLDATE.match(date)
    if not m:
        return "n.d.", one(date)
    year = m.group(1) if m.group(1) != "0000" else "n.d."
    return year, one(m.group(2)) or (year if year != "n.d." else "")


def wrap(line: str) -> list[str]:
    return textwrap.wrap(line, WIDTH, break_on_hyphens=False) or []


def pack(head: str, lines: list[str]) -> list[str]:
    """`head`, then as many of `lines` as fit in one chunk, again and again,
    each passage starting with `head`, so none loses whose it is."""
    if len(head) > HEAD:
        head = head[: HEAD - 1].rstrip() + "…"
    body = [w for line in lines for w in wrap(line)]
    out, cur = [], head
    for line in body:
        if len(cur) + 1 + len(line) > ROOM and cur != head:
            out.append(cur)
            cur = head
        cur += "\n" + line
    out.append(cur)
    return out


def note_lines(html: str) -> list[str]:
    """A note's HTML as the lines it shows (`kernel.html_text`)."""
    html = INLINE.sub("", BLOCK.sub(lambda m: m.group(0) + "\n", html or ""))
    text = kernel.html_text(html)  # an inline tag is not a word break: chapter<b>2</b>
    return [one(x) for x in text.splitlines() if one(x)]


def is_library(con: sqlite3.Connection) -> bool:
    names = {
        r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    return TABLES <= names


def _table(con: sqlite3.Connection, name: str) -> bool:
    return bool(
        con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
    )


def _names(con, plain: str, combined: str, cols: str) -> dict[int, str]:
    """An id-to-name table, from Zotero's combined copy where it is filled."""
    for name in (combined, plain):
        if _table(con, name):
            got = {i: one(n) for i, n in con.execute(f"SELECT {cols} FROM {name}")}
            if got:
                return got
    return {}


class Library:
    """Everything one zotero.sqlite says, read once."""

    def __init__(self, con: sqlite3.Connection):
        types = _names(con, "itemTypes", "itemTypesCombined", "itemTypeID, typeName")
        fields = _names(con, "fields", "fieldsCombined", "fieldID, fieldName")
        self.deleted = {r[0] for r in con.execute("SELECT itemID FROM deletedItems")}
        if _table(con, "feedItems"):  # an RSS feed's items are not the library's
            self.deleted |= {r[0] for r in con.execute("SELECT itemID FROM feedItems")}
        self.items = {i: (types.get(t, ""), stamp(a)) for i, t, a in
                      con.execute("SELECT itemID, itemTypeID, dateAdded FROM items")}  # fmt: skip
        self.data: dict[int, dict[str, str]] = {}
        for i, f, v in con.execute(
            "SELECT d.itemID, d.fieldID, v.value FROM itemData d "
            "JOIN itemDataValues v ON v.valueID = d.valueID"
        ):
            self.data.setdefault(i, {})[fields.get(f, "")] = "" if v is None else str(v)
        self.creators: dict[int, list[tuple[str, str, str]]] = {}
        for i, first, last, mode, role in con.execute(
            "SELECT ic.itemID, c.firstName, c.lastName, c.fieldMode, t.creatorType "
            "FROM itemCreators ic JOIN creators c ON c.creatorID = ic.creatorID "
            "LEFT JOIN creatorTypes t ON t.creatorTypeID = ic.creatorTypeID "
            "ORDER BY ic.itemID, ic.orderIndex"
        ):
            last, first = one(last), one(first)
            short = last or first
            full = last if mode == 1 else one(f"{first} {last}")
            self.creators.setdefault(i, []).append((short, full, one(role) or "author"))
        self.tags: dict[int, list[str]] = {}
        if _table(con, "tags") and _table(con, "itemTags"):
            for i, name in con.execute(
                "SELECT it.itemID, t.name FROM itemTags it JOIN tags t ON t.tagID = it.tagID ORDER BY it.itemID, t.name"
            ):
                self.tags.setdefault(i, []).append(one(name))
        self.collections: dict[int, list[str]] = {}
        if _table(con, "collections") and _table(con, "collectionItems"):
            self._collections(con)
        self.notes = [
            (i, p, html) for i, p, html in con.execute("SELECT itemID, parentItemID, note FROM itemNotes ORDER BY itemID")
            if self.items.get(i, ("",))[0] == "note"
        ]  # fmt: skip
        self.attachments: dict[int, int | None] = {}
        if _table(con, "itemAttachments"):
            self.attachments = dict(
                con.execute("SELECT itemID, parentItemID FROM itemAttachments")
            )
        self.annotations: list[tuple] = []
        if _table(con, "itemAnnotations"):
            self.annotations = con.execute(
                "SELECT itemID, parentItemID, type, text, comment, color, pageLabel, sortIndex "
                "FROM itemAnnotations ORDER BY parentItemID, sortIndex, itemID"
            ).fetchall()

    def _collections(self, con: sqlite3.Connection) -> None:
        rows = {c: (one(n), p) for c, n, p in con.execute(
            "SELECT collectionID, collectionName, parentCollectionID FROM collections")}  # fmt: skip
        gone = set()
        if _table(con, "deletedCollections"):
            gone = {
                r[0] for r in con.execute("SELECT collectionID FROM deletedCollections")
            }

        def path(c: int, seen: tuple = ()) -> str | None:
            if c in gone or c in seen or c not in rows:
                return None
            name, parent = rows[c]
            if parent is None:
                return name
            above = path(parent, seen + (c,))
            return None if above is None else f"{above} / {name}"

        for c, i in con.execute("SELECT collectionID, itemID FROM collectionItems"):
            where = path(c)
            if where is not None:
                self.collections.setdefault(i, []).append(where)

    def gone(self, i) -> bool:
        return i is None or i in self.deleted or i not in self.items

    def regular(self, i) -> bool:
        return not self.gone(i) and self.items[i][0] not in NOT_ITEMS

    def citation(self, i: int) -> str:
        """Author, Author & Author (Year). Title. Publication."""
        data = self.data.get(i, {})
        people = self.creators.get(i, [])
        role = (
            "author"
            if any(r == "author" for *_, r in people)
            else (people[0][2] if people else "")
        )
        names = [s for s, _, r in people if r == role and s]
        if len(names) > CITED:
            who = ", ".join(names[:CITED]) + " et al."
        else:
            who = " & ".join(
                x for x in (", ".join(names[:-1]), names[-1] if names else "") if x
            )
        year, _ = year_of(data.get("date", ""))
        title = next((one(data[f]) for f in TITLE if one(data.get(f))), "(untitled)")
        pub = next((one(data[f]) for f in PUBLISHED if one(data.get(f))), "")
        parts = [f"{who} ({year})" if who else f"{title} ({year})"]
        if who:
            parts.append(title)
        if pub:
            parts.append(pub)
        return " ".join(p if p[-1] in ".?!" else p + "." for p in parts)

    def item(self, i: int) -> list[str]:
        data = self.data.get(i, {})
        kind, added = self.items[i]
        lines = [f"{words_of(kind)}, added {added}"]
        written = year_of(data.get("date", ""))[1]
        lines.append(f"date: {written}" if written else "date: none")
        people = self.creators.get(i, [])
        if people:
            lines.append("creators: " + "; ".join(f"{f} ({r})" for _, f, r in people))
        lines += [f"{label}: {one(data[f])}" for f, label in SHOWN if one(data.get(f))]
        # the citation names where it appeared; the publisher of a book
        # section, a paper's conference, are said here
        also = [f for f in PUBLISHED if one(data.get(f))][1:]
        lines += [f"{words_of(f)}: {one(data[f])}" for f in also]
        if self.tags.get(i):
            lines.append("tags: " + ", ".join(self.tags[i]))
        if self.collections.get(i):
            lines.append("collections: " + "; ".join(sorted(self.collections[i])))
        cit = self.citation(i)
        out = pack(cit, lines)
        abstract = one(data.get("abstractNote"))
        if abstract:
            out += pack(cit, ["abstract: " + abstract])
        return out

    def note(self, i: int, parent, html: str) -> list[str]:
        head = self.citation(parent) if self.regular(parent) else "note:"
        when = (
            f"note, written {self.items[i][1]}"
            if head != "note:"
            else f"written {self.items[i][1]}"
        )
        tags = [f"tags: {', '.join(self.tags[i])}"] if self.tags.get(i) else []
        return pack(head, [when, *tags, *(note_lines(html) or ["(empty)"])])

    def annotation(self, row: tuple, owner) -> list[str]:
        i, _, kind, text, comment, color, page, _ = row
        if owner is not None:
            head = self.citation(owner).removesuffix(".")
        else:  # on a PDF that belongs to no item: the PDF's own title
            head = one(self.data.get(row[1], {}).get("title")) or "attachment"
        head += f", p. {one(page)}:" if one(page) else ":"
        text, comment = one(text), one(comment)
        said = " — ".join(
            x for x in (f"\u201c{text}\u201d" if text else "", comment) if x
        )
        what = ", ".join(x for x in (KINDS.get(kind, f"type {kind}"),
                                     COLOURS.get(one(color).lower(), one(color))) if x)  # fmt: skip
        tags = [f"tags: {', '.join(self.tags[i])}"] if self.tags.get(i) else []
        return pack(head, [said, f"{what}, made {self.items[i][1]}", *tags])


def library_text(lib: Library) -> str:
    """The mirror text: each item with its abstract, notes and annotations,
    then the standalone notes, then annotations on PDFs of no item."""
    items = sorted(
        (i for i in lib.items if lib.regular(i)), key=lambda i: (lib.citation(i), i)
    )
    notes: dict = {}
    for i, parent, html in lib.notes:
        if lib.gone(i) or (parent is not None and lib.gone(parent)):
            continue
        notes.setdefault(parent if lib.regular(parent) else None, []).append(
            (i, parent, html)
        )
    marks: dict = {}
    blank: dict[str, int] = {}
    for row in lib.annotations:
        i, pdf = row[0], row[1]
        owner = lib.attachments.get(pdf)
        if lib.gone(i) or lib.gone(pdf) or (owner is not None and lib.gone(owner)):
            continue
        if not one(row[3]) and not one(row[4]):
            kind = KINDS.get(row[2], f"type {row[2]}")
            blank[kind] = blank.get(kind, 0) + 1
            continue
        marks.setdefault(owner if lib.regular(owner) else None, []).append(row)
    passages: list[str] = []
    n_notes = n_marks = 0
    for key in [*items, None]:
        if key is not None:
            passages += lib.item(key)
        for i, parent, html in sorted(
            notes.get(key, []), key=lambda n: (lib.items[n[0]][1], n[0])
        ):
            passages += lib.note(i, parent, html)
            n_notes += 1
        for row in marks.get(key, []):
            passages += lib.annotation(row, key)
            n_marks += 1
    s = lambda n, word: f"{n} {word}{'' if n == 1 else 's'}"  # noqa: E731
    head = f"Zotero library: {s(len(items), 'item')}, {s(n_notes, 'note')}, {s(n_marks, 'annotation')}"
    tail = []
    if blank:
        kinds = ", ".join(f"{n} {k}" for k, n in sorted(blank.items()))
        tail = [
            f"left out: {s(sum(blank.values()), 'annotation')} with no text ({kinds})"
        ]
    return "\n\n".join([head, *passages, *tail]) + "\n"


def library_of(path: Path) -> str | None:
    """The mirror text for a Zotero library, or None if the file isn't one.
    Opened read-only and immutable: no lock, no journal, nothing written."""
    uri = f"file:{quote(path.resolve().as_posix())}?mode=ro&immutable=1"
    try:
        con = sqlite3.connect(uri, uri=True)
    except sqlite3.Error:
        return None
    try:
        if not is_library(con):
            return None
        return library_text(Library(con))
    except sqlite3.Error:
        return None
    finally:
        con.close()


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if (
                not name.startswith(".")
                and name.lower().endswith(".sqlite")
                and p.is_file()
            ):
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
            text = library_of(path)
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except OSError:
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
