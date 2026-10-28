"""ci_memo.py: a gate whose inputs' bytes are unchanged keeps its verdict.

    python adapters/stdlib/ci-memo/ci_memo.py keys [GATE ...] [--repo DIR]
    python adapters/stdlib/ci-memo/ci_memo.py pin  --box DIR [--box DIR ...] --to FILE [--repo DIR]
    python adapters/stdlib/ci-memo/ci_memo.py plan --pin FILE [--repo DIR] [--bare]

A full `ci.py run` re-checks every add-on on every change, though most gates
read none of what changed. Each gate's verdict is a function of the bytes it
can reach, so this names that reach, hashes it to a key (each file's path and
SHA-256, sorted, as ci.py hashes the whole tree), and memoizes:

- `keys` says each gate's key now, and how many files are under it;
- `pin`, run after a full `ci.py run` on this same tree, writes FILE: each
  gate's key beside the verdict the record holds for it. It refuses a record
  with no run of this tree (every verdict row carries `files_sha256`, the
  tree it ran on), and a broken chain. A run cut into shards, each with its
  own record, is pinned whole by naming each record with its own `--box`;
  a gate in two of them takes the later one named;
- `plan` reads the pin against the tree as it is now. A gate whose key is
  unchanged stands, with the pinned verdict; one whose key changed, or that
  the pin doesn't hold, runs, and the line that runs just those is printed,
  for you to run. `--bare` prints only their names, for `ci.py run $(...)`.

A verdict that stands is the old run's, not a new pass: the same bytes gave
it, and the pin says which bytes. Three parts are never memoized, because
their verdicts reach past the tree, where no hash holds: `deps` (it
installs), `ports` and `tools` (what this machine has). A gate this tool
hasn't drawn the reach of is keyed on the whole tree, so it stands only when
nothing at all changed: over-run, never under-run. The reaches drawn narrow
(`lint`, the kernel's own tests, each add-on's mutants) are in `inputs`
here, each wide of the truth, and a rule that finds its folder empty falls
back to the whole tree.

It decides nothing: ci.py's record stays the receipt, the full run stays the
merge's evidence, and `plan` only says which rows of it the bytes still
cover. Exit codes, the kernel's: 0 every pinned gate stands and nothing need
run; 42 gates to run, printed; 2 refused.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

CI = Path(__file__).resolve().parents[1] / "ci" / "ci.py"
spec = importlib.util.spec_from_file_location("willow_ci_for_memo", CI)
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

ROOT = Path(__file__).resolve().parents[3]
#: parts whose verdicts reach past the tree, where no hash holds
NEVER = {"deps": "it installs", "ports": "it needs this machine's tools",
         "tools": "it reads this machine's PATH"}  # fmt: skip
#: the repo's own tools, whose tests read the whole tree (cards, docs, lists)
REPO_TOOLS = {"ci", "readme", "similar", "github"}


class Refused(Exception):
    pass


def files_of(root: Path) -> list[str]:
    """The tree's files, as ci.py counts them: every file git tracks or would
    track; in a folder git doesn't hold, every file not hidden."""
    if (root / ".git").exists():
        names = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root, capture_output=True, check=True,
        ).stdout.split(b"\0")  # fmt: skip
        return sorted(n.decode() for n in names if n and (root / n.decode()).is_file())
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and not any(part.startswith(".") for part in p.parts)
    )


def digests(root: Path) -> dict[str, str]:
    """Each file's SHA-256, by its path from the root."""
    return {
        f: hashlib.sha256((root / f).read_bytes()).hexdigest() for f in files_of(root)
    }


def key_of(paths, seen: dict[str, str]) -> str:
    """The paths and their bytes, hashed together as ci.py's `files_sha256`
    hashes the tree, so the same files give the same key anywhere."""
    h = hashlib.sha256()
    for f in sorted(paths):
        h.update(f.encode() + b"\0" + bytes.fromhex(seen[f]))
    return h.hexdigest()


def commands_mark(root: Path, files: list[str]) -> str:
    """What the contract test reads of every stdlib script without opening
    this add-on's own folder: each script's path, and whether it is one a
    person runs (it holds a `__main__` line), so a renamed script or one
    gaining a command line re-runs every add-on's mutants, as it should:
    the COMMANDS test runs in each of them."""
    lines = []
    for f in files:
        if f.startswith("adapters/stdlib/") and f.endswith(".py"):
            main = "__main__" in (root / f).read_text(encoding="utf-8", errors="ignore")
            lines.append(f"{f} {int(main)}")
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def inputs(gate: str, files: list[str]) -> list[str]:
    """The files a gate's verdict can depend on, each reach drawn wide of the
    truth, never narrow. A gate with no reach drawn here, a repo tool's
    mutants (their tests read the whole tree), and a rule that finds its
    folder empty all take every file, standing only when nothing changed."""
    part, _, name = gate.partition(":")
    if part == "lint":
        # ruff reads every .py and its config; CI's ruff pin is in the workflow
        return [f for f in files if f.endswith(".py")
                or f in ("ruff.toml", ".github/workflows/ci.yml")]  # fmt: skip
    if gate == "tests:beats":
        return ["kernel.py"]
    if gate == "tests:kernel":
        return ["kernel.py", "test_kernel.py"] + under("vectors/", files)
    if part == "mutants" and name not in REPO_TOOLS:
        own = under(f"adapters/stdlib/{name}/", files)
        if own:
            return (
                ["kernel.py", "<commands>"]
                + own
                + under("adapters/stdlib/ci/", files)
                + under("adapters/stdlib/mutants/", files)
            )
    return list(files)


