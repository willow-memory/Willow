"""The pools study's freeze holds: each file it names is the bytes it was,
and the grid, the seeded pairs and the cards made again come to the hashes
it keeps."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FROZEN = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_every_file_the_freeze_names_is_as_it_was():
    changed = [f for f, h in FROZEN["files"].items() if sha(ROOT / f) != h]
    assert not changed, f"changed since the freeze, so a new freeze is owed: {changed}"


def test_the_grid_pairs_and_cards_made_again_are_the_freezes(tmp_path):
    py = [sys.executable]
    grid, truth = HERE / "grid" / "grid.py", HERE / "truth" / "truth.py"
    subprocess.run([*py, str(grid), "write", "--to", str(tmp_path / "g")], check=True, capture_output=True)  # fmt: skip
    manifest = tmp_path / "g" / "manifest.json"
    subprocess.run([*py, str(truth), "pairs", "--grid", str(manifest), "--to", str(tmp_path / "p.json")], check=True, capture_output=True)  # fmt: skip
    subprocess.run([*py, str(truth), "cards", "--to", str(tmp_path / "c.json")], check=True, capture_output=True)  # fmt: skip
    made = FROZEN["made"]
    assert sha(manifest) == made["grid manifest (grid.py write)"]
    assert sha(tmp_path / "p.json") == made["no-bridge pairs (truth.py pairs)"]
    assert sha(tmp_path / "c.json") == made["cards (truth.py cards)"]


def test_every_pile_is_pinned_and_no_private_salt_is_kept():
    public = FROZEN["piles"]["public, on Kaggle"]
    private = FROZEN["piles"]["private, on the laptop only"]
    assert len(public) + len(private) >= json.loads((HERE / "truth" / "rules.json").read_text())["min_piles"]  # fmt: skip
    for name, p in public.items():
        assert len(p["shape"]) == 64 and p["salt"]
        assert ("commit" in p and len(p["commit"]) == 40) or name == "known-gaps"
    for p in private.values():
        assert set(p) == {"where", "shape", "salt_sha256"}
