"""The docs say what the repo holds, and the repo holds what the docs say.

- FILES.md's tree lists every file in the repo, and nothing that isn't
  there; README.md's tree under "What's in this repo" lists exactly the
  repo's top level.
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
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
FILES = ROOT / "FILES.md"


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


def tree(doc: Path = FILES, heading: str = "# Every file") -> tuple[set[str], set[str]]:
    """(files, folders) a doc's tree lists, as paths from the repo root:
    FILES.md's, every file, unless the README's top level is asked for."""
    block = section(doc.read_text(encoding="utf-8"), heading)
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
        f"FILES.md's tree is out of date.\n  in the repo, not the tree: {missing}"
        f"\n  in the tree, not the repo: {extra}"
    )


def test_the_readmes_tree_is_the_repos_top_level():
    """The front page shows the top: every file and folder at the root, each
    once, and nothing deeper."""
    files, folders = tree(README, "## What's in this repo")
    actual = repo_files()
    top_files = {f for f in actual if "/" not in f}
    top_folders = {f.split("/")[0] for f in actual if "/" in f}
    assert files == top_files and folders == top_folders, (
        f"README.md's top-level tree is out of date: files {sorted(files ^ top_files)}, "
        f"folders {sorted(folders ^ top_folders)}"
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
    "docs/how-it-works.md": {
        "dad/": "in Odile's generated files (test_odiles_files_are_what_the_docs_say)",
    },
    "docs/tour.md": {
        "hives/2026.txt": "in Odile's generated files (the same test)",
        "odile-record/": "made by the first-five-minutes walkthrough",
        "odile.key": "made by the first-five-minutes walkthrough",
    },
    "adapters/stdlib/ci/README.md": {
        ".ci-record/": "made by `ci.py run`, ignored by git",
        ".ci-record.key": "made by `ci.py run`, ignored by git",
    },
    "adapters/stdlib/surprise/README.md": {
        "sha256-stream/v1": "the name of willow-bot's stream generator, not a file",
    },
    "adapters/README.md": {
        "requirements.txt": "each deps add-on's own file, in its folder",
        "requirements-floor.txt": "each deps add-on's own file, in its folder",
    },
    "CONSTITUTION.md": {
        "CASEBOOK.md": "willows-grove's: its cases name people and files, so not here",
    },
    "CONTRIBUTING.md": {
        "requirements.txt": "each deps add-on's own file, in its folder",
        "requirements-floor.txt": "each deps add-on's own file, in its folder",
    },
    "adapters/deps/README.md": {
        "requirements.txt": "each deps add-on's own file, in its folder",
        "requirements-floor.txt": "each deps add-on's own file, in its folder",
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


# ── question numbers ─────────────────────────────────────────────────────────
ITEM = re.compile(r"^(\d+)\. (.+)$", re.M)
ONE = re.compile(r"\bquestion (\d+)(?:, \"([^\"]+)\")?", re.I)
MANY = re.compile(r"\bquestions (\d+(?:, \d+)*(?:,? and \d+)?)", re.I)
#: The willow system's id families: a Q8 there names one question everywhere,
#: so a demo's own "Q8" would be read as that one (and was, cross-repo).
RESERVED = re.compile(r"(?<![A-Za-z0-9_\-])(?:OW|Q|D|F)[1-9]\d{0,2}(?![A-Za-z0-9_])")


def test_a_question_number_is_one_its_folder_asks_and_its_words_are_its_own():
    files = repo_files()
    for qs in sorted(p for p in files if p.endswith("/QUESTIONS.md")):
        here = Path(qs).parent
        asked = {
            int(n): text.strip() for n, text in ITEM.findall((ROOT / qs).read_text())
        }
        assert sorted(asked) == list(range(1, len(asked) + 1)), f"{qs} skips a number"
        for doc in sorted(
            p for p in files if p.endswith(".md") and Path(p).parent == here
        ):
            text = (ROOT / doc).read_text(encoding="utf-8")
            for n, words in ONE.findall(text):
                assert int(n) in asked, f"{doc}: question {n}; {qs} has {len(asked)}"
                if words:
                    assert words.lower() == asked[int(n)].lower(), (
                        f"{doc}: question {n} quoted as {words!r}; it asks {asked[int(n)]!r}"
                    )
            for run in MANY.findall(text):
                for n in re.findall(r"\d+", run):
                    assert int(n) in asked, (
                        f"{doc}: question {n}; {qs} has {len(asked)}"
                    )


def test_no_doc_uses_the_willow_systems_id_families():
    bad = [
        f"{doc}:{n}: {m.group(0)}"
        for doc in sorted(p for p in repo_files() if p.endswith(".md"))
        for n, line in enumerate(
            (ROOT / doc).read_text(encoding="utf-8").splitlines(), 1
        )
        for m in RESERVED.finditer(line)
    ]
    assert not bad, "OW, Q, D and F ids belong to the willow system:\n  " + "\n  ".join(
        bad
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
    lines = len((ROOT / "kernel.py").read_text(encoding="utf-8").splitlines())
    for doc in (README, FILES):
        said = re.search(
            r"kernel\.py\s+the whole program \(about ([\d,]+) lines\)", doc.read_text()
        )
        assert said and number(said.group(1)) == round(lines, -1), (
            f"kernel.py is {lines} lines; {doc.name} says about {said and said.group(1)}"
        )


def test_odiles_files_are_what_the_docs_say(tmp_path):
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
    text = "\n".join(
        (ROOT / "docs" / f).read_text(encoding="utf-8")
        for f in ("tour.md", "how-it-works.md")
    )
    m = re.search(
        r"On Odile's ([\d,]+) files \(([\d,]+) KB, about ([\d,]+)\s+paragraphs\)", text
    )
    assert m, "docs/how-it-works.md no longer says how big Odile's folder is"
    assert number(m.group(1)) == len(paths), f"she has {len(paths)} files"
    size = sum(p.stat().st_size for p in paths)
    assert number(m.group(2)) == round(size / 1000, -1), f"her files are {size:,} bytes"
    assert number(m.group(3)) == round(paragraphs, -2), f"{paragraphs} paragraphs"
    assert f"writes her {len(paths)} files" in text
    for name in ODILE_NAMED:
        assert (life / name.rstrip("/")).exists(), (
            f"the docs name {name}; her files don't have it"
        )


def test_the_readmes_contents_link_every_section_in_order():
    """The contents line at the top names each `##` section, in order, and
    links to it, so a section added or renamed can't be left out of it."""
    text = README.read_text(encoding="utf-8")
    line = next((ln for ln in text.splitlines() if ln.startswith("**Contents:** ")), "")
    links = re.findall(r"\[([^\]]+)\]\(#([^)]+)\)", line)
    heads = re.findall(r"^## (.+)$", text, re.M)
    slug = lambda h: re.sub(r"[^a-z0-9 -]", "", h.lower()).replace(" ", "-")  # noqa: E731
    assert links == [(h, slug(h)) for h in heads], (
        f"README.md's contents: {[n for n, _ in links]}; its sections: {heads}"
    )


