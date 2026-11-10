"""ready.py: a branch made ready for its pull request, on no host. Python 3.9+.

    python adapters/stdlib/ready/ready.py steps  [--steps FILE]
    python adapters/stdlib/ready/ready.py check  --base REF
    python adapters/stdlib/ready/ready.py run    --base REF [--open REF]... [--steps FILE] [--to FILE]
    python adapters/stdlib/ready/ready.py body   --base REF --from FILE [--footer TEXT]
    python adapters/stdlib/ready/ready.py opened --base REF --pr N [--steps FILE] [--to FILE]

Everything a pull request needs before and after it opens that no host has
to answer. REF is the branch it goes into as this checkout has it
(origin/main): fetch it first. The steps are steps.md beside this (`--steps`
names another), a stack, the same file the stack add-on reads, run in order
rather than composed.

    steps   the steps, pool by pool: what `run` and `opened` would run
    check   what stops a branch before anything runs: not on a branch, on
            REF's own branch, uncommitted changes, nothing REF doesn't
            have (each refused), or a change that owes a changelog
            fragment and has none (42)
    run     check, then every pool but "after it opens", in order, from the
            repo's root. A step that exits 0 is done; a 42 that owes
            nothing (no other pull request given, no add-on a person runs)
            is noted and passed; any other exit stops the run there, and
            so does a collision `against` names. What a step leaves changed
            is committed as `tidy:`. `--open` names each other open pull
            request's branch, for `{open}`; `--to` keeps what each step
            printed, for `body`
    body    the pull request's body, the template's four sections, printed:
            the commits' messages, each touched add-on's card promises,
            what each step printed (from `--from`, as `run --to` kept it),
            and what was left to CI
    opened  once it has number N: each changes/+<branch>.<kind>.md renamed
            changes/N.<kind>.md and committed, then the "after it opens"
            pool, its steps' output added to `--to`

A step's args fill `{base}` with REF, `{branch}` with this branch,
`{scratch}` with a folder of the run's own, `{open}` with the `--open`
branches, and `{pr}` with N.

It never pushes, never asks a host anything, and never rebases, amends or
force-pushes: create_pr.py (adapters/stdlib/github) does the host's part
around it, and without a host it is run by hand. It writes no file but
`--to` and a fragment's new name; every other change is a step's, committed.
Exit codes, the kernel's: 0 done; 42 something needs you (a step that
failed or stopped, a missing fragment), it says what; 2 refused.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STDLIB = HERE.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STEPS = HERE / "steps.md"
USAGE = (
    "usage: ready.py steps [--steps FILE] | check --base REF"
    " | run --base REF [--open REF]... [--steps FILE] [--to FILE]"
    " | body --base REF --from FILE [--footer TEXT]"
    " | opened --base REF --pr N [--steps FILE] [--to FILE]"
)
#: the pool whose steps need the pull request's number
AFTER = "after it opens"
#: a step's 42 that owes nothing: noted for the body, not stopped on
FINE_42 = {"restack", "test-impact.impact", "against", "ci.realdata"}
#: a line that stops a step which exited 0: (step, the line's start, why)
STOP_ON = {
    "against": (
        "collides:",
        "it collides with another open pull request: merge that one's branch"
        " in and base on it (CONTRIBUTING.md, Pull requests)",
    )
}
#: the template's sections, in its order
SECTIONS = (
    "What this changes, and why",
    "Its promises",
    "Evidence",
    "What you didn't check",
)
#: a commit made here is the run's own, not the change's
MINE = re.compile(r"^(tidy: |changelog: its number )")
TRAILER = re.compile(r"^(Co-Authored-By|Claude-Session|Signed-off-by): ", re.I)
TAIL = 15
#: each verb's options: those it needs, and those it may take
NEEDS = {
    "steps": ((), ("--steps",)),
    "check": (("--base",), ()),
    "run": (("--base",), ("--open", "--steps", "--to")),
    "body": (("--base", "--from"), ("--footer",)),
    "opened": (("--base", "--pr"), ("--steps", "--to")),
}


class Stop(Exception):
    """Something a person has to look at: exit 42."""


class Refused(Exception):
    """The command line, or where it was run: exit 2."""


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def changelog():
    return load("willow_changelog_for_ready", STDLIB / "ci" / "changelog.py")


def git(*args: str, check: bool = True) -> str:
    got = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and got.returncode != 0:
        raise Stop(f"git {' '.join(args)}: {(got.stderr or got.stdout).strip()}")
    return got.stdout.strip() if got.returncode == 0 else ""


def clean() -> bool:
    return git("status", "--porcelain") == ""


# ── the steps ────────────────────────────────────────────────────────────────
def script_of(name: str) -> Path:
    """`ci.bugs` is adapters/stdlib/ci/bugs.py; `readme` is readme/readme.py
    (a dash in the folder's name is an underscore in the script's)."""
    folder, _, file = name.partition(".")
    path = STDLIB / folder / f"{file or folder.replace('-', '_')}.py"
    if not path.is_file():
        raise Refused(f"a step names {name}, and there is no {path.relative_to(ROOT)}")
    return path


def steps(path: Path) -> list[tuple[str, list[tuple[str, list[str]]]]]:
    stack = load("willow_stack_for_ready", STDLIB / "stack" / "stack.py")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise Refused(f"can't read {path}: {e}") from e
    pools, error = stack.parse_stack(text)
    if error:
        raise Refused(f"{path.name}: {error}")
    for _, ss in pools:
        for name, _ in ss:
            script_of(name)
    return pools


def fill(args: list[str], fields: dict) -> list[str]:
    out = []
    for a in args:
        if a == "{open}":
            out += fields["open"]
            continue
        for k, v in fields.items():
            if k != "open":
                a = a.replace("{" + k + "}", str(v))
        out.append(a)
    return out


def run_step(name: str, args: list[str], said: list, notes: list) -> None:
    """One step: done, noted in `notes`, or Stop. A change it leaves is
    committed as tidy."""
    print(f"\n── {name} {' '.join(args)}", flush=True)
    got = subprocess.run(
        [sys.executable, str(script_of(name)), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    out = (got.stdout + got.stderr).rstrip()
    print(out, flush=True)
    said.append([name, args, got.returncode, out])
    last = out.splitlines()[-1] if out else "(it printed nothing)"
    if got.returncode == kernel.ESCALATE and name in FINE_42:
        # the line that says why (a gate's verdict), not a closing line
        why = [x.strip() for x in out.splitlines() if " unreachable " in f" {x} "]
        notes.append(f"`{name}` came back 42: {'; '.join(why) or last}")
    elif got.returncode != kernel.ALIVE:
        raise Stop(f"{name} exited {got.returncode}: {last}")
    stop = STOP_ON.get(name)
    if stop and any(line.startswith(stop[0]) for line in out.splitlines()):
        raise Stop(f"{name}: {stop[1]}")
    if not clean():
        git("add", "-A")
        git("commit", "-q", "-m", f"tidy: made again by {name} {' '.join(args)}")
        print(f"(committed what {name} made, as tidy)")


def run_pools(pools, after: bool, fields: dict, said: list, notes: list) -> None:
    for heading, ss in pools:
        if (heading == AFTER) == after:
            for name, args in ss:
                run_step(name, fill(args, fields), said, notes)


# ── the changelog ────────────────────────────────────────────────────────────
def changed(base: str) -> list[str]:
    return [f for f in git("diff", "--name-only", f"{base}...HEAD").split("\n") if f]


def new_fragments(base: str) -> list[str]:
    """The changelog fragments this branch added under changes/, towncrier's
    shape (changes/README.md), that are there now."""
    log = changelog()
    return [f for f in changed(base) if log.FRAGMENT.match(f) and (ROOT / f).is_file()]


def name_fragments(base: str, number: int) -> list[str]:
    """Each `+<branch>.<kind>.md` fragment this branch added, renamed for the pull
    request, `<number>.<kind>.md` (`.1`, `.2` when a kind is there already): towncrier
    writes `(#N)` from the name. The new names."""
    log = changelog()
    out = []
    for rel in new_fragments(base):
        m = log.FRAGMENT.match(rel)
        if not m.group(1).startswith("+"):
            continue
        kind, k = m.group(2), 0
        new = f"changes/{number}.{kind}.md"
        while (ROOT / new).exists():
            k += 1
            new = f"changes/{number}.{kind}.{k}.md"
        git("mv", rel, new)
        out.append(new)
    return out


# ── the body ─────────────────────────────────────────────────────────────────
def commits(base: str) -> list[tuple[str, str]]:
    """(subject, body) of the change's own commits, oldest first, trailers
    and the run's own tidy and number commits left out."""
    raw = git(
        "log", "--reverse", "--no-merges", "--format=%s%x00%b%x1e", f"{base}..HEAD"
    )
    out = []
    for rec in raw.split("\x1e"):
        if not rec.strip():
            continue
        subject, _, body = rec.strip("\n").partition("\x00")
        if MINE.match(subject):
            continue
        body = "\n".join(x for x in body.strip().split("\n") if not TRAILER.match(x))
        out.append((subject, body.strip()))
    return out


