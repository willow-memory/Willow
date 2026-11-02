"""csv-rows: a table as one passage per row, each value beside its header and
cited by the row's own line; the delimiter by one fixed rule; a headerless
table, notes above the header, a wide row cut so nothing is lost; a file with
no data row, not UTF-8 or not well-formed skipped and counted; the same bytes
twice, originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "csv_rows.py"
spec = importlib.util.spec_from_file_location("csv_rows", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
kernel = mod.kernel

CENSUS = (
    b"Surname,Forename,Townland,DED,County,Age,Sex,Relation to head,Occupation\n"
    b"Considine,Honora,Caherfeenick,Kilmurry,Clare,52,Female,Head of Family,Farmer\n"
    b"Considine,Patrick,Caherfeenick,Kilmurry,Clare,17,Male,Son,Farm Labourer\n"
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


def rows(data: bytes, tsv: bool = False) -> list[str]:
    return mod.convert(data, tsv).rstrip("\n").split("\n\n")


def test_each_row_is_one_passage_with_each_value_beside_its_header():
    assert mod.convert(CENSUS) == (
        "row 2: Surname: Considine; Forename: Honora; Townland: Caherfeenick; DED: Kilmurry; "
        "County: Clare; Age: 52; Sex: Female; Relation to head: Head of Family; Occupation: Farmer\n\n"
        "row 3: Surname: Considine; Forename: Patrick; Townland: Caherfeenick; DED: Kilmurry; "
        "County: Clare; Age: 17; Sex: Male; Relation to head: Son; Occupation: Farm Labourer\n"
    )


def test_a_row_is_numbered_by_the_line_it_starts_on_in_the_source():
    data = (
        b"date,what,notes\n"
        b'2024-03-01,sowed,"broad beans,\nrow two"\n'
        b"\n"
        b"2024-03-09,planted,onions\r\n"
    )
    assert rows(data) == [
        "row 2: date: 2024-03-01; what: sowed; notes: broad beans, row two",
        "row 5: date: 2024-03-09; what: planted; notes: onions",
    ]


def test_empty_cells_extra_cells_short_rows_and_blank_headers():
    data = b"a,,c\n1,2,3,4,5\n,x\n7,,\n"
    assert rows(data) == [
        "row 2: a: 1; column 2: 2; c: 3; column 4: 4; column 5: 5",
        "row 3: column 2: x",
        "row 4: a: 7",
    ]


def test_a_row_of_empty_cells_is_not_a_passage():
    assert rows(b"a,b\n1,2\n , \n3,4\n") == ["row 2: a: 1; b: 2", "row 4: a: 3; b: 4"]


def test_the_delimiter_is_the_one_that_cuts_the_first_line_into_most_cells():
    assert rows(b"day;amount,net\n3;4,5\n") == ["row 2: day;amount: 3;4; net: 5"]
    assert rows(b"day|amount\n3|4\n") == ["row 2: day: 3; amount: 4"]
    assert rows(b"day\tamount\n3\t4\n") == ["row 2: day: 3; amount: 4"]
    assert rows(b"day,amount;x\n3,4;y\n") == ["row 2: day: 3; amount;x: 4;y"]
    assert rows(b'"day;a",amount,x\n3,4,5\n') == ["row 2: day;a: 3; amount: 4; x: 5"]
    assert rows(b"species\nThemeda triandra\n") == ["row 2: species: Themeda triandra"]


def test_a_tsv_is_read_by_tabs_whatever_its_first_line_holds():
    data = b"name\tplace, county\nHonora\tKilmurry, Clare\n"
    assert rows(data, tsv=True) == [
        "row 2: name: Honora; place, county: Kilmurry, Clare"
    ]
    assert rows(b"a,b,c\td\n1,2,3\t4\n", tsv=True) == ["row 2: a,b,c: 1,2,3; d: 4"]


def test_a_first_line_with_a_number_or_a_date_is_data_not_a_header():
    data = b'30/06/2022,"-112.87","WOOLWORTHS 3350","+26648.24"\n28/06/2022,"-45.38","ALDI",""\n'
    assert rows(data) == [
        "row 1: column 1: 30/06/2022; column 2: -112.87; column 3: WOOLWORTHS 3350; column 4: +26648.24",
        "row 2: column 1: 28/06/2022; column 2: -45.38; column 3: ALDI",
    ]
    assert rows(b"Name,Value\n12:30,4\n") == ["row 2: Name: 12:30; Value: 4"]


def test_notes_above_the_header_are_kept_by_their_line():
    data = b'"# reader export, device 7"\n# routing 0110\ndate,amount\n2021-05-08,24\n'
    assert rows(data) == [
        'line 1: "# reader export, device 7"',
        "line 2: # routing 0110",
        "row 4: date: 2021-05-08; amount: 24",
    ]


def test_a_byte_order_mark_is_not_part_of_the_first_header():
    assert rows(b"\xef\xbb\xbfDate,Rent\nJul,1680\n") == [
        "row 2: Date: Jul; Rent: 1680"
    ]


def test_a_wide_row_is_cut_at_a_cell_and_nothing_is_lost():
    header = ",".join(f"col{k}" for k in range(60)).encode()
    cells = ",".join(f"value{k}" for k in range(60)).encode()
    out = mod.convert(header + b"\n" + cells + b"\n")
    lines = out.rstrip("\n").split("\n")
    assert "" not in lines, "one passage: no blank line inside the row"
    assert len(lines) > 1 and all(len(x) <= kernel.MAX_CHUNK for x in lines)
    assert lines[0].startswith("row 2: col0: value0; ")
    assert all(x.startswith("row 2, continued: col") for x in lines[1:])
    pairs = [p for x in lines for p in x.split(": ", 1)[1].split("; ")]
    assert pairs == [f"col{k}: value{k}" for k in range(60)]
    assert not any(x.endswith(";") for x in lines)


def test_one_long_cell_is_cut_at_a_space_into_lines_the_kernel_keeps_whole(tmp_path):
    words = " ".join(f"word{k}" for k in range(300))
    out = mod.convert(b'when,notes\n2024-03-01,"' + words.encode() + b'"\n')
    lines = out.rstrip("\n").split("\n")
    assert len(lines) > 2 and all(len(x) <= kernel.MAX_CHUNK for x in lines)
    assert lines[0] == "row 2: when: 2024-03-01"
    assert lines[1].startswith("row 2, continued: notes: word0 word1 ")
    assert all(x.startswith("row 2, continued: word") for x in lines[2:])
    rest = [x.split(": ", 1)[1] for x in lines[2:]]
    assert " ".join([lines[1].split("notes: ", 1)[1], *rest]) == words
    (tmp_path / "t.txt").write_text(out)
    got = " ".join(c["text"] for c in kernel.chunks(tmp_path))
    assert all(f"word{k} " in got + " " for k in range(300)), "nothing cut off"


def test_a_cell_with_no_space_is_cut_where_it_must_be():
    out = mod.convert(b"k\n" + b"x" * 1200 + b"\n")
    lines = out.rstrip("\n").split("\n")
    assert all(len(x) <= kernel.MAX_CHUNK for x in lines)
    assert lines[0].startswith("row 2: k: xxx") and len(lines) == 3
    assert "".join(x.split(": ", 1)[1] for x in lines) == "k: " + "x" * 1200


def test_a_word_is_cut_only_where_no_space_fits():
    cell = "w" * 489 + " a " + "b" * 600
    lines = mod.convert(b"k\n" + cell.encode() + b"\n").rstrip("\n").split("\n")
    assert lines == [
        "row 2: k: " + "w" * 489,
        "row 2, continued: a",
        "row 2, continued: " + "b" * (kernel.MAX_CHUNK - 18),
        "row 2, continued: " + "b" * (600 - kernel.MAX_CHUNK + 18),
    ]


def test_a_table_with_no_data_row_is_not_a_result():
    for data in (
        b"",
        b"\n\n",
        b"date,amount\n",
        b"# a note\n",
        b"# a note\ndate,amount\n , \n",
    ):
        assert mod.convert(data) is None, data


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path, {"Family History/census.csv": CENSUS, "log.TSV": b"a\tb\n1\t2\n"}
    )
    assert got.returncode == 0, got.stderr
    assert (out / "Family History/census.csv.txt").read_text() == mod.convert(CENSUS)
    assert (out / "log.TSV.txt").read_text() == "row 2: a: 1; b: 2\n"
    assert got.stdout.strip().endswith("wrote 2 files to " + str(out) + "; skipped 0")


def test_what_cannot_be_read_as_a_table_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "good.csv": CENSUS,
            "latin1.csv": "name,town\nHonora,Kilm\xfarry\n".encode("latin-1"),
            "header-only.csv": b"date,amount\n",
            "empty.csv": b"",
            "bad-quote.csv": b'a,b\n1,"2"x\n',
            "notes.txt": b"a,b\n1,2\n",
        },
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 4" in got.stdout
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == ["good.csv.txt"]


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path, {"a/t.csv": CENSUS, ".hid/a/t.csv": CENSUS, ".t.csv": CENSUS}
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["a/t.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"t.csv": CENSUS})
    before = (tmp_path / "src" / "t.csv").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "t.csv.txt").read_bytes() == (out / "t.csv.txt").read_bytes()
    assert (tmp_path / "src" / "t.csv").read_bytes() == before


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n", "h.csv": b"a,b\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout
    assert "skipped 1" in got.stdout


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
        ["mirror", "--from", "a", "--into", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "csv_rows.py mirror" in got.stderr


def test_the_kernel_finds_one_person_by_name_on_the_mirror(tmp_path):
    got, out = mirror_of(tmp_path, {"census.csv": CENSUS})
    found = kernel.rank(kernel.chunks(out), "Patrick Considine occupation")
    assert (
        found
        and found[0]["text"].startswith("row 3: ")
        and "Farm Labourer" in found[0]["text"]
    )
    assert "Honora" not in found[0]["text"]
