"""scan: an index's answers are the kernel's, byte for byte, and only faster."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import scan  # noqa: E402

SCAN = HERE / "scan.py"
CASES = json.loads((ROOT / "vectors" / "cases.json").read_text(encoding="utf-8"))[
    "cases"
]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCAN), *argv], capture_output=True, text=True
    )


def write(folder: Path, files: dict[str, str | bytes]) -> Path:
    for rel, data in files.items():
        p = folder / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
    return folder


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}  # fmt: skip


#: a folder with what the kernel's rank turns on: rare and common words, word
#: forms, a serial matched by its ending, the same text in two places, a log's
#: date heading, a folder's name, web pages, and a words list
FOLDER = {
    "garden.md": "Tomatoes want six hours of sun.\n\nWater tomatoes at the root.\n",
    "care/2024-03-01.md": "Dad's weight 71.2 kg.\n\nDad owes the clinic.\n",
    "care/2025-01-09.md": "Weight 75.1 kg, owing nothing.\n",
    "log.md": "2021-05-14\nOwed the vet.\n\nThe van sold.\n\n2023-02-01\nOwes the vet again.\n",
    "a/memo.txt": "Order jars for the honey.\n",
    "b/memo.txt": "Order jars for the honey.\n",
    "c/jar.txt": "Jars cracked in the van.\n",
    "lot.html": "<p>The blue Civic, VIN 1HGEJ6672841, one owner.</p>\n",
    "parts.md": "Serial 2841 is the pump; 841 is a page.\n",
    "invoice.md": "Invoice 7 outstanding since June.\n",
    ".hidden/secret.md": "Tomatoes are hidden here.\n",
    # its date is a paragraph of its own, a passage no question about the vet holds
    "diary.md": "2021-05-14\n\nPaid the vet.\n\n2023-02-01\n\nPaid the vet twice.\n",
    # held through its folder's name; its copy elsewhere doesn't hold the
    # question, yet still counts as a copy, and puts it after visit/other.md
    "dad/clinic/visit.md": "Weight checked.\n",
    "dad/clinic/visit/other.md": "Weight again.\n",
    "elsewhere.md": "Weight checked.\n",
}
QUESTIONS = [
    "how much sun do tomatoes want", "tomatoes", "water the tomatoes", "dad weight",
    "who owes the vet", "owed", "order jars", "jars", "honey jars van",
    "that one ending 672841", "2841", "841", "pump 2841", "civic owner",
    "who owes me money", "care", "invoice", "the", "what", "nothing at all here",
    "dad owes", "jar", "sold van", "paid the vet", "dad clinic visit weight",
]  # fmt: skip
WORDS = {"money": ["invoice", "outstanding"], "jar": ["jars"], "dad": ["care"]}


@pytest.fixture
def indexed(tmp_path):
    folder = write(tmp_path / "folder", FOLDER)
    assert (
        run("index", "--from", str(folder), "--to", str(tmp_path / "ix")).returncode
        == 0
    )
    return kernel.chunks(folder), scan.Index(tmp_path / "ix")


@pytest.mark.parametrize("alias", [{}, WORDS])
def test_every_passage_ranked_as_the_kernel_ranks_it(indexed, alias):
    pile, ix = indexed
    for q in QUESTIONS:
        for top in (1, 3, 10**9):
            kernel.TOP, was = top, kernel.TOP
            try:
                want = kernel.rank(pile, q, alias)
            finally:
                kernel.TOP = was
            got = ix.rank(q, alias, top)
            assert [(c["path"], c["line"], c["id"]) for c in got] == [
                (c["path"], c["line"], c["id"]) for c in want
            ], (q, top)


def test_the_kernel_is_put_back(indexed):
    _, ix = indexed
    top, dates = kernel.TOP, kernel.dates
    ix.rank("tomatoes", {}, 50)
    assert (kernel.TOP, kernel.dates) == (top, dates)


def test_every_ranking_vector_the_four_kernels_are_held_to(tmp_path):
    """vectors/cases.json: the piles, written byte for byte, and each case's
    passages as kernel.py, Java, TypeScript and C# serve them."""
    ixs = []
    for n, case in enumerate(CASES["chunks"]):
        folder = tmp_path / f"pile{n}"
        folder.mkdir()
        for f in case["pile"]:
            p = folder.joinpath(*f["parts"])
            p.parent.mkdir(parents=True, exist_ok=True)
            if "b64" in f:
                p.write_bytes(base64.b64decode(f["b64"]))
            else:  # a big one, written as a run: n times `repeat`, then `then`
                p.write_bytes((f["repeat"] * f["n"] + f["then"]).encode())
        got = run("index", "--from", str(folder), "--to", str(tmp_path / f"ix{n}"))
        assert got.returncode in (0, 42), got.stderr
        ixs.append(scan.Index(tmp_path / f"ix{n}"))
    for case in CASES["rank"]:
        got = ixs[case["pile"]].rank(case["bite"], case["alias"], kernel.TOP)
        assert [c["id"] for c in got] == case["ids"], case["bite"]
    assert len(CASES["rank"]) > 600


