"""new.py: an add-on started from its idea on the list. Python 3.9+.

    python adapters/stdlib/ci/new.py NAME [--added YYYY-MM-DD]

Building an idea from adapters/planned.json starts the same way every time,
and this does that part (docs/agents/add-ons.md's steps 1, 3, 4 and 5):

- its folder, adapters/KIND/NAME/, with its card, README.md, whose header
  is the idea's entry as it stands (every field, in its order, `added`
  after `source`: today, or --added), a title and the idea's line;
- its script, NAME.py (a dash an underscore), that keeps the command-line
  contract from the start: every command line is refused, exit 2, naming
  the script, until it's built;
- its test file, holding that refusal, a test that can fail;
- the idea out of adapters/planned.json, written as that file always is;
- FILES.md's tree (files.py write) and the add-on list (readme.py write).

What it can't do is the add-on itself, and it says what's left for a
person, which is why it exits 42 when it has made everything: the code, its
tests, the card's body, its line in test_contract.py's COMMANDS (a command
that works, which only the built add-on has), a changelog fragment, and its
mutants run. A deps idea also needs its two requirements files and its
card's `floor:` line, said too.

It refuses a name that isn't an idea on the list, and one whose folder is
already there; it changes nothing then.

Exit codes, the kernel's: 42 made, with what's left for a person; 2
refused.
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: new.py NAME [--added YYYY-MM-DD]"


class Refused(Exception):
    pass


def card(name: str, entry: dict, added: str, script: str, kind: str) -> str:
    fields = [(k, v) for k, v in entry.items() if k not in ("name", "kind")]
    at = next((i + 1 for i, (k, _) in enumerate(fields) if k == "source"), len(fields))
    fields.insert(at, ("added", added))
    head = "".join(f"{k}: {v}\n" for k, v in fields)
    return (
        f"<!-- willow-addon\n{head}-->\n# {name}\n\n{entry['line']}\n\n"
        f"    python adapters/{kind}/{name}/{script}\n"
    )


def stub(name: str, entry: dict, script: str, kind: str) -> str:
    return f'''"""{script}: {entry["line"].rstrip(".")}. Python 3.9+.

    python adapters/{kind}/{name}/{script}

Not built yet: made by adapters/stdlib/ci/new.py from its idea. Until it
is, every command line is refused.

Exit codes, the kernel's: 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: {script}"


def main(argv: list[str]) -> int:
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def test_stub(name: str, script: str) -> str:
    return f'''"""{name}'s tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = subprocess.run([sys.executable, str(HERE / "{script}")], capture_output=True, text=True)
    assert got.returncode == 2 and "{script}" in got.stderr
'''


def _files_mod(root: Path):
    spec = importlib.util.spec_from_file_location(
        "willow_files_for_new", root / "adapters/stdlib/ci/files.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def readme_write(root: Path) -> None:
    subprocess.run([sys.executable, str(root / "adapters/stdlib/readme/readme.py"), "write"],
                   cwd=root, capture_output=True, text=True, check=True)  # fmt: skip


def make(
    root: Path, name: str, added: str, regenerate=readme_write
) -> tuple[list[str], list[str]]:
    """(the files made, what's left for a person). Refused changes nothing."""
    planned = root / "adapters" / "planned.json"
    entries = json.loads(planned.read_text(encoding="utf-8"))
    entry = next((e for e in entries if e.get("name") == name), None)
    if entry is None:
        raise Refused(f"{name} isn't an idea on adapters/planned.json")
    kind = entry.get("kind")
    if kind not in ("stdlib", "deps"):
        raise Refused(f"{name}'s idea says kind {kind!r}, not stdlib or deps")
    folder = root / "adapters" / kind / name
    if folder.exists():
        raise Refused(f"adapters/{kind}/{name}/ is already there")
    script = name.replace("-", "_") + ".py"
    rel = f"adapters/{kind}/{name}"
    folder.mkdir()
    made = {
        f"{rel}/README.md": card(name, entry, added, script, kind),
        f"{rel}/{script}": stub(name, entry, script, kind),
        f"{rel}/test_{script}": test_stub(name, script),
    }
    for path, text in made.items():
        (root / path).write_text(text, encoding="utf-8")
    rest = [e for e in entries if e is not entry]
    planned.write_text(
        json.dumps(rest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    files = _files_mod(root)
    files.write(root / "FILES.md", root, files.repo_files(root))
    regenerate(root)
    left = [
        f"the add-on itself, in {rel}/{script}, and the card's body in {rel}/README.md",
        f"its tests, in {rel}/test_{script}, beyond the refusal it holds",
        f"its line in COMMANDS, once it's built: python adapters/stdlib/ci/commands.py suggest {name} --write",
        f"its changelog fragment, changes/+<branch>.added.md, opening `{name}`",
        f"its mutants: python adapters/stdlib/mutants/mutants.py run {name}",
    ]
    if kind == "deps":
        left.insert(
            2,
            f"{rel}/requirements.txt and requirements-floor.txt, and the card's floor: line",
        )
    return sorted(made), left


def main(argv: list[str]) -> int:
    args = list(argv)
    added = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    if "--added" in args:
        i = args.index("--added")
        try:
            added = datetime.date.fromisoformat(args[i + 1]).isoformat()
        except (IndexError, ValueError):
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
        del args[i : i + 2]
    if len(args) != 1 or args[0].startswith("-"):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        made, left = make(ROOT, args[0], added)
    except Refused as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    for path in made:
        print(f"made: {path}")
    print("taken off adapters/planned.json; FILES.md and the add-on list written")
    print("left for a person:")
    for item in left:
        print(f"  - {item}")
    return kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
