"""order.py: the lists people add to, A to Z. A table's entries move with
the comments above them and nothing else changes; planned.json is written
as it always is; a FILES.md folder with a slip comes back in order and one
in an order of its own is left; what can't be taken apart is refused; and
the repo's own lists are A to Z."""

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
spec = importlib.util.spec_from_file_location("order", HERE / "order.py")
order = importlib.util.module_from_spec(spec)
spec.loader.exec_module(order)

TABLE = '''"""a module"""

NOW = ["--now", "x"]

#: by name
COMMANDS: dict[str, tuple[str, list[str]]] = {
    "zed": ("zed.py", ["--box", "{box}"]),
    # beta's port is closed: it answers before any fetch
    "beta": ("beta.py", ["--url",
             "http://127.0.0.1:9/"]),
    "alpha": ("alpha.py", [*NOW]),  # its own note
    **{n: (n + ".py", []) for n in ("x", "y")},
}  # fmt: skip

AFTER = 1
'''
SORTED = '''"""a module"""

NOW = ["--now", "x"]

#: by name
COMMANDS: dict[str, tuple[str, list[str]]] = {
    "alpha": ("alpha.py", [*NOW]),  # its own note
    # beta's port is closed: it answers before any fetch
    "beta": ("beta.py", ["--url",
             "http://127.0.0.1:9/"]),
    "zed": ("zed.py", ["--box", "{box}"]),
    **{n: (n + ".py", []) for n in ("x", "y")},
}  # fmt: skip

AFTER = 1
'''


def test_a_table_goes_a_to_z_each_entry_with_its_comment_its_spread_at_the_end():
    got = order.sort_table(TABLE, "COMMANDS")
    assert got.splitlines()[:10] == SORTED.splitlines()[:10]
    assert got.splitlines()[-5:] == SORTED.splitlines()[-5:]
    assert order.sort_table(got, "COMMANDS") == got


def test_a_sorted_table_is_the_same_dict_and_the_same_lines():
    src = TABLE
    got = order.sort_table(src, "COMMANDS")

    def value(s):
        ns = {}
        exec(s, ns)
        return ns["COMMANDS"]

    assert value(got) == value(src) and list(value(got))[:3] == ["alpha", "beta", "zed"]
    assert sorted(got.splitlines()) == sorted(src.splitlines())


@pytest.mark.parametrize(
    "src, why",
    [
        ('T = {\n    "b": 1, "a": 2,\n}\n', "shares a line"),
        ('T = {\n    "b": 1,\n    **X,\n    "a": 2,\n}\n', "spread in the middle"),
        ('T = {\n    "b": 1,\n    "a": 2,\n    "b": 3,\n}\n', "twice"),
        ('T = {\n    "b": 1,\n    2: 2,\n}\n', "isn't a string"),
        ('T = {\n    "b": 1\n    ,\n    "a": 2,\n}\n', "comma on a line"),
        ("T = [1]\n", "isn't a table"),
    ],
)
def test_what_cant_be_taken_apart_line_by_line_is_refused(src, why):
    with pytest.raises(order.Refused, match=why):
        order.sort_table(src, "T")


@pytest.fixture
def repo():
    """The three kinds of list, in scratch made with tempfile."""
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        (r / "adapters/stdlib/ci").mkdir(parents=True)
        shutil.copy(HERE / "files.py", r / "adapters/stdlib/ci/files.py")
        shutil.copy(HERE.parents[2] / "kernel.py", r / "kernel.py")
        (r / order.CONTRACT).write_text(
            TABLE.replace("COMMANDS", "READERS")
            + "PILE_EXTRA = {}\nCOMMANDS = {}\nREPORT_COMMANDS = {}\n"
        )
        ideas = [{"name": "b", "kind": "stdlib"}, {"name": "a", "line": "é"}]
        (r / order.PLANNED).write_text(json.dumps(ideas, indent=1) + "\n")
        folders = ["alpha", "beta", "delta", "charlie", *(f"m{k}" for k in range(7))]
        tree = "# Every file\n\n```\nwillow/\n├── b.md\n├── a.md\n└── stdlib/\n"
        for k, n in enumerate(folders):
            corner, bar = ("└", " ") if k == len(folders) - 1 else ("├", "│")
            tree += f"    {corner}── {n}/\n    {bar}   └── {n}.py   {n}'s\n"
        (r / "FILES.md").write_text(tree + "```\n")
        yield r


def test_check_names_each_list_and_write_puts_each_in_order(repo):
    tree = (repo / "FILES.md").read_text()
    assert order.run(repo, write=False) == [
        f"{order.CONTRACT}: READERS",
        order.PLANNED,
        "FILES.md: stdlib/",
    ]
    assert (repo / "FILES.md").read_text() == tree, "check writes nothing"
    order.run(repo, write=True)
    assert order.run(repo, write=False) == []
    assert (repo / order.PLANNED).read_text() == json.dumps(
        [{"name": "a", "line": "é"}, {"name": "b", "kind": "stdlib"}],
        indent=1,
        ensure_ascii=False,
    ) + "\n"
    lines = (repo / "FILES.md").read_text().splitlines()
    assert lines[4:6] == ["├── b.md", "├── a.md"], "an order of its own stays"
    at = lines.index("    ├── charlie/")
    assert lines[at - 2 : at + 4] == [
        "    ├── beta/",
        "    │   └── beta.py   beta's",
        "    ├── charlie/",
        "    │   └── charlie.py   charlie's",
        "    ├── delta/",
        "    │   └── delta.py   delta's",
    ]
    assert lines[-3:] == ["    └── m6/", "        └── m6.py   m6's", "```"]


def test_the_repos_own_lists_are_a_to_z():
    assert order.run(order.ROOT, write=False) == [], (
        "python adapters/stdlib/ci/order.py write"
    )


@pytest.mark.parametrize("argv", [[], ["writ"], ["check", "more"]])
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = subprocess.run(
        [sys.executable, str(HERE / "order.py"), *argv], capture_output=True, text=True
    )
    assert got.returncode == 2 and "order.py" in got.stderr
