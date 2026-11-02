"""opml: a feed list as one line per feed under its folder's name, an outline as
indented items with their notes, cut into passages at its top-level items;
the file's own words only; a DTD or entity never parsed; hidden files and
folders skipped, an unreadable file skipped and counted, the same bytes twice,
originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "opml.py"
spec = importlib.util.spec_from_file_location("opml", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
kernel = mod.kernel

FEEDS = b"""<?xml version="1.0" encoding="UTF-8"?>

<opml version="1.0">
  <head>
    <title>Ada subscriptions in feedly Cloud</title>
  </head>
  <body>
    <outline text="Gardening" title="Gardening">
      <outline type="rss" text="Hedgerow Diaries" title="Hedgerow Diaries" xmlUrl="https://hedgerow.example.org/feed.xml" htmlUrl="https://hedgerow.example.org/"/>
      <outline type="rss" text="The Seed Exchange" title="The Seed Exchange" xmlUrl="https://seeds.example.com/rss" htmlUrl="https://seeds.example.com"/>
    </outline>
    <outline text="Tech" title="Tech">
      <outline type="rss" text="Ink &amp; Switch notes" title="Ink &amp; Switch notes" xmlUrl="https://notes.example.net/atom.xml"/>
    </outline>
    <outline type="rss" title="Town council minutes" xmlUrl="https://council.example.gov/minutes.rss" description="Agendas and minutes"/>
  </body>
</opml>
"""

OVERCAST = b"""<?xml version="1.0" encoding="utf-8"?>
<opml version="1.0">
    <head><title>Overcast Podcast Subscriptions</title></head>
    <body>
        <outline text="feeds">
            <outline type="rss" overcastId="1203344" text="The Allotment Hour" title="The Allotment Hour" xmlUrl="https://feeds.example.org/allotment-hour" htmlUrl="https://allotmenthour.example.org/">
                <outline type="podcast-episode" overcastId="88001" pubDate="2024-05-01T05:00:00-04:00" title="Slugs, again" url="https://allotmenthour.example.org/ep/112" enclosureUrl="https://media.example.org/ah/112.mp3" played="1" />
                <outline type="podcast-episode" overcastId="88002" title="Raised beds on clay" url="https://allotmenthour.example.org/ep/113" />
            </outline>
            <outline type="rss" text="Night Shift Radio" xmlUrl="https://nightshift.example.net/rss" />
        </outline>
    </body>
</opml>
"""

OUTLINE = b"""<?xml version="1.0"?>
<opml version="2.0">
  <head>
    <title>Garden notebook</title>
    <dateCreated>Mon, 02 Mar 2026 09:14:00 GMT</dateCreated>
    <ownerName>Ada Example</ownerName>
    <expansionState>0,1</expansionState>
  </head>
  <body>
    <outline text="Garden plans" _note="Allotment plot 14, by the water butts.">
      <outline text="Spring beds" created="Sun, 01 Mar 2026 10:00:00 GMT">
        <outline text="Tomatoes" _note="Sungold and San Marzano, against the south fence.&#10;&#10;Start indoors mid-March." />
        <outline text="Broad beans" _complete="true" />
      </outline>
    </outline>
    <outline text="Reading">
      <outline text="The Overstory" _note="Gift from Jo; the chestnut chapter." />
    </outline>
    <outline text="Call the plumber about the boiler" />
    <outline text="Renew passport before June" />
  </body>
</opml>
"""

BOMB = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
 <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
 <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
 <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
 <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
 <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
 <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
 <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
]>
<opml version="2.0"><head><title>&lol9;</title></head><body><outline text="&lol9;"/></body></opml>
"""


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def opml(body: str, head: str = "") -> str | None:
    return mod.convert(
        f'<opml version="2.0"><head>{head}</head><body>{body}</body></opml>'.encode()
    )


def passages(text: str) -> list[str]:
    return text.rstrip("\n").split("\n\n")


def test_a_feed_list_is_a_line_per_feed_under_its_folders_name():
    assert mod.convert(FEEDS) == (
        "Ada subscriptions in feedly Cloud\n\n"
        "Gardening\n"
        "Hedgerow Diaries <https://hedgerow.example.org/feed.xml> <https://hedgerow.example.org/>\n"
        "The Seed Exchange <https://seeds.example.com/rss> <https://seeds.example.com>\n\n"
        "Tech\n"
        "Ink & Switch notes <https://notes.example.net/atom.xml>\n\n"
        "Town council minutes <https://council.example.gov/minutes.rss>\n"
        "  Agendas and minutes\n"
    )


def test_a_folder_inside_a_folder_is_named_with_both():
    out = opml(
        '<outline text="News"><outline text="Local">'
        '<outline type="rss" text="Gazette" xmlUrl="https://g.example/rss"/>'
        "</outline></outline>"
    )
    assert out == "News / Local\nGazette <https://g.example/rss>\n"


