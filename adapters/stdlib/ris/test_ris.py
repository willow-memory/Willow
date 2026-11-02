"""ris: each reference as a passage that opens with its citation; continuation
lines, CRLF, a byte-order mark and blank lines between records read; a broken
record skipped and counted; EndNote's own .enw lines read too; hidden files
and folders skipped, an unreadable file skipped and counted, the same bytes
twice, originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "ris.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

spec = importlib.util.spec_from_file_location("ris", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    "TY  - JOUR\nAU  - Example, Ada\nAU  - Sample, Cy\nTI  - Tides of the Estuary\n"
    "T2  - Journal of Made-Up Studies\nPY  - 2020/03/15/\nVL  - 12\nIS  - 3\nSP  - 45\nEP  - 67\n"
    "DO  - 10.1000/xyz123\nKW  - tides\nKW  - estuaries\nAB  - We measure the tide\n  at six harbours.\n"
    "N1  - Read for chapter 2.\nER  - \n"
).encode()


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


def convert(text: str) -> str | None:
    return mod.convert(text.encode())


def test_a_reference_opens_with_its_citation_and_carries_the_rest():
    assert mod.convert(SAMPLE) == (
        "Example, Ada; Sample, Cy (2020). Tides of the Estuary. Journal of Made-Up Studies 12(3), 45–67.\n"
        "JOUR\n2020-03-15\n10.1000/xyz123\ntides; estuaries\n"
        "We measure the tide at six harbours.\nRead for chapter 2.\n\n"
        "1 references\n"
    )


def test_the_other_tags_for_title_journal_and_date_are_read():
    out = convert(
        "TY  - JOUR\nA1  - Turing, Alan Mathison\nT1  - On computable numbers\nJO  - Proc. London Math. Soc.\n"
        "Y1  - 1937///\nVL  - 47\nSP  - 230\nER  - \n"
    )
    assert out.startswith(
        "Turing, Alan Mathison (1937). On computable numbers. Proc. London Math. Soc. 47, 230.\n"
        "JOUR\n\n"
    )
    for tag in ("JF", "JA"):
        assert "Tides. Estuary Letters 3." in convert(
            f"TY  - JOUR\nTI  - Tides\n{tag}  - Estuary Letters\nVL  - 3\nER  -\n"
        )
    assert convert("TY  - JOUR\nTI  - T\nT2  - Full\nJO  - Abbr\nER  -\n").startswith(
        "T. Full.\n"
    )


def test_the_year_comes_only_from_the_date_tags_and_a_bare_month_is_kept():
    out = convert(
        "TY  - JOUR\nAU  - Ex, A\nTI  - Made in 1999\nPY  - 1948\nDA  - July\nER  - \n"
    )
    assert out.startswith("Ex, A (1948). Made in 1999.\nJOUR\nJuly\n")
    out = convert(
        "TY  - GEN\nAU  - Ex, A\nTI  - Made in 1999\nN1  - 2004 draft\nER  - \n"
    )
    assert out.startswith("Ex, A. Made in 1999.\nGEN\n2004 draft\n\n")
    out = convert("TY  - GEN\nTI  - X\nDA  - 2021/05//\nER  - \n")
    assert out.startswith("(2021). X.\nGEN\n2021/05\n\n")
    assert convert("TY  - GEN\nTI  - X\nPY  - 2021///\nER  - \n").startswith(
        "(2021). X.\nGEN\n\n"
    )


def test_the_type_is_kept_as_the_file_writes_it():
    for code in ("BOOK", "CHAP", "THES", "ODDX"):
        assert convert(f"TY  - {code}\nTI  - T\nER  - \n").split("\n")[1] == code


def test_a_chapter_carries_its_book_editors_publisher_and_links():
    out = convert(
        "TY  - CHAP\nAU  - Example, Ada\nTI  - Salt marshes\nT2  - Coasts of the North\nA2  - Editor, Ed\n"
        "A3  - Series, Sam\nPY  - 2001\nPB  - Harbour Press\nCY  - Leeds\nSN  - 978-0-00-000000-0\n"
        "UR  - https://example.org/a\nUR  - https://example.org/b\nID  - ex2001\nER  - \n"
    )
    assert out.startswith(
        "Example, Ada (2001). Salt marshes. Coasts of the North.\nCHAP\nEditor, Ed\nSeries, Sam\n"
        "Harbour Press, Leeds\nhttps://example.org/a; https://example.org/b\n978-0-00-000000-0\nex2001\n\n"
    )


def test_crlf_a_byte_order_mark_and_blank_lines_between_records_are_read():
    data = (
        b"\xef\xbb\xbf"
        + b"TY  - JOUR\r\nTI  - First\r\nER  - \r\n\r\n\r\nTY  - BOOK\r\nTI  - Second\r\nER  - \r\n"
    )
    assert mod.convert(data) == "First.\nJOUR\n\nSecond.\nBOOK\n\n2 references\n"


def test_a_broken_record_is_skipped_and_counted_never_fatal():
    out = convert(
        "TY  - JOUR\nTI  - Never ended\nTY  - JOUR\nTI  - Good\nER  - \nTY  - JOUR\nTI  - Cut off at the end\n"
    )
    assert out == "Good.\nJOUR\n\n1 references; 2 malformed\n"


def test_lines_outside_a_record_and_unknown_tags_are_ignored():
    out = convert(
        "Provider: Example\nAU  - Stray, Sam\nER  - \nTY  - JOUR\nTI  - Kept\nL1  - internal-pdf://x.pdf\nER  - \n"
    )
    assert out == "Kept.\nJOUR\n\n1 references\n"


def test_a_zotero_html_note_is_read_as_words_and_an_abstract_with_a_less_than_is_kept():
    out = convert(
        "TY  - JOUR\nTI  - T\nAB  - Depth < 5 m and > 2 m.\nN1  - <p>Read <b>twice</b>.</p><p>Tea &amp; cake</p>\n"
        "N1  - Second note\nER  - \n"
    )
    assert out.startswith(
        "T.\nJOUR\nDepth < 5 m and > 2 m.\nRead twice. Tea & cake; Second note\n\n"
    )


def test_n2_is_the_abstract_when_there_is_no_ab_and_ab_wins_when_both():
    assert convert("TY  - JOUR\nN2  - Alt\nER  - \n").startswith("JOUR\nAlt\n\n")
    assert convert("TY  - JOUR\nAB  - Main\nN2  - Alt\nER  - \n").startswith(
        "JOUR\nMain\n\n"
    )


def test_a_title_ending_in_a_question_mark_gets_no_extra_full_stop():
    assert convert("TY  - JOUR\nTI  - Why tides?\nER  - \n").startswith("Why tides?\n")


def test_endnote_tagged_enw_lines_are_read_as_references():
    out = convert(
        "%0 Journal Article\n%A Example, Ada\n%A Sample, Cy\n%T Tides of the Estuary\n%J Estuary Letters\n"
        "%D 2020\n%V 12\n%N 3\n%P 45-67\n%R 10.1000/xyz123\n%K tides\nestuaries\n%X We measure\nthe tide.\n\n"
        "%0 Book\n%T Second\n\nno tag here\n%T broken\n"
    )
    assert out == (
        "Example, Ada; Sample, Cy (2020). Tides of the Estuary. Estuary Letters 12(3), 45-67.\n"
        "Journal Article\n10.1000/xyz123\ntides; estuaries\nWe measure the tide.\n\n"
        "Second.\nBook\n\n2 references; 1 malformed\n"
    )


LIBRARY = (
    "TY  - JOUR\r\nAU  - Example, Ada\r\nAU  - Sample, Cy\r\nTI  - Tides of the Estuary\r\nT2  - Journal of Made-Up Studies\r\n"
    "PY  - 2020/03/15/\r\nVL  - 12\r\nIS  - 3\r\nSP  - 45\r\nEP  - 67\r\nDO  - 10.1000/xyz123\r\nKW  - tides\r\nKW  - estuaries\r\n"
    "AB  - We measure the tide at six harbours.\r\nN1  - Read for chapter 2.\r\nER  - \r\n\r\n"
    "TY  - JOUR\r\nAU  - Moss, Bea\r\nTI  - Lichen on harbour walls\r\nT2  - Coastal Ecology\r\nPY  - 2018///\r\n"
    "DO  - 10.1000/lichen\r\nKW  - lichen\r\nAB  - Lichen grows slowly on granite.\r\nER  - \r\n\r\n"
    "TY  - CHAP\r\nAU  - Example, Ada\r\nTI  - Salt marshes\r\nT2  - Coasts of the North\r\nA2  - Editor, Ed\r\n"
    "PY  - 2001\r\nPB  - Harbour Press\r\nCY  - Leeds\r\nDO  - 10.1000/marsh\r\nKW  - marshes\r\nAB  - Marsh grass holds the mud.\r\nER  - \r\n\r\n"
    "TY  - JOUR\r\nAU  - Reed, Dan\r\nTI  - Seabird counts\r\nT2  - Coastal Ecology\r\nPY  - 2019///\r\n"
    "DO  - 10.1000/birds\r\nKW  - seabirds\r\nAB  - Puffins returned in May.\r\nER  - \r\n"
)


def test_no_word_of_this_readers_repeats_in_every_passage(tmp_path):
    """The owner's ruling: a word in most passages, paired with one the folder
    doesn't hold, must not be served. The labels "doi:", "keywords:",
    "abstract:", "notes:", "date:" and the type in words ("journal article")
    failed this, and are gone. What still repeats is the file's own: the TY
    code (JOUR), a DOI's 10., a journal or an author."""
    got, out = mirror_of(tmp_path, {"library.ris": LIBRARY.encode()})
    assert got.returncode == 0, got.stderr
    pile = kernel.chunks(out)
    texts = [set(kernel.words(c["text"])) for c in pile]
    common = {w for t in texts for w in t if sum(w in u for u in texts) * 2 > len(pile)}
    # every word in most passages is the file's own (its type code, the DOI's
    # 10., a journal or author it repeats), none of this reader's
    assert common and common <= set(kernel.words(LIBRARY))
    for label in ("doi", "keywords", "abstract", "notes", "date", "article"):
        assert not any(label in t for t in texts), label
        assert kernel.rank(pile, f"volcano {label}") == [], label
    for question, holds in (
        ("tides estuary", "Tides of the Estuary"),
        ("who wrote salt marshes", "Salt marshes"),
        ("lichen granite", "Lichen on harbour walls"),
        ("doi of seabird counts", "10.1000/birds"),
        ("puffins abstract", "Puffins returned in May."),
    ):
        served = kernel.rank(pile, question)
        assert served and holds in served[0]["text"], question


