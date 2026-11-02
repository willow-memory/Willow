"""weights-pin: a weights file runs only while it is the one on its card."""

from __future__ import annotations

import hashlib
import struct
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "weights_pin.py"
CARD = HERE.parent / "weights-card" / "weights_card.py"


def gguf(name: str) -> bytes:
    """A GGUF header holding only general.name."""
    key, value = b"general.name", name.encode()
    return (b"GGUF" + struct.pack("<IQQ", 3, 0, 1) + struct.pack("<Q", len(key))
            + key + struct.pack("<IQ", 8, len(value)) + value)  # fmt: skip


def run(script: Path, *argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


@pytest.fixture
def pinned(tmp_path) -> tuple[Path, Path]:
    """A weights file and the card weights-card writes for it."""
    w = tmp_path / "gemma.gguf"
    w.write_bytes(gguf("Gemma"))
    made = run(CARD, "--from", w, "--to", tmp_path / "gemma.md")
    assert made.returncode == 0, made.stderr
    return w, tmp_path / "gemma.md"


def test_the_file_on_its_card_is_the_same(pinned):
    w, card = pinned
    got = run(SCRIPT, "--card", card, "--from", w)
    assert got.returncode == 0, got.stderr
    digest = hashlib.sha256(w.read_bytes()).hexdigest()
    assert got.stdout == f"same     gemma.gguf  sha256={digest} (as on its card)\n"


def test_a_file_changed_in_place_differs(pinned):
    w, card = pinned
    was = hashlib.sha256(w.read_bytes()).hexdigest()
    w.write_bytes(gguf("Gemmb"))  # one byte changed, the same size
    now = hashlib.sha256(w.read_bytes()).hexdigest()
    got = run(SCRIPT, "--card", card, "--from", w)
    assert got.returncode == 42
    size = len(gguf("Gemma"))
    assert got.stdout == (
        f"differs  gemma.gguf: its card says sha256={was} ({size} bytes);\n"
        f"         the file is sha256={now} ({size} bytes)\n"
    )


def test_a_file_of_another_size_differs_without_being_read(pinned, tmp_path):
    w, card = pinned
    other = tmp_path / "other.gguf"
    other.write_bytes(gguf("Gemma 3"))
    got = run(SCRIPT, "--card", card, "--from", other)
    assert got.returncode == 42
    assert (
        f"the file is sha256=not read, another size ({other.stat().st_size} bytes)"
        in got.stdout
    )
    assert got.stdout.endswith("         its card names gemma.gguf\n")


def test_the_hash_decides_not_the_name(pinned, tmp_path):
    w, card = pinned
    renamed = tmp_path / "renamed.gguf"
    renamed.write_bytes(w.read_bytes())
    got = run(SCRIPT, "--card", card, "--from", renamed)
    assert got.returncode == 0 and got.stdout.startswith("same     renamed.gguf  ")


def test_a_card_written_by_hand_is_read(tmp_path):
    w = tmp_path / "m.bin"
    w.write_bytes(b"weights")
    digest = hashlib.sha256(b"weights").hexdigest()
    card = tmp_path / "m.md"
    card.write_text(f"# M\n<!-- willow-model\nsha256: {digest}\nbytes: 7\n-->\n")
    assert run(SCRIPT, "--card", card, "--from", w).returncode == 0
    card.write_text(f"<!-- willow-model\nsha256 {digest}\nbytes: 7\n-->\n")
    assert run(SCRIPT, "--card", card, "--from", w).returncode == 2


@pytest.mark.parametrize(
    "text",
    [
        "# just notes\n",
        "<!-- willow-model\nsha256: abc\nbytes: 7\n-->\n",
        f"<!-- willow-model\nsha256: {'a' * 64}\nbytes: seven\n-->\n",
        f"<!-- willow-model\nsha256: {'a' * 64}\n-->\n",
        f"<!-- willow-model\nbytes: 7\n-->\nsha256: {'a' * 64}\n",
        f"<!-- willow-model\nsha256: {'a' * 64}\nbytes: 7\n",
        f"sha256: {'a' * 64}\nbytes: 7\n-->\n",
    ],
)
def test_a_card_without_a_pin_is_refused(text, tmp_path):
    w = tmp_path / "m.bin"
    w.write_bytes(b"weights")
    card = tmp_path / "m.md"
    card.write_text(text, encoding="utf-8")
    got = run(SCRIPT, "--card", card, "--from", w)
    assert got.returncode == 2 and "not a model card" in got.stderr
    assert got.stdout == ""


def test_a_bad_command_line_is_refused(pinned, tmp_path):
    w, card = pinned
    got = run(SCRIPT)
    assert got.returncode == 2 and "weights_pin.py" in got.stderr
    got = run(SCRIPT, "--card", card, "--from", w, "stray")
    assert got.returncode == 2 and "weights_pin.py" in got.stderr
    got = run(SCRIPT, "--card", card, "--from", tmp_path / "missing.gguf")
    assert got.returncode == 2 and "not a file" in got.stderr
    got = run(SCRIPT, "--card", tmp_path / "missing.md", "--from", w)
    assert got.returncode == 2 and "could not read the card" in got.stderr
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe")
    got = run(SCRIPT, "--card", tmp_path / "bad.md", "--from", w)
    assert got.returncode == 2 and "could not read the card" in got.stderr