def test_podcast_episodes_follow_their_podcast_with_dates_as_written():
    out = mod.convert(OVERCAST)
    assert passages(out) == [
        "Overcast Podcast Subscriptions",
        "The Allotment Hour <https://feeds.example.org/allotment-hour> <https://allotmenthour.example.org/>\n"
        "  Slugs, again (2024-05-01T05:00:00-04:00) <https://media.example.org/ah/112.mp3>\n"
        "  Raised beds on clay <https://allotmenthour.example.org/ep/113>",
        "feeds\nNight Shift Radio <https://nightshift.example.net/rss>",
    ]


def test_many_episodes_are_cut_into_passages_each_starting_with_the_podcast():
    eps = "".join(
        f'<outline type="podcast-episode" title="Episode number {i} of the long run" '
        f'enclosureUrl="https://m.example/{i}.mp3"/>'
        for i in range(30)
    )
    out = opml(
        f'<outline type="rss" text="Night Shift Radio" xmlUrl="https://n.example/rss">{eps}</outline>'
    )
    parts = passages(out)
    assert len(parts) > 2
    assert all(
        p.startswith("Night Shift Radio <https://n.example/rss>\n  Episode")
        for p in parts
    )
    assert all(len(p) <= kernel.MAX_CHUNK for p in parts)
    assert sum(p.count("\n  Episode") for p in parts) == 30


def test_an_outline_is_indented_items_with_their_notes_and_the_head_first():
    assert mod.convert(OUTLINE) == (
        "Garden notebook\nMon, 02 Mar 2026 09:14:00 GMT\nAda Example\n\n"
        "- Garden plans\n"
        "  Allotment plot 14, by the water butts.\n"
        "  - Spring beds (Sun, 01 Mar 2026 10:00:00 GMT)\n"
        "    - Tomatoes\n"
        "      Sungold and San Marzano, against the south fence.\n"
        "      Start indoors mid-March.\n"
        "    - ✓ Broad beans\n\n"
        "- Reading\n"
        "  - The Overstory\n"
        "    Gift from Jo; the chestnut chapter.\n\n"
        "- Call the plumber about the boiler\n"
        "- Renew passport before June\n"
    )


def test_a_head_with_only_a_modified_date_is_kept():
    out = opml('<outline text="a"/>', "<dateModified>Sat, 14 Feb 2026</dateModified>")
    assert out == "Sat, 14 Feb 2026\n\n- a\n"


def test_a_link_its_address_and_markup_taken_off():
    out = opml(
        '<outline text="Hotel" type="link" url="https://hotel.example.pt/"/>'
        '<outline text="New &lt;b&gt;secateurs&lt;/b&gt; &amp;amp; gloves" checked="true"/>'
        '<outline text="Old" _status="checked"/><outline text="Maybe" _complete="false"/>'
        '<outline title="From the title"/><outline text=""/>'
    )
    assert out == (
        "- Hotel <https://hotel.example.pt/>\n- ✓ New secateurs & gloves\n"
        "- ✓ Old\n- Maybe\n- From the title\n"
    )


def test_an_item_with_no_text_but_children_is_kept_as_a_bare_dash():
    assert (
        opml('<outline text=""><outline text="child"/></outline>') == "-\n  - child\n"
    )


def test_a_long_branch_is_cut_at_its_children_and_each_passage_fits():
    beds = "".join(
        f'<outline text="Bed {i}">'
        + "".join(
            f'<outline text="Row {j} of bed {i}" _note="Sown in week {j}, thinned twice."/>'
            for j in range(4)
        )
        + "</outline>"
        for i in range(6)
    )
    out = opml(f'<outline text="Allotment">{beds}</outline><outline text="Loose"/>')
    parts = passages(out)
    assert all(len(p) <= kernel.MAX_CHUNK for p in parts)
    assert parts[0].startswith("- Allotment\n  - Bed 0\n")
    assert any(p.startswith("  - Bed ") for p in parts), "a cut piece keeps its indent"
    for i in range(6):  # a bed and all its rows in one passage
        assert [p.count(f" of bed {i}\n") for p in parts if f"- Bed {i}\n" in p] == [4]
    assert parts[-1] == "- Loose"
    assert sum(p.count("Sown in week") for p in parts) == 24
    # nothing above a cut piece is repeated: "Allotment" is in one passage
    assert sum("Allotment" in p for p in parts) == 1


