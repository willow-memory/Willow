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
#: the kernel's own contract, which one test holds the index to; read only by
#: that test, so the rest stand in a copy of this folder taken without it
VECTORS = ROOT / "vectors" / "cases.json"


def cases() -> dict:
    if not VECTORS.is_file():
        pytest.fail(f"this test needs the kernel's vectors, {VECTORS}: copy "
                    "vectors/cases.json beside kernel.py, as willow keeps it")  # fmt: skip
    return json.loads(VECTORS.read_text(encoding="utf-8"))["cases"]


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
            want = kernel.rank(pile, q, alias, top)
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
    CASES = cases()
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


#: FOLDER, a release later: passages edited, one added, one gone, a date
#: heading kept above an edited line, and two copies edited alike
LATER = {
    **{k: v for k, v in FOLDER.items() if k != "invoice.md"},
    "garden.md": "Tomatoes want six hours of sun.\n\nWater tomatoes at dawn.\n",
    "diary.md": "2021-05-14\n\nPaid the vet.\n\n2023-02-01\n\nPaid the vet three times.\n",
    "a/memo.txt": "Order jars and lids for the honey.\n",
    "b/memo.txt": "Order jars and lids for the honey.\n",
    "care/2026-02-02.md": "Dad's weight 74 kg; paid the clinic.\n",
}


def test_changed_from_is_the_kernel_on_only_what_changed(tmp_path):
    for name, files in (("old", FOLDER), ("new", LATER)):
        write(tmp_path / name, files)
        run(
            "index",
            "--from",
            str(tmp_path / name),
            "--to",
            str(tmp_path / f"ix-{name}"),
        )
    new = kernel.chunks(tmp_path / "new")
    before = {c["id"] for c in kernel.chunks(tmp_path / "old")}
    day = {id(c): d for c, d in zip(new, kernel.dates(new))}
    changed = [c for c in new if c["id"] not in before]
    assert len(changed) == 5
    ix = scan.Index(tmp_path / "ix-new")
    for q in [*QUESTIONS, "jars lids honey", "paid vet times", "dad paid clinic"]:
        for top in (3, 10**9):
            want = kernel.rank(
                changed, q, WORDS, top, lambda pile: [day[id(c)] for c in pile]
            )
            got = ix.rank(q, WORDS, top, before)
            assert [(c["path"], c["line"]) for c in got] == [
                (c["path"], c["line"]) for c in want
            ], (q, top)
    paid = ix.rank("paid the vet", {}, 3, before)
    assert [c["path"] + ":" + str(c["line"]) for c in paid] == [
        "diary.md:7",  # dated 2023 by a heading that didn't change
        "care/2026-02-02.md:1",
    ]
    jars = ix.rank("order jars", {}, 3, before)
    assert [c["path"] for c in jars] == ["a/memo.txt"]  # two copies, served once


def test_changed_from_on_the_command_line(tmp_path):
    for name, files in (("old", FOLDER), ("new", LATER)):
        write(tmp_path / name, files)
        run(
            "index",
            "--from",
            str(tmp_path / name),
            "--to",
            str(tmp_path / f"ix-{name}"),
        )
    (tmp_path / "q").write_text(
        "w\twater tomatoes\nn\tnothing changed about civic owner\n"
    )
    ask = ["scan", "--index", str(tmp_path / "ix-new"), "--index", str(tmp_path / "ix-old"),
           "--questions", str(tmp_path / "q"), "--changed-from", str(tmp_path / "ix-old")]  # fmt: skip
    got = run(*ask)
    assert got.returncode == 0, got.stderr
    rows = [json.loads(line) for line in got.stdout.splitlines()]
    assert [(r["index"], r["question"], r["changed_from"], r["state"]) for r in rows] == [
        ("ix-new", "w", "ix-old", "populated"), ("ix-new", "n", "ix-old", "empty"),
        ("ix-old", "w", "ix-old", "empty"), ("ix-old", "n", "ix-old", "empty"),
    ]  # fmt: skip
    [water] = rows[0]["served"]
    assert water["where"] == "garden.md:3" and water["gone_from"] == ["ix-old"]
    plain = run(*ask[:-2])  # without it, the unchanged first paragraph is served too
    served = json.loads(plain.stdout.splitlines()[0])["served"]
    assert [s["where"] for s in served][:2] == ["garden.md:3", "garden.md:1"]
    got = run(*ask[:-1], str(tmp_path / "nope"))
    assert got.returncode == 2 and "not an index" in got.stderr and not got.stdout


