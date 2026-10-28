"""trees.py: each gap's vulnerable and fixed trees, written as git stores them.

    python demo/known-gaps/trees.py fetch --to DIR --repos DIR [--unit NAME]
    python demo/known-gaps/trees.py check --to DIR [--unit NAME]

`fetch` writes, for each unit in pins.json, DIR/trees/<unit>/old (the
vulnerable side) and /new (the fixed side), and DIR/fixes/<unit>.diff (the
fix's diff, restricted to files_scored where the gap names them), from the
repository DIR/<repo> under --repos. A unit is a gap, or, for a gap fixed in
two repositories, the gap and the repository (KG03-kartikeya). It reads local
repositories only: no network. Each tree is every file of the pinned commit,
byte for byte, as git stores it (php2shell's phase3 `write_tree`). `check`
holds each tree to its git tree hash and each diff to its SHA-256, without
git. It also lists, per file, any counted file of a vulnerable tree that holds
a character making the kernel count lines differently from git (`unreachable`):
informational, it does not change the exit code. --unit limits either to one unit.

This module is also the folder's shared ground: the pins, the units, and the
php2shell modules the other scripts reuse.

Exit codes, the kernel's: 0 everything there and matching; 42 something is
missing; 2 something doesn't match, or a bad command line.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P2S = ROOT / "demo" / "php2shell"
for p in (ROOT / "adapters" / "stdlib" / "ci", ROOT / "adapters" / "stdlib" / "scan",
          P2S, ROOT):  # fmt: skip
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import make_trees  # noqa: E402
import phase3  # noqa: E402

DIFF = make_trees.DIFF
#: every tool file the rule and the statistics run on, by import graph from
#: this folder's scripts: FROZEN.json holds each one's hash, and the freeze
#: test re-hashes them, so a php2shell re-freeze can't change results silently
TOOLS = (
    "kernel.py",
    "adapters/stdlib/scan/scan.py",
    "adapters/stdlib/todo/todo.py",
    "adapters/stdlib/ci/whose.py",
    "demo/php2shell/make_trees.py",
    "demo/php2shell/phase2.py",
    "demo/php2shell/phase3.py",
    "demo/php2shell/phase4.py",
    "demo/php2shell/score.py",
    "demo/php2shell/score2.py",
)
PINS_FILE = HERE / "pins.json"


def sibling(name: str):
    """A script of this folder, loaded under its own name (kg_<name>): php2shell
    has a score.py too, and the two must never share `score`."""
    key = "kg_" + name
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def load_pins(path: Path = PINS_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["units"]


def load_gaps(path: Path = HERE / "gaps.json") -> dict:
    return {g["id"]: g for g in json.loads(path.read_text(encoding="utf-8"))["gaps"]}


def fetch_unit(to: Path, repos: Path, unit: str, pin: dict) -> None:
    src = repos / pin["repo"]
    for side, name in (("vulnerable", "old"), ("fixed", "new")):
        out = to / "trees" / unit / name
        if out.exists() and make_trees.git_tree(out) == pin[side]["tree"]:
            continue
        out.mkdir(parents=True, exist_ok=True)
        phase3.write_tree(src, pin[side]["commit"], out)
    (to / "fixes").mkdir(exist_ok=True)
    argv = [*DIFF, pin["vulnerable"]["commit"], pin["fixed"]["commit"]]
    if pin.get("files_scored"):
        argv += ["--", *pin["files_scored"]]
    (to / "fixes" / f"{unit}.diff").write_bytes(phase3.git(*argv, cwd=src))


def unreachable_files(tree: Path) -> list:
    """The counted files of a tree that hold a character making the kernel's
    line numbers differ from git's (a form feed, a vertical tab, U+2028, a
    lone carriage return, ...). A position in one can't be trusted, so ask.py
    and score.py give such a file no positions."""
    score = sibling("score")
    out = []
    for p in sorted(tree.rglob("*")):
        rel = p.relative_to(tree)
        if not p.is_file() or any(part.startswith(".") for part in rel.parts):
            continue
        if not score.counts(rel.as_posix()):
            continue
        try:
            text = p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue  # the kernel leaves it out too
        if score.shifted(text):
            out.append(rel.as_posix())
    return out


def check(to: Path, pins: dict) -> int:
    bad = missing = 0
    for unit, pin in pins.items():
        for side, name in (("vulnerable", "old"), ("fixed", "new")):
            t = to / "trees" / unit / name
            if not t.is_dir():
                print(f"missing   {unit} {name}")
                missing += 1
            elif make_trees.git_tree(t) != pin[side]["tree"]:
                print(f"DIFFERS   {unit} {name}")
                bad += 1
            else:
                print(f"matches   {unit} {name}")
                if name == "old":
                    for path in unreachable_files(t):
                        print(
                            f"unreachable   {unit} {path}: positions can't be trusted"
                        )
        d = to / "fixes" / f"{unit}.diff"
        if not d.is_file():
            print(f"missing   {unit} fix")
            missing += 1
        elif hashlib.sha256(d.read_bytes()).hexdigest() != pin["diff_sha256"]:
            print(f"DIFFERS   {unit} fix")
            bad += 1
        else:
            print(f"matches   {unit} fix")
    return 2 if bad else 42 if missing else 0


def main(argv: list[str]) -> int:
    cmd, opts = (argv[0] if argv else ""), dict(zip(argv[1::2], argv[2::2]))
    allowed = {"fetch": {"--to", "--repos", "--unit"}, "check": {"--to", "--unit"}}
    need = {"fetch": {"--to", "--repos"}, "check": {"--to"}}
    if (cmd not in allowed or len(argv) != 1 + 2 * len(opts)
            or not need[cmd] <= set(opts) <= allowed[cmd]):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    pins = load_pins()
    if "--unit" in opts:
        if opts["--unit"] not in pins:
            print(f"refused: no unit {opts['--unit']}", file=sys.stderr)
            return 2
        pins = {opts["--unit"]: pins[opts["--unit"]]}
    to = Path(opts["--to"])
    if cmd == "fetch":
        to.mkdir(parents=True, exist_ok=True)
        for unit, pin in pins.items():
            fetch_unit(to, Path(opts["--repos"]), unit, pin)
    return check(to, pins)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
