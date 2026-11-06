"""new.py: an add-on started from its idea. Its card's header is the idea's
entry, its script keeps the command-line contract from the start, the idea
leaves the list as the list is always written, FILES.md has it, and what's
left for a person is said. A name that isn't an idea, or a folder already
there, changes nothing."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("new", HERE / "new.py")
new = importlib.util.module_from_spec(spec)
spec.loader.exec_module(new)

IDEAS = [
    {"name": "anki-deck", "kind": "stdlib", "section": "Ways to use it",
     "line": "Approved answers as an Anki deck.", "source": "new",
     "writes": "to", "network": "none", "role": "makes", "tags": "cards"},
    {"name": "pdf-forms", "kind": "deps", "section": "Reading more kinds of files",
     "line": "Filled PDF forms as text.", "source": "new", "needs": "pypdf; BSD-3-Clause",
     "writes": "to", "network": "none", "role": "reads"},
    {"name": "zebra", "kind": "stdlib", "section": "Play", "line": "Stripes.",
     "source": "new", "writes": "nothing", "network": "none", "role": "tools"},
]  # fmt: skip
TREE = """# Every file

```
willow/
├── kernel.py                 the whole program
├── FILES.md                  every file
├── .gitignore                what git leaves out
└── adapters/
    ├── planned.json          the ideas
    ├── stdlib/
    │   └── ci/
    │       └── files.py      FILES.md's tree
    └── deps/
        └── pdf/
            └── pdf.py        pdfs
```
"""


@pytest.fixture
def repo():
    """A repo of its own, in scratch made with tempfile, as git sees it."""
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        shutil.copy(ROOT / "kernel.py", r / "kernel.py")
        (r / "adapters/stdlib/ci").mkdir(parents=True)
        (r / "adapters/deps/pdf").mkdir(parents=True)
        shutil.copy(HERE / "files.py", r / "adapters/stdlib/ci/files.py")
        (r / "adapters/deps/pdf/pdf.py").write_text('"""pdf.py: pdfs."""\n')
        (r / "adapters/planned.json").write_text(json.dumps(IDEAS, indent=1) + "\n")
        (r / "FILES.md").write_text(TREE)
        (r / ".gitignore").write_text("__pycache__/\n")
        subprocess.run(["git", "init", "-q", str(r)], check=True)
        yield r


def make(repo: Path, name: str):
    ran = []
    got = new.make(repo, name, "2026-11-04", regenerate=ran.append)
    assert ran == [repo], "the add-on list is written after"
    return got


def test_an_idea_becomes_a_folder_whose_card_is_its_entry(repo):
    made, left = make(repo, "anki-deck")
    assert made == ["adapters/stdlib/anki-deck/README.md", "adapters/stdlib/anki-deck/anki_deck.py",
                    "adapters/stdlib/anki-deck/test_anki_deck.py"]  # fmt: skip
    card = (repo / "adapters/stdlib/anki-deck/README.md").read_text()
    assert card.startswith(
        "<!-- willow-addon\nsection: Ways to use it\nline: Approved answers as an Anki deck.\n"
        "source: new\nadded: 2026-11-04\nwrites: to\nnetwork: none\nrole: makes\ntags: cards\n-->\n# anki-deck\n"
    )
    assert any("COMMANDS" in item for item in left) and any(
        "changelog fragment" in item for item in left
    )
    assert not any("requirements" in item for item in left), (
        "a stdlib idea installs nothing"
    )


def test_its_script_refuses_every_command_line_naming_itself_and_its_test_says_so(repo):
    make(repo, "anki-deck")
    folder = repo / "adapters/stdlib/anki-deck"
    for argv in ([], ["--box", "x"]):
        got = subprocess.run(
            [sys.executable, str(folder / "anki_deck.py"), *argv],
            capture_output=True,
            text=True,
        )
        assert got.returncode == 2 and "anki_deck.py" in got.stderr
    ran = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(folder)],
                         capture_output=True, text=True)  # fmt: skip
    assert ran.returncode == 0, ran.stdout


def test_the_idea_leaves_the_list_written_as_the_list_always_is(repo):
    make(repo, "anki-deck")
    text = (repo / "adapters/planned.json").read_text()
    assert text == json.dumps(IDEAS[1:], indent=1, ensure_ascii=False) + "\n"


def test_files_md_lists_the_new_folder_in_its_place(repo):
    make(repo, "anki-deck")
    lines = (repo / "FILES.md").read_text().splitlines()
    at = lines.index("    ├── stdlib/")
    assert lines[at + 1 : at + 7] == [
        "    │   ├── anki-deck/",
        "    │   │   ├── anki_deck.py  Approved answers as an Anki deck",
        "    │   │   ├── test_anki_deck.py",
        "    │   │   └── README.md     its card",
        "    │   └── ci/",
        "    │       └── files.py      FILES.md's tree",
    ]
    files = new._files_mod(repo)
    assert files.Tree((repo / "FILES.md").read_text()).files() == files.repo_files(repo)


def test_a_deps_idea_also_owes_its_requirements(repo):
    made, left = make(repo, "pdf-forms")
    assert made[0] == "adapters/deps/pdf-forms/README.md"
    assert any("requirements.txt" in item and "floor" in item for item in left)
    assert "needs: pypdf; BSD-3-Clause\n" in (repo / made[0]).read_text()


@pytest.mark.parametrize("name", ["not-an-idea", "zebra"])
def test_no_idea_or_a_folder_already_there_is_refused_and_nothing_moves(repo, name):
    if name == "zebra":
        (repo / "adapters/stdlib/zebra").mkdir()
    before = {
        p: p.read_bytes()
        for p in repo.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }
    with pytest.raises(new.Refused):
        new.make(repo, name, "2026-11-04", regenerate=lambda r: None)
    after = {
        p: p.read_bytes()
        for p in repo.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }
    assert after == before


@pytest.mark.parametrize(
    "argv", [[], ["a", "b"], ["--added"], ["x", "--added", "soon"], ["-x"]]
)
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "new.py"), *argv], capture_output=True, text=True
    )
    assert got.returncode == 2 and "new.py" in got.stderr
