"""rtf: an RTF document as the plain text it displays; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "rtf.py"
spec = importlib.util.spec_from_file_location("rtf", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b"{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Arial;}}{\\colortbl;\\red0\\green0\\blue0;}"
    b"\\pard\\b The roof\\b0  is fixed.\\par\nBills go out on Thursday.\\par}"
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


BS = chr(92)
RAW_ONE = f"caf{BS}'e9 {BS}u233?lan {BS}u8364?5 {BS}u-10179?{BS}u-8567?"
RAW_TWO = f"na{BS}'efve {BS}'93quoted{BS}'94"
RAW_THREE = f"{BS}uc2{BS}u233ab x"
RAW_FOUR = f"a{BS}tab b{BS}line c{BS}emdash d{BS}bullet {BS}{{x{BS}}} {BS}{BS} {BS}~ {BS}lquote{BS}rquote"


def rtf(body: str) -> str | None:
    return mod.convert(("{\\rtf1\\ansi " + body + "}").encode("latin-1"))


def test_paragraphs_and_formatting_words_become_plain_text():
    assert mod.convert(SAMPLE) == "The roof is fixed.\n\nBills go out on Thursday.\n"


def test_the_font_colour_and_style_tables_and_info_are_dropped():
    out = rtf(
        r"{\fonttbl{\f0 Arial;}}{\colortbl;\red1;}{\stylesheet{\s1 Heading;}}{\info{\title Secret}{\author Jane}}Hello"
    )
    assert out == "Hello\n"


def test_hex_and_unicode_escapes_are_read_as_the_letters_they_are():
    assert rtf(RAW_ONE) == "café élan €5 " + chr(0x1F689) + "\n", (
        "two negative escapes make one astral character"
    )
    assert rtf(RAW_TWO) == "naïve “quoted”\n"
    assert rtf(RAW_THREE) == "é x\n"


def test_symbols_and_escaped_braces_and_backslashes():
    assert rtf(RAW_FOUR) == "a\tb\nc—d•{x} \\   ‘’\n"


def test_a_fields_shown_result_is_kept_and_its_instruction_dropped():
    out = rtf(r"See {\field{\*\fldinst HYPERLINK \"http://x\"}{\fldrslt the page}} now")
    assert out == "See the page now\n"


def test_pictures_headers_footers_and_ignorable_destinations_are_left_out():
    out = rtf(
        r"{\header Page header}{\pict\pngblip 89504e47}{\*\generator Word 16;}{\footer Footer}Body{\*\unknown stuff}"
    )
    assert out == "Body\n"


def test_blank_runs_are_squeezed_and_trailing_spaces_removed():
    assert rtf("a   \\par\\par\\par\\par b") == "a\n\nb\n"


def test_something_that_is_not_rtf_or_has_no_text_is_not_a_result():
    assert (
        mod.convert(b"plain text") is None
        and mod.convert(b"{\\rtf1\\ansi{\\fonttbl{\\f0 A;}}}") is None
    )


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"docs/letter.rtf": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "docs/letter.rtf.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "docs/letter.rtf": SAMPLE,
            ".hid/docs/letter.rtf": SAMPLE,
            ".docs/letter.rtf": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["docs/letter.rtf.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"docs/letter.rtf": SAMPLE})
    before = (tmp_path / "src" / "docs/letter.rtf").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "docs/letter.rtf.txt").read_bytes() == (
        out / "docs/letter.rtf.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "docs/letter.rtf").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.rtf": SAMPLE, "bad.rtf": b"not rich text at all"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.rtf.txt").is_file() and not (out / "bad.rtf.txt").exists()


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
        assert got.returncode == 2 and "rtf.py" in got.stderr
