"""run.py: the study, end to end, its pass rules as kernel verdict rows.

    python demo/craft-assembly/run.py --work DIR --box BOX [--now TS] [--stage NAME]

DIR is where sources.py fetched the sources (DIR/sources); everything this
writes is under DIR, and the verdicts go on the record in BOX, made if it
isn't there (its key beside it, BOX.key, never read here). The stages, in
order, each needing the one before:

    pieces     every source taken apart into DIR/store, and again into
               DIR/store-again; every source rebuilt from DIR/store alone into
               DIR/rebuilt
    baseline   each of the composite's apps, in its rebuilt copy, with its own
               Cargo.lock: each package that will be a composite member is
               built (cargo build -p P --locked) and tested (cargo test -p P
               --locked --no-fail-fast)
    composite  compose.py into DIR/composite and again into DIR/composite-again;
               its lockfile made once (cargo generate-lockfile), then each
               member built and tested the same way, --locked to it

The pass rules, one verdict row each, all frozen with this file:

    rebuilt         every source rebuilt from the store hashes to its pinned
                    git tree
    same-store      taking apart twice gives the same store, byte for byte
    same-composite  composing twice gives the same composite, byte for byte
    builds          every package that builds in its own app builds in the
                    composite
    tests           every package whose tests pass in its own app passes them
                    in the composite

A package that doesn't build, or whose tests fail, in its own app is said in
the results and counts for neither rule: the rules ask what assembling lost.
Each cargo command gets an hour; past that it counts as failing. Builds run
with CARGO_PROFILE_DEV_DEBUG=0 and CARGO_INCREMENTAL=0, the same for both.

DIR/results.json holds every outcome; each verdict row holds its SHA-256 and
the SHA-256 of every tool. Exit codes: 0 every rule held; 42 one didn't; 2
refused.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT)]
import compose  # noqa: E402
import kernel  # noqa: E402
import pieces  # noqa: E402
import sources  # noqa: E402

RECIPE = json.loads((HERE / "composite.json").read_text(encoding="utf-8"))
HOUR = 3600
ENV = {
    "CARGO_PROFILE_DEV_DEBUG": "0",
    "CARGO_INCREMENTAL": "0",
    "CARGO_TERM_COLOR": "never",
}
TOOLS = ("kernel.py", "demo/craft-assembly/pieces.py", "demo/craft-assembly/compose.py",
         "demo/craft-assembly/run.py", "demo/craft-assembly/sources.py",
         "demo/php2shell/make_trees.py", "demo/craft-assembly/sources.json",
         "demo/craft-assembly/composite.json")  # fmt: skip
STAGES = ("pieces", "baseline", "composite")


def digest(folder: Path) -> str:
    """One SHA-256 over every file under `folder`: its path, mode and bytes."""
    h = hashlib.sha256()
    for path, mode, data in pieces.files_of(folder):
        h.update(f"{path}\0{mode}\0".encode() + hashlib.sha256(data).digest())
    return h.hexdigest()


def cargo(argv: list[str], cwd: Path, target: Path) -> bool:
    env = {**os.environ, **ENV, "CARGO_TARGET_DIR": str(target)}
    try:
        got = subprocess.run(["cargo", *argv], cwd=cwd, env=env, capture_output=True,
                             text=True, timeout=HOUR)  # fmt: skip
    except subprocess.TimeoutExpired:
        return False
    return got.returncode == 0


def package_names(folder: Path, members: list[str]) -> dict[str, str]:
    """member folder -> package name, read from each member's manifest."""
    return {m: tomllib.loads((folder / m / "Cargo.toml").read_text(encoding="utf-8"))["package"]["name"]
            for m in members}  # fmt: skip


def try_each(folder: Path, packages: list[str], target: Path) -> dict[str, dict]:
    out = {}
    for p in packages:
        built = cargo(["build", "-p", p, "--locked"], folder, target)
        tested = built and cargo(
            ["test", "-p", p, "--locked", "--no-fail-fast"], folder, target
        )
        out[p] = {"builds": built, "tests": tested}
        print(
            f"  {p}: {'builds' if built else 'BUILD FAILS'}, {'tests pass' if tested else 'tests fail'}",
            flush=True,
        )
    return out


def stage_pieces(work: Path, res: dict) -> None:
    for d in ("store", "store-again", "rebuilt"):
        shutil.rmtree(work / d, ignore_errors=True)
    res["pieces"] = pieces.apart(work / "sources", work / "store")
    pieces.apart(work / "sources", work / "store-again")
    pieces.rebuild(work / "store", work / "rebuilt")
    held = pieces.check(work / "store", work / "rebuilt")
    pins = {n: p["tree"] for n, p in sources.PINS.items()}
    res["rebuilt"] = {n: held.get(n, False) and pieces.recipe(work / "store", n)["tree"] == t
                      for n, t in sorted(pins.items())}  # fmt: skip
    res["store_sha256"] = digest(work / "store")
    res["same_store"] = res["store_sha256"] == digest(work / "store-again")


