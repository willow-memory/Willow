"""reports.py: bringing add-ons onto the report contract, in batches. Python 3.9+.

    python adapters/stdlib/ci/reports.py survey
    python adapters/stdlib/ci/reports.py scaffold NAME...
    python adapters/stdlib/ci/reports.py check NAME...

A report is the one shape an add-on prints what it found in (README.md beside
this file, the report contract). Which add-ons should print one, and what
their rows are, is a person's call; the rest is the same every time, and
this does it.

`survey` runs every add-on with a command line (test_contract.py's COMMANDS)
on one box, over a pile holding something to find, and says what shape each
printed: `report` (it keeps the contract), `rows` (lines with a place, the
nearest to a report), `json`, `one line`, `text`, `silent` (a hook or a
server) or `reader` (it keeps the readers' contract instead). The `rows`
ones that aren't reports yet are the next batch.

`scaffold` does the part of a conversion that is the same for every add-on:
the add-on's NAME, its own copy of `report`, `report_text` (taken from the
stack add-on, so the two can't drift) and `say`, `import json`, and `--json`
taken off the command line first thing in `main(argv)`, as `as_json`, so
however the add-on reads its arguments it never sees the flag. It refuses an
add-on that already has a report, and says what is left for a person:
building the report in `main`, the card's `output: report` and example, its
tests. Until the report is said with it, `as_json` carries a mark, and
`check` says an add-on with the mark isn't done.

`check` runs the report contract on the add-ons named, each alone.

Exit codes, the kernel's: 0 done; 42 something was left as it was (survey:
candidates remain; scaffold: an add-on it couldn't touch); 2 refused.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STDLIB = ROOT / "adapters" / "stdlib"
HERE = Path(__file__).resolve().parent
ALIVE, ESCALATE, REFUSED = 0, 42, 2
PLACE = re.compile(r"\S+\.\w+:\d+")
HEAD = re.compile(r"[a-z0-9-]+: (?:populated|empty|unreachable), \S.*")
#: the mark scaffold leaves on `as_json` until main says the report with it
WIRE = "# noqa: F841  wire: say(report(...), as_json)"
REPORT = '''

# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


{report_text}


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))
'''


def contract():
    """test_contract.py, for its COMMANDS, READERS and the findings pile."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("contract", HERE / "test_contract.py")
    tc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tc)
    return tc


def is_report(name: str) -> bool:
    """Whether its card's header says `output: report`, as stack reads it."""
    card = (STDLIB / name / "README.md").read_text(encoding="utf-8")
    head = re.search(r"<!--\s*willow-addon\s*\n(.*?)-->", card, re.S)
    return bool(
        head
        and re.search(r"^output:(?:.*,)?\s*report\s*(?:,.*)?$", head.group(1), re.M)
    )


def shape(out: str) -> str:
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines:
        return "silent"
    if HEAD.fullmatch(lines[0]):
        return "report"
    if out.lstrip().startswith(("{", "[")):
        return "json"
    if sum(1 for ln in lines if PLACE.search(ln)) >= 1 and len(lines) > 1:
        return "rows"
    return "one line" if len(lines) == 1 else "text"


def survey() -> int:
    tc = contract()
    tmp = Path(tempfile.mkdtemp())
    pile, box = tmp / "pile", tmp / "box"
    pile.mkdir()
    for rel, data in {"garden.md": b"Tomatoes want sun.\n", **tc.FINDINGS}.items():
        (pile / rel).write_bytes(data)
    subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(box),
                    "--pile", str(pile), "--key", str(tmp / "key"), *tc.NOW],
                   check=True, capture_output=True)  # fmt: skip
    seen: dict[str, list[str]] = {}
    for name, (script, argv) in sorted(tc.COMMANDS.items()):
        if name in tc.READERS:
            seen.setdefault("reader", []).append(name)
            continue
        here = tmp / "runs" / name
        here.mkdir(parents=True)
        fill = {"box": str(box), "pile": str(pile), "tmp": str(here)}
        try:
            got = subprocess.run([sys.executable, str(STDLIB / name / script),
                                  *[a.format(**fill) for a in argv]], cwd=here,
                                 capture_output=True, text=True, timeout=120,
                                 stdin=subprocess.DEVNULL)  # fmt: skip
            kind = shape(got.stdout)
        except subprocess.TimeoutExpired:
            kind = "silent"
        if kind == "report" and not is_report(name):
            kind = "report-shaped, card doesn't say so"
        seen.setdefault(kind, []).append(name)
    for kind in sorted(seen, key=lambda k: (-len(seen[k]), k)):
        print(f"{kind} ({len(seen[kind])})")
        print("  " + ", ".join(seen[kind]))
    left = seen.get("rows", [])
    print(
        f"\nnext batch: the {len(left)} that print rows with places and aren't reports yet"
    )
    return ESCALATE if left else ALIVE


