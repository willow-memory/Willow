"""renamed.py: a study's frozen code, run where the add-ons are now. Python 3.9+.

A study freezes its files and the tools it ran on, path and bytes. When an
add-on is renamed after (adapters/renamed.json), its folder moves, and the
frozen code still names the old one. Two of them, scan and predict, moved to
batch-ask and forecast-ask with their script files kept as they were, name
and bytes, so that what a study froze is still the same file. A study's
tests (never its frozen files) call this before they import frozen code:

    bridge()   each renamed add-on's folder on the import path, so a frozen
               `import scan` finds scan.py in batch-ask
    now(rel)   a path as a study froze it, as it is now:
               adapters/stdlib/scan/scan.py is adapters/stdlib/batch-ask/scan.py,
               adapters/stdlib/pins/pins.py is adapters/stdlib/unpinned/unpinned.py,
               and pins/pins.py (a path from the add-ons' folder) is
               unpinned/unpinned.py

Re-running a study's own scripts by hand still needs the commit it froze
at; each study's README says so.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = json.loads((ROOT / "adapters" / "renamed.json").read_text(encoding="utf-8"))
NAMES, KEPT = DOC["names"], set(DOC.get("kept_files", []))


def bridge() -> None:
    for new in NAMES.values():
        for kind in ("stdlib", "deps"):
            folder = ROOT / "adapters" / kind / new
            if folder.is_dir() and str(folder) not in sys.path:
                sys.path.append(str(folder))


def now(rel: str) -> str:
    parts = rel.split("/")
    at = 2 if parts[0] == "adapters" else 0
    if len(parts) > at + 1 and parts[at] in NAMES:
        old = parts[at]
        parts[at] = NAMES[old]
        if old not in KEPT and parts[-1] == old.replace("-", "_") + ".py":
            parts[-1] = NAMES[old].replace("-", "_") + ".py"
    return "/".join(parts)