def test_a_cut_branch_keeps_small_children_together_and_cuts_deeper_ones():
    big = "".join(f'<outline text="leaf {j} {"w" * 40}"/>' for j in range(12))
    out = opml(
        '<outline text="Top">'
        '<outline text="small one"/><outline text="small two"/>'
        f'<outline text="Deep">{big}</outline>'
        '<outline text="after one"/>'
        f'<outline text="long leaf" _note="{"z " * 300}"/>'
        '<outline text="after two"/>'
        "</outline>"
    )
    parts = passages(out)
    assert parts[0] == "- Top\n  - small one\n  - small two"
    assert parts[1].startswith("  - Deep\n    - leaf 0")
    assert any(p.startswith("  - after one") for p in parts)
    assert any(p.startswith("  - long leaf\n    z z") for p in parts)
    assert parts[-1] == "  - after two"
    assert sum(p.count("- leaf ") for p in parts) == 12


def test_a_long_note_is_wrapped_so_the_kernel_never_cuts_a_line_short(tmp_path):
    note = " ".join(f"word{i}" for i in range(200))
    out = opml(f'<outline text="Diary" _note="{note}"/>')
    lines = out.splitlines()
    assert all(len(x) <= mod.WRAP for x in lines)
    assert all(x.startswith("  word") for x in lines[1:])
    assert " ".join(x.strip() for x in lines[1:]) == note
    (tmp_path / "m").mkdir()
    (tmp_path / "m" / "d.txt").write_text(out)
    held = " ".join(c["text"] for c in kernel.chunks(tmp_path / "m"))
    assert all(f"word{i}" in held.split() for i in range(200))


def test_a_long_item_wraps_at_its_own_indent():
    out = opml(f'<outline text="a"><outline text="{"long " * 60}"/></outline>')
    lines = out.splitlines()
    assert len(lines) > 2 and all(x.startswith("  ") for x in lines[1:])


def test_an_outline_with_a_link_to_one_feed_stays_an_outline_with_its_notes():
    out = opml(
        '<outline text="Ideas" _note="for the newsletter"/>'
        '<outline text="Kitchen" _note="tiles"/>'
        '<outline type="rss" text="Gazette" xmlUrl="https://g.example/rss"/>'
    )
    assert out == (
        "- Ideas\n  for the newsletter\n- Kitchen\n  tiles\n"
        "- Gazette <https://g.example/rss>\n"
    )


def test_an_include_and_a_link_without_an_address_keep_what_they_have():
    out = opml(
        '<outline text="Archive" type="include" url="https://x.example/old.opml"/>'
        '<outline text="Broken link" type="link"/>'
    )
    assert out == "- Archive <https://x.example/old.opml>\n- Broken link\n"


def test_a_passage_fits_as_the_kernel_counts_it_newlines_and_all(tmp_path):
    """Ten lines of 498 characters with their newlines are 508: two passages,
    each one of the kernel's, never one the kernel cuts where it likes. Ten of
    489 are 499, which the kernel keeps whole: one passage, not cut early."""
    (tmp_path / "m").mkdir()
    for width, count in ((51, 2), (50, 1)):
        kids = "".join(f'<outline text="{chr(97 + i) * width}"/>' for i in range(9))
        out = opml(f'<outline text="T">{kids}</outline>')
        parts = passages(out)
        assert len(parts) == count
        (tmp_path / "m" / "o.txt").write_text(out)
        assert [c["text"] for c in kernel.chunks(tmp_path / "m")] == parts


def test_a_feed_list_keeps_a_stray_item_and_its_note():
    out = opml(
        '<outline type="rss" text="Gazette" xmlUrl="https://g.example/rss"/>'
        '<outline text="to read later" _note="the long one"/>'
    )
    assert out == "Gazette <https://g.example/rss>\n- to read later\n  the long one\n"


def test_a_billion_laughs_is_skipped_and_counted_never_expanded(tmp_path):
    got, out = mirror_of(tmp_path, {"lol.opml": BOMB, "good.opml": FEEDS})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert "lol.opml" in got.stderr and "DTD" in got.stderr
    assert not (out / "lol.opml.txt").exists()


def test_a_dtd_or_entity_is_refused_before_parsing_even_in_utf16():
    for data in (
        BOMB,
        b'<?xml version="1.0"?><!doctype opml><opml/>',
        b'<!ENTITY x "y"><opml/>',
        '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE opml><opml><body><outline text="a"/></body></opml>'.encode(
            "utf-16"
        ),
    ):
        try:
            mod.convert(data)
        except mod.Declares:
            continue
        raise AssertionError(f"not refused: {data[:40]!r}")


def test_a_utf16_file_without_a_dtd_is_read():
    data = '<?xml version="1.0" encoding="UTF-16"?><opml><body><outline text="café"/></body></opml>'
    assert mod.convert(data.encode("utf-16")) == "- café\n"


