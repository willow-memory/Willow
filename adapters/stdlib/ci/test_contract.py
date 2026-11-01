"""What every add-on promises alike, held for all of them in one place.

The command line: run with nothing, an add-on refuses (exit 2) and says how
to run it, by its own file name. Run right, it works; with one argument more,
against a real box, it refuses the same way, so the refusal is the command
line's and nothing else's.

The readers: each that writes a mirror (`mirror --from FOLDER --to MIRROR`)
keeps the one contract the readers share, whatever it reads. It says
`wrote N files to MIRROR; skipped M`; the same folder gives the same bytes;
originals are never changed; hidden files and folders are never read; a
folder with nothing to read is 42; a mirror inside the folder, or the folder
inside the mirror, or a folder that isn't one, is refused and writes
nothing. `check_reader` is the contract, so a reader in adapters/deps (pdf)
runs it from its own tests, where its install is.

WILLOW_ONLY=NAME narrows both to one add-on: mutants.py runs an add-on's own
tests and its share of these, and nothing else.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
STDLIB = ROOT / "adapters" / "stdlib"
KERNEL = ROOT / "kernel.py"
ONLY = os.environ.get("WILLOW_ONLY", "")
NOW = ["--now", "2026-10-23T00:00:00Z"]


def _docx(text: str) -> bytes:
    from io import BytesIO

    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", f'<w:document xmlns:w="{w}"><w:body><w:p><w:r>'
                   f"<w:t>{text}</w:t></w:r></w:p></w:body></w:document>")  # fmt: skip
    return buf.getvalue()


def _zip(files: dict[str, str]) -> bytes:
    from io import BytesIO

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buf.getvalue()


def _png() -> bytes:
    import struct
    import zlib

    def chunk(kind: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + kind
            + body
            + struct.pack(">I", zlib.crc32(kind + body))
        )

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"tEXt", b"Author\0Ana") + chunk(b"IDAT", zlib.compress(b"\0\xff\0\0")) + chunk(b"IEND", b""))  # fmt: skip


def _sqlite(script: str) -> bytes:
    import sqlite3
    import tempfile

    path = Path(tempfile.mkdtemp()) / "t.db"
    con = sqlite3.connect(path)
    con.executescript(script)
    con.commit()
    con.close()
    return path.read_bytes()


def _tar(files: dict[str, str]) -> bytes:
    import io
    import tarfile

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


#: files an add-on needs in the pile besides the default, by add-on
PILE_EXTRA: dict[str, dict[str, bytes]] = {
    "scrub": {"photo.png": _png()},
    # an entry with no permitted copy: almanac-keep answers before any fetch
    "almanac-keep": {
        "catalog.json": b'{"entries": [{"id": "tides", "status": "dark", '
        b'"recovery": [{"url": "https://x.example/", "permission": "excluded"}]}]}'
    },
}

#: one small readable file per reader, by the name it is written under
READERS: dict[str, tuple[str, dict[str, bytes]]] = {
    "agent-transcript": ("agent_transcript.py", {"sess.jsonl": (
        b'{"type":"user","sessionId":"s1","origin":{"kind":"human"},'
        b'"message":{"role":"user","content":"When is the dentist?"}}\n'
        b'{"type":"assistant","sessionId":"s1","message":{"role":"assistant",'
        b'"content":[{"type":"text","text":"Tuesday at 3."}]}}\n')}),
    "corpus-lens": ("corpus_lens.py", {"report.md": (
        b"# corpuslens report\n\n"
        b"- **steering_density** - 70.0% of your prompt turns arrive mid-task.\n"
        b"- **composition_mix** - You authored code in 0.0% of your prompts.\n")}),
    "codebase-memory": ("codebase_memory.py", {"graph.db": _sqlite(
        "CREATE TABLE symbols (fqn TEXT, name TEXT, kind TEXT, file_path TEXT, "
        "start_line INTEGER);\n"
        "CREATE TABLE edges (source_fqn TEXT, target_fqn TEXT, edge_type TEXT);\n"
        "INSERT INTO symbols VALUES ('mod.run','run','function','mod.py',10);\n"
    )}),
    "nestor": ("nestor.py", {"nestor.db": _sqlite(
        "CREATE TABLE tm_pairs (source_text TEXT, verifier TEXT, status TEXT, "
        "created_at TEXT);\n"
        "INSERT INTO tm_pairs VALUES ('tomatoes want sun','ada','sealed',"
        "'2026-10-01');\n"
    )}),
    "almanac": ("almanac.py", {"catalog.json": (
        '{"name": "Made-Up Almanac", "entries": [{"id": "tide-gauge-records", '
        '"title": "Tide Gauge Records", "source": {"canonical_url": '
        '"https://stats.example.org/tides"}, "status": "live"}]}\n').encode()}),
    "books": ("books.py", {"My Clippings.txt": (
        "Made-Up Harbour (Ada Example)\n- Your Highlight on page 12 | Location 180 | "
        "Added on Sunday, 3 March 2024 10:15:22\n\nThe tide keeps its own calendar.\n"
        "==========\n").encode()}),
    "calendar": ("cal.py", {"home.ics": (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nDTSTART:20261028T140000Z\r\n"
        "SUMMARY:Dentist\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n").encode()}),
    "chats": ("chats.py", {"chat.txt": (
        "[13/12/2024, 08:10:00] Dev Raman: I can do 600 tonight\n"
        "[13/12/2024, 08:11:00] Ada: Done\n").encode()}),
    "mail": ("mail.py", {"roof.eml": (
        "From: Ada Example <ada@example.org>\nDate: Thu, 14 Oct 2026 09:15:00 +0100\n"
        "Subject: Roof estimate\n\nThe estimate is in.\n").encode()}),
    "bibtex": ("bibtex.py", {"refs.bib": (
        b'% a comment\n@string{jms = "Journal of Made-Up Studies"}\n@article{smith2020,\n  author = {Example, Ada and Sample, Cy},\n'
        b'  title = {Tides of the {E}stuary},\n  journal = jms,\n  year = 2020, volume = {12}, number = {3}, pages = {45--67},\n'
        b'  doi = "10.1000/xyz123", keywords = {tides, estuaries},\n  abstract = {We measure the tide at six harbours.}\n}\n'
    )}),
    "rtf": ("rtf.py", {"letter.rtf": (
        b"{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Arial;}}{\\colortbl;\\red0\\green0\\blue0;}"
        b"\\pard\\b The roof\\b0  is fixed.\\par\nBills go out on Thursday.\\par}"
    )}),
    "jupyter": ("jupyter.py", {"tides.ipynb": (
        b'{"nbformat": 4, "nbformat_minor": 5, "metadata": {"kernelspec": {"name": "python3", "display_name": "Tide analysis"}, "language_info": {"name": "python"}},'
        b' "cells": [{"cell_type": "markdown", "source": ["# Tides at the estuary\\n", "Six harbours."]},'
        b' {"cell_type": "code", "source": "df = load(\\"harbours.csv\\")\\nprint(len(df))", "outputs": [{"output_type": "stream", "name": "stdout", "text": ["6 rows\\n"]},'
        b' {"output_type": "display_data", "data": {"image/png": "iVBORw0KGgo=", "text/plain": ["<Figure size 640x480>"]}}]}]}'
    )}),
    "latex": ("latex.py", {"main.tex": (
        b"\\documentclass{article}\n\\usepackage{amsmath}\n\\title{Tides of the Estuary}\n\\author{Ada Example}\n\\begin{document}\n\\maketitle\n"
        b"\\section{Method}\\label{sec:m}\nWe measure the tide at six harbours \\cite{smith2020}. % a comment\n"
        b"The result is $x = 1$ and\n\\begin{equation}\ny = mx + b\n\\end{equation}\nholds \\emph{everywhere}.\n\\end{document}\n"
    )}),
    "pgn": ("pgn.py", {"club.pgn": (
        b'[Event "Club Championship"]\n[Site "Leeds"]\n[Date "2024.03.03"]\n[White "Ada Example"]\n[Black "Cy Sample"]\n[Result "1-0"]\n[ECO "B20"]\n[Opening "Sicilian Defense"]\n\n'
        b'1. e4 {My usual start.} c5 2. Nf3 d6 (2... Nc6 {Also fine}) 3. d4 cxd4 4. Nxd4 Nf6 14. Qd7 {I missed the fork here.} 1-0\n'
    )}),
    "chordpro": ("chordpro.py", {"estuary.cho": (
        b"{title: Down by the Estuary}\n{artist: Ada Example}\n{key: G}\n{capo: 2}\n# a comment\n\n{start_of_verse}\n"
        b"[G]Down by the [C]estuary the [D]tide comes [Em]in\n{end_of_verse}\n{soc}\nOh, the [G]water, the [D]water\n{eoc}\n"
    )}),
    "places": ("places.py", {"leeds.kml": (
        b'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Leeds</name><Folder><name>Plots</name>'
        b'<Placemark><name>Allotment</name><description><![CDATA[<p>Plot 14, the <b>gate</b> sticks.</p>]]></description>'
        b'<Point><coordinates>-1.5491,53.8008,0</coordinates></Point></Placemark></Folder></Document></kml>'
    )}),
    "evernote": ("evernote.py", {"Garden.enex": (
        b'<?xml version="1.0" encoding="UTF-8"?><en-export export-date="20240306T000000Z"><note><title>Allotment plan</title>'
        b'<content><![CDATA[<?xml version="1.0" encoding="UTF-8"?><en-note><div>Plot 14 gets the beans.</div><div><en-todo checked="true"/>Order seed</div><div><en-todo/>Fix the gate</div></en-note>]]></content>'
        b'<created>20240303T101500Z</created><updated>20240305T080000Z</updated><tag>garden</tag><tag>plots</tag>'
        b'<note-attributes><author>Ada Example</author><source-url>https://example.org/plots</source-url></note-attributes>'
        b'<resource><resource-attributes><file-name>plan.pdf</file-name></resource-attributes></resource></note></en-export>'
    )}),
    "family-tree": ("family_tree.py", {"family.ged": (
        b"0 HEAD\n1 CHAR UTF-8\n0 @I1@ INDI\n1 NAME John /Smith/\n1 BIRT\n2 DATE 2 Mar 1850\n2 PLAC Leeds\n1 DEAT\n2 DATE 1920\n2 PLAC York\n"
        b"1 FAMC @F1@\n1 FAMS @F2@\n1 NOTE A weaver\n2 CONC  and a singer.\n2 CONT Second line.\n"
        b"0 @I2@ INDI\n1 NAME Mary /Brown/\n1 FAMS @F2@\n0 @I4@ INDI\n1 NAME Arthur /Smith/\n0 @I5@ INDI\n1 NAME Ann /Jones/\n"
        b"0 @F1@ FAM\n1 HUSB @I4@\n1 WIFE @I5@\n1 CHIL @I1@\n0 @F2@ FAM\n1 HUSB @I1@\n1 WIFE @I2@\n1 MARR\n2 DATE 1875\n2 PLAC Hull\n0 TRLR\n"
    )}),
    "mediawiki": ("mediawiki.py", {"dump.xml": (
        b'<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/" version="0.10"><siteinfo><sitename>Garden</sitename></siteinfo>'
        b'<page><title>Tomatoes</title><ns>0</ns><id>1</id><revision><timestamp>2024-01-01T10:00:00Z</timestamp><text xml:space="preserve">old text</text></revision>'
        b'<revision><timestamp>2024-03-03T10:00:00Z</timestamp><text xml:space="preserve">\'\'\'Tomatoes\'\'\' want [[sun|six hours of sun]].{{cite|x}}&lt;ref&gt;n&lt;/ref&gt;\n== Growing ==\n* plant in [[Bed 2]]\n[[Category:Veg]]</text></revision></page>'
        b'<page><title>Maters</title><ns>0</ns><id>2</id><revision><timestamp>2024-02-02T00:00:00Z</timestamp><text>#REDIRECT [[Tomatoes]]</text></revision></page></mediawiki>'
    )}),
    "screenplay": ("screenplay.py", {"garden.fountain": (
        b"Title: Garden Party\nAuthor: Ana Example\n\n"
        b"INT. KITCHEN - DAY #1#\n\nAna waters the tomatoes.\n\nANA\nSix hours of sun.\n\nBEN (V.O.)\n(dryly)\nOr so she says.\n\n"
        b"CUT TO:\n\n.EXT. GARDEN - NIGHT\n\n[[a note]]The moon /* hidden */ rises.\n"
    )}),
    "musicxml": ("musicxml.py", {"song.musicxml": (
        b'<?xml version="1.0"?><score-partwise version="3.1"><work><work-title>Evening Song</work-title></work>'
        b'<identification><creator type="composer">Ana Example</creator><creator type="lyricist">Ben Sample</creator></identification>'
        b'<part-list><score-part id="P1"><part-name>Soprano</part-name></score-part></part-list>'
        b'<part id="P1"><measure number="1"><attributes><key><fifths>1</fifths><mode>major</mode></key><time><beats>3</beats><beat-type>4</beat-type></time></attributes>'
        b'<direction><direction-type><words>Andante</words></direction-type><sound tempo="72"/></direction>'
        b'<direction><direction-type><dynamics><p/></dynamics></direction-type></direction>'
        b'<note><pitch><step>G</step><octave>4</octave></pitch><lyric number="1"><syllabic>begin</syllabic><text>Ev</text></lyric></note>'
        b'<note><pitch><step>A</step><octave>4</octave></pitch><lyric number="1"><syllabic>end</syllabic><text>ening</text></lyric></note>'
        b'<note><pitch><step>B</step><octave>4</octave></pitch><lyric number="1"><syllabic>single</syllabic><text>comes</text></lyric><lyric number="2"><syllabic>single</syllabic><text>Morn</text></lyric></note></measure></part></score-partwise>'
    )}),
    "joplin": ("joplin.py", {"notes.jex": (
        _tar({
        "aaa.md": "Garden\n\nid: aaa\nparent_id: \ncreated_time: 2024-01-01T00:00:00.000Z\ntype_: 2",
        "bbb.md": "Veg\n\nid: bbb\nparent_id: aaa\ntype_: 2",
        "n1.md": "Tomato notes\n\nPlant out after the last frost.\nSecond line.\n\nid: n1\nparent_id: bbb\ncreated_time: 2024-03-02T08:00:00.000Z\nupdated_time: 2024-03-05T09:30:00.000Z\ndeleted_time: 0\ntype_: 1",
        "n2.md": "Bin day\n\nid: n2\nparent_id: \ncreated_time: 2024-04-01T00:00:00.000Z\ntype_: 1",
        "gone.md": "Old\n\nrubbish\n\nid: g\nparent_id: bbb\ndeleted_time: 1710000000000\ntype_: 1",
        "tag.md": "mytag\n\nid: t\ntype_: 5",
        "resources/pic.png": "not markdown",
        })
    )}),
    "day-one": ("day_one.py", {"Journal.json": (
        b'{"metadata":{"version":"1.0"},"entries":['
        b'{"creationDate":"2024-03-03T09:00:00Z","text":"Second entry\\\\.","tags":["garden","spring"],"starred":true,"location":{"placeName":"Kitchen","localityName":"Leeds","country":"United Kingdom"},"weather":{"conditionsDescription":"Cloudy","temperatureCelsius":7.6}},'
        b'{"creationDate":"2024-03-02T08:15:00Z","text":"Planted out the tomatoes. It was 5\\\\-6 degrees\\\\!"},'
        b'{"creationDate":"2024-03-01T00:00:00Z","text":"  "}]}'
    )}),
    "google-keep": ("google_keep.py", {"Shopping.json": (
        b'{"color":"DEFAULT","isTrashed":false,"isPinned":true,"title":"Shopping","userEditedTimestampUsec":1710000000000000,"createdTimestampUsec":1709380000000000,'
        b'"labels":[{"name":"home"},{"name":"food"}],"listContent":[{"text":"milk","isChecked":false},{"text":"eggs","isChecked":true},{"text":" ","isChecked":false}]}'
    )}),
    "karakeep": ("karakeep.py", {"karakeep.json": (
        b'{"bookmarks":[{"createdAt":1710000000,"title":"Tomato growing guide","tags":["garden",{"name":"veg"}],"note":"Read the  staking section.","summary":"How to grow tomatoes.",'
        b'"content":{"type":"link","url":"https://example.org/tomatoes","description":"A guide\\nto tomatoes."}},'
        b'{"createdAt":"2024-02-01T10:00:00Z","title":"","content":{"type":"text","text":"Remember   the basil."}}]}'
    )}),
    "wallabag": ("wallabag.py", {"wallabag.json": (
        b'[{"title":"Tomato growing guide","url":"https://example.org/tomatoes","created_at":"2024-03-02T10:00:00+0000","tags":["garden",{"label":"veg"},5],'
        b'"content":"<p>Plant   after <b>frost</b>.</p><script>x()</script><p>Stake early.</p>","annotations":[{"quote":"Stake early.","text":"do this in April"}]},'
        b'{"title":"","url":"https://example.org/older","created_at":"2024-01-01T00:00:00+0000","content":"<p>Old &amp; dusty.</p>"}, 7]'
    )}),
    "sarif": ("sarif.py", {"codeql.sarif": (
        b'{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"CodeQL","rules":[{"id":"py/sql-injection","shortDescription":{"text":"SQL injection"}}]}},"results":['
        b'{"ruleId":"py/xss","level":"warning","message":{"text":"Reflected   XSS."},"locations":[{"physicalLocation":{"artifactLocation":{"uri":"src/web.py"},"region":{"startLine":7}}}]},'
        b'{"ruleId":"py/sql-injection","level":"error","message":{"text":"This query depends on a user-provided value."},"locations":[{"physicalLocation":{"artifactLocation":{"uri":"src/db.py"},"region":{"startLine":42}}}]},'
        b'{"ruleId":"py/other","message":{"markdown":"Plain **md**"}}]}]}'
    )}),
    "sbom": ("sbom.py", {"sbom.json": (
        b'{"bomFormat":"CycloneDX","specVersion":"1.5","metadata":{"component":{"name":"garden-app","version":"1.0"}},"components":['
        b'{"name":"urllib3","version":"2.0.7","purl":"pkg:pypi/urllib3@2.0.7","licenses":[{"expression":"MIT OR Apache-2.0"}]},'
        b'{"name":"requests","version":"2.31.0","purl":"pkg:pypi/requests@2.31.0","licenses":[{"license":{"id":"Apache-2.0"}}]},'
        b'{"name":"legacy-lib"},{"group":"org.x","name":"Tool","version":"3","licenses":[{"license":{"name":"Custom"}},5]}]}'
    )}),
    "mastodon": ("mastodon.py", {"outbox.json": (
        b'{"type":"OrderedCollection","orderedItems":['
        b'{"type":"Create","published":"2024-03-03T19:40:00Z","object":{"type":"Note","summary":"gardening","content":"<p>The slugs are <b>winning</b>.</p>","inReplyTo":"https://x/1",'
        b'"attachment":[{"type":"Document","mediaType":"image/jpeg","name":"slug on a leaf"},{"type":"Document","mediaType":"video/mp4","name":"clip"},{"mediaType":"image/png"}]}},'
        b'{"type":"Announce","published":"2024-03-02T10:00:00Z","object":"https://x/2"},'
        b'{"type":"Create","published":"2024-03-02T08:15:00Z","object":{"type":"Note","content":"<p>Planted out the tomatoes   today.</p>"}}]}'
    )}),
    "x-archive": ("x_archive.py", {"tweets.js": (
        b'window.YTD.tweets.part0 = [ {"tweet": {"created_at": "Wed Mar 02 08:15:00 +0000 2022", "full_text": "Planted out the tomatoes. https://t.co/abc &amp; more",'
        b' "entities": {"urls": [{"url": "https://t.co/abc", "expanded_url": "https://example.org/guide"}]}}},'
        b' {"tweet": {"created_at": "Thu Mar 03 19:40:00 -0500 2022", "full_text": "@ana the slugs are winning.", "in_reply_to_status_id_str": "123"}} ]'
    )}),
    "irc": ("irc.py", {"irc.libera.#garden.weechatlog": (
        b"2024-03-02 08:15:30\tana\tSix hours of sun, I read.\n2024-03-02 08:15:50\t--> \tben (~b@host) has joined #garden\n"
        b"2024-03-02 08:16:01\t *\tben waves\n2024-03-03 19:40:00\tben\tThe slugs are winning.\n"
    )}),
    "listening": ("listening.py", {"StreamingHistory0.json": (
        b'[{"endTime":"2024-03-02 09:02","artistName":"Nina Simone","trackName":"Sinnerman","msPlayed":620000},'
        b'{"endTime":"2024-03-02 08:15","artistName":"X","trackName":"Skipped","msPlayed":29999},'
        b'{"ts":"2024-03-02T07:30:00Z","master_metadata_track_name":"Feeling Good","master_metadata_album_artist_name":"Nina Simone","ms_played":175500},'
        b'{"ts":"2024-03-03T10:00:00Z","episode_name":"Staking tomatoes","episode_show_name":"Garden Radio","ms_played":1450000},'
        b'{"ts":"2024-03-03T11:00:00Z","ms_played":60000}]'
    )}),
    "lockfiles": ("lockfiles.py", {"package-lock.json": (
        b'{"lockfileVersion":3,"packages":{"":{"name":"app","version":"1.0.0"},"node_modules/lodash":{"version":"4.17.21","resolved":"x","integrity":"y"},'
        b'"node_modules/left-pad":{"version":"1.3.0"},"node_modules/a/node_modules/left-pad":{"version":"0.0.3"},"node_modules/@scope/pkg":{"version":"2.0.0"},"node_modules/bad":{}}}'
    )}),
    "man-pages": ("man_pages.py", {"ls.1": (
        b'.\\" a comment\n.TH LS 1 "March 2024" "coreutils" "User Commands"\n.SH NAME\nls \\- list directory contents\n.SH SYNOPSIS\n.B ls\n[\\fIOPTION\\fR]... [\\fIFILE\\fR]...\n'
        b'.SH DESCRIPTION\nList information about the \\fBFILE\\fRs.\n.TP\n.BR \\-a ", " \\-\\-all\ndo not ignore entries starting with \\&.\n.PP\nSecond \\(em paragraph.\n'
    )}),
    "matrix": ("matrix.py", {"room.json": (
        b'{"room_name":"Garden Club","topic":"Plants","messages":['
        b'{"type":"m.room.message","sender":"@ben:example.org","origin_server_ts":1709367360000,"content":{"msgtype":"m.emote","body":"waves"}},'
        b'{"type":"m.room.message","sender":"@ana:example.org","origin_server_ts":1709367300000,"content":{"msgtype":"m.text","body":"Six  hours of sun."}},'
        b'{"type":"m.room.member","sender":"@ben:example.org","origin_server_ts":1709367000000,"content":{"membership":"join"}},'
        b'{"type":"m.room.message","sender":"@ana:example.org","origin_server_ts":1709367400000,"content":{"msgtype":"m.image","body":"tomato.png"}},'
        b'{"type":"m.room.message","sender":"@ana:example.org","origin_server_ts":1709367500000,"content":{"msgtype":"m.text","body":""}}]}'
    )}),
    "trello": ("trello.py", {"garden.json": (
        b'{"name":"Garden","lists":[{"id":"l1","name":"To do"},{"id":"l2","name":"Done"},{"id":"l3","name":"Old","closed":true}],'
        b'"cards":[{"id":"c1","idList":"l1","name":"Stake the tomatoes","desc":"Use the  long canes.","due":"2024-03-09T12:00:00.000Z","labels":[{"name":"urgent"},{"name":""},{"name":"veg"}],"idChecklists":["k1"]},'
        b'{"id":"c2","idList":"l2","name":"Order seed"},{"id":"c3","idList":"l1","name":"Archived","closed":true},{"id":"c4","idList":"l3","name":"In a closed list"}],'
        b'"checklists":[{"id":"k1","name":"Tools","checkItems":[{"name":"canes","state":"complete"},{"name":"twine","state":"incomplete"}]}],'
        b'"actions":[{"type":"commentCard","date":"2024-03-02T08:00:00.000Z","data":{"text":"Borrow Ben\'s.","card":{"id":"c1"}},"memberCreator":{"fullName":"Ana"}},'
        b'{"type":"updateCard","data":{"card":{"id":"c1"}}}]}'
    )}),
    "gh-json": ("gh_json.py", {"issues.json": (
        b'[{"number":14,"title":"Move tomatoes to bed 2","state":"MERGED","createdAt":"2024-03-04T09:00:00Z","author":{"login":"ben"},"headRefName":"bed-2","mergedAt":"2024-03-05T10:00:00Z"},'
        b'{"number":12,"title":"Tomatoes want more sun","state":"OPEN","createdAt":"2024-03-02T08:15:00Z","author":{"login":"ana"},"body":"The bed by the  fence\\nis shaded.",'
        b'"labels":[{"name":"bug"},{"name":"garden"}],"comments":[{"author":{"login":"ben"},"createdAt":"2024-03-03T10:00:00Z","body":"Move them."},{"body":" "}]},'
        b'{"databaseId":1234,"name":"ci","workflowName":"CI","conclusion":"failure","headBranch":"main","createdAt":"2024-03-04T09:30:00Z","displayTitle":"Move tomatoes"}]'
    )}),
    "meta-archive": ("meta_archive.py", {"message_1.json": (
        b'{"participants":[{"name":"Ana"},{"name":"Ben"}],"title":"Garden chat","messages":['
        b'{"sender_name":"Ben","timestamp_ms":1709370000000,"content":"Caf\xc3\x83\xc2\xa9 later?"},'
        b'{"sender_name":"Ana","timestamp_ms":1709367300000,"content":"Six  hours of sun."},{"sender_name":"Ana","timestamp_ms":1709367400000,"photos":[{}]}]}'
    )}),
    "location-history": ("location_history.py", {"2024_MARCH.json": (
        b'{"timelineObjects":[{"activitySegment":{"activityType":"WALKING","distance":1500,"duration":{"startTimestamp":"2024-03-02T09:10:00Z","endTimestamp":"2024-03-02T09:40:00Z"}}},'
        b'{"placeVisit":{"location":{"name":"Kitchen Cafe","address":"1 High St, Leeds"},"duration":{"startTimestamp":"2024-03-02T08:15:00.000Z","endTimestamp":"2024-03-02T09:10:00.000Z"}}},'
        b'{"placeVisit":{"location":{},"duration":{"startTimestamp":"2024-03-02T23:00:00Z","endTimestamp":"2024-03-03T07:00:00Z"}}},{"placeVisit":{"duration":{}}}]}'
    )}),
    "slack": ("slack.py", {"slack.zip": (
        _zip({
        "users.json": '[{"id":"U1","name":"ana","real_name":"Ana Lopez","profile":{"display_name":"ana"}},{"id":"U2","name":"ben","real_name":"Ben Ruiz","profile":{"display_name":""}}]',
        "channels.json": '[{"id":"C1","name":"garden"}]',
        "garden/2024-03-02.json": '[{"type":"message","user":"U1","text":"Six hours of sun, <@U2>? &amp; <#C1|garden>","ts":"1709367300.000100"},'
        '{"type":"message","user":"U2","text":"See <https://example.org/guide|the guide> <!here>","ts":"1709367360.000200"},'
        '{"type":"message","subtype":"channel_join","user":"U2","text":"<@U2> has joined","ts":"1709367000.000000"},'
        '{"type":"message","user":"U3","text":"","ts":"1709367400.0"}]',
        "garden/2024-03-03.json": '[{"type":"message","subtype":"me_message","user":"U1","text":"waves","ts":"1709460000.0"}]',
        })
    )}),
    "discord": ("discord.py", {"discord.zip": (
        _zip({
        "Messages/index.json": '{"123": "Direct Message with ben", "456": "garden"}',
        "Messages/c123/channel.json": '{"id":"123","type":1}',
        "Messages/c123/messages.json": '[{"ID":"1","Timestamp":"2024-03-02 08:16:00","Contents":"See you  Saturday.","Attachments":""},{"ID":"2","Timestamp":"2024-03-02 08:20:00","Contents":"","Attachments":"https://cdn/x.png"},{"ID":"3","Timestamp":"2024-03-02 08:21:00","Contents":"","Attachments":""}]',
        "Messages/c456/channel.json": '{"id":"456","type":0,"name":"garden","guild":{"id":"9","name":"Garden Club"}}',
        "Messages/c456/messages.csv": 'ID,Timestamp,Contents,Attachments\n7,2024-03-02 08:15:30,"Six hours of sun.",\n',
        })
    )}),
    "notion": ("notion.py", {"notion.zip": (
        _zip({
        "Garden 0123456789abcdef0123456789abcdef.md": "# Garden\n\nIntro.\n",
        "Garden/Veg 11111111111111111111111111111111/Tomato notes 22222222222222222222222222222222.md": "# Tomato notes\n\nCreated: March 2, 2024 8:15 AM\nPlant out after the last frost.\n",
        "Garden/Seed orders 33333333333333333333333333333333.csv": "Name,Qty,Supplier\nBasil,3,Seeds Ltd\n,,\n",
        "Garden/photo.png": "not text",
        })
    )}),
    "code-comments": ("code_comments.py", {"cache.py": (
        b'"""Module docstring.\n\nSecond line."""\n# A cache of parsed answers.\nTTL = 60  # seconds an entry lives\ns = "# not a comment"\n\n\ndef f():\n    """Do the thing."""\n    return 1\n'
    )}),
    "ci-logs": ("ci_logs.py", {"run.log": (
        b"2026-10-29T03:28:14.1000000Z ##[group]Run actions/checkout@v7\n2026-10-29T03:28:14.2000000Z with:\n2026-10-29T03:28:14.3000000Z ##[endgroup]\n"
        b"2026-10-29T03:28:15.0000000Z ##[group]Run pytest\n2026-10-29T03:28:15.5000000Z \x1b[31mFAILED\x1b[0m tests/test_garden.py::test_sun - assert 5 == 6\n"
        b"2026-10-29T03:28:16.0000000Z ===== 1 failed, 40 passed in 2.31s =====\n2026-10-29T03:28:17.0000000Z ##[error]Process completed with exit code 1.\n"
        b"2026-10-29T03:28:18.0000000Z Post job cleanup.\n"
    )}),
    "health": ("health.py", {"export.xml": (
        b'<?xml version="1.0"?><HealthData locale="en_GB"><Record type="HKQuantityTypeIdentifierStepCount" unit="count" startDate="2024-03-02 07:00:00 +0000" value="5000"/>'
        b'<Record type="HKQuantityTypeIdentifierStepCount" unit="count" startDate="2024-03-02 12:00:00 +0000" value="3123"/>'
        b'<Record type="HKQuantityTypeIdentifierDistanceWalkingRunning" unit="mi" startDate="2024-03-02 07:00:00 +0000" value="3.6"/>'
        b'<Record type="HKQuantityTypeIdentifierHeartRate" unit="count/min" startDate="2024-03-02 07:00:00 +0000" value="70"/>'
        b'<Record type="HKQuantityTypeIdentifierHeartRate" unit="count/min" startDate="2024-03-02 08:00:00 +0000" value="72"/>'
        b'<Record type="HKQuantityTypeIdentifierBodyMass" unit="lb" startDate="2024-03-02 06:00:00 +0000" value="160"/>'
        b'<Record type="HKQuantityTypeIdentifierBodyMass" unit="kg" startDate="2024-03-02 09:00:00 +0000" value="72.4"/>'
        b'<Record type="HKQuantityTypeIdentifierStepCount" unit="count" startDate="2024-03-03 07:00:00 +0000" value="10442"/>'
        b'<Record type="HKCategoryTypeIdentifierSleepAnalysis" startDate="2024-03-03 01:00:00 +0000" value="HKCategoryValueSleepAnalysisAsleep"/>'
        b'<Workout workoutActivityType="HKWorkoutActivityTypeRunning" startDate="2024-03-03 07:00:00 +0000"/></HealthData>'
    )}),
    "home-sensors": ("home_sensors.py", {"history.json": (
        b'[[{"entity_id":"sensor.kitchen_temp","state":"21.0","last_changed":"2024-03-02T08:00:00+00:00","attributes":{"unit_of_measurement":"C","friendly_name":"Kitchen temperature"}},'
        b'{"entity_id":"sensor.kitchen_temp","state":"21.8","last_changed":"2024-03-02T20:00:00+00:00","attributes":{}},'
        b'{"entity_id":"sensor.kitchen_temp","state":"unavailable","last_changed":"2024-03-02T21:00:00+00:00"},'
        b'{"entity_id":"sensor.kitchen_temp","state":"20.9","last_changed":"2024-03-03T08:00:00+00:00"}],'
        b'[{"entity_id":"sensor.hall_humidity","state":"48.5","last_changed":"2024-03-02T09:00:00+00:00","attributes":{"unit_of_measurement":"%","friendly_name":"Hall, humidity"}}],'
        b'[{"entity_id":"light.hall","state":"on","last_changed":"2024-03-02T09:00:00+00:00"}]]'
    )}),
    "jira": ("jira.py", {"export.xml": (
        b'<rss version="0.92"><channel><item><title>[GARDEN-12] Tomatoes want more sun</title><key id="1">GARDEN-12</key><summary>Tomatoes want more sun</summary>'
        b'<type>Bug</type><status>Open</status><reporter username="a">ana</reporter><assignee username="b">ben</assignee><created>Sat, 2 Mar 2024 08:15:00 +0000</created>'
        b'<description>&lt;p&gt;The bed by the  fence is shaded.&lt;/p&gt;</description><labels><label>garden</label><label>urgent</label></labels>'
        b'<comments><comment id="1" author="ben" created="Sun, 3 Mar 2024 10:00:00 +0000">Move them to bed 2.</comment></comments></item>'
        b'<item><title>[GARDEN-3] Order seed</title><key id="2">GARDEN-3</key><type>Task</type><status>Done</status><reporter>cy</reporter><assignee>Unassigned</assignee><created>Fri, 1 Mar 2024 09:00:00 +0000</created></item></channel></rss>'
    )}),
    "letterboxd": ("letterboxd.py", {"diary.csv": (
        b'Date,Name,Year,Letterboxd URI,Rating,Rewatch,Review,Tags,Watched Date\n'
        b'2024-03-05,Heat,1995,https://boxd.it/1,4.5,Yes,,"crime, night",2024-03-02\n'
        b'2024-03-10,Paddington 2,2017,https://boxd.it/2,4,,Funnier than it has   any right to be.,,2024-03-09\n'
    )}),
    "goodreads": ("goodreads.py", {"goodreads_library_export.csv": (
        b'Book Id,Title,Author,My Rating,Date Read,Date Added,Bookshelves,Exclusive Shelf,My Review,Private Notes\n'
        b'1,The Hobbit,J.R.R. Tolkien,4,2024/03/02,2023/01/05,"fantasy, favourites",read,A comfort   read.,secret\n'
        b'2,Dune,Frank Herbert,0,,2024/03/09,,currently-reading,,\n'
        b'3,Piranesi,Susanna Clarke,0,,2023/12/01,,to-read,,\n'
    )}),
    "linkedin": ("linkedin.py", {"messages.csv": (
        b'CONVERSATION ID,CONVERSATION TITLE,FROM,SENDER PROFILE URL,TO,RECIPIENT PROFILE URLS,DATE,SUBJECT,CONTENT,FOLDER\n'
        b'c1,,Ana Lopez,https://x/a,Ben Ruiz,https://x/b,2024-03-02 08:15:30 UTC,Garden talk,Are you   coming on Saturday?,INBOX\n'
        b'c1,,Ben Ruiz,https://x/b,Ana Lopez,https://x/a,2024-03-02 08:20:00 UTC,,Yes!,SENT\n'
        b'c2,,Cy,https://x/c,Ben Ruiz,https://x/b,2024-03-01 09:00:00 UTC,,,INBOX\n'
    )}),
    "reddit": ("reddit.py", {"posts.csv": (
        b'id,permalink,date,ip,subreddit,gildings,title,url,body\n'
        b'abc,https://www.reddit.com/r/gardening/comments/abc/,2024-03-02 08:15:30 UTC,1.2.3.4,gardening,0,Tomatoes want more sun,,The bed by the   fence is shaded.\n'
        b'def,https://www.reddit.com/r/gardening/comments/def/,2024-03-01 09:00:00 UTC,1.2.3.4,gardening,0,Link only,https://example.org,\n'
    )}),
    "orders": ("orders.py", {"Retail.OrderHistory.1.csv": (
        b'Website,Order ID,Order Date,Currency,Unit Price,Total Owed,Product Name,Order Status\n'
        b'Amazon.co.uk,026-1234567-8901234,2024-03-02T08:15:00Z,GBP,4.5,"4.50",Basil seeds,   3 packets,Closed\n'
        b'Amazon.co.uk,026-7654321-0987654,2024-03-09T10:00:00Z,GBP,6.99,6.99,Garden twine,Closed\n'
    )}),
    "bank": ("bank.py", {"statement.csv": (
        b'Date,Description,Amount,Balance\n2024-03-05,ACME PAYROLL,2000.00,3000.00\n2024-03-02,TESCO STORES 3241,-45.20,1000.00\n'
    )}),
    "readwise": ("readwise.py", {"readwise-data.csv": (
        b'Highlight,Book Title,Book Author,Amazon Book ID,Note,Color,Tags,Location Type,Location,Highlighted at\n'
        b'"In a hole in the ground there lived a hobbit.",The Hobbit,J.R.R. Tolkien,B1,the best   opening,yellow,fantasy,location,120,2024-03-02 08:15:00\n'
        b'Tie the stem loosely.,Staking tomatoes,Ana Lopez,,,,,,,2024-03-04T10:00:00Z\n'
    )}),
    "logs": ("logs.py", {"syslog.log": (
        b"Mar  2 08:15:30 host sshd[1234]: Accepted publickey for ana from 10.0.0.2\nMar  2 08:16:01 host cron: (root) CMD (run-parts /etc/cron.hourly)\n"
        b"    at stack frame\n2024-03-02T08:17:00.123456+00:00 host app[7]: started\n"
    )}),
    "notes": ("notes.py", {"garden.md": b"Tomatoes want [[sun]].\n"}),
    "shell-history": ("shell_history.py", {"zsh_history": (
        b": 1709460900:0;git push\n: 1709461000:0;rsync -a photos/ /mnt/backup/\n"
    )}),
    "jrnl": ("jrnl.py", {"journal.txt": (
        "[2024-03-03 10:15] Fixed the gate.\nThe hinge wanted oil, not force.\n\n"
        "[2024-03-04 09:00] Rain all day.\n").encode()}),
    "office": ("office.py", {"letter.docx": _docx("The roof is fixed.")}),
    "subtitles": ("subtitles.py", {"ep1.srt": (
        "1\n00:00:01,000 --> 00:00:04,000\nThe tide keeps its own calendar.\n"
    ).encode()}),
    "web-pages": ("web_pages.py", {"saved.html": (
        "<!-- saved from url=(0020)https://example.org/ -->\n"
        "<p>The roof is fixed.</p>\n").encode()}),
    "clauses": ("clauses.py", {"terms.html": (
        "<h1>Terms</h1><p>We keep your data. We delete it on request.</p>\n").encode()}),
}  # fmt: skip

#: the language packs' codes: a pack is words- and its language's ISO 639 code
LANGUAGES = sorted(p.name[6:] for p in STDLIB.glob("words-*") if re.fullmatch(r"words-[a-z]{2,3}", p.name))  # fmt: skip

#: a command that works, for each add-on a person runs; {box}, {pile} and
#: {tmp} are filled in. The repo's own tools (ci, readme, similar, mutants,
#: github) are tested in their own folders.
COMMANDS: dict[str, tuple[str, list[str]]] = {
    "a11y-check": ("a11y_check.py", ["--box", "{box}"]),
    "abbreviations": ("abbreviations.py", ["--box", "{box}", "tomatoes"]),
    "accents": ("accents.py", ["--box", "{box}", "tomatoes"]),
    "amounts": ("amounts.py", ["--box", "{box}"]),
    "invoices": ("invoices.py", ["--box", "{box}", "--id", "INV-\\d+"]),
    "first-mention": ("first_mention.py", ["--box", "{box}", "tomatoes"]),
    "fuzzy-dates": ("fuzzy_dates.py", ["--box", "{box}"]),
    "again": ("again.py", ["--box", "{box}"]),
    "aider": ("aider.py", ["--box", "{box}"]),
    "openai-compatible": ("openai_compatible.py", ["ask", "--box", "{box}", "--url",
                          "http://127.0.0.1:9/v1", "--model", "m", "tomatoes"]),
    "ci-memo": ("ci_memo.py", ["keys", "mutants:accents"]),
    "ci-why": ("ci_why.py", ["--record", "{box}/record.jsonl"]),
    "ci-cache": ("ci_cache.py", ["--from", "{pile}"]),
    "claude-code": ("hook.py", ["setup", "--box", "{box}"]),
    "codex-cli": ("codex_cli.py", ["--box", "{box}"]),
    "copilot": ("copilot.py", ["--box", "{box}"]),
    "cursor": ("cursor.py", ["--box", "{box}"]),
    "daily-word": ("daily_word.py", ["--box", "{box}", "today", *NOW]),
    "debts": ("debts.py", ["--box", "{box}"]),
    "emacs": ("emacs.py", ["--box", "{box}"]),
    "gemini-cli": ("gemini_cli.py", ["--box", "{box}"]),
    "habits": ("habits.py", ["--box", "{box}"]),
    "hosts": ("hosts.py", ["list"]),
    "ids": ("ids.py", ["--box", "{box}"]),
    "jetbrains": ("jetbrains.py", ["--box", "{box}"]),
    "mcp-lite": ("server.py", ["--box", "{box}"]),
    "merkle": ("merkle.py", ["root", "--box", "{box}"]),
    "opencode": ("opencode.py", ["--box", "{box}"]),
    "shell": ("shell.py", ["script", "bash"]),
    "vim": ("vim.py", ["--box", "{box}"]),
    "vscode": ("vscode.py", ["--box", "{box}"]),
    "live": ("live.py", ["list"]),
    "windsurf": ("windsurf.py", ["--box", "{box}"]),
    "zed": ("zed.py", ["--box", "{box}"]),
    "all": ("all.py", ["--box", "{box}", "tomatoes"]),
    "coming-up": ("coming_up.py", ["--box", "{box}", *NOW]),
    "export": ("export.py", ["--box", "{box}"]),
    "gaps": ("gaps.py", ["--box", "{box}", *NOW]),
    "on-this-day": ("on_this_day.py", ["--box", "{box}", *NOW]),
    "pipe": ("pipe.py", ["--box", "{box}", *NOW]),
    "plain": ("plain.py", ["bite", "--box", "{box}", *NOW, "tomatoes"]),
    "privacy": ("privacy.py", ["bite", "--box", "{box}", *NOW, "tomatoes"]),
    "quiz": ("quiz.py", ["--box", "{box}", "ask", *NOW]),
    "quote-check": ("quote_check.py", ["--box", "{box}", "Tomatoes want sun"]),
    "reading-level": ("reading_level.py", ["--box", "{box}"]),
    "renewals": ("renewals.py", ["--box", "{box}", *NOW]),
    "misquote": ("misquote.py", ["--box", "{box}", "Tomatoes want rain"]),
    "quotes": ("quotes.py", ["--box", "{box}", "--in", "{pile}/garden.md"]),
    "almanac-keep": ("keep.py", ["--catalog", "{pile}/catalog.json", "--id", "tides", "--to", "{tmp}/kept"]),
    "claim-check": ("claim_check.py", ["--box", "{box}", "tomatoes want sun"]),
    "policy-watch": ("policy_watch.py", ["--url", "http://127.0.0.1:9/terms", "--to", "{tmp}/w"]),
    "readings": ("readings.py", ["bite", "--box", "{box}", *NOW, "tomatoes"]),
    "advisories": ("advisories.py", ["--box", "{box}"]),
    "outdated": ("outdated.py", ["--box", "{box}"]),
    "typosquat": ("typosquat.py", ["--box", "{box}"]),
    "install-scripts": ("install_scripts.py", ["--box", "{box}"]),
    "agents-md-check": ("agents_md_check.py", ["--box", "{box}"]),
    "instruction-files": ("instruction_files.py", ["--box", "{box}"]),
    "licenses": ("licenses.py", ["--box", "{box}"]),
    "codeowners": ("codeowners.py", ["--box", "{box}", "garden.md"]),
    "in-toto": ("in_toto.py", ["--box", "{box}", "--to", "{tmp}/in-toto.jsonl"]),
    "prov": ("prov.py", ["--box", "{box}", "--to", "{tmp}/prov.json"]),
    "package-contents": ("package_contents.py", ["--box", "{box}"]),
    "pii-audit": ("pii_audit.py", ["--box", "{box}"]),
    "pins": ("pins.py", ["--box", "{box}"]),
    "scan": ("scan.py", ["index", "--from", "{pile}", "--to", "{tmp}/index"]),
    "index-cache": ("index_cache.py", ["--from", "{pile}", "--to", "{tmp}/ix"]),
    "pile-build": ("pile_build.py", ["--from", "{pile}", "--to", "{tmp}/pile.sqlite"]),
    "pile-gold": ("pile_gold.py", ["--box", "{box}", "--questions", "{pile}/garden.md", *NOW]),
    "pile-rank": ("pile_rank.py", ["--from", "{pile}", "tomatoes"]),
    "pile-rungs": ("pile_rungs.py", ["--from", "{pile}", "tomatoes"]),
    "pile-serve": ("pile_serve.py", ["serve", "--from", "{pile}", "--to", "{tmp}/s", "--for", "0"]),
    "pile-sweep": ("pile_sweep.py", ["--box", "{box}", "--questions", "{pile}/garden.md"]),
    "pile-store": ("pile_store.py", ["--from", "{pile}", "--to", "{tmp}/pile.sqlite"]),
    "parallel": ("parallel.py", ["--reader", "notes", "--from", "{pile}", "--to", "{tmp}/pm"]),
    "people": ("people.py", ["--box", "{box}"]),
    "lesson-time": ("lesson_time.py", ["--box", "{box}"]),
    "pair-drift": ("pair_drift.py", ["--box", "{box}"]),
    "slow-tests": ("slow_tests.py", ["--runs", "{pile}"]),
    "snapshot": ("snapshot.py", ["check", "--in", "{pile}"]),
    "wayback": ("wayback.py", ["find", "--url", "https://example.org/", "--to", "{tmp}/w",
                               "--after", "20261016", "--before", "20261001"]),
    "stale": ("stale.py", ["--box", "{box}"]),
    "tip-pin": ("tip_pin.py", ["pin", "--box", "{box}", "--to", "{tmp}/pin.json"]),
    "starter-words": ("starter.py", ["copy", "--to", "{tmp}/words.txt"]),
    "surprise": ("surprise.py", ["--box", "{box}", *NOW]),
    "symptoms": ("symptoms.py", ["--box", "{box}", "tomatoes"]),
    "todo": ("todo.py", ["--box", "{box}"]),
    "contradictions": ("contradictions.py", ["--box", "{box}"]),
    "lending": ("lending.py", ["--box", "{box}"]),
    "timeline": ("timeline.py", ["--box", "{box}", "--to", "{tmp}/timeline.txt", "tomatoes"]),
    "transcript-redact": ("transcript_redact.py", ["--from", "{pile}/garden.md", "--to", "{tmp}/shareable.md"]),
    "across": ("across.py", ["--box", "{box}", "digest"]),
    "stack": ("stack.py", ["--box", "{box}", "--stack", "adapters/stdlib/stack/example.md"]),
    "serve": ("serve.py", ["scope", "--box", "{box}"]),
    "browse": ("browse.py", ["launcher", "--box", "{box}"]),
    "digest": ("digest.py", ["--box", "{box}", *NOW]),
    # every language pack, from its folder: a new one is run here without a line of its own
    **{f"words-{c}": (f"words_{c}.py", ["bite", "--box", "{box}", *NOW, "tomatoes"])
       for c in LANGUAGES},
    "backup": ("backup.py", ["--box", "{box}", "--to", "{tmp}/backups", *NOW]),
    "fixity": ("fixity.py", ["--box", "{box}", *NOW]),
    "format-rot": ("format_rot.py", ["--from", "{pile}"]),
    "git-history": ("git_history.py", ["mirror", "--from", "{pile}", "--to", "{tmp}/gh"]),
    "persona-card": ("persona_card.py", ["--box", "{box}", "--from", "{pile}/garden.md", *NOW]),
    "restore-drill": ("restore_drill.py", ["--from", "{pile}/garden.md"]),
    "session-cost": ("session_cost.py", ["--from", "{pile}"]),
    "three-two-one": ("three_two_one.py", ["--box", "{box}"]),
    "bench": ("bench.py", ["run", "--sizes", "20,40"]),
    "hook-leaks": ("hook_leaks.py", ["check", "--from", "{pile}/garden.md"]),
    "hook-shell": ("hook_shell.py", ["split", "ls -la"]),
    "hook-start": ("hook_start.py", ["--box", "{box}", *NOW]),
    "why-not": ("why_not.py", ["--box", "{box}", "tomatoes"]),
    "fair-merge": ("fair_merge.py", ["--box", "{box}", "tomatoes"]),
    "nicknames": ("nicknames.py", ["--box", "{box}", "--to", "{tmp}/nicknames.txt"]),
    "box-health": ("box_health.py", ["--box", "{box}", *NOW]),
    "profile": ("question_profile.py", ["--box", "{box}", "tomatoes"]),
    "scrub": ("scrub.py", ["--from", "{pile}/photo.png", "--to", "{tmp}/clean.png"]),
    "ro-crate": ("ro_crate.py", ["--box", "{box}", "--to", "{tmp}/crate"]),
    "annotations": ("annotations.py", ["--box", "{box}", "--to", "{tmp}/annotations.json"]),
    "cloudevents": ("cloudevents.py", ["--box", "{box}", "--to", "{tmp}/events.jsonl"]),
    "calendar-out": ("calendar_out.py", ["--box", "{box}", "--to", "{tmp}/coming.ics", *NOW]),
    "rss-out": ("rss_out.py", ["--box", "{box}", "--to", "{tmp}/feed.xml"]),
    "deep-links": ("deep_links.py", ["--box", "{box}"]),
    "braille": ("braille.py", ["--box", "{box}", "--to", "{tmp}/answers.brf"]),
    "llms-txt": ("llms_txt.py", ["write", "--from", "{pile}", "--to", "{tmp}/llms.txt"]),
    "badge": ("badge.py", ["--box", "{box}", "--to", "{tmp}/badge.svg"]),
    "hours": ("hours.py", ["--box", "{box}"]),
    "mileage": ("mileage.py", ["--box", "{box}"]),
    "minutes": ("minutes.py", ["--box", "{box}"]),
    "gradebook": ("gradebook.py", ["--box", "{box}"]),
    "mood": ("mood.py", ["--box", "{box}"]),
    "car": ("car.py", ["--box", "{box}"]),
    "pets": ("pets.py", ["--box", "{box}"]),
    "home-upkeep": ("home_upkeep.py", ["--box", "{box}"]),
    "warranties": ("warranties.py", ["--box", "{box}"]),
    "attendance": ("attendance.py", ["--box", "{box}"]),
    "baby-log": ("baby_log.py", ["--box", "{box}"]),
    "garden": ("garden.py", ["--box", "{box}"]),
    "job-hunt": ("job_hunt.py", ["--box", "{box}"]),
    "hook-compact": ("hook_compact.py", ["--box", "{box}"]),
    "hook-guard": ("hook_guard.py", ["rules"]),
    "hook-impact": ("hook_impact.py", ["check", "--box", "{box}", "{pile}/garden.md"]),
    "hook-stop": ("hook_stop.py", ["check", "--box", "{box}", "--repo", "{tmp}"]),
    "oracle-text": ("oracle_text.py", ["--seed", "demo"]),
    "pile-poetry": ("pile_poetry.py", ["--box", "{box}"]),
    "subscriptions": ("subscriptions.py", ["--box", "{box}"]),
    "reading-log": ("reading_log.py", ["--box", "{box}"]),
    "milestones": ("milestones.py", ["--box", "{box}", "--born", "2020-01-01"]),
    "livestock": ("livestock.py", ["--box", "{box}"]),
    "syllabus": ("syllabus.py", ["--box", "{box}"]),
    "foia": ("foia.py", ["--box", "{box}"]),
    "budget": ("budget.py", ["--box", "{box}"]),
    "launcher": ("launcher.py", ["--box", "{box}"]),
    "history": ("history.py", ["--box", "{box}"]),
    "make-it-so": ("make_it_so.py", ["plan", "--box", "{box}", "--to", "{tmp}/plan.json", "--cmd", "echo hi", "tomatoes"]),
    "dice": ("dice.py", ["--box", "{box}", "roll", "2d6", *NOW]),
    "hook-fail-closed": ("hook_fail_closed.py", ["--hook", "true"]),
    "hook-fuzz": ("hook_fuzz.py", ["--hook", "true"]),
    "hook-pin": ("hook_pin.py", ["--box", "{box}", "approve", "{pile}/garden.md", *NOW]),
    "hook-replay": ("hook_replay.py", ["--box", "{box}", "--to", "{tmp}", "run", "--hook", "true", *NOW]),
    "horoscope": ("horoscope.py", ["Ana", "--date", "2026-10-24"]),
    "life": ("life.py", ["--box", "{box}", "play", "--generations", "8", *NOW]),
    "odds": ("odds.py", ["2d6"]),
    "changed": ("changed.py", ["--box", "{box}", *NOW]),
    "diverge": ("diverge.py", ["{pile}", "{pile}"]),
    "duplicates": ("duplicates.py", ["--box", "{box}"]),
    "secrets-audit": ("secrets_audit.py", ["--box", "{box}"]),
    "risky-code": ("risky_code.py", ["--box", "{box}"]),
    "said": ("said.py", ["--box", "{box}"]),
    "session-seal": ("session_seal.py", ["--box", "{box}", *NOW]),
    "typos": ("typos.py", ["--box", "{box}", "tomatoes"]),
    "xref": ("xref.py", ["--box", "{box}"]),
    "tarot": ("tarot.py", ["--box", "{box}", "draw", *NOW]),
    "test-impact": ("impact.py", ["plan", "README.md"]),
    "print": ("print.py", ["--box", "{box}", "--to", "{tmp}/page.html", *NOW, "tomatoes"]),
    "start": ("start.py", ["--pile", "{pile}", "--to", "{tmp}/willow"]),
    # a list naming no owner/repo builds nothing, before any clone: no network
    "repo-pile": ("repo_pile.py", ["build", "--to", "{tmp}/base", "--repos",
                                   "{pile}/garden.md", "--key", "{tmp}/base.key"]),
    "test-shards": ("shards.py", ["--shards", "2", "--tests", "{pile}/garden.md"]),
    "bot-venv": ("bot_venv.py", ["--venv", "{pile}"]),
    "restack": ("restack.py", ["--onto", "HEAD", "HEAD"]),
    **{name: (script, ["mirror", "--from", "{pile}", "--to", "{tmp}/mirror"])
       for name, (script, _) in READERS.items()},
}  # fmt: skip


def only(names) -> list[str]:
    return [n for n in sorted(names) if not ONLY or n == ONLY]


def run(script: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], stdin=subprocess.DEVNULL,
                          capture_output=True, text=True)  # fmt: skip


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}  # fmt: skip


def test_every_add_on_a_person_runs_is_listed_here():
    """A new add-on with a command line can't slip past these checks."""
    run_by_people = {
        p.parent.name for p in STDLIB.glob("*/*.py")
        if "__main__" in p.read_text(encoding="utf-8") and not p.name.startswith("test_")
    } - {"ci", "readme", "similar", "mutants", "github"}  # fmt: skip
    assert run_by_people == set(COMMANDS)


