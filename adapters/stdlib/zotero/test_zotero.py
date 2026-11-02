"""zotero: a copy of zotero.sqlite as passages, each item, note and PDF
annotation with its citation; the trash left out, a year only from the date
field, the file opened read-only with no journal beside it, other .sqlite
files left alone, the same bytes twice, and MIRROR and FOLDER kept apart.

The library here is built with the table and column names of Zotero's own
schema (resource/schema/userdata.sql, schema 130, as Zotero 7 ships it)."""

from __future__ import annotations

import importlib.util
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "zotero.py"
spec = importlib.util.spec_from_file_location("zotero", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

SCHEMA = """
CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT, templateItemTypeID INT, display INT DEFAULT 1);
CREATE TABLE itemTypesCombined (itemTypeID INT NOT NULL, typeName TEXT NOT NULL, display INT DEFAULT 1 NOT NULL,
    custom INT NOT NULL, PRIMARY KEY (itemTypeID));
CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT, fieldFormatID INT);
CREATE TABLE fieldsCombined (fieldID INT NOT NULL, fieldName TEXT NOT NULL, label TEXT, fieldFormatID INT,
    custom INT NOT NULL, PRIMARY KEY (fieldID));
CREATE TABLE creatorTypes (creatorTypeID INTEGER PRIMARY KEY, creatorType TEXT);
CREATE TABLE items (itemID INTEGER PRIMARY KEY, itemTypeID INT NOT NULL,
    dateAdded TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, dateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    clientDateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, libraryID INT NOT NULL, key TEXT NOT NULL,
    version INT NOT NULL DEFAULT 0, clientVersion INT NOT NULL DEFAULT 0, synced INT NOT NULL DEFAULT 0,
    UNIQUE (libraryID, key));
CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value UNIQUE, valueNormalized TEXT);
CREATE TABLE itemData (itemID INT, fieldID INT, valueID, PRIMARY KEY (itemID, fieldID));
CREATE TABLE itemNotes (itemID INTEGER PRIMARY KEY, parentItemID INT, note TEXT, title TEXT);
CREATE TABLE itemAttachments (itemID INTEGER PRIMARY KEY, parentItemID INT, linkMode INT, contentType TEXT,
    charsetID INT, path TEXT, syncState INT DEFAULT 0, storageModTime INT, storageHash TEXT,
    lastProcessedModificationTime INT, lastRead INT);
CREATE TABLE itemAnnotations (itemID INTEGER PRIMARY KEY, parentItemID INT NOT NULL, type INTEGER NOT NULL,
    authorName TEXT, text TEXT, textNormalized TEXT, comment TEXT, commentNormalized TEXT, color TEXT,
    pageLabel TEXT, sortIndex TEXT NOT NULL, position TEXT NOT NULL, isExternal INT NOT NULL);
CREATE TABLE tags (tagID INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, nameNormalized TEXT);
CREATE TABLE itemTags (itemID INT NOT NULL, tagID INT NOT NULL, type INT NOT NULL, PRIMARY KEY (itemID, tagID));
CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT, fieldMode INT,
    firstNameNormalized TEXT, lastNameNormalized TEXT, UNIQUE (lastName, firstName, fieldMode));
CREATE TABLE itemCreators (itemID INT NOT NULL, creatorID INT NOT NULL, creatorTypeID INT NOT NULL DEFAULT 1,
    orderIndex INT NOT NULL DEFAULT 0, PRIMARY KEY (itemID, creatorID, creatorTypeID, orderIndex),
    UNIQUE (itemID, orderIndex));
CREATE TABLE collections (collectionID INTEGER PRIMARY KEY, collectionName TEXT NOT NULL,
    parentCollectionID INT DEFAULT NULL, clientDateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    libraryID INT NOT NULL, key TEXT NOT NULL, version INT NOT NULL DEFAULT 0, clientVersion INT NOT NULL DEFAULT 0,
    synced INT NOT NULL DEFAULT 0, UNIQUE (libraryID, key));
CREATE TABLE collectionItems (collectionID INT NOT NULL, itemID INT NOT NULL, orderIndex INT NOT NULL DEFAULT 0,
    PRIMARY KEY (collectionID, itemID));
CREATE TABLE deletedCollections (collectionID INTEGER PRIMARY KEY, dateDeleted DEFAULT CURRENT_TIMESTAMP NOT NULL);
CREATE TABLE deletedItems (itemID INTEGER PRIMARY KEY, dateDeleted DEFAULT CURRENT_TIMESTAMP NOT NULL);
CREATE TABLE feedItems (itemID INTEGER PRIMARY KEY, guid TEXT NOT NULL UNIQUE, readTime TIMESTAMP, translatedTime TIMESTAMP);
"""
# Zotero's own ids for these (system ids, the same in every library)
TYPES = {
    1: "annotation",
    2: "artwork",
    3: "attachment",
    7: "book",
    8: "bookSection",
    22: "journalArticle",
    28: "note",
}
FIELDS = {1: "title", 2: "abstractNote", 6: "date", 13: "url", 19: "volume", 20: "issue", 32: "pages",
          38: "publicationTitle", 7: "place", 59: "DOI", 115: "bookTitle", 8: "publisher"}  # fmt: skip
ROLES = {1: "author", 2: "contributor", 3: "editor"}


class Lib:
    """A zotero.sqlite in the making."""

    def __init__(self, path: Path):
        self.path = path
        self.con = sqlite3.connect(path)
        self.con.executescript(SCHEMA)
        for i, t in TYPES.items():
            self.con.execute("INSERT INTO itemTypes VALUES (?, ?, NULL, 1)", (i, t))
            self.con.execute(
                "INSERT INTO itemTypesCombined VALUES (?, ?, 1, 0)", (i, t)
            )
        for i, f in FIELDS.items():
            self.con.execute("INSERT INTO fields VALUES (?, ?, NULL)", (i, f))
            self.con.execute(
                "INSERT INTO fieldsCombined VALUES (?, ?, NULL, NULL, 0)", (i, f)
            )
        for i, r in ROLES.items():
            self.con.execute("INSERT INTO creatorTypes VALUES (?, ?)", (i, r))
        self.next = 1

    def item(self, kind: str, added="2021-03-04 10:22:33", **data) -> int:
        i = self.next
        self.next += 1
        t = next(k for k, v in TYPES.items() if v == kind)
        self.con.execute("INSERT INTO items (itemID, itemTypeID, dateAdded, libraryID, key) VALUES (?, ?, ?, 1, ?)",
                         (i, t, added, f"K{i:07d}"))  # fmt: skip
        for name, value in data.items():
            f = next(k for k, v in FIELDS.items() if v == name)
            self.con.execute(
                "INSERT OR IGNORE INTO itemDataValues (value) VALUES (?)", (value,)
            )
            (v,) = self.con.execute(
                "SELECT valueID FROM itemDataValues WHERE value = ?", (value,)
            ).fetchone()
            self.con.execute("INSERT INTO itemData VALUES (?, ?, ?)", (i, f, v))
        return i

    def creator(
        self,
        item: int,
        order: int,
        last: str,
        first: str = "",
        mode: int = 0,
        role: int = 1,
    ) -> None:
        self.con.execute("INSERT OR IGNORE INTO creators (firstName, lastName, fieldMode) VALUES (?, ?, ?)",
                         (first, last, mode))  # fmt: skip
        (c,) = self.con.execute(
            "SELECT creatorID FROM creators WHERE firstName = ? AND lastName = ? AND fieldMode = ?",
            (first, last, mode),
        ).fetchone()
        self.con.execute(
            "INSERT INTO itemCreators VALUES (?, ?, ?, ?)", (item, c, role, order)
        )

    def note(self, parent: int | None, html: str, added="2023-05-01 09:00:00") -> int:
        i = self.item("note", added)
        self.con.execute(
            "INSERT INTO itemNotes VALUES (?, ?, ?, '')", (i, parent, html)
        )
        return i

    def pdf(self, parent: int | None, **data) -> int:
        i = self.item("attachment", **data)
        self.con.execute(
            "INSERT INTO itemAttachments (itemID, parentItemID, linkMode, contentType, path) "
            "VALUES (?, ?, 0, 'application/pdf', 'storage:paper.pdf')",
            (i, parent),
        )
        return i

    def mark(
        self,
        pdf: int,
        kind: int,
        text=None,
        comment=None,
        page="12",
        color="#ffd400",
        sort="00011|000100|00050",
    ) -> int:
        i = self.item("annotation", "2023-05-02 08:30:00")
        self.con.execute(
            "INSERT INTO itemAnnotations (itemID, parentItemID, type, text, comment, color, pageLabel, sortIndex, "
            "position, isExternal) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}', 0)",
            (i, pdf, kind, text, comment, color, page, sort),
        )
        return i

    def tag(self, item: int, name: str) -> None:
        self.con.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        (t,) = self.con.execute(
            "SELECT tagID FROM tags WHERE name = ?", (name,)
        ).fetchone()
        self.con.execute("INSERT INTO itemTags VALUES (?, ?, 0)", (item, t))

    def collection(self, cid: int, name: str, parent: int | None = None) -> None:
        self.con.execute("INSERT INTO collections (collectionID, collectionName, parentCollectionID, libraryID, key) "
                         "VALUES (?, ?, ?, 1, ?)", (cid, name, parent, f"C{cid:07d}"))  # fmt: skip

    def file(self, cid: int, item: int) -> None:
        self.con.execute("INSERT INTO collectionItems VALUES (?, ?, 0)", (cid, item))

    def trash(self, item: int) -> None:
        self.con.execute("INSERT INTO deletedItems (itemID) VALUES (?)", (item,))

    def done(self) -> Path:
        self.con.commit()
        self.con.close()
        return self.path


def sample(path: Path) -> Path:
    z = Lib(path)
    a = z.item("journalArticle", date="2020-03-00 March 2020", title="Tides of the Estuary",
               publicationTitle="Journal of Tides", DOI="10.1000/xyz123", volume="12", issue="3",
               pages="45-67", abstractNote="We measure the tide at six harbours along the coast.")  # fmt: skip
    z.creator(a, 0, "Example", "Ada")
    z.creator(a, 1, "Sample", "Cy")
    z.creator(a, 2, "Lee", "Bo")
    z.creator(a, 3, "Moss", "Di", role=3)
    z.tag(a, "tides")
    z.tag(a, "estuaries")
    z.collection(1, "Thesis")
    z.collection(2, "Chapter 2", 1)
    z.file(2, a)
    z.note(
        a,
        '<div data-schema-version="9"><p>Read for <b>chapter&nbsp;2</b>.</p><p>Ask Lee about the gauges.</p></div>',
    )
    z.note(None, "<p>Buy a tide table for Brest.</p><p>Ask at the harbour.</p>")
    pdf = z.pdf(a, title="Full Text PDF")
    z.mark(
        pdf,
        1,
        text="the tide turns twice a day",
        comment="check this against Lee",
        page="12",
    )
    z.mark(pdf, 4, page="13", sort="00012|000000|00000")
    z.mark(pdf, 3, page="14", sort="00013|000000|00000")
    b = z.item("book", date="", title="A Book With No Date", publisher="Harbour Press")
    z.creator(b, 0, "Coastal Survey Office", mode=1)
    gone = z.item("journalArticle", date="2019-00-00 2019", title="Thrown Away Paper")
    z.trash(gone)
    return z.done()


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def text_of(tmp_path: Path, build=sample) -> str:
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    build(src / "zotero.sqlite")
    out = tmp_path / "out"
    got = run("mirror", "--from", str(src), "--to", str(out))
    assert got.returncode == 0, got.stderr
    return (out / "zotero.sqlite.txt").read_text(encoding="utf-8")


def passages(text: str) -> list[str]:
    return text.rstrip("\n").split("\n\n")


def test_an_item_is_one_passage_of_its_own_words_and_numbers(tmp_path):
    first = next(p for p in passages(text_of(tmp_path)) if p.startswith("Example"))
    assert first.split("\n") == [
        "Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides.",
        "2021-03-04 10:22",
        "March 2020",
        "Ada Example; Cy Sample; Bo Lee; Di Moss",
        "12(3), 45-67",
        "10.1000/xyz123",
        "estuaries, tides",
        "Thesis / Chapter 2",
    ]


def test_the_abstract_is_its_own_passage_under_the_citation(tmp_path):
    assert (
        "Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides.\n"
        "We measure the tide at six harbours along the coast."
        in passages(text_of(tmp_path))
    )


def test_a_note_is_read_as_the_words_it_shows_under_its_items_citation(tmp_path):
    ps = passages(text_of(tmp_path))
    assert (
        "Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides.\n"
        "2023-05-01 09:00\nRead for chapter 2.\nAsk Lee about the gauges." in ps
    )
    assert "Buy a tide table for Brest.\n2023-05-01 09:00\nAsk at the harbour." in ps


def test_an_annotation_is_quoted_with_its_page_and_comment(tmp_path):
    assert (
        "Example, Sample & Lee (2020). Tides of the Estuary. Journal of Tides, at 12:\n"
        "“the tide turns twice a day” — check this against Lee\n"
        "2023-05-02 08:30" in passages(text_of(tmp_path))
    )


def test_ink_and_image_annotations_with_no_text_are_counted_in_a_passage_of_their_own(
    tmp_path,
):
    text = text_of(tmp_path)
    assert text.endswith("\n\n2 annotations with no text: 1 image, 1 ink\n")
    assert "at 13" not in text and "at 14" not in text
    assert text.startswith("Coastal Survey Office. A Book")


def test_a_single_field_name_and_no_date_never_guess_a_year(tmp_path):
    ps = passages(text_of(tmp_path))
    book = next(p for p in ps if p.startswith("Coastal"))
    assert book.split("\n") == [
        "Coastal Survey Office. A Book With No Date. Harbour Press.",
        "2021-03-04 10:22",
        "Coastal Survey Office",
    ]


def test_the_trash_attachments_notes_and_annotations_are_not_items(tmp_path):
    text = text_of(tmp_path)
    assert "Thrown Away Paper" not in text and "Full Text PDF" not in text
    # two items, an abstract, two notes, one annotation, the count
    assert len(passages(text)) == 7


def test_the_year_is_only_the_date_fields_own():
    assert mod.year_of("2020-03-00 March 2020") == ("2020", "March 2020")
    assert mod.year_of("0000-00-00 Spring, some year") == ("", "Spring, some year")
    assert mod.year_of("circa 1990") == ("", "circa 1990")
    assert mod.year_of("2020-00-00") == ("2020", "2020")
    assert mod.year_of("") == ("", "")


def test_two_names_three_names_and_more_than_five(tmp_path):
    def build(path):
        z = Lib(path)
        two = z.item("journalArticle", date="2001-00-00 2001", title="Two")
        z.creator(two, 0, "Ash", "A")
        z.creator(two, 1, "Birch", "B")
        many = z.item("journalArticle", date="2002-00-00 2002", title="Many")
        for n, name in enumerate(["Cedar", "Dogwood", "Elm", "Fir", "Gum", "Hazel"]):
            z.creator(many, n, name)
        ed = z.item("book", date="2003-00-00 2003", title="Edited")
        z.creator(ed, 0, "Ivy", "I", role=3)
        z.creator(ed, 1, "Juniper", "J", role=3)
        z.creator(ed, 2, "Kale", "K", role=2)
        return z.done()

    ps = passages(text_of(tmp_path, build))
    assert [p.split("\n")[0] for p in ps] == [
        "Ash & Birch (2001). Two.",
        "Cedar, Dogwood, Elm, Fir, Gum et al. (2002). Many.",
        "Ivy & Juniper (2003). Edited.",
    ]
    assert "Cedar; Dogwood; Elm; Fir; Gum; Hazel" in ps[1].split("\n")
    assert "I Ivy; J Juniper; K Kale" in ps[2]


def test_a_trashed_parent_takes_its_notes_and_annotations_with_it(tmp_path):
    def build(path):
        z = Lib(path)
        a = z.item("journalArticle", date="2020-00-00 2020", title="Trashed")
        z.note(a, "<p>orphaned thought</p>")
        z.mark(z.pdf(a), 1, text="orphaned highlight")
        kept = z.item("journalArticle", date="2021-00-00 2021", title="Kept")
        z.trash(z.note(kept, "<p>a trashed note</p>"))
        z.trash(z.mark(z.pdf(kept), 1, text="a trashed highlight"))
        z.mark(z.pdf(None, title="Loose scan"), 2, comment="a loose comment", page="")
        z.trash(a)
        return z.done()

    text = text_of(tmp_path, build)
    assert "orphaned" not in text and "trashed" not in text and "Trashed" not in text
    assert "Loose scan:\na loose comment\n2023-05-02 08:30" in passages(text)
    assert passages(text)[0].startswith("Kept (2021).") and len(passages(text)) == 2


def test_a_trashed_collection_and_its_children_are_not_named(tmp_path):
    def build(path):
        z = Lib(path)
        a = z.item("journalArticle", date="2020-00-00 2020", title="Filed")
        z.collection(1, "Old")
        z.collection(2, "Inside Old", 1)
        z.collection(3, "Reading")
        for c in (2, 3):
            z.file(c, a)
        z.con.execute("INSERT INTO deletedCollections (collectionID) VALUES (1)")
        return z.done()

    text = text_of(tmp_path, build)
    assert passages(text)[0].split("\n")[-1] == "Reading" and "Old" not in text


def test_an_rss_feeds_items_are_not_the_library(tmp_path):
    def build(path):
        z = Lib(path)
        z.item("journalArticle", date="2020-00-00 2020", title="Mine")
        f = z.item("journalArticle", date="2020-00-00 2020", title="From a feed")
        z.con.execute("INSERT INTO feedItems (itemID, guid) VALUES (?, 'g1')", (f,))
        return z.done()

    text = text_of(tmp_path, build)
    assert "Mine" in text and "From a feed" not in text


def test_a_long_note_is_cut_into_passages_that_each_keep_the_citation(tmp_path):
    words = " ".join(f"tide{n}" for n in range(400))

    def build(path):
        z = Lib(path)
        a = z.item("journalArticle", date="2020-00-00 2020", title="Long")
        z.creator(a, 0, "Ash")
        z.note(a, f"<p>{words}</p>")
        return z.done()

    src = tmp_path / "src"
    src.mkdir()
    build(src / "zotero.sqlite")
    out = tmp_path / "out"
    run("mirror", "--from", str(src), "--to", str(out))
    found = [c for c in kernel.chunks(out) if "tide" in c["text"]]
    assert len(found) > 2
    assert all(c["text"].startswith("Ash (2020). Long.\n") for c in found)
    assert (
        " ".join(w for c in found for w in c["text"].split() if w.startswith("tide"))
        == words
    )


def test_an_annotation_type_zotero_adds_later_is_counted_by_its_number(tmp_path):
    def build(path):
        z = Lib(path)
        pdf = z.pdf(z.item("journalArticle", date="2020-00-00 2020", title="New"))
        z.mark(pdf, 9, text="a future kind", color="#123456")
        z.mark(pdf, 9, page="2")
        return z.done()

    text = text_of(tmp_path, build)
    assert "New (2020)., at 12:" not in text
    assert "“a future kind”\n2023-05-02 08:30" in text
    assert text.endswith("\n\n1 annotations with no text: 1 type 9\n")


def test_a_book_sections_book_is_cited_and_its_publisher_is_not_lost(tmp_path):
    def build(path):
        z = Lib(path)
        s = z.item("bookSection", date="2015-00-00 2015", title="Sediment",
                   bookTitle="Coastal Processes", publisher="Springer", place="Cham")  # fmt: skip
        z.creator(s, 0, "Weiss", "Hannah")
        return z.done()

    item = passages(text_of(tmp_path, build))[0].split("\n")
    assert item == [
        "Weiss (2015). Sediment. Coastal Processes.",
        "2021-03-04 10:22",
        "2015",
        "Hannah Weiss",
        "Cham",
        "Springer",
    ]


def test_an_overlong_citation_is_cut_with_an_ellipsis():
    got = mod.pack("x" * 300, ["body"])
    assert got == ["x" * (mod.HEAD - 1) + "…\nbody"]


def test_the_kernel_finds_a_highlight_by_its_words_and_says_whose_it_is(tmp_path):
    text_of(tmp_path)
    pile = kernel.chunks(tmp_path / "out")
    top = kernel.rank(pile, "which paper says the tide turns twice a day")
    assert top and top[0]["text"].startswith("Example, Sample & Lee (2020)")
    noted = kernel.rank(pile, "what did I note about the gauges")
    assert noted and "Ask Lee about the gauges." in noted[0]["text"]
    assert all("no text" not in c["text"] for c in noted), "a count is no note"
    # with no "doi:" label the paper's note and highlight hold as much of
    # this as its item does, and are newer: the right paper, maybe not its DOI
    doi = kernel.rank(pile, "the DOI of Tides of the Estuary")
    assert doi and all(c["text"].startswith("Example, Sample & Lee") for c in doi)
    # "added" is no longer written, so a paper's newer note and highlight,
    # which hold its title too, come first: the accepted cost, on the card
    when = kernel.rank(pile, "when did I add Tides of the Estuary")
    assert when and all(c["text"].startswith("Example, Sample & Lee") for c in when)


def shelf(path: Path) -> Path:
    """Items alone, every field filled: the library where a label or a type
    word would sit in every passage."""
    z = Lib(path)
    for n, (who, title, journal, tag) in enumerate([
        ("Ash", "Salt marsh accretion", "Wetlands", "marsh"),
        ("Birch", "Dune grass roots", "Coastal Ecology", "dunes"),
        ("Cedar", "Kelp forest decline", "Marine Biology", "kelp"),
        ("Dogwood", "Oyster reef restoration", "Restoration Notes", "oysters"),
        ("Elm", "Seagrass and storms", "Ocean Letters", "seagrass"),
    ]):  # fmt: skip
        month = ("January", "February", "March", "April", "May")[n]
        i = z.item("journalArticle", date=f"201{n}-0{n + 1}-00 {month} 201{n}", title=title,
                   publicationTitle=journal, DOI=f"10.1000/x{n}", volume=str(n + 3),
                   issue="2", pages=f"{n}1-{n}9")  # fmt: skip
        z.creator(i, 0, who, title.split()[0])
        z.creator(i, 1, who + "ley", journal.split()[0], role=3)
        z.tag(i, tag)
    return z.done()


def test_no_word_the_reader_adds_answers_a_question_about_something_absent(tmp_path):
    """A word in most passages of a file (not a date's digits) is asked with a
    word the library doesn't hold; nothing may be served. A citation, each
    passage's first line, is the library's own words and kept: one paper with
    many notes puts its authors and title in most passages, and "Example
    volcano" is then served that paper, measured below and on the card."""
    for name, build in (("sample", sample), ("shelf", shelf)):
        text = text_of(tmp_path / name, build)
        ps = [set(kernel.words(p)) for p in passages(text)]
        cited = {w for p in passages(text) for w in kernel.words(p.split("\n")[0])}
        seen = set().union(*ps) - kernel.FUNCTION - cited
        common = sorted(
            w for w in seen
            if sum(w in p for p in ps) * 2 > len(ps) and not w.isdigit()
        )  # fmt: skip
        pile = kernel.chunks(tmp_path / name / "out")
        for w in common:
            assert kernel.rank(pile, f"{w} volcano") == [], (name, w)
        assert common == [], (name, common)  # none: the reader adds no such word
    pile = kernel.chunks(tmp_path / "sample" / "out")
    served = kernel.rank(pile, "Example volcano")
    assert served and all(c["text"].startswith("Example, Sample & Lee") for c in served)
    pile = kernel.chunks(tmp_path / "shelf" / "out")
    assert kernel.rank(pile, "kelp forest decline")[0]["text"].startswith(
        "Cedar (2012)"
    )
    for q in ("when did I add Kelp forest decline", "the DOI of Kelp forest decline"):
        got = [c["text"] for c in kernel.rank(pile, q)]
        assert any("\n2021-03-04 10:22\n" in t and "10.1000/x2" in t for t in got), q
    for gone in ("doi volcano", "added volcano", "journal volcano", "author volcano",
                 "article volcano", "abstract volcano", "tags volcano"):  # fmt: skip
        assert kernel.rank(pile, gone) == [], gone


def test_the_folder_is_unchanged_and_no_journal_or_wal_appears(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    sample(src / "zotero.sqlite")
    before = {p.name: p.read_bytes() for p in src.iterdir()}
    for out in ("out", "again"):
        assert (
            run("mirror", "--from", str(src), "--to", str(tmp_path / out)).returncode
            == 0
        )
    assert {p.name: p.read_bytes() for p in src.iterdir()} == before
    assert (tmp_path / "out" / "zotero.sqlite.txt").read_bytes() == (
        tmp_path / "again" / "zotero.sqlite.txt"
    ).read_bytes()


def test_a_library_zotero_has_open_in_wal_mode_is_still_read_without_a_trace(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    path = sample(src / "zotero.sqlite")
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.close()
    before = sorted(p.name for p in src.iterdir())
    got = run("mirror", "--from", str(src), "--to", str(tmp_path / "out"))
    assert (
        got.returncode == 0
        and "Tides of the Estuary"
        in (tmp_path / "out" / "zotero.sqlite.txt").read_text()
    )
    assert sorted(p.name for p in src.iterdir()) == before == ["zotero.sqlite"]


def test_other_sqlite_files_and_other_names_are_left_alone(tmp_path):
    src = tmp_path / "src"
    (src / "sub").mkdir(parents=True)
    sample(src / "sub" / "zotero.sqlite")
    sample(src / "zotero.sqlite.bak")
    con = sqlite3.connect(src / "places.sqlite")
    con.execute("CREATE TABLE items (itemID INTEGER)")
    con.close()
    (src / "broken.sqlite").write_bytes(b"not a database at all")
    out = tmp_path / "out"
    got = run("mirror", "--from", str(src), "--to", str(out))
    assert got.returncode == 0 and got.stdout.strip().endswith(
        "wrote 1 files to " + str(out) + "; skipped 2"
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["sub/zotero.sqlite.txt"]


def test_hidden_files_and_folders_are_not_read(tmp_path):
    src = tmp_path / "src"
    (src / ".hid").mkdir(parents=True)
    sample(src / ".hid" / "zotero.sqlite")
    sample(src / ".zotero.sqlite")
    got = run("mirror", "--from", str(src), "--to", str(tmp_path / "out"))
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_an_empty_library_says_so(tmp_path):
    assert (
        text_of(tmp_path, lambda p: Lib(p).done()) == "no items, notes or annotations\n"
    )


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert (
        run(
            "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
        ).returncode
        == 2
    )


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "zotero.py" in got.stderr