def test_todo_lists_what_the_served_file_marks(tmp_path):
    write(tmp_path / "f", {
        "session.c": "static void reset(void)\n{\n\t/* TODO: these should be reset\n"
                     "\t   at shutdown, always */\n\tstate = 0;\n}\n\n"
                     "void cleanup(void) { state = 0; } // FIXME: twice\n",
        "other.c": "/* TODO: not this file */\nint state;\n",
        "plain.c": "int reset_state;\n",
    })  # fmt: skip
    run("index", "--from", str(tmp_path / "f"), "--to", str(tmp_path / "ix"))
    (tmp_path / "q").write_text("reset state\n")
    ask = ["scan", "--index", str(tmp_path / "ix"), "--questions", str(tmp_path / "q")]
    row = json.loads(run(*ask, "--todo").stdout)
    [first] = [s for s in row["served"] if s["where"] == "session.c:1"]
    assert first["marked"] == [
        {"where": "session.c:3", "text": "/* TODO: these should be reset"},
        {
            "where": "session.c:8",
            "text": "void cleanup(void) { state = 0; } // FIXME: twice",
        },
    ]
    assert all(
        s["marked"] == [] for s in row["served"] if s["where"].startswith("plain")
    )
    assert all("marked" not in s for s in json.loads(run(*ask).stdout)["served"])


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
        ["scan", "--index", "i", "--questions", "q", "--todo", "--todo"],
        ["scan", "--index", "i", "--questions", "q", "--changed-from"],
        ["index", "--from", "f", "--to", "t", "--todo"],
    ],
)  # fmt: skip
def test_a_bad_command_line_is_refused(argv, tmp_path):
    got = subprocess.run([sys.executable, str(SCAN), *argv], capture_output=True,
                         text=True, cwd=tmp_path)  # fmt: skip
    assert (
        got.returncode == 2 and "scan.py" in got.stderr and not list(tmp_path.iterdir())
    )


def reference_bm25(pile: list[dict], q: str) -> list[tuple[str, int]]:
    """BM25 as the textbook writes it, over every passage, by brute force."""
    import math

    docs = [kernel.words(c["text"]) for c in pile]
    ws = [w for w in dict.fromkeys(kernel.words(q)) if w not in kernel.FUNCTION]
    n, avg = len(docs), sum(map(len, docs)) / len(docs)
    df = {w: sum(w in d for d in docs) for w in ws}
    out = []
    for i, d in enumerate(docs):
        s = sum(
            math.log((n - df[w] + 0.5) / (df[w] + 0.5) + 1)
            * d.count(w) * 2.2 / (d.count(w) + 1.2 * (0.25 + 0.75 * len(d) / avg))
            for w in ws if d.count(w)
        )  # fmt: skip
        if s > 0:
            out.append((-s, i))
    return [(pile[i]["path"], pile[i]["line"]) for _, i in sorted(out)]


def test_bm25_ranks_as_bm25_does_over_all_or_only_what_changed(tmp_path):
    for name, files in (("old", FOLDER), ("new", LATER)):
        write(tmp_path / name, files)
        run(
            "index",
            "--from",
            str(tmp_path / name),
            "--to",
            str(tmp_path / f"ix-{name}"),
        )
    new = kernel.chunks(tmp_path / "new")
    before = {c["id"] for c in kernel.chunks(tmp_path / "old")}
    changed = [c for c in new if c["id"] not in before]
    ix = scan.Index(tmp_path / "ix-new")
    for q in [*QUESTIONS, "jars lids honey", "paid vet times"]:
        got = [(c["path"], c["line"]) for c in ix.bm25(q, 10**9)]
        assert got == reference_bm25(new, q), q
        got = [(c["path"], c["line"]) for c in ix.bm25(q, 10**9, before)]
        assert got == (reference_bm25(changed, q) if changed else []), q
    assert len(ix.bm25("tomatoes", 1)) == 1 and ix.bm25("the", 5) == []
    (tmp_path / "q").write_text("t\ttomatoes water\n")
    ask = [
        "scan",
        "--index",
        str(tmp_path / "ix-new"),
        "--questions",
        str(tmp_path / "q"),
    ]
    row = json.loads(run(*ask, "--rank", "bm25").stdout)
    assert row["ranked_by"] == "bm25" and row["served"][0]["where"] == "garden.md:3"
    assert "ranked_by" not in json.loads(run(*ask).stdout)
    (tmp_path / "w").write_text("money = invoice\n")
    for bad in (["--rank", "grep"], ["--rank", "bm25", "--words", str(tmp_path / "w")]):
        got = run(*ask, *bad)
        assert got.returncode == 2 and "scan.py" in got.stderr


