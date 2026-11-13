"""known_gaps.py: the cut keeps entries whole and parts under the kernel's
limit, a source that isn't its SHA-256 is refused, and the probes are well
formed, with three or more a gap and a control for each gap's reader."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("known_gaps", HERE / "known_gaps.py")
kg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kg)


def test_the_cut_keeps_each_entry_whole_and_each_part_under_the_limit(monkeypatch):
    monkeypatch.setattr(kg, "PART", 120)
    entry = "  <entry>\n    <orth>w{}</orth>\n    <quote>g{}</quote>\n  </entry>\n"
    tei = "<TEI>\n" + "".join(entry.format(i, i) for i in range(9)) + "</TEI>\n"
    parts = kg.parts(tei)
    assert "".join(parts) == tei and len(parts) > 1
    for p in parts:
        assert len(p.encode()) < 120
        assert p.count("<entry>") == p.count("</entry>")


def test_a_source_that_isnt_its_sha256_is_refused(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for name in kg.SOURCES:
        (src / name).write_bytes(b"not it")
    assert kg.main(["make", "--to", str(tmp_path / "pile"), "--from", str(src)]) == 2
    assert not (tmp_path / "pile").exists()


def test_a_bad_command_line_is_refused():
    assert kg.main([]) == 2
    assert kg.main(["make"]) == 2
    assert kg.main(["make", "--to"]) == 2
    assert kg.main(["make", "--to", "x", "--into", "y"]) == 2


def test_the_probes_are_three_or_more_a_gap_with_controls_for_its_reader():
    probes = json.loads((HERE / "probes.json").read_text(encoding="utf-8"))["probes"]
    keys = {"id", "gap", "reader", "expect", "question", "answer", "folder"}
    assert all(set(p) == keys and set(p["answer"]) == {"file", "line"} for p in probes)
    assert len({p["id"] for p in probes}) == len(probes)
    assert all(p["folder"] in ("pile", *kg.READERS) for p in probes)
    gaps: dict[str, set[str]] = {}
    for p in probes:
        if p["gap"] != "control":
            gaps.setdefault(p["gap"], set()).add(p["reader"])
    for gap, readers in gaps.items():
        assert sum(p["gap"] == gap for p in probes) >= 3, gap
        for r in readers:
            assert any(p["gap"] == "control" and p["reader"] == r for p in probes), r
