"""bookmarks: a browser's bookmark export, Firefox's backup (plain and
compressed), Chrome's Bookmarks file, and copies of places.sqlite and History,
each as one passage per bookmark or page; recognised by what a file holds, the
times read in each format's own epoch, other files left alone, the same bytes
twice, originals unchanged, and MIRROR and FOLDER kept apart.

The samples follow each format as the browsers write it: no real export was at
hand, so they were built to the formats' documented shapes."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "bookmarks.py"
spec = importlib.util.spec_from_file_location("bookmarks", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# 2024-03-02 11:15:30 UTC, in each format's own clock
SECONDS = 1709378130
FIREFOX_US = SECONDS * 1_000_000
CHROME_US = (SECONDS + 11644473600) * 1_000_000

# a Firefox HTML export, as Firefox writes it (unclosed <DT> and <DD>, <p> after <DL>)
FIREFOX_HTML = f"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'none'; img-src data: *; object-src 'none'"></meta>
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks Menu</H1>

<DL><p>
    <DT><H3 ADD_DATE="1709337600" LAST_MODIFIED="1709337600" PERSONAL_TOOLBAR_FOLDER="true">Bookmarks Toolbar</H3>
    <DD>Add bookmarks to this folder to see them displayed on the Bookmarks Toolbar
    <DL><p>
        <DT><H3 ADD_DATE="1709337600" LAST_MODIFIED="1709337600">Garden</H3>
        <DL><p>
            <DT><A HREF="https://example.org/tomatoes" ADD_DATE="{SECONDS}" LAST_MODIFIED="{SECONDS}" ICON_URI="https://example.org/favicon.ico" ICON="data:image/png;base64,iVBORw0KGgo=" TAGS="garden,veg">Tomato growing guide</A>
            <DD>Staking &amp; pruning,
            step by step.
            <DT><A HREF="https://example.org/blight" ADD_DATE="1709510400" LAST_MODIFIED="1709510400">Blight</A>
        </DL><p>
    </DL><p>
    <DT><A HREF="place:sort=8&amp;maxResults=10" ADD_DATE="1709337600">Recently Bookmarked</A>
    <HR>    <DT><A HREF="https://example.com/bread" ADD_DATE="0" SHORTCUTURL="bread">Sourdough &lt;starter&gt;</A>
</DL>
"""

# Chrome's export: an <H1>Bookmarks</H1> then the bar as a folder
CHROME_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="1709337600" LAST_MODIFIED="1709337600" PERSONAL_TOOLBAR_FOLDER="true">Bookmarks bar</H3>
    <DL><p>
        <DT><A HREF="https://example.org/roof" ADD_DATE="1709337600" ICON="data:image/png;base64,AAAA">Roof repair quotes</A>
    </DL><p>
