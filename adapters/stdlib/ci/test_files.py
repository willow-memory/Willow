"""files.py: FILES.md's tree kept to the repo's files. A missing file goes in
its folder's own order, with what it says of itself; a gone one comes out
with its notes; the corners and bars stay right; and on the real tree,
taking a file out and putting it back gives the line it had."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("files", HERE / "files.py")
files = importlib.util.module_from_spec(spec)
spec.loader.exec_module(files)

DOC = """# Files

Words before.

# Every file

```
willow/
├── kernel.py                 the whole program
├── README.md                 the front page
└── adapters/
    ├── stdlib/
    │   ├── alpha/
    │   │   ├── alpha.py      alpha's script
    │   │   ├── test_alpha.py
    │   │   └── README.md     its card
    │   └── gamma/
    │       ├── gamma.py      gamma's script
    │       │                 a note under gamma.py
    │       └── test_gamma.py
    └── planned.json          the ideas
```

## After

Words after.
"""
LISTED = {
    "kernel.py", "README.md", "adapters/planned.json",
    "adapters/stdlib/alpha/alpha.py", "adapters/stdlib/alpha/test_alpha.py",
    "adapters/stdlib/alpha/README.md", "adapters/stdlib/gamma/gamma.py",
    "adapters/stdlib/gamma/test_gamma.py",
}  # fmt: skip


@pytest.fixture
def scratch():
    """Scratch made with tempfile, which the guard counts as the tool's own."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "FILES.md").write_text(DOC, encoding="utf-8")
        yield root


def put(root: Path, path: str, text: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text, encoding="utf-8")


def tree_of(root: Path) -> list[str]:
    return files.Tree((root / "FILES.md").read_text(encoding="utf-8")).lines


def test_a_file_goes_in_its_folders_order_saying_what_its_docstring_says(scratch):
    put(
        scratch,
        "adapters/stdlib/alpha/beta.py",
        '"""beta.py: the second script. Python 3.9+.\n\nMore."""\n',
    )
    added, gone, ended, blank = files.write(
        scratch / "FILES.md", scratch, LISTED | {"adapters/stdlib/alpha/beta.py"}
    )
    assert (added, gone, ended, blank) == (
        ["adapters/stdlib/alpha/beta.py"],
        [],
        [],
        [],
    )
    lines = tree_of(scratch)
    at = lines.index("    │   ├── alpha/")
    assert lines[at + 1 : at + 5] == [
        "    │   │   ├── alpha.py      alpha's script",
        "    │   │   ├── beta.py       the second script",
        "    │   │   ├── test_alpha.py",
        "    │   │   └── README.md     its card",
    ]
    text = (scratch / "FILES.md").read_text(encoding="utf-8")
    assert text.startswith("# Files\n\nWords before.") and text.endswith(
        "## After\n\nWords after.\n"
    )


def test_a_new_add_on_folder_goes_between_its_neighbours_with_its_corners_right(
    scratch,
):
    new = {
        "adapters/stdlib/beta/beta.py",
        "adapters/stdlib/beta/test_beta.py",
        "adapters/stdlib/beta/README.md",
    }
    put(scratch, "adapters/stdlib/beta/README.md", "<!-- willow-addon -->\n# beta\n")
    files.write(scratch / "FILES.md", scratch, LISTED | new)
    lines = tree_of(scratch)
    at = lines.index("    ├── stdlib/")
    assert lines[at + 1 : at + 13] == [
        "    │   ├── alpha/",
        "    │   │   ├── alpha.py      alpha's script",
        "    │   │   ├── test_alpha.py",
        "    │   │   └── README.md     its card",
        "    │   ├── beta/",
        "    │   │   ├── beta.py",
        "    │   │   ├── test_beta.py",
        "    │   │   └── README.md     its card",
        "    │   └── gamma/",
        "    │       ├── gamma.py      gamma's script",
        "    │       │                 a note under gamma.py",
        "    │       └── test_gamma.py",
    ]
    assert files.Tree((scratch / "FILES.md").read_text()).files() == LISTED | new


def test_the_new_last_entry_takes_the_corner_and_the_old_last_ones_lines_get_the_bar(
    scratch,
):
    files.write(
        scratch / "FILES.md", scratch, LISTED | {"adapters/stdlib/zeta/zeta.py"}
    )
    lines = tree_of(scratch)
    at = lines.index("    │   ├── gamma/")
    assert lines[at + 1 : at + 6] == [
        "    │   │   ├── gamma.py      gamma's script",
        "    │   │   │                 a note under gamma.py",
        "    │   │   └── test_gamma.py",
        "    │   └── zeta/",
        "    │       └── zeta.py",
    ]


def test_a_gone_file_goes_with_its_notes_and_a_folder_left_empty_goes_too(scratch):
    files.write(
        scratch / "FILES.md", scratch, LISTED - {"adapters/stdlib/gamma/gamma.py"}
    )
    lines = tree_of(scratch)
    assert "a note under gamma.py" not in "\n".join(lines)
    assert "    │       └── test_gamma.py" in lines
    files.write(
        scratch / "FILES.md",
        scratch,
        LISTED
        - {"adapters/stdlib/gamma/gamma.py", "adapters/stdlib/gamma/test_gamma.py"},
    )
    lines = tree_of(scratch)
    assert not any("gamma" in line for line in lines)
    assert (
        "    │   └── alpha/" in lines
        and "    │       └── README.md     its card" in lines
    )


