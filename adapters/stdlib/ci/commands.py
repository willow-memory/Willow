"""commands.py: an add-on's line in COMMANDS, found from its own usage lines. Python 3.9+.

    python adapters/stdlib/ci/commands.py suggest NAME [--write]

Every add-on a person runs has a line in test_contract.py's COMMANDS: a
command that works, which the contract test runs (exit 0 or 42), and runs
again with two stray arguments (refused, naming the script). It was written
by hand for each add-on, from the usage lines the script's docstring
already gives.

`suggest` reads those lines (`python adapters/stdlib/NAME/SCRIPT ...`),
makes each a command the test can fill in (`--box DIR` is `{box}`, `--to
DIR` is `{tmp}`, `--from DIR` is `{pile}`, `--now TS` is NOW, a question or
a word is "tomatoes", an optional `[...]` left out), and runs each the way
the test does, on the same small box and pile, each run held to 20 seconds.
The first that keeps the contract is printed as its line; `--write` puts it
in COMMANDS, in its place A to Z. When none does, it says what each did,
and the line is a person's to write.

A reader's line is made from READERS, and the repo's own tools are tested
in their own folders: both are refused.

Exit codes, the kernel's: 0 a line found (written, with --write); 42 none
of the usage lines keeps the contract, said one by one; 2 refused.
"""

from __future__ import annotations

import ast
import importlib.util
import itertools
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STDLIB = ROOT / "adapters" / "stdlib"
CONTRACT = HERE / "test_contract.py"
USAGE = "usage: commands.py suggest NAME [--write]"
NOW = "2026-10-23T00:00:00Z"
OWN = {"ci", "readme", "similar", "mutants", "github"}
WAIT = 20
#: what a placeholder after a flag becomes, by flag
AFTER = {"--box": "{box}", "--to": "{tmp}", "--from": "{pile}", "--pile": "{pile}",
         "--now": NOW, "--record": "{box}/record.jsonl"}  # fmt: skip


class Refused(Exception):
    pass


def script_of(name: str, stdlib: Path = STDLIB) -> Path:
    """The script a person runs: NAME.py (a dash an underscore), or the one
    script in the folder with a __main__."""
    folder = stdlib / name
    if not folder.is_dir():
        raise Refused(f"there is no adapters/stdlib/{name}/")
    plain = folder / f"{name.replace('-', '_')}.py"
    if plain.is_file():
        return plain
    mains = [p for p in sorted(folder.glob("*.py"))
             if not p.name.startswith("test_") and "__main__" in p.read_text(encoding="utf-8")]  # fmt: skip
    if len(mains) != 1:
        raise Refused(f"{name}: can't tell which script a person runs")
    return mains[0]


def usage_lines(script: Path) -> list[list[str]]:
    """Each usage line of the docstring, as its words after the script; a
    line that runs on is read with the indented lines under it."""
    doc = ast.get_docstring(ast.parse(script.read_text(encoding="utf-8"))) or ""
    out, lines = [], doc.splitlines()
    for k, line in enumerate(lines):
        m = re.match(rf"(\s*)python3? \S*{re.escape(script.name)}(.*)$", line)
        if not m:
            continue
        said = m.group(2).rstrip()
        for more in lines[k + 1 :]:
            deeper = re.match(rf"{m.group(1)}\s{{4,}}(\S.*)$", more)
            if not deeper or "python" in more:
                break
            said += " " + deeper.group(1).rstrip()
        words = re.split(r"\s{2,}", said.strip())[0]  # what follows is said of it
        try:
            out.append(shlex.split(words))
        except ValueError:
            continue
    return out


def _drop_optional(words: list[str]) -> list[str]:
    out, depth = [], 0
    for w in words:
        opens, closes = w.count("["), w.count("]")
        if depth == 0 and not opens:
            out.append(w)
        depth += opens - closes
    return out


def _values(flag: str | None, word: str) -> list[str]:
    """What a placeholder could be filled with, likeliest first."""
    if flag in AFTER and not (flag == "--to" and _filelike(word)):
        return [AFTER[flag]] + (["{tmp}/out"] if flag == "--to" else [])
    if re.fullmatch(r"YYYY-MM-DD|DATE|DAY|\d{4}-\d\d-\d\d", word):
        return ["2026-10-01"]
    if "URL" in word or word.startswith("http"):
        return ["http://127.0.0.1:9/"]
    if flag in ("--to", "--out") or (flag and _filelike(word) and flag not in READ):
        ext = Path(word).suffix if "." in word else ""
        return [f"{{tmp}}/out{ext}", "{tmp}"]
    if flag in READ or _filelike(word):
        return ["{pile}/garden.md", "{tmp}/out"]
    if word.isdigit() or word in ("N", "K", "NUMBER", "COUNT"):
        return ["1"]
    if "|" in word:
        return [word.split("|")[0]]
    return ["tomatoes"]


#: flags whose file is one the add-on reads
READ = {"--questions", "--in", "--file", "--notes", "--input", "--catalog"}


def _filelike(word: str) -> bool:
    return word in ("FILE", "PATH") or bool(re.search(r"\.[a-z]{2,5}$", word))


