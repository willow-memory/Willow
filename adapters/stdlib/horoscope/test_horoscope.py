"""horoscope: the bot's pick, the SHA-256 of "name:date", so the same name
and day give the same reading anywhere; the bot's own lines kept for coders."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("horoscope", HERE / "horoscope.py")
hs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hs)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "horoscope.py"), *argv],
        capture_output=True,
        text=True,
    )


def test_the_same_name_and_day_give_the_same_reading_by_the_bots_rule():
    i = int(hashlib.sha256(b"Ana:2026-10-24").hexdigest()[:8], 16)
    assert hs.reading("Ana", "2026-10-24") == hs.LINES[i % len(hs.LINES)]
    assert hs.reading("Ana", "2026-10-24", hs.CODER) == hs.CODER[i % len(hs.CODER)]
    got = run("Ana", "--date", "2026-10-24")
    assert (
        got.returncode == 0
        and got.stdout == f"Today, Ana: {hs.LINES[i % len(hs.LINES)]}.\n"
    )
    assert run("Ana", "--date", "2026-10-24").stdout == got.stdout


def test_another_day_or_name_can_read_differently():
    days = {hs.reading("Ana", f"2026-10-{d:02d}") for d in range(1, 29)}
    names = {
        hs.reading(n, "2026-10-24")
        for n in ("Ana", "Bo", "Cy", "Di", "Ed", "Flo", "Gus")
    }
    assert len(days) > 10 and len(names) > 3


def test_the_bots_lines_are_kept_as_they_were():
    assert (
        len(hs.CODER) == 30
        and hs.CODER[0] == "a variable you named in haste will forgive you"
    )
    assert hs.CODER[-1] == "the ticket is more finished than the ticket admits"
    assert (
        len(hs.LINES) == 30
        and len(set(hs.LINES)) == 30
        and not set(hs.LINES) & set(hs.CODER)
    )
    assert (
        run("Ana", "--date", "2026-10-24", "--coder")
        .stdout.rstrip(".\n")
        .split(": ", 1)[1]
        in hs.CODER
    )


def test_today_is_the_default_and_a_bad_command_line_is_refused():
    assert run("Ana").returncode == 0
    for argv in ([], ["Ana", "Bo"], ["  "], ["--coder"], ["Ana", "--date", "soon"]):
        got = run(*argv)
        assert got.returncode == 2
    assert "horoscope.py" in run().stderr
