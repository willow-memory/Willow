"""tip-pin: a record cut short, or rewritten and re-hashed, passes `verify`
and is found by a pin kept outside the box."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

NOW = ["--now", "2026-10-26T00:00:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "kernel.py"), *argv], capture_output=True, text=True
    )


def tip(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "tip_pin.py"), *argv],
        capture_output=True,
        text=True,
    )


def box_of(tmp_path: Path, bites: int = 4) -> Path:
    """A box with a boot row and `bites` questions on its record."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    key = tmp_path / "key"
    key.write_text("ab" * 32)
    key.chmod(0o600)
    b = tmp_path / "box"
    assert (
        k(
            "init", "--box", str(b), "--pile", str(pile), "--key", str(key), *NOW
        ).returncode
        == 0
    )
    for i in range(bites):
        k("bite", "--box", str(b), *NOW, f"how much sun do tomatoes want {i}")
    return b


def pinned(tmp_path: Path, b: Path) -> Path:
    out = tmp_path / "keep" / "pin.json"
    out.parent.mkdir()
    assert tip("pin", "--box", str(b), "--to", str(out)).returncode == 0
    return out


def lines(b: Path) -> list[str]:
    return (b / "record.jsonl").read_text().split("\n")[:-1]


def put(b: Path, rows: list[dict]) -> None:
    """Rewrite the record with every row re-hashed from the first: the
    rewrite `verify` can't tell from the original."""
    prev, out = kernel.GENESIS, []
    for n, r in enumerate(rows):
        r = {x: v for x, v in r.items() if x != "hash"}
        r["n"], r["prev"] = n, prev
        r["hash"] = prev = kernel.h256(kernel.canon(r))
        out.append(kernel.canon(r))
    (b / "record.jsonl").write_text("\n".join(out) + "\n")


def test_a_pin_holds_the_rows_and_the_last_hash(tmp_path):
    b = box_of(tmp_path)
    out = pinned(tmp_path, b)
    rows = [json.loads(x) for x in lines(b)]
    assert json.loads(out.read_text()) == {"rows": len(rows), "tip": rows[-1]["hash"]}
    assert oct(out.stat().st_mode & 0o777) == "0o600"
    got = tip("check", "--box", str(b), "--pin", str(out))
    assert got.returncode == 0
    assert (
        got.stdout == f"holds       {len(rows)} rows pinned; the box has {len(rows)}\n"
    )


def test_a_record_that_has_only_grown_holds(tmp_path):
    b = box_of(tmp_path, bites=2)
    out = pinned(tmp_path, b)
    k("bite", "--box", str(b), *NOW, "another question about tomatoes")
    got = tip("check", "--box", str(b), "--pin", str(out))
    assert got.returncode == 0 and "(1 added since)" in got.stdout


def test_rows_cut_off_the_end_pass_verify_and_fail_the_pin(tmp_path):
    b = box_of(tmp_path)
    out = pinned(tmp_path, b)
    n = len(lines(b))
    (b / "record.jsonl").write_text("\n".join(lines(b)[:-2]) + "\n")
    assert k("verify", "--box", str(b)).returncode == 0  # the gap
    got = tip("check", "--box", str(b), "--pin", str(out))
    assert got.returncode == 42
    assert got.stdout == f"cut short   {n} rows pinned; the box has {n - 2}\n"


def test_a_bite_dropped_and_the_chain_rehashed_passes_verify_and_fails_the_pin(
    tmp_path,
):
    # the gap as it was reproduced: one row gone, every hash after it redone
    b = box_of(tmp_path)
    out = pinned(tmp_path, b)
    rows = [json.loads(x) for x in lines(b)]
    put(b, rows[:1] + rows[2:])
    assert k("verify", "--box", str(b)).returncode == 0  # the gap
    got = tip("check", "--box", str(b), "--pin", str(out))
    assert got.returncode == 42 and "cut short" in got.stdout


def test_a_record_rewritten_and_rehashed_passes_verify_and_fails_the_pin(tmp_path):
    b = box_of(tmp_path)
    out = pinned(tmp_path, b)
    rows = [json.loads(x) for x in lines(b)]
    n = len(rows)
    put(b, rows[:1] + rows[2:] + [rows[-1]])  # a bite dropped, another row added
    assert k("verify", "--box", str(b)).returncode == 0  # the gap
    got = tip("check", "--box", str(b), "--pin", str(out))
    assert got.returncode == 42
    assert got.stdout == f"rewritten   row {n - 1} is not the one you pinned\n"


def test_a_rewrite_that_keeps_the_pinned_row_but_changes_an_earlier_one_is_found(
    tmp_path,
):
    # re-hashing from an earlier row changes every hash after it, the pinned one too
    b = box_of(tmp_path)
    out = pinned(tmp_path, b)
    rows = [json.loads(x) for x in lines(b)]
    rows[1]["where"] = "elsewhere.md"
    put(b, rows)
    assert k("verify", "--box", str(b)).returncode == 0
    assert tip("check", "--box", str(b), "--pin", str(out)).returncode == 42


