"""secrets-audit: each password, key and card number in plain files listed
by file, line and kind, the value never shown; placeholders, comparisons and
everyday addresses left alone; nothing written."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location(
    "secrets_audit", HERE / "secrets_audit.py"
)
sa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sa)
PV = sa.privacy()


@pytest.mark.parametrize("line, kinds", [
    ("wifi password: hunter2", ["password"]),
    ("user: cwcftp pw: widgets1998", ["password"]),
    ('$password = "s3cret word";', ["password"]),
    ("token sk-ant-abcdefghijklmnopqrstuvwxyz0123", ["key"]),
    ("-----BEGIN OPENSSH PRIVATE KEY-----", ["key"]),
    ("card 4111 1111 1111 1111", ["card"]),
    ("IBAN GB82 WEST 1234 5698 7654 32", ["iban"]),
    ("SSN 078-05-1120", ["ssn"]),
    ("netbank: client 61847720  pw Wendouree#14", ["password"]),
    ("myGov: ana@example.org / Tide2024!", ["password"]),
    ("password: changeme", []),
    ("password:", []),
    ("if ($p == $password) { ok(); }", []),
    ("password = None", []),
    ("password: env:WIFI", []),
    ("write to ana@example.org or call (555) 010-0142", []),
    ("order 4111111111111112", []),  # fails Luhn
    ("The password policy changed last year.", []),
])  # fmt: skip
def test_each_kind_is_found_and_ordinary_lines_are_left_alone(line, kinds):
    assert sa.kinds_in(line, PV) == kinds


def test_a_file_of_passwords_is_read_as_one(tmp_path):
    pile = tmp_path / "pile"
    (pile / "Desktop").mkdir(parents=True)
    (pile / "Desktop" / "passwords.txt").write_text(
        "PASSWORDS - do not lose!!\n\nancestry: Considine1911\nNetflix: kieran knows\n"
    )
    (pile / "family.txt").write_text("ancestry: Considine1911 was the census name\n")
    got = run("--from", str(pile))
    assert got.returncode == 42 and "Desktop/passwords.txt:3  password" in got.stdout
    assert "family.txt" not in got.stdout, "the same words in another file aren't one"
    assert "Considine1911" not in got.stdout and "1 place hold" in got.stdout


def make(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    (pile / "work").mkdir(parents=True)
    (pile / "wifi.txt").write_text("Router in the hall.\nwifi password: hunter2\n")
    (pile / "work" / "deploy.md").write_text(
        "Deploy notes\n\nkey sk-ant-abcdefghijklmnopqrstuvwxyz0123\n"
    )
    (pile / "shopping.txt").write_text("Milk, eggs, bread.\n")
    return pile


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "secrets_audit.py"), *argv],
        capture_output=True,
        text=True,
    )


def test_a_folder_is_listed_by_file_line_and_kind_never_the_value(tmp_path):
    pile = make(tmp_path)
    got = run("--from", str(pile))
    assert got.returncode == 42
    assert "wifi.txt:2" in got.stdout and "password" in got.stdout
    assert "work/deploy.md:3" in got.stdout and "  key" in got.stdout
    assert "hunter2" not in got.stdout and "sk-ant" not in got.stdout
    assert "2 places hold a secret" in got.stdout and "shopping" not in got.stdout


def test_a_box_audits_its_own_files_and_writes_nothing(tmp_path):
    pile = make(tmp_path)
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "k")],
                   check=True, capture_output=True)  # fmt: skip
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    got = run("--box", str(b))
    assert got.returncode == 42 and "wifi.txt:2" in got.stdout
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_nothing_found_says_so(tmp_path):
    (tmp_path / "pile").mkdir()
    (tmp_path / "pile" / "a.txt").write_text("Nothing secret here.\n")
    got = run("--from", str(tmp_path / "pile"))
    assert got.returncode == 0 and "No passwords, keys or card numbers" in got.stdout


def test_without_the_privacy_add_on_typed_passwords_are_still_found(
    tmp_path, monkeypatch, capsys
):
    pile = make(tmp_path)
    monkeypatch.setattr(sa, "STDLIB", tmp_path / "empty")
    assert sa.privacy() is None
    assert sa.main(["--from", str(pile)]) == 42
    out = capsys.readouterr()
    assert (
        "only typed passwords" in out.err
        and "wifi.txt:2" in out.out
        and "key" not in out.out
    )


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    for argv in (
        [],
        ["--box"],
        ["--from", str(tmp_path), "--box", str(tmp_path)],
        ["--from", str(tmp_path), "x"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "secrets_audit.py" in got.stderr
    assert "not a kernel box" in run("--box", str(tmp_path)).stderr
    assert "isn't a folder" in run("--from", str(tmp_path / "nope")).stderr
