"""again: repeats counted from the record's bite keys, offered on willow-bot's
ladder (every third ask), and never offered once an approval stands."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]
spec = importlib.util.spec_from_file_location("again", HERE / "again.py")
ag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ag)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    return b


def ask(b: Path, q: str, n: int) -> None:
    for _ in range(n):
        run(str(KERNEL), "bite", "--box", str(b), *NOW, q)


def test_the_ladder_asked_noticed_offered(tmp_path):
    b = box(tmp_path)
    ask(b, "how much sun do tomatoes want", 1)
    got = run(str(HERE / "again.py"), "--box", str(b))
    assert got.returncode == 0
    assert got.stdout == "again: empty, no question asked more than once\n"
    ask(b, "How much SUN do tomatoes want?", 1)  # the same words: the same question
    got = run(str(HERE / "again.py"), "--box", str(b))
    assert (
        got.returncode == 0
        and "asked 2 times" in got.stdout
        and "standing?" not in got.stdout
    )
    ask(b, "how much sun do tomatoes want", 1)
    got = run(str(HERE / "again.py"), "--box", str(b))
    head, group, row = got.stdout.splitlines()
    assert got.returncode == 42
    assert head == "again: populated, 1 question asked more than once, 1 at an offer"
    assert group.startswith("## make it standing? approve an answer for it")
    assert row.startswith("  question ") and row.endswith(
        "  asked 3 times, last 2026-10-23, answered from garden.md:1"
    )
    ask(b, "how much sun do tomatoes want", 1)
    assert (
        "standing?" not in run(str(HERE / "again.py"), "--box", str(b)).stdout
    )  # 4: not a third


def test_one_question_by_its_words_and_no_words_in_the_record(tmp_path):
    b = box(tmp_path)
    ask(b, "when does the frost come", 2)
    one = run(str(HERE / "again.py"), "--box", str(b), "When does the frost come?")
    assert (
        "asked 2 times" in one.stdout
        and "nothing in your folder answered it" in one.stdout
    )
    assert (
        "haven't asked"
        in run(str(HERE / "again.py"), "--box", str(b), "something new").stdout
    )
    assert "frost" not in (b / "record.jsonl").read_text()


def test_every_repeat_as_json_is_the_same_report_by_rung(tmp_path):
    b = box(tmp_path)
    ask(b, "how much sun do tomatoes want", 3)
    ask(b, "when does the frost come", 2)
    text = run(str(HERE / "again.py"), "--box", str(b))
    got = run(str(HERE / "again.py"), "--box", str(b), "--json")
    assert got.returncode == text.returncode == 42
    doc = json.loads(got.stdout)
    assert (doc["addon"], doc["state"]) == ("again", "populated")
    assert doc["said"] == "2 questions asked more than once, 1 at an offer"
    assert [g["name"] for g in doc["groups"]] == [
        "make it standing? approve an answer for it, and it's served as yours",
        "noticed",
    ]
    noticed = doc["groups"][1]["rows"]
    assert len(noticed) == 1 and noticed[0]["what"] == (
        "asked 2 times, last 2026-10-23, nothing in your folder answered it"
    )
    assert text.stdout.splitlines()[0] == f"again: populated, {doc['said']}"
    ask(b, "how much sun do tomatoes want", 1)  # 4: noticed, not offered
    got = run(str(HERE / "again.py"), "--box", str(b), "--json")
    assert got.returncode == 0
    assert [g["name"] for g in json.loads(got.stdout)["groups"]] == ["noticed"]


def test_one_questions_words_take_no_json(tmp_path):
    b = box(tmp_path)
    got = run(str(HERE / "again.py"), "--box", str(b), "--json", "frost")
    assert got.returncode == 2 and "again.py" in got.stderr


def test_one_question_by_its_words_is_42_only_at_the_offer(tmp_path):
    """Asked by its words, a question at the offer rung (every third ask)
    waits on you; asked twice, it doesn't yet."""
    b = box(tmp_path)
    q = "how much sun do tomatoes want"
    ask(b, q, 2)
    assert run(str(HERE / "again.py"), "--box", str(b), q).returncode == 0
    ask(b, q, 1)
    assert run(str(HERE / "again.py"), "--box", str(b), q).returncode == 42


def test_only_bite_rows_are_counted():
    """A seal (or any non-bite) is not a repeat even when it carries a
    bite_key; a bite without a key is not one either."""
    rows = [
        {
            "kind": "seal",
            "bite_key": "fake",
            "ts": "2026-10-23T00:00:00Z",
            "served": [],
        },
        {
            "kind": "bite",
            "bite_key": "q",
            "ts": "2026-10-23T00:00:00Z",
            "served": [],
        },
        {
            "kind": "bite",
            "bite_key": "q",
            "ts": "2026-10-23T01:00:00Z",
            "served": [],
        },
        {"kind": "bite", "ts": "2026-10-23T02:00:00Z", "served": []},
    ]
    got = ag.repeats(rows)
    assert list(got) == ["q"] and got["q"]["times"] == 2