def promises(base: str) -> list[str]:
    seen, out = set(), []
    for f in changed(base):
        m = re.match(r"adapters/(stdlib|deps)/([^/]+)/", f)
        if not m or m.group(2) in seen:
            continue
        seen.add(m.group(2))
        card = ROOT / m.group(0) / "README.md"
        head = (
            card.read_text(encoding="utf-8").split("-->")[0] if card.is_file() else ""
        )
        field = {
            k: v.strip() for k, v in re.findall(r"^(writes|network): (.*)$", head, re.M)
        }
        out.append(f"- `{m.group(2)}`: writes {field.get('writes', '(no card)')};"
                   f" network {field.get('network', '(no card)')}")  # fmt: skip
    return out


def body(base: str, said: list, notes: list, footer: str) -> str:
    what = "\n\n".join(f"**{s}**" + (f"\n\n{b}" if b else "") for s, b in commits(base))
    kept = promises(base)
    evidence = "\n\n".join(
        f"`{name} {' '.join(args)}`: exit {code}\n\n```\n"
        + "\n".join(out.splitlines()[-TAIL:])
        + "\n```"
        for name, args, code, out in said
    )
    left = notes + [
        "Every gate this change doesn't reach here runs in CI on this pull request."
    ]
    parts = [
        (SECTIONS[0], what or "(no commit message says)"),
        (SECTIONS[1], "\n".join(kept) or "It touches no add-on."),
        (SECTIONS[2], f"Made by ready.py, on {git('rev-parse', '--short', 'HEAD')}:\n\n{evidence}"),
        (SECTIONS[3], "\n".join(f"- {n}" for n in left)),
    ]  # fmt: skip
    text = "\n\n".join(f"## {h}\n\n{t}" for h, t in parts)
    return text + (f"\n\n{footer}" if footer else "") + "\n"


