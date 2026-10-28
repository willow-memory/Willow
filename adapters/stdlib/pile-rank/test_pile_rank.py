"""pile-rank: BM25F over words and the folder's own word pairs. A passage
holding the phrase outranks one holding its words apart; a pair only one text
uses is no phrase; a title or a question line weighs more than the body; a
text is served once; it reads a current store and falls back to the folder
when the store is stale, writing neither; and it refuses a bad command line."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PR = HERE / "pile_rank.py"
PS = HERE.parent / "pile-store" / "pile_store.py"
sys.path.insert(0, str(HERE))
import pile_rank  # noqa: E402


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PR), *argv], capture_output=True, text=True
    )


def ask(folder: Path, *more: str) -> dict:
    got = run("--from", str(folder), *more)
    assert got.returncode in (0, 42), got.stderr
    return json.loads(got.stdout)


def where(row: dict) -> list[str]:
    return [s["where"] for s in row["served"]]


def a_folder(tmp: Path, files: dict[str, str]) -> Path:
    folder = tmp / "folder"
    folder.mkdir()
    for name, text in files.items():
        (folder / name).write_text(text)
    return folder


BAKING = {
    "apart.md": "The bread was stale. Sourdough starter needs feeding.\n",
    "loaf.md": "Baked sourdough bread on Sunday.\n",
    "again.md": "More sourdough bread for the market.\n",
}


def test_a_phrase_outranks_its_words_apart(tmp_path):
    folder = a_folder(tmp_path, BAKING)
    row = ask(folder, "sourdough", "bread")
    assert row["ranked_by"] == "pile-rank" and row["read_from"] == "folder"
    assert where(row)[2] == "apart.md:1", where(row)
    assert row["served"][0]["phrases"] == ["sourdough bread"]
    assert row["served"][2]["phrases"] == []


def test_a_pair_one_text_uses_is_no_phrase(tmp_path):
    folder = a_folder(tmp_path, {**BAKING, "again.md": "Market day.\n"})
    r = pile_rank.Ranker(pile_rank.kernel.chunks(folder))
    assert "sourdough bread" not in r.phrases
    assert r.terms("sourdough bread") == ["sourdough", "bread"]


def test_a_title_and_a_question_line_weigh_more_than_the_body(tmp_path):
    folder = a_folder(
        tmp_path,
        {
            "a.md": "Notes on the boiler and the gutter.\n",
            "b.md": "# Boiler\nNotes on the gutter and the shed.\n",
            "c.md": "When is the boiler serviced?\nNotes on the shed.\n",
            "boiler.md": "Notes on the shed and the gutter.\n",
        },
    )
    order = where(ask(folder, "boiler"))
    assert order[-1] == "a.md:1" and set(order[:3]) == {
        "b.md:1",
        "c.md:1",
        "boiler.md:1",
    }


def test_a_text_held_twice_is_served_once(tmp_path):
    memo = "Order more jars before the market.\n"
    folder = a_folder(tmp_path, {"may.md": memo, "june.md": memo, "x.md": "jars\n"})
    assert sorted(where(ask(folder, "jars"))) == ["june.md:1", "x.md:1"]


def test_nothing_held_says_so(tmp_path):
    folder = a_folder(tmp_path, BAKING)
    got = run("--from", str(folder), "kayak")
    assert got.returncode == 42 and json.loads(got.stdout)["state"] == "empty"
    assert run("--from", str(folder), "the", "and").returncode == 42


def test_top_limits_what_is_served(tmp_path):
    folder = a_folder(tmp_path, BAKING)
    assert len(ask(folder, "--top", "1", "sourdough")["served"]) == 1
    assert len(ask(folder, "sourdough")["served"]) == 3


def test_a_current_store_is_read_and_a_stale_one_is_not(tmp_path):
    folder = a_folder(tmp_path, BAKING)
    store = tmp_path / "pile.sqlite"
    built = subprocess.run(
        [sys.executable, str(PS), "--from", str(folder), "--to", str(store)],
        capture_output=True,
        text=True,
    )
    assert built.returncode == 0, built.stderr
    row = ask(folder, "--store", str(store), "sourdough", "bread")
    assert row["read_from"] == "store"
    assert row["served"] == ask(folder, "sourdough", "bread")["served"]
    (folder / "rye.md").write_text("Rye bread, no sourdough bread today.\n")
    before = store.read_bytes()
    row = ask(folder, "--store", str(store), "rye")
    assert row["read_from"] == "folder" and where(row) == ["rye.md:1"]
    assert store.read_bytes() == before
    missing = ask(folder, "--store", str(tmp_path / "none.sqlite"), "rye")
    assert missing["read_from"] == "folder"
    assert not (tmp_path / "none.sqlite").exists()


def test_the_same_question_ranks_the_same_way_each_run(tmp_path):
    folder = a_folder(tmp_path, BAKING)
    assert (
        run("--from", str(folder), "bread").stdout
        == run("--from", str(folder), "bread").stdout
    )


def test_a_bad_command_line_is_refused(tmp_path):
    folder = a_folder(tmp_path, BAKING)
    for argv in ([], ["bread"], ["--from", str(folder)],
                 ["--from", str(folder), "--stray", "bread"],
                 ["--from", str(folder), "--top", "0", "bread"],
                 ["--from", str(folder), "--top", "x", "bread"],
                 ["--from", str(folder), "--store", "", "bread"],
                 ["--from", str(folder / "loaf.md"), "bread"]):  # fmt: skip
        got = run(*argv)
        assert got.returncode == 2 and got.stdout == "", (argv, got.stdout)
    assert "pile_rank.py" in run().stderr
