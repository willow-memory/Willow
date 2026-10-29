"""job-hunt: a company and a stage on a day in a job search, the latest event
the company's standing, waiting counted from it to --now."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("job_hunt", HERE / "job_hunt.py")
jh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jh)
NOW = ["--now", "2026-10-29T00:00:00Z"]
SCRIPT = str(HERE / "job_hunt.py")


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def box(tmp_path: Path, files: dict) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir(parents=True)
    for name, text in files.items():
        p = pile / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    return b


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'job_hunt.py')!r})\n"
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


def test_the_company_is_the_name_the_line_starts_with_or_follows_a_preposition():
    c = jh.company_of
    assert c("Acme: applied (Designer)") == "Acme"
    assert c("2026-02-20 Globex Corp - applied") == "Globex Corp"
    assert c("- Initech (Analyst) interview") == "Initech"
    assert c("applied to Hooli for the role") == "Hooli"
    assert c("phone screen with Wayne Enterprises Ltd today") == "Wayne Enterprises Ltd"
    assert c("heard back from Umbrella") == "Umbrella"
    assert c("offer at Stark Industries Group Intl") == "Stark Industries Group"
    assert c("Offer: pending") == "", "Offer is not a company"
    assert c("Subject: your offer") == ""
    assert c("applied online") == ""
    assert c("today I applied") == ""


def test_the_stage_is_the_strongest_the_line_names():
    s = jh.stage_of
    assert s("applied") == "applied"
    assert s("application sent") == "applied"
    assert s("sent my CV") == "applied"
    assert s("heard back") == "replied"
    assert s("got back to me") == "replied"
    assert s("phone screen") == "interview"
    assert s("take-home assessment") == "interview"
    assert s("followed up") == "followed up"
    assert s("chased them") == "followed up"
    assert s("rejected") == "rejected"
    assert s("not moving forward") == "rejected"
    assert s("unsuccessful") == "rejected"
    assert s("offer") == "offer"
    assert s("rejected after the interview") == "rejected"
    assert s("offer after the interview and I applied") == "offer"
    assert s("interview, then they replied") == "interview"
    assert s("had a coffee") == ""


def test_a_job_search_line_names_a_company_and_a_stage_on_a_day():
    pile = [
        {"path": "jobs/log.md", "line": 1, "text": (
            "2026-02-20 Acme (Designer): applied\n"
            "2026-03-10 Acme: interview\n"
            "2026-02-10 Globex: applied\n"
            "2026-03-02 Globex: rejected\n"
        )},
        {"path": "notes.md", "line": 1, "text": "2026-05-01 applied sunscreen\n2026-05-02 Mum: interview on the radio\n"},
        {"path": "chat.md", "line": 1, "text": "2026-05-03 Acme: lunch\n"},
    ]  # fmt: skip
    got = jh.hunt(pile)
    assert set(got) == {"Acme", "Globex"}, "a radio interview is not a job search"
    assert got["Acme"] == {
        "role": "Designer",
        "events": [("20260220", "applied"), ("20260310", "interview")],
    }
    assert got["Globex"]["events"][-1] == ("20260302", "rejected")


def test_the_listing_waiting_longest_first_then_the_finished(tmp_path):
    b = box(tmp_path, {"jobs/log.md": (
        "2026-02-20 Acme (Designer): applied\n2026-03-10 Acme: interview\n"
        "2026-09-01 Initech: applied\n"
        "2026-02-10 Globex: applied\n2026-03-02 Globex: rejected\n"
        "2026-08-01 Hooli: applied\n2026-09-15 Hooli: offer\n"
        "2026-10-28 Umbrella: applied\n")})  # fmt: skip
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "Acme (Designer)  interview 2026-03-10  after applied 2026-02-20  waiting 233 days",
        "Initech          applied 2026-09-01  waiting 58 days",
        "Umbrella         applied 2026-10-28  waiting 1 day",
        "Globex           rejected 2026-03-02  after applied 2026-02-10",
        "Hooli            offer 2026-09-15  after applied 2026-08-01",
        "5 applications: 3 waiting, 1 rejected, 1 offer",
    ]
    assert run(SCRIPT, "--box", str(b), *NOW).stdout == got.stdout


def test_a_future_event_and_one_application_are_said_plainly(tmp_path):
    b = box(tmp_path, {"jobs/log.md": "2026-11-05 Acme: interview\n"})
    assert run(SCRIPT, "--box", str(b), *NOW).stdout.splitlines() == [
        "Acme  interview 2026-11-05  (in the future)",
        "1 application: 1 waiting, 0 rejected, 0 offers",
    ]


def test_nothing_is_42_and_refusals(tmp_path):
    b = box(tmp_path, {"garden.md": "Tomatoes want sun.\n"})
    got = run(SCRIPT, "--box", str(b), *NOW)
    assert got.returncode == 42 and "job application to a company" in got.stdout
    for argv in (
        [],
        ["--box", str(tmp_path)],
        ["--box", str(b), "stray"],
        ["--box", str(b), "--now", "soon"],
        ["--box", str(b), "--now", "2026-13-45"],
    ):
        assert run(SCRIPT, *argv).returncode == 2, argv
    assert "job_hunt.py" in run(SCRIPT).stderr
    assert "not a kernel box" in run(SCRIPT, "--box", str(tmp_path)).stderr