def test_a_row_dropped_without_rehashing_is_refused_by_the_chain_itself(tmp_path):
    b = box_of(tmp_path)
    out = pinned(tmp_path, b)
    rest = lines(b)
    del rest[1]
    (b / "record.jsonl").write_text("\n".join(rest) + "\n")
    got = tip("check", "--box", str(b), "--pin", str(out))
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_pin_refuses_a_record_that_does_not_verify(tmp_path):
    b = box_of(tmp_path)
    (b / "record.jsonl").write_text(lines(b)[0][:-3] + "\n")
    got = tip("pin", "--box", str(b), "--to", str(tmp_path / "pin.json"))
    assert got.returncode == 2 and "doesn't verify" in got.stderr
    assert not (tmp_path / "pin.json").exists()


def test_pin_refuses_an_empty_record_and_a_folder_that_is_not_a_box(tmp_path):
    b = box_of(tmp_path)
    (b / "record.jsonl").write_text("")
    got = tip("pin", "--box", str(b), "--to", str(tmp_path / "pin.json"))
    assert got.returncode == 2 and "empty" in got.stderr
    got = tip("pin", "--box", str(tmp_path), "--to", str(tmp_path / "pin.json"))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_pin_never_writes_inside_the_box_or_the_folder_or_over_a_file(tmp_path):
    b = box_of(tmp_path)
    for inside, name in ((b, "the box"), (tmp_path / "pile", "your folder")):
        got = tip("pin", "--box", str(b), "--to", str(inside / "pin.json"))
        assert got.returncode == 2 and f"inside {name}" in got.stderr
        assert not (inside / "pin.json").exists()
    old = tmp_path / "old.json"
    old.write_text("keep me")
    got = tip("pin", "--box", str(b), "--to", str(old))
    assert got.returncode == 2 and "never overwrites" in got.stderr
    assert old.read_text() == "keep me"


def test_pin_does_not_make_a_missing_folder(tmp_path):
    b = box_of(tmp_path)
    got = tip("pin", "--box", str(b), "--to", str(tmp_path / "nope" / "pin.json"))
    assert got.returncode == 2 and "never makes one" in got.stderr
    assert not (tmp_path / "nope").exists()


def test_check_refuses_what_is_not_a_pin(tmp_path):
    b = box_of(tmp_path)
    tipx = "a" * 64
    bad = {
        "missing": tmp_path / "missing.json",
        "text": "not json",
        "a list": "[1, 2]",
        "extra key": json.dumps({"rows": 3, "tip": tipx, "more": 1}),
        "no tip": json.dumps({"rows": 3}),
        "zero rows": json.dumps({"rows": 0, "tip": tipx}),
        "bool rows": json.dumps({"rows": True, "tip": tipx}),
        "text rows": json.dumps({"rows": "3", "tip": tipx}),
        "short tip": json.dumps({"rows": 3, "tip": "abc"}),
        "upper tip": json.dumps({"rows": 3, "tip": "A" * 64}),
        "number tip": json.dumps({"rows": 3, "tip": 5}),
    }
    for why, content in bad.items():
        path = content if isinstance(content, Path) else tmp_path / "p.json"
        if not isinstance(content, Path):
            path.write_text(content)
        got = tip("check", "--box", str(b), "--pin", str(path))
        assert got.returncode == 2 and "refused" in got.stderr, why


def test_check_refuses_a_box_that_does_not_verify_or_is_not_one(tmp_path):
    b = box_of(tmp_path)
    out = pinned(tmp_path, b)
    got = tip("check", "--box", str(tmp_path / "nowhere"), "--pin", str(out))
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    (b / "record.jsonl").write_text(lines(b)[0][:-3] + "\n")
    got = tip("check", "--box", str(b), "--pin", str(out))
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_the_command_line_is_exact(tmp_path):
    b = box_of(tmp_path)
    out = pinned(tmp_path, b)
    for argv in (
        [],
        ["pin"],
        ["check", "--box", str(b)],
        ["check", "--box", str(b), "--pin"],
        ["check", "--box", str(b), "--to", str(out)],  # pin takes --to, check --pin
        ["pin", "--box", str(b), "--pin", str(out)],
        ["check", "--bx", str(b), "--pin", str(out)],
        ["check", "--box", str(b), "--pin", str(out), "extra"],
        ["verify", "--box", str(b), "--pin", str(out)],
    ):
        got = tip(*argv)
        assert got.returncode == 2 and "tip_pin.py" in got.stderr, argv


def test_it_reads_no_key_and_writes_nothing_in_the_box(tmp_path):
    b = box_of(tmp_path)
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    out = pinned(tmp_path, b)
    tip("check", "--box", str(b), "--pin", str(out))
    assert before == {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
