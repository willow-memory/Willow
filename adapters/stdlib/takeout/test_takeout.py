"""takeout: My Activity and YouTube history, JSON or HTML, as one dated line per
activity; dates read only when they read in full, other files left alone,
hidden files and folders skipped, a big mirror cut into parts, the same bytes
twice, originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "takeout.py"
spec = importlib.util.spec_from_file_location("takeout", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
kernel = mod.kernel

# the keys Takeout writes in My Activity/<Product>/MyActivity.json and in
# YouTube and YouTube Music/history/watch-history.json
SEARCH = [
    {"header": "Search", "title": "Searched for leek soup", "titleUrl": "https://www.google.com/search?q=leek+soup",
     "time": "2024-03-03T10:15:22.517Z", "products": ["Search"], "activityControls": ["Web & App Activity"]},
    {"header": "Search", "title": "Searched for tomato blight", "titleUrl": "https://www.google.com/search?q=tomato+blight",
     "time": "2024-02-28T21:04:10Z", "products": ["Search"], "activityControls": ["Web & App Activity"],
     "locationInfos": [{"name": "At this general area", "source": "From your places (Home)"}]},
]  # fmt: skip
WATCH = [
    {"header": "YouTube", "title": "Watched Leek and potato soup in 10 minutes", "titleUrl": "https://www.youtube.com/watch?v=abc123",
     "subtitles": [{"name": "Soup Kitchen", "url": "https://www.youtube.com/channel/UC123"}],
     "time": "2024-03-02T19:40:05.123Z", "products": ["YouTube"], "activityControls": ["YouTube watch history"]},
    {"header": "YouTube", "title": "Watched a video that has been removed", "time": "2024-03-01T08:00:00.000Z",
     "products": ["YouTube"], "activityControls": ["YouTube watch history"]},
    {"header": "YouTube", "title": "Watched Garden hose 50% off", "titleUrl": "https://www.youtube.com/watch?v=ad1",
     "time": "2024-03-01T07:59:00.000Z", "products": ["YouTube"], "details": [{"name": "From Google Ads"}],
     "activityControls": ["Web & App Activity", "YouTube watch history"]},
]  # fmt: skip


def page(*cells: str) -> bytes:
    """A My Activity HTML page as Takeout writes it."""
    return (
        '<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
        '<style type="text/css">.mdl-grid{}</style></head><body><div class="mdl-grid">'
        + "".join(cells)
        + "</div></body></html>"
    ).encode("utf-8")


def cell(product: str, body: str, extra: str = "") -> str:
    """One activity's outer-cell, with its header, body, empty right-hand cell
    and caption, the classes Takeout gives them."""
    return (
        '<div class="outer-cell mdl-cell mdl-cell--12-col mdl-shadow--2dp"><div class="mdl-grid">'
        '<div class="header-cell mdl-cell mdl-cell--12-col"><p class="mdl-typography--title">'
        f"{product}<br></p></div>"
        f'<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">{body}</div>'
        '<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1 mdl-typography--text-right"></div>'
        '<div class="content-cell mdl-cell mdl-cell--12-col mdl-typography--caption">'
        f"<b>Products:</b><br>&emsp;{product}<br>{extra}"
        "<b>Why is this here?</b><br>&emsp;This activity was saved to your Google Account because the following"
        " settings were on:&nbsp;YouTube watch history.&nbsp;You can control these settings &nbsp;"
        '<a href="https://myaccount.google.com/activitycontrols">here</a>.</div></div></div>'
    )


SEARCHED = 'Searched for&nbsp;<a href="https://www.youtube.com/results?search_query=leek+soup">leek soup</a><br>{}<br>'
WATCHED = (
    'Watched&nbsp;<a href="https://www.youtube.com/watch?v=abc123">Leek and potato soup in 10 minutes</a><br>'
    '<a href="https://www.youtube.com/channel/UC123">Soup Kitchen</a><br>{}<br>'
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def js(items) -> bytes:
    return json.dumps(items).encode("utf-8")


def when(raw: str) -> str:
    """The time an HTML date line is written as."""
    return mod.convert(page(cell("YouTube", SEARCHED.format(raw))), "a.html").split(
        " YouTube:"
    )[0]


# ── JSON ────────────────────────────────────────────────────────────────────
def test_a_search_is_one_dated_line_in_utc_to_the_minute_each_its_own_passage():
    assert mod.convert(js(SEARCH), "MyActivity.json") == (
        "2024-03-03 10:15 Search: Searched for leek soup\n\n"
        "2024-02-28 21:04 Search: Searched for tomato blight\n"
    )


def test_a_watch_keeps_its_channel_and_an_ad_says_so():
    assert mod.convert(js(WATCH), "watch-history.json") == (
        "2024-03-02 19:40 YouTube: Watched Leek and potato soup in 10 minutes, channel: Soup Kitchen\n\n"
        "2024-03-01 08:00 YouTube: Watched a video that has been removed\n\n"
        "2024-03-01 07:59 YouTube: Watched Garden hose 50% off [From Google Ads]\n"
    )


def test_subtitles_of_anything_but_a_watch_follow_in_brackets():
    item = {"header": "Maps", "title": "Viewed area around Leeds", "time": "2024-03-01T08:00:00Z",
            "subtitles": [{"name": "Kirkgate Market"}, {"name": ""}, {"url": "x"}, "loose", {"name": "Leeds"}]}  # fmt: skip
    assert mod.convert(js([item]), "a.json") == (
        "2024-03-01 08:00 Maps: Viewed area around Leeds (Kirkgate Market; Leeds)\n"
    )


def test_a_time_that_is_not_utc_or_not_a_day_is_kept_as_written():
    def at(t):
        return mod.convert(
            js([{"header": "Search", "title": "x", "time": t}]), "a.json"
        )

    assert at("2024-03-01T08:00:00+00:00") == "2024-03-01 08:00 Search: x\n"
    assert at("2024-03-01T08:00:00+01:00") == "[2024-03-01T08:00:00+01:00] Search: x\n"
    assert at("2024-02-30T08:00:00Z") == "[2024-02-30T08:00:00Z] Search: x\n"
    assert (
        at("2024-03-01T08:00:00Z trailing")
        == "[2024-03-01T08:00:00Z trailing] Search: x\n"
    )
    assert at("") == "[no date] Search: x\n"
    assert (
        mod.convert(js([{"header": "Search", "title": "x"}]), "a.json")
        == "[no date] Search: x\n"
    )


def test_a_missing_product_or_title_is_said_not_left_out():
    items = [
        {"header": "", "products": ["Chrome"], "title": "Visited Leek soup", "time": "2024-03-01T08:00:00Z"},
        {"header": None, "title": "", "time": "2024-03-01T08:00:00Z"},
    ]  # fmt: skip
    assert mod.convert(js(items), "a.json") == (
        "2024-03-01 08:00 Chrome: Visited Leek soup\n\n"
        "2024-03-01 08:00 (no product): (no title)\n"
    )


def test_whitespace_in_a_title_is_one_space():
    item = {
        "header": "Search",
        "title": "Searched for\n leek   soup ",
        "time": "2024-03-01T08:00:00Z",
    }
    assert (
        mod.convert(js([item]), "a.json")
        == "2024-03-01 08:00 Search: Searched for leek soup\n"
    )


def test_json_that_is_not_my_activity_is_not_read():
    keep = b'{"title":"Shopping","textContent":"milk","userEditedTimestampUsec":1710000000000000}'
    for data in (keep, b"[]", b'[{"header":"Search"}]', b'[{"title":"x"}]', b'[{"header":"S","title":"x"}, 3]',
                 b'{"timelineObjects":[]}', b"not json", b'"a string"'):  # fmt: skip
        assert mod.convert(data, "a.json") is None, data


# ── HTML ────────────────────────────────────────────────────────────────────
def test_an_html_page_reads_as_the_json_does():
    html = page(
        cell("YouTube", SEARCHED.format("Mar 3, 2024, 10:15:22 AM GMT")),
        cell("YouTube", WATCHED.format("Mar 2, 2024, 7:40:05 PM UTC")),
    )
    assert mod.convert(html, "search-history.html") == (
        "2024-03-03 10:15 YouTube: Searched for leek soup\n\n"
        "2024-03-02 19:40 YouTube: Watched Leek and potato soup in 10 minutes, channel: Soup Kitchen\n"
    )


def test_an_english_html_date_is_read_and_its_zone_kept_unless_utc():
    assert when("Mar 3, 2024, 10:15:22 AM GMT") == "2024-03-03 10:15"
    assert when("Mar 3, 2024, 10:15:22 AM GMT") == "2024-03-03 10:15"
    assert when("Mar 3, 2024, 7:05:00 PM CET") == "2024-03-03 19:05 CET"
    assert when("Mar 3, 2024, 12:05:00 AM GMT") == "2024-03-03 00:05"
    assert when("Mar 3, 2024, 12:05:00 PM GMT") == "2024-03-03 12:05"
    assert when("Sept 3, 2024, 1:05:00 PM GMT+01:00") == "2024-09-03 13:05 GMT+01:00"
    assert when("3 Mar 2024, 07:59:00 GMT") == "2024-03-03 07:59"
    assert when("3 December 2024, 23:59:00 BST") == "2024-12-03 23:59 BST"


def test_an_html_date_that_does_not_read_in_full_is_kept_as_written():
    for raw in (
        "3 mars 2024, 10:15:22 UTC",
        "Foo 3, 2024, 10:15:22 AM GMT",
        "Feb 30, 2024, 10:15:22 AM GMT",
        "Mar 3, 2024, 13:15:22 PM GMT",
        "Mar 3, 2024, 0:15:22 AM GMT",
        "3 Mar 2024, 25:15:22 GMT",
        "Mar 3, 2024",
    ):
        assert when(raw) == f"[{raw}]", raw


def test_html_details_are_kept_and_the_rest_of_the_caption_is_not():
    html = page(
        cell(
            "YouTube",
            WATCHED.format("1 Mar 2024, 07:59:00 GMT"),
            "<b>Details:</b><br>&emsp;From Google Ads<br>",
        )
    )
    assert mod.convert(html, "watch-history.html") == (
        "2024-03-01 07:59 YouTube: Watched Leek and potato soup in 10 minutes, channel: Soup Kitchen [From Google Ads]\n"
    )


def test_an_html_activity_with_no_date_line_says_so_and_an_empty_cell_is_passed_over():
    html = page(cell("Search", "Searched for leek soup"), cell("Search", ""))
    assert (
        mod.convert(html, "MyActivity.html")
        == "[no date] Search: Searched for leek soup\n"
    )


def test_a_line_break_in_the_source_is_not_a_break_in_the_page():
    html = page(
        cell(
            "Search",
            "Searched for\n<a href='x'>leek\r\nsoup</a><br>\nMar 3, 2024, 10:15:22 AM GMT\n<br>",
        )
    )
    assert (
        mod.convert(html, "MyActivity.html")
        == "2024-03-03 10:15 Search: Searched for leek soup\n"
    )


def test_html_that_is_not_my_activity_is_not_read():
    for data in (
        b"<html><body><h1>Archive</h1><p>Your Takeout</p></body></html>",
        b'<div class="outer-cell"></div>',
        page(cell("Search", "")),
        b"\xff\xfe<html>",
    ):
        assert mod.convert(data, "archive_browser.html") is None, data


# ── what the kernel serves ──────────────────────────────────────────────────
def test_when_did_i_search_for_leek_soup_is_answered_by_its_own_line(tmp_path):
    many = [
        {
            "header": "Search",
            "title": f"Searched for soup number {i}",
            "time": "2024-01-01T00:00:00Z",
        }
        for i in range(20)
    ]
    got, out = mirror_of(
        tmp_path, {"My Activity/Search/MyActivity.json": js(SEARCH[:1] + many)}
    )
    assert got.returncode == 0, got.stderr
    pile = kernel.chunks(out)
    assert len(pile) == 21, "each activity its own passage"
    served = kernel.rank(pile, "when did I search for leek soup")
    assert served[0]["text"] == "2024-03-03 10:15 Search: Searched for leek soup"


# ── the command line ────────────────────────────────────────────────────────
def test_mirror_writes_each_activity_file_beside_its_path_and_leaves_the_rest(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "Takeout/My Activity/Search/MyActivity.json": js(SEARCH),
            "Takeout/YouTube and YouTube Music/history/watch-history.html": page(
                cell("YouTube", WATCHED.format("Mar 2, 2024, 7:40:05 PM GMT"))
            ),
            "Takeout/Keep/Shopping.json": b'{"title":"Shopping","textContent":"milk"}',
            "Takeout/archive_browser.html": b"<html><body>Archive</body></html>",
            "Takeout/YouTube and YouTube Music/subscriptions/subscriptions.csv": b"Channel Id,Channel Url\n",
            "Takeout/.hidden/MyActivity.json": js(SEARCH),
            "Takeout/.MyActivity.json": js(SEARCH),
        },
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("wrote 2 files to " + str(out) + "; skipped 2")
    made = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    assert made == [
        "Takeout/My Activity/Search/MyActivity.json.txt",
        "Takeout/YouTube and YouTube Music/history/watch-history.html.txt",
    ]
    assert (
        (out / made[1]).read_text().startswith("2024-03-02 19:40 YouTube: Watched Leek")
    )


def test_the_same_folder_gives_the_same_bytes_and_is_never_changed(tmp_path):
    files = {
        "a/MyActivity.json": js(SEARCH),
        "b/watch-history.html": page(cell("YouTube", SEARCHED.format("x"))),
    }
    got, out = mirror_of(tmp_path, files)
    first = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
    again = run(
        "mirror", "--from", str(tmp_path / "src"), "--to", str(tmp_path / "again")
    )
    assert again.returncode == 0
    second = {
        out / p.relative_to(tmp_path / "again"): p.read_bytes()
        for p in (tmp_path / "again").rglob("*")
        if p.is_file()
    }
    assert first == second and len(first) == 2
    assert {
        p.relative_to(tmp_path / "src").as_posix(): p.read_bytes()
        for p in (tmp_path / "src").rglob("*")
        if p.is_file()
    } == files


def test_a_mirror_bigger_than_the_kernel_reads_is_cut_into_parts_it_can(tmp_path):
    big = [
        {
            "header": "YouTube",
            "title": f"Watched video {i} " + "x" * 80,
            "time": "2024-03-01T08:00:00Z",
        }
        for i in range(12000)
    ]
    got, out = mirror_of(tmp_path, {"watch-history.json": js(big)})
    assert got.returncode == 0 and "wrote 1 files" in got.stdout
    made = sorted(p.name for p in out.iterdir())
    assert made == ["watch-history.json.part2.txt", "watch-history.json.txt"]
    texts = [
        (out / mod._part_name("watch-history.json", n)).read_text() for n in (1, 2)
    ]
    assert all(len(t.encode()) <= kernel.MAX_FILE for t in texts)
    assert texts[0].startswith("2024-03-01 08:00 YouTube: Watched video 0 ")
    assert texts[0].endswith("x\n") and not texts[0].endswith("\n\n")
    every = (texts[0] + "\n" + texts[1]).split("\n\n")
    assert len(every) == 12000 and every[-1].startswith(
        "2024-03-01 08:00 YouTube: Watched video 11999 "
    )

    (tmp_path / "src" / "watch-history.json").write_bytes(js(big[:2]))
    assert (
        run("mirror", "--from", str(tmp_path / "src"), "--to", str(out)).returncode == 0
    )
    assert sorted(p.name for p in out.iterdir()) == ["watch-history.json.txt"], (
        "a stale part is removed"
    )


def test_a_passage_longer_than_a_part_is_shortened_to_fit_and_parts_fall_between_passages():
    assert mod.parts("a\n\n" + "é" * 40 + "\n\nb\n", limit=20) == [
        "a\n",
        "é" * 9 + "\n",
        "b\n",
    ]
    assert mod.parts("aaaa\n\nbbbb\n\ncccc\n", limit=13) == ["aaaa\n\nbbbb\n", "cccc\n"]
    assert mod.parts("aaaa\n\nbbbb\n\ncccc\n", limit=12) == ["aaaa\n\nbbbb\n", "cccc\n"]


def test_an_unreadable_file_is_skipped_and_counted_and_nothing_readable_is_42(tmp_path):
    got, out = mirror_of(
        tmp_path, {"MyActivity.json": b"\xff\xfe[", "MyActivity.html": b"<html></html>"}
    )
    assert got.returncode == kernel.ESCALATE
    assert got.stdout.strip().endswith("wrote 0 files to " + str(out) + "; skipped 2")


def test_refusals(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "MyActivity.json").write_bytes(js(SEARCH))
    for argv in (
        ["mirror", "--from", str(src)],
        ["mirror", "--from", str(src), "--to", str(tmp_path / "o"), "x"],
        ["copy", "--from", str(src), "--to", str(tmp_path / "o")],
        ["mirror", "--from", str(src), "--into", str(tmp_path / "o")],
    ):
        got = run(*argv)
        assert got.returncode == kernel.REFUSED and got.stderr.startswith("usage:"), (
            argv
        )
    got = run(
        "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "o")
    )
    assert got.returncode == kernel.REFUSED and "not a folder" in got.stderr
    for dst in (src / "inside", tmp_path, src):
        got = run("mirror", "--from", str(src), "--to", str(dst))
        assert got.returncode == kernel.REFUSED and "inside one another" in got.stderr
    assert sorted(p.name for p in tmp_path.rglob("*")) == ["MyActivity.json", "src"]


def test_main_in_process_writes_and_says_so(tmp_path, capsys, monkeypatch):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "MyActivity.json").write_bytes(js(SEARCH))
    argv = ["mirror", "--from", str(src), "--to", str(out)]
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), *argv])
    assert mod.main(argv) == kernel.ALIVE
    assert capsys.readouterr().out == f"wrote 1 files to {out}; skipped 0\n"
    assert (
        (out / "MyActivity.json.txt").read_text().startswith("2024-03-03 10:15 Search:")
    )
