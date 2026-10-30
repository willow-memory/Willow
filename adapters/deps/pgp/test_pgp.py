"""pgp: a detached signature made by the person's own gpg, written only to
--to and never over a file; checked back, a changed file and an unknown key
both not good; and a refusal, never a quiet skip, without what it needs."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "pgp.py"


@pytest.fixture
def home():
    """A keyring of its own, with one key and no passphrase; gpg's agent
    socket needs a short path, so it's under the system's temp folder."""
    path = tempfile.mkdtemp(prefix="g")
    env = {**os.environ, "GNUPGHOME": path}
    subprocess.run(["gpg", "--batch", "--passphrase", "", "--quick-gen-key",
                    "Odile Varga <odile@example.org>", "ed25519", "sign", "never"],
                   env=env, capture_output=True, check=True)  # fmt: skip
    yield env
    subprocess.run(["gpgconf", "--kill", "gpg-agent"], env=env, capture_output=True)
    shutil.rmtree(path, ignore_errors=True)


def run(*argv: str, env) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True, env=env)  # fmt: skip


@pytest.fixture
def export(tmp_path: Path) -> Path:
    p = tmp_path / "answers.md"
    p.write_text("# Approved answers\n\nThe van was sold on 2021-05-14.\n")
    return p


def test_sign_then_verify(home, export, tmp_path):
    sig = tmp_path / "answers.md.asc"
    got = run("sign", str(export), "--to", str(sig), env=home)
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith("signed answers.md with key ")
    assert sig.read_text().startswith("-----BEGIN PGP SIGNATURE-----")
    ok = run("verify", str(export), str(sig), env=home)
    assert ok.returncode == 0, ok.stderr
    assert ok.stdout.startswith(
        "good signature by Odile Varga <odile@example.org>, key "
    )
    assert "your trust in the key: ultimate" in ok.stdout
    plain = subprocess.run(["gpg", "--verify", str(sig), str(export)], env=home,
                           capture_output=True, text=True)  # fmt: skip
    assert plain.returncode == 0  # gpg's standard form: anyone's gpg reads it


def test_a_changed_file_or_an_unknown_key_is_not_good(home, export, tmp_path):
    sig = tmp_path / "answers.md.asc"
    run("sign", str(export), "--to", str(sig), env=home)
    export.write_text(export.read_text().replace("2021", "2022"))
    bad = run("verify", str(export), str(sig), env=home)
    assert bad.returncode == 42 and bad.stdout.startswith("not good: ")
    stranger = {**home, "GNUPGHOME": tempfile.mkdtemp(prefix="g")}
    try:
        export.write_text(export.read_text().replace("2022", "2021"))
        unknown = run("verify", str(export), str(sig), env=stranger)
        assert unknown.returncode == 42 and "not good" in unknown.stdout
    finally:
        subprocess.run(
            ["gpgconf", "--kill", "gpg-agent"], env=stranger, capture_output=True
        )
        shutil.rmtree(stranger["GNUPGHOME"], ignore_errors=True)


def test_it_never_overwrites_and_never_makes_a_folder(home, export, tmp_path):
    sig = tmp_path / "answers.md.asc"
    sig.write_text("someone else's\n")
    assert run("sign", str(export), "--to", str(sig), env=home).returncode == 2
    assert sig.read_text() == "someone else's\n"
    deep = tmp_path / "no" / "such" / "x.asc"
    assert run("sign", str(export), "--to", str(deep), env=home).returncode == 2
    assert not (tmp_path / "no").exists()


def test_a_key_it_hasnt_is_refused_and_nothing_written(home, export, tmp_path):
    """gpg itself would sign with the default key instead: never here."""
    sig = tmp_path / "answers.md.asc"
    named = run("sign", str(export), "--to", str(sig), "--key", "Odile", env=home)
    assert named.returncode == 0, named.stderr
    sig.unlink()
    got = run(
        "sign", str(export), "--to", str(sig), "--key", "nobody@example.org", env=home
    )
    assert got.returncode == 2 and not sig.exists()


def test_refusals(home, export, tmp_path):
    for argv in ([], ["sign", str(export)], ["sign", str(export), "--to"],
                 ["sign", str(tmp_path / "none"), "--to", str(tmp_path / "s")],
                 ["sign", str(export), "--to", str(tmp_path / "s"), "--key"],
                 ["verify", str(export)], ["verify", str(export), str(tmp_path / "none")]):  # fmt: skip
        assert run(*argv, env=home).returncode == 2, argv


def test_without_gpg_it_refuses_and_names_the_install(export, tmp_path):
    env = {"PATH": str(tmp_path / "nothing"), "PYTHONPATH": ":".join(sys.path)}
    got = run("sign", str(export), "--to", str(tmp_path / "s.asc"), env=env)
    assert got.returncode == 2 and "gnupg" in got.stderr


def test_without_python_gnupg_it_refuses_and_names_the_install(export, tmp_path):
    blocker = tmp_path / "block"
    blocker.mkdir()
    (blocker / "gnupg.py").write_text("raise ImportError('hidden')\n")
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
    )
    got = subprocess.run([sys.executable, "-c", script, "verify", str(export), str(export)],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "requirements.txt" in got.stderr
