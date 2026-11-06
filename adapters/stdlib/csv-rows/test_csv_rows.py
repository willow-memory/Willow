"""csv-rows: a table's header row once, then each row as one passage of its
values, cited by the row's own line, with no word repeated from row to row (so
a question about something absent is answered by no row); the delimiter by one
fixed rule; a headerless
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


def test_the_header_once_then_each_row_as_its_values():
    assert mod.convert(CENSUS) == (
        "[1] Surname; Forename; Townland; DED; County; Age; Sex; Relation to head; Occupation\n\n"
        "[2] Considine; Honora; Caherfeenick; Kilmurry; Clare; 52; Female; Head of Family; Farmer\n\n"
        "[3] Considine; Patrick; Caherfeenick; Kilmurry; Clare; 17; Male; Son; Farm Labourer\n"
    )


def test_a_row_is_numbered_by_the_line_it_starts_on_in_the_source():
    data = (
        b"date,what,notes\n"
        b'2024-03-01,sowed,"broad beans,\nrow two"\n'
        b"\n"
        b"2024-03-09,planted,onions\r\n"
    )
    assert rows(data) == [
        "[1] date; what; notes",
        "[2] 2024-03-01; sowed; broad beans, row two",
        "[5] 2024-03-09; planted; onions",
    ]


def test_an_empty_cell_keeps_its_place_and_empty_cells_at_the_end_go():
    data = b"a,,c\n1,2,3,4,5\n,x\n7,,\ndate,in,out\n"
    assert rows(data) == [
        "[1] a; ; c",
        "[2] 1; 2; 3; 4; 5",
        "[3] ; x",
        "[4] 7",
        "[5] date; in; out",
    ]
    assert rows(b"date,in,out\n2020-11-05,,148\n") == [
        "[1] date; in; out",
        "[2] 2020-11-05; ; 148",
    ]


def test_a_row_of_empty_cells_is_not_a_passage():
    assert rows(b"a,b\n1,2\n , \n3,4\n") == ["[1] a; b", "[2] 1; 2", "[4] 3; 4"]


def test_the_delimiter_is_the_one_that_cuts_the_first_line_into_most_cells():
    assert rows(b"day;amount,net\n3;4,5\n") == ["[1] day;amount; net", "[2] 3;4; 5"]
    assert rows(b"day|amount\n3|4\n") == ["[1] day; amount", "[2] 3; 4"]
    assert rows(b"day\tamount\n3\t4\n") == ["[1] day; amount", "[2] 3; 4"]
    assert rows(b"day,amount;x\n3,4;y\n") == ["[1] day; amount;x", "[2] 3; 4;y"]
    assert rows(b'"day;a",amount,x\n3,4,5\n') == ["[1] day;a; amount; x", "[2] 3; 4; 5"]
    assert rows(b"species\nThemeda triandra\n") == [
        "[1] species",
        "[2] Themeda triandra",
    ]


def test_a_tsv_is_read_by_tabs_whatever_its_first_line_holds():
    data = b"name\tplace, county\nHonora\tKilmurry, Clare\n"
    assert rows(data, tsv=True) == [
        "[1] name; place, county",
        "[2] Honora; Kilmurry, Clare",
    ]
    assert rows(b"a,b,c\td\n1,2,3\t4\n", tsv=True) == ["[1] a,b,c; d", "[2] 1,2,3; 4"]


def test_a_first_line_with_a_number_or_a_date_is_data_not_a_header():
    data = b'30/06/2022,"-112.87","WOOLWORTHS 3350","+26648.24"\n28/06/2022,"-45.38","ALDI",""\n'
    assert rows(data) == [
        "[1] 30/06/2022; -112.87; WOOLWORTHS 3350; +26648.24",
        "[2] 28/06/2022; -45.38; ALDI",
    ]
    assert mod.convert(b"30/06/2022,x\n") == "[1] 30/06/2022; x\n", (
        "one data row is a table"
    )
    assert mod.convert(b"Name,Value\n") is None, "a header alone is not"
    assert rows(b"Name,Value\n12:30,4\n") == ["[1] Name; Value", "[2] 12:30; 4"]


def test_notes_above_the_header_are_kept_by_their_line():
    data = b'"# reader export, device 7"\n# routing 0110\ndate,amount\n2021-05-08,24\n'
    assert rows(data) == [
        '[1] "# reader export, device 7"',
        "[2] # routing 0110",
        "[3] date; amount",
        "[4] 2021-05-08; 24",
    ]


def test_a_byte_order_mark_is_not_part_of_the_first_header():
    assert rows(b"\xef\xbb\xbfDate,Rent\nJul,1680\n") == [
        "[1] Date; Rent",
        "[2] Jul; 1680",
    ]


def test_a_wide_row_is_cut_at_a_cell_and_nothing_is_lost():
    header = ",".join(f"col{k}" for k in range(80)).encode()
    cells = ",".join(f"value{k}" for k in range(80)).encode()
    head, row = rows(header + b"\n" + cells + b"\n")
    for passage, n, word in ((head, 1, "col"), (row, 2, "value")):
        lines = passage.split("\n")
        assert len(lines) > 1 and all(len(x) <= kernel.MAX_CHUNK for x in lines)
        assert all(x.startswith(f"[{n}] {word}") for x in lines)
        got = [c for x in lines for c in x[4:].split("; ")]
        assert got == [f"{word}{k}" for k in range(80)]
        assert not any(x.endswith(";") for x in lines)


def test_one_long_cell_is_cut_at_a_space_into_lines_the_kernel_keeps_whole(tmp_path):
    words = " ".join(f"word{k}" for k in range(300))
    out = mod.convert(b'when,notes\n2024-03-01,"' + words.encode() + b'"\n')
    lines = out.rstrip("\n").split("\n\n")[1].split("\n")
    assert len(lines) > 2 and all(len(x) <= kernel.MAX_CHUNK for x in lines)
    assert lines[0] == "[2] 2024-03-01"
    assert all(x.startswith("[2] word") for x in lines[1:])
    assert lines[1].startswith("[2] word0 word1 ")
    assert " ".join(x[4:] for x in lines[1:]) == words
    (tmp_path / "t.txt").write_text(out)
    got = " ".join(c["text"] for c in kernel.chunks(tmp_path))
    assert all(f"word{k} " in got + " " for k in range(300)), "nothing cut off"


def test_a_cell_with_no_space_is_cut_where_it_must_be():
    lines = rows(b"k\n" + b"x" * 1200 + b"\n")[1].split("\n")
    assert len(lines) == 3 and all(len(x) <= kernel.MAX_CHUNK for x in lines)
    assert "".join(x[4:] for x in lines) == "x" * 1200


def test_a_word_is_cut_only_where_no_space_fits():
    cell = "w" * 496 + " a " + "b" * 600
    assert rows(b"k\n" + cell.encode() + b"\n")[1].split("\n") == [
        "[2] " + "w" * 496,
        "[2] a",
        "[2] " + "b" * (kernel.MAX_CHUNK - 4),
        "[2] " + "b" * (600 - kernel.MAX_CHUNK + 4),
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
    assert (out / "log.TSV.txt").read_text() == "[1] a; b\n\n[2] 1; 2\n"
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
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == [
        "good.csv.txt",
        "good.csv.txt.json",
    ]


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path, {"a/t.csv": CENSUS, ".hid/a/t.csv": CENSUS, ".t.csv": CENSUS}
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == [".places/a/t.csv.txt.json", "a/t.csv.txt"]


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
        and found[0]["text"].startswith("[3] ")
        and "Farm Labourer" in found[0]["text"]
    )
    assert "Honora" not in found[0]["text"]


SEEDS = (
    b"Date,Species,Accession,Seed weight (g),Viability %,Notes\n"
    b"08/01/2026,Themeda triandra,BBG-2026001,28.8,91,\n"
    b"22/01/2026,Leptospermum continentale,BBG-2026002,54.2,81,\n"
    b"05/02/2026,Bursaria spinosa,BBG-2026003,47.8,63,\n"
    b"19/02/2026,Hakea decurrens,BBG-2026004,15.1,96,seed from the creek\n"
)
BANK = b'30/06/2022,"-112.87","WOOLWORTHS 3350","+26648.24"\n28/06/2022,"-45.38","ALDI",""\n'


def test_no_word_repeats_from_row_to_row_so_an_absent_question_finds_no_row(tmp_path):
    files = {"census.csv": CENSUS, "seeds.csv": SEEDS, "bank.csv": BANK}
    got, out = mirror_of(tmp_path, files)
    pile = kernel.chunks(out)
    for name, data in files.items():
        mine = [c for c in pile if c["path"] == name + ".txt"]
        assert len(mine) > 1
        header, body = data.decode().split("\n", 1)
        # a header word that is also a value ("Head of Family") is the row's own
        for word in (
            set(kernel.words(header)) - set(kernel.words(body)) - kernel.FUNCTION
        ):
            served = kernel.rank(pile, f"volcano {word}")
            assert all(c["text"].startswith("[1] ") for c in served), (name, word)
    for word in ("row", "column", "line", "continued", "occupation", "religion"):
        assert not [c for c in kernel.rank(pile, f"volcano {word}") if c["line"] > 1], (
            word
        )
    head = kernel.rank(pile, "Seamus occupation")
    assert [c["text"][:14] for c in head] == ["[1] Surname; F"], "the header row only"


def test_real_questions_land_on_their_row(tmp_path):
    got, out = mirror_of(tmp_path, {"census.csv": CENSUS, "seeds.csv": SEEDS})
    pile = kernel.chunks(out)
    for question, holds in (
        ("how old was Patrick Considine", "Patrick; Caherfeenick; Kilmurry; Clare; 17"),
        ("Hakea decurrens seed", "Hakea decurrens; BBG-2026004; 15.1; 96"),
        ("when did I bank the Bursaria spinosa", "05/02/2026"),
    ):
        found = kernel.rank(pile, question)
        assert found and holds in found[0]["text"], question


def test_each_row_is_placed_on_its_lines_a_quoted_cell_over_several():
    data = b'# a note\nname,town,age\nAda,Ennis,17\n"Ben\nOg",Clare,30\n'
    found = mod.placed(data)
    assert [(a, b) for _, a, b in found] == [(1, 1), (2, 2), (3, 3), (4, 5)]
    assert mod.places(found) == {
        "1": "line 1",
        "3": "line 2",
        "5": "line 3",
        "7": "lines 4-5",
    }
    assert mod.placed(b"name,town\n") == [] and mod.convert(b"name,town\n") is None
