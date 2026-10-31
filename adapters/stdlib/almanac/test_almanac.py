"""Tests for almanac.py. Every catalog is built here: made-up datasets, no fixture files."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALMANAC = HERE / "almanac.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-31T00:00:00Z"]


def _entry(eid, title, **over):
    entry = {
        "id": eid,
        "type": "dataset",
        "title": title,
        "description": "A made-up\n  dataset of things.",
        "publisher": "Made-Up Statistics Office",
        "topics": ["things", "counts"],
        "source": {"canonical_url": f"https://stats.example.org/{eid}"},
        "status": "live",
        "status_since": "2026-07-01",
        "status_source": "curator",
        "observed": {"checked": "2026-10-30", "reachable": True, "http_status": 200},
        "coverage": {
            "spatial": "Example Island",
            "temporal": "1990-present",
            "cadence": "annual",
        },
        "license": "CC-BY-4.0",
    }
    entry.update(over)
    return entry


CATALOG = {
    "name": "Made-Up Almanac",
    "count": 3,
    "entries": [
        _entry(
            "tide-gauge-records",
            "Tide Gauge Records",
            description="Hourly sea level at the harbour gauge.",
            topics=["sea-level", "tides"],
        ),
        _entry(
            "harbour-rainfall",
            "Harbour Rainfall",
            observed={"checked": "2026-10-30", "reachable": False, "http_status": None},
        ),
        _entry(
            "lamp-census",
            "Lamp Census",
            observed={"checked": "2026-10-31", "reachable": None},
            status="frozen",
        ),
    ],
}

EXPECTED_TIDE = (
    "Tide Gauge Records (tide-gauge-records)\n"
    "Hourly sea level at the harbour gauge.\n"
    "publisher: Made-Up Statistics Office\n"
    "source: https://stats.example.org/tide-gauge-records\n"
    "status: live since 2026-07-01 (curator); licence: CC-BY-4.0\n"
    "link last checked: 2026-10-30, reachable, HTTP 200\n"
    "coverage: Example Island; 1990-present; annual\n"
    "topics: sea-level, tides\n"
    "\n"
)


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *map(str, argv)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def mirror(folder: Path, to: Path) -> subprocess.CompletedProcess:
    return run(ALMANAC, "mirror", "--from", folder, "--to", to)


def snapshot(folder: Path) -> dict[str, bytes]:
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def make_checkouts(folder: Path) -> None:
    (folder / "made-up-almanac").mkdir(parents=True)
    (folder / "made-up-almanac" / "catalog.json").write_text(
        json.dumps(CATALOG), encoding="utf-8"
    )
    (folder / "made-up-almanac" / "README.md").write_text(
        "Not a catalog.\n", encoding="utf-8"
    )


def test_each_entry_is_one_paragraph_in_a_fixed_order(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_checkouts(folder)
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    text = (to / "made-up-almanac" / "catalog.json.txt").read_text(encoding="utf-8")
    assert text.startswith("almanac: Made-Up Almanac, 3 entries\n\n")
    assert EXPECTED_TIDE in text
    # sorted by id: harbour-rainfall, lamp-census, tide-gauge-records
    assert (
        text.index("(harbour-rainfall)")
        < text.index("(lamp-census)")
        < text.index("(tide-gauge-records)")
    )


def test_the_link_checkers_last_word_is_kept_as_it_said_it(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_checkouts(folder)
    assert mirror(folder, to).returncode == 0
    text = (to / "made-up-almanac" / "catalog.json.txt").read_text(encoding="utf-8")
    assert "link last checked: 2026-10-30, no response\n" in text
    assert "link last checked: 2026-10-31, not yet probed\n" in text
    # the curator's status is the almanac's own, never re-judged here
    assert "status: frozen since 2026-07-01 (curator)" in text
    assert "status: live since 2026-07-01 (curator)" in text


def test_whitespace_inside_a_field_is_collapsed(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_checkouts(folder)
    assert mirror(folder, to).returncode == 0
    text = (to / "made-up-almanac" / "catalog.json.txt").read_text(encoding="utf-8")
    assert "A made-up dataset of things.\n" in text


def test_missing_fields_leave_their_lines_out(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "catalog.json").write_text(
        json.dumps({"entries": [{"id": "bare"}]}), encoding="utf-8"
    )
    assert mirror(folder, to).returncode == 0
    assert (to / "catalog.json.txt").read_text(encoding="utf-8") == (
        "almanac: an almanac, 1 entry\n\n"
        "bare (bare)\nstatus: unknown\nlink last checked: never, not yet probed\n\n"
    )


def test_only_catalog_json_is_read_and_hidden_parts_are_skipped(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_checkouts(folder)
    (folder / ".git").mkdir()
    (folder / ".git" / "catalog.json").write_text(json.dumps(CATALOG), encoding="utf-8")
    (folder / "other").mkdir()
    (folder / "other" / "Catalog.JSON").write_text(
        json.dumps(CATALOG), encoding="utf-8"
    )
    (folder / "other" / "entries.json").write_text(
        json.dumps(CATALOG), encoding="utf-8"
    )
    assert mirror(folder, to).returncode == 0
    made = sorted(p.relative_to(to).as_posix() for p in to.rglob("*") if p.is_file())
    assert made == ["made-up-almanac/catalog.json.txt", "other/Catalog.JSON.txt"]


def test_a_catalog_json_that_is_not_a_catalog_is_skipped_and_counted(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    make_checkouts(folder)
    (folder / "broken").mkdir()
    (folder / "broken" / "catalog.json").write_text("{not json", encoding="utf-8")
    (folder / "list").mkdir()
    (folder / "list" / "catalog.json").write_text("[1, 2]", encoding="utf-8")
    got = mirror(folder, to)
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 2"


def test_nothing_readable_exits_42(tmp_path):
    folder, to = tmp_path / "f", tmp_path / "m"
    folder.mkdir()
    (folder / "catalog.json").write_bytes(b"\xff\xfe not utf-8 \x80")
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 1"


def test_mirror_inside_folder_is_refused(tmp_path):
    folder = tmp_path / "f"
    make_checkouts(folder)
    before = snapshot(folder)
    got = mirror(folder, folder / "out")
    assert got.returncode == 2 and got.stderr.startswith("refused:")
    assert snapshot(folder) == before


def test_folder_that_is_not_a_folder_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "m")
    assert got.returncode == 2 and got.stderr.startswith("refused:")


def test_two_runs_give_identical_bytes_and_originals_are_unchanged(tmp_path):
    folder = tmp_path / "f"
    make_checkouts(folder)
    before = snapshot(folder)
    first, second = tmp_path / "m1", tmp_path / "m2"
    assert mirror(folder, first).returncode == 0
    assert mirror(folder, second).returncode == 0

    def digests(root: Path) -> dict[str, str]:
        return {k: hashlib.sha256(v).hexdigest() for k, v in snapshot(root).items()}

    assert digests(first) == digests(second)
    assert snapshot(folder) == before


def test_kernel_serves_a_dataset_from_the_mirror(tmp_path):
    folder, to, box, key = (
        tmp_path / "f",
        tmp_path / "m",
        tmp_path / "box",
        tmp_path / "key",
    )
    make_checkouts(folder)
    assert mirror(folder, to).returncode == 0
    init = run(KERNEL, "init", "--box", box, "--pile", to, "--key", key, *NOW)
    assert init.returncode == 0, init.stderr
    got = run(KERNEL, "bite", "--box", box, *NOW, "hourly sea level harbour gauge")
    assert got.returncode == 0, got.stderr
    assert "Hourly sea level at the harbour gauge." in got.stdout
