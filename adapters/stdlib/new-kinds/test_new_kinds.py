"""new-kinds's tests: a kind no step reads is said with the readers that
took some of it, tried on copies; a kind a step reads, or one left, isn't;
and nothing of a file but its kind and count is ever said."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "new_kinds.py"
spec = importlib.util.spec_from_file_location("new_kinds", SCRIPT)
nk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nk)

OUTBOX = {
    "type": "OrderedCollection",
    "orderedItems": [{"type": "Create", "published": "2024-03-02T08:15:00Z",
                      "object": {"type": "Note", "content": "<p>Planted the BEANSTALK.</p>"}}],
}  # fmt: skip


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)  # fmt: skip


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """Named and filled so a leak would show."""
    f = tmp_path / "pile"
    (f / "sub").mkdir(parents=True)
    (f / ".hidden").mkdir()
    (f / "outbox-SECRETNAME.json").write_text(json.dumps(OUTBOX))
    (f / "sub" / "settings-OTHERNAME.json").write_text('{"theme": "WALRUS"}')
    (f / "diary-PRIVATE.txt").write_text("Rain again.\n")
    (f / "blob-ODDNAME.qqzz").write_bytes(b"\0\1\2QUOKKA")
    (f / ".hidden" / "a.qqyy").write_bytes(b"\0\1")
    return f


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    for args in ([], ["--from"], ["--from", str(tmp_path / "nope")],
                 ["--from", str(tmp_path), "--leave", "json"],
                 ["--from", str(tmp_path), "--what"]):  # fmt: skip
        got = run(*args)
        assert got.returncode == 2 and "new_kinds.py" in got.stderr, args
        assert got.stdout == ""
    prose = tmp_path / "stack.md"
    prose.write_text("# a stack\n\nno steps at all\n")
    got = run("--from", str(tmp_path), "--stack", str(prose))
    assert got.returncode == 2 and "names no steps" in got.stderr


def test_a_kind_no_step_reads_is_said_with_the_readers_that_took_it(folder):
    got = run("--from", str(folder), "--json")
    assert got.returncode == 42, got.stderr
    doc = json.loads(got.stdout)
    assert doc["addon"] == "new-kinds" and doc["state"] == "populated"
    rows = {
        g["name"]: {r["where"]: r["what"] for r in g["rows"]} for g in doc["groups"]
    }
    shape = rows["a reader knows their shape"][".json"]
    assert shape.startswith("2 files; ") and "mastodon took 1 of 2" in shape
    assert "any .json is taken by json-paths" in shape
    assert "json-paths took" not in shape  # it takes anything, so it is no fit
    assert ".txt" not in json.dumps(
        rows["a reader knows their shape"]
    )  # plain text, no shape
    assert rows["no reader for them yet"][".qqzz"].startswith("1 file;")
    assert ".qqyy" not in got.stdout  # hidden, as the kernel skips it
    for leak in ("SECRETNAME", "OTHERNAME", "PRIVATE", "ODDNAME", "BEANSTALK", "WALRUS",
                 "QUOKKA", "Rain", "outbox", "sub"):  # fmt: skip
        assert leak not in got.stdout, leak


def test_a_kind_a_step_reads_or_you_leave_is_not_said(folder, tmp_path):
    stack = tmp_path / "stack.md"
    stack.write_text(f"# s\n## read\n- mastodon -- mirror --from {folder} --to {tmp_path / 'm'}\n- digest\n")  # fmt: skip
    got = run("--from", str(folder), "--stack", str(stack))
    assert got.returncode == 42 and ".json" not in got.stdout and ".qqzz" in got.stdout
    got = run("--from", str(folder), "--stack", str(stack), "--leave", ".QQZZ")
    assert got.returncode == 0, got.stdout
    assert got.stdout.startswith("new-kinds: empty, every kind of 3 in 1 folder")
    assert run("--from", str(folder), "--leave", ".json,.qqzz").returncode == 0


def test_what_the_kernel_cant_read_names_its_readers_even_when_none_took_it(tmp_path):
    f = tmp_path / "pile"
    f.mkdir()
    (f / "scan.pdf").write_bytes(b"%PDF-1.4\0\0not really")
    doc = json.loads(run("--from", str(f), "--json").stdout)
    (g,) = doc["groups"]
    assert g["name"] == "the kernel can't read them"
    what = g["rows"][0]["what"]
    assert what.startswith("1 file; ") and "pdf" in what


def test_the_copies_tried_are_gone_after(folder, tmp_path, monkeypatch, capsys):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(nk.tempfile, "tempdir", str(scratch))
    assert nk.main(["--from", str(folder)]) == 42
    assert "mastodon took 1 of 2" in capsys.readouterr().out
    assert list(scratch.iterdir()) == []


def test_a_reader_that_fails_or_refuses_took_nothing(tmp_path):
    src = tmp_path / "from"
    (src / "0").mkdir(parents=True)
    (src / "0" / "a.json").write_text("{}")
    bad = tmp_path / "bad.py"
    bad.write_text("import sys\nsys.exit(2)\n")
    assert nk.took_by(bad, src, tmp_path / "to") == set()
    ok = tmp_path / "ok.py"
    ok.write_text(
        "import sys, pathlib\nto = pathlib.Path(sys.argv[sys.argv.index('--to') + 1])\n"
        "(to / '0').mkdir(parents=True)\n(to / '0' / 'a.txt').write_text('x')\n"
        "(to / 'places.json').write_text('{}')\n"
    )
    assert nk.took_by(ok, src, tmp_path / "to2") == {
        "0"
    }  # a sidecar isn't a file taken
    slow = tmp_path / "slow.py"
    slow.write_text("import time\ntime.sleep(5)\n")
    nk.TRY_SECONDS, was = 0.5, nk.TRY_SECONDS
    try:
        assert nk.took_by(slow, src, tmp_path / "to3") == set()
    finally:
        nk.TRY_SECONDS = was


def test_a_few_files_are_tried_spread_over_the_kind():
    some = nk.sample([Path(f"{i:02}.json") for i in range(10)])
    assert [p.name for p in some] == ["00.json", "03.json", "06.json", "09.json"]
    assert nk.sample([Path("b"), Path("a")]) == [Path("a"), Path("b")]
    assert (
        nk.nonsense(".json") == b'{"willow": 1}\n'
        and nk.nonsense(".gpx") == b"willow\n"
    )


def test_the_readers_are_the_cards_that_say_role_reads():
    known = nk.readers()
    assert ".json" in known["mastodon"]["reads"] and known["mastodon"]["script"]
    assert "new-kinds" not in known and "box-health" not in known
    assert all(
        r["script"] is None or r["script"].suffix == ".py" for r in known.values()
    )


def test_a_stack_whose_only_step_names_a_path_names_no_steps(tmp_path):
    stack = tmp_path / "stack.md"
    stack.write_text("# s\n## read\n- adapters/stdlib/mastodon -- mirror\n")
    got = run("--from", str(tmp_path), "--stack", str(stack))
    assert got.returncode == 2 and "names no steps" in got.stderr


def test_the_printed_report_heads_each_named_group_and_caps_the_where_column(folder):
    got = run("--from", str(folder))
    assert got.returncode == 42, got.stderr
    assert "## no reader for them yet" in got.stdout and "## None" not in got.stdout
    doc = nk.report("new-kinds", "populated", "said",
                    [(None, [("x" * 70, "long")]), ("named", [(".a", "short")])])  # fmt: skip
    assert nk.report_text(doc).splitlines() == [
        "new-kinds: populated, said",
        f"  {'x' * 70}  long",
        "## named",
        f"  {'.a':<60}  short",
    ]
