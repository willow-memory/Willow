"""package_contents.py: what's inside a wheel, sdist, npm tarball or .crate
before you install it. Python 3.9+.

    python adapters/stdlib/package-contents/package_contents.py --from FILE-OR-FOLDER
    python adapters/stdlib/package-contents/package_contents.py --box DIR

Each package file is opened and its members listed, every one, with its size:
nothing is unpacked, run, fetched or written. Then the code that would run
because you installed it, each cited by the file and line that makes it run:

    evil-1.0-py3-none-any.whl   wheel, 3 files
        evil/__init__.py                  12 B
        evil-1.0.dist-info/METADATA      204 B
        evil.pth                          38 B
      runs on install:
        evil.pth:1   import: the line runs at every Python start

A wheel runs nothing while it is installed, but a `.pth` line that starts
with `import` runs every time Python starts. An sdist is built first: its
setup.py, and the build backend its pyproject.toml names, run. An npm tarball
runs its preinstall, install and postinstall scripts, and a binding.gyp with
no install script makes npm run node-gyp. A crate's build.rs runs when it is
compiled, and so does a procedural macro. A path that is absolute or climbs out
with `..` is flagged too: an unpacker that trusts it writes outside its folder.

Exit codes, the kernel's: 0 nothing would run (or no package file); 42 code
would run, or a path escapes, and waits on you; 2 refused.
"""

from __future__ import annotations

import io
import json
import re
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

SUFFIXES = (".whl", ".zip", ".tar.gz", ".tgz", ".tar", ".crate")
READ_CAP = 1 << 20  # a file is read for the checks up to this many bytes
HOOKS = ("preinstall", "install", "postinstall")


