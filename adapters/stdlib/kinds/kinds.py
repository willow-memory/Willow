"""kinds.py: every file of this repo sorted by what it is, and the ones nothing declares. Python 3.9+.

    python adapters/stdlib/kinds/kinds.py count [--json] [--root DIR]
    python adapters/stdlib/kinds/kinds.py of PATH... [--json] [--root DIR]

A repository holds several kinds of thing in one folder: what was written
to be read, what a script made from that, tests, made-up data, ideas not
built, an account of what was done. Asked a question, they answer as
equals, so a list made from the cards outranks the cards, and an idea reads
as if it were built. This says which is which, and it starts with what is
here: a file has a kind only when something the repo already keeps says so.

    made      a script makes it: ci's made.py names the script
    account   what was done, not what is: towncrier.toml names the changelog
    idea      not built yet: adapters/planned.json is the ideas list
    frozen    a study froze it: a FROZEN.json in its demo lists it
    test      pytest runs it: it is named test_*.py or conftest.py
    card      an add-on's README.md, the one that opens `<!-- willow-addon`
    code      a script beside an add-on's card
    fixture   anything else in an add-on's folder: samples, stand-ins
    made-up   a made-up person's files: the demo holds a make_life.py

The first of these that fits is the file's kind. A file none fits is one
nothing declares, and those are listed by folder: the kernel, its ports and
its law are among them today, which is the point of counting.

`count` reports the whole repo: the files git tracks, and new ones it isn't
told to ignore. `of` says each named file's kind and what says so, a line
each. `--root DIR` reads another checkout; `--json` prints the report as one
JSON object.

It reads the repo and writes nothing. Exit codes, the kernel's: 0 every
file asked about has a kind; 42 some have none, and they are listed, or git
couldn't list the files; 2 refused (a bad command line, a `--root` that is
not a folder, a PATH git doesn't track).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

NAME = "kinds"
USAGE = "usage: kinds.py count [--json] [--root DIR] | kinds.py of PATH... [--json] [--root DIR]"

#: Each kind, in the order they are tried, and what says a file is one.
KINDS = (
    ("made", "a script makes it: made.py names the script"),
    ("account", "what was done: towncrier.toml names the changelog"),
    ("idea", "not built yet: the ideas list"),
    ("frozen", "a study froze it: its demo's FROZEN.json lists it"),
    ("test", "pytest runs it: named test_*.py or conftest.py"),
    ("card", "an add-on's own README.md"),
    ("code", "a script beside an add-on's card"),
    ("fixture", "the rest of an add-on's folder"),
    ("made-up", "a made-up person's files: the demo holds a make_life.py"),
)
MADE_PY = "adapters/stdlib/ci/made.py"
IDEAS = "adapters/planned.json"
CARD_OPENS = "<!-- willow-addon"

#: What each script made.py names writes. made.py holds the scripts, not
#: their files, so the files are said here; a script it names that isn't
#: here is reported, never passed over.
WRITES = {
    "adapters/stdlib/readme/readme.py": ("ADDONS.md",),
    "adapters/stdlib/ci/bugs.py": ("BUGS.md",),
    "adapters/stdlib/ci/files.py": ("FILES.md",),
    "adapters/stdlib/ci/order.py": (),  # it sorts lists in place; it makes no file
    "adapters/stdlib/ci/pypi_dates.py": ("adapters/stdlib/ci/pypi-dates.json",),
    "demo/craft-assembly/report.py": (
        "demo/craft-assembly/REPORT.md",
        "demo/craft-assembly/results/checks.md",
    ),
}


def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
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


def tracked(root: Path) -> list[str] | None:
    """The repo's files under root: the ones git tracks, and new ones it
    isn't told to ignore. None when git can't say."""
    git = shutil.which("git")
    if git is None:
        return None
    got = subprocess.run(
        [
            git,
            "-C",
            str(root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        capture_output=True,
    )
    if got.returncode != 0:
        return None
    return sorted(f for f in got.stdout.decode("utf-8", "replace").split("\0") if f)


def text_of(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def made_by(root: Path) -> tuple[dict[str, str], list[str]]:
    """({file: the script that makes it}, [scripts made.py names that WRITES
    doesn't know])."""
    scripts = re.findall(r'"((?:adapters|demo)/[^"\s]+\.py)"', text_of(root / MADE_PY))
    files = {f: s for s in scripts for f in WRITES.get(s, ())}
    return files, sorted(s for s in set(scripts) if s not in WRITES)


def changelog(root: Path) -> tuple[str | None, str | None]:
    """(the fragments' folder, the changelog's file), as towncrier.toml names them."""
    toml = text_of(root / "towncrier.toml")
    found = [re.search(rf'^{key}\s*=\s*"([^"]+)"', toml, flags=re.M) for key in ("directory", "filename")]  # fmt: skip
    return tuple(m.group(1).strip("/") if m else None for m in found)


def frozen_by(root: Path, files: list[str]) -> dict[str, str]:
    """{file: the FROZEN.json that lists it}. A freeze lists its files under
    `files` or `sources`, by their path from its own folder."""
    out: dict[str, str] = {}
    for f in files:
        parts = f.split("/")
        if len(parts) != 3 or parts[0] != "demo" or not re.fullmatch(r"FROZEN(-\d+)?\.json", parts[2]):  # fmt: skip
            continue
        try:
            doc = json.loads(text_of(root / f) or "{}")
        except ValueError:
            doc = {}  # a freeze that can't be read lists nothing, and is still one
        for key in ("files", "sources"):
            listed = doc.get(key) if isinstance(doc, dict) else None
            for name in listed if isinstance(listed, (dict, list)) else ():
                if isinstance(name, str):
                    out.setdefault(f"demo/{parts[1]}/{name}", f)
        out.setdefault(f, f)  # the freeze itself is frozen: the tests hash it
    return out


def census(
    root: Path, files: list[str]
) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """({file: (kind, what says so)} for each file that has one, [made.py's
    scripts this doesn't know]). The first kind in KINDS that fits is it."""
    have = set(files)
    made, unknown = made_by(root)
    fragments, log = changelog(root)
    frozen = frozen_by(root, files)
    cards = {
        f.rsplit("/", 1)[0]
        for f in files
        if f.count("/") == 3 and f.startswith("adapters/") and f.endswith("/README.md")
        and text_of(root / f).startswith(CARD_OPENS)
    }  # fmt: skip
    people = {f.split("/")[1] for f in files if f.count("/") == 2 and f.startswith("demo/") and f.endswith("/make_life.py")}  # fmt: skip
    out: dict[str, tuple[str, str]] = {}
    for f in files:
        parts = f.split("/")
        base = parts[-1]
        addon = (
            "/".join(parts[:3])
            if len(parts) > 3 and "/".join(parts[:3]) in cards
            else None
        )
        if f in made and made[f] in have:
            out[f] = ("made", made[f])
        elif f == log or (
            fragments and f.startswith(fragments + "/") and base != "README.md"
        ):
            out[f] = ("account", "towncrier.toml")
        elif f == IDEAS:
            out[f] = ("idea", IDEAS)
        elif f in frozen:
            out[f] = ("frozen", frozen[f])
        elif (
            base.startswith("test_") and base.endswith(".py")
        ) or base == "conftest.py":
            out[f] = ("test", "its name")
        elif addon and len(parts) == 4 and base == "README.md":
            out[f] = ("card", f)
        elif addon and len(parts) == 4 and base.endswith(".py"):
            out[f] = ("code", addon + "/README.md")
        elif addon:
            out[f] = ("fixture", addon + "/README.md")
        elif len(parts) > 2 and parts[0] == "demo" and parts[1] in people:
            out[f] = ("made-up", f"demo/{parts[1]}/make_life.py")
    return out, unknown


def folder_of(f: str) -> str:
    """Where an undeclared file is counted: its top folder, one deeper under
    adapters/ and demo/, and `(top level)` for a file at the root."""
    parts = f.split("/")
    if len(parts) == 1:
        return "(top level)"
    deep = 2 if parts[0] in ("adapters", "demo") and len(parts) > 2 else 1
    return "/".join(parts[:deep]) + "/"


def whole(files: list[str], known: dict, unknown: list[str]) -> dict:
    counts = {k: sum(1 for kind, _ in known.values() if kind == k) for k, _ in KINDS}
    rows = [
        (k, f"{counts[k]} file{'' if counts[k] == 1 else 's'}; {why}")
        for k, why in KINDS
        if counts[k]
    ]
    lost: dict[str, list[str]] = {}
    for f in files:
        if f not in known:
            lost.setdefault(folder_of(f), []).append(f)
    none = [
        (where, f"{len(fs)} file{'' if len(fs) == 1 else 's'}, such as {fs[0]}")
        for where, fs in sorted(lost.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]
    missed = [
        (s, "made.py names it, and what it writes isn't said here") for s in unknown
    ]
    n, undeclared = len(files), len(files) - len(known)
    if not files:
        return report(NAME, "empty", "no file is tracked here", [])
    said = (
        f"{n} files: {len(known)} are one of {len(rows)} kinds, "
        f"{undeclared} nothing declares"
    )
    return report(NAME, "populated", said, [
        ("what it is, and what says so", rows),
        ("nothing declares", none),
        ("a script whose files aren't known", missed),
    ])  # fmt: skip


def named(paths: list[str], known: dict) -> dict:
    rows = [
        (p, "; ".join(known[p]) if p in known else "nothing declares it") for p in paths
    ]
    lacking = sum(1 for p in paths if p not in known)
    said = f"{len(paths)} asked: {len(paths) - lacking} have a kind, {lacking} nothing declares"
    return report(NAME, "populated", said, [(None, rows)])


def args_of(argv: list[str]) -> tuple[bool, Path, list[str]]:
    """(as JSON, the root, the paths asked of: none for `count`)."""
    if not argv or argv[0] not in ("count", "of"):
        raise ValueError(USAGE)
    as_json, root, paths, it = False, ROOT, [], iter(argv[1:])
    for a in it:
        if a == "--json":
            as_json = True
        elif a == "--root":
            given = next(it, "")
            root = Path(given)
            if not given or not root.is_dir():
                raise ValueError(
                    f"refused: --root {given or 'with no folder'} is not a folder"
                )
        elif a.startswith("-"):
            raise ValueError(USAGE)
        else:
            paths.append(a.rstrip("/"))
    if (argv[0] == "of") != bool(paths):
        raise ValueError(USAGE)
    return as_json, root, paths


def main(argv: list[str]) -> int:
    try:
        as_json, root, paths = args_of(argv)
    except ValueError as why:
        print(why, file=sys.stderr)
        return kernel.REFUSED
    files = tracked(root)
    if files is None:
        say(report(NAME, "unreachable", f"git couldn't list the files of {root}", []), as_json)  # fmt: skip
        return kernel.ESCALATE
    stray = [p for p in paths if p not in files]
    if stray:
        print(f"refused: git doesn't track {stray[0]} here", file=sys.stderr)
        return kernel.REFUSED
    known, unknown = census(root, files)
    say(named(paths, known) if paths else whole(files, known, unknown), as_json)
    asked = paths or files
    waits = unknown or any(f not in known for f in asked)
    return kernel.ESCALATE if waits else kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
