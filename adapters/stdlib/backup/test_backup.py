"""backup: one zip of the box, every byte and the chain checked before it's
kept; the key never read and never in it; never beside the key or inside
what it backs up; and it restores by unzipping."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("backup", HERE / "backup.py")
bk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bk)
NOW = ["--now", "2026-10-24T09:30:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def life(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "dentist.txt").write_text("The dentist is on Tuesday at 3pm.\n")
    (tmp_path / "keys").mkdir()
    b = tmp_path / "box"
    k(
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "keys" / "key"),
        *NOW,
    )
    served = json.loads(k("bite", "--box", str(b), *NOW, "when is the dentist").stdout)[
        "served"
    ]
    row = {
        "path": "dentist.md",
        "data": "Tuesday 3pm",
        "cites": [served[0]["id"]],
        "claim": "the note",
    }
    (tmp_path / "s.jsonl").write_text(json.dumps(row) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"), *NOW)
    subj = json.loads((b / "record.jsonl").read_text().splitlines()[-1])["subject"]
    k("seal", "--box", str(b), subj, *NOW)
    (b / "notes-of-mine.txt").write_text("not the kernel's\n")
    return b


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "backup.py"), *argv], capture_output=True, text=True
    )


def test_one_zip_of_the_box_checked_and_without_the_key(tmp_path):
    b = life(tmp_path)
    got = run("--box", str(b), "--to", str(tmp_path / "usb"), *NOW)
    assert got.returncode == 0, got.stderr
    z = tmp_path / "usb" / "willow-backup-20261024-093000.zip"
    names = zipfile.ZipFile(z).namelist()
    assert {"kernel.json", "record.jsonl", "written/dentist.md"} <= set(names)
    assert any(n.startswith("proposals/") for n in names)
    assert "notes-of-mine.txt" not in names and not any(
        "key" == Path(n).name for n in names
    )
    key = (tmp_path / "keys" / "key").read_text().strip()
    assert all(key.encode() not in zipfile.ZipFile(z).read(n) for n in names)
    assert "every byte and the chain checked" in got.stdout
    assert (
        str(tmp_path / "keys" / "key") in got.stdout
        and "willow never reads it" in got.stdout
    )


def test_it_restores_by_unzipping(tmp_path):
    b = life(tmp_path)
    run("--box", str(b), "--to", str(tmp_path / "usb"), *NOW)
    restored = tmp_path / "restored"
    zipfile.ZipFile(next((tmp_path / "usb").glob("*.zip"))).extractall(restored)
    assert k("verify", "--box", str(restored)).returncode == 0
    got = k("bite", "--box", str(restored), *NOW, "when is the dentist")
    assert json.loads(got.stdout)["state"] == "sealed"


def test_a_copy_that_differs_is_caught(tmp_path):
    b = life(tmp_path)
    z = tmp_path / "bad.zip"
    with zipfile.ZipFile(z, "w") as out:
        for p in bk.files(b):
            data = p.read_bytes()
            if p.name == "record.jsonl":
                data = data.replace(b'"bite"', b'"bitE"', 1)
            out.writestr(p.relative_to(b).as_posix(), data)
    assert "differs from the box: record.jsonl" in bk.check(z, b)
    with zipfile.ZipFile(z, "w") as out:
        for p in bk.files(b)[1:]:
            out.writestr(p.relative_to(b).as_posix(), p.read_bytes())
    assert "differs from the box" in bk.check(z, b)


def test_a_copy_whose_chain_breaks_is_caught_even_if_the_box_broke_the_same_way(
    tmp_path,
):
    b = life(tmp_path)
    rec = b / "record.jsonl"
    z = tmp_path / "same.zip"
    with zipfile.ZipFile(z, "w") as out:
        for p in bk.files(b):
            out.writestr(p.relative_to(b).as_posix(), p.read_bytes())
    assert bk.check(z, b) is None
    rec.write_bytes(rec.read_bytes().replace(b'"bite"', b'"bitE"', 1))
    with zipfile.ZipFile(z, "w") as out:
        for p in bk.files(b):
            out.writestr(p.relative_to(b).as_posix(), p.read_bytes())
    assert "doesn't verify" in bk.check(z, b)


def test_never_beside_the_key_nor_inside_what_it_backs_up(tmp_path):
    b = life(tmp_path)
    for to, why in ((tmp_path / "keys", "where your key is"), (b / "bk", "inside the box"),
                    (b, "inside the box"), (tmp_path / "pile" / "bk", "inside your files")):  # fmt: skip
        got = run("--box", str(b), "--to", str(to), *NOW)
        assert got.returncode == 2 and why in got.stderr, (to, got.stderr)
    assert not (b / "bk").exists()


def test_a_broken_record_isnt_copied_and_nothing_is_overwritten(tmp_path):
    b = life(tmp_path)
    assert run("--box", str(b), "--to", str(tmp_path / "usb"), *NOW).returncode == 0
    again = run("--box", str(b), "--to", str(tmp_path / "usb"), *NOW)
    assert again.returncode == 2 and "isn't overwritten" in again.stderr
    rec = b / "record.jsonl"
    rec.write_bytes(rec.read_bytes().replace(b'"bite"', b'"bitE"', 1))
    got = run("--box", str(b), "--to", str(tmp_path / "usb2"), *NOW)
    assert got.returncode == 2 and "doesn't verify" in got.stderr
    assert (
        not list((tmp_path / "usb2").glob("*.zip"))
        if (tmp_path / "usb2").exists()
        else True
    )


def test_a_failed_check_leaves_no_zip(tmp_path, monkeypatch):
    b = life(tmp_path)
    monkeypatch.setattr(bk, "check", lambda z, box: "the copy differs from the box: x")
    monkeypatch.setattr(
        sys, "argv", ["backup.py", "--box", str(b), "--to", str(tmp_path / "usb")]
    )
    out, said = bk.backup(b, tmp_path / "usb", "2026-10-24T09:30:00Z")
    assert out is None and "differs" in said
    assert list((tmp_path / "usb").glob("*.zip")) == []


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b = life(tmp_path)
    for argv in (
        [],
        ["--box", str(b)],
        ["--to", str(tmp_path)],
        ["--box", str(b), "--to", str(tmp_path), "x"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "backup.py" in got.stderr
    got = run("--box", str(tmp_path / "pile"), "--to", str(tmp_path / "u"))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_the_key_line_is_each_systems_own():
    key = Path("/home/a b/willow/key")
    assert (
        bk.how_to_copy(key, "posix")
        == "cp '/home/a b/willow/key' /path/to/your/usb/stick/"
    )
    assert bk.how_to_copy(key, "nt") == f'copy "{key}" E:\\'