</DL><p>
"""

FIREFOX_BACKUP = {
    "guid": "root________", "title": "", "index": 0, "dateAdded": 1709337600000000,
    "lastModified": FIREFOX_US, "id": 1, "typeCode": 2,
    "type": "text/x-moz-place-container", "root": "placesRoot",
    "children": [
        {"guid": "menu________", "title": "menu", "index": 0, "dateAdded": 1709337600000000,
         "id": 2, "typeCode": 2, "type": "text/x-moz-place-container", "root": "bookmarksMenuFolder",
         "children": [
             {"guid": "aB3dEf6hIj9k", "title": "Kitchen", "index": 0, "id": 7, "typeCode": 2,
              "type": "text/x-moz-place-container", "dateAdded": 1709337600000000,
              "children": [
                  {"guid": "x1y2z3a4b5c6", "title": "Sourdough starter", "index": 0,
                   "dateAdded": FIREFOX_US, "lastModified": FIREFOX_US, "id": 8, "typeCode": 1,
                   "tags": "baking,bread", "iconUri": "https://example.com/favicon.ico",
                   "type": "text/x-moz-place", "uri": "https://example.com/starter",
                   "annos": [{"name": "bookmarkProperties/description", "flags": 0, "expires": 4,
                              "value": "Feed it twice a day."}]},
                  {"guid": "sep_________", "index": 1, "id": 9, "typeCode": 3,
                   "type": "text/x-moz-place-separator", "dateAdded": FIREFOX_US},
                  {"guid": "q1q2q3q4q5q6", "title": "Most Visited", "index": 2, "id": 10, "typeCode": 1,
                   "type": "text/x-moz-place", "uri": "place:sort=8&maxResults=10"},
              ]},
         ]},
        {"guid": "toolbar_____", "title": "toolbar", "index": 1, "id": 3, "typeCode": 2,
         "type": "text/x-moz-place-container", "root": "toolbarFolder", "children": [
             {"guid": "t1t2t3t4t5t6", "title": "Train times", "index": 0, "dateAdded": 0,
              "id": 11, "typeCode": 1, "type": "text/x-moz-place", "uri": "https://example.net/trains"}]},
        {"guid": "tags________", "title": "tags", "index": 2, "id": 4, "typeCode": 2,
         "type": "text/x-moz-place-container", "root": "tagsFolder", "children": [
             {"title": "baking", "id": 12, "typeCode": 2, "type": "text/x-moz-place-container",
              "children": [{"id": 13, "typeCode": 1, "type": "text/x-moz-place",
                            "uri": "https://example.com/starter"}]}]},
        {"guid": "unfiled_____", "title": "unfiled", "index": 3, "id": 5, "typeCode": 2,
         "type": "text/x-moz-place-container", "root": "unfiledBookmarksFolder"},
    ],
}  # fmt: skip

CHROME_BOOKMARKS = {
    "checksum": "0d1f6e0e4c1a8b7f9e2d3c4b5a697887",
    "roots": {
        "bookmark_bar": {
            "children": [
                {"date_added": str(CHROME_US), "date_last_used": "0", "guid": "0b6f0d0e-1",
                 "id": "5", "meta_info": {"power_bookmark_meta": ""}, "name": "Library hours",
                 "type": "url", "url": "https://example.org/library"},
                {"children": [
                    {"date_added": "13353900000000000", "guid": "0b6f0d0e-3", "id": "7",
                     "name": "Bus timetable", "type": "url", "url": "https://example.org/bus"}],
                 "date_added": "13353800000000000", "date_last_used": "0",
                 "date_modified": "13353900000000000", "guid": "0b6f0d0e-2", "id": "6",
                 "name": "Travel", "type": "folder"},
            ],
            "date_added": "13353800000000000", "date_last_used": "0",
            "date_modified": "13353900000000000", "guid": "0bc5d13f-2cba-5d74-951f-3f233fe6c908",
            "id": "1", "name": "Bookmarks bar", "type": "folder",
        },
        "other": {"children": [
            {"date_added": "0", "guid": "0b6f0d0e-4", "id": "8", "name": "Undated thing",
             "type": "url", "url": "https://example.org/undated"}],
            "date_added": "13353800000000000", "date_modified": "0",
            "guid": "82b081ec-3dd3-529c-8475-ab6c344590dd", "id": "2",
            "name": "Other bookmarks", "type": "folder"},
        "synced": {"children": [], "date_added": "13353800000000000", "date_modified": "0",
                   "guid": "4cf2e351-0e85-532b-bb37-df045d8f8d0f", "id": "3",
                   "name": "Mobile bookmarks", "type": "folder"},
    },
    "version": 1,
}  # fmt: skip

# Firefox's places.sqlite, its tables as Firefox makes them (the columns read, and their neighbours)
PLACES_SCHEMA = """
CREATE TABLE moz_origins (id INTEGER PRIMARY KEY, prefix TEXT NOT NULL, host TEXT NOT NULL,
  frecency INTEGER NOT NULL, recalc_frecency INTEGER NOT NULL DEFAULT 0, alt_frecency INTEGER,
  recalc_alt_frecency INTEGER NOT NULL DEFAULT 0, UNIQUE (prefix, host));
CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url LONGVARCHAR, title LONGVARCHAR,
  rev_host LONGVARCHAR, visit_count INTEGER DEFAULT 0, hidden INTEGER DEFAULT 0 NOT NULL,
  typed INTEGER DEFAULT 0 NOT NULL, frecency INTEGER DEFAULT -1 NOT NULL, last_visit_date INTEGER,
  guid TEXT, foreign_count INTEGER DEFAULT 0 NOT NULL, url_hash INTEGER DEFAULT 0 NOT NULL,
  description TEXT, preview_image_url TEXT, site_name TEXT, origin_id INTEGER REFERENCES moz_origins(id),
  recalc_frecency INTEGER NOT NULL DEFAULT 0, alt_frecency INTEGER,
  recalc_alt_frecency INTEGER NOT NULL DEFAULT 0);
CREATE TABLE moz_historyvisits (id INTEGER PRIMARY KEY, from_visit INTEGER, place_id INTEGER,
  visit_date INTEGER, visit_type INTEGER, session INTEGER, source INTEGER DEFAULT 0 NOT NULL,
  triggeringPlaceId INTEGER);
CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY, type INTEGER, fk INTEGER DEFAULT NULL,
  parent INTEGER, position INTEGER, title LONGVARCHAR, keyword_id INTEGER, folder_type TEXT,
  dateAdded INTEGER, lastModified INTEGER, guid TEXT, syncStatus INTEGER NOT NULL DEFAULT 0,
  syncChangeCounter INTEGER NOT NULL DEFAULT 1);
CREATE TABLE moz_keywords (id INTEGER PRIMARY KEY AUTOINCREMENT, keyword TEXT UNIQUE,
  place_id INTEGER, post_data TEXT);
INSERT INTO moz_bookmarks (id, type, fk, parent, position, title, dateAdded, guid) VALUES
  (1, 2, NULL, 0, 0, '', 1709337600000000, 'root________'),
  (2, 2, NULL, 1, 0, 'menu', 1709337600000000, 'menu________'),
  (3, 2, NULL, 1, 1, 'toolbar', 1709337600000000, 'toolbar_____'),
  (4, 2, NULL, 1, 2, 'tags', 1709337600000000, 'tags________'),
  (5, 2, NULL, 1, 3, 'unfiled', 1709337600000000, 'unfiled_____'),
  (6, 2, NULL, 1, 4, 'mobile', 1709337600000000, 'mobile______'),
  (10, 2, NULL, 3, 0, 'Garden', 1709337600000000, 'gArDeNfOlDeR'),
  (11, 1, 1, 10, 0, 'Tomato growing guide', 1709378130000000, 'bm1bm1bm1bm1'),
  (12, 2, NULL, 4, 0, 'veg', 1709337600000000, 'tagvegtagveg'),
  (13, 1, 1, 12, 0, NULL, 1709378130000000, 'tagbm1tagbm1'),
  (14, 3, NULL, 3, 1, NULL, 1709378130000000, 'separator001'),
  (15, 1, 4, 2, 0, 'Most Visited', 1709378130000000, 'smartbm00001');
INSERT INTO moz_places (id, url, title, rev_host, visit_count, hidden, last_visit_date, guid, description) VALUES
  (1, 'https://example.org/tomatoes', 'Tomatoes | Example', 'gro.elpmaxe.', 1, 0, 1709378130000000, 'p1p1p1p1p1p1', 'How to grow tomatoes.'),
  (2, 'https://example.org/blight', 'Tomato blight: what to do', 'gro.elpmaxe.', 3, 0, 1709650920000000, 'p2p2p2p2p2p2', NULL),
  (3, 'https://ads.example.net/frame', 'ad frame', 'ten.elpmaxe.sda.', 1, 1, 1709650920000000, 'p3p3p3p3p3p3', NULL),
  (4, 'place:sort=8&maxResults=10', NULL, NULL, 0, 0, NULL, 'p4p4p4p4p4p4', NULL),
  (5, 'https://example.org/old', 'Allotment rota', 'gro.elpmaxe.', 7, 0, 1577836800000000, 'p5p5p5p5p5p5', NULL),
  (6, 'https://example.org/never', 'Bookmarked, never visited', 'gro.elpmaxe.', 0, 0, NULL, 'p6p6p6p6p6p6', NULL),
  (7, 'https://example.org/embed', 'Only embedded', 'gro.elpmaxe.', 0, 0, NULL, 'p7p7p7p7p7p7', NULL);
INSERT INTO moz_historyvisits (id, from_visit, place_id, visit_date, visit_type, session) VALUES
  (1, 0, 1, 1709378130000000, 1, 0),
  (2, 0, 2, 1709251200000000, 2, 0),
  (3, 2, 2, 1709280000000000, 1, 0),
  (4, 0, 2, 1709650920000000, 1, 0),
  (5, 0, 3, 1709650920000000, 1, 0),
  (6, 0, 7, 1709650920000000, 4, 0),
  (7, 0, 7, 1709650920000000, 8, 0);
"""

# Chrome's History, its tables as Chrome makes them
HISTORY_SCHEMA = f"""
CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, value LONGVARCHAR);
CREATE TABLE urls(id INTEGER PRIMARY KEY AUTOINCREMENT, url LONGVARCHAR, title LONGVARCHAR,
  visit_count INTEGER DEFAULT 0 NOT NULL, typed_count INTEGER DEFAULT 0 NOT NULL,
  last_visit_time INTEGER NOT NULL, hidden INTEGER DEFAULT 0 NOT NULL);
