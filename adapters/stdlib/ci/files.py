"""files.py: FILES.md's tree kept to the repo's files, by a script. Python 3.9+.

    python adapters/stdlib/ci/files.py check
    python adapters/stdlib/ci/files.py write

`test_docs.py` fails when FILES.md's tree and the repo disagree. `check`
says how (the files the tree doesn't list, and the ones it lists that are
gone); `write` puts each missing file in its folder, with any folder above
it the tree lacks, and takes out each gone one with the notes under it and
any folder left empty. Nothing else in the file moves.

Where a new line goes: a folder whose entries are in A-to-Z order (tests
after the code, in some) gets it in that order, its README.md kept last. A
folder kept in an order of its own (the top level, ci/) gets it at its end,
before README.md, and write says so, for a person to move it if it reads
better elsewhere.

What it says of the file: a `.py` file's docstring's first line (less its
own `name.py:`), a Markdown file's title, `its card` for an add-on's
README.md, and nothing for a test or a folder, as the tree already does. A
file it can't describe goes in with nothing, and write names it, for a
person to describe.

Exit codes, the kernel's: 0 the tree is the repo's (write: it is now); 2
check: it isn't, or refused.
"""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

DOC = ROOT / "FILES.md"
HEADING = "# Every file"
ENTRY = re.compile(r"^((?:│   |    )*)(├── |└── )(\S+)(?:\s+(.*))?$")
COLUMN = 30
USAGE = "usage: files.py check | files.py write"