def test_a_folder_in_an_order_of_its_own_gets_it_at_its_end_and_says_so(scratch):
    put(scratch, "zz.md", "# Zed\n")
    added, _, ended, blank = files.write(
        scratch / "FILES.md", scratch, LISTED | {"zz.md", "aa.json"}
    )
    assert ended == ["aa.json", "zz.md"] and blank == ["aa.json"]
    lines = tree_of(scratch)
    assert lines[1:5] == [
        "├── kernel.py                 the whole program",
        "├── README.md                 the front page",
        "├── adapters/",
        "│   ├── stdlib/",
    ]
    assert lines[-3:] == [
        "│   └── planned.json          the ideas",
        "├── aa.json",
        "└── zz.md                     Zed",
    ]


def test_what_a_file_says_of_itself(scratch):
    put(scratch, "adapters/stdlib/x/x.py", '"""x.py: the x thing. Python 3.9+."""\n')
    put(scratch, "adapters/stdlib/x/README.md", "# x\n")
    put(scratch, "docs/a.md", "intro\n\n# A Title\n")
    put(scratch, "plain.py", "print(1)\n")
    put(scratch, "broken.py", "def (\n")
    assert files.describe(scratch, "adapters/stdlib/x/x.py") == "the x thing"
    assert files.describe(scratch, "adapters/stdlib/x/README.md") == "its card"
    assert files.describe(scratch, "docs/a.md") == "A Title"
    assert files.describe(scratch, "adapters/stdlib/x/test_x.py") == ""
    assert (
        files.describe(scratch, "plain.py")
        == files.describe(scratch, "broken.py")
        == ""
    )
    assert files.describe(scratch, "not-there.txt") == ""


def test_nothing_to_do_writes_nothing(scratch):
    before = (scratch / "FILES.md").stat().st_mtime_ns
    assert files.write(scratch / "FILES.md", scratch, LISTED) == ([], [], [], [])
    assert (scratch / "FILES.md").stat().st_mtime_ns == before


@pytest.mark.parametrize("argv", [[], ["writ"], ["check", "more"]])
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "files.py"), *argv], capture_output=True, text=True
    )
    assert got.returncode == 2 and "files.py" in got.stderr


def test_on_the_real_tree_a_file_taken_out_and_put_back_gets_its_line_back():
    """Every tenth file in a folder kept A to Z: same place, same bars."""
    text = (files.ROOT / "FILES.md").read_text(encoding="utf-8")
    base = files.Tree(text)
    tried = 0
    for i, depth, path, is_folder in base.entries()[::10]:
        folder = path.rsplit("/", 1)[0] if "/" in path else ""
        d, kids = base.children(folder)
        names = [base.lines[k][4 * d + 4 :].split()[0] for k, *_ in kids]
        body = [n for n in names if n != "README.md"]
        if (
            is_folder
            or path.endswith("README.md")
            or body != sorted(body, key=lambda n: (n.startswith("test_"), n.lower()))
        ):
            continue
        t = files.Tree(text)
        t.remove(path)
        said = files.ENTRY.match(base.lines[i]).group(4) or ""
        t.insert(folder, path.rsplit("/", 1)[-1], said)
        assert (
            t.lines[:i] == base.lines[:i] and t.lines[i + 1 :] == base.lines[i + 1 :]
        ), path
        assert t.lines[i].split() == base.lines[i].split(), path
        tried += 1
    assert tried > 50


def test_folders_sort_without_their_slash_and_one_slip_by_hand_keeps_a_folder_a_to_z(
    scratch,
):
    """almanac/ before almanac-keep/, as the tree has them; and a folder with
    one pair out of turn among many is still A to Z, not an order of its own."""
    names = [
        "almanac",
        "almanac-keep",
        "deep-links",
        "decisions",
        *(
            f"m{k:02}" for k in range(16)
        ),  # 20 folders, one slip: a slip by hand, as stdlib had 3 in 311
        "nestor",
        "pdf",
        "zotero",
    ]
    tree = "# Every file\n\n```\nwillow/\n└── stdlib/\n"
    for k, n in enumerate(names):
        tree += f"    {'└' if k == len(names) - 1 else '├'}── {n}/\n"
        tree += f"    {' ' if k == len(names) - 1 else '│'}   └── {n}.py\n"
    (scratch / "FILES.md").write_text(tree + "```\n", encoding="utf-8")
    listed = {f"stdlib/{n}/{n}.py" for n in names}
    _, _, ended, _ = files.write(
        scratch / "FILES.md", scratch, listed | {"stdlib/anki/anki.py"}
    )
    lines = tree_of(scratch)
    assert ended == []
    assert (
        lines.index("    ├── anki/") == lines.index("    │   └── almanac-keep.py") + 1
    )
    # a folder in an order of its own: the new folder at its end, and said
    small = (
        "# Every file\n\n```\nwillow/\n└── stdlib/\n    ├── b/\n    │   └── b.py\n"
        "    └── a/\n        └── a.py\n```\n"
    )
    (scratch / "FILES.md").write_text(small, encoding="utf-8")
    listed = {"stdlib/a/a.py", "stdlib/b/b.py", "stdlib/c/c.py"}
    _, _, ended, _ = files.write(scratch / "FILES.md", scratch, listed)
    assert ended == ["stdlib/c/"]
    assert tree_of(scratch)[-2:] == ["    └── c/", "        └── c.py"]
