"""install_scripts.py: the install scripts the packages in node_modules would
run, each cited by file and line. Python 3.9+.

    python adapters/stdlib/install-scripts/install_scripts.py --box DIR
    python adapters/stdlib/install-scripts/install_scripts.py --from FOLDER

Every package.json under the folder (the box's pile, or any folder) that sits
inside a node_modules folder is read, and its `scripts` object is checked for
the three hooks npm runs on an install: preinstall, install and postinstall.
Each one is listed under its package, by the file and line its key is on,
and the command as written:

    esbuild
        web/node_modules/esbuild/package.json:5   postinstall   node install.js

so you can see what code runs on npm install before you trust it. Nothing is
run, fetched or written. A key written with escapes can't be placed, so it is
cited at line 1; a package.json that isn't valid JSON is noted and not checked.

Exit codes, the kernel's: 0 nothing would run (or no node_modules); 42 an
install script is there, which waits on you; 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

HOOKS = ("preinstall", "install", "postinstall")
SCRIPTS = re.compile(r'"scripts"\s*:')


def hook_line(text: str, hook: str) -> int:
    """The line a hook's key is on: the first one after the `scripts` key, so a
    look-alike earlier in the file isn't cited. 1 if the key is written with
    escapes and can't be placed."""
    start = SCRIPTS.search(text)
    m = re.compile(rf'"{hook}"\s*:').search(text, start.end() if start else 0)
    return text.count("\n", 0, m.start()) + 1 if m else 1


def shown(value) -> str:
    """A command as one line: a string as written, anything else as JSON."""
    text = value if isinstance(value, str) else json.dumps(value)
    return text.replace("\n", "\\n")


def name_of(data: dict, pkg: Path) -> str:
    """The package's own name, else its folder's (with its @scope, if any)."""
    name = data.get("name")
    if isinstance(name, str) and name.strip():
        return name
    if pkg.parent.name.startswith("@"):
        return f"{pkg.parent.name}/{pkg.name}"
    return pkg.name


def find(folder: Path):
    """(packages with install scripts, packages read, package.json files that
    couldn't be read). A package is (name, [(file, line, hook, command)])."""
    base = folder.resolve().name
    found, read, bad = [], 0, []
    for p in sorted(folder.rglob("package.json")):
        rel = p.relative_to(folder)
        if not p.is_file() or "node_modules" not in (base, *rel.parts[:-1]):
            continue
        try:
            raw = p.read_text(encoding="utf-8", errors="replace")
            data = json.loads(raw)
        except (OSError, ValueError):
            bad.append(rel.as_posix())
            continue
        read += 1
        scripts = data.get("scripts") if isinstance(data, dict) else None
        if not isinstance(scripts, dict):
            continue
        hooks = [h for h in HOOKS if h in scripts]
        if hooks:
            found.append((name_of(data, p.parent), [
                (rel.as_posix(), hook_line(raw, h), h, shown(scripts[h]))
                for h in hooks
            ]))  # fmt: skip
    return found, read, bad


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
        folder = Path(kernel.config(box)["pile"])
    else:
        folder = Path(opts["--from"])
        if not folder.is_dir():
            print(f"refused: {folder} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    found, read, bad = find(folder)
    for path in bad:
        print(f"note: {path} couldn't be read as a package.json, so it was not checked",
              file=sys.stderr)  # fmt: skip
    if not read and not bad:
        print(
            "No node_modules folder here, so no install script would run on npm install."
        )
        return kernel.ALIVE
    if not found:
        print(
            f"No install scripts in {read} package{'s' if read != 1 else ''} in node_modules."
        )
        return kernel.ALIVE
    width = max(len(f"{path}:{n}") for _, hooks in found for path, n, _, _ in hooks)
    for name, hooks in found:
        print(name)
        for path, n, hook, cmd in hooks:
            print(f"    {f'{path}:{n}':<{width}}   {hook:<11}   {cmd}")
    scripts, pkgs = sum(len(h) for _, h in found), len(found)
    print(f"\n{scripts} install script{'s' if scripts != 1 else ''} in {pkgs} "
          f"package{'s' if pkgs != 1 else ''} would run on npm install. Read each before "
          "you trust its package; none was run here.")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
