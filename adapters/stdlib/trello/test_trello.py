"""trello: a Trello board by list with cards, checklists and comments; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "trello.py"
spec = importlib.util.spec_from_file_location("trello", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b'{"name":"Garden","lists":[{"id":"l1","name":"To do"},{"id":"l2","name":"Done"},{"id":"l3","name":"Old","closed":true}],'
    b'"cards":[{"id":"c1","idList":"l1","name":"Stake the tomatoes","desc":"Use the  long canes.","due":"2024-03-09T12:00:00.000Z","labels":[{"name":"urgent"},{"name":""},{"name":"veg"}],"idChecklists":["k1"]},'
    b'{"id":"c2","idList":"l2","name":"Order seed"},{"id":"c3","idList":"l1","name":"Archived","closed":true},{"id":"c4","idList":"l3","name":"In a closed list"}],'
    b'"checklists":[{"id":"k1","name":"Tools","checkItems":[{"name":"canes","state":"complete"},{"name":"twine","state":"incomplete"}]}],'
    b'"actions":[{"type":"commentCard","date":"2024-03-02T08:00:00.000Z","data":{"text":"Borrow Ben\'s.","card":{"id":"c1"}},"memberCreator":{"fullName":"Ana"}},'
    b'{"type":"updateCard","data":{"card":{"id":"c1"}}}]}'
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


def test_a_board_is_its_open_lists_and_cards_with_due_labels_description_checklists_and_comments():
    assert mod.convert(SAMPLE) == (
        "board: Garden\n\nlist: To do\n- Stake the tomatoes (due 2024-03-09) [urgent, veg]\n  Use the long canes.\n"
        "  checklist Tools: [x] canes, [ ] twine\n  comment 2024-03-02 Ana: Borrow Ben's.\n\nlist: Done\n- Order seed\n"
    )


def test_comments_are_oldest_first_and_a_nameless_writer_is_someone():
    doc = (
        b'{"lists":[{"id":"l","name":"L"}],"cards":[{"id":"c","idList":"l","name":"C"}],"actions":['
        b'{"type":"commentCard","date":"2024-05-01T00:00:00Z","data":{"text":"later","card":{"id":"c"}}},'
        b'{"type":"commentCard","date":"2024-04-01T00:00:00Z","data":{"text":"earlier","card":{"id":"c"}},"memberCreator":{"fullName":"Ana"}},'
        b'{"type":"commentCard","data":{"text":"undated","card":{"id":"c"}}},{"type":"commentCard","data":{"text":" ","card":{"id":"c"}}}]}'
    )
    out = mod.convert(doc)
    assert (
        out
        == "board: (unnamed board)\n\nlist: L\n- C\n  comment someone: undated\n  comment 2024-04-01 Ana: earlier\n  comment 2024-05-01 someone: later\n"
    )


def test_an_empty_checklist_a_missing_checklist_and_odd_items_are_left_out():
    doc = (
        b'{"lists":[{"id":"l"}],"cards":[{"id":"c","idList":"l","name":"C","idChecklists":["none","k1","k2"]}],'
        b'"checklists":[{"id":"k1","name":"Empty","checkItems":[]},{"id":"k2","checkItems":[{"name":"one","state":"complete"},5,{"name":" "}]}]}'
    )
    assert (
        mod.convert(doc)
        == "board: (unnamed board)\n\nlist: (unnamed list)\n- C\n  checklist (unnamed): [x] one\n"
    )


def test_a_board_with_no_open_card_or_that_is_no_board_is_not_a_result_and_bad_json_is_an_error():
    for other in (
        b"[]",
        b"5",
        b"null",
        b"{}",
        b'{"lists":[],"cards":[]}',
        b'{"lists":{},"cards":[]}',
        b'{"lists":[],"cards":{}}',
        b'{"lists":[{"id":"l"}],"cards":[{"idList":"l","name":"x","closed":true},{"idList":"l","name":" "},5]}',
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"{nope")
    except ValueError:
        pass
    else:
        raise AssertionError("bad json")


def test_a_json_file_that_is_no_board_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"a.json": SAMPLE, "b.json": b'{"other": 1}'})
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"boards/garden.json": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "boards/garden.json.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "boards/garden.json": SAMPLE,
            ".hid/boards/garden.json": SAMPLE,
            ".boards/garden.json": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["boards/garden.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"boards/garden.json": SAMPLE})
    before = (tmp_path / "src" / "boards/garden.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "boards/garden.json.txt").read_bytes() == (
        out / "boards/garden.json.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "boards/garden.json").read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(tmp_path, {"good.json": SAMPLE, "bad.json": b"{not json"})
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.json.txt").is_file() and not (out / "bad.json.txt").exists()


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
        assert got.returncode == 2 and "trello.py" in got.stderr
