"""trace.py: one add-on's command run on one pile under the guard, and one row of what was seen: not what its card says.

    python demo/pools/trace/trace.py pile --pile PILE --name NAME --salt SALT --work DIR --to ROWS
        [--only STEP]... [--timeout SECONDS]
    python demo/pools/trace/trace.py stack --grid MANIFEST --stack ID [--stack ID]...
        --pile PILE --name NAME --salt SALT --work DIR --to ROWS [--timeout SECONDS]
        [--memo DIR [--never FILE] [--check FRACTION]]

PILE is a folder of files; NAME is what the rows call it. A box is made
over it once, under a key made for the run. Then each add-on that has a
command line (COMMANDS and DEPS_COMMANDS in the contract test, the
table the grid takes its steps from) is run alone: on a copy of that
box, so every step meets the same record; with a scratch folder of its
own; under the add-on guard, so it cannot change the pile and a write
its card does not promise is refused and said. One line a step is added
to ROWS:

    step, pile        which add-on, on which pile
    card, code        the SHA-256 of its card and of its code (tests left out)
    manifest          the SHA-256 of the pile's files, paths and bytes
    exit, seconds     how it ended (the kernel's codes), and how long it took;
                      a step past the timeout is `timed_out`
    state             a report's own word (populated, empty, unreachable),
                      or none when what it printed is no report
    lines, out        how many lines it printed, and their SHA-256 with the
                      run's own folders and any time of day taken out, so
                      one step's output can be held to another run of it
    rows              the kinds of row it added to the record, each counted
    wrote             the files it left in its scratch folder, counted by
                      suffix, and how many of them are a mirror's map
    places, files     the places in the pile its output names, each as a
                      hash with the pile's salt: a file and line, mapped
                      back through a mirror's map to the original where
                      there is one; and the same at the level of the file
    mapped            how many of those places went through a map
    breaches          what the guard refused, if anything
    refusal_names     for a step that refused (exit 2): whether what it said
                      names a path in the pile or in its scratch folder, so
                      "takes a file that isn't here" is told from the rest

Nothing of the pile's words is kept: a row holds counts, hashes and the
add-on's name. SALT is the pile's own, so one pile's place hashes say
nothing of another's. A place is seen only when the output names a
file of the pile as one word (a path with a space in it is missed), so
the places are a floor, not a count.

`stack` runs stacks of the grid (MANIFEST is the manifest.json that
demo/pools/grid/grid.py writes): each on a box of its own that carries
on from step to step, in the order the stack lists, each step's
scratch folder beside the others' so a later step can be given what an
earlier one left. The row is the same, with the stack and where in it
the step came.

`--memo DIR` is the run memory: a step whose every read is as it was the
last time it ran is not run again, and its row and the files it left are
taken from that time. What a step reads is said by memo/sitecustomize.py,
which the step runs under before the guard: each file it opened to read,
each folder it listed, each database it connected to, as a hash of what
was there. A read of the pile, the box or the stack's scratch folders
counts; one of the step's own folder, the code, or anything else on the
machine (the same for every step of one run) does not. A step is never
remembered when it added a row to the record (the record chains, so a
row can't be replayed), changed the box, started a program that isn't
Python (whose reads can't be seen), timed out, breached the guard, or is
named in `--never` (a JSON list: the steps stage 0 found unsteady).
`--check` (0.05 unless given) is the share of remembered steps run anyway,
drawn by the stack and place, and held to what was remembered: a row says
`memo`: ran, reused, checked (with `memo_same`), or never. DIR may be
there already, so one memory serves several calls on one pile; it must
be outside this repository too.

DIR is made, and must be outside this repository. Exit codes, the
kernel's: 0 every step traced; 2 refused (a bad command line, a pile
that isn't a folder, a DIR inside the repository, a step that isn't
one, or a pile that changed while it was traced).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CI = ROOT / "adapters" / "stdlib" / "ci"
USAGE = __doc__.split("\n\n")[1]
REPORT = re.compile(r"^[a-z0-9-]+: (populated|empty|unreachable)\b")
TRIM = ",;()[]{}<>\"'`"
WHEN = re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d:?\d\d)?")


def steady(out: str, fill: dict[str, str], mine: Path) -> str:
    """What was printed with what differs from run to run for no reason of
    the add-on's taken out: the run's own folders, and the time of day."""
    for path, word in ((str(mine), "{mine}"), (fill["tmp"], "{tmp}"), (fill["box"], "{box}"),
                       (fill["pile"], "{pile}")):  # fmt: skip
        out = out.replace(path, word)
    return WHEN.sub("{when}", out)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def contract():
    spec = importlib.util.spec_from_file_location(
        "contract_for_trace", CI / "test_contract.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def table(mod) -> dict[str, tuple[Path, list[str]]]:
    """{step: (its script, its command line with {box}, {pile} and {tmp})}."""
    out = {}
    for kind, commands in (
        ("stdlib", mod.COMMANDS),
        ("deps", getattr(mod, "DEPS_COMMANDS", {})),
    ):
        for name, (script, argv) in commands.items():
            out[name] = (ROOT / "adapters" / kind / name / script, list(argv))
    return dict(sorted(out.items()))


def manifest(pile: Path) -> tuple[str, list[str]]:
    """(the SHA-256 of every file's path and bytes, the paths)."""
    files = sorted(p for p in pile.rglob("*") if p.is_file())
    said = [[p.relative_to(pile).as_posix(), sha(p.read_bytes())] for p in files]
    return sha(json.dumps(said).encode()), [rel for rel, _ in said]


def of_addon(script: Path) -> tuple[str, str]:
    """(the SHA-256 of an add-on's card, of its code with tests left out)."""
    folder = script.parent
    card = folder / "README.md"
    code = [p for p in sorted(folder.glob("*.py")) if not p.name.startswith("test_")]
    return (sha(card.read_bytes()) if card.is_file() else "",
            sha(b"".join(p.name.encode() + b"\0" + p.read_bytes() for p in code)))  # fmt: skip


def placed(pile: Path, rel: str, line: int | None) -> tuple[str, str, bool]:
    """(the file, the place in it, whether a mirror's map was gone through)
    for a path of the pile and a line its output names."""
    for mirror in [pile, *(pile / p for p in Path(rel).parents if str(p) != ".")]:
        inside = (pile / rel).relative_to(mirror).as_posix()
        mapped = mirror / ".places" / (inside + ".json")
        if mapped.is_file():
            try:
                said = json.loads(mapped.read_text(encoding="utf-8"))
            except ValueError:
                break
            at = [
                int(k)
                for k in said.get("places", {})
                if k.isdigit() and (line is None or int(k) <= line)
            ]
            where = said["places"][str(max(at))] if at and line is not None else ""
            return said.get("source", rel), where, True
    return rel, f"line {line}" if line is not None else "", False


def places(pile: Path, known: set[str], out: str) -> list[tuple[str, str, bool]]:
    """Each place in the pile that the output names, once."""
    found, root = set(), str(pile.resolve()) + "/"
    for word in out.split():
        word = word.strip(TRIM)
        path, _, line = (
            word.rpartition(":") if re.search(r":\d+$", word) else (word, "", "")
        )
        path = path[len(root) :] if path.startswith(root) else path
        if path in known:
            found.add(placed(pile, path, int(line) if line else None))
    return sorted(found)


def trace(step: str, script: Path, argv: list[str], pile: Path, box: Path, tmp: Path, mine: Path,
          known: set[str], salt: str, timeout: float, reads: Path | None = None) -> dict:  # fmt: skip
    """One step on a box: the row of what was seen. `tmp` is what {tmp}
    stands for, and `mine` the folder under it that is this step's own."""
    log = mine.parent / f"{mine.name}.guard.log"
    mine.mkdir(parents=True, exist_ok=True)
    fill = {"box": str(box), "pile": str(pile), "tmp": str(tmp)}
    env = dict(os.environ)
    first = HERE / "memo" if reads is not None else CI / "guard"
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (str(first), env.get("PYTHONPATH", "")) if p
    )
    env.update(WILLOW_GUARD_LOG=str(log), PYTHONDONTWRITEBYTECODE="1")
    if reads is not None:
        env["WILLOW_READ_LOG"] = str(reads)
    before = (box / "record.jsonl").read_text(encoding="utf-8").count("\n")
    had = {x for x in mine.rglob("*") if x.is_file()}
    began, timed_out = time.perf_counter(), False
    try:
        got = subprocess.run([sys.executable, str(script), *(a.format(**fill) for a in argv)],
                             stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env,
                             cwd=mine, timeout=timeout)  # fmt: skip
        code, out, err = got.returncode, got.stdout, got.stderr
    except subprocess.TimeoutExpired as late:
        code, out, err, timed_out = None, late.stdout or "", "", True
        out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
    seconds = round(time.perf_counter() - began, 3)
    record = (box / "record.jsonl").read_text(encoding="utf-8").splitlines()[before:]
    rows: dict[str, int] = {}
    for line in record:
        kind = json.loads(line).get("kind", "?")
        rows[kind] = rows.get(kind, 0) + 1
    wrote: dict[str, int] = {}
    maps = 0
    for p in sorted(x for x in mine.rglob("*") if x.is_file() and x not in had):
        if ".places" in p.relative_to(mine).parts:
            maps += 1
        else:
            wrote[p.suffix or "(none)"] = wrote.get(p.suffix or "(none)", 0) + 1
    seen = places(pile, known, out)
    first = out.splitlines()[0] if out.strip() else ""
    state = REPORT.match(first)
    card, code_sha = of_addon(script)

    def salted(text: str) -> str:
        return sha(f"{salt}\0{text}".encode())[:16]

    breaches = (
        sorted(set(log.read_text(encoding="utf-8").splitlines()))
        if log.is_file()
        else []
    )
    named = (
        "the pile"
        if str(pile) in err
        else "its scratch folder"
        if str(tmp) in err
        else None
    )
    return {
        "step": step, "card": card, "code": code_sha, "exit": code, "timed_out": timed_out,
        "seconds": seconds, "state": state.group(1) if state else None,
        "lines": len(out.splitlines()), "out": sha(steady(out, fill, mine).encode()), "rows": dict(sorted(rows.items())),
        "wrote": dict(sorted(wrote.items())), "maps": maps,
        "places": sorted({salted(f"{f}\0{w}") for f, w, _ in seen}),
        "files": sorted({salted(f) for f, _, _ in seen}),
        "mapped": sum(1 for _, _, through in seen if through), "breaches": len(breaches),
        "breach_kinds": sorted({b.split(":")[0][:40] for b in breaches})[:5],
        "refusal_names": named if code == 2 else None,
    }  # fmt: skip


