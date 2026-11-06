"""agents_md_check.py: the commands and paths AGENTS.md, CLAUDE.md, GEMINI.md
or copilot-instructions.md name that the repo no longer has. Python 3.9+.

    python adapters/stdlib/agents-md-check/agents_md_check.py --from REPO [--json]
    python adapters/stdlib/agents-md-check/agents_md_check.py --box DIR [--json]

Every AGENTS.md, CLAUDE.md, GEMINI.md and copilot-instructions.md in the
folder (at any depth; not inside a node_modules, vendor or .git folder) is
read, and four kinds of thing in it are checked against what is there. What
is gone is listed as a report (adapters/stdlib/ci/README.md, the report
contract), a group per kind of thing, each row the line of the instruction
file, then what it names:

    agents-md-check: populated, 3 things named in 2 instruction files not found; each is a lead: a path a build makes shows here too
    ## path
      AGENTS.md:57  adapters/old/old.py: no such file
    ## import
      CLAUDE.md:3   RULES.md: no such file
    ## make target
      AGENTS.md:60  make lint: not in the Makefile

- a path in backticks (or in a code block): it has a slash or ends in a file
  extension, and is looked for from the repo's top, then from the file's own
  folder;
- a relative link, `[text](path)`, with any `#fragment` left off;
- a script a command runs (`python`, `node`, `bash`, `sh`, `./x`): the script
  is looked for the same way;
- `make TARGET`, `npm run NAME` (and pnpm, yarn): the target is looked for in
  the Makefile, the script in package.json;
- an `@path` import on a line of its own.

Left alone, since they say nothing about this repo: URLs, absolute and `~`
paths, a path holding `<`, `{`, `*`, `$` or `...`, a path whose first part is
a CAPITALISED placeholder (`DIR/x`, `VENV/bin/python`), and a command line
inside a block that starts with `$ `-less prose. What it lists is a lead: a
path made by a build, or created by the command itself, will show here too.

`--json` gives the same report as one JSON object. It only reads, and writes
nothing. Exit codes, the kernel's: 0 everything named is there, or no
instruction file (empty); 42 something named is gone (populated), and waits on
you; 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

NAMES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "copilot-instructions.md")
SKIP = {"node_modules", "vendor", ".git"}
TICKS = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMPORT = re.compile(r"^\s*@(\S+)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
RUNNERS = {
    "python",
    "python3",
    "py",
    "node",
    "bash",
    "sh",
    "ruby",
    "perl",
    "php",
    "deno",
    "bun",
}
TASK = {"npm", "pnpm", "yarn"}
#: a name with no slash is a file only when it ends in one of these
EXT = re.compile(
    r"\.(?:md|mdx|txt|py|pyi|json|jsonl|ya?ml|toml|cfg|ini|lock|sh|bash|zsh|ps1|js|mjs|cjs|jsx|ts|tsx"
    r"|rs|go|c|h|cc|cpp|hpp|java|kt|rb|php|pl|lua|swift|cs|html|css|scss|csv|tsv|xml|sql|svg|png"
    r"|jpg|jpeg|gif|pdf|ipynb|mk|env|gradle|tf)$"
)
NOT_THIS_REPO = re.compile(r"[<>{}*$|\;&=]|\.\.\.|^(?:[A-Za-z][\w+.-]*:|~|/|#)")
PLACEHOLDER = re.compile(r"^[A-Z][A-Z0-9_-]*(?:/|$)")
REPO_WORD = re.compile(r"\brepo(?:sitory|s)?\b", re.I)


NAME = "agents-md-check"


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
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
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    if not rows:
        return out[0]
    w = min(max(len(r["where"]) for r in rows), 60)
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def candidate(token: str) -> str | None:
    """The token as a repo path, or None if it isn't one worth checking."""
    token = token.strip().lstrip("\"'(").rstrip("\"',.:)")
    token = token.split("#", 1)[0].rstrip("/")
    if not token or NOT_THIS_REPO.search(token) or PLACEHOLDER.match(token + "/"):
        return None
    if "/" not in token and not EXT.search(token):
        return None
    if re.fullmatch(r"\d+(?:\.\d+)+", token) or token.endswith(("i.e", "e.g")):
        return None
    return token


def named_as_repo(token: str, line: str) -> bool:
    """A two-part owner/repo name is not a path when the line says it is a repo."""
    return (
        token.count("/") == 1 and not EXT.search(token) and bool(REPO_WORD.search(line))
    )


def exists(root: Path, here: Path, rel: str) -> bool:
    return any((base / rel).exists() for base in (root, here))


def make_targets(root: Path) -> set[str] | None:
    for name in ("Makefile", "makefile", "GNUmakefile"):
        p = root / name
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            found = set()
            for m in re.finditer(
                r"^([A-Za-z0-9_.%/-][^:=\s]*(?:\s+[^:=\s]+)*)\s*:(?!=)", text, re.M
            ):
                found.update(m.group(1).split())
            return found
    return None


