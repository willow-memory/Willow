"""assemble.py: a willow stack, put together from this willow one add-on at
a time, each addition a row on the stack's own kernel record. The UI's
(canvas.py) other half, and a command line of its own. Python 3.9+, stdlib.

    python ui/assemble.py init    [--pin FILE] [--to DIR]
    python ui/assemble.py add     NAME... [--to DIR] [--python EXE]
    python ui/assemble.py refresh NAME... [--to DIR]
    python ui/assemble.py status  [--to DIR]
    python ui/assemble.py check   [--to DIR]
    python ui/assemble.py vectors [--to DIR]

A stack lives in --to, ~/willow-stack unless you say, and never inside this
repository:

    stack/            kernel.py, CONSTITUTION.md, vectors/cases.json and
                      adapters/stdlib/<name>/, laid out as in willow, so
                      every add-on finds the kernel where it looks
    stack/STACK.json  what is here: willow's commit, each file's SHA-256,
                      each add-on's card promises and what it leans on
    box/              the stack's own kernel record; its pile is stack/
    keys/stack.key    the record's key, outside the box

`init` makes one from this willow (`--pin` refuses a kernel.py the pin file
doesn't name). `add` copies an add-on and every add-on its card `uses`, and
theirs; one it only `looks-for` is listed as absent, with who wants it. An
add-on that `runs-in: repo` is refused: it works on willow's own repository.
Each one added gets its contract check (no arguments: refused, exit 2) and
its own tests, if --python names an interpreter with pytest; else its tests
are `unreachable`, said. `refresh` copies a piece again from this willow as
it is now. `vectors` puts the kernel's vectors into a stack made before they
were carried. `check` re-hashes every file against STACK.json.

Exit codes, the kernel's: 0 done; 42 something absent or unreachable; 2
refused, or a file changed since it was put in.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # never a __pycache__ in a stack, or in this repo
ALIVE, ESCALATE, REFUSED = 0, 42, 2
#: the willow this file is part of: what a stack is made from
WILLOW = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
HARD = re.compile(
    r"sys\.path\.insert\(.*?/\s*[\"']([a-z0-9-]+)[\"']"
)  # every spelling: HERE.parent, STDLIB, parents[1]
SOFT = re.compile(
    r"sibling\(\s*\"([a-z0-9-]+)\"|STDLIB\s*/\s*[\"']([a-z0-9-]+)[\"']|piece\([^,]+,\s*\"([a-z0-9-]+)\""
)
HEADER = re.compile(r"<!--\s*willow-addon\s*\n(.*?)-->", re.S)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def paths(to: Path):
    return (
        to / "stack",
        to / "box",
        to / "keys" / "stack.key",
        to / "stack" / "STACK.json",
    )


def load_kernel(stack: Path):
    sys.path.insert(0, str(stack))
    import kernel  # noqa: E402

    return kernel


def manifest(stack: Path) -> dict:
    return json.loads((stack / "STACK.json").read_text(encoding="utf-8"))


def save(stack: Path, m: dict) -> None:
    (stack / "STACK.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")


def card(folder: Path) -> dict:
    f = folder / "README.md"
    if not f.is_file():
        return {}
    got = HEADER.search(f.read_text(encoding="utf-8"))
    if not got:
        return {}
    out = {}
    for line in got.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep:
            out[k.strip()] = v.strip()
    return out


def deps(folder: Path) -> tuple[list[str], list[str]]:
    """(uses, looks-for): from the card when it says (willow's cards name
    what they lean on, and CI holds the code to them), else read from the
    code, for a willow from before cards said."""
    c = card(folder)
    if (
        "uses" in c
        or "looks-for" in c
        or "runs-in" in c
        or (folder.parents[2] / "adapters" / "stdlib" / "ci" / "alone.py").is_file()
    ):
        split = lambda v: sorted(x.strip() for x in v.split(",") if x.strip())  # noqa: E731
        return split(c.get("uses", "")), split(c.get("looks-for", ""))
    return code_deps(folder)


def code_deps(folder: Path) -> tuple[list[str], list[str]]:
    hard, soft = set(), set()
    for py in sorted(folder.glob("*.py")):
        if py.name.startswith("test_"):
            continue
        for line in py.read_text(encoding="utf-8").splitlines():
            if "sys.path.insert" in line:
                named = re.findall(r"[\"']([a-z0-9-]+)[\"']", line.split("#")[0])
                if named and HARD.search(
                    line
                ):  # ROOT / "adapters" / "stdlib" / "scan": the last one
                    hard.add(named[-1])
                continue
            for groups in SOFT.findall(line):
                soft |= {g for g in groups if g}
    me = folder.name
    return sorted(hard - {me}), sorted(soft - hard - {me})


def init(willow: Path, to: Path, pin: Path | None) -> int:
    stack, box, key, _ = paths(to)
    if (stack / "STACK.json").exists():
        print(f"refused: {stack} is already a stack", file=sys.stderr)
        return REFUSED
    src = willow / "kernel.py"
    if not src.is_file():
        print(f"refused: no kernel.py in {willow}", file=sys.stderr)
        return REFUSED
    commit = subprocess.run(["git", "-C", str(willow), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()  # fmt: skip
    dirty = subprocess.run(["git", "-C", str(willow), "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip() != ""  # fmt: skip
    pinned = None
    if pin is not None:
        want = json.loads(pin.read_text(encoding="utf-8"))["sha256"]
        pinned = want == sha(src)
        if not pinned:
            print(
                f"refused: willow's kernel.py isn't the one {pin} pins", file=sys.stderr
            )
            return REFUSED
    (stack / "adapters" / "stdlib").mkdir(parents=True)
    shutil.copy2(src, stack / "kernel.py")
    law = (
        willow / "CONSTITUTION.md"
    )  # the law: neither kernel nor add-on, and the loop refuses without it
    if law.is_file():
        shutil.copy2(law, stack / "CONSTITUTION.md")
    key.parent.mkdir(parents=True, exist_ok=True)
    save(stack, {"willow": str(willow), "commit": commit, "dirty": dirty,
                 "kernel": sha(stack / "kernel.py"), "pinned": pinned, "addons": {},
                 "law": sha(stack / "CONSTITUTION.md") if law.is_file() else None})  # fmt: skip
    kernel = load_kernel(stack)
    code = kernel.main(
        ["init", "--box", str(box), "--pile", str(stack), "--key", str(key)]
    )
    if code != ALIVE:
        return code
    kernel.append(box, kernel.now(), "assemble", who="assembler", piece="kernel",
                  source=commit, dirty=dirty, sha256=sha(stack / "kernel.py"),
                  pinned=pinned)  # fmt: skip
    if law.is_file():
        kernel.append(
            box,
            kernel.now(),
            "assemble",
            who="assembler",
            piece="law",
            source=commit,
            sha256=sha(stack / "CONSTITUTION.md"),
        )
    kernel_contract(stack, willow, box, commit)
    print(f"stack at {stack}: kernel.py from willow {commit[:7]}"
          f"{' (dirty tree)' if dirty else ''}{', matches the pin' if pinned else ''}")  # fmt: skip
    return ALIVE


def kernel_contract(stack: Path, willow: Path, box: Path, commit: str) -> str:
    """The kernel's contract, vectors/cases.json, beside kernel.py as willow
    keeps it: the tests that hold an add-on to the kernel's answers read it."""
    src, dst = willow / "vectors" / "cases.json", stack / "vectors" / "cases.json"
    if dst.is_file():
        return "already here"
    if not src.is_file():
        return "unreachable: willow has no vectors/cases.json"
    dst.parent.mkdir(exist_ok=True)
    shutil.copy2(src, dst)
    m = manifest(stack)
    m["vectors"] = sha(dst)
    save(stack, m)
    kernel = load_kernel(stack)
    kernel.append(box, kernel.now(), "assemble", who="assembler", piece="vectors",
                  source=commit, sha256=sha(dst))  # fmt: skip
    return "put in"