def test_an_index_is_the_same_bytes_every_time(tmp_path):
    folder = write(tmp_path / "folder", FOLDER)
    run("index", "--from", str(folder), "--to", str(tmp_path / "one"))
    run("index", "--from", str(folder), "--to", str(tmp_path / "two"))
    assert snapshot(tmp_path / "one") == snapshot(tmp_path / "two")
    assert sorted(snapshot(tmp_path / "one")) == sorted(scan.FILES)


def test_scan_says_which_other_index_lacks_the_words(tmp_path):
    old = write(
        tmp_path / "old", {"rfc1867.c": "if (oom) bailout();\n\nfree(state);\n"}
    )
    new = write(tmp_path / "new", {"rfc1867.c": "if (oom) unwind();\n\nfree(state);\n"})
    got = run("index", "--from", str(old), "--to", str(tmp_path / "ix" / "old"))
    assert got.returncode == 2 and "make it first" in got.stderr
    assert not (tmp_path / "ix").exists()
    (tmp_path / "ix").mkdir()
    for f in (old, new):
        assert (
            run(
                "index", "--from", str(f), "--to", str(tmp_path / "ix" / f.name)
            ).returncode
            == 0
        )
    qs = tmp_path / "q.txt"
    qs.write_text("# what the advisory says\nb\toom bailout\n\nfree state\n")
    got = run("scan", "--index", str(tmp_path / "ix/old"), "--index", str(tmp_path / "ix/new"),
              "--questions", str(qs))  # fmt: skip
    assert got.returncode == 0, got.stderr
    rows = [json.loads(line) for line in got.stdout.splitlines()]
    assert [(r["index"], r["question"], r["state"]) for r in rows] == [
        ("old", "b", "populated"), ("old", "4", "populated"),
        ("new", "b", "populated"), ("new", "4", "populated"),
    ]  # fmt: skip
    bailout, freed = rows[0]["served"][0], rows[1]["served"][0]
    assert bailout["where"] == "rfc1867.c:1" and "bailout" in bailout["text"]
    assert (bailout["held_in"], bailout["gone_from"]) == ([], ["new"])
    assert (freed["held_in"], freed["gone_from"]) == (["new"], [])
    assert rows[2]["served"][0]["text"] == "if (oom) unwind();"  # "oom" holds half
    assert rows[2]["served"][0]["gone_from"] == ["old"]
    assert bailout["rank"] == 1 and bailout["echo"] is False


def test_nothing_holds_it_is_42(tmp_path):
    write(tmp_path / "f", {"a.md": "Nothing to see.\n"})
    run("index", "--from", str(tmp_path / "f"), "--to", str(tmp_path / "ix"))
    (tmp_path / "q").write_text("tomatoes\n")
    got = run(
        "scan", "--index", str(tmp_path / "ix"), "--questions", str(tmp_path / "q")
    )
    assert got.returncode == 42 and json.loads(got.stdout)["state"] == "empty"


def test_a_folder_with_nothing_to_read_is_42(tmp_path):
    (tmp_path / "empty").mkdir()
    got = run("index", "--from", str(tmp_path / "empty"), "--to", str(tmp_path / "ix"))
    assert got.returncode == 42 and "indexed 0 passages" in got.stdout


def test_top_and_a_words_list(tmp_path):
    write(tmp_path / "f", FOLDER)
    run("index", "--from", str(tmp_path / "f"), "--to", str(tmp_path / "ix"))
    (tmp_path / "q").write_text("who owes me money\n")
    (tmp_path / "w").write_text("money = invoice, outstanding\n")
    ix = ["--index", str(tmp_path / "ix"), "--questions", str(tmp_path / "q")]
    plain = json.loads(run("scan", *ix, "--top", "1").stdout)
    assert [s["where"] for s in plain["served"]] == ["care/2025-01-09.md:1"]
    worded = json.loads(run("scan", *ix, "--words", str(tmp_path / "w")).stdout)
    assert worded["served"][0]["where"] == "invoice.md:1"
    (tmp_path / "w").write_text("money invoice\n")
    got = run("scan", *ix, "--words", str(tmp_path / "w"))
    assert got.returncode == 2 and "words list line 1" in got.stderr


def test_the_folder_is_never_changed(tmp_path):
    folder = write(tmp_path / "folder", FOLDER)
    before = snapshot(folder)
    run("index", "--from", str(folder), "--to", str(tmp_path / "ix"))
    (tmp_path / "q").write_text("tomatoes\n")
    run("scan", "--index", str(tmp_path / "ix"), "--questions", str(tmp_path / "q"))
    assert snapshot(folder) == before


