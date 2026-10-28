"""cores.py: ci.py's run, its shards at once on this machine. Python 3.9+.

    python adapters/stdlib/ci/cores.py --box DIR [--jobs N] [PART|GATE ...]
                                          [--without GATE ...] [--now TS]

Run alone, ci.py runs every gate one after another, which takes most of an
hour. This starts N of `ci.py run ... --shard K/N --box DIR/K` at once, K
from 1 to N, each with the Python that runs this, then shows every gate's
verdict from the N records in ci.py's own order, and verifies each record.
What the shards print is printed as each one ends, under its name.

N is this machine's CPUs unless --jobs says, and never more than there are
gates. Shards are cut by gate count, as `--shard` cuts them, not by time.
PART, GATE, --without and --now mean what they mean to ci.py, and a name it
doesn't know is refused before anything runs.

The records are ci.py's, one a shard, in DIR/1 to DIR/N; DIR must be outside
the repo, or under .ci-record, as ci.py asks of a record. This writes
nothing of its own, and never a seal.

Exit codes, the kernel's, for every gate together: 0 every gate satisfied;
42 a gate unreachable and none failing; 2 a gate failing, a record that
doesn't verify, or a bad command line.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_ci_for_cores", HERE / "ci.py")
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)
kernel = ci.kernel


def shard(k: int, n: int, args: list[str], box: Path) -> tuple[int, int, str]:
    """`ci.py run ARGS --shard K/N --box BOX/K`: its exit and what it said."""
    got = subprocess.run(
        [sys.executable, str(HERE / "ci.py"), "run", *args,
         "--shard", f"{k}/{n}", "--box", str(box / str(k))],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )  # fmt: skip
    return k, got.returncode, got.stdout


def main(argv: list[str]) -> int:
    opts, names, without, args, it = {}, [], [], [], iter(argv)
    bad = False
    for a in it:
        if a in ("--box", "--jobs", "--now"):
            opts[a] = v = next(it, "")
            bad = bad or not v
            if a == "--now":
                args += [a, v]
        elif a == "--without":
            without.append(next(it, ""))
            args += [a, without[-1]]
        elif a.startswith("-"):
            bad = True
        else:
            names.append(a)
            args.append(a)
    jobs = opts.get("--jobs", str(os.cpu_count() or 1))
    if bad or not opts.get("--box") or not jobs.isdigit() or int(jobs) < 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    try:
        chosen = ci.select(names, without, None)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    n = max(1, min(int(jobs), len(chosen)))
    box = Path(opts["--box"])
    with ThreadPoolExecutor(n) as pool:
        running = [pool.submit(shard, k, n, args, box) for k in range(1, n + 1)]
        for done in as_completed(running):
            k, code, said = done.result()
            print(f"\n══ shard {k} of {n}: exit {code}\n{said}", flush=True)
    latest, broken = {}, []
    for k in range(1, n + 1):
        with contextlib.redirect_stdout(io.StringIO()) as said:
            code = ci.do_verify(box / str(k))
        if code == kernel.REFUSED:
            broken.append(f"{box / str(k)}: {said.getvalue().strip() or 'refused'}")
            continue
        rows, _ = kernel.read(box / str(k) / "record.jsonl")
        latest.update({r["gate"]: r for r in rows if r["kind"] == "verdict"})
    print()
    states = []
    for gate in chosen:
        r = latest.get(gate)
        if r is None:
            continue
        states.append(r["state"])
        print(f"{gate:<18} {r['state']}" + (f"  ({r['why']})" if "why" in r else ""))
    for b in broken:
        print(f"doesn't verify: {b}")
    missing = [g for g in chosen if g not in latest]
    if missing and not broken:
        print(f"no verdict for: {' '.join(missing)}")
    tally = {s: states.count(s) for s in (ci.SATISFIED, ci.UNREACHABLE, ci.FAILING)}
    print(", ".join(f"{c} {s}" for s, c in tally.items()) + f", in {n} records")
    if broken or missing:
        return kernel.REFUSED
    return ci.code_of(states)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