def boxed(pile: Path, work: Path) -> tuple[str, set[str]]:
    """A box over the pile under a key made for the run: (the pile's
    manifest, its files)."""
    work.mkdir(parents=True)
    was, files = manifest(pile)
    key = work / "run.key"
    key.write_text(secrets.token_hex(32))
    made = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(work / "box"),
                           "--pile", str(pile), "--key", str(key)], capture_output=True, text=True)  # fmt: skip
    if made.returncode != 0:
        raise ValueError(
            f"no box could be made over the pile: {made.stderr.strip()[:200]}"
        )
    return was, set(files)


def run(
    pile: Path,
    name: str,
    salt: str,
    work: Path,
    to: Path,
    only: list[str],
    timeout: float,
) -> int:
    steps = table(contract())
    wanted = only or list(steps)
    unknown = [s for s in wanted if s not in steps]
    if unknown:
        raise ValueError(f"not a step: {', '.join(unknown)}")
    was, known = boxed(pile, work)
    with to.open("a", encoding="utf-8") as f:
        for step in wanted:
            script, argv = steps[step]
            here = work / "steps" / step
            shutil.copytree(work / "box", here / "box")
            row = trace(
                step,
                script,
                argv,
                pile,
                here / "box",
                here / "tmp",
                here / "tmp",
                known,
                salt,
                timeout,
            )
            f.write(
                json.dumps({"pile": name, "manifest": was, **row}, sort_keys=True)
                + "\n"
            )
            f.flush()
            shutil.rmtree(here, ignore_errors=True)
    if manifest(pile)[0] != was:
        raise ValueError(
            "the pile changed while it was traced; the rows are not to be used"
        )
    print(f"{len(wanted)} steps traced on {name} ({len(known)} files) to {to}")
    return 0