# ── the verbs ────────────────────────────────────────────────────────────────
def args_of(argv: list[str]) -> tuple[str, dict]:
    if not argv or argv[0] not in NEEDS:
        raise Refused(USAGE)
    verb, (need, may) = argv[0], NEEDS[argv[0]]
    opts: dict = {"--open": []}
    it = iter(argv[1:])
    for a in it:
        value = next(it, None)
        if a not in need + may or value is None or value in need + may:
            raise Refused(USAGE)
        if a == "--open":
            opts[a].append(value)
        elif a in opts:
            raise Refused(USAGE)
        else:
            opts[a] = value
    if any(n not in opts for n in need):
        raise Refused(USAGE)
    if "--pr" in opts and not opts["--pr"].isdigit():
        raise Refused(USAGE)
    return verb, opts


def check(base: str) -> str:
    """The branch, once nothing stops it."""
    branch = git("symbolic-ref", "-q", "--short", "HEAD", check=False)
    if not branch:
        raise Refused("not on a branch: check out the one to open")
    name = base.split("/", 1)[1] if base.startswith("origin/") else base
    if branch == name:
        raise Refused(f"on {name} itself: a pull request comes from a branch of its own")  # fmt: skip
    if not clean():
        raise Refused("uncommitted changes: commit the change, entry and all, first")
    if not git("rev-parse", "-q", "--verify", f"{base}^{{commit}}", check=False):
        raise Refused(f"no {base} here: fetch it first")
    if git("rev-list", "--count", f"{base}..HEAD") == "0":
        raise Refused(f"{branch} holds nothing {base} doesn't: nothing to open")
    if changelog().owed(changed(base)) and not new_fragments(base):
        raise Stop("no changelog entry: write it in changes/+<branch>.<kind>.md"
                   " (changes/README.md says how; <kind> added, changed, fixed or"
                   " removed), commit it, run this again")  # fmt: skip
    return branch


def keep(to: str | None, said: list, notes: list) -> None:
    if not to:
        return
    path = Path(to)
    if not path.parent.is_dir():
        raise Refused(f"no folder {path.parent} for --to")
    path.write_text(json.dumps({"said": said, "notes": notes}, indent=1) + "\n",
                    encoding="utf-8")  # fmt: skip


def kept(path: str) -> tuple[list, list]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return list(data["said"]), list(data["notes"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise Refused(f"can't read {path} as run --to keeps it: {e}") from e


def verb(name: str, opts: dict) -> int:
    pools = (
        steps(Path(opts.get("--steps", STEPS))) if "--steps" in NEEDS[name][1] else []
    )
    if name == "steps":
        for heading, ss in pools:
            print(f"## {heading}")
            for step, args in ss:
                print(f"- {step} -- {' '.join(args)}")
        return kernel.ALIVE
    base = opts["--base"]
    if name == "body":
        said, notes = kept(opts["--from"])
        print(body(base, said, notes, opts.get("--footer", "")), end="")
        return kernel.ALIVE
    if name == "check":
        print(f"{check(base)} is ready to run its steps against {base}")
        return kernel.ALIVE
    said, notes = kept(opts["--to"]) if name == "opened" and opts.get("--to") and Path(opts["--to"]).is_file() else ([], [])  # fmt: skip
    branch = check(base) if name == "run" else git("symbolic-ref", "-q", "--short", "HEAD")  # fmt: skip
    with tempfile.TemporaryDirectory() as scratch:
        fields = {"base": base, "branch": branch, "scratch": scratch, "open": opts["--open"]}  # fmt: skip
        try:
            if name == "opened":
                number = int(opts["--pr"])
                named = name_fragments(base, number)
                if named:
                    git("add", "-A", "changes")
                    git("commit", "-q", "-m", f"changelog: its number (#{number})")
                    for new in named:
                        print(f"named its changelog fragment {new}")
                fields["pr"] = number
            run_pools(pools, name == "opened", fields, said, notes)
        finally:
            keep(opts.get("--to"), said, notes)
    print(f"\n{branch}: every step done")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    try:
        return verb(*args_of(argv))
    except Refused as why:
        print(f"refused: {why}" if str(why) != USAGE else USAGE, file=sys.stderr)
        return kernel.REFUSED
    except Stop as why:
        print(f"\nstopped: {why}", file=sys.stderr)
        return kernel.ESCALATE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