def contract(stack: Path, folder: Path) -> str:
    mains = [p for p in sorted(folder.glob("*.py")) if not p.name.startswith("test_")]
    if not mains:
        return "unreachable: no script"
    r = subprocess.run([sys.executable, str(mains[0])], cwd=stack, capture_output=True,
                       stdin=subprocess.DEVNULL, timeout=60, env=ENV)  # fmt: skip
    return "held" if r.returncode == REFUSED else f"broken: exit {r.returncode}, not 2"


def tests(stack: Path, folder: Path, python: str | None) -> dict:
    if not list(folder.glob("test_*.py")):
        return {"state": "unreachable", "why": "no tests in the folder"}
    if python is None:
        return {"state": "unreachable", "why": "no --python with pytest given"}
    r = subprocess.run([python, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        str(folder.relative_to(stack))], cwd=stack,
                       capture_output=True, text=True, timeout=900, env=ENV)  # fmt: skip
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    return {"state": "passed" if r.returncode == 0 else "failed", "exit": r.returncode,
            "tail": tail}  # fmt: skip


def add(names: list[str], to: Path, python: str | None) -> int:
    stack, box, _, _ = paths(to)
    m = manifest(stack)
    willow = Path(m["willow"])
    kernel = load_kernel(stack)
    todo, why = list(names), {n: "asked" for n in names}
    worst = ALIVE
    copied: list[tuple[str, Path, list[str], list[str]]] = []
    while todo:  # first every copy, so a check never runs short of a hard sibling
        name = todo.pop(0)
        if name in m["addons"]:
            continue
        src = willow / "adapters" / "stdlib" / name
        if src.is_dir() and card(src).get("runs-in") == "repo":
            print(f"refused: {name} works on willow's own repository; it isn't copied out of it",
                  file=sys.stderr)  # fmt: skip
            return REFUSED
        if not src.is_dir():
            if (willow / "adapters" / "deps" / name).is_dir():
                print(f"refused: {name} is a deps add-on; this base stack is stdlib only",
                      file=sys.stderr)  # fmt: skip
            else:
                print(f"refused: willow has no add-on {name}", file=sys.stderr)
            return REFUSED
        dst = stack / "adapters" / "stdlib" / name
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        hard, soft = deps(dst)
        for h in hard:
            if h not in m["addons"] and h not in todo:
                todo.append(h)
                why[h] = f"imported by {name}"
        copied.append((name, dst, hard, soft))
    for name, dst, hard, soft in copied:
        files = {
            str(p.relative_to(dst)): sha(p)
            for p in sorted(dst.rglob("*"))
            if p.is_file()
        }
        c = card(dst)
        entry = {"why": why[name], "hard": hard, "soft": soft, "files": files,
                 "card": {k: c.get(k) for k in ("section", "line", "source", "writes",
                                                "network")},
                 "contract": contract(stack, dst), "tests": tests(stack, dst, python)}  # fmt: skip
        m["addons"][name] = entry
        save(stack, m)
        kernel.append(box, kernel.now(), "assemble", who="assembler", piece=name,
                      source=m["commit"], why=entry["why"], hard=hard, soft=soft,
                      files=hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
                      writes=entry["card"]["writes"], network=entry["card"]["network"],
                      contract=entry["contract"], tests=entry["tests"]["state"])  # fmt: skip
        t = entry["tests"]
        print(f"+ {name:<14} {entry['why']:<24} contract {entry['contract']:<8} "
              f"tests {t['state']}{': ' + t.get('tail', t.get('why', '')) if t['state'] != 'passed' else ''}")  # fmt: skip
        if entry["contract"] != "held" or t["state"] == "failed":
            worst = REFUSED if t["state"] == "failed" else max(worst, ESCALATE)
        elif t["state"] == "unreachable":
            worst = max(worst, ESCALATE) if worst != REFUSED else worst
    return worst


