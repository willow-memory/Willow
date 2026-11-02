"""shortcuts: a .url, a .webloc (XML and binary) and a .desktop link as the
title its name gives and the address it holds; a launcher as its name and
command; a .lnk left alone; hidden files and folders skipped, an unreadable
file skipped and counted, the same bytes twice, originals unchanged, and
MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import plistlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "shortcuts.py"
spec = importlib.util.spec_from_file_location("shortcuts", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

#: as Windows 10 writes one dragged from a browser's address bar
URL_FILE = (
    b"[{000214A0-0000-0000-C000-000000000046}]\r\nProp3=19,11\r\n"
    b"[InternetShortcut]\r\nIDList=\r\nURL=https://example.org/allotment/rules\r\n"
    b"IconIndex=13\r\nHotKey=0\r\nIconFile=C:\\Windows\\System32\\SHELL32.dll\r\n"
)
WEBLOC = {"URL": "https://example.org/tide-tables"}
DESKTOP_LINK = (
    b"[Desktop Entry]\nVersion=1.0\nType=Link\nName=Bin days\nName[fr]=Jours des poubelles\n"
    b"Comment=Which bin goes out when\nIcon=text-html\nURL=https://example.org/bins\n"
)
DESKTOP_APP = (
    b"[Desktop Entry]\nType=Application\nName=GNU Image Manipulation Program\n"
    b"GenericName=Image Editor\nComment=Create images and edit photographs\n"
    b"Keywords=GIMP;graphic;design;\nExec=gimp-2.10 %U\nTerminal=false\n"
    b"\n[Desktop Action new]\nName=New window\nExec=gimp-2.10 --new\n"
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


def test_a_windows_url_file_is_its_name_and_its_address():
    assert mod.convert(URL_FILE, "Allotment rules.url") == (
        "Allotment rules\nhttps://example.org/allotment/rules\n"
    )


def test_a_webloc_is_read_whether_saved_as_xml_or_binary():
    want = "Tide tables\nhttps://example.org/tide-tables\n"
    for fmt in (plistlib.FMT_XML, plistlib.FMT_BINARY):
        data = plistlib.dumps(WEBLOC, fmt=fmt)
        assert mod.convert(data, "Tide tables.webloc") == want


def test_a_desktop_link_is_its_name_comment_and_address_not_a_translation():
    assert mod.convert(DESKTOP_LINK, "bins.desktop") == (
        "Bin days\nWhich bin goes out when\nhttps://example.org/bins\n"
    )


def test_a_launcher_is_its_name_what_it_is_and_the_command_it_runs():
    assert mod.convert(DESKTOP_APP, "gimp.desktop") == (
        "GNU Image Manipulation Program\nImage Editor\n"
        "Create images and edit photographs\nGIMP;graphic;design;\n"
        "gimp-2.10 %U\n"
    )


def test_a_desktop_entry_without_a_name_takes_the_files_and_its_escapes_are_read():
    data = b"[Desktop Entry]\nType=Link\nComment=Two\\slines\\nhere \\\\ ok\nURL=https://x.example/\n"
    assert mod.convert(data, "Council.desktop") == (
        "Council\nTwo lines here \\ ok\nhttps://x.example/\n"
    )
    app = b"[Desktop Entry]\nType=Application\nExec=tool\n"
    assert mod.convert(app, "tool.desktop") == "tool\ntool\n"


def test_a_deleted_folder_or_unknown_desktop_entry_holds_no_link():
    for body in (
        DESKTOP_LINK + b"Hidden=true\n",
        b"[Desktop Entry]\nType=Directory\nName=Games\n",
        b"[Desktop Entry]\nName=No type\nURL=https://x.example/\n",
        b"[Other]\nType=Link\nURL=https://x.example/\n",
        b"[Desktop Entry]\nType=Link\nName=Empty\nURL=\n",
    ):
        assert mod.convert(body, "x.desktop") is None, body
    assert mod.convert(DESKTOP_LINK + b"Hidden=false\n", "x.desktop").startswith(
        "Bin days"
    )


def test_a_url_file_without_its_section_or_address_holds_no_link():
    for body in (
        b"[InternetShortcut]\r\nIconIndex=0\r\n",
        b"[Other]\r\nURL=https://x.example/\r\n",
        b"[InternetShortcut]\r\nURL=   \r\n",
    ):
        assert mod.convert(body, "x.url") is None, body


def test_a_default_section_as_windows_writes_it_lends_the_shortcut_nothing():
    data = (
        b"[DEFAULT]\r\nBASEURL=https://example.org/\r\nURL=https://wrong.example/\r\n"
        b"[InternetShortcut]\r\nIconIndex=0\r\n"
    )
    assert mod.convert(data, "x.url") is None
    data = b"[DEFAULT]\r\nBASEURL=https://example.org/\r\n" + URL_FILE
    assert "https://example.org/allotment/rules\n" in mod.convert(data, "x.url")


def test_a_url_files_keys_keep_their_case_and_a_colon_is_not_a_key():
    data = b"[InternetShortcut]\r\nurl=https://lower.example/\r\nURL=https://x.example/a:b=c\r\n"
    assert mod.convert(data, "x.url").endswith("https://x.example/a:b=c\n")


def test_a_url_file_in_windows_1252_is_read_but_a_desktop_file_must_be_utf8():
    data = b"[InternetShortcut]\r\nURL=https://x.example/\r\nIconFile=C:\\Users\\Ren\xe9e\\icon.ico\r\n"
    assert mod.convert(data, "Caf\u00e9.url") == "Caf\u00e9\nhttps://x.example/\n"
    bom = b"\xef\xbb\xbf" + URL_FILE
    assert mod.convert(bom, "a.url").endswith("allotment/rules\n")
    try:
        mod.convert(DESKTOP_LINK.replace(b"Bin days", b"Bin d\xe9ys"), "x.desktop")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("a desktop entry is UTF-8 by its spec")


def test_a_webloc_with_no_address_holds_no_link():
    for value in ({"Other": "x"}, {"URL": 3}, ["https://x.example/"], {"URL": ""}):
        assert mod.convert(plistlib.dumps(value), "x.webloc") is None, value


def test_an_extension_in_capitals_is_read(tmp_path):
    got, out = mirror_of(tmp_path, {"Rules.URL": URL_FILE})
    assert (out / "Rules.URL.txt").read_text() == (
        "Rules\nhttps://example.org/allotment/rules\n"
    )


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "Desktop/Allotment rules.url": URL_FILE,
            "Desktop/Tide tables.webloc": plistlib.dumps(
                WEBLOC, fmt=plistlib.FMT_BINARY
            ),
            "apps/gimp.desktop": DESKTOP_APP,
        },
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("wrote 3 files to " + str(out) + "; skipped 0")
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == [
        "Desktop/Allotment rules.url.txt",
        "Desktop/Tide tables.webloc.txt",
        "apps/gimp.desktop.txt",
    ]


def test_a_windows_lnk_is_neither_read_nor_counted(tmp_path):
    lnk = b"L\x00\x00\x00\x01\x14\x02\x00" + b"\x00" * 68
    got, out = mirror_of(tmp_path, {"a.url": URL_FILE, "Word.lnk": lnk})
    assert got.stdout.strip().endswith("skipped 0") and "wrote 1 files" in got.stdout
    assert not (out / "Word.lnk.txt").exists()


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"a.url": URL_FILE, ".hid/a.url": URL_FILE, ".a.url": URL_FILE},
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["a.url.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"a.url": URL_FILE})
    before = (tmp_path / "src" / "a.url").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "a.url.txt").read_bytes() == (out / "a.url.txt").read_bytes()
    assert (tmp_path / "src" / "a.url").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "good.url": URL_FILE,
            "nohead.url": b"URL=https://x.example/\r\n",
            "empty.url": b"[InternetShortcut]\r\n",
            "bad.webloc": b"<?xml version='1.0'?><plist><dict><key>URL",
            "junk.webloc": b"not a plist",
            "latin.desktop": b"[Desktop Entry]\nType=Link\nName=\xe9\nURL=x\n",
            "undefined.url": b"[InternetShortcut]\r\nURL=https://x.example/\x81\r\n",
        },
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and got.stdout.strip().endswith("skipped 6")
    assert [p.name for p in out.rglob("*")] == ["good.url.txt"]


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
        assert got.returncode == 2 and "shortcuts.py" in got.stderr


def folder_of_links(tmp_path: Path) -> list[dict]:
    """A desktop's worth of link files, mirrored and cut as the kernel cuts it."""
    files = {
        "Allotment rules.url": URL_FILE,
        "Tide tables.webloc": plistlib.dumps(WEBLOC, fmt=plistlib.FMT_BINARY),
        "Recipes.webloc": plistlib.dumps({"URL": "https://cooking.example/soup"}),
        "Council tax.url": b"[InternetShortcut]\r\nURL=https://council.example/tax\r\n",
        "bins.desktop": DESKTOP_LINK,
        "gimp.desktop": DESKTOP_APP,
    }
    got, out = mirror_of(tmp_path, files)
    assert got.stdout.strip().endswith("skipped 0"), got.stdout
    return mod.kernel.chunks(out)