def report_text_source() -> str:
    """stack's report_text, word for word: the one rendering."""
    src = (STDLIB / "stack" / "stack.py").read_text(encoding="utf-8")
    node = next(n for n in ast.parse(src).body
                if isinstance(n, ast.FunctionDef) and n.name == "report_text")  # fmt: skip
    lines = src.splitlines()[node.lineno - 1 : node.end_lineno]
    return "\n".join(lines)


def scaffold_one(name: str, stdlib: Path = STDLIB) -> tuple[bool, str]:
    folder = stdlib / name
    mains = [p for p in sorted(folder.glob("*.py"))
             if not p.name.startswith("test_") and "__main__" in p.read_text(encoding="utf-8")]  # fmt: skip
    if len(mains) != 1:
        return False, "no single script with a command line"
    path = mains[0]
    src = path.read_text(encoding="utf-8")
    if re.search(r"^def (report|report_text|say)\(", src, re.M):
        return False, "already has report, report_text or say"
    tree = ast.parse(src)
    main = next((n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name == "main" and n.args.args), None)  # fmt: skip
    if main is None:
        return False, "no main(argv) to take --json in"
    argv = main.args.args[0].arg
    # --json taken off before anything reads the command line, however it reads
    # it: its own parsing never sees it, so no flag count or position changes
    first = main.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        first = main.body[1]  # after a docstring
    lines = src.splitlines(keepends=True)
    lead = re.match(r"[ \t]*", lines[first.lineno - 1]).group()
    take = (
        f'{lead}as_json = "--json" in {argv}  {WIRE}\n'
        f'{lead}{argv} = [a for a in {argv} if a != "--json"]\n'
    )
    src = "".join(lines[: first.lineno - 1]) + take + "".join(lines[first.lineno - 1 :])
    # import json, NAME and the report's three functions
    if not re.search(r"^import json$", src, re.M):
        src = re.sub(r"^(import \w+\n)", r"import json\n\1", src, count=1, flags=re.M)
    tree = ast.parse(src)
    first_def = next(
        n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
    )
    lines = src.splitlines(keepends=True)
    start = first_def.lineno - 1 - len(first_def.decorator_list)
    while start > 0 and lines[start - 1].lstrip().startswith("#"):
        start -= 1  # keep a comment block with what it heads
    block = (
        f'NAME = "{name}"\n'
        + REPORT.replace("{report_text}", report_text_source())
        + "\n\n"
    )
    src = "".join(lines[:start]) + block + "".join(lines[start:])
    ast.parse(src)  # it still reads as Python
    path.write_text(src, encoding="utf-8")
    return True, path.relative_to(stdlib.parents[1]).as_posix()


def scaffold(names: list[str]) -> int:
    worst = ALIVE
    for name in names:
        if not (STDLIB / name / "README.md").is_file():
            print(f"refused: no add-on {name}", file=sys.stderr)
            return REFUSED
    for name in names:
        ok, said = scaffold_one(name)
        print(f"{'scaffolded' if ok else 'left as it was'}: {name} ({said})")
        if not ok:
            worst = ESCALATE
    print("\nleft for a person, each add-on:\n"
          "  1. in main, build report(NAME, state, said, groups) where it printed,\n"
          "     and say(doc, as_json) it; empty exits 0, unreachable 42\n"
          "  2. its card: `output: report`, [--json] in the usage, the report as the example\n"
          "  3. its tests: the report's lines and its JSON\n"
          "  4. reports.py check NAME, then readme.py write")  # fmt: skip
    return worst


def check(names: list[str]) -> int:
    worst = ALIVE
    for name in names:
        got = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                              str(HERE / "test_contract.py"), "-k", "report"],
                             env={**os.environ, "WILLOW_ONLY": name}, cwd=ROOT,
                             capture_output=True, text=True)  # fmt: skip
        tail = (got.stdout.strip().splitlines() or [""])[-1]
        unwired = any(WIRE in p.read_text(encoding="utf-8")
                      for p in (STDLIB / name).glob("*.py"))  # fmt: skip
        held = (
            got.returncode == 0 and "passed" in tail and is_report(name) and not unwired
        )
        tail += "; as_json not wired yet" if unwired else ""
        print(f"{'holds' if held else 'not yet'}: {name} ({tail})")
        if not held:
            worst = ESCALATE
    return worst


def main(argv: list[str]) -> int:
    verb, names = (argv[0], argv[1:]) if argv else ("", [])
    if verb == "survey" and not names:
        return survey()
    if (
        verb in ("scaffold", "check")
        and names
        and not any(n.startswith("-") for n in names)
    ):
        return scaffold(names) if verb == "scaffold" else check(names)
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
