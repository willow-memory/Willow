"""pocket: Pocket's export, the HTML and the CSVs in its zip, one dated line per
saved article, oldest first; other files left alone, an unreadable one skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "pocket.py"
spec = importlib.util.spec_from_file_location("pocket", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

HTML = (
    "<!DOCTYPE html>\n<html>\n\t<!--So long and thanks for all the fish-->\n\t<head>\n"
    '\t\t<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n'
    "\t\t<title>Pocket Export</title>\n\t</head>\n\t<body>\n\t\t<h1>Unread</h1>\n\t\t<ul>\n"
    '\t\t\t<li><a href="https://example.org/sourdough" time_added="1677925200" tags="baking,bread">'
    "How to keep a sourdough starter alive &amp; happy</a></li>\n"
    '\t\t\t<li><a href="https://example.org/no-title" time_added="1678011600" tags="">'
    "https://example.org/no-title</a></li>\n\t\t</ul>\n\t\t\n\t\t<h1>Read Archive</h1>\n\t\t<ul>\n"
    '\t\t\t<li><a href="https://example.org/tide" time_added="1520000000" tags="tides">'
    "Why the tide is late</a></li>\n\t\t</ul>\n\t</body>\n</html>\n"
).encode()
CSV = (
    "title,url,time_added,tags,status\n"
    '"Rye, spelt and the slow ferment",https://example.org/rye,1717236000,baking|bread,unread\n'
    "https://example.org/bare,https://example.org/bare,1717322400,,archive\n"
    '"Tide tables, explained",https://example.org/tides,1709370000,tides,archive\n'
    ",https://example.org/blank,1709456400,,unread\n"
).encode()
PART1 = b"title,url,time_added,tags,status\nOn allotments,https://example.org/allot,1690000000,garden,unread\n"


def zipped(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


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


def lines(text: str) -> list[str]:
    return [x for x in text.split("\n") if x]


def test_the_csv_is_one_dated_line_per_article_oldest_first():
    assert mod.convert("part_000000.csv", CSV) == (
        "2024-03-02 saved: Tide tables, explained <https://example.org/tides> [tides] (archived)\n\n"
        "2024-03-03 saved: https://example.org/blank (unread)\n\n"
        "2024-06-01 saved: Rye, spelt and the slow ferment <https://example.org/rye> [baking, bread] (unread)\n\n"
        "2024-06-02 saved: https://example.org/bare (archived)\n"
    )


def test_the_html_export_reads_both_lists_and_its_entities():
    assert lines(mod.convert("ril_export.html", HTML)) == [
        "2018-03-02 saved: Why the tide is late <https://example.org/tide> [tides] (archived)",
        "2023-03-04 saved: How to keep a sourdough starter alive & happy <https://example.org/sourdough> [baking, bread] (unread)",
        "2023-03-05 saved: https://example.org/no-title (unread)",
    ]


def test_each_status_pocket_wrote_is_said_and_one_it_did_not_is_left_out():
    rows = "".join(
        f"T{i},https://x.example/{i},1700000000,,{s}\n"
        for i, s in enumerate(["unread", "archive", "read", "Archive", "", "later"])
    )
    got = lines(
        mod.convert("a.csv", ("title,url,time_added,tags,status\n" + rows).encode())
    )
    assert [x.rsplit(">", 1)[1] for x in got] == [
        " (unread)",
        " (archived)",
        " (archived)",
        " (archived)",
        "",
        " (later)",
    ]


def test_a_missing_or_broken_time_is_said_and_goes_first_so_it_takes_no_other_date():
    csv = (
        b"title,url,time_added,tags,status\n"
        b"New,https://x.example/n,1717236000,,unread\n"
        b"Undated,https://x.example/u,,,unread\n"
        b"Garbled,https://x.example/g,soon,,unread\n"
        b"Same day first,https://x.example/a,1717236001,,unread\n"
    )
    assert [x.split(" <")[0] for x in lines(mod.convert("a.csv", csv))] == [
        "(no date) saved: Undated",
        "(no date) saved: Garbled",
        "2024-06-01 saved: New",
        "2024-06-01 saved: Same day first",
    ]


def test_the_day_is_utcs_whatever_the_machine_says():
    # 23:30 UTC on 2 March 2024 is already 3 March east of Greenwich
    assert (
        mod.day("1709422200") == "2024-03-02" and mod.day("1709424000") == "2024-03-03"
    )
    assert mod.day("") == "" and mod.day("99999999999999999999") == ""


def test_tags_are_pipe_joined_in_the_csv_and_comma_joined_in_the_html():
    csv = b"title,url,time_added,tags,status\nT,https://x.example/,1700000000,a|b c||d,unread\n"
    assert "[a, b c, d]" in mod.convert("a.csv", csv)
    assert "[baking, bread]" in mod.convert("ril_export.html", HTML)


def test_a_row_with_neither_title_nor_address_is_not_a_line_and_one_with_a_title_only_is():
    csv = (
        b"title,url,time_added,tags,status\n"
        b",,1700000000,,unread\n"
        b"  A   title only ,,1700000000,,unread\n"
        b"Short row,https://x.example/s\n"
        b"Long row,https://x.example/l,1700000000,t,unread,extra\n"
    )
    assert lines(mod.convert("a.csv", csv)) == [
        "(no date) saved: Short row <https://x.example/s>",
        "2023-11-14 saved: A title only (unread)",
        "2023-11-14 saved: Long row <https://x.example/l> [t] (unread)",
    ]


def test_a_file_that_is_not_pockets_is_left_alone_and_not_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "bank.csv": b"date,amount\n2024-01-01,5\n",
            "almost.csv": b"title,url,time_added,tags\nT,https://x.example/,1700000000,a\n",
            "page.html": b"<html><h1>Unread</h1><a href='x'>no time</a></html>",
            "links.html": b"<html><a href='x' time_added='1700000000'>no lists</a></html>",
            "photos.zip": zipped({"a.csv": b"date,amount\n", "b.txt": b"hi"}),
        },
    )
    assert got.returncode == 42 and got.stdout.strip().endswith(
        "wrote 0 files to " + str(out) + "; skipped 0"
    )
    assert not out.exists()


def test_the_zip_is_read_without_unpacking_into_one_mirror_beside_its_path(tmp_path):
    z = zipped(
        {
            "part_000000.csv": CSV,
            "part_000001.csv": PART1,
            "annotations/part_000000.json": b'[{"url": "https://example.org/rye"}]',
            "__MACOSX/._part_000000.csv": b"\x00\x05\x16\x07junk",
            "old/.part_000009.csv": CSV,
            "notes.csv": b"date,amount\n",
            "folder/": b"",
        }
    )
    got, out = mirror_of(tmp_path, {"mail/pocket.zip": z})
    assert got.returncode == 0, got.stderr
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["mail/pocket.zip.txt"]
    text = (out / "mail/pocket.zip.txt").read_text(encoding="utf-8")
    assert (
        lines(text)[0]
        == "2023-07-22 saved: On allotments <https://example.org/allot> [garden] (unread)"
    )
    assert len(lines(text)) == 5 and text.count("Rye, spelt") == 1
    assert sorted(p.name for p in (tmp_path / "src/mail").iterdir()) == ["pocket.zip"]


def test_a_zip_holding_the_old_html_is_read_too():
    assert lines(mod.convert("Pocket.ZIP", zipped({"ril_export.html": HTML})))[
        0
    ].startswith("2018-03-02 saved: Why the tide is late")


def test_a_member_over_the_limit_is_left_out(monkeypatch):
    monkeypatch.setattr(mod, "BIGGEST", len(PART1))
    got = mod.convert(
        "p.zip", zipped({"part_000000.csv": CSV, "part_000001.csv": PART1})
    )
    assert "On allotments" in got and "Rye" not in got


def test_the_size_limit_is_sixty_four_megabytes():
    assert mod.BIGGEST == 64 * 1024 * 1024


def test_a_pocket_file_with_no_articles_or_that_cannot_be_read_is_skipped_and_counted(
    tmp_path,
):
    got, out = mirror_of(
        tmp_path,
        {
            "good.csv": CSV,
            "empty.csv": b"title,url,time_added,tags,status\n",
            "bad.csv": b"\xff\xfe not utf8",
            "broken.zip": b"PK\x03\x04 not really",
        },
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and got.stdout.strip().endswith("skipped 3")
    assert [p.name for p in out.iterdir()] == ["good.csv.txt"]


def test_a_byte_order_mark_and_windows_line_ends_are_read():
    data = b"\xef\xbb\xbf" + CSV.replace(b"\n", b"\r\n")
    assert mod.convert("a.csv", data) == mod.convert("a.csv", CSV)


def test_each_article_is_one_passage_and_the_kernel_serves_the_one_asked_about(
    tmp_path,
):
    (tmp_path / "pocket.zip.txt").write_text(
        mod.convert(
            "pocket.zip", zipped({"part_000000.csv": CSV, "ril_export.html": HTML})
        ),
        encoding="utf-8",
    )
    pile = kernel.chunks(tmp_path)
    assert len(pile) == 7 and all("\n" not in c["text"] for c in pile)
    served = kernel.rank(pile, "when did I save that article about sourdough")
    assert [c["text"][:10] for c in served] == ["2023-03-04"]
    assert kernel.dates([c for c in pile])[-1] == 20240602, (
        "oldest first: each line its own date"
    )
    assert [d for d in kernel.dates(pile)] == sorted(kernel.dates(pile))


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path, {"old/ril_export.html": HTML, "part_000000.csv": CSV}
    )
    assert got.returncode == 0, got.stderr
    assert (out / "old/ril_export.html.txt").is_file() and (
        out / "part_000000.csv.txt"
    ).is_file()
    assert "wrote 2 files to" in got.stdout and got.stdout.strip().endswith("skipped 0")


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(tmp_path, {"a.csv": CSV, ".hid/a.csv": CSV, ".a.csv": CSV})
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["a.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    z = zipped({"part_000000.csv": CSV})
    got, out = mirror_of(tmp_path, {"pocket.zip": z})
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "pocket.zip.txt").read_bytes() == (
        out / "pocket.zip.txt"
    ).read_bytes()
    assert (tmp_path / "src/pocket.zip").read_bytes() == z
    assert [p.name for p in (tmp_path / "src").iterdir()] == ["pocket.zip"]


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    got = run(
        "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
    )
    assert got.returncode == 2 and got.stderr.startswith("refused: not a folder")


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
        ["mirror", "--from", "a", "--from", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "pocket.py" in got.stderr
