"""text: every .txt as UTF-8 the kernel reads whole, line for line; an encoding
decoded only when certain or named, a binary skipped, long lines and big files
cut with a hidden map of where they go, no word added, the same bytes twice, originals
unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import codecs
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "text.py"
spec = importlib.util.spec_from_file_location("text_addon", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

NOTEPAD = "Boiler service\r\n\r\nServiced by Keane Heating on 12 March 2019.\r\n"
ANSI = "The rent for plot 14 rose to €45 – “agreed” by all.\r\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def folder_of(tmp_path: Path, files: dict[str, bytes]) -> Path:
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    return src


def mirror_of(
    tmp_path: Path, files: dict[str, bytes], *more: str
) -> tuple[subprocess.CompletedProcess, Path]:
    src = folder_of(tmp_path, files)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out), *more), out


def lines(data: bytes, encoding: str | None = None) -> list[str]:
    return [text for text, _ in mod.convert(data, encoding)]


# ── decoding, only when certain ─────────────────────────────────────────────
def test_a_notepad_unicode_file_is_read_and_the_kernel_could_not(tmp_path):
    data = codecs.BOM_UTF16_LE + NOTEPAD.encode("utf-16-le")
    got, out = mirror_of(tmp_path, {"boiler.txt": data})
    assert got.returncode == 0, got.stderr
    assert (out / "boiler.txt.txt").read_bytes() == (
        b"Boiler service\n\nServiced by Keane Heating on 12 March 2019.\n"
    )
    assert kernel.chunks(tmp_path / "src") == [], "the kernel leaves it out"
    found = kernel.chunks(out)
    assert [c["text"] for c in found][1] == (
        "Serviced by Keane Heating on 12 March 2019."
    )


@pytest.mark.parametrize(
    "codec", ["utf-8-sig", "utf-16", "utf-16-be", "utf-32", "utf-32-be"]
)
def test_every_unicode_byte_order_mark_is_read_and_dropped(codec):
    data = "Tschüß, € and Ω\n".encode(codec)
    if codec in ("utf-16-be", "utf-32-be"):
        data = "﻿Tschüß, € and Ω\n".encode(codec)
    assert lines(data) == ["Tschüß, € and Ω"]


def test_utf8_with_no_mark_is_read_as_it_is():
    assert lines("Grüße\n".encode()) == ["Grüße"]


@pytest.mark.parametrize("codec", ["utf-16-le", "utf-16-be"])
def test_utf16_with_no_mark_is_read_when_every_other_byte_is_nul(codec):
    assert lines("Plot 14\nTomás\n".encode(codec)) == ["Plot 14", "Tomás"]


@pytest.mark.parametrize("codec", ["utf-16-le", "utf-16-be"])
def test_utf16_with_no_mark_and_a_letter_beyond_latin1_is_not_guessed(codec):
    data = "Rent €45\n".encode(codec)
    with pytest.raises(mod.Skip, match="NUL bytes"):
        mod.decode(data)
    assert mod.decode(data, codec) == "Rent €45\n", "unless it is named"


def test_the_pattern_is_held_across_the_whole_sniff_window_only():
    good = ("a" * kernel.SNIFF).encode("utf-16-le")
    assert mod.bare_utf16(good) == "utf-16-le"
    broken = bytearray(good)
    broken[kernel.SNIFF - 1] = 0x20  # the last high byte of the window
    assert mod.bare_utf16(bytes(broken)) is None
    beyond = bytearray(good)
    beyond[kernel.SNIFF + 1] = 0x20  # past the window: not looked at
    assert mod.bare_utf16(bytes(beyond)) == "utf-16-le"
    assert mod.bare_utf16(good[:-1]) is None, "an odd length is not UTF-16"
    assert mod.bare_utf16(b"a") is None


def test_an_ansi_file_is_skipped_and_named_unless_its_encoding_is_given(tmp_path):
    files = {"minutes.txt": ANSI.encode("cp1252"), "ok.txt": b"Fine.\n"}
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0 and got.stdout.strip().endswith("; skipped 1")
    assert "skipped minutes.txt: not UTF-8; name its encoding with --encoding" in (
        got.stderr
    )
    assert not (out / "minutes.txt.txt").exists()
    got, out = mirror_of(tmp_path, files, "--encoding", "cp1252")
    assert got.stdout.strip().endswith("wrote 2 files to " + str(out) + "; skipped 0")
    assert (out / "minutes.txt.txt").read_text(encoding="utf-8") == ANSI[:-2] + "\n"


def test_a_named_encoding_never_overrides_a_file_that_is_certain():
    data = "Grüße\n".encode()
    assert mod.decode(data, "cp1252") == "Grüße\n", "not Ã¼"
    data = codecs.BOM_UTF16_LE + "Grüße\n".encode("utf-16-le")
    assert mod.decode(data, "latin-1") == "Grüße\n"


def test_a_file_the_named_encoding_cannot_decode_is_skipped_and_says_so():
    with pytest.raises(mod.Skip, match="not ascii"):
        mod.decode(ANSI.encode("cp1252"), "ascii")


def test_mac_roman_is_read_when_named():
    data = "Café crème\r".encode("mac-roman")
    assert lines(data, "mac-roman") == ["Café crème"]


@pytest.mark.parametrize("encoding", [None, "latin-1"])
def test_a_binary_named_txt_is_skipped_and_counted(tmp_path, encoding):
    png = b"\x89PNG\r\n\x1a\n" + bytes(64) + b"IHDR" + bytes(range(256))
    more = ["--encoding", encoding] if encoding else []
    got, out = mirror_of(tmp_path, {"photo.txt": png, "ok.txt": b"Fine.\n"}, *more)
    assert got.stdout.strip().endswith("; skipped 1"), got.stdout
    assert "skipped photo.txt: " in got.stderr and "NUL" in got.stderr
    assert not (out / "photo.txt.txt").exists()


def test_a_binary_behind_a_utf16_mark_is_skipped():
    with pytest.raises(mod.Skip, match="NUL characters"):
        mod.decode(codecs.BOM_UTF16_LE + bytes(40))


def test_utf32_marks_are_told_from_utf16_marks():
    # FF FE 00 00 opens UTF-32 LE, and also UTF-16 LE text whose first
    # character is U+0000; a UTF-16 file that fails UTF-32 is read as UTF-16
    data = codecs.BOM_UTF16_LE + "\0a".encode("utf-16-le")
    with pytest.raises(mod.Skip, match="NUL characters"):
        mod.decode(data)
    assert mod.decode("hi\n".encode("utf-32")) == "hi\n"


def test_an_empty_file_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"blank.txt": b"\n  \n", "ok.txt": b"Fine.\n"})
    assert "skipped blank.txt: empty" in got.stderr
    assert got.stdout.strip().endswith("wrote 1 files to " + str(out) + "; skipped 1")


def test_a_file_over_the_biggest_is_not_read(monkeypatch):
    monkeypatch.setattr(mod, "BIGGEST", 10)
    with pytest.raises(mod.Skip, match="over 50 MB"):
        mod.decode(b"x" * 11)
    assert mod.decode(b"x" * 10) == "x" * 10


# ── line for line ───────────────────────────────────────────────────────────
def test_crlf_and_a_bare_cr_become_lf_and_keep_the_line_count():
    assert lines(b"one\r\ntwo\rthree\n\nfive") == ["one", "two", "three", "", "five"]


def test_a_form_feed_alone_is_a_blank_line_and_inside_a_line_a_space():
    data = "page one\n\x0c\npage two\x0cstill two\nend same\x0bline\x85too\n"
    assert lines(data.encode()) == [
        "page one",
        "",
        "page two still two",
        "end same line too",
    ]
    assert lines(b"page one\n \x0c \npage two\n")[1] == ""


def test_the_kernel_reads_the_mirror_on_the_sources_own_lines(tmp_path):
    data = b"Garden\r\rTomatoes want sun.\rBeans want water.\r\x0c\rRoses last.\r"
    got, out = mirror_of(tmp_path, {"g.txt": data})
    found = {c["text"]: c["line"] for c in kernel.chunks(out)}
    assert found == {
        "Garden": 1,
        "Tomatoes want sun.\nBeans want water.": 3,
        "Roses last.": 6,
    }


# ── long lines and big files ────────────────────────────────────────────────
PARA = ("We walked the coast path past the lime kilns and the chapel. " * 12).strip()


def test_a_line_longer_than_the_kernel_reads_is_broken_at_spaces_and_mapped(tmp_path):
    data = (PARA + "\r\nThe ferry leaves at ten past nine.\r\n").encode()
    rows = mod.convert(data)
    got = [text for text, _ in rows]
    assert all(len(x) <= kernel.MAX_CHUNK for x in got) and len(got) == 3
    assert " ".join(got[:-1]) == PARA, "no word lost or changed"
    assert rows[-1] == ("The ferry leaves at ten past nine.", 2)
    assert [n for _, n in rows] == [1, 1, 2]
    res, out = mirror_of(tmp_path, {"h.txt": data})
    lines_map = (out / ".h.txt.lines").read_text()
    assert lines_map == "h.txt.txt\t1\t1\nh.txt.txt\t2\t1\n", "line 3 runs on"
    assert [mod.source_line(lines_map, "h.txt.txt", at) for at in (1, 2, 3)] == [
        1,
        1,
        2,
    ]


def test_the_kernel_finds_the_end_of_a_long_line_it_would_have_cut(tmp_path):
    data = (PARA + " The cottage was for rent.\n").encode()
    got, out = mirror_of(tmp_path, {"h.txt": data})
    assert not any("cottage" in c["text"] for c in kernel.chunks(tmp_path / "src"))
    assert any("cottage" in c["text"] for c in kernel.chunks(out))
    assert (out / "h.txt.txt").read_text().endswith(" rent.\n"), "nothing added"


def test_a_file_that_moves_no_line_has_no_map(tmp_path):
    got, out = mirror_of(tmp_path, {"a.txt": b"one\r\ntwo\r\n"})
    assert sorted(p.name for p in out.iterdir()) == ["a.txt.txt"]
    (tmp_path / "src" / "a.txt").write_bytes((PARA + "\n").encode())
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(out))
    assert (out / ".a.txt.lines").is_file()
    (tmp_path / "src" / "a.txt").write_bytes(b"short\n")
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(out))
    assert sorted(p.name for p in out.iterdir()) == ["a.txt.txt"], "a stale map goes"


def test_a_line_with_no_space_is_cut_where_it_reaches_the_limit():
    assert mod.wrap("a" * 1100) == ["a" * 500, "a" * 500, "a" * 100]
    assert mod.wrap("ab cd", 3) == ["ab", "cd"]
    assert mod.wrap("abc", 3) == ["abc"]


def test_a_mirror_over_the_limit_is_cut_at_a_blank_line():
    rows = [("x" * 9 if n % 4 else "", n) for n in range(1, 41)]
    got = mod.parts(rows, limit=100)
    assert len(got) > 2
    assert all(sum(len(x) + 1 for x, _ in p) <= 100 for p in got)
    for p in got[:-1]:
        assert p[-1][0] == "", "each part ends at a blank line"
    assert [r for p in got for r in p] == rows, "nothing lost, nothing twice"
    assert mod.runs(got[1]) == [(1, got[1][0][1])]


def test_with_no_blank_line_a_part_is_cut_between_lines():
    rows = [(f"line {n}", n) for n in range(1, 30)]
    got = mod.parts(rows, limit=60)
    assert got[0] == rows[:8], "as full as it fits"
    assert got[1][0] == ("line 9", 9)


def test_a_part_never_starts_inside_the_pieces_of_one_long_line():
    rows = [("a", 1)] + [("p" * 30, 2)] * 3 + [("c", 3), ("d", 4)]
    got = mod.parts(rows, limit=96)
    assert got == [rows[:4], rows[4:]]
    got = mod.parts(rows, limit=70)
    assert got[0] == [("a", 1)], "not between two pieces of line 2"
    assert got[1][:3] == [("p" * 30, 2)] * 3


def test_a_big_file_is_cut_into_parts_the_kernel_reads_and_maps_back(tmp_path):
    src = [f"Chapter {c}" if p == 0 else f"Para {c}.{p} of the long tale." for c in range(1, 3200) for p in range(12)]  # fmt: skip
    src = [x for c in range(0, len(src), 6) for x in src[c : c + 6] + [""]]
    src = src[:-1]
    src[-3] = "The miller sold the mill to a cooper from Dunmore."
    data = "\r\n".join(src).encode()
    assert len(data) > kernel.MAX_FILE
    got, out = mirror_of(tmp_path, {"book.txt": data})
    names = sorted(p.name for p in out.iterdir())
    assert names == [".book.txt.lines", "book.txt.part2.txt", "book.txt.txt"]
    assert all((out / n).stat().st_size <= kernel.MAX_FILE for n in names)
    assert kernel.chunks(tmp_path / "src") == [], "the kernel drops it whole"
    hit = [c for c in kernel.chunks(out) if "Dunmore" in c["text"]]
    assert hit and hit[0]["path"] == "book.txt.part2.txt"
    first = (out / "book.txt.txt").read_text().split("\n")[:-1]
    part2 = (out / "book.txt.part2.txt").read_text().split("\n")[:-1]
    assert first + part2 == src, "line for line, nothing added"
    assert first[-1] == "", "cut at a blank line"
    lines_map = (out / ".book.txt.lines").read_text()
    assert lines_map == f"book.txt.txt\t1\t1\nbook.txt.part2.txt\t1\t{len(first) + 1}\n"
    for at in (1, hit[0]["line"], len(part2)):
        n = mod.source_line(lines_map, "book.txt.part2.txt", at)
        assert src[n - 1] == part2[at - 1]


def test_a_shorter_run_removes_the_parts_a_longer_one_left(tmp_path):
    src = folder_of(tmp_path, {"book.txt": ("word " * 99 + "\n\n").encode() * 4000})
    out = tmp_path / "out"
    run("mirror", "--from", str(src), "--to", str(out))
    assert (out / "book.txt.part2.txt").is_file()
    (src / "book.txt").write_bytes(b"Short now.\n")
    run("mirror", "--from", str(src), "--to", str(out))
    assert sorted(p.name for p in out.iterdir()) == ["book.txt.txt"]


# ── the reader's contract ───────────────────────────────────────────────────
def test_txt_and_text_are_read_and_written_at_the_same_path_with_txt_added(tmp_path):
    files = {"a.txt": b"A.\n", "notes/b.TEXT": b"B.\n", "c.md": b"C.\n", "d.nfo": b"D"}
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*.txt")) == [
        "a.txt.txt",
        "notes/b.TEXT.txt",
    ]


def test_hidden_files_and_folders_are_not_read(tmp_path):
    files = {"a.txt": b"A.\n", ".b.txt": b"B.\n", ".hid/c.txt": b"C.\n"}
    got, out = mirror_of(tmp_path, files)
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == ["a.txt.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    files = {"a.txt": NOTEPAD.encode("utf-16"), "b.txt": b"x\ry\r"}
    src = folder_of(tmp_path, files)
    run("mirror", "--from", str(src), "--to", str(tmp_path / "m1"))
    run("mirror", "--from", str(src), "--to", str(tmp_path / "m2"))
    for name in ("a.txt.txt", "b.txt.txt"):
        assert (tmp_path / "m1" / name).read_bytes() == (
            tmp_path / "m2" / name
        ).read_bytes()
    assert {p.name: p.read_bytes() for p in src.iterdir()} == files


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"only.md": b"x\n"})
    assert got.returncode == kernel.ESCALATE and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    src = folder_of(tmp_path, {"a.txt": b"A.\n"})
    for dst in (src / "m", tmp_path):
        got = run("mirror", "--from", str(src), "--to", str(dst))
        assert got.returncode == kernel.REFUSED and got.stderr.startswith("refused")
    assert not (src / "m").exists()


@pytest.mark.parametrize("name", ["no-such-codec", "base64", "rot13"])
def test_an_encoding_python_does_not_know_as_text_is_refused(tmp_path, name):
    src = folder_of(tmp_path, {"a.txt": b"A.\n"})
    got = run("mirror", "--from", str(src), "--to", str(tmp_path / "m"), "--encoding", name)  # fmt: skip
    assert got.returncode == kernel.REFUSED
    assert got.stderr == f"refused: not a text encoding Python knows: {name}\n"
    assert not (tmp_path / "m").exists()


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["mirror", "--from", "a"],
        ["mirror", "--from", "a", "--to", "b", "--stray", "c"],
        ["mirror", "--from", "a", "--to", "b", "--encoding"],
        ["mirror", "--from", "a", "--to", "b", "--encoding", "x", "y", "z"],
        ["copy", "--from", "a", "--to", "b"],
    ],
)
def test_a_bad_command_line_says_how_to_run_it(argv):
    got = run(*argv)
    assert got.returncode == kernel.REFUSED and got.stderr.startswith("usage: text.py")


def test_a_missing_folder_is_refused(tmp_path):
    got = run("mirror", "--from", str(tmp_path / "nope"), "--to", str(tmp_path / "m"))
    assert got.returncode == kernel.REFUSED and "not a folder" in got.stderr


# ── no word of its own in a passage ─────────────────────────────────────────
def test_it_adds_no_word_so_a_question_about_something_absent_gets_nothing(tmp_path):
    """A word this wrote into passage after passage would let a two-word
    question about something the folder doesn't hold be answered (one word is
    half). It writes none: every word of the mirror is the source's, and the
    line map is hidden, so the kernel never reads it."""
    tide = "the tide at the harbour was high and the boats lay on the mud " * 7
    book = "\n\n".join(f"Para {n}: {tide}" for n in range(2500))
    files = {
        "holiday.txt": (PARA + " The cottage was for rent.\r\nThe ferry leaves at nine.\r\n").encode(),
        "book.txt": (book + "\n\nThe miller sold the mill to a cooper.\n").encode(),
        "boiler.txt": codecs.BOM_UTF16_LE + NOTEPAD.encode("utf-16-le"),
    }  # fmt: skip
    got, out = mirror_of(tmp_path, files)
    assert (out / "book.txt.part2.txt").is_file()
    assert (out / ".holiday.txt.lines").is_file()
    pile = kernel.chunks(out)
    when = kernel.dates(pile)  # once: the kernel works them out on each ask

    def ask(q: str) -> list[dict]:
        return kernel.rank(pile, q, dated=lambda _: when)

    for name, data in files.items():
        said = set(kernel.words(mod.decode(data)))
        wrote = {w for c in pile if c["path"].startswith(name) for w in kernel.words(c["text"])}  # fmt: skip
        assert wrote and wrote <= said, (name, wrote - said)
    for w in ("line", "lines", "part", "from", "page"):
        assert ask(f"volcano {w}") == [], w
    for q, needle in (
        ("When does the ferry leave?", "ferry leaves at nine"),
        ("Was the cottage for rent?", "cottage was for rent"),
        ("Who did the miller sell the mill to?", "cooper"),
        ("When was the boiler serviced?", "Keane Heating"),
    ):
        assert any(needle in c["text"] for c in ask(q)), q
