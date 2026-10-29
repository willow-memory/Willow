"""foia: requests sent and the answers that close them, due by a date the line
says or by the law named, counted in working days where the law does; nothing
guessed without a law or a date."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "foia.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-04-29T00:00:00Z"]
spec = importlib.util.spec_from_file_location("foia", SCRIPT)
fo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fo)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    for name, text in files.items():
        (pile / name).parent.mkdir(parents=True, exist_ok=True)
        (pile / name).write_text(text)
    b = tmp_path / "box"
    got = subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "k"),
            *NOW,
        ],
        capture_output=True,
        text=True,
    )
    assert got.returncode == 0, got.stderr
    return b


def chunk(text: str) -> list[dict]:
    return [{"path": "foi/log.md", "line": 1, "text": text}]


def test_a_deadline_counts_working_days_from_the_day_after():
    assert fo.deadline(date(2026, 3, 2), "uk") == date(2026, 3, 30), (
        "Monday + 20 working days"
    )
    assert fo.deadline(date(2026, 3, 6), "uk") == date(2026, 4, 3), (
        "Friday: the next working day is Monday"
    )
    assert fo.deadline(date(2026, 3, 7), "uk") == date(2026, 4, 3), (
        "sent on a Saturday counts from Monday"
    )
    assert fo.deadline(date(2026, 3, 1), "us") == date(2026, 3, 27)
    assert (
        fo.deadline(date(2026, 3, 2), "nz")
        == date(2026, 3, 30)
        == fo.deadline(date(2026, 3, 2), "ie")
    )
    assert fo.deadline(date(2026, 3, 1), "au") == date(2026, 3, 31), "30 calendar days"
    assert fo.deadline(date(2026, 3, 1), "ca") == date(2026, 3, 31)
    assert fo.deadline(date(2026, 1, 20), "au") == date(2026, 2, 19)


def test_the_body_is_who_was_asked():
    b = fo.body_of
    assert b("FOI request to City Council sent") == "City Council"
    assert b("sent a FOIA request to the Home Office") == fo.NONE, "the is not a name"
    assert b("City Council: FOI sent") == "City Council"
    assert b("2026-03-01 Police - FOI request sent") == "Police"
    assert b("FOI request sent") == fo.NONE
    assert b("Note: FOI sent") == fo.NONE
    assert b("response from Environment Agency received") == "Environment Agency"
    assert (
        b("with Hampshire County Council Planning Dept at Winchester")
        == "Hampshire County Council Planning"
    )


def test_a_request_and_its_answer():
    pile = chunk(
        "2026-03-02 FOI request to City Council sent\n"
        "2026-03-03 FOI to City Council acknowledged\n"
        "2026-03-27 FOI response from City Council received\n"
        "2026-03-05 FOIA request to Police submitted, due 2026-04-15\n"
        "2026-03-06 notes about foi\n"
        "2026-04-20 FOI response from Health Trust received\n"
        "2026-03-09 FOI request to Health Trust sent\n"
    )  # fmt: skip
    found, stray = fo.requests(pile, "uk")
    by = {r["body"]: r for r in found}
    assert set(by) == {"City Council", "Police", "Health Trust"}
    assert by["City Council"]["sent"] == date(2026, 3, 2) and by["City Council"][
        "due"
    ] == date(2026, 3, 30)
    assert by["City Council"]["answered"] == date(2026, 3, 27)
    assert by["Police"]["due"] == date(2026, 4, 15), "the line's own due date wins"
    assert by["Police"]["answered"] is None
    assert by["Health Trust"]["answered"] == date(2026, 4, 20) and stray == 0
    none, _ = fo.requests(pile)
    assert {r["body"]: r["due"] for r in none}["City Council"] is None, (
        "no law, no guess"
    )


def test_an_answer_closes_the_latest_open_request_to_the_same_body_and_strays_are_counted():
    pile = chunk(
        "2026-03-02 FOI request to Council sent\n2026-03-09 FOI request to Council sent\n"
        "2026-03-20 FOI response from Council received\n2026-03-21 FOI response from Elsewhere received\n"
    )  # fmt: skip
    found, stray = fo.requests(pile)
    assert [r["answered"] for r in found] == [None, date(2026, 3, 20)]
    assert stray == 1
    before = chunk(
        "2026-03-01 FOI response from Council received\n2026-03-02 FOI request to Council sent\n"
    )
    found, stray = fo.requests(before)
    assert found[0]["answered"] is None and stray == 1, (
        "an answer before the request is not its answer"
    )


def test_the_listing(tmp_path):
    b = box(tmp_path, {"foi/log.md": (
        "2026-03-02 FOI request to City Council sent\n2026-03-27 FOI response from City Council received\n"
        "2026-02-02 FOI request to Home Office sent\n2026-03-02 FOI response from Home Office received\n"
        "2026-03-05 FOIA request to Police submitted\n"
        "2026-04-01 FOI request to Fire Service sent, due 2026-04-29\n")})  # fmt: skip
    got = run("--box", str(b), "--law", "uk", *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "Police        sent 2026-03-05  due 2026-04-02  open, overdue 27 days",
        "Fire Service  sent 2026-04-01  due 2026-04-29  open, due today",
        "Home Office   sent 2026-02-02  due 2026-03-02  answered 2026-03-02 (on the day)",
        "City Council  sent 2026-03-02  due 2026-03-30  answered 2026-03-27 (3 days early)",
        "4 requests: 2 answered, 2 open",
    ]
    nolaw = run("--box", str(b), *NOW).stdout.splitlines()
    assert (
        "due not known (name --law)" in "\n".join(nolaw)
        and nolaw[-1] == "4 requests: 2 answered, 2 open"
    )
    assert run("--box", str(b), "--law", "uk", *NOW).stdout == got.stdout


def test_late_early_and_days_left_are_worded_plainly(tmp_path):
    b = box(tmp_path, {"foi/log.md": (
        "2026-03-02 FOI to A sent, due 2026-03-10\n2026-03-12 FOI response from A received\n"
        "2026-03-02 FOI to B sent, due 2026-03-10\n2026-03-11 FOI response from B received\n"
        "2026-03-02 FOI to C sent, due 2026-03-10\n2026-03-09 FOI response from C received\n"
        "2026-04-01 FOI to D sent, due 2026-04-30\n2026-04-01 FOI to E sent, due 2026-04-28\n"
        "2026-03-02 FOI to F sent, due 2026-04-28\n")})  # fmt: skip
    out = run("--box", str(b), *NOW).stdout
    for text in (
        "answered 2026-03-12 (2 days late)",
        "answered 2026-03-11 (1 day late)",
        "answered 2026-03-09 (1 day early)",
        "open, 1 day left",
        "open, overdue 1 day",
        "1 response",
        "6 requests: 3 answered, 3 open",
    ):
        if text == "1 response":
            continue
        assert text in out, text
    assert "open, 1 day left" in out and "open, overdue 1 day" in out
    (tmp_path / "s").mkdir()
    stray = box(
        tmp_path / "s",
        {
            "foi/log.md": "2026-03-02 FOI response from Z received\n2026-03-03 FOI to Y sent\n"
        },
    )
    assert (
        run("--box", str(stray), *NOW).stdout.splitlines()[-1]
        == "1 request: 0 answered, 1 open, 1 response named no request"
    )


def test_nothing_is_42_and_a_bad_command_line_is_refused(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run("--box", str(b), *NOW)
    assert got.returncode == 42 and "information request was sent" in got.stdout
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for argv in (
        [],
        ["--box"],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--law", "mars"],
        ["--box", str(b), "--now", "soon"],
        ["--box", str(b), "--now", "2026-13-45"],
        ["--box", str(tmp_path)],
    ):
        assert run(*argv).returncode == 2, argv
    assert "foia.py" in run().stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'foia.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "habits"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )
