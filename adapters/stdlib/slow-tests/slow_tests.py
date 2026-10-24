"""slow_tests.py: each test's time over several runs, the slowest named.

    python adapters/stdlib/slow-tests/slow_tests.py --runs DIR [--top N] [--times X] [--seconds S]

DIR holds one JUnit XML file per run, which pytest writes with no install:
`pytest --junitxml=DIR/2026-10-24.xml`. The runs are read in the order of
their file names (numbers inside a name count as numbers, so run-9 comes
before run-10), never by when a file was written, and the last is "this run".
This names the slowest tests in this run, the files they sit in, and any test
slower than before by a fixed rule:

    SLOWER  a test that passed in this run and in an earlier one, when this
            run's time is more than X times (2 unless --times says) its
            median over the earlier runs that it passed, and more than S
            seconds (1 unless --seconds says) longer. Both must hold, so a
            test that went from 0.01 s to 0.05 s is not flagged.

Absence is said, not dropped: a test that ran in an earlier run and is not
in this one, or was skipped, is listed with the run it last passed in; a
skipped test has no time, so it is never counted as fast. A test that failed
has a time that says nothing about how long it takes, so only passes count.
Each list shows N lines (10 unless --top says) and says how many more.

Exit codes, the kernel's: 0 some runs read; 42 no run in DIR to read; 2
refused (no folder, a file that isn't JUnit XML, a time that isn't a number,
or a bad command line).

It only reads DIR. It writes nothing; the person (or CI) keeps the files.
"""

from __future__ import annotations

import math
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: best to worst: when one test appears twice in a run, the worst state stands
ORDER = ("skipped", "passed", "failed", "error")


class Refused(Exception):
    pass


def natural(stem: str) -> list:
    """Numbers inside a name count as numbers: run-9 sorts before run-10."""
    return [
        (False, int(p)) if p.isdigit() else (True, p)
        for p in re.split(r"(\d+)", stem)
        if p
    ]