# ── the run memory ───────────────────────────────────────────────────────────
SAME = ("exit", "timed_out", "state", "lines", "out", "rows", "wrote", "maps", "places",
        "files", "mapped", "breaches", "refusal_names")  # fmt: skip


def _digest(path: Path, event: str) -> str:
    """What was at a path: its bytes' hash, its names' hash for a folder
    listed, or "absent"."""
    try:
        if event == "list":
            return sha("\0".join(sorted(os.listdir(path))).encode())
        return sha(path.read_bytes()) if path.is_file() else "absent"
    except OSError:
        return "absent"


def _where(path: str, roots: dict[str, Path], mine: Path) -> tuple[str, str] | None:
    """(the root a read was under, the path in it), or None for a read that
    doesn't count: the step's own folder, or anywhere off the run's roots."""
    p = Path(path)
    if p == mine or mine in p.parents:
        return None
    for role in ("pile", "box", "tmp"):
        root = roots[role]
        if p == root or root in p.parents:
            return role, p.relative_to(root).as_posix()
    return None


def _reads(log: Path, roots: dict[str, Path], mine: Path) -> dict | None:
    """{"event role path": digest} for what a step read, or None when it
    started a program whose reads can't be seen."""
    out: dict[str, str] = {}
    if not log.is_file():
        return out
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            got = json.loads(line)
        except ValueError:
            continue
        if got["e"] == "run":
            return None
        at = _where(got["p"], roots, mine)
        if at is not None:
            event = "list" if got["e"] == "list" else "file"
            out[f"{event} {at[0]} {at[1]}"] = _digest(roots[at[0]] / at[1], got["e"])
    return dict(sorted(out.items()))