def test_no_word_of_this_readers_own_lets_an_absent_question_through(tmp_path):
    pile = folder_of_links(tmp_path)
    assert len(pile) == 6, "one passage a file"
    texts = [set(mod.kernel.words(c["text"])) for c in pile]
    common = {w for w in set().union(*texts) if sum(w in t for t in texts) * 2 >= 6}
    assert common == {"https", "example", "org"}, "only the addresses' words repeat"
    # not "url", "webloc" or "desktop": the kernel reads a passage's path too, and
    # the mirror keeps the file's own name, so "volcano url" finds the .url files
    for word in ("link", "launcher", "runs", "comment", "keywords", "title"):
        assert mod.kernel.rank(pile, f"volcano {word}") == [], word


def test_a_persons_questions_still_land_on_the_one_file(tmp_path):
    pile = folder_of_links(tmp_path)
    for question, path in (
        ("where are the allotment rules", "Allotment rules.url.txt"),
        ("tide tables", "Tide tables.webloc.txt"),
        ("which bin goes out when", "bins.desktop.txt"),
        ("the image editor", "gimp.desktop.txt"),
        ("council tax", "Council tax.url.txt"),
    ):
        got = mod.kernel.rank(pile, question)
        assert [c["path"] for c in got[:1]] == [path], question
