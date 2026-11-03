"""install_scripts.py: the install scripts the packages in node_modules would
run, each cited by file and line. Python 3.9+.

    python adapters/stdlib/install-scripts/install_scripts.py --box DIR [--json]
    python adapters/stdlib/install-scripts/install_scripts.py --from FOLDER [--json]

Every package.json under the folder (the box's pile, or any folder) that sits
inside a node_modules folder is read, and its `scripts` object is checked for
the three hooks npm runs on an install: preinstall, install and postinstall.
Each one is listed under its package, by the file and line its key is on,
and the command as written:

    install-scripts: populated, 1 install script in 1 package would run on npm install; none was run here
    ## esbuild
      web/node_modules/esbuild/package.json:5  postinstall  node install.js

so you can see what code runs on npm install before you trust it. It prints a
report, as every report add-on does (adapters/stdlib/ci/README.md, the report
contract), and `--json` gives the same report as one JSON object. Nothing is
run, fetched or written. A key written with escapes can't be placed, so it is
cited at line 1; a package.json that isn't valid JSON is noted on stderr, said
in the report's first line, and not checked.

Exit codes, the kernel's: 0 nothing would run, or no node_modules folder
(empty); 42 an install script is there, which waits on you (populated), or
no package.json in node_modules could be read (unreachable); 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

NAME = "install-scripts"
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


def groups_of(found) -> list[tuple[str, list]]:
    """One group per package, in the order found; each row the file and line
    its hook's key is on, then the hook and the command as written."""
    return [(name, [(f"{path}:{n}", f"{hook:<11}  {cmd}") for path, n, hook, cmd in hooks])
            for name, hooks in found]  # fmt: skip


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
    unread = (f"; {len(bad)} package.json{'s' if len(bad) != 1 else ''} couldn't be read"
              if bad else "")  # fmt: skip
    if not read and not bad:
        said = (
            "no node_modules folder here, so no install script would run on npm install"
        )
        say(report(NAME, "empty", said, []), as_json)
        return kernel.ALIVE
    if not read:
        said = f"no package in node_modules could be read{unread}"
        say(report(NAME, "unreachable", said, []), as_json)
        return kernel.ESCALATE
    if not found:
        said = f"no install scripts in {read} package{'s' if read != 1 else ''} in node_modules"
        say(report(NAME, "empty", said + unread, []), as_json)
        return kernel.ALIVE
    scripts, pkgs = sum(len(h) for _, h in found), len(found)
    said = (f"{scripts} install script{'s' if scripts != 1 else ''} in {pkgs} "
            f"package{'s' if pkgs != 1 else ''} would run on npm install; none was run "
            f"here{unread}")  # fmt: skip
    say(report(NAME, "populated", said, groups_of(found)), as_json)
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