CREATE TABLE visits(id INTEGER PRIMARY KEY AUTOINCREMENT, url INTEGER NOT NULL,
  visit_time INTEGER NOT NULL, from_visit INTEGER, external_referrer_url TEXT,
  transition INTEGER DEFAULT 0 NOT NULL, segment_id INTEGER, visit_duration INTEGER DEFAULT 0 NOT NULL,
  incremented_omnibox_typed_score BOOLEAN DEFAULT FALSE NOT NULL, opener_visit INTEGER,
  originator_cache_guid TEXT, originator_visit_id INTEGER, originator_from_visit INTEGER,
  originator_opener_visit INTEGER, is_known_to_sync BOOLEAN DEFAULT FALSE NOT NULL,
  consider_for_ntp_most_visited BOOLEAN DEFAULT FALSE NOT NULL, visited_link_id INTEGER DEFAULT 0 NOT NULL,
  app_id TEXT);
CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT NULL, url_id INTEGER NOT NULL,
  term LONGVARCHAR NOT NULL, normalized_term LONGVARCHAR NOT NULL);
INSERT INTO meta VALUES ('version', '69');
INSERT INTO urls VALUES (1, 'https://example.org/heat-pump', 'Heat pump sizing calculator', 2, 1, {CHROME_US + 86400_000000}, 0);
INSERT INTO urls VALUES (2, 'https://example.org/iframe', 'iframe', 1, 0, {CHROME_US}, 0);
INSERT INTO urls VALUES (3, 'https://example.org/hidden', 'hidden', 1, 0, {CHROME_US}, 1);
INSERT INTO visits (id, url, visit_time, from_visit, transition, segment_id, visit_duration) VALUES
  (1, 1, {CHROME_US}, 0, 805306369, 1, 120000000),
  (2, 1, {CHROME_US + 86400_000000}, 0, 838860808, 1, 3000000),
  (3, 2, {CHROME_US}, 1, 3, 0, 0);
