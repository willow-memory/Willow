"""pile-gold: the person's sealed answers as a test of the search. A sealed
answer's cited passages are its question's gold, matched by the question's
key however it is retyped; each rank's top five is scored against them; a
cited passage gone from the folder is counted as gone, not missed; a
proposal waiting or declined is no gold; one row is recorded, holding counts
and a hash, never a word, and the chain still verifies; nothing to score
records nothing; and a bad command line is refused."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PG = HERE / "pile_gold.py"
PS = HERE.parent / "pile-store" / "pile_store.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-28T00:00:00Z"]
Q = "when is the boiler serviced"


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KERNEL), *argv, *NOW],
                          capture_output=True, text=True)  # fmt: skip


def gold_cmd(box: Path, *more: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PG), "--box", str(box), *more, *NOW],
                          capture_output=True, text=True)  # fmt: skip


def rows(box: Path) -> list[dict]:
    return [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]


def a_box(tmp: Path) -> tuple[Path, Path]:
    pile = tmp / "pile"
    pile.mkdir()
    (pile / "house.md").write_text(
        "2026-03-01 The boiler is serviced every March by Tamsin.\n\n"
        "2026-03-02 The gutter needs clearing.\n"
    )
    (pile / "garden.md").write_text("Tomatoes want sun.\n")
    box = tmp / "box"
    assert k("init", "--box", str(box), "--pile", str(pile),
             "--key", str(tmp / "key")).returncode == 0  # fmt: skip
    return box, pile


def answer(box: Path, tmp: Path, question: str, act: str = "seal") -> list[str]:
    """Ask, propose an answer citing what was served, and seal (or decline,
    or leave waiting) it, as the person would; the ids it cites."""
    served = json.loads(k("bite", "--box", str(box), question).stdout)["served"]
    cites = [s["id"] for s in served[:1]]
    prop = {"path": "answers/boiler.md", "data": "March, by Tamsin.\n",
            "cites": cites, "claim": "the house notes say so"}  # fmt: skip
    f = tmp / f"prop-{len(rows(box))}.jsonl"
    f.write_text(json.dumps(prop) + "\n")
    out = k("propose", "--box", str(box), "--file", str(f)).stdout
    subj = out.split()[1]
    if act != "wait":
        assert k(act, "--box", str(box), subj).returncode == 0
    return cites


def questions(tmp: Path, *lines: str) -> Path:
    f = tmp / "questions.txt"
    f.write_text("".join(x + "\n" for x in lines))
    return f


def test_a_sealed_answer_scores_both_ranks_and_records_no_words(tmp_path):
    box, _ = a_box(tmp_path)
    answer(box, tmp_path, Q)
    qs = questions(tmp_path, "# mine", "boiler\tWhen is the BOILER serviced?",
                   "kayak storage")  # fmt: skip
    got = gold_cmd(box, "--questions", str(qs))
    assert got.returncode == 0, got.stdout + got.stderr
    assert "boiler: kernel 1, pile-rank 1 of 1" in got.stdout
    assert "kernel     found 1 of 1 approved passages in the top 5" in got.stdout
    assert "pile-rank  found 1 of 1" in got.stdout
    row = rows(box)[-1]
    assert row["kind"] == "gold" and row["who"] == "pile-gold"
    assert row["standing"] == "unattested" and row["ts"] == NOW[1]
    assert (row["asked"], row["scored"], row["of"], row["gone"], row["at"]) == (
        2, 1, 1, 0, 5)  # fmt: skip
    assert row["found"] == {"kernel": 1, "pile_rank": 1}
    assert row["read_from"] == "folder" and len(row["questions_sha256"]) == 64
    text = json.dumps(row).lower()
    assert not any(w in text for w in ("boiler", "tamsin", "kayak", "house.md"))
    assert k("verify", "--box", str(box)).returncode == 0


def test_a_miss_is_counted_against_the_rank_that_missed(tmp_path):
    box, pile = a_box(tmp_path)
    answer(box, tmp_path, Q)
    for i in range(8):  # the kernel prefers the newest; these push it out
        (pile / f"log{i}.md").write_text(f"2026-04-0{i + 1} boiler serviced\n")
    got = gold_cmd(box, "--questions", str(questions(tmp_path, Q)))
    assert got.returncode == 0
    assert "kernel     found 0 of 1" in got.stdout, got.stdout
    assert rows(box)[-1]["found"]["kernel"] == 0


def test_a_cited_passage_gone_from_the_folder_is_not_a_miss(tmp_path):
    box, pile = a_box(tmp_path)
    answer(box, tmp_path, Q)
    (pile / "house.md").write_text("2026-03-01 The boiler was replaced.\n")
    got = gold_cmd(box, "--questions", str(questions(tmp_path, Q)))
    assert got.returncode == 0 and "(1 gone)" in got.stdout
    assert "1 approved passage no longer in the folder" in got.stdout
    row = rows(box)[-1]
    assert (row["of"], row["gone"]) == (0, 1)


def test_waiting_or_declined_is_no_gold_and_nothing_is_recorded(tmp_path):
    box, _ = a_box(tmp_path)
    answer(box, tmp_path, Q, "wait")
    answer(box, tmp_path, "tomatoes sun", "decline")
    before = (box / "record.jsonl").read_bytes()
    got = gold_cmd(box, "--questions", str(questions(tmp_path, Q, "tomatoes sun")))
    assert got.returncode == 42 and "none of 2 questions" in got.stdout
    assert (box / "record.jsonl").read_bytes() == before


def test_a_current_store_is_read(tmp_path):
    box, pile = a_box(tmp_path)
    answer(box, tmp_path, Q)
    store = tmp_path / "pile.sqlite"
    subprocess.run([sys.executable, str(PS), "--from", str(pile), "--to",
                    str(store)], check=True, capture_output=True)  # fmt: skip
    got = gold_cmd(box, "--questions", str(questions(tmp_path, Q)),
                   "--store", str(store))  # fmt: skip
    assert got.returncode == 0 and "found 1 of 1" in got.stdout
    assert rows(box)[-1]["read_from"] == "store"


def test_a_bad_command_line_or_a_broken_record_is_refused(tmp_path):
    box, _ = a_box(tmp_path)
    qs = questions(tmp_path, Q)
    for argv in ([], ["--box", str(box)], ["--questions", str(qs)],
                 ["--box", str(box), "--questions", str(qs), "--stray"],
                 ["--box", str(box), "--questions", str(qs), "--store", ""],
                 ["--box", str(tmp_path), "--questions", str(qs)],
                 ["--box", str(box), "--questions", str(tmp_path / "none")]):  # fmt: skip
        got = subprocess.run([sys.executable, str(PG), *argv],
                             capture_output=True, text=True)  # fmt: skip
        assert got.returncode == 2 and got.stdout == "", (argv, got.stdout)
    assert (
        "pile_gold.py"
        in subprocess.run(
            [sys.executable, str(PG)], capture_output=True, text=True
        ).stderr
    )
    answer(box, tmp_path, Q)
    text = (box / "record.jsonl").read_text().replace('"bite"', '"btie"', 1)
    (box / "record.jsonl").write_text(text)
    assert gold_cmd(box, "--questions", str(qs)).returncode == 2