def stage_composite_layout(work: Path, res: dict) -> dict:
    for d in ("composite", "composite-again"):
        shutil.rmtree(work / d, ignore_errors=True)
    glue = compose.compose(work / "store", RECIPE, work / "composite")
    compose.compose(work / "store", RECIPE, work / "composite-again")
    res["glue"] = {
        k: glue[k]
        for k in (
            "members",
            "left_out",
            "profiles_dropped",
            "library",
            "local_cargo_config",
        )
    }
    res["composite_sha256"] = digest(work / "composite")
    res["same_composite"] = res["composite_sha256"] == digest(work / "composite-again")
    return glue


def members_by_app(work: Path) -> dict[str, list[str]]:
    root = tomllib.loads(
        (work / "composite" / "Cargo.toml").read_text(encoding="utf-8")
    )
    out: dict[str, list[str]] = {}
    for m in root["workspace"]["members"]:
        app, rest = m.split("/", 1)
        out.setdefault(app, []).append(rest)
    return out


def stage_baseline(work: Path, res: dict) -> None:
    res["baseline"] = {}
    for app, members in sorted(members_by_app(work).items()):
        print(f"baseline: {app}", flush=True)
        names = package_names(work / "rebuilt" / app, members)
        res["baseline"][app] = try_each(
            work / "rebuilt" / app, sorted(names.values()), work / "target-sources"
        )


def stage_composite(work: Path, res: dict) -> None:
    out = work / "composite"
    res["lockfile_made"] = cargo(["generate-lockfile"], out, work / "target-composite")
    lock = out / "Cargo.lock"
    res["lockfile_sha256"] = (
        hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else None
    )
    res["composite"] = {}
    for app, members in sorted(members_by_app(work).items()):
        print(f"composite: {app}", flush=True)
        names = package_names(out / app, members)
        res["composite"][app] = try_each(
            out, sorted(names.values()), work / "target-composite"
        )


def rules(res: dict) -> dict[str, bool]:
    held = {"rebuilt": all(res.get("rebuilt", {}).values()) and len(res.get("rebuilt", {})) == len(sources.PINS),
            "same-store": res.get("same_store") is True,
            "same-composite": res.get("same_composite") is True}  # fmt: skip
    if "composite" in res:
        base, comp = res["baseline"], res["composite"]
        for rule, field in (("builds", "builds"), ("tests", "tests")):
            want = {(a, p) for a, ps in base.items() for p, o in ps.items() if o[field]}
            held[rule] = all(comp.get(a, {}).get(p, {}).get(field) for a, p in want)
    return held


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        v = next(it, "")
        if a not in ("--work", "--box", "--now", "--stage") or not v or a in opts:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return 2
        opts[a] = v
    if (
        not {"--work", "--box"} <= opts.keys()
        or opts.get("--stage", "composite") not in STAGES
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    work, box = Path(opts["--work"]), Path(opts["--box"])
    if not all(sources.check(work).values()):
        print(
            "refused: the sources don't match their pins; run sources.py --check",
            file=sys.stderr,
        )
        return 2
    if shutil.which("cargo") is None and opts.get("--stage") != "pieces":
        print("refused: the baseline and the composite need cargo", file=sys.stderr)
        return 2
    now = opts.get("--now") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    last = STAGES.index(opts.get("--stage", "composite"))
    res: dict = {}
    stage_pieces(work, res)
    stage_composite_layout(work, res)
    if last >= 1:
        stage_baseline(work, res)
    if last >= 2:
        stage_composite(work, res)
    (work / "results.json").write_text(pieces.dump(res), encoding="utf-8")
    held = rules(res)
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):  # its own "ready" line
            if (
                kernel.init(
                    box, work / "rebuilt", box.parent / (box.name + ".key"), now
                )
                != kernel.ALIVE
            ):
                print(f"refused: couldn't start a record at {box}", file=sys.stderr)
                return 2
    tools = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in TOOLS}
    sha = hashlib.sha256((work / "results.json").read_bytes()).hexdigest()
    for rule, ok in held.items():
        kernel.append(box, now, "verdict", who="craft-assembly", gate=f"craft-assembly:{rule}",
                      state="satisfied" if ok else "failing", results_sha256=sha, tools=tools)  # fmt: skip
    print(json.dumps(held, indent=1))
    return 0 if all(held.values()) else 42


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