def test_the_python_version_is_the_kernels():
    """The README names the oldest Python the kernel's own first line does.
    That CI tests it there is the host's to hold (adapters/stdlib/github)."""
    head = (ROOT / "kernel.py").read_text(encoding="utf-8").splitlines()[0]
    first = re.search(r"Python (3\.\d+)\+", head).group(1)
    text = " ".join(README.read_text(encoding="utf-8").split())  # wrapped lines
    assert f"Python {first} or newer" in text, f"kernel.py says Python {first}+"


# ── add-ons and ports ────────────────────────────────────────────────────────
def add_on_folders() -> list[Path]:
    return sorted(
        p
        for kind in ("stdlib", "deps")
        for p in (ROOT / "adapters" / kind).glob("*")
        if p.is_dir() and not p.name.startswith(("_", "."))
    )


def test_add_ons_live_only_in_stdlib_or_deps():
    loose = sorted(
        p.name
        for p in (ROOT / "adapters").iterdir()
        if p.is_dir() and p.name not in ("stdlib", "deps", "__pycache__")
    )
    assert not loose, f"adapters/ holds {loose}: an add-on goes in stdlib/ or deps/"


def test_every_add_on_has_its_card_and_its_tests():
    for here in add_on_folders():
        name = here.relative_to(ROOT)
        assert (here / "README.md").is_file(), f"{name} has no card"
        assert list(here.glob("test_*.py")), f"{name} has no tests"


PIN = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)==[A-Za-z0-9.+!-]+")


def test_every_deps_add_on_pins_what_it_needs_and_names_it_on_its_card():
    for here in add_on_folders():
        if here.parent.name != "deps":
            continue
        req = here / "requirements.txt"
        assert req.is_file(), f"{here.relative_to(ROOT)} has no requirements.txt"
        lines = [
            line.split("#")[0].strip()
            for line in req.read_text(encoding="utf-8").splitlines()
        ]
        pins = [line for line in lines if line]
        bad = [line for line in pins if not PIN.fullmatch(line)]
        assert pins and not bad, f"{req.relative_to(ROOT)}: pin each with ==: {bad}"
        head = (here / "README.md").read_text(encoding="utf-8").split("-->")[0]
        needs = re.search(r"^needs: (.*)$", head, re.M)
        assert needs, f"{here.relative_to(ROOT)}: its card's header has no needs:"
        for pin in pins:
            package = PIN.fullmatch(pin).group(1)
            assert package.lower() in needs.group(1).lower(), (
                f"{here.relative_to(ROOT)}: {package} is pinned but not on its card"
            )