def candidates(lines: list[list[str]]) -> list[list[str]]:
    """Commands the test can fill in, each line with its options left out
    and then as written, each placeholder's likeliest fillings, no repeats."""
    out = []
    for words in lines:
        for kept in (_drop_optional(words), [w.strip("[]") for w in words]):
            choices, flag = [], None
            for w in kept:
                if w in ("...", "…", "--"):
                    continue
                w = w[:-3] if w.endswith("...") else w
                if w.startswith("--"):
                    choices.append([w])
                    flag = w
                    continue
                placeholder = w.isupper() or not re.fullmatch(r"[a-z][a-z0-9-]*", w)
                choices.append(_values(flag, w) if placeholder or flag else [w])
                flag = None
            for argv in list(itertools.product(*choices))[:6]:
                if list(argv) not in out:
                    out.append(list(argv))
    return out


def _run(script: Path, *argv: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run([sys.executable, str(script), *argv], stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=WAIT)  # fmt: skip
    except subprocess.TimeoutExpired:
        return None


def keeps_contract(script: Path, argv: list[str], scratch: Path) -> str:
    """'' when the command keeps the contract test's promises; else what
    it did, as the test would say it."""
    pile, box = scratch / "pile", scratch / "box"
    if not pile.exists():
        pile.mkdir()
        (pile / "garden.md").write_text("Tomatoes want sun.\n", encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(box), "--pile",
                        str(pile), "--key", str(scratch / "key"), "--now", NOW],
                       check=True, capture_output=True)  # fmt: skip
    bare = _run(script)
    if bare is None or bare.returncode != 2 or script.name not in bare.stderr:
        return "a bare command line isn't refused naming the script"
    tmp = scratch / "tmp"
    tmp.mkdir(exist_ok=True)
    good = [a.format(box=box, pile=pile, tmp=tmp) for a in argv]
    got = _run(script, *good)
    if got is None:
        return f"still running after {WAIT}s"
    if got.returncode not in (0, 42):
        last = (got.stderr or got.stdout).strip().splitlines()[-1:] or [""]
        return f"exit {got.returncode}: {last[0][:120]}"
    stray = _run(script, *good, "--stray", "more")
    if stray is None or stray.returncode != 2 or script.name not in stray.stderr:
        return "two stray arguments aren't refused naming the script"
    return ""


def source(script: Path, argv: list[str]) -> str:
    """The line as COMMANDS writes one: NOW as *NOW."""
    parts, i = [], 0
    while i < len(argv):
        if argv[i : i + 2] == ["--now", NOW]:
            parts.append("*NOW")
            i += 2
            continue
        parts.append(
            repr(argv[i]).replace("'", '"') if '"' not in argv[i] else repr(argv[i])
        )
        i += 1
    return f'("{script.name}", [{", ".join(parts)}])'


def suggest(
    name: str, stdlib: Path = STDLIB
) -> tuple[str | None, list[tuple[list[str], str]]]:
    """(the line's source, or None; what each candidate did)."""
    if name in OWN:
        raise Refused(f"{name} is the repo's own tool, tested in its own folder")
    if f'"{name}": ("' in _readers_block():
        raise Refused(f"{name} is a reader: its line comes from READERS")
    script = script_of(name, stdlib)
    tried = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, argv in enumerate(candidates(usage_lines(script))):
            scratch = Path(tmp) / str(k)
            scratch.mkdir()
            why = keeps_contract(script, argv, scratch)
            tried.append((argv, why))
            if not why:
                return source(script, argv), tried
    return None, tried


def _readers_block() -> str:
    text = CONTRACT.read_text(encoding="utf-8")
    start = text.index("READERS: dict")
    return text[start : text.index("\n}", start)]


def write(name: str, line: str, contract: Path = CONTRACT) -> None:
    """The line into COMMANDS, then COMMANDS put A to Z by order.py."""
    text = contract.read_text(encoding="utf-8")
    if re.search(
        rf'^\s+"{re.escape(name)}": \(', text[text.index("COMMANDS: dict") :], re.M
    ):
        raise Refused(f"{name} already has a line in COMMANDS")
    head = re.search(r"^COMMANDS: dict\[.*\] = \{\n", text, re.M)
    text = text[: head.end()] + f'    "{name}": {line},\n' + text[head.end() :]
    spec = importlib.util.spec_from_file_location(
        "willow_order_for_commands", HERE / "order.py"
    )
    order = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(order)
    contract.write_text(order.sort_table(text, "COMMANDS"), encoding="utf-8")


def main(argv: list[str]) -> int:
    args = list(argv)
    do_write = "--write" in args
    if do_write:
        args.remove("--write")
    if len(args) != 2 or args[0] != "suggest" or args[1].startswith("-"):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    name = args[1]
    try:
        line, tried = suggest(name)
        if line and do_write:
            write(name, line)
    except Refused as why:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    for argv_, why in tried:
        print(f"{' '.join(argv_) or '(no arguments)'}: {why or 'keeps the contract'}")
    if line is None:
        print(
            f"none of {name}'s usage lines keeps the contract: its line in COMMANDS is a person's"
        )
        return kernel.ESCALATE
    print(f'\n    "{name}": {line},')
    print(
        "written into COMMANDS, A to Z" if do_write else "(--write puts it in COMMANDS)"
    )
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
