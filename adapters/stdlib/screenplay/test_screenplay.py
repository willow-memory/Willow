"""screenplay: a Fountain or Final Draft script as scenes, cues and dialogue; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "screenplay.py"
spec = importlib.util.spec_from_file_location("screenplay", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = (
    b"Title: Garden Party\nAuthor: Ana Example\n\n"
    b"INT. KITCHEN - DAY #1#\n\nAna waters the tomatoes.\n\nANA\nSix hours of sun.\n\nBEN (V.O.)\n(dryly)\nOr so she says.\n\n"
    b"CUT TO:\n\n.EXT. GARDEN - NIGHT\n\n[[a note]]The moon /* hidden */ rises.\n"
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


def script(text: str) -> str | None:
    return mod.convert(text.encode())


def test_a_script_is_its_title_page_then_scenes_with_cues_and_dialogue():
    out = mod.convert(SAMPLE)
    assert out == (
        "title: Garden Party\nauthor: Ana Example\n\n"
        "scene 1: INT. KITCHEN - DAY\nAna waters the tomatoes.\nANA: Six hours of sun.\nBEN (V.O.): Or so she says.\n\n"
        "scene 2: EXT. GARDEN - NIGHT\nThe moon rises.\n"
    )


def test_headings_are_int_ext_est_ie_or_forced_with_a_dot():
    for h in (
        "INT. A - DAY",
        "EXT. A - DAY",
        "EST. A",
        "INT./EXT. CAR - DAY",
        "INT/EXT CAR",
        "I/E CAR",
        "int. lower - day",
    ):
        assert f"scene 1: {h}" in script(f"{h}\n\nAction.\n")
    assert "scene 1: STAIRS" in script(".STAIRS\n\nAction.\n")
    assert "scene" not in (script("..not a heading\n\nANA\nhi\n") or ""), (
        "two dots are an ellipsis"
    )
    assert "scene 1: INT. A - DAY" in script("INT. A - DAY #12A#\n\nx\n")


def test_dialogue_joins_its_lines_and_leaves_out_parentheticals():
    out = script("INT. A - DAY\n\nANA\n(softly)\nLine one\nline two\n\nBEN ^\nHi\n")
    assert "ANA: Line one line two" in out and "BEN: Hi" in out and "softly" not in out


def test_a_forced_cue_and_an_upper_case_action_line_with_no_dialogue_under_it():
    assert "mcGee: hello" in script("INT. A - DAY\n\n@mcGee\nhello\n")
    assert "ANA: hi" in script("INT. A - DAY\n\nANA\nhi\n")
    out = script("INT. A - DAY\n\nSHOUTED ACTION LINE\n\nANA\nhi\n")
    assert "\nSHOUTED ACTION LINE\n" in out and "SHOUTED ACTION LINE: " not in out


def test_transitions_notes_boneyard_sections_and_page_breaks_are_dealt_with():
    out = script(
        "INT. A - DAY\n\nCUT TO:\n\n> FADE OUT.\n\n===\n\n# Act One\n\n= synopsis\n\nText[[note]] here /* gone */ now.\n"
    )
    assert (
        "CUT TO" not in out
        and "FADE OUT" not in out
        and "synopsis" not in out
        and "===" not in out
    )
    assert "section: Act One" in out and "Text here now." in out.replace("  ", " ")


def test_a_centered_line_is_action_and_a_forced_action_loses_its_bang():
    out = script("INT. A - DAY\n\n> THE END <\n\n!ANA SPEAKS in caps\n")
    assert "THE END" in out and "ANA SPEAKS in caps" in out and "!" not in out


def test_final_draft_paragraphs_are_read_by_type():
    fdx = (
        b'<?xml version="1.0"?><FinalDraft DocumentType="Script"><Content>'
        b'<Paragraph Type="Scene Heading"><Text>INT. KITCHEN - DAY</Text></Paragraph>'
        b'<Paragraph Type="Action"><Text>Ana </Text><Text>waters.</Text></Paragraph>'
        b'<Paragraph Type="Character"><Text>ANA</Text></Paragraph>'
        b'<Paragraph Type="Parenthetical"><Text>(softly)</Text></Paragraph>'
        b'<Paragraph Type="Dialogue"><Text>Six hours.</Text></Paragraph>'
        b'<Paragraph Type="Transition"><Text>CUT TO:</Text></Paragraph></Content></FinalDraft>'
    )
    assert (
        mod.convert(fdx)
        == "scene 1: INT. KITCHEN - DAY\nAna waters.\nANA: Six hours.\n"
    )


def test_other_xml_and_entity_bombs_are_not_read_and_an_empty_script_is_no_result():
    assert mod.convert(b"<root/>") is None
    assert (
        mod.convert(
            b'<!DOCTYPE FinalDraft [<!ENTITY a "x">]><FinalDraft><Content/></FinalDraft>'
        )
        is None
    )
    assert (
        mod.convert(b"") is None
        and mod.convert(b"Just a paragraph of prose.\n") is None
    )


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"scripts/garden.fountain": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "scripts/garden.fountain.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "scripts/garden.fountain": SAMPLE,
            ".hid/scripts/garden.fountain": SAMPLE,
            ".scripts/garden.fountain": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["scripts/garden.fountain.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"scripts/garden.fountain": SAMPLE})
    before = (tmp_path / "src" / "scripts/garden.fountain").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "scripts/garden.fountain.txt").read_bytes() == (
        out / "scripts/garden.fountain.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "scripts/garden.fountain").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.fountain": SAMPLE, "bad.fountain": b"\xff\xfe\x00"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.fountain.txt").is_file() and not (
        out / "bad.fountain.txt"
    ).exists()


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
        assert got.returncode == 2 and "screenplay.py" in got.stderr
