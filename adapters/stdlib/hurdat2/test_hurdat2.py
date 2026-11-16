"""hurdat2: a storm's track rows each carrying the storm's name and id, the
labels written once on a header passage and never in a row, the status and
record codes as NHC's words, missing values as empty cells, each passage
cited by its line, a file that isn't well-formed HURDAT2 skipped and counted,
long files cut between storms under the kernel's megabyte, the same bytes
twice, originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "hurdat2.py"
spec = importlib.util.spec_from_file_location("hurdat2", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
kernel = mod.kernel

TAIL = ", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -999"


def row(
    d: str, t: str, ident: str, status: str, lat: str, lon: str, wind: str, pres: str
) -> str:
    return f"{d}, {t}, {ident}, {status}, {lat}, {lon}, {wind}, {pres}{TAIL}"


MARIA = (
    "AL152017,              MARIA,      3,\n"
    + row("20170919", "0115", "L", "HU", "15.4N", "61.3W", "145", "922")
    + "\n"
    + row("20170920", "1015", "L", "HU", "18.0N", "65.9W", "135", "920")
    + "\n"
    + row("20170921", "0000", " ", "TS", "22.0N", "70.0W", "60", "-999")
    + "\n"
)
UNNAMED = (
    "AL011851,            UNNAMED,      1,\n"
    + row("18510625", "0000", " ", "HU", "28.0N", "94.8W", "80", "-999")
    + "\n"
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


def passages(text: str) -> list[str]:
    found = mod.storms(text)
    assert found
    out = []
    for head, rows in found:
        out += [head] + [p for _, p in rows]
    return out


def test_the_storm_is_a_header_passage_then_each_row_with_the_name_and_id():
    assert passages(MARIA) == [
        "[1] MARIA AL152017; 3 track rows, 2017-09-19 to 2017-09-21;"
        " each row: date time UTC; status; record; position; wind kt; pressure mb",
        "[2] MARIA AL152017; 2017-09-19 01:15; hurricane; landfall; 15.4N 61.3W; 145; 922",
        "[3] MARIA AL152017; 2017-09-20 10:15; hurricane; landfall; 18.0N 65.9W; 135; 920",
        "[4] MARIA AL152017; 2017-09-21 00:00; tropical storm; ; 22.0N 70.0W; 60",
    ]


def test_no_label_is_written_in_a_row_only_on_the_header():
    got = passages(MARIA)
    for p in got[1:]:
        for label in ("wind", "pressure", "kt", "mb", "position", "status", "UTC"):
            assert label not in p.split()
    assert "pressure" in got[0]


def test_a_passage_is_numbered_by_its_line_and_the_next_storm_by_its_own():
    got = passages(MARIA + UNNAMED)
    assert got[0].startswith("[1] ") and got[3].startswith("[4] ")
    assert got[4].startswith("[5] AL011851; 1 track row, 1851-06-25 to 1851-06-25;")
    assert got[5] == "[6] AL011851; 1851-06-25 00:00; hurricane; ; 28.0N 94.8W; 80"


def test_an_unnamed_storm_is_its_id_alone_and_no_row_says_unnamed():
    assert not any("UNNAMED" in p.upper() for p in passages(UNNAMED))


def test_a_missing_wind_or_pressure_is_an_empty_cell_and_a_trailing_one_is_dropped():
    data = (
        "AL012000,               TEST,      2,\n"
        + row("20000101", "0600", " ", "TD", "10.0N", "40.0W", "-99", "1009")
        + "\n"
        + row("20000101", "1200", " ", "TD", "10.5N", "41.0W", "30", "-999")
        + "\n"
    )
    got = passages(data)
    assert got[1].endswith("tropical depression; ; 10.0N 40.0W; ; 1009")
    assert got[2].endswith("tropical depression; ; 10.5N 41.0W; 30")


def test_the_codes_are_nhcs_words_and_one_it_does_not_know_is_kept_as_written():
    data = (
        "AL012000,               TEST,      3,\n"
        + row("20000101", "0600", "P", "SS", "10.0N", "40.0W", "50", "990")
        + "\n"
        + row("20000101", "1200", "Q", "WV", "10.5N", "41.0W", "30", "1009")
        + "\n"
        + row("20000101", "1800", "I", "ZZ", "11.0N", "42.0W", "40", "1000")
        + "\n"
    )
    got = passages(data)
    assert "subtropical storm; minimum pressure;" in got[1]
    assert "tropical wave; Q;" in got[2]
    assert "; ZZ; peak intensity;" in got[3]


def test_a_count_that_is_not_the_rows_that_follow_is_not_read():
    short = MARIA.replace("MARIA,      3,", "MARIA,      4,")
    assert mod.storms(short) is None
    assert mod.storms(MARIA.replace("MARIA,      3,", "MARIA,      2,")) is None


def test_a_first_line_that_is_no_header_and_a_row_that_is_no_row_are_not_read():
    assert mod.storms("Tomatoes want sun.\n") is None
    assert mod.storms(MARIA.replace("20170920, 1015", "soon, later")) is None
    assert mod.storms("") is None
    assert mod.storms("AL152017, MARIA, 0,\n") is None


def test_a_file_cut_between_storms_by_size_with_each_part_placed(tmp_path, monkeypatch):
    big = (MARIA + UNNAMED) * 1
    monkeypatch.setattr(mod, "PART", 400)
    found = mod.storms(big)
    grouped = mod.parts(found)
    assert len(grouped) == 2
    assert grouped[0][0][0].startswith("[1] MARIA") and grouped[1][0][0].startswith(
        "[5] AL011851"
    )
    assert mod.places(grouped[1]) == {"1": "line 5", "3": "line 6"}


def test_a_long_file_is_written_in_parts_under_a_megabyte(tmp_path):
    lines = []
    for n in range(6000):
        lines.append(
            f"AL{n % 99 + 1:02}{2000 + n // 99:04},              STORM{n},      3,"
        )
        for k in range(3):
            lines.append(
                row("20000101", f"{k:02}00", " ", "TS", "10.0N", "40.0W", "40", "1000")
            )
    got, out = mirror_of(tmp_path, {"big.txt": ("\n".join(lines) + "\n").encode()})
    assert got.returncode == 0, got.stderr
    files = sorted(out.glob("big.txt.part*.txt"))
    assert len(files) >= 2
    assert all(f.stat().st_size <= mod.PART for f in files)
    assert not (out / "big.txt.txt").exists()
    first = json.loads((out / ".places" / "big.txt.part0.txt.json").read_text())
    assert first["source"] == "big.txt" and first["places"]["1"] == "line 1"


def test_the_kernel_finds_marias_rows_by_her_name(tmp_path):
    got, out = mirror_of(tmp_path, {"hurdat.txt": (MARIA + UNNAMED).encode()})
    assert got.returncode == 0
    found = kernel.chunks(out)
    hit = [
        c["text"]
        for c in found
        if {"maria", "landfall"} <= set(kernel.words(c["text"]))
    ]
    assert len(hit) == 2 and "10:15" in hit[1]
    assert not any(
        {"maria", "landfall"} <= set(kernel.words(c["text"]))
        for c in found
        if "AL011851" in c["text"]
    )


def test_a_file_that_is_not_utf8_or_not_hurdat2_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "notes.txt": b"Tomatoes want sun.\n",
            "latin.txt": MARIA.encode().replace(b"MARIA", b"MAR\xcdA"),
            "good.txt": MARIA.encode(),
        },
    )
    assert (
        got.returncode == 0
        and "wrote 1 files" in got.stdout
        and "skipped 2" in got.stdout
    )
    assert (out / "good.txt.txt").exists() and not (out / "notes.txt.txt").exists()


def test_nothing_readable_is_exit_42(tmp_path):
    got, out = mirror_of(tmp_path, {"notes.txt": b"Tomatoes want sun.\n"})
    assert got.returncode == 42


def test_the_same_bytes_twice_and_the_originals_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"a/h.txt": MARIA.encode()})
    first = {p.name: p.read_bytes() for p in out.rglob("*") if p.is_file()}
    again = run("mirror", "--from", str(tmp_path / "src"), "--to", str(out))
    assert again.returncode == 0
    assert first == {p.name: p.read_bytes() for p in out.rglob("*") if p.is_file()}
    assert (tmp_path / "src" / "a" / "h.txt").read_bytes() == MARIA.encode()
    assert (out / "a" / "h.txt.txt").exists()


def test_mirror_and_folder_inside_one_another_are_refused(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    assert run("mirror", "--from", str(src), "--to", str(src / "m")).returncode == 2
    assert (
        run("mirror", "--from", str(src / "x"), "--to", str(tmp_path / "o")).returncode
        == 2
    )


def test_a_bad_command_line_is_refused_and_names_the_script():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["look", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "hurdat2.py" in got.stderr


def test_a_part_holds_at_most_the_900000_bytes_the_card_promises():
    assert mod.PART == 900_000 < kernel.MAX_FILE  # the kernel reads no more of a file


def test_the_next_part_starts_empty_so_two_storms_that_exactly_fit_stay_together(
    monkeypatch,
):
    other = UNNAMED.replace("AL011851", "AL021851")
    found = mod.storms(MARIA + UNNAMED + other)
    need = [
        sum(len(x.encode()) + 2 for x in [h] + [r for _, r in rows])
        for h, rows in found
    ]
    assert need[0] > need[2] and need[1] == need[2]
    monkeypatch.setattr(mod, "PART", need[1] + need[2])
    grouped = mod.parts(found)
    assert [len(g) for g in grouped] == [4, 4]
    monkeypatch.setattr(
        mod, "PART", need[0] + need[1]
    )  # the first two fill a part exactly
    assert [len(g) for g in mod.parts(found)] == [6, 2]


def test_a_storm_longer_than_a_part_is_one_part_of_its_own_with_no_empty_one_before(
    monkeypatch,
):
    monkeypatch.setattr(mod, "PART", 10)
    found = mod.storms(MARIA + UNNAMED)
    grouped = mod.parts(found)
    assert [len(g) for g in grouped] == [4, 2]
    assert all(grouped)