# ── a question reads only the passages and words it needs ──────────────────────
def test_an_index_is_read_a_passage_and_a_word_at_a_time(tmp_path, monkeypatch):
    """With offsets.bin and copies.tsv, Index reads no passage but those a
    question holds and their copies, and the answer is the one an index read
    whole gives; without them it is read whole, as before."""
    import scan as sc

    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text(
        "The ferry leaves the square at noon.\n\nUnrelated text.\n"
    )
    (pile / "b.md").write_text("The ferry leaves the square at noon.\n")  # a copy
    (pile / "c.md").write_text("Buses wait by the square 2026x7 until dusk.\n")
    at = tmp_path / "ix"
    sc.build(pile, at)
    lazy = sc.Index(at)
    assert lazy._pile is None
    got = lazy.rank("when does the ferry leave the square", {}, None)
    assert lazy._pile is None and len(lazy._read) == 2  # the two copies, only
    for f in ("offsets.bin", "copies.tsv"):
        (at / f).rename(tmp_path / f)
    eager = sc.Index(at)
    assert eager._pile is not None
    assert [c["id"] for c in got] == [
        c["id"] for c in eager.rank("when does the ferry leave the square", {}, None)
    ]
    for f in ("offsets.bin", "copies.tsv"):
        (tmp_path / f).rename(at / f)
    # a word with digits is matched within words too, as read whole
    assert [c["path"] for c in sc.Index(at).near("2026x7 buses", {})] == ["c.md"]
    assert sc.Index(at).pile == eager.pile  # read whole when wanted: the same


def test_a_word_is_found_in_the_sorted_words_by_a_search_of_the_file(tmp_path):
    import scan as sc

    f = tmp_path / "w.tsv"
    words = sorted(["a", "b", "ab", "zz", "é", "m1", "m10", "m2"])
    f.write_text("".join(f"{w}\t{i}\n" for i, w in enumerate(words)))
    lines = sc.Lines(f)
    for i, w in enumerate(words):
        assert lines.get(w) == str(i)
    for missing in ("", "0", "aa", "m", "zzz", "ée"):
        assert lines.get(missing, "none") == "none"
    assert list(lines.keys()) == words
    f.write_text("only\t7")  # no newline at the end
    assert sc.Lines(f).get("only") == "7"
    (tmp_path / "e.tsv").write_text("")
    assert sc.Lines(tmp_path / "e.tsv").get("x") == ""


def test_an_index_whose_offsets_dont_match_is_refused(tmp_path):
    import scan as sc

    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("One.\n\nTwo.\n")
    at = tmp_path / "ix"
    sc.build(pile, at)
    (at / "offsets.bin").write_bytes((at / "offsets.bin").read_bytes()[:8])
    with pytest.raises(ValueError, match="offsets"):
        sc.Index(at)


def test_a_word_is_found_by_halving_not_by_reading_line_after_line(
    tmp_path, monkeypatch
):
    """On 20,000 words, finding one reads about log2 of them, not a run of
    them: the search is the speed, so a slip that still finds the word by
    walking the file is a failure too."""
    import scan as sc

    f = tmp_path / "w.tsv"
    words = sorted(f"w{i:05d}" for i in range(20000))
    f.write_text("".join(f"{w}\t{i}\n" for i, w in enumerate(words)))
    lines = sc.Lines(f)
    read = []
    real = lines._line
    monkeypatch.setattr(lines, "_line", lambda at: read.append(at) or real(at))
    for w in ("w00000", "w12345", "w19999", "w99999"):
        read.clear()
        lines.get(w)
        assert len(read) <= 40, (w, len(read))
