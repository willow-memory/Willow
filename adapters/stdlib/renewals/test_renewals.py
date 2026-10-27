"""renewals: an expiry is a line saying one of the words and its own date,
the kernel's kind or written out; soonest first, gone by marked by the clock
you give, and nothing stitched together from nearby lines."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("renewals", HERE / "renewals.py")
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)
NOW = ["--now", "2026-10-23T00:00:00Z"]


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


def rows(text: str) -> list[tuple[str, str]]:
    got = rn.found([{"path": "a.md", "line": 1, "text": text}])
    return [(r["when"], r["text"]) for r in got]


def test_an_expiry_is_a_word_and_a_date_on_the_same_line():
    assert rows("Passport expires 2031-05-02.") == [
        ("20310502", "Passport expires 2031-05-02.")
    ]
    assert rows("Your cover ends on 31/10/2026 unless renewed.") == [
        ("20261031", "Your cover ends on 31/10/2026 unless renewed.")
    ]
    assert rows("Gym membership, valid until 2027-01-31") == [
        ("20270131", "Gym membership, valid until 2027-01-31")
    ]
    assert rows("expires some day") == [], "a word without a date says too little"
    assert rows("the meeting is on 2026-11-02") == [], "a date without a word too"
    assert rows("licence renewal due\n2027-03-01 pay it") == [], (
        "an expiry whose date only a nearby line holds is not stitched together"
    )


def test_a_date_written_out_is_read_and_a_month_alone_is_not():
    assert rows("Policy HC-7718203 renews on 4 March 2026.") == [
        ("20260304", "Policy HC-7718203 renews on 4 March 2026.")
    ]
    assert rows("Visa expires March 4, 2027") == [
        ("20270304", "Visa expires March 4, 2027")
    ]
    assert rows("expires on the 1st of June 2027") == [
        ("20270601", "expires on the 1st of June 2027")
    ]
    assert rows("RACV home & contents, renews March") == [], "no day, no year: unplaced"
    assert rows("Registration expiry: 03/11/2025") == [], (
        "a date reading either way round is never guessed"
    )
    assert rows("renews on 31 February 2027") == [], "a day the month hasn't is no date"
    assert rows("renews on 31 April 2027") == [] and rows("expires 30 April 2027")
    assert rows("renews on 29 February 2027") == [], "2027 has no 29 February"
    assert rows("renews on 29 February 2028") == [
        ("20280229", "renews on 29 February 2028")
    ]
    assert rn.prose_date("by 4 March 2026 or 30 June 2026") == "20260630", "the latest"


def test_soonest_first_and_gone_by_is_by_the_clock_you_give(tmp_path):
    b = box(tmp_path, {
        "ids/passport.md": "Passport expires 2024-01-31.\n",
        "work/insurance.txt": "Your cover ends on 31/10/2026 unless renewed.\n",
        "mail/racv.txt": "Policy HC-7718203 renews on 4 March 2027.\n",
    })  # fmt: skip
    got = run(str(HERE / "renewals.py"), "--box", str(b), *NOW)
    lines = got.stdout.splitlines()
    assert got.returncode == 0
    assert lines[0].startswith("gone by  2024-01-31") and "passport" in lines[0]
    assert lines[1].startswith("         2026-10-31")
    assert lines[2].startswith("         2027-03-04")
    assert lines[3] == "3 renewals: 1 gone by, 2 to come"
    later = run(
        str(HERE / "renewals.py"), "--box", str(b), "--now", "2027-01-01T00:00:00Z"
    )
    assert "2 gone by, 1 to come" in later.stdout
    assert got.stdout == run(str(HERE / "renewals.py"), "--box", str(b), *NOW).stdout


def test_one_renewal_alone_and_none_at_all(tmp_path):
    b = box(tmp_path, {"a.md": "Licence expires 2030-01-02.\n"})
    got = run(str(HERE / "renewals.py"), "--box", str(b), *NOW)
    assert got.stdout.splitlines()[-1] == "1 renewal: 0 gone by, 1 to come"
    b2 = box(tmp_path / "b2", {"garden.md": "Tomatoes want sun.\n"})
    got = run(str(HERE / "renewals.py"), "--box", str(b2), *NOW)
    assert got.returncode == 42 and "says an expiry" in got.stdout


def test_a_bad_command_line_and_a_folder_that_is_no_box_are_refused(tmp_path):
    got = run(str(HERE / "renewals.py"))
    assert got.returncode == 2 and "renewals.py" in got.stderr
    got = run(str(HERE / "renewals.py"), "--box", str(tmp_path / "b"), "--now", "soon")
    assert got.returncode == 2, "the clock is the kernel's kind of timestamp"
    got = run(str(HERE / "renewals.py"), "--box", str(tmp_path), *NOW)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