"""


def make_db(path: Path, script: str) -> Path:
    con = sqlite3.connect(path)
    con.executescript(script)
    con.commit()
    con.close()
    return path


def lz4_compress(data: bytes) -> bytes:
    """A small greedy LZ4 block compressor, to make .jsonlz4 files to read."""
    out = bytearray()

    def more(n: int) -> None:
        while n >= 255:
            out.append(255)
            n -= 255
        out.append(n)

    def emit(lits: bytes, back: int = 0, length: int = 0) -> None:
        token = min(len(lits), 15) << 4 | (min(length - 4, 15) if back else 0)
        out.append(token)
        if len(lits) >= 15:
            more(len(lits) - 15)
        out.extend(lits)
        if back:
            out.extend(struct.pack("<H", back))
            if length - 4 >= 15:
                more(length - 4 - 15)

    seen: dict = {}
    i = anchor = 0
    end = len(data) - 5  # the last five bytes are always literals
    while i + 4 <= end:
        j = seen.get(data[i : i + 4])
        seen[data[i : i + 4]] = i
        if j is not None and i - j <= 65535:
            m = 4
            while i + m < end and data[j + m] == data[i + m]:
                m += 1
            emit(data[anchor:i], i - j, m)
            i += m
            anchor = i
        else:
            i += 1
    emit(data[anchor:])
    return bytes(out)


def jsonlz4(doc: dict) -> bytes:
    raw = json.dumps(doc).encode()
    return b"mozLz40\0" + struct.pack("<I", len(raw)) + lz4_compress(raw)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def passages(text: str) -> list[str]:
    return text.rstrip("\n").split("\n\n")


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


# ── the formats ─────────────────────────────────────────────────────────────
def test_firefoxs_html_export_one_passage_per_bookmark_with_its_folder_tags_and_description(
    tmp_path,
):
    got, out = mirror_of(tmp_path, {"bookmarks.html": FIREFOX_HTML.encode()})
    assert got.returncode == 0, got.stderr
    assert passages((out / "bookmarks.html.txt").read_text()) == [
        # the export's own <H1> and the toolbar hold everything: not written
        "2024-03-02  Tomato growing guide\n"
        "example.org/tomatoes\n"
        "in Garden\n"
        "#garden, #veg\n"
        "Staking & pruning, step by step.",
        "2024-03-04  Blight\nexample.org/blight\nin Garden",
        "Sourdough <starter>\nexample.com/bread",
    ]


def test_chromes_html_export_and_a_bookmark_at_the_top_level(tmp_path):
    assert mod.netscape(CHROME_HTML) == [
        "2024-03-02  Roof repair quotes\nexample.org/roof"
    ]
    bare = "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<DL><p>\n<DT><A HREF='http://www.a.example/'></A>\n</DL>"
    assert mod.netscape(bare) == ["http://www.a.example/"], (
        "no date, no title: nothing in their place"
    )


def test_a_description_ends_at_the_next_folder_and_a_folders_own_is_not_a_bookmarks():
    html = (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<H1>B</H1>\n<DL><p>\n"
        '<DT><A HREF="https://a.example/" ADD_DATE="1709378130">A</A>\n<DD>about a\n'
        "<DT><H3>F</H3>\n<DD>the folder's note\n<DL><p>\n"
        '<DT><A HREF="https://b.example/">B</A>\n<DD>about b\n</DL><p>\n'
        '<DT><A HREF="https://c.example/">C</A>\n<DD>about c'
    )
    got = mod.netscape(html)
    assert [p.splitlines()[-1] for p in got] == ["about a", "about b", "about c"]
    assert "folder's note" not in "".join(got)
    assert got[1].splitlines()[2] == "in F"
    assert got[2] == "C\nc.example/\nabout c", "the folder F closed before C"


def test_a_firefox_backup_keeps_its_folders_tags_and_description_and_drops_queries(
    tmp_path,
):
    got, out = mirror_of(tmp_path, {"bookmarks-2024-03-02.json": json.dumps(FIREFOX_BACKUP).encode()})  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert passages((out / "bookmarks-2024-03-02.json.txt").read_text()) == [
        "2024-03-02  Sourdough starter\n"
        "example.com/starter\n"
        "in Kitchen\n"
        "#baking, #bread\n"
        "Feed it twice a day.",
        "Train times\nexample.net/trains",
    ]


def test_a_compressed_firefox_backup_reads_the_same_as_the_plain_one(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "plain.json": json.dumps(FIREFOX_BACKUP).encode(),
            "bookmarks-2024-03-02_2_abc.jsonlz4": jsonlz4(FIREFOX_BACKUP),
        },
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 2 files" in got.stdout
    assert (out / "bookmarks-2024-03-02_2_abc.jsonlz4.txt").read_bytes() == (
        out / "plain.json.txt"
    ).read_bytes()


def test_chromes_bookmarks_file_bar_first_with_its_folders_and_dates(tmp_path):
    got, out = mirror_of(
        tmp_path, {"Default/Bookmarks": json.dumps(CHROME_BOOKMARKS, indent=3).encode()}
    )
    assert got.returncode == 0, got.stderr
    assert passages((out / "Default/Bookmarks.txt").read_text()) == [
        "2024-03-02  Library hours\nexample.org/library",
        "2024-03-03  Bus timetable\nexample.org/bus\nin Travel",
        "Undated thing\nexample.org/undated",
    ]


def test_a_copy_of_places_sqlite_gives_its_bookmarks_then_each_page_visited(tmp_path):
    db = make_db(tmp_path / "places.sqlite", PLACES_SCHEMA)
    got, out = mirror_of(tmp_path / "x", {"places.sqlite": db.read_bytes()})
    assert got.returncode == 0, got.stderr
    assert passages((out / "places.sqlite.txt").read_text()) == [
        "2024-03-02  Tomato growing guide\n"
        "example.org/tomatoes\n"
        "in Garden\n"
        "#veg\n"
        "How to grow tomatoes.",
        # history, oldest last visit first; a page whose visits expired keeps its count
        "2020-01-01 00:00  Allotment rota\nexample.org/old\n×7",
        "2024-03-02 11:15  Tomatoes | Example\nexample.org/tomatoes\n×1  2024-03-02",
        "2024-03-05 15:02  Tomato blight: what to do\n"
        "example.org/blight\n"
        "×3  2024-03-01, 2024-03-05",
    ]


def test_a_copy_of_chromes_history_counts_your_visits_and_not_a_pages_frames(tmp_path):
    db = make_db(tmp_path / "History", HISTORY_SCHEMA)
    got, out = mirror_of(tmp_path / "x", {"History": db.read_bytes()})
    assert got.returncode == 0, got.stderr
    assert (out / "History.txt").read_text() == (
        "2024-03-03 11:15  Heat pump sizing calculator\n"
        "example.org/heat-pump\n"
        "×2  2024-03-02, 2024-03-03\n"
    )


def test_the_database_is_opened_read_only_so_nothing_is_written_beside_it(tmp_path):
    (tmp_path / "w").mkdir()
    db = make_db(tmp_path / "w" / "places.sqlite", PLACES_SCHEMA)
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=WAL")
    con.close()
    before = sorted(p.name for p in db.parent.iterdir())
    (db.parent / "places.sqlite").chmod(0o444)
    got = run("mirror", "--from", str(db.parent), "--to", str(tmp_path / "out"))
    assert got.returncode == 0, got.stderr
    assert sorted(p.name for p in db.parent.iterdir()) == before == ["places.sqlite"]


def test_a_page_visited_on_many_days_lists_the_newest_twenty_and_counts_the_rest():
    visits = [utc(2024, 1, d, 9) for d in range(1, 26)] + [utc(2024, 1, 25, 18)]
    got = mod.page("Tides", "https://t.example/", visits, 0, None)
    lines = got.splitlines()
    assert lines[:2] == ["2024-01-25 18:00  Tides", "t.example/"]
    assert (
        lines[2] == "×26  " + ", ".join(f"2024-01-{d:02}" for d in range(6, 26)) + " +5"
    )
    assert mod.page("T", "u", visits[4:], 0, None).endswith("2024-01-25 +1")
    assert mod.page("T", "u", visits[5:], 0, None).endswith(", 2024-01-25")
    assert mod.page("", "u", [], 4, utc(2020, 1, 1)) == "2020-01-01 00:00\nu\n×4"


def test_a_long_address_lists_fewer_days_so_the_page_stays_one_passage():
    visits = [utc(2024, 1, d, 9) for d in range(1, 26)]
    url = "https://search.example/?q=tides&" + "x" * 300
    got = mod.page("Tides", url, visits, 0, None)
    assert (
        len(got)
        <= mod.kernel.MAX_CHUNK
        < len(mod.page("Tides", "u", visits, 0, None)) + len(url)
    )
    days = got.splitlines()[2]
    assert days.startswith("×25  2024-01-") and ", 2024-01-25 +" in days
    shown = days.count("2024-")
    assert 1 <= shown < 20 and days.endswith(f" +{25 - shown}")
    one_more = got.replace(days, "×25  2024-01-%02d, " % (25 - shown) + days[5:])
    assert len(one_more) > mod.kernel.MAX_CHUNK, "as many days as fit, not fewer"
    huge = mod.page("T", "https://x.example/" + "y" * 600, visits, 0, None)
    assert huge.splitlines()[2] == "×25  2024-01-25 +24"


# ── the clocks ──────────────────────────────────────────────────────────────
def test_each_formats_clock_on_real_looking_values():
    assert mod.moment(SECONDS, mod.UNIX, 1) == utc(2024, 3, 2, 11, 15, 30)
    assert mod.moment(FIREFOX_US, mod.UNIX, 1_000_000) == utc(2024, 3, 2, 11, 15, 30)
    assert mod.moment(str(CHROME_US), mod.WINDOWS, 1_000_000) == utc(2024, 3, 2, 11, 15, 30)  # fmt: skip


def test_the_epochs_edges():
    w = mod.WINDOWS
    assert mod.moment("11644473600000000", w, 1_000_000) == utc(1970, 1, 1)
    assert mod.day(mod.moment("11644473599999999", w, 1_000_000)) == "1969-12-31"
    assert mod.moment(1, w, 1_000_000) == utc(1601, 1, 1, 0, 0, 0, 1)
    assert mod.moment(1, mod.UNIX, 1) == utc(1970, 1, 1, 0, 0, 1)
    assert mod.day(mod.moment(253402300799, mod.UNIX, 1)) == "9999-12-31"
    for nothing in (0, "0", -1, None, "", "soon", 253402300800, 10**30):
        assert mod.moment(nothing, mod.UNIX, 1) is None, nothing
    assert mod.day(None) == ""


def test_an_address_loses_only_the_https_and_www_nearly_every_one_has():
    assert mod.address("https://www.example.org/a?b=c") == "example.org/a?b=c"
    assert mod.address("https://wwwexample.org/") == "wwwexample.org/"
    assert mod.address("http://www.example.org/") == "http://www.example.org/"
    assert mod.address("ftp://files.example/x") == "ftp://files.example/x"


# ── the compression ─────────────────────────────────────────────────────────
def test_an_lz4_block_by_hand_with_a_match_that_overlaps_itself():
    # one literal "a", then 8 more copied from 1 back, then a last literal "b"
    assert mod.lz4_block(bytes([0x14, 0x61, 0x01, 0x00, 0x10, 0x62]), 10) == b"a" * 9 + b"b"  # fmt: skip


def test_lz4_long_literals_and_long_matches_round_trip():
    data = bytes(range(256)) * 3 + b"x" * 1000 + b"tide " * 300 + bytes(range(40))
    packed = lz4_compress(data)
    assert len(packed) < len(data) // 3
    assert mod.lz4_block(packed, len(data)) == data


def test_a_broken_lz4_block_is_refused_not_misread():
    for block, size in ((bytes([0x14, 0x61, 0x02, 0x00]), 9), (bytes([0x14, 0x61, 0x00, 0x00]), 9),
                        (bytes([0x10, 0x61]), 2)):  # fmt: skip
        try:
            mod.lz4_block(block, size)
        except ValueError:
            continue
        raise AssertionError(block)


# ── which files ─────────────────────────────────────────────────────────────
def test_files_are_known_by_what_they_hold_and_others_are_left_alone(tmp_path):
    other_db = make_db(tmp_path / "o.db", "CREATE TABLE notes (t TEXT);")
    got, out = mirror_of(
        tmp_path / "x",
        {
            "export.txt": b"\xef\xbb\xbf"
            + FIREFOX_HTML.lower().encode(),  # any name, any case
            "about.md": b"Exports start with <!DOCTYPE NETSCAPE-Bookmark-file-1>.\n",
            "reader.py": b'HEAD = "<!DOCTYPE NETSCAPE-Bookmark-file-1>"\n',
            "notes.html": b"<html><body>Not bookmarks</body></html>",
            "package.json": b'{"name": "x", "version": "1.0.0"}',
            "Bookmarks-like.json": b'{"roots": {"a": 1}}',
            "app.db": other_db.read_bytes(),
            "garden.md": b"Tomatoes want sun.\n",
        },
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("wrote 1 files to " + str(out) + "; skipped 0")
    assert [p.name for p in out.rglob("*")] == ["export.txt.txt"]


def test_a_known_file_it_cannot_read_or_that_holds_nothing_is_skipped_and_counted(
    tmp_path,
):
    empty = json.dumps({"roots": {"bookmark_bar": {"type": "folder", "children": []},
                                  "other": {"type": "folder"}}}).encode()  # fmt: skip
    got, out = mirror_of(
        tmp_path,
        {
            "good.html": CHROME_HTML.encode(),
            "broken.json": b'{"roots": {"bookmark_bar": ',
            "cut.jsonlz4": jsonlz4(FIREFOX_BACKUP)[:60],
            "latin.html": "<!DOCTYPE NETSCAPE-Bookmark-file-1><A HREF='x'>caf\xe9</A>".encode("latin-1"),
            "Bookmarks": empty,
        },
    )  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and got.stdout.strip().endswith("skipped 4")
    assert [p.name for p in out.rglob("*")] == ["good.html.txt"]


def test_a_big_history_is_cut_between_passages_into_parts_the_kernel_reads(tmp_path):
    text = "\n\n".join(f"2024-01-01 09:00  Page {i}\nx.example/{i}\n×1" for i in range(9)) + "\n"  # fmt: skip
    pieces = mod.parts(text, limit=120)
    assert all(len(p.encode()) <= 120 for p in pieces) and len(pieces) > 1
    assert "\n\n".join(p.rstrip("\n") for p in pieces) + "\n" == text
    assert all(p.startswith("2024-01-01 09:00  Page") for p in pieces)
    assert mod.parts("x" * 300, limit=100) == ["x" * 99 + "\n"]


def test_a_big_mirror_is_written_in_parts_and_stale_parts_are_removed(
    tmp_path, monkeypatch
):
    src, dst = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "b.html").write_text(FIREFOX_HTML)
    # in-process, the command line the guard reads is this one
    monkeypatch.setattr(sys, "argv", ["bookmarks.py", "mirror", "--from", str(src), "--to", str(dst)])  # fmt: skip
    real = mod.parts
    monkeypatch.setattr(mod, "parts", lambda t: real(t, 80))
    assert mod.mirror(src, dst) == (1, 0)
    names = sorted(p.name for p in dst.iterdir())
    assert names == ["b.html.part2.txt", "b.html.part3.txt", "b.html.txt"]
    (dst / "b.html.part4.txt").write_text("stale")
    monkeypatch.setattr(mod, "parts", lambda t: real(t, 10_000))
    assert mod.mirror(src, dst) == (1, 0)
    assert sorted(p.name for p in dst.iterdir()) == ["b.html.txt"]


# ── no word on every passage ────────────────────────────────────────────────
#: a folder of several passages of each kind, with the hosts a real one has
ABSENT_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks Menu</H1>
<DL><p>
    <DT><H3 PERSONAL_TOOLBAR_FOLDER="true">Bookmarks Toolbar</H3>
    <DL><p>
        <DT><H3>Kitchen</H3>
        <DL><p>
            <DT><A HREF="https://www.seriouseats.com/sourdough-starter" ADD_DATE="1709378130" TAGS="baking">Sourdough starter guide</A>
            <DT><A HREF="https://cooking.nytimes.com/recipes/focaccia" ADD_DATE="1709510400">Focaccia</A>
        </DL><p>
        <DT><H3>House</H3>
        <DL><p>
            <DT><A HREF="https://www.energysavingtrust.org.uk/heat-pumps" ADD_DATE="1709600000">Heat pump sizing calculator</A>
            <DD>Which size for a three-bed semi.
            <DT><A HREF="https://github.com/home-assistant/core" ADD_DATE="1709700000" TAGS="smart-home">Home Assistant</A>
        </DL><p>
        <DT><A HREF="https://en.wikipedia.org/wiki/Tide" ADD_DATE="1709800000">Tide - Wikipedia</A>
        <DT><A HREF="https://www.bbc.co.uk/weather/2644688" ADD_DATE="1709900000">Leeds weather</A>
    </DL><p>
</DL>
"""