def refresh(names: list[str], to: Path) -> int:
    """A piece copied again from willow, as it is there now: its files, hashes
    and siblings re-read, one `refresh` row each. Only what's already here."""
    stack, box, _, _ = paths(to)
    m = manifest(stack)
    willow = Path(m["willow"])
    kernel = load_kernel(stack)
    commit = subprocess.run(["git", "-C", str(willow), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()  # fmt: skip
    for name in names:
        if name not in m["addons"]:
            print(f"refused: {name} isn't in this stack; add it", file=sys.stderr)
            return REFUSED
    for name in names:
        dst = stack / "adapters" / "stdlib" / name
        shutil.rmtree(dst)
        shutil.copytree(willow / "adapters" / "stdlib" / name, dst,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))  # fmt: skip
        files = {str(p.relative_to(dst)): sha(p) for p in sorted(dst.rglob("*"))
                 if p.is_file() and "__pycache__" not in p.parts}  # fmt: skip
        was = m["addons"][name]["files"]
        hard, soft = deps(dst)
        m["addons"][name].update(files=files, hard=hard, soft=soft, source=commit)
        save(stack, m)
        moved = sorted(f for f in set(files) | set(was) if files.get(f) != was.get(f))
        kernel.append(box, kernel.now(), "refresh", who="assembler", piece=name, source=commit,
                      changed=moved)  # fmt: skip
        print(
            f"~ {name:<14} from willow {commit[:7]}: {', '.join(moved) or 'nothing changed'}"
        )
    return ALIVE


def status(to: Path) -> int:
    stack, box, _, _ = paths(to)
    m = manifest(stack)
    kernel = load_kernel(stack)
    print(f"willow {m['commit'][:7]}{' (dirty)' if m['dirty'] else ''}; "
          f"kernel {m['kernel'][:12]}; {len(m['addons'])} add-ons")  # fmt: skip
    absent: dict[str, list[str]] = {}
    for name, e in sorted(m["addons"].items()):
        c = e["card"]
        print(f"  {name:<14} writes {c['writes'] or '?':<14} network {c['network'] or '?':<8} "
              f"hard {','.join(e['hard']) or '-'}")  # fmt: skip
        for s in e["soft"]:
            if s not in m["addons"]:
                absent.setdefault(s, []).append(name)
    if absent:
        print("absent, looked for and done without:")
        for s, by in sorted(absent.items()):
            print(f"  {s:<14} wanted by {', '.join(by)}")
    code = kernel.main(["verify", "--box", str(box)])
    return code if code != ALIVE else (ESCALATE if absent else ALIVE)


def check(to: Path) -> int:
    stack, _, _, _ = paths(to)
    m = manifest(stack)
    moved = [] if sha(stack / "kernel.py") == m["kernel"] else ["kernel.py"]
    if m.get("law") and sha(stack / "CONSTITUTION.md") != m["law"]:
        moved.append("CONSTITUTION.md")
    if m.get("vectors") and sha(stack / "vectors" / "cases.json") != m["vectors"]:
        moved.append("vectors/cases.json")
    for name, e in m["addons"].items():
        d = stack / "adapters" / "stdlib" / name
        now = {str(p.relative_to(d)): sha(p) for p in sorted(d.rglob("*"))
               if p.is_file() and "__pycache__" not in p.parts}  # fmt: skip
        if now != e["files"]:
            moved.append(name)
    for x in moved:
        print(f"drift: {x}")
    if not moved:
        print("every file is the one assembled")
    return REFUSED if moved else ALIVE


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return REFUSED
    verb, rest = argv[0], argv[1:]
    opts: dict[str, str] = {}
    names: list[str] = []
    it = iter(rest)
    for a in it:
        if a in ("--pin", "--to", "--python"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            print(f"refused: unknown option {a}", file=sys.stderr)
            return REFUSED
        else:
            names.append(a)
    to = Path(opts.get("--to") or Path.home() / "willow-stack").expanduser()
    if to.resolve().is_relative_to(WILLOW.resolve()):
        print(
            f"refused: keep a stack outside this repository, not in {to}",
            file=sys.stderr,
        )
        return REFUSED
    if verb == "init" and not names and "--willow" not in opts:
        pin = Path(opts["--pin"]) if opts.get("--pin") else None
        return init(WILLOW, to, pin)
    if verb == "add" and names:
        return add(names, to, opts.get("--python"))
    if verb == "refresh" and names:
        return refresh(names, to)
    if verb == "status" and not names:
        return status(to)
    if verb == "check" and not names:
        return check(to)
    if verb == "vectors" and not names:
        stack, box, _, _ = paths(to)
        m = manifest(stack)
        said = kernel_contract(stack, Path(m["willow"]), box, m["commit"])
        print(f"vectors/cases.json: {said}")
        return ALIVE if said in ("put in", "already here") else ESCALATE
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