def test_a_file_with_no_reference_is_not_a_reader_result():
    assert mod.convert(b"just words, no references") is None
    assert mod.convert(b"TY  - JOUR\nTI  - never ended\n") is None
    assert mod.convert(b"") is None


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path, {"refs/zotero.ris": SAMPLE, "refs/old.ENW": b"%0 Book\n%T Kept\n"}
    )
    assert got.returncode == 0, got.stderr
    assert (out / "refs/zotero.ris.txt").read_bytes() == mod.convert(SAMPLE).encode()
    assert (out / "refs/old.ENW.txt").is_file()
    assert "wrote 2 files to" in got.stdout and got.stdout.strip().endswith("skipped 0")


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "refs/a.ris": SAMPLE,
            ".hid/refs/a.ris": SAMPLE,
            ".refs/a.ris": SAMPLE,
            "refs/.a.ris": SAMPLE,
            "refs/a.bib": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["refs/a.ris.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"refs/a.ris": SAMPLE})
    before = (tmp_path / "src" / "refs/a.ris").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "refs/a.ris.txt").read_bytes() == (
        out / "refs/a.ris.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "refs/a.ris").read_bytes() == before
    assert sorted(p.name for p in (tmp_path / "src").rglob("*")) == ["a.ris", "refs"]


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "good.ris": SAMPLE,
            "latin1.ris": "TY  - JOUR\nTI  - Café\nER  - \n".encode("latin-1"),
            "empty.ris": b"no records\n",
        },
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 2" in got.stdout
    assert (out / "good.ris.txt").is_file() and not (out / "latin1.ris.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert not (tmp_path / "src" / "m").exists()
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
        ["mirror", "--from", "a", "--from", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "ris.py" in got.stderr


def test_the_first_date_tag_gives_the_year_and_a_date_with_no_year_gives_none():
    assert convert(
        "TY  - JOUR\nTI  - X\nPY  - 1948\nY1  - 1950///\nER  - \n"
    ).startswith("(1948). X.\n")
    assert convert("TY  - JOUR\nTI  - X\nDA  - Spring\nER  - \n").startswith(
        "X.\nJOUR\nSpring\n\n"
    )