def repo_files(root: Path = ROOT) -> set[str]:
    """Every file git would count, as test_docs.py counts them."""
    git = shutil.which("git")
    if git is None or not (root / ".git").exists():
        raise SystemExit(
            "refused: FILES.md is held to git's list of files: run it in a clone"
        )
    out = subprocess.run(
        [git, "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    return {p for p in out.splitlines() if (root / p).is_file()}


# ── the tree ─────────────────────────────────────────────────────────────────
class Tree:
    """FILES.md's tree, as lines: entries with their depth and path, and the
    note lines under them, kept as they are."""

    def __init__(self, text: str):
        start = text.index(HEADING)
        self.open = text.index("```\n", start) + 4
        self.close = text.index("```", self.open)
        self.head, self.tail = text[: self.open], text[self.close :]
        self.lines = text[self.open : self.close].rstrip("\n").split("\n")
        if self.lines[0] != "willow/":
            raise ValueError("FILES.md's tree starts at willow/")

    def text(self) -> str:
        return self.head + "\n".join(self.lines) + "\n" + self.tail

    def entries(self) -> list[tuple[int, int, str, bool]]:
        """(line index, depth, path, is a folder), in order."""
        out, stack = [], []
        for i, line in enumerate(self.lines[1:], 1):
            m = ENTRY.match(line)
            if m is None:
                continue
            depth, name = len(m.group(1)) // 4, m.group(3)
            stack = stack[:depth]
            path = "/".join([*stack, name.rstrip("/")])
            out.append((i, depth, path, name.endswith("/")))
            if name.endswith("/"):
                stack.append(name.rstrip("/"))
        return out

    def files(self) -> set[str]:
        return {p for _, _, p, folder in self.entries() if not folder}

    def folders(self) -> set[str]:
        return {p for _, _, p, folder in self.entries() if folder}

    def span(self, index: int, depth: int) -> int:
        """The line after an entry's own lines: its notes, and everything
        under it when it's a folder."""
        j = index + 1
        while j < len(self.lines):
            m = ENTRY.match(self.lines[j])
            if m and len(m.group(1)) // 4 <= depth:
                break
            j += 1
        return j

    def children(self, folder: str) -> tuple[int, list[tuple[int, int, str, bool]]]:
        """(the folder's depth + 1, its entries) for '' (the top) or a path."""
        if folder == "":
            return 0, [e for e in self.entries() if e[1] == 0]
        entries = self.entries()
        for k, (i, depth, path, is_folder) in enumerate(entries):
            if path == folder and is_folder:
                end = self.span(i, depth)
                return depth + 1, [
                    e for e in entries[k + 1 :] if e[0] < end and e[1] == depth + 1
                ]
        raise KeyError(folder)

    def _set_corner(self, index: int, depth: int, last: bool) -> None:
        """Make an entry the last of its folder, or not, with its lines below."""
        line = self.lines[index]
        at = 4 * depth
        self.lines[index] = line[:at] + ("└── " if last else "├── ") + line[at + 4 :]
        bar = "    " if last else "│   "
        for j in range(index + 1, self.span(index, depth)):
            if len(self.lines[j]) >= at + 4 and self.lines[j][at : at + 4] in (
                "│   ",
                "    ",
            ):
                self.lines[j] = self.lines[j][:at] + bar + self.lines[j][at + 4 :]

    def _prefix(self, folder: str, depth: int) -> str:
        """The bars in front of an entry at `depth` under `folder`."""
        if depth == 0:
            return ""
        for i, d, path, is_folder in self.entries():
            if path == folder and is_folder:
                line = self.lines[i]
                return line[: 4 * d] + (
                    "    " if line[4 * d : 4 * d + 4] == "└── " else "│   "
                )
        raise KeyError(folder)

    def insert(self, folder: str, name: str, said: str) -> bool:
        """`name` into `folder`, where its order puts it; True when that is
        the folder's end because it keeps an order of its own."""
        depth, kids = self.children(folder)
        names = [self.lines[i][4 * depth + 4 :].split()[0] for i, *_ in kids]
        body = [n for n in names if n != "README.md"]

        # A folder's name sorts without its slash (almanac/ before
        # almanac-keep/). Tests after the code first: every A-to-Z folder in
        # the tree keeps it too, and a folder down to one file fits both. A
        # folder is A to Z with at most one pair in twenty out of turn, a
        # slip by hand (deep-links/ before decisions/ in stdlib), and kept
        # in an order of its own past that.
        def plain(n: str) -> str:
            return n.rstrip("/").lower()

        def tests_after(n: str) -> tuple[bool, str]:
            return (n.startswith("test_"), plain(n))

        def slips(k) -> int:
            return sum(k(a) > k(b) for a, b in zip(body, body[1:]))

        best = min((tests_after, plain), key=slips)
        key = best if slips(best) * 20 <= len(body) else None
        own_order = key is None and len(body) > 1
        # positions are in `names`, README.md and all: the end is before a
        # README.md that closes the folder, after one that opens it
        end = len(names) - 1 if names and names[-1] == "README.md" else len(names)
        later = [
            k
            for k, n in enumerate(names)
            if n != "README.md" and key is not None and key(n) > key(name)
        ]
        at = len(names) if name == "README.md" else (later[0] if later else end)
        prefix = self._prefix(folder, depth)
        line = prefix + "├── " + name
        if said:
            line = line.ljust(COLUMN) if len(line) < COLUMN - 1 else line + " "
            line += said
        if at < len(kids):
            self.lines.insert(kids[at][0], line.rstrip())
        else:
            if kids:
                last_index, last_depth = kids[-1][0], kids[-1][1]
                end = self.span(last_index, last_depth)
                self._set_corner(last_index, last_depth, last=False)
            else:
                end = (
                    self.span(*self._folder_line(folder)) if folder else len(self.lines)
                )
            self.lines.insert(end, line.rstrip())
            self._set_corner(end, depth, last=True)
        return own_order and name != "README.md"

    def _folder_line(self, folder: str) -> tuple[int, int]:
        for i, d, path, is_folder in self.entries():
            if path == folder and is_folder:
                return i, d
        raise KeyError(folder)

    def remove(self, path: str) -> None:
        """An entry, with its notes and anything under it."""
        for i, depth, p, _ in self.entries():
            if p == path:
                break
        else:
            raise KeyError(path)
        was_last = self.lines[i][4 * depth : 4 * depth + 4] == "└── "
        del self.lines[i : self.span(i, depth)]
        if was_last:
            folder = path.rsplit("/", 1)[0] if "/" in path else ""
            _, kids = self.children(folder)
            if kids:
                self._set_corner(kids[-1][0], kids[-1][1], last=True)


# ── what a file is ───────────────────────────────────────────────────────────
def describe(root: Path, path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if name.startswith("test_") or name == "conftest.py":
        return ""
    if name == "README.md" and re.match(
        r"adapters/(stdlib|deps)/[^/]+/README\.md$", path
    ):
        return "its card"
    file = root / path
    try:
        text = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    if name.endswith(".py"):
        try:
            doc = ast.get_docstring(ast.parse(text)) or ""
        except SyntaxError:
            return ""
        first = doc.strip().split("\n", 1)[0].strip()
        first = re.sub(rf"^{re.escape(name)}:\s*", "", first)
        first = re.sub(r"\s*Python 3\.\d+\+\.?$", "", first)
        return first.rstrip(".")
    if name.endswith(".md"):
        m = re.search(r"^# (.+)$", text, re.M)
        return m.group(1).strip() if m else ""
    return ""


# ── check and write ──────────────────────────────────────────────────────────
def differ(tree: Tree, files: set[str]) -> tuple[list[str], list[str]]:
    listed = tree.files()
    return sorted(files - listed), sorted(listed - files)


def write(
    doc: Path, root: Path, files: set[str]
) -> tuple[list[str], list[str], list[str], list[str]]:
    """(added, removed, put at a folder's end, added with no description)."""
    tree = Tree(doc.read_text(encoding="utf-8"))
    missing, gone = differ(tree, files)
    ended, blank = [], []
    for path in gone:
        tree.remove(path)
        folder = path.rsplit("/", 1)[0] if "/" in path else ""
        while folder and not any(f.startswith(folder + "/") for f in files):
            if folder in tree.folders():
                tree.remove(folder)
            folder = folder.rsplit("/", 1)[0] if "/" in folder else ""
    for path in missing:
        parts = path.split("/")
        for depth in range(1, len(parts)):
            folder = "/".join(parts[:depth])
            if folder not in tree.folders():
                if tree.insert(
                    "/".join(parts[: depth - 1]), parts[depth - 1] + "/", ""
                ):
                    ended.append(folder + "/")
        said = describe(root, path)
        if tree.insert("/".join(parts[:-1]), parts[-1], said):
            ended.append(path)
        if (
            not said
            and not parts[-1].startswith("test_")
            and parts[-1] != "conftest.py"
        ):
            blank.append(path)
    if missing or gone:
        doc.write_text(tree.text(), encoding="utf-8")
    return missing, gone, ended, blank


def main(argv: list[str]) -> int:
    if argv not in (["check"], ["write"]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    files = repo_files()
    if argv == ["check"]:
        missing, gone = differ(Tree(DOC.read_text(encoding="utf-8")), files)
        for p in missing:
            print(f"not in the tree: {p}")
        for p in gone:
            print(f"in the tree, not the repo: {p}")
        if missing or gone:
            print("FILES.md is out of date: python adapters/stdlib/ci/files.py write")
            return kernel.REFUSED
        print("FILES.md is the repo's")
        return kernel.ALIVE
    missing, gone, ended, blank = write(DOC, ROOT, files)
    for p in missing:
        print(f"added: {p}")
    for p in gone:
        print(f"removed: {p}")
    for p in ended:
        print(
            f"at the end of a folder kept in its own order, for a person to move: {p}"
        )
    for p in blank:
        print(f"no description found, for a person to write: {p}")
    print("FILES.md is the repo's" + (" now" if missing or gone else ""))
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
