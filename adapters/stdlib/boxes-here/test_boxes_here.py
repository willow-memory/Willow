"""boxes-here: a box already in a folder is found by its kernel.json and
said with what waits on it; where the look stopped short is said; a list of
chosen boxes is kept by where they are, each marked not for a model off
this machine; and nothing but that list is written, nor the key read."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "boxes_here.py"
NOW = ["--now", "2026-11-11T00:00:00Z"]

_spec = importlib.util.spec_from_file_location("boxes_here_under_test", SCRIPT)
boxes_here = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(boxes_here)


def k(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def here(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True)  # fmt: skip


def rows(got: subprocess.CompletedProcess) -> dict[str, dict[str, str]]:
    doc = json.loads(got.stdout)
    return {g["name"]: {r["where"]: r["what"] for r in g["rows"]} for g in doc["groups"]}  # fmt: skip


def box(at: Path) -> Path:
    """A record started at `at`; its files and its key are kept outside the
    folder that is looked in."""
    aside = at.parents[len(at.parents) - 2] / f"aside-{'-'.join(at.parts[-2:])}"
    for p in at.parents:
        if p.name == "home":
            aside = p.parent / "aside" / "-".join(at.relative_to(p).parts)
    (aside / "pile").mkdir(parents=True)
    (aside / "pile" / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater at the root.\n"
    )
    at.parent.mkdir(parents=True, exist_ok=True)
    got = k("init", "--box", at, "--pile", aside / "pile", "--key", aside / "key", *NOW)
    assert got.returncode == 0, got.stderr
    return at


def suggest(b: Path, aside: Path, *lines: str) -> None:
    """A question asked, and a suggestion that waits for each line."""
    got = k("bite", "--box", b, *NOW, "how much sun do tomatoes want")
    cite = json.loads(got.stdout)["served"][0]["id"]
    f = aside / "rows.jsonl"
    f.write_text(
        "\n".join(
            json.dumps({"path": f"sun{i}.md", "data": x, "cites": [cite], "claim": "garden.md"})
            for i, x in enumerate(lines)
        )
        + "\n"
    )  # fmt: skip
    out = k("propose", "--box", b, "--file", f, *NOW)
    assert out.stdout.count("pass") == len(lines), out.stdout + out.stderr


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for argv in (
        [], ["--in"], ["--in", tmp_path, "--deep", "x"], ["--in", tmp_path, "--deep", "10"],
        ["--in", tmp_path, "--in", tmp_path], ["--kept"], ["--kept", "f", "--deep", "1"],
        ["keep"], ["keep", "--to", "f"], ["drop", "--from", "f", "b"], ["--nope"],
        ["keep", "--to", tmp_path / "f", tmp_path, "--json"],
    ):  # fmt: skip
        got = here(*argv)
        assert got.returncode == 2 and "boxes_here.py" in got.stderr, argv
        assert got.stderr.startswith("usage: boxes_here.py --in FOLDER"), argv
    got = here("--in", tmp_path / "nope")
    assert got.returncode == 2 and "isn't a folder" in got.stderr


def test_boxes_already_in_a_folder_are_found_with_what_waits_on_each(tmp_path):
    home = tmp_path / "home"
    a = box(home / "taxes" / "box")
    box(home / "letters")
    (home / "plain" / "notes").mkdir(parents=True)
    (home / ".hidden").mkdir()
    (home / ".hidden" / "kernel.json").write_text("{}")
    suggest(a, tmp_path / "aside", "Six hours of sun.", "Water at the root.")
    got = here("--in", home)
    assert got.returncode == 42, "something waits"
    assert got.stdout.splitlines()[0] == (
        f"boxes-here: populated, 2 boxes under {home}; 2 suggestions wait on you"
    )
    assert rows(here("--in", home, "--json")) == {
        "boxes already here": {
            "letters": "1 row: 0 asked, 0 approved, 0 waiting",
            "taxes/box": "4 rows: 1 asked, 0 approved, 2 waiting",
        }
    }, "a folder named with a dot is not looked in"
    got = here("--in", home / "letters")
    assert got.returncode == 0 and "1 box under" in got.stdout
    assert rows(here("--in", home / "letters", "--json")) == {
        "boxes already here": {".": "1 row: 0 asked, 0 approved, 0 waiting"}
    }, "the folder itself is a box"


def test_where_the_look_stopped_short_is_said_and_never_none_here(tmp_path):
    home = tmp_path / "home"
    box(home / "a" / "b" / "c")
    (home / "x" / "y").mkdir(parents=True)
    got = here("--in", home, "--deep", "2")
    assert got.returncode == 0
    assert got.stdout.splitlines()[0] == (
        f"boxes-here: empty, no box in {home} or 2 folders under it; 1 folder not looked in"
    )
    assert rows(here("--in", home, "--deep", "2", "--json")) == {
        "not looked in": {"a/b": "it is 2 folders down, and holds folders of its own"}
    }
    assert "  a/b/c  1 row" in here("--in", home).stdout, "three down by default"
    assert "  a/b/c  1 row" in here("--in", home, "--deep", "4").stdout
    got = here("--in", home, "--deep", "0")
    assert "or 0 folders under it; 1 folder not looked in" in got.stdout
    one = here("--in", home / "a", "--deep", "1")
    assert "no box in" in one.stdout and "1 folder under it" in one.stdout
    assert "it is 1 folder down" in one.stdout


def test_a_box_is_not_looked_inside_and_a_link_is_not_followed(tmp_path):
    home = tmp_path / "home"
    a = box(home / "a")
    (a / "inner").mkdir()
    (a / "inner" / "kernel.json").write_text("{}")
    (home / "loop").symlink_to(home, target_is_directory=True)
    found, skipped = boxes_here.find(home)
    assert found == [a] and skipped == []


def test_a_record_that_cannot_be_counted_is_listed_with_why(tmp_path):
    home = tmp_path / "home"
    a = box(home / "a")
    (home / "b").mkdir()
    (home / "b" / "kernel.json").write_text("{}")
    record = a / "record.jsonl"
    record.write_bytes(record.read_bytes().replace(b"2026-11-11", b"2026-11-12", 1))
    got = here("--in", home, "--json")
    said = rows(got)["boxes already here"]
    assert got.returncode == 42
    assert said["a"].startswith("its chain is broken: ")
    assert said["b"] == "its record couldn't be read: KeyError", (
        "found, and said why it can't be opened"
    )


def test_chosen_boxes_are_kept_by_where_they_are_and_dropped_again(tmp_path):
    home = tmp_path / "home"
    a, b = box(home / "a"), box(home / "b" / "box")
    file = tmp_path / "kept.json"
    got = here("keep", "--to", file, a, b, a)
    assert got.returncode == 0 and got.stdout == f"kept 2 of 3; 2 in {file}\n"
    assert json.loads(file.read_text()) == [
        {"box": str(a.resolve())},
        {"box": str(b.resolve())},
    ]
    assert file.read_text().endswith("]\n")
    again = here("keep", "--to", file, a)
    assert again.stdout == f"kept 0 of 1; 2 in {file}\n", "a box is kept once"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["aside", "home", "kept.json"]
    before = {p: p.read_bytes() for p in home.rglob("*") if p.is_file()}
    listed = here("--kept", file, "--json")
    assert listed.returncode == 0
    assert rows(listed) == {
        "kept boxes": {
            str(a.resolve()): "1 row: 0 asked, 0 approved, 0 waiting",
            str(b.resolve()): "1 row: 0 asked, 0 approved, 0 waiting",
        }
    }
    assert here("--kept", file).stdout.splitlines()[0] == (
        f"boxes-here: populated, 2 boxes kept in {file}"
    )
    got = here("drop", "--to", file, a, tmp_path / "never")
    assert got.stdout == f"dropped 1 of 2; 1 in {file}\n"
    assert [x["box"] for x in json.loads(file.read_text())] == [str(b.resolve())]
    assert {p: p.read_bytes() for p in home.rglob("*") if p.is_file()} == before, (
        "nothing of a box is written, moved or copied"
    )


def test_a_kept_box_that_is_gone_or_waits_is_said(tmp_path):
    home = tmp_path / "home"
    a, b = box(home / "a"), box(home / "b")
    file = tmp_path / "kept.json"
    assert here("keep", "--to", file, a, b).returncode == 0
    suggest(a, tmp_path / "aside", "Six hours of sun.")
    (b / "kernel.json").unlink()
    got = here("--kept", file)
    assert got.returncode == 42
    assert "2 boxes kept in" in got.stdout and "1 suggestion waits on you" in got.stdout
    said = rows(here("--kept", file, "--json"))["kept boxes"]
    assert said[str(b.resolve())] == "no box is there now"
    assert said[str(a.resolve())].endswith("1 waiting")
    empty = here("--kept", tmp_path / "none.json")
    assert empty.returncode == 0 and "empty, no box is kept in" in empty.stdout
    assert not (tmp_path / "none.json").exists(), "reading a list never makes one"


def test_what_is_not_a_box_or_not_a_list_is_refused_and_nothing_written(tmp_path):
    home = tmp_path / "home"
    a = box(home / "a")
    file = tmp_path / "kept.json"
    got = here("keep", "--to", file, a, home)
    assert got.returncode == 2 and "is not a box: it holds no kernel.json" in got.stderr
    assert not file.exists()
    got = here("keep", "--to", tmp_path / "nope" / "kept.json", a)
    assert got.returncode == 2 and "isn't a folder that's there" in got.stderr
    assert not (tmp_path / "nope").exists(), "a missing folder is not made"
    got = here("keep", "--to", home, a)
    assert got.returncode == 2 and "is a folder, not a list" in got.stderr
    for bad in ("{", '{"box": "x"}', '[{"bx": "x"}]', '[{"box": ""}]',
                '[{"box": 3}]', '["x"]', "[3]"):  # fmt: skip
        file.write_text(bad)
        for argv in (["keep", "--to", file, a], ["drop", "--to", file, a], ["--kept", file]):  # fmt: skip
            got = here(*argv)
            assert got.returncode == 2 and str(file) in got.stderr, (bad, argv)
        assert file.read_text() == bad, "a file that isn't a list is left as it is"
    file.write_text("[" + " " * (1 << 20) + "]")
    assert "too long" in here("--kept", file).stderr


def test_the_key_is_never_read_and_only_the_list_is_written():
    code = SCRIPT.read_text(encoding="utf-8")
    body = code.split('"""', 2)[2]
    assert "verifiers" not in body and "--key" not in body and ".pem" not in body
    assert body.count("write_text") == 1 and "open(" not in body
    assert "mkdir" not in body and "unlink" not in body and "rename" not in body