def test_an_index_from_another_kernel_or_tampered_is_refused(tmp_path):
    write(tmp_path / "f", FOLDER)
    ix = tmp_path / "ix"
    run("index", "--from", str(tmp_path / "f"), "--to", str(ix))
    (tmp_path / "q").write_text("tomatoes\n")
    ask = ["scan", "--index", str(ix), "--questions", str(tmp_path / "q")]
    head = json.loads((ix / "index.json").read_text())
    (ix / "index.json").write_text(json.dumps({**head, "kernel": "0" * 64}))
    got = run(*ask)
    assert got.returncode == 2 and "another kernel.py" in got.stderr and not got.stdout
    (ix / "index.json").write_text(json.dumps({**head, "format": "other/1"}))
    assert "another kind" in run(*ask).stderr
    (ix / "index.json").write_text(json.dumps(head))
    lines = (ix / "chunks.jsonl").read_text().splitlines()
    (ix / "chunks.jsonl").write_text("\n".join(lines[1:]) + "\n")
    got = run(*ask)
    assert got.returncode == 2 and "don't match" in got.stderr
    (ix / "index.json").unlink()
    got = run(*ask)
    assert got.returncode == 2 and "not an index" in got.stderr


def test_where_an_index_may_go(tmp_path):
    folder = write(tmp_path / "folder", FOLDER)
    before = snapshot(folder)
    for to in (folder / "ix", tmp_path):
        got = run("index", "--from", str(folder), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr
    write(tmp_path / "taken", {"mine.txt": "not an index"})
    got = run("index", "--from", str(folder), "--to", str(tmp_path / "taken"))
    assert got.returncode == 2 and "isn't an index" in got.stderr
    assert snapshot(tmp_path / "taken") == {"mine.txt": b"not an index"}
    got = run("index", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m"))
    assert got.returncode == 2 and "not a folder" in got.stderr
    assert snapshot(folder) == before
    run("index", "--from", str(folder), "--to", str(tmp_path / "ix"))
    write(folder, {"new.md": "Tomatoes again.\n"})
    assert (
        run("index", "--from", str(folder), "--to", str(tmp_path / "ix")).returncode
        == 0
    )
    visible = sum(not rel.startswith(".") for rel in FOLDER)
    assert (
        json.loads((tmp_path / "ix" / "index.json").read_text())["files"] == visible + 1
    )


def test_a_scan_refuses_before_printing_anything(tmp_path):
    write(tmp_path / "a" / "x", FOLDER)
    write(tmp_path / "b" / "x", FOLDER)
    for side in ("a", "b"):
        run(
            "index",
            "--from",
            str(tmp_path / side / "x"),
            "--to",
            str(tmp_path / side / "ix"),
        )
    (tmp_path / "q").write_text("tomatoes\n")
    got = run("scan", "--index", str(tmp_path / "a/ix"), "--index", str(tmp_path / "b/ix"),
              "--questions", str(tmp_path / "q"))  # fmt: skip
    assert got.returncode == 2 and "same folder name" in got.stderr and not got.stdout
    got = run("scan", "--index", str(tmp_path / "a/ix"), "--index", str(tmp_path / "nope"),
              "--questions", str(tmp_path / "q"))  # fmt: skip
    assert got.returncode == 2 and "not an index" in got.stderr and not got.stdout
    (tmp_path / "q").write_text("# only a note\n\n")
    got = run(
        "scan", "--index", str(tmp_path / "a/ix"), "--questions", str(tmp_path / "q")
    )
    assert got.returncode == 2 and "holds no question" in got.stderr


@pytest.mark.parametrize(
    "argv",
    [
        [], ["find"], ["index"], ["index", "--from", "f"], ["index", "--from", "f", "--to"],
        ["index", "--from", "f", "--to", "t", "--index", "i"],
        ["index", "--from", "f", "--from", "g", "--to", "t"],
        ["scan", "--index", "i"], ["scan", "--questions", "q"],
        ["scan", "--index", "i", "--questions", "q", "--top", "0"],
        ["scan", "--index", "i", "--questions", "q", "--top", "x"],
        ["scan", "--index", "i", "--questions", "q", "--to", "t"],
        ["scan", "--index", "i", "--questions", "q", "--questions", "r"],
    ],
)  # fmt: skip
def test_a_bad_command_line_is_refused(argv, tmp_path):
    got = subprocess.run([sys.executable, str(SCAN), *argv], capture_output=True,
                         text=True, cwd=tmp_path)  # fmt: skip
    assert (
        got.returncode == 2 and "scan.py" in got.stderr and not list(tmp_path.iterdir())
    )
