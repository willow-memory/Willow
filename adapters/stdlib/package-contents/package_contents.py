"""package_contents.py: what's inside a wheel, sdist, npm tarball or .crate
before you install it. Python 3.9+.

    python adapters/stdlib/package-contents/package_contents.py --from FILE-OR-FOLDER [--json]
    python adapters/stdlib/package-contents/package_contents.py --box DIR [--json]

Each package file is opened and its members listed, every one, with its size:
nothing is unpacked, run, fetched or written. Then the code that would run
because you installed it, each cited by the file and line that makes it run:

    package-contents: populated, 1 of 1 package would run code on install or write outside its folder; none was run here
    ## evil-1.0-py3-none-any.whl: wheel, 3 files
      evil/__init__.py             12 B
      evil-1.0.dist-info/METADATA  204 B
      evil.pth                     38 B
    ## evil-1.0-py3-none-any.whl runs on install
      evil.pth:1                   import: the line runs at every Python start

It prints a report, as every report add-on does (adapters/stdlib/ci/README.md,
the report contract), and `--json` gives the same report as one JSON object.

A wheel runs nothing while it is installed, but a `.pth` line that starts
with `import` runs every time Python starts. An sdist is built first: its
setup.py, and the build backend its pyproject.toml names, run. An npm tarball
runs its preinstall, install and postinstall scripts, and a binding.gyp with
no install script makes npm run node-gyp. A crate's build.rs runs when it is
compiled, and so does a procedural macro. A path that is absolute or climbs out
with `..` is flagged too: an unpacker that trusts it writes outside its folder.

Exit codes, the kernel's: 0 packages listed and nothing would run
(populated), or no package file (empty); 42 code would run, or a path
escapes, and waits on you (populated), or no package file here could be
opened (unreachable); 2 refused.
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

NAME = "package-contents"
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


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def groups_of(path: Path, pkg: Package) -> tuple[list[tuple[str, list]], bool]:
    """A package's groups: its files, each with its size; the code that runs
    on install, by file and line; and the paths that escape. And whether it
    was flagged (code runs, or a path escapes)."""
    kind = kind_of(pkg)
    files = [e for e in pkg.entries if e[2] != "dir"]
    listed = [
        (name, size_of(size) if k == "file" else "link") for name, size, k in files
    ]
    code, bad = runs(pkg, kind), escapes(pkg)
    head = f"{path.name}: {kind}, {len(files)} file{'s' if len(files) != 1 else ''}"
    return [
        (head, listed),
        (f"{path.name} runs on install", [(f"{n}:{i}", why) for n, i, why in code]),
        (f"{path.name} has paths that escape",
         [(n, "absolute or climbs out with ..") for n in bad]),
    ], bool(code or bad)  # fmt: skip


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from"):
            opts[a] = next(it, "")
        elif a == "--json":
            opts[a] = "yes"
        else:
            args.append(a)
    as_json = opts.pop("--json", None) is not None
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
    groups, shown, flagged, unopened = [], 0, 0, 0
    for path in paths:
        try:
            pkg = Package(path)
        except (OSError, tarfile.TarError, zipfile.BadZipFile, EOFError):
            print(
                f"note: {path.name} couldn't be opened as a package, so it was not checked",
                file=sys.stderr,
            )
            unopened += 1
            continue
        shown += 1
        these, hit = groups_of(path, pkg)
        groups += these
        flagged += hit
    unread = (f"; {unopened} couldn't be opened as {'a package' if unopened == 1 else 'packages'}"
              if unopened else "")  # fmt: skip
    if not paths:
        said = "no package file here (a wheel, sdist, npm tarball or .crate)"
        say(report(NAME, "empty", said, []), as_json)
        return kernel.ALIVE
    if not shown:
        said = f"no package file here could be opened{unread}"
        say(report(NAME, "unreachable", said, []), as_json)
        return kernel.ESCALATE
    pkgs = f"package{'s' if shown != 1 else ''}"
    if not flagged:
        said = f"{shown} {pkgs} listed; none would run code on install{unread}"
    else:
        said = (f"{flagged} of {shown} {pkgs} would run code on install or write outside"
                f" its folder; none was run here{unread}")  # fmt: skip
    doc = report(NAME, "populated", said, groups)
    if not doc["groups"]:  # every package holds nothing: no rows to show
        doc["state"] = "empty"
    say(doc, as_json)
    return kernel.ESCALATE if flagged else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