def npm_scripts(root: Path) -> set[str] | None:
    p = root / "package.json"
    if not p.is_file():
        return None
    try:
        scripts = json.loads(p.read_text(encoding="utf-8", errors="replace")).get(
            "scripts"
        )
    except (ValueError, AttributeError):
        return None
    return set(scripts) if isinstance(scripts, dict) else set()


def command_checks(words: list[str]):
    """(kind, thing) pairs a command line asks the repo for."""
    while words and re.fullmatch(r"[A-Za-z_]\w*=\S*", words[0]):
        words = words[1:]  # VAR=value prefixes
    if not words:
        return
    head = Path(words[0]).name
    if words[0].startswith("./"):
        yield "path", words[0]
    elif head in RUNNERS or re.fullmatch(r"python3?\.\d+", head):
        rest = [w for w in words[1:] if not w.startswith("-")]
        if rest and not words[1].startswith("-"):
            yield "path", rest[0]
        elif rest and words[1] in ("-u", "-B", "-I", "-X"):
            yield "path", rest[0]
    elif (
        words[0] == "make"
        and len(words) > 1
        and re.fullmatch(r"[A-Za-z0-9_.-]+", words[1])
    ):
        yield "make", words[1]
    elif words[0] in TASK and len(words) > 2 and words[1] in ("run", "run-script"):
        yield "npm", words[2]


def check_text(text: str, root: Path, here: Path):
    """[(line, thing, kind, why)] for each missing thing in one file."""
    makes, scripts = make_targets(root), npm_scripts(root)
    out, seen, fenced = [], set(), False
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        found: list[tuple[str, str]] = []
        if m := IMPORT.match(line):
            found.append(("import", m.group(1)))
        for m in LINK.finditer(line):
            found.append(("link", m.group(1)))
        chunks = (
            [line.strip()] if fenced or line.startswith("    ") else TICKS.findall(line)
        )
        for chunk in chunks:
            chunk = re.sub(r"^\$\s+", "", chunk)
            words = chunk.split()
            kinds = list(command_checks(words)) if len(words) > 1 else []
            found += [(k, t) for k, t in kinds]
            if len(words) == 1 and (c := candidate(words[0])):
                found.append(("path", c))
        for kind, thing in found:
            if kind == "make":
                missing = makes is not None and thing not in makes
                why = "make target: not in the Makefile"
            elif kind == "npm":
                missing = scripts is not None and thing not in scripts
                why = "script: not in package.json"
            else:
                rel = (
                    candidate(thing) if kind != "import" else candidate(thing) or thing
                )
                if rel is None:
                    continue
                if named_as_repo(rel, line):
                    continue
                missing = not exists(root, here, rel)
                why = (
                    "import: no such file" if kind == "import" else "path: no such file"
                )
            key = (n, kind, thing)
            if missing and key not in seen:
                seen.add(key)
                out.append(
                    (
                        n,
                        thing
                        if kind not in ("make", "npm")
                        else f"{'make' if kind == 'make' else 'npm run'} {thing}",
                        why,
                    )
                )
    return out


def find(folder: Path):
    for p in sorted(folder.rglob("*.md")):
        rel = p.relative_to(folder)
        if p.name in NAMES and p.is_file() and not SKIP & set(rel.parts[:-1]):
            yield p, rel


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
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
        root = Path(kernel.config(box)["pile"])
    else:
        root = Path(opts["--from"])
        if not root.is_dir():
            print(f"refused: {root} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    files = list(find(root))
    if not files:
        said = (
            "no AGENTS.md, CLAUDE.md, GEMINI.md or copilot-instructions.md here,"
            " so nothing in one has gone missing"
        )
        say(report(NAME, "empty", said, []), as_json)
        return kernel.ALIVE
    rows = []
    for p, rel in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        rows += [
            (rel.as_posix(), n, thing, why)
            for n, thing, why in check_text(text, root, p.parent)
        ]
    n_files = f"{len(files)} instruction file{'s' if len(files) != 1 else ''}"
    if not rows:
        say(
            report(NAME, "empty", f"everything named in {n_files} is there", []),
            as_json,
        )
        return kernel.ALIVE
    # a group per kind (path, import, make target, script), each row the line
    # of the instruction file and then the thing it names and why it is dead
    kinds = ("path", "import", "make target", "script")
    groups = [
        (kind, [(f"{f}:{n}", f"{thing}: {why.split(': ', 1)[1]}")
                for f, n, thing, why in rows if why.split(": ", 1)[0] == kind])
        for kind in kinds
    ]  # fmt: skip
    said = (f"{len(rows)} thing{'s' if len(rows) != 1 else ''} named in {n_files} not found;"
            " each is a lead: a path a build makes shows here too")  # fmt: skip
    say(report(NAME, "populated", said, groups), as_json)
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
