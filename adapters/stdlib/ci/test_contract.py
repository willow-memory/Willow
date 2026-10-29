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
PILE_EXTRA: dict[str, dict[str, bytes]] = {"scrub": {"photo.png": _png()}}

#: one small readable file per reader, by the name it is written under
READERS: dict[str, tuple[str, dict[str, bytes]]] = {
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
    "notes": ("notes.py", {"garden.md": b"Tomatoes want [[sun]].\n"}),
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

#: a command that works, for each add-on a person runs; {box}, {pile} and
#: {tmp} are filled in. The repo's own tools (ci, readme, similar, mutants,
#: github) are tested in their own folders.
COMMANDS: dict[str, tuple[str, list[str]]] = {
    "a11y-check": ("a11y_check.py", ["--box", "{box}"]),
    "abbreviations": ("abbreviations.py", ["--box", "{box}", "tomatoes"]),
    "accents": ("accents.py", ["--box", "{box}", "tomatoes"]),
    "amounts": ("amounts.py", ["--box", "{box}"]),
    "first-mention": ("first_mention.py", ["--box", "{box}", "tomatoes"]),
    "fuzzy-dates": ("fuzzy_dates.py", ["--box", "{box}"]),
    "again": ("again.py", ["--box", "{box}"]),
    "aider": ("aider.py", ["--box", "{box}"]),
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
    **{f"words-{c}": (f"words_{c}.py", ["bite", "--box", "{box}", *NOW, "tomatoes"])
       for c in ("ar", "cy", "de", "es", "fr", "it", "nl", "pl", "pt", "ru", "sv", "tr")},
    "backup": ("backup.py", ["--box", "{box}", "--to", "{tmp}/backups", *NOW]),
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
    "history": ("history.py", ["--box", "{box}"]),
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
