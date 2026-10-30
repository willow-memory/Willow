"""static-search: each approved answer a page, indexed by Pagefind, a search
page over them; only approvals that prove under the key; the site made only
under --to and never over a folder; the same answers give the same bytes;
and a refusal, never a quiet skip, without Pagefind."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "static_search.py"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *argv],
                          capture_output=True, text=True)  # fmt: skip


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)  # fmt: skip


def approve(b: Path, tmp_path: Path, question: str, answer: str, at: str) -> None:
    got = k("bite", "--box", str(b), "--now", f"2026-10-{at}T09:00:00Z", question)
    served = json.loads(got.stdout)["served"]
    row = {
        "path": "a.md",
        "data": answer,
        "cites": [served[0]["id"]],
        "claim": "the note says so",
    }
    (tmp_path / "s.jsonl").write_text(json.dumps(row) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"),
      "--now", f"2026-10-{at}T09:01:00Z")  # fmt: skip
    subj = json.loads((b / "record.jsonl").read_text().splitlines()[-1])["subject"]
    got = k("seal", "--box", str(b), subj, "--now", f"2026-10-{at}T09:02:00Z")
    assert got.returncode == 0, got.stderr


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "van.txt").write_text("The van was sold on 2021-05-14 to Mr Petrak.\n")
    (pile / "gas.txt").write_text("The gas bill is paid by direct debit on the 28th.\n")
    b = tmp_path / "box"
    k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "key"),
      "--now", "2026-10-01T09:00:00Z")  # fmt: skip
    approve(
        b, tmp_path, "when was the van sold", "Sold 2021-05-14, to Mr Petrak.", "02"
    )
    approve(
        b, tmp_path, "gas bill paid", "Direct debit on the 28th <every month>.", "03"
    )
    return b


def test_each_answer_a_page_indexed_with_a_search_page(box, tmp_path):
    site = tmp_path / "site"
    got = run("--box", str(box), "--to", str(site))
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith(f"wrote 2 answers to {site}, searchable\n")
    one = (site / "answers" / "1.html").read_text()
    assert (
        "<main data-pagefind-body>" in one and "Sold 2021-05-14, to Mr Petrak." in one
    )
    assert "<code>van.txt:1</code>" in one and "Approved 2026-10-02" in one
    two = (site / "answers" / "2.html").read_text()
    assert "&lt;every month&gt;" in two and "<every month>" not in two
    index = (site / "index.html").read_text()
    assert 'href="answers/1.html"' in index and "pagefind/pagefind-ui.js" in index
    entry = json.loads((site / "pagefind" / "pagefind-entry.json").read_text())
    assert entry["languages"]["en"]["page_count"] == 2  # the index page isn't one
    assert "http" not in index.replace("http.server", "")  # it loads only its own files


def test_the_same_answers_give_the_same_bytes(box, tmp_path):
    for name in ("one", "two"):
        assert run("--box", str(box), "--to", str(tmp_path / name)).returncode == 0
    files = sorted(
        p.relative_to(tmp_path / "one")
        for p in (tmp_path / "one").rglob("*")
        if p.is_file()
    )
    assert files == sorted(
        p.relative_to(tmp_path / "two")
        for p in (tmp_path / "two").rglob("*")
        if p.is_file()
    )
    for f in files:
        assert (tmp_path / "one" / f).read_bytes() == (
            tmp_path / "two" / f
        ).read_bytes(), f


def test_an_approval_whose_file_changed_is_left_out(box, tmp_path):
    prop = sorted((box / "proposals").glob("*.json"))[0]
    prop.write_text(prop.read_text().replace("Petrak", "Someone"))
    got = run("--box", str(box), "--to", str(tmp_path / "site"))
    assert got.returncode == 42 and "left out 1 approval" in got.stderr
    pages = list((tmp_path / "site" / "answers").glob("*.html"))
    assert len(pages) == 1 and "Someone" not in pages[0].read_text()


def test_no_answer_writes_nothing(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.txt").write_text("hello\n")
    b = tmp_path / "box"
    k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "key"))
    got = run("--box", str(b), "--to", str(tmp_path / "site"))
    assert got.returncode == 42 and not (tmp_path / "site").exists()


def test_refusals(box, tmp_path):
    (tmp_path / "there").mkdir()
    for argv in ([], ["--box", str(box)], ["--to", str(tmp_path / "s")],
                 ["--box", str(box), "--to", str(tmp_path / "there")],
                 ["--box", str(box), "--to", str(tmp_path / "no" / "s")],
                 ["--box", str(tmp_path), "--to", str(tmp_path / "s")],
                 ["--box", str(box), "--to", str(tmp_path / "s"), "stray"]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert not (tmp_path / "no").exists() and not (tmp_path / "s").exists()


def test_without_pagefind_it_refuses_and_names_the_install(box, tmp_path):
    script = (
        "import runpy, sys, importlib.util\n"
        "importlib.util.find_spec = lambda name, *a: None\n"
        f"sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
    )
    got = subprocess.run([sys.executable, "-c", script, "--box", str(box), "--to",
                          str(tmp_path / "site")], capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "requirements.txt" in got.stderr