def test_a_language_pack_is_named_by_its_code():
    """words- and a two- or three-letter code, with words_<code>.py beside its
    card, so the table above runs it and ADDONS.md lists it as a language."""
    for folder in STDLIB.glob("words-*"):
        code = folder.name[6:]
        assert re.fullmatch(r"[a-z]{2,3}", code), (
            f"{folder.name}: words- and an ISO 639 code"
        )
        assert (folder / f"words_{code}.py").is_file(), (
            f"{folder.name} has no words_{code}.py"
        )


@pytest.mark.parametrize("name", only(COMMANDS))
def test_a_bad_command_line_is_refused_and_says_how_to_run_it(name, tmp_path):
    script_name, argv = COMMANDS[name]
    script = STDLIB / name / script_name
    got = run(script)
    assert got.returncode == 2 and script_name in got.stderr, got.stderr
    pile = tmp_path / "pile"
    pile.mkdir()
    files = READERS.get(name, ("", {"garden.md": b"Tomatoes want sun.\n"}))[1]
    for rel, data in {**files, **PILE_EXTRA.get(name, {})}.items():
        (pile / rel).write_bytes(data)
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
                    str(pile), "--key", str(tmp_path / "key"), *NOW], check=True,
                   capture_output=True)  # fmt: skip
    fill = {"box": str(box), "pile": str(pile), "tmp": str(tmp_path)}
    good = [a.format(**fill) for a in argv]
    assert run(script, *good).returncode in (0, 42), "the command that works"
    if name == "starter-words":
        (tmp_path / "words.txt").unlink()
    got = run(script, *good, "--stray", "more")  # two: again takes one more as words
    assert got.returncode == 2 and script_name in got.stderr, (
        got.returncode,
        got.stderr,
    )


