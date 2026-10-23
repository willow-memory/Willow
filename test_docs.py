"""The docs say what the repo holds, and the repo holds what the docs say.

- README.md's tree under "What's in this repo" lists every file in the repo,
  and nothing that isn't there.
- Every path a doc names, as a link or in backticks, exists: from the doc's
  own folder or the repo root. A path that lives somewhere else (another
  repo, a record folder the walkthrough makes) is listed in ELSEWHERE with
  where it lives. In a demo person's docs, most paths are inside their
  generated files, so only those starting at a repo entry are checked.
- The numbers README.md gives are the repo's: the case count, the kernel's
  length, Odile's files, and the Python versions CI runs.
- Every add-on folder has its card and its tests, and every port folder is run
  by vectors/compare.py.

The files are the ones git tracks plus any new ones it doesn't ignore, so a
file added without a line in the tree fails here before it is committed.
"""

from __future__ import annotations

import fnmatch
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"


def repo_files() -> set[str]:
    git = shutil.which("git")
    if git is None or not (ROOT / ".git").exists():
        pytest.fail(
            "the docs are checked against git's list of files: run from a clone"
        )
    out = subprocess.run(
        [git, "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {p for p in out.splitlines() if (ROOT / p).is_file()}


def dirs_of(files: set[str]) -> set[str]:
    return {
        str(Path(f).parents[i]) for f in files for i in range(len(Path(f).parts) - 1)
    }


def section(text: str, heading: str) -> str:
    start = text.index(heading)
    nxt = text.find("\n## ", start + len(heading))
    return text[start : nxt if nxt != -1 else len(text)]


# ── the tree ─────────────────────────────────────────────────────────────────
ENTRY = re.compile(r"^((?:│   |    )*)(├── |└── )(\S+)")


def tree() -> tuple[set[str], set[str]]:
    """(files, folders) README.md's tree lists, as paths from the repo root."""
    block = section(README.read_text(encoding="utf-8"), "## What's in this repo")
    lines = block.split("```")[1].strip("\n").splitlines()
    assert lines[0] == "willow/", "the tree starts at willow/"
    files: set[str] = set()
    folders: set[str] = set()
    stack: list[str] = []
    last_file_depth = None
    for n, line in enumerate(lines[1:], 2):
        m = ENTRY.match(line)
        if m is None:
            assert "├" not in line and "└" not in line, f"tree line {n}: {line!r}"
            continue  # a note under an entry
        depth, name = len(m.group(1)) // 4, m.group(3)
        assert len(m.group(1)) % 4 == 0, f"tree line {n} is indented off the grid"
        assert depth <= len(stack), f"tree line {n} is deeper than its parent"
        if last_file_depth is not None:
            assert depth <= last_file_depth, f"tree line {n} sits under a file"
        stack = stack[:depth]
        path = "/".join([*stack, name.rstrip("/")])
        if name.endswith("/"):
            folders.add(path)
            stack.append(name.rstrip("/"))
            last_file_depth = None
        else:
            files.add(path)
            last_file_depth = depth
    return files, folders


def test_the_tree_lists_every_file_and_nothing_else():
    listed, _ = tree()
    actual = repo_files()
    missing, extra = sorted(actual - listed), sorted(listed - actual)
    assert not missing and not extra, (
        f"README.md's tree is out of date.\n  in the repo, not the tree: {missing}"
        f"\n  in the tree, not the repo: {extra}"
    )


def test_every_folder_in_the_tree_is_one_that_holds_its_files():
    listed, folders = tree()
    assert folders <= dirs_of(listed), (
        f"empty folders: {sorted(folders - dirs_of(listed))}"
    )


# ── paths the docs name ──────────────────────────────────────────────────────
FENCE = re.compile(r"^```.*?^```", re.S | re.M)
LINK = re.compile(r"\]\(([^)\s]+)\)")
TICK = re.compile(r"`([A-Za-z0-9_.*\-/]+)`")
FILE = re.compile(
    r"\.(py|json|jsonl|md|ts|js|java|cs|csproj|yml|toml|txt|csv|ics|eml|key)$"
)

#: Paths a doc outside demo/ names that are not files of this repo, each with
#: where it lives. An entry its doc no longer names fails too, so this list
#: can't go stale.
ELSEWHERE = {
    "README.md": {
        "dad/": "in Odile's generated files (test_odiles_files_are_what_the_readme_says)",
        "hives/2026.txt": "in Odile's generated files (the same test)",
        "odile-record/": "made by the first-five-minutes walkthrough",
        "odile.key": "made by the first-five-minutes walkthrough",
    },
    "vectors/README.md": {
        "foundation/": "willow-bot",
        "foundation/gen.py": "willow-bot",
        "foundation/compare.py": "willow-bot",
        "canon_local.py": "willow-mcp",
        "test_sign.py": "willow-bot",
        "test_signing_encoding.py": "willow-mcp and willow-gate",
        "scripts/generate_states_js.py": "willows-grove",
        "states.js": "willows-grove",
        "dist/": "the TypeScript build's output, never committed",
    },
}
ODILE_NAMED = ("dad/", "hives/2026.txt")


def is_path(name: str) -> bool:
    """A backticked name that reads as a path, not a date like 21/10/2026."""
    if re.fullmatch(r"[\d/.\-]+", name):
        return False
    return "/" in name or bool(FILE.search(name))


def named_paths(doc: Path) -> list[tuple[str, Path]]:
    """(what the doc wrote, the folder it's relative to) for each path it
    names. Links always. Outside demo/, every backticked path; in a demo
    person's docs, those starting at an entry of the repo or of the doc's own
    folder (the rest are paths inside that person's generated files)."""
    text = FENCE.sub("", doc.read_text(encoding="utf-8"))
    files = repo_files()
    here = doc.parent.relative_to(ROOT)
    top = {p.split("/")[0] for p in files}
    local = {
        Path(p).relative_to(here).parts[0]
        for p in files
        if here == Path(".") or Path(p).is_relative_to(here)
    }
    in_demo = here.parts[:1] == ("demo",)
    out = []
    for target in LINK.findall(text):
        if not re.match(r"[a-z]+:|#", target):
            out.append((target.split("#")[0], doc.parent))
    for name in dict.fromkeys(TICK.findall(text)):
        if not is_path(name):
            continue
        first = name.rstrip("/").split("/")[0]
        if not in_demo or first in top or first in local:
            out.append((name, doc.parent))
    return out


def exists(name: str, base: Path, files: set[str]) -> bool:
    """The name, from the doc's folder or from the repo root, is a file or
    folder of the repo (a glob matches at least one)."""
    known = files | dirs_of(files) | {"."}
    for start in (base, ROOT):
        rel = (start / name.rstrip("/")).resolve()
        if not rel.is_relative_to(ROOT):
            continue
        rel = rel.relative_to(ROOT).as_posix()
        if any(fnmatch.fnmatch(k, rel) for k in known) if "*" in rel else rel in known:
            return True
    return False


def test_every_path_a_doc_names_exists():
    files = repo_files()
    bad, used = [], set()
    for doc in sorted(p for p in files if p.endswith(".md")):
        for name, base in named_paths(ROOT / doc):
            if exists(name, base, files):
                continue
            if name in ELSEWHERE.get(doc, {}):
                used.add((doc, name))
            else:
                bad.append(f"{doc}: {name}")
    assert not bad, "docs name paths the repo doesn't have:\n  " + "\n  ".join(bad)
    stale = [
        f"{d}: {n}" for d, ns in ELSEWHERE.items() for n in ns if (d, n) not in used
    ]
    assert not stale, "ELSEWHERE lists names its doc no longer uses:\n  " + "\n  ".join(
        stale
    )


# ── the numbers ──────────────────────────────────────────────────────────────
def number(text: str) -> int:
    return int(text.replace(",", ""))


def test_the_case_count_is_cases_jsons():
    cases = json.loads((ROOT / "vectors" / "cases.json").read_text())["cases"]
    n = sum(
        len(v) if isinstance(v, list) else sum(len(x) for x in v.values())
        for v in cases.values()
    )
    said = re.findall(r"([\d,]+) (?:test )?cases", README.read_text(encoding="utf-8"))
    row = next(
        line
        for line in (ROOT / "vectors" / "README.md").read_text().splitlines()
        if line.startswith("| `cases.json` |")
    )
    said += re.findall(r"([\d,]+) cases", row)
    assert said and all(number(s) == n for s in said), f"cases.json has {n}: {said}"


def test_the_kernels_length_is_what_the_tree_says():
    said = re.search(
        r"kernel\.py\s+the whole program \(about ([\d,]+) lines\)", README.read_text()
    )
    lines = len((ROOT / "kernel.py").read_text(encoding="utf-8").splitlines())
    assert said and number(said.group(1)) == round(lines, -1), (
        f"kernel.py is {lines} lines; the tree says about {said and said.group(1)}"
    )


def test_odiles_files_are_what_the_readme_says(tmp_path):
    """Her files are made in a copy of her folder, never in the repo's."""
    shutil.copytree(ROOT / "demo" / "odile", tmp_path / "odile")
    made = subprocess.run(
        [sys.executable, str(tmp_path / "odile" / "make_life.py")],
        capture_output=True,
        text=True,
    )
    assert made.returncode == 0, made.stderr
    life = tmp_path / "odile" / "life"
    paths = [p for p in life.rglob("*") if p.is_file()]
    sys.path.insert(0, str(ROOT))
    import kernel

    paragraphs = len(kernel.chunks(life))
    text = README.read_text(encoding="utf-8")
    m = re.search(
        r"On Odile's ([\d,]+) files \(([\d,]+) KB, about ([\d,]+)\s+paragraphs\)", text
    )
    assert m, "README.md no longer says how big Odile's folder is"
    assert number(m.group(1)) == len(paths), f"she has {len(paths)} files"
    size = sum(p.stat().st_size for p in paths)
    assert number(m.group(2)) == round(size / 1000, -1), f"her files are {size:,} bytes"
    assert number(m.group(3)) == round(paragraphs, -2), f"{paragraphs} paragraphs"
    assert f"writes her {len(paths)} files" in text
    for name in ODILE_NAMED:
        assert (life / name.rstrip("/")).exists(), (
            f"README.md names {name}; her files don't have it"
        )


def test_the_python_versions_are_the_ones_ci_runs():
    ci = (ROOT / ".github" / "workflows" / "kernel.yml").read_text()
    versions = re.findall(
        r'"(3\.\d+)"', re.search(r"python-version: \[(.*?)\]", ci).group(1)
    )
    first, last = versions[0], versions[-1]
    text = README.read_text(encoding="utf-8")
    assert f"Python {first} through {last}" in text
    assert f"tests on Python {first} to {last}" in text
    assert f"Python {first} or newer" in text
    head = (ROOT / "kernel.py").read_text(encoding="utf-8").splitlines()[0]
    assert f"Python {first}+" in head, f"kernel.py's first line: {head}"


# ── add-ons and ports ────────────────────────────────────────────────────────
def test_every_add_on_has_its_card_its_tests_and_its_row():
    table = (ROOT / "adapters" / "README.md").read_text(encoding="utf-8")
    rows = set(re.findall(r"^\| \[([^\]]+)/\]\(\1/\) \|", table, re.M))
    folders = {p.name for p in (ROOT / "adapters").iterdir() if p.is_dir()} - {
        "__pycache__"
    }
    assert rows == folders, (
        f"adapters/README.md's table: {sorted(rows)}; folders: {sorted(folders)}"
    )
    for name in folders:
        here = ROOT / "adapters" / name
        assert (here / "README.md").is_file(), f"adapters/{name} has no card"
        assert list(here.glob("test_*.py")), f"adapters/{name} has no tests"


def test_every_port_folder_is_one_compare_runs():
    compare = (ROOT / "vectors" / "compare.py").read_text(encoding="utf-8")
    run = set(
        re.findall(
            r'"(\w+)":', re.search(r"^PORTS = \{(.*?)\}", compare, re.M).group(1)
        )
    )
    folders = {p.name for p in (ROOT / "ports").iterdir() if p.is_dir()}
    assert folders == run, f"ports/: {sorted(folders)}; compare.py runs: {sorted(run)}"
