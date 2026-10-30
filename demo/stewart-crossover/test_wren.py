"""Wren's files, as make_life.py makes them: every frozen line in them word
for word, each file labelled fiction first, and no other line naming him."""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_life  # noqa: E402


def test_her_files_hold_every_frozen_line_and_nothing_else_names_him():
    files = make_life.files()
    every = "\n".join(files.values())
    q = make_life.Q
    known = [
        *(f["sentence"] for f in q["facts"]),
        *(x["line"] for x in q["quotes"]),
        *(t["line"] for t in q["traps"]),
        *q["fiction_lines"],
    ]
    assert all(k in every for k in known)
    names = re.compile(q["names"])
    for path, text in files.items():
        lines = text.splitlines()
        assert "Fiction" in lines[0], path
        assert all(any(k in ln for k in known) for ln in lines if names.search(ln))


def test_the_same_bytes_every_run_and_no_date_after_her_today():
    make_life.R.seed(2020)
    one = make_life.files()
    make_life.R.seed(2020)
    assert make_life.files() == one
    assert (
        one == {p: (make_life.LIFE / p).read_text(encoding="utf-8") for p in one}
        or not make_life.LIFE.exists()
    )
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", "\n".join(one.values()))
    assert dates and max(dates) <= make_life.Q["wren_today"]