ABSENT_HISTORY = """
INSERT INTO moz_places (id, url, title, visit_count, hidden, last_visit_date) VALUES
  (20, 'https://www.rhs.org.uk/disease/tomato-blight', 'Tomato blight / RHS Gardening', 2, 0, NULL),
  (21, 'https://docs.python.org/3/library/asyncio.html', 'asyncio — Asynchronous I/O', 5, 0, NULL),
  (22, 'https://www.thetrainline.com/en/train-times/leeds-to-york', 'Leeds to York train times', 1, 0, NULL),
  (23, 'https://news.ycombinator.com/item?id=39561234', 'Show HN: a tiny search engine', 1, 0, NULL),
  (24, 'https://www.gov.uk/self-assessment-tax-returns/deadlines', 'Self Assessment deadlines - GOV.UK', 3, 0, NULL);
INSERT INTO moz_historyvisits (id, place_id, visit_date, visit_type) VALUES
  (20, 20, 1709280000000000, 1), (21, 20, 1709380000000000, 1),
  (22, 21, 1709480000000000, 1), (23, 22, 1709580000000000, 2),
  (24, 23, 1709680000000000, 1), (25, 24, 1709780000000000, 1), (26, 24, 1709880000000000, 1);
"""


def test_a_word_on_most_passages_answers_no_question_about_something_absent(tmp_path):
    db = make_db(tmp_path / "places.sqlite", PLACES_SCHEMA + ABSENT_HISTORY)
    _, out = mirror_of(
        tmp_path / "x",
        {"export.html": ABSENT_HTML.encode(), "places.sqlite": db.read_bytes()},
    )
    pile = mod.kernel.chunks(out)
    common: set = set()
    for path in {c["path"] for c in pile}:
        mine = [set(mod.kernel.words(c["text"])) for c in pile if c["path"] == path]
        counts: dict = {}
        for ws in mine:
            for w in ws - mod.kernel.FUNCTION:
                counts[w] = counts.get(w, 0) + 1
        # dates stay as digits, which the kernel reads as dates
        common |= {
            w for w, n in counts.items() if 2 * n > len(mine) and not w.isdigit()
        }
    # what this reader used to write on every passage, and what it measured
    filler = {"bookmarked", "visited", "url", "folder", "tags", "description",
              "visits", "last", "days", "date", "utc", "https", "www", "menu",
              "toolbar", "bar", "earlier", "title", "top", "level"}  # fmt: skip
    # a host's own parts are the address, kept: "that rhs page", "the github one"
    hosts = {"org", "com", "uk", "example"}
    assert common <= hosts, common - hosts
    for w in sorted((common - hosts) | filler):
        assert mod.kernel.rank(pile, f"volcano {w}") == [], w

    def lands(question: str, needle: str) -> bool:
        return any(needle in c["text"] for c in mod.kernel.rank(pile, question))

    assert lands("when did I bookmark the sourdough starter guide", "seriouseats.com")
    assert lands("heat pump sizing calculator", "energysavingtrust")
    assert lands("when did I look at tomato blight", "rhs.org.uk/disease")
    assert lands("Leeds to York train times", "×1  2024-03-04")
    assert lands("what did I save in Kitchen", "Focaccia")


# ── the contract ────────────────────────────────────────────────────────────
def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "b.html": CHROME_HTML.encode(),
            ".hid/b.html": CHROME_HTML.encode(),
            ".b.html": CHROME_HTML.encode(),
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["b.html.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    db = make_db(tmp_path / "places.sqlite", PLACES_SCHEMA).read_bytes()
    files = {"places.sqlite": db, "b.html": FIREFOX_HTML.encode()}
    got, out = mirror_of(tmp_path / "x", files)
    src = tmp_path / "x" / "src"
    again = tmp_path / "again"
    run("mirror", "--from", str(src), "--to", str(again))
    for name in files:
        assert (again / f"{name}.txt").read_bytes() == (
            out / f"{name}.txt"
        ).read_bytes()
        assert (src / name).read_bytes() == files[name]


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    got = run("mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m"))  # fmt: skip
    assert got.returncode == 2 and got.stderr.startswith("refused")


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "bookmarks.py" in got.stderr
