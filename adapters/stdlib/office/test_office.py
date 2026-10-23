"""Tests for office.py. Every sample file is built here with zipfile, from
minimal XML parts; there are no binary fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OFFICE = HERE / "office.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
SS_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(str(OFFICE), "mirror", "--from", str(folder), "--to", str(to))


def zip_file(path: Path, parts: dict[str, str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, xml in parts.items():
            zf.writestr(name, xml)
    return path


def docx_xml(*paragraphs: str) -> str:
    body = "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{p}</w:t></w:r></w:p>' for p in paragraphs
    )
    return f'{HEAD}<w:document xmlns:w="{W_NS}"><w:body>{body}</w:body></w:document>'


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_docx_paragraphs_become_blank_line_separated_lines(tmp_path):
    folder = tmp_path / "in"
    xml = (
        f'{HEAD}<w:document xmlns:w="{W_NS}"><w:body>'
        "<w:p><w:r><w:t>First paragraph.</w:t></w:r></w:p>"
        '<w:p><w:r><w:t xml:space="preserve">Split </w:t></w:r>'
        "<w:r><w:t>words here</w:t></w:r></w:p>"
        "<w:p/>"  # an empty paragraph is not a line
        "<w:p><w:r><w:t>Last one.</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    zip_file(folder / "a.docx", {"word/document.xml": xml})
    out = tmp_path / "out"
    got = mirror(folder, out)
    assert got.returncode == 0, got.stderr
    assert (out / "a.docx.txt").read_text(encoding="utf-8") == (
        "First paragraph.\n\nSplit words here\n\nLast one.\n"
    )


def test_odt_headings_paragraphs_and_spaces(tmp_path):
    folder = tmp_path / "in"
    xml = (
        f'{HEAD}<office:document-content xmlns:office="{OFFICE_NS}" '
        f'xmlns:text="{TEXT_NS}"><office:body><office:text>'
        '<text:h text:outline-level="1">Heading here</text:h>'
        "<text:p>Body para.</text:p>"
        '<text:p>Hard<text:s text:c="2"/>gap</text:p>'
        "</office:text></office:body></office:document-content>"
    )
    zip_file(folder / "memo.odt", {"content.xml": xml})
    out = tmp_path / "out"
    assert mirror(folder, out).returncode == 0
    assert (out / "memo.odt.txt").read_text(encoding="utf-8") == (
        "Heading here\n\nBody para.\n\nHard  gap\n"
    )


def test_pptx_slides_in_number_order_with_headings(tmp_path):
    folder = tmp_path / "in"

    def slide(text: str) -> str:
        return (
            f'{HEAD}<p:sld xmlns:a="{A_NS}" xmlns:p="{P_NS}"><p:cSld><p:spTree>'
            f"<p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>"
            "</p:spTree></p:cSld></p:sld>"
        )

    # slide10 is written first on purpose: the order must be numeric, not textual
    zip_file(
        folder / "deck.pptx",
        {
            "ppt/slides/slide10.xml": slide("Ten"),
            "ppt/slides/slide1.xml": slide("Title one"),
            "ppt/slides/slide2.xml": slide("Second"),
        },
    )
    out = tmp_path / "out"
    assert mirror(folder, out).returncode == 0
    assert (out / "deck.pptx.txt").read_text(encoding="utf-8") == (
        "== slide 1\n\nTitle one\n\n== slide 2\n\nSecond\n\n== slide 10\n\nTen\n"
    )


def test_xlsx_sheets_rows_cells_and_shared_strings(tmp_path):
    folder = tmp_path / "in"
    strings = (
        f'{HEAD}<sst xmlns="{SS_NS}">'
        "<si><t>Item</t></si><si><t>Cost</t></si>"
        "<si><r><t>Rich </t></r><r><t>text</t></r></si>"
        "</sst>"
    )
    workbook = (
        f'{HEAD}<workbook xmlns="{SS_NS}" xmlns:r="{R_NS}"><sheets>'
        '<sheet name="Budget" sheetId="1" r:id="rId1"/>'
        '<sheet name="Notes" sheetId="2" r:id="rId2"/>'
        "</sheets></workbook>"
    )
    rels = (
        f'{HEAD}<Relationships xmlns="{PKG_NS}">'
        '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Target="/xl/worksheets/sheet2.xml"/>'
        "</Relationships>"
    )
    budget = (
        f'{HEAD}<worksheet xmlns="{SS_NS}"><sheetData>'
        '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
        '<row r="2"><c r="A2" t="inlineStr"><is><t>Rent</t></is></c>'
        '<c r="C2"><v>900</v></c></row>'
        '<row r="3"/>'  # a blank row is dropped
        '<row r="4"><c r="A4" t="str"><f>A1</f><v>cached</v></c></row>'
        "</sheetData></worksheet>"
    )
    notes = (
        f'{HEAD}<worksheet xmlns="{SS_NS}"><sheetData>'
        '<row r="1"><c r="A1" t="s"><v>2</v></c></row>'
        "</sheetData></worksheet>"
    )
    zip_file(
        folder / "money.xlsx",
        {
            "xl/workbook.xml": workbook,
            "xl/_rels/workbook.xml.rels": rels,
            "xl/sharedStrings.xml": strings,
            "xl/worksheets/sheet1.xml": budget,
            "xl/worksheets/sheet2.xml": notes,
        },
    )
    out = tmp_path / "out"
    assert mirror(folder, out).returncode == 0
    assert (out / "money.xlsx.txt").read_text(encoding="utf-8") == (
        "== sheet Budget\n\nItem | Cost\nRent |  | 900\ncached\n\n"
        "== sheet Notes\n\nRich text\n"
    )


def test_ods_rows_cells_and_repeats(tmp_path):
    folder = tmp_path / "in"
    xml = (
        f'{HEAD}<office:document-content xmlns:office="{OFFICE_NS}" '
        f'xmlns:table="{TABLE_NS}" xmlns:text="{TEXT_NS}"><office:body>'
        "<office:spreadsheet>"
        '<table:table table:name="Ledger">'
        "<table:table-row>"
        '<table:table-cell office:value-type="string"><text:p>Date</text:p></table:table-cell>'
        '<table:table-cell office:value-type="string"><text:p>Amount</text:p></table:table-cell>'
        '<table:table-cell table:number-columns-repeated="1000"/>'
        "</table:table-row>"
        '<table:table-row table:number-rows-repeated="5000">'
        '<table:table-cell table:number-columns-repeated="1024"/>'
        "</table:table-row>"
        "<table:table-row>"
        '<table:table-cell office:value-type="string"><text:p>Rent</text:p></table:table-cell>'
        '<table:table-cell table:number-columns-repeated="2"/>'
        '<table:table-cell office:value-type="float" office:value="900"/>'
        '<table:table-cell table:number-columns-repeated="1000"/>'
        "</table:table-row>"
        "</table:table>"
        '<table:table table:name="Two"><table:table-row>'
        "<table:table-cell><text:p>x</text:p></table:table-cell>"
        "</table:table-row></table:table>"
        "</office:spreadsheet></office:body></office:document-content>"
    )
    zip_file(folder / "ledger.ods", {"content.xml": xml})
    out = tmp_path / "out"
    assert mirror(folder, out).returncode == 0
    assert (out / "ledger.ods.txt").read_text(encoding="utf-8") == (
        "== sheet Ledger\n\nDate | Amount\nRent |  |  | 900\n\n== sheet Two\n\nx\n"
    )


def test_mirror_naming_and_skips_dotted_and_other_files(tmp_path):
    folder = tmp_path / "in"
    zip_file(folder / "reports" / "q3.docx", {"word/document.xml": docx_xml("Q3.")})
    zip_file(folder / "top.docx", {"word/document.xml": docx_xml("Top.")})
    zip_file(folder / ".git" / "hidden.docx", {"word/document.xml": docx_xml("No.")})
    zip_file(folder / ".secret.docx", {"word/document.xml": docx_xml("No.")})
    (folder / "notes.txt").write_text("plain\n", encoding="utf-8")
    out = tmp_path / "out"
    got = mirror(folder, out)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == f"wrote 2 files to {out.resolve()}; skipped 0"
    assert sorted(snapshot(out)) == ["reports/q3.docx.txt", "top.docx.txt"]
    assert not (out / ".git").exists()


def test_corrupt_files_are_skipped_and_counted(tmp_path):
    folder = tmp_path / "in"
    zip_file(folder / "good.docx", {"word/document.xml": docx_xml("Fine.")})
    (folder / "broken.docx").write_bytes(b"this is not a zip")
    zip_file(folder / "missing.docx", {"word/other.xml": "<x/>"})
    zip_file(folder / "badxml.odt", {"content.xml": "<office:document-content"})
    out = tmp_path / "out"
    got = mirror(folder, out)
    assert got.returncode == 0, got.stderr
    assert "Traceback" not in got.stderr
    assert got.stdout.strip() == f"wrote 1 files to {out.resolve()}; skipped 3"
    assert sorted(snapshot(out)) == ["good.docx.txt"]


def test_nothing_readable_exits_42(tmp_path):
    corrupt = tmp_path / "corrupt"
    (corrupt / "x").mkdir(parents=True)
    (corrupt / "x" / "bad.xlsx").write_bytes(b"\x00\x01 nope")
    got = mirror(corrupt, tmp_path / "out1")
    assert got.returncode == 42
    assert got.stdout.strip().endswith("skipped 1")

    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "notes.txt").write_text("nothing here\n", encoding="utf-8")
    got = mirror(plain, tmp_path / "out2")
    assert got.returncode == 42
    assert got.stdout.strip().endswith("skipped 0")


def test_refusals_say_why_and_write_nothing(tmp_path):
    folder = tmp_path / "in"
    zip_file(folder / "a.docx", {"word/document.xml": docx_xml("A.")})

    inside = folder / "out"
    got = mirror(folder, inside)
    assert got.returncode == 2 and got.stderr.startswith("refused:")
    assert not inside.exists()

    same = mirror(folder, folder)
    assert same.returncode == 2 and same.stderr.startswith("refused:")

    outer = tmp_path / "outer"
    nested_folder = outer / "src"
    zip_file(nested_folder / "a.docx", {"word/document.xml": docx_xml("A.")})
    got = mirror(nested_folder, outer)
    assert got.returncode == 2 and got.stderr.startswith("refused:")
    assert snapshot(outer) == {"src/a.docx": (nested_folder / "a.docx").read_bytes()}

    got = mirror(tmp_path / "missing", tmp_path / "out3")
    assert got.returncode == 2 and got.stderr.startswith("refused:")
    assert not (tmp_path / "out3").exists()

    got = run(str(OFFICE), "mirror", "--from", str(folder))
    assert got.returncode == 2 and got.stderr.startswith("usage:")


def test_originals_are_unchanged(tmp_path):
    folder = tmp_path / "in"
    zip_file(folder / "a.docx", {"word/document.xml": docx_xml("Keep me.")})
    zip_file(folder / "sub" / "b.ods", {"content.xml": "<bad"})
    (folder / "c.txt").write_text("kept\n", encoding="utf-8")
    before = snapshot(folder)
    assert mirror(folder, tmp_path / "out").returncode == 0
    assert snapshot(folder) == before


def test_two_runs_give_identical_bytes(tmp_path):
    folder = tmp_path / "in"
    zip_file(folder / "a.docx", {"word/document.xml": docx_xml("One.", "Two.")})
    zip_file(
        folder / "b" / "c.pptx",
        {
            "ppt/slides/slide1.xml": f'<p:sld xmlns:a="{A_NS}"><a:p><a:t>S</a:t></a:p></p:sld>'
        },
    )
    first, second = tmp_path / "first", tmp_path / "second"
    assert mirror(folder, first).returncode == 0
    assert mirror(folder, second).returncode == 0
    assert mirror(folder, second).returncode == 0  # again over its own output
    assert snapshot(first) == snapshot(second)
    assert snapshot(first)["a.docx.txt"] == b"One.\n\nTwo.\n"


def test_bite_finds_a_word_only_inside_a_docx(tmp_path):
    folder = tmp_path / "in"
    zip_file(
        folder / "reports" / "q3.docx",
        {"word/document.xml": docx_xml("The marmalade order shipped in September.")},
    )
    (folder / "plain.txt").write_text("Nothing about jam.\n", encoding="utf-8")
    mirror_dir = tmp_path / "mirror"
    assert mirror(folder, mirror_dir).returncode == 0
    box, key = tmp_path / "box", tmp_path / "key"
    init = run(
        str(KERNEL),
        "init",
        "--box",
        str(box),
        "--pile",
        str(mirror_dir),
        "--key",
        str(key),
        *NOW,
    )
    assert init.returncode == 0, init.stderr
    got = run(str(KERNEL), "bite", "--box", str(box), *NOW, "marmalade")
    assert got.returncode == 0, got.stdout + got.stderr
    doc = json.loads(got.stdout)
    assert doc["state"] == "populated"
    assert any(s["where"].startswith("reports/q3.docx.txt") for s in doc["served"])


def test_xlsx_column_aa_comes_straight_after_z(tmp_path):
    folder = tmp_path / "in"
    workbook = (f'{HEAD}<workbook xmlns="{SS_NS}" xmlns:r="{R_NS}"><sheets>'
                '<sheet name="Wide" sheetId="1" r:id="rId1"/></sheets></workbook>')  # fmt: skip
    rels = (f'{HEAD}<Relationships xmlns="{PKG_NS}">'
            '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')  # fmt: skip
    sheet = (f'{HEAD}<worksheet xmlns="{SS_NS}"><sheetData><row r="1">'
             '<c r="Z1" t="inlineStr"><is><t>z</t></is></c>'
             '<c r="AA1" t="inlineStr"><is><t>aa</t></is></c>'
             "</row></sheetData></worksheet>")  # fmt: skip
    zip_file(folder / "wide.xlsx", {"xl/workbook.xml": workbook,
             "xl/_rels/workbook.xml.rels": rels, "xl/worksheets/sheet1.xml": sheet})  # fmt: skip
    out = tmp_path / "out"
    assert mirror(folder, out).returncode == 0
    row = (out / "wide.xlsx.txt").read_text(encoding="utf-8").splitlines()[-1]
    assert row.split(" | ")[25:] == ["z", "aa"]  # columns 26 and 27
