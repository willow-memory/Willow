"""times.py: test-times.json kept to what CI's own run took, by a script. Python 3.9+.

    python adapters/stdlib/ci/times.py write --run latest|RUN_ID
    python adapters/stdlib/ci/times.py write --from DIR [DIR ...]
    python adapters/stdlib/ci/times.py check

test-times.json is each add-on test file's seconds, which ci.py cuts the
add-ons' tests into even chunks by. It was made by hand from one run, and
went stale: a file it doesn't list counts as the median, so new files, and
files that grew, unbalance the chunks (CI's slowest shard sets every pull
request's wait).

CI writes pytest's JUnit XML for each tests:adapters gate on a push to main
(WILLOW_JUNIT_DIR, one file per gate) and keeps them as the run's
`test-times` artifact. `write --run latest` fetches that artifact from the
last green run on main with gh (`--run ID` names one); `--from DIR` reads
XML files already here. Each file seen gets its seconds, summed over its
tests; a file not seen keeps what it had; a file that's gone comes out.
`check` says which test files the json lacks and which it lists that are
gone; it reads nothing online, and staleness never fails: only the
balance depends on it.

Exit codes, the kernel's: 0 written, or current (check); 42 check: it
lacks files or lists gone ones, said; 2 refused (no artifact, gh not here,
nothing to read).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

TIMES = HERE / "test-times.json"
ARTIFACT = "test-times"
USAGE = ("usage: times.py write --run latest|RUN_ID | times.py write --from DIR [DIR ...]"
         " | times.py check")  # fmt: skip


class Refused(Exception):
    pass


def test_files(root: Path = ROOT) -> set[str]:
    """Every add-on test file ci.py cuts into chunks."""
    return {p.relative_to(root).as_posix()
            for p in (root / "adapters" / "stdlib").rglob("test_*.py")
            if "__pycache__" not in p.parts}  # fmt: skip


def _file_of(classname: str, root: Path) -> str | None:
    """adapters.stdlib.a11y-check.test_a11y_check(.TestClass) -> its path."""
    parts = classname.split(".")
    for k in range(len(parts), 0, -1):
        rel = "/".join(parts[:k]) + ".py"
        if (root / rel).is_file():
            return rel
    return None


def measured(xml_texts: list[str], root: Path = ROOT) -> dict[str, float]:
    """{test file: seconds}, each testcase's time summed under its file."""
    out: dict[str, float] = {}
    for text in xml_texts:
        for case in ET.fromstring(text).iter("testcase"):
            rel = _file_of(case.get("classname", ""), root)
            if rel:
                out[rel] = out.get(rel, 0.0) + float(case.get("time") or 0)
    return out


def merged(
    old: dict[str, float], seen: dict[str, float], files: set[str]
) -> dict[str, float]:
    """What was seen, what wasn't kept as it was, what's gone left out."""
    out = {f: t for f, t in old.items() if f in files}
    out.update({f: max(0.1, round(t, 1)) for f, t in seen.items() if f in files})
    return dict(sorted(out.items()))


def text_of(times: dict[str, float]) -> str:
    return json.dumps(times, indent=1) + "\n"


def from_run(run: str) -> list[str]:
    """The XML files of a CI run's test-times artifact, by gh."""
    gh = shutil.which("gh")
    if gh is None:
        raise Refused("gh isn't installed: fetch the artifact by hand and use --from")
    if run == "latest":
        got = subprocess.run([gh, "run", "list", "--workflow", "ci.yml", "--branch", "main",
                              "--status", "success", "--event", "push", "--limit", "1",
                              "--json", "databaseId", "--jq", ".[0].databaseId"],
                             capture_output=True, text=True)  # fmt: skip
        run = got.stdout.strip()
        if got.returncode != 0 or not run:
            raise Refused(f"no green run on main to read: {got.stderr.strip()[:200]}")
    with tempfile.TemporaryDirectory() as tmp:
        got = subprocess.run([gh, "run", "download", run, "--name", ARTIFACT, "--dir", tmp],
                             capture_output=True, text=True)  # fmt: skip
        if got.returncode != 0:
            raise Refused(
                f"run {run} has no {ARTIFACT} artifact: {got.stderr.strip()[:200]}"
            )
        return [p.read_text(encoding="utf-8") for p in sorted(Path(tmp).rglob("*.xml"))]


def main(argv: list[str]) -> int:
    if argv == ["check"]:
        listed = set(json.loads(TIMES.read_text(encoding="utf-8")))
        files = test_files()
        lack, gone = sorted(files - listed), sorted(listed - files)
        for f in lack:
            print(f"not in test-times.json (counted as the median): {f}")
        for f in gone:
            print(f"in test-times.json, gone: {f}")
        if lack or gone:
            print(
                "python adapters/stdlib/ci/times.py write --run latest brings it up to date"
            )
            return kernel.ESCALATE
        print(f"test-times.json lists every add-on test file ({len(files)})")
        return kernel.ALIVE
    try:
        if argv[:1] == ["write"] and argv[1:2] == ["--run"] and len(argv) == 3:
            texts = from_run(argv[2])
        elif argv[:1] == ["write"] and argv[1:2] == ["--from"] and len(argv) >= 3:
            texts = [p.read_text(encoding="utf-8")
                     for d in argv[2:] for p in sorted(Path(d).rglob("*.xml"))]  # fmt: skip
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
        if not texts:
            raise Refused("no JUnit XML to read")
        seen = measured(texts)
    except (Refused, OSError, ET.ParseError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    old = json.loads(TIMES.read_text(encoding="utf-8"))
    new = merged(old, seen, test_files())
    moved = sum(
        1 for f in new if f in old and abs(new[f] - old[f]) >= max(1.0, old[f] / 2)
    )
    added, removed = len(set(new) - set(old)), len(set(old) - set(new))
    if text_of(new) != TIMES.read_text(encoding="utf-8"):
        TIMES.write_text(text_of(new), encoding="utf-8")
    print(f"test-times.json: {len(seen)} files measured, {added} added, {removed} gone,"
          f" {moved} moved by half or more")  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
