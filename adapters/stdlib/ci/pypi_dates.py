"""pypi_dates.py: PyPI's upload dates for every deps floor pin, kept for the tests. Python 3.9+.

    python adapters/stdlib/ci/pypi_dates.py write
    python adapters/stdlib/ci/pypi_dates.py check

The `deps:floors` gate asks PyPI when each floor pin came out, against the
release the floor rule names (the last before 2021). Its test can't go
online, so it reads pypi-dates.json beside this: for each package a deps
add-on pins at its floor, the floor's version and the rule's, each with its
first upload time, as PyPI gives them. It was a table typed into
test_ci.py, one more line by hand for each new deps package.

`check` says which floor pins the file lacks, and which of its packages no
add-on pins now; it reads no network. `write` asks PyPI only for a package
whose pins the file lacks, keeps the rest as they are, and writes it sorted,
so with nothing new it writes nothing and goes nowhere: made.py runs it in
every pull request.

Exit codes, the kernel's: 0 the file holds every floor pin (write: it does
now); 2 check: it doesn't, or a pin isn't on PyPI, or PyPI out of reach, or
refused.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

DATES = HERE / "pypi-dates.json"
USAGE = "usage: pypi_dates.py write | pypi_dates.py check"


def _ci():
    spec = importlib.util.spec_from_file_location("willow_ci_for_dates", HERE / "ci.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pinned(ci, root: Path) -> dict[str, set[str]]:
    """{package: the versions deps add-ons pin it at, at their floors}."""
    out: dict[str, set[str]] = {}
    for folder in sorted((root / "adapters" / "deps").glob("*/requirements-floor.txt")):
        for package, version in ci.pins_of(folder).items():
            out.setdefault(package, set()).add(version)
    return out


def missing(kept: dict, pins: dict[str, set[str]]) -> tuple[list[str], list[str]]:
    """(package==version pins the file lacks, its packages no add-on pins)."""
    lack = [f"{p}=={v}" for p, vs in sorted(pins.items()) for v in sorted(vs)
            if v not in kept.get(p, {})]  # fmt: skip
    extra = sorted(set(kept) - set(pins))
    return lack, extra


def write(ci, root: Path, path: Path, releases) -> list[str]:
    """The packages asked of PyPI; the file written only when it changes."""
    kept = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    pins = pinned(ci, root)
    asked, out = [], {}
    for package, versions in sorted(pins.items()):
        have = kept.get(package, {})
        if all(v in have for v in versions):
            out[package] = have
            continue
        asked.append(package)
        uploaded = releases(package)
        gone = sorted(v for v in versions if v not in uploaded)
        if gone:
            raise ValueError(f"{package}=={', '.join(gone)} is not on PyPI")
        rule = ci.rule_floor(uploaded)
        out[package] = {v: uploaded[v] for v in sorted({rule, *versions})}
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    return asked


def main(argv: list[str]) -> int:
    if argv not in (["write"], ["check"]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    ci = _ci()
    if argv == ["check"]:
        kept = json.loads(DATES.read_text(encoding="utf-8")) if DATES.exists() else {}
        lack, extra = missing(kept, pinned(ci, ROOT))
        for p in lack:
            print(f"not in pypi-dates.json: {p}")
        for p in extra:
            print(f"in pypi-dates.json, pinned by no add-on: {p}")
        if lack or extra:
            print("python adapters/stdlib/ci/pypi_dates.py write asks PyPI for them")
            return kernel.REFUSED
        print("pypi-dates.json holds every floor pin")
        return kernel.ALIVE
    try:
        asked = write(ci, ROOT, DATES, ci.releases)
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    for p in asked:
        print(f"asked PyPI: {p}")
    print("pypi-dates.json holds every floor pin" + (" now" if asked else ""))
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
