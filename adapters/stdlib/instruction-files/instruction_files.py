"""instruction_files.py: which instruction files each coding agent would load
for a folder, in what order, with each file's size and hash. Python 3.9+.

    python adapters/stdlib/instruction-files/instruction_files.py --from FOLDER [--at SUBFOLDER]
    python adapters/stdlib/instruction-files/instruction_files.py --box DIR [--at SUBFOLDER]

For an agent started in the folder (or, with --at, in a folder under it), the
files it reads, general first and most specific last, each with its size and
the start of its SHA-256:

    claude-code
        1  CLAUDE.md                    1.1 KB   sha256:3f2a9c0d41be
        2    @AGENTS.md (imported)      6.4 KB   sha256:b81c77e0aa13
    codex-cli
        1  AGENTS.md                    6.4 KB   sha256:b81c77e0aa13

The agents and what each reads:

| Agent | Files |
|---|---|
| claude-code | CLAUDE.md, .claude/CLAUDE.md and CLAUDE.local.md in each folder from the top down; .claude/rules; and the files an `@path` import pulls in |
| codex-cli | in each folder from the top down, AGENTS.override.md, or else AGENTS.md |
| gemini-cli | GEMINI.md in each folder from the top down |
| cursor | AGENTS.md in each folder; .cursor/rules; .cursorrules |
| copilot | .github/copilot-instructions.md; .github/instructions; AGENTS.md in each folder |
| windsurf | AGENTS.md in each folder; .windsurfrules; .windsurf/rules |
| opencode | in each folder, AGENTS.md, or else CLAUDE.md |
| cline | .clinerules, a file or a folder of them |

Two agents that read the same bytes show the same hash, and a file that is
the same bytes as another instruction file is said so. It lists what each tool
documents it reads; an agent's version, settings or a global file in your home
folder can add more, and none of those are read here.

It only reads, and writes nothing. Exit codes, the kernel's: 0 at least one
instruction file would load; 42 none would, which waits on you; 2 refused.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

SKIP = {"node_modules", ".git"}
IMPORT = re.compile(r"(?<![\w`])@([\w./-][\w./~-]*\.[\w]+|[\w./-]+/[\w./-]+)")
MAX_HOPS = 5


def size_of(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    return f"{n / 1024:.1f} KB" if n < 1 << 20 else f"{n / (1 << 20):.1f} MB"


def folders(root: Path, at: str) -> list[Path]:
    """The top, then each folder down to `at`."""
    out, cur = [root], root
    for part in Path(at).parts:
        if part not in (".", ""):
            cur = cur / part
            out.append(cur)
    return out


def tree(base: Path, patterns: tuple[str, ...]) -> list[Path]:
    """Files under base matching a glob, sorted, not inside a skipped folder."""
    found = []
    for pat in patterns:
        found += [
            p
            for p in base.glob(pat)
            if p.is_file() and not SKIP & set(p.relative_to(base).parts)
        ]
    return sorted(set(found))


def first(folder: Path, names: tuple[str, ...]) -> list[Path]:
    for name in names:
        if (folder / name).is_file():
            return [folder / name]
    return []


def each(dirs: list[Path], *names: str) -> list[Path]:
    return [folder / n for folder in dirs for n in names if (folder / n).is_file()]


def agents(root: Path, dirs: list[Path]) -> dict[str, list[Path]]:
    cline = root / ".clinerules"
    return {
        "claude-code": each(dirs, "CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md")
        + tree(root, (".claude/rules/**/*.md",)),
        "codex-cli": [
            p for d in dirs for p in first(d, ("AGENTS.override.md", "AGENTS.md"))
        ],
        "gemini-cli": each(dirs, "GEMINI.md"),
        "cursor": each(dirs, "AGENTS.md")
        + tree(root, (".cursor/rules/**/*.mdc", ".cursor/rules/**/*.md"))
        + first(root, (".cursorrules",)),
        "copilot": first(root, (".github/copilot-instructions.md",))
        + tree(root, (".github/instructions/**/*.instructions.md",))
        + each(dirs, "AGENTS.md"),
        "windsurf": each(dirs, "AGENTS.md")
        + first(root, (".windsurfrules",))
        + tree(root, (".windsurf/rules/**/*.md",)),
        "opencode": [p for d in dirs for p in first(d, ("AGENTS.md", "CLAUDE.md"))],
        "cline": tree(root, (".clinerules/**/*",))
        if cline.is_dir()
        else first(root, (".clinerules",)),
    }


def imports(path: Path, root: Path, seen: set[Path], depth: int = 1):
    """[(depth, written, file)] for the @path imports a Claude file pulls in."""
    if depth > MAX_HOPS:
        return
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        if fenced:
            continue
        for m in IMPORT.finditer(re.sub(r"`[^`]*`", "", line)):
            target = (path.parent / m.group(1)).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                continue  # an import that leaves the folder isn't followed
            if target.is_file() and target not in seen:
                seen.add(target)
                yield depth, m.group(1), target
                yield from imports(target, root, seen, depth + 1)


def digest(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()[:12]


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from", "--at"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    src = [k for k in ("--box", "--from") if k in opts]
    if (
        args
        or len(src) != 1
        or not opts[src[0]]
        or ("--at" in opts and not opts["--at"])
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if src[0] == "--box":
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
    at = opts.get("--at", "")
    if Path(at).is_absolute() or ".." in Path(at).parts or not (root / at).is_dir():
        print(f"refused: {at} isn't a folder under {root}", file=sys.stderr)
        return kernel.REFUSED
    table = agents(root, folders(root, at))
    sums: dict[str, str] = {}
    top = root.resolve()
    total = 0
    for agent, files in table.items():
        print(agent)
        if not files:
            print("    (none)")
        n = 0
        for f in files:
            n += 1
            size, sha = digest(f)
            rel = f.relative_to(root).as_posix()
            sums[rel] = sha
            print(f"    {n:<2} {rel:<34} {size_of(size):>8}   sha256:{sha}")
            if agent == "claude-code" and f.suffix == ".md":
                for depth, written, target in imports(f, root, {f.resolve()}):
                    n += 1
                    size, sha = digest(target)
                    sums[target.relative_to(top).as_posix()] = sha
                    label = "  " * depth + f"@{written} (imported)"
                    print(f"    {n:<2} {label:<34} {size_of(size):>8}   sha256:{sha}")
        total += len(files)
    same: dict[str, list[str]] = {}
    for rel, sha in sums.items():
        same.setdefault(sha, []).append(rel)
    for names in same.values():
        if len(names) > 1:
            print(f"\nsame bytes: {', '.join(sorted(names))}")
    if not total:
        print("\nNo instruction file would load here.")
        return kernel.ESCALATE
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