def size_of(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    return f"{n / 1024:.1f} KB" if n < 1 << 20 else f"{n / (1 << 20):.1f} MB"


def line_of(text: str, pattern: str, after: int = 0) -> int:
    """The line a regex first matches at or after an offset; 1 if it doesn't."""
    m = re.compile(pattern, re.M).search(text, after)
    return text.count("\n", 0, m.start()) + 1 if m else 1


class Package:
    """One archive, opened for reading only: names, sizes, and capped reads."""

    def __init__(self, path: Path):
        self.path = path
        self.entries: list[tuple[str, int, str]] = []  # (name, size, kind)
        self._read = lambda name: b""
        if path.name.lower().endswith((".whl", ".zip")):
            z = zipfile.ZipFile(path)
            for i in z.infolist():
                kind = "dir" if i.is_dir() else "file"
                self.entries.append((i.filename, i.file_size, kind))
            self._read = lambda name: z.open(name).read(READ_CAP)
        else:
            t = tarfile.open(path)
            members = {}
            for m in t.getmembers():
                kind = "dir" if m.isdir() else "file" if m.isfile() else "link"
                self.entries.append((m.name, m.size, kind))
                members[m.name] = m
            self._read = lambda name: (
                t.extractfile(members[name]) or io.BytesIO()
            ).read(READ_CAP)

    def text(self, name: str) -> str:
        return self._read(name).decode("utf-8", errors="replace")

    def at_root(self, base: str) -> str | None:
        """A file named base at the top, or one folder down (an sdist, npm
        tarball or crate keeps everything under one folder)."""
        for name, _, kind in self.entries:
            parts = PurePosixPath(name).parts
            if kind == "file" and parts[-1:] == (base,) and len(parts) <= 2:
                return name
        return None


def kind_of(pkg: Package) -> str:
    name = pkg.path.name.lower()
    if name.endswith(".whl"):
        return "wheel"
    if name.endswith(".crate") or pkg.at_root("Cargo.toml"):
        return "crate"
    if pkg.at_root("package.json"):
        return "npm tarball"
    if (
        pkg.at_root("PKG-INFO")
        or pkg.at_root("setup.py")
        or pkg.at_root("pyproject.toml")
    ):
        return "sdist"
    return "archive"


def runs(pkg: Package, kind: str) -> list[tuple[str, int, str]]:
    """(file, line, why) for each piece of code that runs because of the install."""
    out: list[tuple[str, int, str]] = []
    if kind == "wheel":
        for name, _, k in pkg.entries:
            if k == "file" and name.lower().endswith(".pth"):
                for n, line in enumerate(pkg.text(name).splitlines(), 1):
                    if re.match(r"import[ \t]", line):
                        out.append(
                            (name, n, "import: the line runs at every Python start")
                        )
    elif kind == "sdist":
        if setup := pkg.at_root("setup.py"):
            out.append((setup, 1, "setup.py: pip runs it to build the package"))
        if proj := pkg.at_root("pyproject.toml"):
            text = pkg.text(proj)
            if m := re.search(r"^\s*build-backend\s*=\s*(.+)$", text, re.M):
                where = (
                    "in-tree backend"
                    if re.search(r"^\s*backend-path\s*=", text, re.M)
                    else "build backend"
                )
                out.append(
                    (
                        proj,
                        line_of(text, r"^\s*build-backend\s*="),
                        f"{where} {m.group(1).strip()}: pip runs it to build",
                    )
                )
    elif kind == "npm tarball":
        pj = pkg.at_root("package.json")
        text = pkg.text(pj)
        try:
            scripts = json.loads(text).get("scripts")
        except (ValueError, AttributeError):
            scripts = None
        if isinstance(scripts, dict):
            start = re.search(r'"scripts"\s*:', text)
            for hook in HOOKS:
                if hook in scripts:
                    cmd = str(scripts[hook]).replace("\n", "\\n")
                    out.append(
                        (
                            pj,
                            line_of(
                                text, rf'"{hook}"\s*:', start.end() if start else 0
                            ),
                            f"{hook}: {cmd}",
                        )
                    )
        gyp = pkg.at_root("binding.gyp")
        if gyp and not (isinstance(scripts, dict) and "install" in scripts):
            out.append(
                (
                    gyp,
                    1,
                    "binding.gyp with no install script: npm runs node-gyp rebuild",
                )
            )
    elif kind == "crate":
        cargo = pkg.at_root("Cargo.toml")
        text = pkg.text(cargo) if cargo else ""
        base = str(PurePosixPath(cargo).parent) if cargo else "."
        explicit = re.search(r'^build\s*=\s*"([^"]+)"', text, re.M)
        script = explicit.group(1) if explicit else "build.rs"
        found = pkg.at_root(script) if "/" not in script else None
        found = found or next(
            (
                n
                for n, _, k in pkg.entries
                if k == "file" and n == str(PurePosixPath(base) / script)
            ),
            None,
        )
        if found:
            out.append(
                (found, 1, "build script: cargo compiles and runs it before the crate")
            )
        if re.search(r"^proc-macro\s*=\s*true", text, re.M):
            out.append(
                (
                    cargo,
                    line_of(text, r"^proc-macro\s*=\s*true"),
                    "procedural macro: cargo runs it inside the compiler",
                )
            )
    return out


def escapes(pkg: Package) -> list[str]:
    """Members whose path is absolute or climbs out with `..`."""
    return [
        name for name, _, _ in pkg.entries
        if name.startswith(("/", "\\")) or ".." in re.split(r"[\\/]", name) or re.match(r"[A-Za-z]:", name)
    ]  # fmt: skip


def find(folder: Path) -> list[Path]:
    if folder.is_file():
        return [folder]
    return sorted(
        p
        for p in folder.rglob("*")
        if p.is_file() and p.name.lower().endswith(SUFFIXES)
    )


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if args or len([v for v in opts.values() if v]) != 1 or len(opts) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if "--box" in opts:
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        source = Path(kernel.config(box)["pile"])
    else:
        source = Path(opts["--from"])
        if not source.exists():
            print(f"refused: {source} doesn't exist", file=sys.stderr)
            return kernel.REFUSED
    paths = find(source)
    shown, flagged = 0, 0
    for path in paths:
        try:
            pkg = Package(path)
        except (OSError, tarfile.TarError, zipfile.BadZipFile, EOFError):
            print(
                f"note: {path.name} couldn't be opened as a package, so it was not checked",
                file=sys.stderr,
            )
            continue
        shown += 1
        kind = kind_of(pkg)
        files = [e for e in pkg.entries if e[2] != "dir"]
        print(
            f"{path.name}   {kind}, {len(files)} file{'s' if len(files) != 1 else ''}"
        )
        width = max((len(n) for n, _, _ in files), default=0)
        for name, size, k in files:
            print(f"    {name:<{width}}   {size_of(size) if k == 'file' else 'link'}")
        code, bad = runs(pkg, kind), escapes(pkg)
        if code or bad:
            flagged += 1
            print("  runs on install:" if code else "  paths that escape:")
            for name, n, why in code:
                print(f"    {name}:{n}   {why}")
            if code and bad:
                print("  paths that escape:")
            for name in bad:
                print(f"    {name}   absolute or climbs out with ..")
        print()
    if not shown:
        print("No package file here (a wheel, sdist, npm tarball or .crate).")
        return kernel.ALIVE
    if not flagged:
        print(
            f"{shown} package{'s' if shown != 1 else ''} listed; none would run code on install."
        )
        return kernel.ALIVE
    print(f"{flagged} of {shown} package{'s' if shown != 1 else ''} would run code on install or "
          "write outside its folder. Read each before you install it; none was run here.")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