def under(folder: str, files: list[str]) -> list[str]:
    return [f for f in files if f.startswith(folder)]


def keyed(names: list[str], root: Path) -> list[tuple[str, str, str, int]]:
    """(part, gate, key, files under it) for each gate, in ci.py's order;
    `names` narrows it. A name ci.py has no gate of is refused, so a gate
    spelled wrong never reads as unchanged."""
    every = [(part, gate) for part, gate, _ in ci.gates()]
    known = {g for _, g in every}
    for n in names:
        if n not in known:
            raise Refused(f"{n} isn't a gate of ci.py")
    seen = digests(root)
    files = sorted(seen)
    mark = commands_mark(root, files)
    out = []
    for part, gate in every:
        if names and gate not in names:
            continue
        paths = inputs(gate, files)
        real = [p for p in paths if p != "<commands>"]
        h = hashlib.sha256(key_of(real, seen).encode())
        if "<commands>" in paths:
            h.update(mark.encode())
        out.append((part, gate, h.hexdigest(), len(real)))
    return out


def do_keys(names: list[str], root: Path) -> int:
    rows = keyed(names, root)
    width = max(len(g) for _, g, _, _ in rows)
    for _, gate, key, n in rows:
        print(f"{gate:<{width}}  {key}  ({n} files)")
    return kernel.ALIVE


def do_pin(boxes: list[Path], to: Path, root: Path) -> int:
    seen = digests(root)
    tree = key_of(sorted(seen), seen)
    held = {}
    for box in boxes:
        if not (box / "kernel.json").exists():
            raise Refused(f"{box} is not a kernel box; run ci.py first")
        rows, breaks = kernel.read(box / "record.jsonl")
        if breaks:
            raise Refused(f"{box}: " + "; ".join(breaks))
        held.update(
            (r["gate"], r)
            for r in rows
            if r.get("kind") == "verdict" and r.get("files_sha256") == tree
        )
    if not held:
        raise Refused(
            "the record holds no run of this tree (no verdict's files_sha256"
            " matches it); run ci.py on it first"
        )
    if to.resolve().is_relative_to(root.resolve()):
        raise Refused("FILE is inside the tree; a pin in it would change the keys")
    if (to.parent / "kernel.json").exists():
        raise Refused("FILE is inside a box; a box is written only through the kernel")
    if to.exists():
        try:
            old = json.loads(to.read_text(encoding="utf-8"))
            if not ("gates" in old and "files_sha256" in old):
                raise ValueError
        except ValueError:
            raise Refused(f"{to} exists and is no pin; this replaces only its own")
    gates = {}
    for _, gate, key, _ in keyed([], root):
        if gate in held:
            gates[gate] = {"key": key, "state": held[gate]["state"]}
            if "why" in held[gate]:
                gates[gate]["why"] = held[gate]["why"]
    page = {
        "files_sha256": tree,
        "python": "{}.{}".format(*sys.version_info[:2]),
        "gates": gates,
    }
    to.write_text(
        json.dumps(page, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"pinned {len(gates)} gates to {to}")
    return kernel.ALIVE


def do_plan(pin: Path, root: Path, bare: bool) -> int:
    try:
        page = json.loads(pin.read_text(encoding="utf-8"))
        held, pinned_py = page["gates"], page["python"]
    except (OSError, ValueError, KeyError) as e:
        raise Refused(f"{pin} isn't a pin: {type(e).__name__}")
    py = "{}.{}".format(*sys.version_info[:2])
    stand, run = [], []
    for part, gate, key, _ in keyed([], root):
        if part in NEVER:
            run.append((gate, f"never memoized: {NEVER[part]}"))
        elif pinned_py != py:
            run.append((gate, f"pinned under python {pinned_py}, this is {py}"))
        elif gate not in held:
            run.append((gate, "not in the pin"))
        elif held[gate]["key"] != key:
            run.append((gate, "inputs changed"))
        else:
            stand.append((gate, held[gate]["state"], held[gate].get("why")))
    if bare:
        print(" ".join(g for g, _ in run))
        return kernel.ESCALATE if run else kernel.ALIVE
    width = max(len(g) for g, *_ in stand + run)
    for gate, state, why in stand:
        print(f"stand  {gate:<{width}}  {state}" + (f"  ({why})" if why else ""))
    for gate, reason in run:
        print(f"run    {gate:<{width}}  {reason}")
    print(f"{len(stand)} stand, {len(run)} to run")
    if not run:
        return kernel.ALIVE
    print()
    print("python adapters/stdlib/ci/ci.py run \\")
    print("    " + " ".join(g for g, _ in run) + " --box DIR")
    return kernel.ESCALATE


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    opts, args, boxes, it = {}, [], [], iter(rest)
    for a in it:
        if a == "--box":
            boxes.append(next(it, ""))
            opts[a] = boxes[-1]
        elif a in ("--to", "--repo", "--pin"):
            opts[a] = next(it, "")
        elif a == "--bare":
            opts[a] = "yes"
        else:
            args.append(a)
    root = Path(opts["--repo"]) if opts.get("--repo") else ROOT
    bad = (
        any(a.startswith("-") for a in args)
        or not root.is_dir()
        or (
            verb == "pin"
            and (args or not all(boxes) or not boxes or not opts.get("--to"))
        )
        or (verb == "plan" and (args or not opts.get("--pin")))
        or verb not in ("keys", "pin", "plan")
    )
    if bad:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        if verb == "keys":
            return do_keys(args, root)
        if verb == "pin":
            return do_pin([Path(b) for b in boxes], Path(opts["--to"]), root)
        return do_plan(Path(opts["--pin"]), root, "--bare" in opts)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
