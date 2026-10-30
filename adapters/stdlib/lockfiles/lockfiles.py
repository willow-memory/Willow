r"""lockfiles.py: Lockfiles as passages: each locked package and version. Python 3.9+.

    python adapters/stdlib/lockfiles/lockfiles.py mirror --from FOLDER --to MIRROR

Walks FOLDER for lockfiles by name (hidden folders and files skipped):
package-lock.json, yarn.lock, pnpm-lock.yaml, Cargo.lock, poetry.lock, uv.lock
and go.sum. Each is written as a heading and a line for each locked package, in
name order:

    lockfile: package-lock.json (npm), 3 packages
    lodash 4.17.21
    left-pad 1.3.0
    left-pad 0.0.3

so a question like "which version of lodash is locked?" finds a line. A package
locked at two versions is two lines; a line repeated is written once. Integrity
hashes, resolved addresses and the dependency lists are not copied. Python 3.9
has no TOML reader, so Cargo.lock, poetry.lock and uv.lock are read by their
`[[package]]` blocks' `name` and `version` lines; pnpm-lock.yaml and yarn.lock
are read by the shape of their package keys. A file with no package, or of a
kind it does not know by name, is skipped and counted.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KINDS = {
    "package-lock.json": "npm", "yarn.lock": "yarn", "pnpm-lock.yaml": "pnpm",
    "cargo.lock": "cargo", "poetry.lock": "poetry", "uv.lock": "uv", "go.sum": "go",
}  # fmt: skip
PNPM = re.compile(
    r"""^ {2,4}['"]?/?(@?[^@'"\s/]+(?:/[^@'"\s/]+)?)[@/]([0-9][^'":(\s]*)"""
)
YARN_KEY = re.compile(r'^"?(@?[^@"\s,]+(?:/[^@"\s,]+)?)@')
TOML_VALUE = re.compile(r'^(name|version)\s*=\s*"([^"]*)"')


def kind_of(name: str) -> str:
    low = name.lower()
    return next((k for f, k in KINDS.items() if low.endswith(f)), "")


def npm(doc: dict) -> set[tuple[str, str]]:
    found = set()
    packages = doc.get("packages")
    if isinstance(packages, dict):
        for path, meta in packages.items():
            if path and isinstance(meta, dict) and isinstance(meta.get("version"), str):
                found.add((path.rsplit("node_modules/", 1)[-1], meta["version"]))
    else:

        def walk(deps: object) -> None:
            for name, meta in (deps if isinstance(deps, dict) else {}).items():
                if isinstance(meta, dict) and isinstance(meta.get("version"), str):
                    found.add((name, meta["version"]))
                    walk(meta.get("dependencies"))

        walk(doc.get("dependencies"))
    return found


def toml_blocks(text: str) -> set[tuple[str, str]]:
    found, cur, active = set(), {}, False
    for line in text.splitlines() + ["[[package]]"]:
        s = line.strip()
        if s.startswith("["):  # a header ends the block being read
            if "name" in cur and "version" in cur:
                found.add((cur["name"], cur["version"]))
            cur, active = (
                {},
                s == "[[package]]",
            )  # [package.metadata] keys are not the package's
        elif active and not line.startswith((" ", "\t")):
            m = TOML_VALUE.match(s)
            if m and m.group(1) not in cur:
                cur[m.group(1)] = m.group(2)
    return found


def pnpm(text: str) -> set[tuple[str, str]]:
    found, inside = set(), False
    for line in text.splitlines():
        if line and not line.startswith((" ", "#")):
            inside = line.rstrip(":") in ("packages", "snapshots")
        elif inside and (m := PNPM.match(line)):
            found.add((m.group(1), m.group(2)))
    return found


def yarn(text: str) -> set[tuple[str, str]]:
    found, name = set(), ""
    for line in text.splitlines():
        if line and not line.startswith((" ", "#")) and line.rstrip().endswith(":"):
            m = YARN_KEY.match(line)
            name = m.group(1) if m else ""
        elif name and (m := re.match(r'^\s+version:?\s+"?([^"\s]+)"?\s*$', line)):
            found.add((name, m.group(1)))
            name = ""
    return found


def gosum(text: str) -> set[tuple[str, str]]:
    found = set()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2].startswith("h1:"):
            found.add((parts[0], parts[1].removesuffix("/go.mod")))
    return found


def convert(data: bytes, name: str = "") -> str | None:
    kind = kind_of(name)
    if not kind:
        return None
    text = data.decode("utf-8-sig")
    if kind == "npm":
        doc = json.loads(text)
        found = npm(doc) if isinstance(doc, dict) else set()
    elif kind in ("cargo", "poetry", "uv"):
        found = toml_blocks(text)
    else:
        found = {"pnpm": pnpm, "yarn": yarn, "go": gosum}[kind](text)
    if not found:
        return None
    n = len(found)
    lines = [
        f"{p} {v}"
        for p, v in sorted(found, key=lambda pv: (pv[0].lower(), pv[0], pv[1]))
    ]
    return (
        f"lockfile: {Path(name).name} ({kind}), {n} package{'s' if n != 1 else ''}\n"
        + "\n".join(lines)
        + "\n"
    )


EXTS = (
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "cargo.lock",
    "poetry.lock",
    "uv.lock",
    "go.sum",
)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: lockfiles.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(path.read_bytes(), path.name)
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
