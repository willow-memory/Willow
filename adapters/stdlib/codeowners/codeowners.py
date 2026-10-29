"""codeowners.py: who owns a file, by the CODEOWNERS rule that matches it,
cited by line. Python 3.9+.

    python adapters/stdlib/codeowners/codeowners.py --from REPO PATH [PATH...]
    python adapters/stdlib/codeowners/codeowners.py --box DIR PATH [PATH...]

The CODEOWNERS file is looked for where GitHub, GitLab and Forgejo each look
(.github/, the top, docs/, .gitlab/, .forgejo/, .gitea/; the first there is
read), and each PATH is matched against it the way that forge does:

    src/app.py
        .github/CODEOWNERS:12   /src/   @alice @org/web

GitHub's file: the last rule that matches wins. GitLab's: the last match in
each [Section] wins, and a section's owners add up; a rule with no owners
takes its section's defaults. Forgejo's and Gitea's: each rule is a regular
expression, and every rule that matches adds its owners. A rule with no
owners clears the file for GitHub; it is shown as "(no owners)".

Paths are only matched, never opened: a path need not exist. Nothing is run,
fetched or written.

Exit codes, the kernel's: 0 every path has an owner; 42 a path has none (or
there is no CODEOWNERS file), which waits on you; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

PLACES = (
    ".github/CODEOWNERS",
    "CODEOWNERS",
    "docs/CODEOWNERS",
    ".gitlab/CODEOWNERS",
    ".forgejo/CODEOWNERS",
    ".gitea/CODEOWNERS",
)
SECTION = re.compile(r"^\^?\[([^\]]+)\](?:\[(\d+)\])?(.*)$")


def locate(repo: Path) -> str | None:
    for rel in PLACES:
        if (repo / rel).is_file():
            return rel
    return None


def strip_comment(line: str) -> str:
    """The line less a trailing comment: a # that isn't escaped with a backslash."""
    out, i = [], 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line):
            out.append(line[i : i + 2])
            i += 2
            continue
        if line[i] == "#":
            break
        out.append(line[i])
        i += 1
    return "".join(out).strip()


def split_rule(text: str) -> tuple[str, list[str]]:
    """(pattern, owners): the pattern runs to the first unescaped space."""
    i = 0
    while i < len(text) and not (text[i] in " \t" and text[i - 1 : i] != "\\"):
        i += 1
    return text[:i], text[i:].split()


def glob_regex(pattern: str) -> re.Pattern:
    """A gitignore-style CODEOWNERS pattern as a regex over a path with no
    leading slash. Anchored when it starts with a slash or has one inside;
    `dir/` is every file under a folder of that name; `dir/*` only the files
    directly in it."""
    directory = pattern.endswith("/")
    body = pattern.strip("/") if pattern != "/" else ""
    anchored = pattern.startswith("/") or "/" in pattern.rstrip("/")
    direct = body.endswith("/*") or body == "*" and anchored
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if body.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif body.startswith("/**", i) and i + 3 == len(body):
            out.append("/.*")
            i += 3
        elif c == "*":
            j = i
            while j < len(body) and body[j] == "*":
                j += 1
            out.append(".*" if j - i > 1 else "[^/]*")
            i = j
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "\\" and i + 1 < len(body):
            out.append(re.escape(body[i + 1]))
            i += 2
        else:
            out.append(re.escape(c))
            i += 1
    tail = "/.*" if directory else "" if direct else "(?:/.*)?"
    return re.compile(("^" if anchored else "^(?:.*/)?") + "".join(out) + tail + "$")


def parse(text: str, dialect: str):
    """Sections of rules: [(name, [(line, pattern, owners, matcher)])]. A file
    with no [Section] is one section named ''. Rules in a regex file carry the
    compiled regex itself; a bad one is skipped and listed in `bad`."""
    sections, bad = [("", [])], []
    defaults: list[str] = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw)
        if not line:
            continue
        m = SECTION.match(line) if dialect != "regex" else None
        if m:
            name = m.group(1)
            defaults = m.group(3).split()
            same = [x for x in sections if x[0].casefold() == name.casefold()]
            if not same:  # a section named twice is one section
                sections.append((name, []))
            else:
                sections.append(sections.pop(sections.index(same[0])))
            continue
        pattern, owners = split_rule(line)
        try:
            matcher = re.compile(pattern) if dialect == "regex" else glob_regex(pattern)
        except re.error:
            bad.append(n)
            continue
        sections[-1][1].append((n, pattern, owners or list(defaults), matcher))
    return [s for s in sections if s[1] or s[0]], bad


def owners_of(path: str, sections, dialect: str):
    """[(line, pattern, owners, section)] for the rules that decide the path."""
    hits = []
    for name, rules in sections:
        found = [
            r
            for r in rules
            if (r[3].search(path) if dialect == "regex" else r[3].match(path))
        ]
        if dialect == "regex":
            hits += [(n, p, o, name) for n, p, o, _ in found]
        elif found:
            n, p, o, _ = found[-1]
            hits.append((n, p, o, name))
    return hits


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if (
        not args
        or any(a.startswith("--") for a in args)
        or len([v for v in opts.values() if v]) != 1
        or len(opts) != 1
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if "--box" in opts:
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        repo = Path(kernel.config(box)["pile"])
    else:
        repo = Path(opts["--from"])
        if not repo.is_dir():
            print(f"refused: {repo} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    where = locate(repo)
    if where is None:
        print("No CODEOWNERS file here (looked in .github/, the top, docs/, .gitlab/, "
              ".forgejo/ and .gitea/), so no file has an owner.")  # fmt: skip
        return kernel.ESCALATE
    dialect = "regex" if where.startswith((".forgejo/", ".gitea/")) else "glob"
    sections, bad = parse(
        (repo / where).read_text(encoding="utf-8", errors="replace"), dialect
    )
    for n in bad:
        print(
            f"note: {where}:{n} isn't a pattern this reads, so it was skipped",
            file=sys.stderr,
        )
    unowned = 0
    for raw in args:
        path = raw.replace("\\", "/").lstrip("/")
        while path.startswith("./"):
            path = path[2:]
        print(raw)
        hits = owners_of(path, sections, dialect)
        if not any(o for _, _, o, _ in hits):
            unowned += 1
        if not hits:
            print("    no rule matches")
        for n, pattern, owners, name in hits:
            tag = f"  [{name}]" if name else ""
            print(
                f"    {where}:{n}   {pattern}   {' '.join(owners) or '(no owners)'}{tag}"
            )
    if unowned:
        print(
            f"\n{unowned} of {len(args)} path{'s' if len(args) != 1 else ''} with no owner."
        )
        return kernel.ESCALATE
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