def _box_state(box: Path) -> list:
    """Every file of the box but the record, with its size and bytes' hash."""
    return sorted((p.relative_to(box).as_posix(), sha(p.read_bytes())) for p in box.rglob("*")
                  if p.is_file() and p.name != "record.jsonl")  # fmt: skip


class Memo:
    """Steps remembered on one pile: each time a step ran, what it read and
    what came of it, the files it left kept by their hash."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        (folder / "blobs").mkdir(parents=True, exist_ok=True)
        self.path = folder / "memo.jsonl"
        self.seen: dict[str, list[dict]] = {}
        if self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                one = json.loads(line)
                self.seen.setdefault(one["step"], []).append(one)

    def find(self, step: str, roots: dict[str, Path]) -> dict | None:
        for one in self.seen.get(step, []):
            if all(_digest(roots[role] / rel, "list" if event == "list" else "open") == want
                   for key, want in one["reads"].items()
                   for event, role, rel in [key.split(" ", 2)]):  # fmt: skip
                return one
        return None

    def keep(self, step: str, reads: dict, row: dict, mine: Path) -> None:
        if any(one["reads"] == reads for one in self.seen.get(step, [])):
            return
        files = {}
        for p in sorted(x for x in mine.rglob("*") if x.is_file()):
            data = p.read_bytes()
            files[p.relative_to(mine).as_posix()] = blob = sha(data)
            (self.folder / "blobs" / blob).write_bytes(data)
        one = {"step": step, "reads": reads, "row": {k: row[k] for k in row if k != "memo"},
               "files": files}  # fmt: skip
        self.seen.setdefault(step, []).append(one)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(one, sort_keys=True) + "\n")

    def replay(self, one: dict, mine: Path) -> None:
        mine.mkdir(parents=True, exist_ok=True)
        for rel, blob in one["files"].items():
            (mine / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.folder / "blobs" / blob, mine / rel)


def drawn(stack: str, at: int, share: float) -> bool:
    """Whether a remembered step is run anyway, to be held to the memory."""
    return int(sha(f"check\0{stack}\0{at}".encode())[:8], 16) / 16**8 < share


def run_stack(grid: Path, ids: list[str], pile: Path, name: str, salt: str, work: Path, to: Path,
              timeout: float, memo: Memo | None = None, never: frozenset = frozenset(),
              share: float = 0.05) -> int:  # fmt: skip
    """Each stack named, on a box of its own that carries on from step to
    step, in the order the stack lists: the same row a step, with the
    stack and where in it the step came."""
    said = json.loads(grid.read_text(encoding="utf-8"))
    stacks = {row["id"]: row["steps"] for row in said["stacks"]}
    unknown = [i for i in ids if i not in stacks]
    if unknown:
        raise ValueError(f"not a stack of this grid: {', '.join(unknown)}")
    scripts = table(contract())
    was, known = boxed(pile, work)
    done = 0
    with to.open("a", encoding="utf-8") as f:
        for n, stack in enumerate(ids):
            here = work / "stacks" / str(n)
            shutil.copytree(work / "box", here / "box")
            for at, step in enumerate(stacks[stack]):
                argv = said["steps"][step]["args"]
                mine = here / "tmp" / step
                roots = {"pile": pile, "box": here / "box", "tmp": here / "tmp"}
                kept = (
                    memo.find(step, roots)
                    if memo is not None and step not in never
                    else None
                )
                if kept is not None and not drawn(stack, at, share):
                    memo.replay(kept, mine)
                    row = {**kept["row"], "memo": "reused"}
                else:
                    log = here / "reads" / f"{step}.log" if memo is not None else None
                    if log is not None:
                        log.parent.mkdir(exist_ok=True)
                    box_was = _box_state(here / "box") if memo is not None else None
                    row = trace(step, scripts[step][0], argv, pile, here / "box", here / "tmp",
                                mine, known, salt, timeout, reads=log)  # fmt: skip
                    if memo is not None:
                        row["memo"] = "never" if step in never else "ran"
                        if kept is not None:
                            row["memo"] = "checked"
                            row["memo_same"] = all(
                                row[k] == kept["row"][k] for k in SAME
                            )
                        reads = _reads(log, roots, mine)
                        if (step not in never and reads is not None and not row["rows"]
                                and row["exit"] is not None and not row["timed_out"]
                                and not row["breaches"] and _box_state(here / "box") == box_was):  # fmt: skip
                            memo.keep(step, reads, row, mine)
                f.write(json.dumps({"pile": name, "manifest": was, "stack": stack, "at": at, **row},
                                   sort_keys=True) + "\n")  # fmt: skip
                f.flush()
                done += 1
            shutil.rmtree(here, ignore_errors=True)
    if manifest(pile)[0] != was:
        raise ValueError(
            "the pile changed while it was traced; the rows are not to be used"
        )
    print(f"{done} steps of {len(ids)} stacks traced on {name} to {to}")
    return 0


def main(argv: list[str]) -> int:
    opts: dict = {"only": [], "stack": []}
    it = iter(argv[1:])
    for a in it:
        if (
            a
            in (
                "--pile",
                "--name",
                "--salt",
                "--work",
                "--to",
                "--timeout",
                "--grid",
                "--memo",
                "--never",
                "--check",
            )
            and a[2:] not in opts
        ):
            opts[a[2:]] = next(it, "")
        elif a in ("--only", "--stack"):
            opts[a[2:]].append(next(it, ""))
        else:
            opts = {}
            break
    need = ("pile", "name", "salt", "work", "to")
    verb = argv[0] if argv else ""
    ok = verb in ("pile", "stack") and all(opts.get(k) for k in need)
    ok = ok and (verb == "pile") == (not opts.get("grid") and not opts.get("stack"))
    memo_opts = {k for k in ("memo", "never", "check") if k in opts}
    if (
        not ok
        or (memo_opts and (verb != "stack" or "memo" not in opts))
        or (
            verb == "stack"
            and not (opts.get("grid") and opts["stack"] and not opts["only"])
        )
    ):
        print(USAGE, file=sys.stderr)
        return 2
    try:
        pile, work = Path(opts["pile"]).resolve(), Path(opts["work"]).resolve()
        timeout = float(opts.get("timeout") or 120)
        if not pile.is_dir():
            raise ValueError("PILE is not a folder")
        if work.is_relative_to(ROOT) or work.exists():
            raise ValueError("DIR must be new, and outside the repository")
        if verb == "stack":
            memo = never = None
            if opts.get("memo"):
                folder = Path(opts["memo"]).resolve()
                if folder.is_relative_to(ROOT):
                    raise ValueError("the memory must be outside the repository")
                memo = Memo(folder)
                never = frozenset(
                    json.loads(Path(opts["never"]).read_text())
                    if opts.get("never")
                    else []
                )
            share = float(opts.get("check") or 0.05)
            if not 0 <= share <= 1:
                raise ValueError("--check is a share, from 0 to 1")
            return run_stack(Path(opts["grid"]), opts["stack"], pile, opts["name"], opts["salt"], work,
                             Path(opts["to"]), timeout, memo, never or frozenset(), share)  # fmt: skip
        return run(
            pile,
            opts["name"],
            opts["salt"],
            work,
            Path(opts["to"]),
            opts["only"],
            timeout,
        )
    except (OSError, ValueError, KeyError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
