"""land: a placed file is copied, never moved, to its category's pile and
logged with its hash; a tie, an unsorted file, one in two categories and a
copy that would replace a different file wait on you; --dry-run writes
nothing; --json is the same report."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SORT = HERE.parent / "sort" / "sort.py"
NOW = ["--now", "2026-11-12T00:00:00Z"]
spec = importlib.util.spec_from_file_location("land_addon", HERE / "land.py")
la = importlib.util.module_from_spec(spec)
spec.loader.exec_module(la)

CATS = "money:  invoice, bank statement\nhealth: prescription, appointment\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def folder(tmp_path: Path, files: dict) -> Path:
    src = tmp_path / "nest"
    for rel, text in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text(text)
    return src


def sorted_report(tmp_path: Path, pile: dict) -> Path:
    """sort's own --json report over a pile of `pile`'s files."""
    p = tmp_path / "pile"
    for rel, text in pile.items():
        (p / rel).parent.mkdir(parents=True, exist_ok=True)
        (p / rel).write_text(text)
    box = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(box),
        "--pile",
        str(p),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    cats = tmp_path / "categories.txt"
    cats.write_text(CATS)
    got = run(str(SORT), "--box", str(box), "--categories", str(cats), "--json")
    out = tmp_path / "sort.json"
    out.write_text(got.stdout)
    return out


def doc(groups: dict) -> dict:
    return {"addon": "sort", "state": "populated", "said": "",
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups.items()]}  # fmt: skip


def land(
    tmp_path: Path, of: Path, src: Path, *more: str
) -> subprocess.CompletedProcess:
    to = tmp_path / "out"
    to.mkdir(exist_ok=True)
    return run(
        str(HERE / "land.py"),
        "--of",
        str(of),
        "--from",
        str(src),
        "--to",
        str(to),
        *more,
    )


def test_a_placed_file_is_copied_to_its_category_and_logged_with_its_hash(tmp_path):
    src = folder(tmp_path, {"bank/may.txt": "bank statement for may, invoice 7"})
    of = sorted_report(tmp_path, {"bank/may.txt": "bank statement for may, invoice 7"})
    got = land(tmp_path, of, src)
    assert got.returncode == 0, got.stderr
    copy = tmp_path / "out" / "money" / "files" / "bank" / "may.txt"
    assert copy.read_text() == "bank statement for may, invoice 7"
    assert (src / "bank" / "may.txt").is_file()  # copied, never moved
    log = [
        json.loads(x)
        for x in (tmp_path / "out" / "money" / "landed.jsonl").read_text().splitlines()
    ]
    assert log == [{"path": "bank/may.txt", "from": str(src / "bank" / "may.txt"),
                    "sha256": hashlib.sha256(copy.read_bytes()).hexdigest(),
                    "sorted": log[0]["sorted"]}]  # fmt: skip
    assert "bank statement" in log[0]["sorted"]
    assert got.stdout.splitlines()[0].startswith(
        "land: populated, copied 1 files into 1 categories"
    )
    assert "## money" in got.stdout and "bank/may.txt  copied" in got.stdout


def test_a_reader_folder_and_mirror_name_lead_back_to_the_original(tmp_path):
    src = folder(tmp_path, {"letters/rx.pdf": "%PDF", "big.txt": "x"})
    of = tmp_path / "sort.json"
    of.write_text(json.dumps(doc({"health": [("pdf/letters/rx.pdf.txt", "1 hit"),
                                             ("ocr/letters/rx.pdf.txt", "1 hit"),
                                             ("text/big.txt.part2.txt", "1 hit")]})))  # fmt: skip
    got = land(tmp_path, of, src)
    assert got.returncode == 0, got.stderr
    pile = tmp_path / "out" / "health" / "files"
    assert (pile / "letters" / "rx.pdf").read_text() == "%PDF"
    assert (pile / "big.txt").read_text() == "x"
    lines = (tmp_path / "out" / "health" / "landed.jsonl").read_text().splitlines()
    assert len(lines) == 2  # two readers, one original, one copy
    assert la.candidates("pdf/a/b.pdf.txt") == [
        "pdf/a/b.pdf.txt",
        "pdf/a/b.pdf",
        "a/b.pdf",
        "a/b.pdf.txt",
    ]


def test_a_file_at_the_pile_path_itself_is_the_original_first(tmp_path):
    src = folder(tmp_path, {"notes.txt": "plain", "notes": "other"})
    assert la.original(src, "notes.txt") == "notes.txt"
    assert la.original(src, "markdown/notes.txt") == "notes"
    assert la.original(src, "../etc/passwd") is None
    assert la.candidates("notes") == ["notes"]  # tried once, not twice
    assert la.candidates("a/b") == ["a/b", "b"]
    # a mirror of a mirror: nest-read's own .txt, then the reader's part
    assert la.candidates("text/x.md.txt.part2.txt") == [
        "text/x.md.txt.part2.txt", "text/x.md.txt", "text/x.md",
        "x.md", "x.md.txt", "x.md.txt.part2.txt",
    ]  # fmt: skip
    assert la.candidates(".txt") == [".txt"]


def test_ties_unsorted_and_two_categories_wait_and_are_copied_nowhere(tmp_path):
    src = folder(tmp_path, {"a.txt": "a", "b.txt": "b", "c.pdf": "c"})
    of = tmp_path / "sort.json"
    of.write_text(
        json.dumps(
            doc(
                {
                    "money": [("pdf/c.pdf.txt", "1 hit")],
                    "health": [("ocr/c.pdf.txt", "1 hit")],
                    "more than one": [("a.txt", "money 1, health 1")],
                    "unsorted": [("b.txt", "no phrase of yours")],
                }
            )
        )
    )
    got = land(tmp_path, of, src)
    assert got.returncode == 42
    assert (
        not (tmp_path / "out" / "money").exists()
        and not (tmp_path / "out" / "health").exists()
    )
    assert "## waiting on you" in got.stdout
    assert "a.txt  more than one: money 1, health 1" in got.stdout
    assert "b.txt  unsorted: no phrase of yours" in got.stdout
    assert (
        "## in two categories" in got.stdout and "c.pdf  in health, money" in got.stdout
    )


def test_a_different_file_already_there_is_left_and_the_same_one_is_already_there(
    tmp_path,
):
    src = folder(tmp_path, {"a.txt": "new", "b.txt": "same"})
    of = tmp_path / "sort.json"
    of.write_text(json.dumps(doc({"money": [("a.txt", "1 hit"), ("b.txt", "1 hit")]})))
    pile = tmp_path / "out" / "money" / "files"
    pile.mkdir(parents=True)
    (pile / "a.txt").write_text("old")
    (pile / "b.txt").write_text("same")
    got = land(tmp_path, of, src)
    assert got.returncode == 42
    assert (pile / "a.txt").read_text() == "old"
    assert "## left as it was" in got.stdout and "b.txt  already there" in got.stdout
    assert not (tmp_path / "out" / "money" / "landed.jsonl").exists()


def test_no_original_a_bad_category_name_and_a_skipped_prefix(tmp_path):
    src = folder(tmp_path, {"Willow/kernel.py": "k", "x.txt": "x"})
    of = tmp_path / "sort.json"
    of.write_text(json.dumps(doc({"code": [("markdown/Willow/kernel.py.txt", "1 hit")],
                                  "../up": [("x.txt", "1 hit")],
                                  "money": [("gone.txt", "1 hit")]})))  # fmt: skip
    got = land(tmp_path, of, src, "--skip", "Willow/")
    assert got.returncode == 42
    assert not (tmp_path / "out" / "code").exists()
    assert "1 skipped" in got.stdout.splitlines()[0]
    assert "gone.txt  money: no original in the folder" in got.stdout
    assert "x.txt     '../up' isn't a folder name" in got.stdout
    assert not (tmp_path / "up").exists()


def test_dry_run_says_the_same_and_writes_nothing(tmp_path):
    src = folder(tmp_path, {"a.txt": "a"})
    of = tmp_path / "sort.json"
    of.write_text(json.dumps(doc({"money": [("a.txt", "1 hit")]})))
    got = land(tmp_path, of, src, "--dry-run")
    assert got.returncode == 0
    assert list((tmp_path / "out").iterdir()) == []
    assert (
        got.stdout.startswith("land: populated, would copy 1 files")
        and "a.txt  would copy" in got.stdout
    )


def test_a_second_run_copies_nothing_again(tmp_path):
    src = folder(tmp_path, {"a.txt": "a"})
    of = tmp_path / "sort.json"
    of.write_text(json.dumps(doc({"money": [("a.txt", "1 hit")]})))
    land(tmp_path, of, src)
    got = land(tmp_path, of, src)
    assert got.returncode == 0 and "a.txt  already there" in got.stdout
    assert (
        len((tmp_path / "out" / "money" / "landed.jsonl").read_text().splitlines()) == 1
    )


def test_json_is_the_same_report(tmp_path):
    src = folder(tmp_path, {"a.txt": "a", "b.txt": "b"})
    of = tmp_path / "sort.json"
    of.write_text(
        json.dumps(
            doc({"money": [("a.txt", "1 hit")], "unsorted": [("b.txt", "none")]})
        )
    )
    text = land(tmp_path, of, src, "--dry-run")
    js = land(tmp_path, of, src, "--dry-run", "--json")
    assert la.report_text(json.loads(js.stdout)) == text.stdout.rstrip("\n")
    assert json.loads(js.stdout)["groups"][0] == {
        "name": "money",
        "rows": [{"where": "a.txt", "what": "would copy"}],
    }


def test_a_missing_dir_is_made_on_the_first_copy_and_not_by_a_dry_run(tmp_path):
    src = folder(tmp_path, {"a.txt": "a"})
    of = tmp_path / "sort.json"
    of.write_text(json.dumps(doc({"money": [("a.txt", "1 hit")]})))
    to = tmp_path / "new"
    dry = run(
        str(HERE / "land.py"),
        "--of",
        str(of),
        "--from",
        str(src),
        "--to",
        str(to),
        "--dry-run",
    )
    assert dry.returncode == 0 and not to.exists()
    got = run(
        str(HERE / "land.py"), "--of", str(of), "--from", str(src), "--to", str(to)
    )
    assert got.returncode == 0 and (to / "money" / "files" / "a.txt").read_text() == "a"


def test_nothing_placed_is_empty(tmp_path):
    src = folder(tmp_path, {})
    src.mkdir()
    of = tmp_path / "sort.json"
    of.write_text(json.dumps(doc({})))
    got = land(tmp_path, of, src)
    assert got.returncode == 0 and got.stdout.startswith("land: empty,")


def test_what_you_settle_lands_where_you_said_before_anything_sort_said(tmp_path):
    src = folder(
        tmp_path,
        {
            "tie.md": "t",
            "lost.pdf": "l",
            "wrong.txt": "w",
            "Willow/x.md": "x",
            "Willow/y.md": "y",
        },
    )
    of = tmp_path / "sort.json"
    of.write_text(
        json.dumps(
            doc(
                {
                    "money": [("wrong.txt", "1 hit")],
                    "more than one": [("tie.md", "money 1, health 1")],
                    "unsorted": [
                        ("pdf/lost.pdf.txt", "no phrase of yours"),
                        ("Willow/y.md", "none"),
                    ],
                }
            )
        )
    )
    settle = tmp_path / "settle.txt"
    settle.write_text(
        "# mine\n\nhealth: tie.md\nhealth:   lost.pdf\nhealth: wrong.txt\n"
        "code: Willow/x.md\nmoney: not-here.txt\n../up: tie.md\n"
    )
    got = land(tmp_path, of, src, "--settle", str(settle), "--skip", "Willow/")
    assert got.returncode == 42  # the two lines naming nothing wait
    pile = tmp_path / "out" / "health" / "files"
    assert sorted(p.name for p in pile.iterdir()) == ["lost.pdf", "wrong.txt"]
    assert not (tmp_path / "out" / "money").exists()
    assert (tmp_path / "out" / "code" / "files" / "Willow" / "x.md").is_file()
    assert "## waiting on you" not in got.stdout
    assert "not-here.txt  money: settled, but no such file in the folder" in got.stdout
    assert "tie.md        '../up' isn't a folder name" in got.stdout
    log = [
        json.loads(x)
        for x in (tmp_path / "out" / "health" / "landed.jsonl").read_text().splitlines()
    ]
    assert {x["sorted"] for x in log} == {"settled by you"}
    assert la.settles("a: b\nnot a line\n") is None
    assert la.settles("a:\n") is None and la.settles(": b\n") is None
    assert la.settles("") == {}


def test_refusals(tmp_path):
    src = folder(tmp_path, {"a.txt": "a"})
    good = tmp_path / "sort.json"
    good.write_text(json.dumps(doc({})))
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"addon": "todo", "groups": []}))
    broken = tmp_path / "broken.json"
    broken.write_text("{")
    to = tmp_path / "out"
    to.mkdir()
    bad = [
        [],
        ["--of", str(good), "--from", str(src)],
        ["--of", str(good), "--from", str(src), "--to", str(to), "--what", "x"],
        ["--of", str(good), "--from", str(src), "--to", str(to), "--skip"],
        ["--of", str(other), "--from", str(src), "--to", str(to)],
        ["--of", str(broken), "--from", str(src), "--to", str(to)],
        ["--of", str(tmp_path / "none.json"), "--from", str(src), "--to", str(to)],
        ["--of", str(good), "--from", str(src), "--to", str(good)],
        ["--of", str(good), "--from", str(tmp_path / "missing"), "--to", str(to)],
        ["--of", str(good), "--from", str(src), "--to", str(src / "inside")],
        ["--of", str(good), "--from", str(tmp_path), "--to", str(to)],
        [
            "--of",
            str(good),
            "--from",
            str(src),
            "--to",
            str(to),
            "--settle",
            str(broken),
        ],
        [
            "--of",
            str(good),
            "--from",
            str(src),
            "--to",
            str(to),
            "--settle",
            str(tmp_path / "none"),
        ],
        [
            "--of",
            str(good),
            "--from",
            str(src),
            "--to",
            str(to),
            "--settle",
            str(good),
            "--settle",
            str(good),
        ],
    ]
    (src / "inside").mkdir()
    for argv in bad:
        got = run(str(HERE / "land.py"), *argv)
        assert got.returncode == 2, argv
        assert got.stderr and not got.stdout, argv