def check_reader(script: Path, sample: dict[str, bytes], tmp: Path) -> None:
    """The contract every reader keeps, run on one folder of its own files."""
    folder, mirror = tmp / "folder", tmp / "mirror"
    for rel, data in sample.items():
        for where in (rel, f".hidden/{rel}", f".{Path(rel).name}"):
            p = folder / where
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    before = snapshot(folder)

    got = run(script, "mirror", "--from", str(folder), "--to", str(mirror))
    assert got.returncode == 0, got.stderr
    line = got.stdout.strip().splitlines()[-1]
    assert re.fullmatch(rf"wrote {len(sample)} files? to .+; skipped 0", line), line
    assert sorted(snapshot(mirror)) == sorted(f"{rel}.txt" for rel in sample)
    again = tmp / "again"
    run(script, "mirror", "--from", str(folder), "--to", str(again))
    assert snapshot(again) == snapshot(mirror), "the same folder, the same bytes"
    assert snapshot(folder) == before, "originals are never changed"

    empty = tmp / "empty"
    empty.mkdir()
    got = run(script, "mirror", "--from", str(empty), "--to", str(tmp / "m2"))
    assert got.returncode == 42 and "wrote 0 files" in got.stdout

    for src, dst in ((folder, folder / "inside"), (folder, tmp)):
        got = run(script, "mirror", "--from", str(src), "--to", str(dst))
        assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr
    assert snapshot(folder) == before, "a refusal writes nothing"
    got = run(script, "mirror", "--from", str(tmp / "missing"), "--to", str(tmp / "m3"))
    assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr


@pytest.mark.parametrize("name", only(READERS))
def test_every_reader_keeps_the_readers_contract(name, tmp_path):
    script, sample = READERS[name]
    check_reader(STDLIB / name / script, sample, tmp_path)
