"""alone.py: an add-on's tests run in a copy holding only the kernel, the
add-on and what its card uses; one that leans on an add-on its card doesn't
name fails, and one that only looks for an add-on holds without it."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("alone", HERE / "alone.py")
alone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alone)


def card(**fields: str) -> dict:
    return {"kind": "stdlib", "built": True, **fields}


def addon(root: Path, name: str, code: str, test: str) -> None:
    folder = root / "adapters" / "stdlib" / name
    folder.mkdir(parents=True)
    (folder / f"{name}.py").write_text(code)
    (folder / f"test_{name}.py").write_text(test)


@pytest.fixture
def willow(tmp_path, monkeypatch):
    """A scratch willow: the kernel's files, b, a that uses b and says so, c
    that uses b and doesn't, and d that looks for b and copes without it."""
    root = tmp_path / "willow"
    for f in alone.KERNEL_FILES:
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, root / f)
    addon(root, "b", "WORD = 'b'\n", "def test_b():\n    assert True\n")
    uses_b = (
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'b'))\n"
        "import b\n\n\ndef test_it():\n    assert b.WORD == 'b'\n"
    )
    addon(root, "a", "", uses_b)
    addon(root, "c", "", uses_b)
    addon(root, "d", "", (
        "from pathlib import Path\n\n\ndef test_it():\n"
        "    here = (Path(__file__).resolve().parents[1] / 'b').is_dir()\n"
        "    assert here in (True, False)\n"
    ))  # fmt: skip
    monkeypatch.setattr(alone, "ROOT", root)
    monkeypatch.setattr(alone, "STDLIB", root / "adapters" / "stdlib")
    return {
        "a": card(uses="b"),
        "b": card(),
        "c": card(),
        "d": card(**{"looks-for": "b"}),
    }


def test_what_a_card_uses_comes_along_and_nothing_else(willow):
    assert alone.needed("a", willow) == ["a", "b"]
    assert alone.needed("c", willow) == ["c"]
    assert alone.needed("d", willow) == ["d"], "looks-for is never brought"


def test_an_add_on_that_says_what_it_uses_holds_alone(willow):
    assert alone.held("a", willow) == ("a", "")
    assert alone.held("d", willow) == ("d", "")


def test_one_that_leans_on_what_its_card_doesnt_name_fails(willow):
    name, why = alone.held("c", willow)
    assert name == "c" and why == "1 error", why  # b isn't there to import


def test_its_summary_never_holds_a_time_or_a_scratch_path(willow):
    _, why = alone.held("c", willow)
    assert " in " not in why and "willow-alone-" not in why, why


def test_a_bad_command_line_is_refused():
    assert alone.main(["--jobs", "0"]) == 2
    assert alone.main(["--stray"]) == 2
    assert alone.main(["no-such-add-on"]) == 2
