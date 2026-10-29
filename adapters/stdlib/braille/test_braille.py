"""braille: text as uncontracted (grade 1) braille ASCII, a BRF: capitals,
numbers and letter signs, punctuation cells, characters with no cell counted;
lines of N cells and pages of N lines with CR LF and form feeds; approved
answers (with reason and places) or a text file; written once, ASCII only, the
same bytes twice; refusals."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "braille.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-24T00:00:00Z"]
spec = importlib.util.spec_from_file_location("braille", SCRIPT)
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def subject(row: dict) -> str:
    canon = json.dumps(
        {x: row[x] for x in ("path", "data", "cites", "claim")},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def box(tmp_path: Path, seal: bool = True) -> tuple[Path, str]:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    assert (
        k(
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "key"),
            *NOW,
        ).returncode
        == 0
    )
    served = json.loads(
        k("bite", "--box", str(b), *NOW, "how much sun do tomatoes want").stdout
    )["served"]
    row = {
        "path": "sun.md",
        "data": "Six hours of sun.",
        "cites": [served[0]["id"]],
        "claim": "the garden notes",
    }
    (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
    assert (
        k(
            "propose", "--box", str(b), "--file", str(tmp_path / "r.jsonl"), *NOW
        ).returncode
        == 42
    )
    if seal:
        assert k("seal", "--box", str(b), subject(row), *NOW).returncode == 0
    return b, subject(row)


def test_letters_capitals_and_punctuation():
    assert br.cells("Hello, World.") == (",hello1 ,world4", 0)
    assert br.cells("NASA said hi") == (",,nasa said hi", 0)
    assert br.cells("a I") == ("a ,i", 0), (
        "one capital letter is a capital, not a word in capitals"
    )
    assert br.cells("Yes! No? Well; ok: it's a-b") == (
        ",yes6 ,no8 ,well2 ok3 it's a-b",
        0,
    )
    assert (
        br.cells("(see) a/b a & b @ 50% + = *")[0]
        == '"<see"> a_/b a @& b @a #ej.0 "6 "7 "9'
    )


def test_numbers_have_a_number_sign_and_a_letter_after_digits_is_marked():
    assert br.cells("2024")[0] == "#bjbd" and br.cells("0 9")[0] == "#j #i"
    assert br.cells("2a 2k")[0] == "#b;a #bk"
    assert br.cells("abc123")[0] == "abc#abc"


def test_a_decimal_point_and_a_thousands_comma_stay_inside_the_number():
    assert br.cells("3.5")[0] == "#c.e" and br.cells("1,000")[0] == "#a1jjj"
    assert br.cells("see 3. Then 4, and")[0] == "see #c4 ,then #d1 and", (
        "a full stop or comma after a number is punctuation"
    )


def test_quotes_open_and_close():
    assert br.cells('"yes" and "no"')[0] == "8yes0 and 8no0"
    assert br.cells("“yes”")[0] == "8yes0"


def test_a_character_with_no_cell_is_a_space_and_counted():
    assert br.cells("caf\u00e9 \u20ac5") == ("caf   #e", 2)
    text, missing = br.cells("aéb")
    assert text == "a b" and missing == 1


def test_lines_are_cut_at_the_width_on_word_boundaries_and_pages_at_the_height():
    words = " ".join(["abcd"] * 20)  # 20 words of 4 cells
    out = br.layout([words], 14, 3)
    pages = out.split("\f")
    lines = [line for p in pages for line in p.split("\r\n") if line]
    assert (
        all(len(x) <= 14 for x in lines)
        and lines[0] == "abcd abcd abcd"
        and len(lines) == 7
    )
    assert [len([x for x in p.split("\r\n") if x]) for p in pages] == [3, 3, 1]
    assert out.endswith("\r\n") and "\n" not in out.replace("\r\n", "")


def test_a_word_longer_than_a_line_is_cut_and_paragraphs_are_separated_by_a_blank_line():
    out = br.layout(["x" * 25, "next"], 10, 25)
    assert out.split("\r\n") == ["x" * 10, "x" * 10, "xxxxx", "", "next", ""]


def test_an_approved_answer_with_its_reason_and_places_is_written_as_a_brf(tmp_path):
    b, _ = box(tmp_path)
    to = tmp_path / "a.brf"
    got = run("--box", str(b), "--to", str(to))
    assert got.returncode == 0, got.stderr
    text = to.read_bytes().decode("ascii")
    assert text.split("\r\n") == [
        ",six hours of sun4",
        ",why3 the garden notes",
        ",from3 garden4md3#a",
        "",
    ]
    assert text.count("\r\n") == len(text.splitlines()) and text.isascii()
    assert f"wrote {to}: 1 paragraph, 1 page" in got.stdout


def test_a_text_file_is_set_paragraph_by_paragraph(tmp_path):
    src = tmp_path / "t.txt"
    src.write_text("First line.\nSecond.\n\nAnother paragraph, 12.\n")
    got = run("--from", str(src), "--to", str(tmp_path / "t.brf"))
    assert got.returncode == 0 and "2 paragraphs" in got.stdout
    assert (tmp_path / "t.brf").read_bytes().decode().split("\r\n") == [
        ",first line4",
        ",second4",
        "",
        ",another paragraph1 #ab4",
        "",
    ]


def test_a_character_with_no_cell_is_said_on_standard_error(tmp_path):
    src = tmp_path / "t.txt"
    src.write_text("café é\n")
    got = run("--from", str(src), "--to", str(tmp_path / "t.brf"))
    assert (
        "2 characters have no braille cell here" in got.stderr and got.returncode == 0
    )


def test_cells_and_lines_set_the_size(tmp_path):
    src = tmp_path / "t.txt"
    src.write_text(" ".join(["word"] * 12) + "\n")
    run(
        "--from",
        str(src),
        "--to",
        str(tmp_path / "t.brf"),
        "--cells",
        "10",
        "--lines",
        "2",
    )
    pages = (tmp_path / "t.brf").read_bytes().decode().split("\f")
    assert [len(p.split("\r\n")) - 1 for p in pages] == [2, 2, 2] and all(
        len(x) <= 10 for p in pages for x in p.split("\r\n")
    )


def test_nothing_approved_or_an_empty_file_writes_nothing(tmp_path):
    b, _ = box(tmp_path, seal=False)
    got = run("--box", str(b), "--to", str(tmp_path / "a.brf"))
    assert (
        got.returncode == 42
        and not (tmp_path / "a.brf").exists()
        and "no approved answer" in got.stdout
    )
    (tmp_path / "e.txt").write_text("\n\n  \n")
    got = run("--from", str(tmp_path / "e.txt"), "--to", str(tmp_path / "e.brf"))
    assert got.returncode == 42 and not (tmp_path / "e.brf").exists()


def test_a_changed_proposal_is_left_out_and_said(tmp_path):
    b, subj = box(tmp_path)
    f = b / "proposals" / f"{subj[9:]}.json"
    f.write_text(f.read_text().replace("Six", "Ten"))
    got = run("--box", str(b), "--to", str(tmp_path / "a.brf"))
    assert got.returncode == 42 and "1 approval left out" in got.stderr


def test_the_file_is_written_once_private_and_the_same_bytes_twice(tmp_path):
    b, _ = box(tmp_path)
    to = tmp_path / "a.brf"
    assert run("--box", str(b), "--to", str(to)).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    first = to.read_bytes()
    again = run("--box", str(b), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    to.unlink()
    run("--box", str(b), "--to", str(to))
    assert to.read_bytes() == first
    assert (
        run("--box", str(b), "--to", str(tmp_path / "nope" / "a.brf")).returncode == 2
    )


def test_a_record_that_does_not_verify_is_refused(tmp_path):
    b, _ = box(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("garden.md", "garden.mx", 1))
    assert run("--box", str(b), "--to", str(tmp_path / "a.brf")).returncode == 2


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b, _ = box(tmp_path)
    src = tmp_path / "t.txt"
    src.write_text("x\n")
    to = str(tmp_path / "a.brf")
    for argv in ([], ["--box", str(b)], ["--to", to], ["--box", str(b), "--from", str(src), "--to", to], ["--box", str(b), "--to", to, "stray"],
                 ["--box", str(b), "--to", to, "--cells", "5"], ["--box", str(b), "--to", to, "--cells", "x"], ["--box", str(b), "--to", to, "--lines", "0"],
                 ["--from", str(tmp_path / "missing"), "--to", to], ["--box", str(tmp_path), "--to", to]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "braille.py" in run().stderr


def test_two_capital_letters_are_a_word_in_capitals_and_one_is_not():
    assert (
        br.cells("AB")[0] == ",,ab"
        and br.cells("A")[0] == ",a"
        and br.cells("Ab")[0] == ",ab"
        and br.cells("aB")[0] == "a,b"
    )


def test_one_character_with_no_cell_is_said_in_the_singular(tmp_path):
    src = tmp_path / "t.txt"
    src.write_text("café\n")
    got = run("--from", str(src), "--to", str(tmp_path / "t.brf"))
    assert "1 character has no braille cell here and was left as a space" in got.stderr