def read_run(path: Path) -> dict[str, tuple[str, float]]:
    """{test id: (state, seconds)} for one JUnit file."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as e:
        raise Refused(f"{path.name} is not JUnit XML ({e})") from e
    out: dict[str, tuple[str, float]] = {}
    for case in root.iter("testcase"):
        cls, name = case.get("classname", ""), case.get("name", "")
        tid = f"{cls}::{name}" if cls else name
        try:
            secs = float(case.get("time", ""))
        except ValueError:
            secs = math.nan
        if not math.isfinite(secs) or secs < 0:
            raise Refused(f"{path.name}: {tid} has no usable time")
        kids = {c.tag for c in case}
        state = (
            "error"
            if "error" in kids
            else "failed"
            if "failure" in kids
            else "skipped"
            if "skipped" in kids
            else "passed"
        )
        if tid in out:  # the same id twice in one run: times add, worst state stands
            old_state, old_secs = out[tid]
            state = max(state, old_state, key=ORDER.index)
            secs += old_secs
        out[tid] = (state, secs)
    return out


def load(folder: Path) -> list[tuple[str, dict[str, tuple[str, float]]]]:
    if not folder.is_dir():
        raise Refused(f"{folder} is not a folder")
    files = [
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix == ".xml" and not p.name.startswith(".")
    ]
    files.sort(key=lambda p: (natural(p.stem), p.stem))
    return [(p.stem, read_run(p)) for p in files]


def secs(x: float) -> str:
    return f"{x:.2f}"


def capped(lines: list[str], top: int) -> list[str]:
    more = len(lines) - top
    return lines[:top] + (
        [f"  ... and {more} more (--top shows more)"] if more > 0 else []
    )


def report(runs, top: int, times: float, seconds: float) -> list[str]:
    name, now = runs[-1]
    earlier = runs[:-1]
    out = [f"{len(runs)} run{'s' * (len(runs) != 1)}, oldest first:"]
    for rn, tests in runs:
        n = {s: sum(1 for st, _ in tests.values() if st == s) for s in ORDER}
        total = sum(t for st, t in tests.values() if st == "passed")
        out.append(
            f"  {rn}  {len(tests)} tests  passed {n['passed']}  skipped {n['skipped']}"
            f"  failed {n['failed'] + n['error']}  passed time {secs(total)} s"
        )

    def past(tid: str) -> list[float]:
        return [r[tid][1] for _, r in earlier if tid in r and r[tid][0] == "passed"]

    ran = sorted(
        ((t, tid) for tid, (st, t) in now.items() if st == "passed"),
        key=lambda x: (-x[0], x[1]),
    )
    out += ["", f"Slowest in {name} (seconds; {len(ran)} passed):"]
    lines = []
    for t, tid in ran:
        before = past(tid)
        note = (
            f"median of {len(before)} earlier {secs(statistics.median(before))}"
            if before
            else "no earlier time"
        )
        lines.append(f"  {secs(t):>9}  {tid}  ({note})")
    out += capped(lines, top) or ["  nothing passed in this run"]

    files: dict[str, float] = {}
    for t, tid in ran:
        files[tid.split("::")[0]] = files.get(tid.split("::")[0], 0.0) + t
    out += ["", f"Slowest files in {name} (seconds, passed tests added):"]
    out += capped(
        [
            f"  {secs(t):>9}  {f or '(no file)'}"
            for f, t in sorted(files.items(), key=lambda x: (-x[1], x[0]))
        ],
        top,
    ) or ["  nothing passed in this run"]

    if not earlier:
        out += ["", "One run: nothing earlier to compare with."]
        return out
    slower, new = [], 0
    for t, tid in ran:
        before = past(tid)
        if not before:
            new += 1
            continue
        med = statistics.median(before)
        if t > times * med and t - med > seconds:
            slower.append((t - med, tid, t, med, len(before)))
    slower.sort(key=lambda x: (-x[0], x[1]))
    out += [
        "",
        f"SLOWER than before in {name} (more than {times:g}x and {seconds:g} s"
        " over the median of earlier passes):",
    ]
    out += capped(
        [
            f"  {tid}  {secs(t)} s now, {secs(med)} s median of {n} earlier"
            f"  (+{secs(d)} s, {t / med:.1f}x)"
            for d, tid, t, med, n in slower
        ],
        top,
    ) or ["  none"]
    if new:
        out.append(f"  ({new} passed with no earlier pass, so not compared)")

    gone = []
    for tid in {t for _, r in earlier for t in r}:
        before = [
            (rn, r[tid][1]) for rn, r in earlier if tid in r and r[tid][0] == "passed"
        ]
        state = now[tid][0] if tid in now else "not in this run"
        if before and state in ("skipped", "not in this run"):
            gone.append((state, tid, *before[-1]))
    gone.sort(key=lambda x: (-x[3], x[1]))
    out += ["", f"NOT RUN in {name}, though it passed before:"]
    out += capped(
        [
            f"  {tid}  {state}; last passed in {rn} at {secs(t)} s"
            for state, tid, rn, t in gone
        ],
        top,
    ) or ["  none"]

    bad = sorted((tid, st) for tid, (st, _) in now.items() if st in ("failed", "error"))
    if bad:
        out += ["", f"FAILED in {name} (its time is not counted):"]
        out += capped([f"  {tid}  {st}" for tid, st in bad], top)
    return out


def main(argv: list[str]) -> int:
    usage = __doc__.split("\n\n")[1]
    opts: dict[str, str] = {}
    i = 0
    while i < len(argv):
        if argv[i] not in ("--runs", "--top", "--times", "--seconds") or i + 1 >= len(
            argv
        ):
            print(usage, file=sys.stderr)
            return kernel.REFUSED
        opts[argv[i]] = argv[i + 1]
        i += 2
    if "--runs" not in opts:
        print(usage, file=sys.stderr)
        return kernel.REFUSED
    try:
        top = int(opts.get("--top", "10"))
        times = float(opts.get("--times", "2"))
        seconds = float(opts.get("--seconds", "1"))
    except ValueError:
        print(usage, file=sys.stderr)
        return kernel.REFUSED
    if (
        top < 1
        or not math.isfinite(times)
        or times < 1
        or not math.isfinite(seconds)
        or seconds < 0
    ):
        print(usage, file=sys.stderr)
        return kernel.REFUSED
    try:
        runs = load(Path(opts["--runs"]))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    if not any(tests for _, tests in runs):
        print("no JUnit XML run with any test in that folder")
        return kernel.ESCALATE
    print("\n".join(report(runs, top, times, seconds)))
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
