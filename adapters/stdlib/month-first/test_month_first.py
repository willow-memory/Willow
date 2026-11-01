"""month-first: month-first dates mirrored with their ISO form beside them."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "month_first.py"
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(str(SCRIPT), "mirror", "--from", str(folder), "--to", str(to))


def put(root: Path, rel: str, data: str | bytes) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return path


def out_of(to: Path, rel: str) -> str:
    return (to / f"{rel}.txt").read_bytes().decode("utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def one(tmp_path: Path, text: str) -> str:
    folder, to = tmp_path / "in", tmp_path / "out"
    put(folder, "a.md", text)
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    return out_of(to, "a.md")


def test_every_form_it_reads_gains_its_iso_form(tmp_path):
    got = one(
        tmp_path,
        "Moved to 11/03/2026. Paid 1/2/26.\n"
        "Filed Oct. 2nd, 2026; heard November 3 2026, again Sept 1, 2026 "
        "and may 5, 2026.\n",
    )
    assert got == (
        "Moved to 11/03/2026 [2026-11-03]. Paid 1/2/26 [2026-01-02].\n"
        "Filed Oct. 2nd, 2026 [2026-10-02]; heard November 3 2026 [2026-11-03], "
        "again Sept 1, 2026 [2026-09-01] and may 5, 2026 [2026-05-05].\n"
    )


def test_what_is_not_a_date_is_left_as_it_is(tmp_path):
    text = (
        "13/03/2026 is day first. Feb 30, 2026 never was. 2/30/2026 neither.\n"
        "https://example.org/10/24/2026/ is an address; 1.11/03/2026 and "
        "v11/03/2026 and 11/03/2026/x are not dates. 11/03/1850 is too old, "
        "Mar 3, 2100 too new, 11/03/202 too short.\n"
    )
    assert one(tmp_path, text) == text


def test_a_file_whose_dates_say_day_first_keeps_its_numbered_dates(tmp_path):
    folder, to = tmp_path / "in", tmp_path / "out"
    put(folder, "uk.md", "Due 02/03/2026, paid 13/03/2026, filed Nov 3, 2026.\n")
    put(folder, "us.md", "Due 02/03/2026.\n")
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    assert out_of(to, "uk.md") == (
        "Due 02/03/2026, paid 13/03/2026, filed Nov 3, 2026 [2026-11-03].\n"
    )
    assert out_of(to, "us.md") == "Due 02/03/2026 [2026-02-03].\n"
    assert got.stdout.splitlines() == [
        "2 month-first dates given their ISO form",
        "1 files whose own dates say day first: their numbered dates left",
        f"wrote 2 files to {to}; skipped 0",
    ]
    assert "day first: uk.md, its numbered dates left as they are" in got.stderr


def test_a_number_over_12_that_is_no_date_says_nothing_of_the_order(tmp_path):
    got = one(tmp_path, "Due 02/03/2026; part 14/40/2026 and 31/02/2026.\n")
    assert got.startswith("Due 02/03/2026 [2026-02-03];")


def test_a_two_digit_year_from_70_is_the_1900s(tmp_path):
    got = one(tmp_path, "7/4/76, 7/4/69 and 1/1/70\n")
    assert got == "7/4/76 [1976-07-04], 7/4/69 [2069-07-04] and 1/1/70 [1970-01-01]\n"


def test_a_marked_date_is_not_marked_again(tmp_path):
    first = one(tmp_path, "On 11/03/2026 and Nov 3, 2026.\n")
    again, to = tmp_path / "again", tmp_path / "out2"
    put(again, "a.md", first)
    assert mirror(again, to).returncode == 0
    assert (
        out_of(to, "a.md")
        == first
        == ("On 11/03/2026 [2026-11-03] and Nov 3, 2026 [2026-11-03].\n")
    )


def test_every_text_file_is_written_pages_as_their_words(tmp_path):
    folder, to = tmp_path / "in", tmp_path / "out"
    put(folder, "plain.txt", "Nothing dated here.\n")
    put(folder, "court/order.html", "<p>Hearing on <b>Nov 3, 2026</b></p>\n")
    put(folder, "photo.jpg", b"\xff\xd8\xff")
    put(folder, "old.txt", b"\xff\xfeH\x00i\x00")
    before = snapshot(folder)
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "1 month-first dates given their ISO form",
        f"wrote 2 files to {to}; skipped 1",
    ]
    assert "skipped old.txt: not UTF-8" in got.stderr
    assert sorted(snapshot(to)) == ["court/order.html.txt", "plain.txt.txt"]
    assert out_of(to, "plain.txt") == "Nothing dated here.\n"
    assert out_of(to, "court/order.html").split() == "Hearing on Nov 3, 2026 [2026-11-03]".split()  # fmt: skip
    assert "<b>" not in out_of(to, "court/order.html")
    assert snapshot(folder) == before


def test_the_kernel_reads_a_date_it_would_not_guess(tmp_path):
    text = "Hearing moved to 11/03/2026.\n"
    assert kernel.newest(text) == ""
    assert kernel.newest(one(tmp_path, text)) == "20261103"