def test_every_deps_add_on_has_a_floor_and_its_card_names_it():
    """The floor rule: each deps add-on is also tested at its oldest version,
    the last release of 2020 or else the first, or at a higher floor its card
    gives a reason for. ci.py's deps:floors checks the dates against PyPI."""
    for here in add_on_folders():
        if here.parent.name != "deps":
            continue
        name = here.relative_to(ROOT)
        floor = here / "requirements-floor.txt"
        assert floor.is_file(), f"{name} has no requirements-floor.txt"
        pins = {}
        for line in floor.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line:
                assert PIN.fullmatch(line), (
                    f"{floor.relative_to(ROOT)}: pin with ==: {line}"
                )
                package, version = line.split("==")
                pins[package.lower()] = version
        top = {
            line.split("==")[0].strip().lower()
            for line in (here / "requirements.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.split("#")[0].strip()
        }
        assert set(pins) == top, (
            f"{name}: the floor pins {sorted(pins)}, the top {sorted(top)}"
        )
        head = (here / "README.md").read_text(encoding="utf-8").split("-->")[0]
        line = re.search(r"^floor: (.*)$", head, re.M)
        assert line, f"{name}: its card's header has no floor:"
        for package, version in pins.items():
            assert f"{package} {version}" in line.group(1).lower(), (
                f"{name}: its floor: line doesn't name {package} {version}"
            )


def test_every_port_folder_is_one_compare_runs_and_ci_requires():
    compare = (ROOT / "vectors" / "compare.py").read_text(encoding="utf-8")
    run = set(
        re.findall(
            r'"(\w+)":', re.search(r"^PORTS = \{(.*?)\}", compare, re.M).group(1)
        )
    )
    folders = {p.name for p in (ROOT / "ports").iterdir() if p.is_dir()}
    assert folders == run, f"ports/: {sorted(folders)}; compare.py runs: {sorted(run)}"
    ci = (ROOT / "adapters" / "stdlib" / "ci" / "ci.py").read_text(encoding="utf-8")
    held = set(
        re.findall(r'"(\w+)"', re.search(r"^PORTS = \((.*?)\)", ci, re.M).group(1))
    )
    assert folders == held, (
        f"ports/: {sorted(folders)}; adapters/ci/ci.py runs: {sorted(held)}"
    )


def test_bugs_md_is_the_tests_marked_as_known_bugs():
    """BUGS.md is made from the tests marked as known bugs, and every
    expected-to-fail mark is one (strict, naming its bug)."""
    spec = importlib.util.spec_from_file_location(
        "willow_bugs", ROOT / "adapters" / "stdlib" / "ci" / "bugs.py"
    )
    bugs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bugs)
    made = bugs.render(bugs.bugs())
    assert (ROOT / "BUGS.md").read_text(encoding="utf-8") == made, (
        "BUGS.md isn't current: run python adapters/stdlib/ci/bugs.py write"
    )


def test_every_file_is_checked_out_with_lf_line_endings():
    """kernel.py hashes its own bytes into every record, so a checkout that
    turned LF into CRLF would change what every record says. .gitattributes
    forces LF on every system, and no file in the repo holds a CRLF."""
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "* text=auto eol=lf" in attrs, ".gitattributes doesn't force LF"
    crlf = sorted(f for f in repo_files() if b"\r\n" in (ROOT / f).read_bytes())
    assert not crlf, f"files with CRLF line endings: {crlf}"


RELEASE = re.compile(r"v(\d+\.\d+\.\d+) · (\d{4}-\d{2}-\d{2})")
BEFORE_RELEASES = re.compile(r"\d{4}-\d{2}-\d{2} · pull request #\d+")


def test_each_release_is_a_changelog_heading_and_the_citation_names_the_newest():
    """CHANGELOG.md's headings are `Unreleased`, then releases, newest first,
    `vX.Y.Z · YYYY-MM-DD` (the pull requests before the first release keep
    theirs). CITATION.cff names the newest release, or no version at all
    before there is one."""
    heads = re.findall(r"^## (.+)$", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)  # fmt: skip
    assert heads[0] == "Unreleased", "CHANGELOG.md opens with ## Unreleased"
    odd = [h for h in heads[1:] if not (RELEASE.fullmatch(h) or BEFORE_RELEASES.fullmatch(h))]  # fmt: skip
    assert not odd, f"CHANGELOG.md headings that aren't a release: {odd}"
    releases = [
        RELEASE.fullmatch(h).groups() for h in heads[1:] if RELEASE.fullmatch(h)
    ]
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    said = dict(re.findall(r"^(version|date-released): \"?([\w.-]+)\"?$", cff, re.M))
    newest = (
        {"version": releases[0][0], "date-released": releases[0][1]} if releases else {}
    )
    assert said == newest, (
        f"CITATION.cff says {said}; CHANGELOG.md's newest release is {newest}"
    )