def test_an_xml_file_is_read_only_when_its_root_is_opml(tmp_path):
    plist = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        b'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict/></plist>\n'
    )
    got, out = mirror_of(
        tmp_path,
        {
            "subs.xml": FEEDS,
            "Info.xml": plist,
            "rss.xml": b"<rss><channel><title>x</title></channel></rss>",
            "notes.md": b"# hi\n",
        },
    )
    assert got.stdout.strip().endswith("wrote 1 files to " + str(out) + "; skipped 0")
    assert sorted(p.name for p in out.iterdir()) == ["subs.xml.txt"]


def test_an_opml_file_whose_root_is_not_opml_or_that_says_nothing_is_skipped(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "a.opml": b"<rss><channel/></rss>",
            "b.opml": b'<opml version="2.0"><head><title>Only a title</title></head><body/></opml>',
            "c.opml": b"<opml><head/></opml>",
            "d.OPML": OUTLINE,
        },
    )
    assert got.returncode == 0
    assert "wrote 1 files" in got.stdout and "skipped 3" in got.stdout
    assert sorted(p.name for p in out.iterdir()) == ["d.OPML.txt"]


def test_a_namespaced_root_is_still_opml():
    data = (
        b'<opml xmlns="http://example.org/ns"><body><outline text="a"/></body></opml>'
    )
    assert mod.convert(data) == "- a\n"


def test_none_of_this_readers_own_words_answers_a_question_the_file_cannot(tmp_path):
    """The owner's rule: a word the reader adds to passage after passage would
    answer a two-word question about something absent. Every word in most
    passages of these mirrors is the file's own (an address's parts), and the
    labels this reader once wrote serve nothing beside an absent word."""
    got, out = mirror_of(
        tmp_path, {"feeds.opml": FEEDS, "pods.opml": OVERCAST, "notes.opml": OUTLINE}
    )
    assert got.returncode == 0, got.stderr
    pile = kernel.chunks(out)
    held = set()
    for name, src in (("feeds", FEEDS), ("pods", OVERCAST), ("notes", OUTLINE)):
        values = (
            set()
        )  # the words of the file's values: text and attributes, no tag names
        for el in ET.fromstring(src).iter():
            for value in [el.text or "", *el.attrib.values()]:
                values.update(kernel.words(value))
        held |= values
        mine = [c["text"] for c in pile if c["path"].startswith(name)]
        common = {
            w
            for w in {w for t in mine for w in kernel.words(t)}
            if sum(w in kernel.words(t) for t in mine) * 2 > len(mine)
        }
        assert common <= values, (name, common - values)
    labels = (
        "feed",
        "podcast",
        "folder",
        "created",
        "done",
        "title",
        "owner",
        "episode",
        "published",
        "played",
        "site",
        "note",
        "x",
    )
    # a label the files hold themselves ("feeds", "Podcast") is theirs to answer
    absent = [w for w in labels if not any(v.startswith(w) for v in held)]
    assert len(absent) >= 8, absent
    for word in absent:
        assert kernel.rank(pile, f"volcano {word}") == [], word


def test_a_persons_questions_land_on_the_passage_that_answers_them(tmp_path):
    got, out = mirror_of(
        tmp_path, {"feeds.opml": FEEDS, "pods.opml": OVERCAST, "notes.opml": OUTLINE}
    )
    pile = kernel.chunks(out)
    for question, needle in (
        ("Hedgerow Diaries address", "https://hedgerow.example.org/feed.xml"),
        ("what is in my Gardening folder", "The Seed Exchange"),
        ("which tomatoes against the fence", "Sungold"),
        ("when was Slugs again published", "2024-05-01"),
        ("chestnut chapter Overstory", "Gift from Jo"),
    ):
        served = kernel.rank(pile, question)
        assert served and needle in served[0]["text"], question


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"apps/subs.opml": FEEDS})
    assert got.returncode == 0, got.stderr
    assert (out / "apps/subs.opml.txt").read_text() == mod.convert(FEEDS)
    assert "wrote 1 files to" in got.stdout and got.stdout.strip().endswith("skipped 0")


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"a/s.opml": FEEDS, ".hid/a/s.opml": FEEDS, ".s.opml": FEEDS},
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["a/s.opml.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"b.opml": OUTLINE, "a.opml": FEEDS})
    before = sorted((p.name, p.read_bytes()) for p in (tmp_path / "src").iterdir())
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    for name in ("a.opml.txt", "b.opml.txt"):
        assert (again / name).read_bytes() == (out / name).read_bytes()
    after = sorted((p.name, p.read_bytes()) for p in (tmp_path / "src").iterdir())
    assert after == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.opml": FEEDS, "bad.opml": b"<opml><body><outline"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.opml.txt").is_file() and not (out / "bad.opml.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


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
        assert got.returncode == 2 and "opml.py" in got.stderr
