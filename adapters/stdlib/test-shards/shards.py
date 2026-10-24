"""shards.py: split a test suite into N parts that take about the same time.

    python adapters/stdlib/test-shards/shards.py --past RUN.xml --shards N PATH ...
    python adapters/stdlib/test-shards/shards.py --past RUN.xml --shard K/N PATH ...
    python adapters/stdlib/test-shards/shards.py --past RUN.xml --shards N --tests IDS.txt

Options: `--past FILE` (pytest's `--junitxml` output of an earlier run; as
many as you like, none is allowed), `--by file|test` (default file),
`--default SECONDS` (what a test with no past time counts as).

It reads the past times, learns the suite as it is now, and deals the pieces
out so every part is expected to finish about together. It only reads, and
writes to standard output. Nothing goes online.

The suite as it is now comes from `python -m pytest --collect-only -q PATH
...`, which this runs (importing the test files, writing nothing), or from
`--tests FILE` (`-` is standard input): pytest node ids, one a line, as that
command prints them. A test in the suite but not in the past run is placed
all the same, at the default; a test in the past run but gone from the suite
is left out, and both are said.

A piece is a test file (`--by file`, the default) or a single test (`--by
test`). A file keeps its fixtures together and is a short, safe argument for
pytest; a test splits finer but its id has brackets and spaces to quote.

The split is longest first: pieces by time, slowest first, ties by name, each
to the part with the least so far, ties to the lowest. The same input gives
the same bytes. Times are whole milliseconds, so the sums are exact.

`--shard K/N` prints only part K of N, one piece a line, for a job to run:
`pytest "${PIECES[@]}"`. Without it every part is printed with its expected
time, and how far the slowest is from the fastest.

A test with no past time counts as the median of those that have one (or
`--default`); if none has, one second. Past times are the testcase times
pytest wrote, setup and teardown included, so a module's first fixture costs
the first test. Starting pytest itself is not counted.

Exit codes, the kernel's: 0 split; 42 the suite holds no test; 2 refused (a
bad command line, a file that can't be read, a collection that failed).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = """usage: shards.py --past RUN.xml --shards N PATH ...
       shards.py --past RUN.xml --shard K/N PATH ...
       shards.py --past RUN.xml --shards N --tests IDS.txt
       options: --past FILE (repeatable)  --by file|test  --default SECONDS"""
NODE = re.compile(r"[^\s:][^\s]*?\.py::\S.*")


def key_of(nodeid: str) -> tuple[str, str]:
    """The (classname, name) pytest writes in JUnit XML for a node id."""
    i = nodeid.find("[")
    head = nodeid if i < 0 else nodeid[:i]
    params = "" if i < 0 else nodeid[i:]
    path, *mid, last = head.split("::")
    if path.endswith(".py"):
        path = path[:-3]
    return ".".join([path.replace("/", "."), *mid]), last + params


def past_times(files: list[str]) -> dict[tuple[str, str], int]:
    """Milliseconds per (classname, name): the mean over every time it was seen."""
    seen: dict[tuple[str, str], list[int]] = {}
    for f in files:
        try:
            tree = ET.parse(f)
        except (OSError, ET.ParseError) as e:
            raise ValueError(f"can't read {f} as JUnit XML: {e}") from None
        for case in tree.iter("testcase"):
            try:
                ms = round(float(case.get("time", "0")) * 1000)
            except ValueError:
                raise ValueError(
                    f"{f}: a testcase has a time that isn't a number"
                ) from None
            seen.setdefault(
                (case.get("classname", ""), case.get("name", "")), []
            ).append(ms)
    return {k: sum(v) // len(v) for k, v in seen.items()}


def median(values: list[int]) -> int:
    v = sorted(values)
    if not v:
        return 1000
    return v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) // 2


def collect(paths: list[str]) -> list[str]:
    """The node ids pytest finds under PATHS now."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    got = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *paths],
        capture_output=True, text=True, env=env,
    )  # fmt: skip
    if got.returncode not in (0, 5):
        tail = (got.stdout + got.stderr).strip().splitlines()[-5:]
        raise ValueError("pytest couldn't collect the suite: " + " | ".join(tail))
    return parse_ids(got.stdout)


def parse_ids(text: str) -> list[str]:
    """Node ids from `pytest --collect-only -q` output; its other lines are not ids."""
    return [
        line.rstrip() for line in text.splitlines() if NODE.fullmatch(line.rstrip())
    ]


def secs(ms: int) -> str:
    return f"{ms // 1000}.{ms % 1000:03d} s"


def split(pieces: dict[str, int], n: int) -> list[list[str]]:
    """Longest first, ties by name, each to the least-loaded part, ties to the lowest."""
    parts: list[list[str]] = [[] for _ in range(n)]
    load = [0] * n
    for name in sorted(pieces, key=lambda p: (-pieces[p], p)):
        i = load.index(min(load))
        parts[i].append(name)
        load[i] += pieces[name]
    return [sorted(p) for p in parts]


def parse(argv: list[str]) -> dict:
    """The command line as options; ValueError says what is wrong with it."""
    opt: dict = {"past": [], "by": "file", "tests": None, "default": None,
                 "shards": None, "shard": None, "paths": []}  # fmt: skip
    it = iter(argv)
    for a in it:
        if a in ("--past", "--by", "--tests", "--default", "--shards", "--shard"):
            v = next(it, None)
            if v is None:
                raise ValueError(f"{a} needs a value")
            if a == "--past":
                opt["past"].append(v)
            else:
                opt[a[2:]] = v
        elif a.startswith("-") and a != "-":
            raise ValueError(f"unknown option {a}")
        else:
            opt["paths"].append(a)
    if opt["by"] not in ("file", "test"):
        raise ValueError("--by is file or test")
    if opt["default"] is not None:
        try:
            opt["default"] = round(float(opt["default"]) * 1000)
        except ValueError:
            raise ValueError("--default is a number of seconds") from None
        if opt["default"] < 0:
            raise ValueError("--default can't be negative")
    n = None
    if opt["shards"] is not None:
        if not opt["shards"].isdigit() or int(opt["shards"]) < 1:
            raise ValueError("--shards is a whole number, 1 or more")
        n = int(opt["shards"])
    k = None
    if opt["shard"] is not None:
        m = re.fullmatch(r"([0-9]+)/([0-9]+)", opt["shard"])
        if not m or not 1 <= int(m[1]) <= int(m[2]):
            raise ValueError("--shard is K/N with 1 <= K <= N, such as 2/3")
        k = int(m[1])
        if n is not None and n != int(m[2]):
            raise ValueError("--shards and --shard name different numbers of parts")
        n = int(m[2])
    if n is None:
        raise ValueError("say how many parts: --shards N or --shard K/N")
    if (opt["tests"] is None) == (not opt["paths"]):
        raise ValueError(
            "name the suite: PATH ... to collect, or --tests FILE, not both"
        )
    opt["n"], opt["k"] = n, k
    return opt


def main(argv: list[str]) -> int:
    try:
        opt = parse(argv)
    except ValueError as e:
        print(f"refused: {e}\n{USAGE}", file=sys.stderr)
        return kernel.REFUSED
    try:
        past = past_times(opt["past"])
        if opt["tests"] is None:
            ids = collect(opt["paths"])
        else:
            text = (
                sys.stdin.read()
                if opt["tests"] == "-"
                else Path(opt["tests"]).read_text("utf-8")
            )
            ids = parse_ids(text)
    except (OSError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    ids = sorted(set(ids))
    if not ids:
        print("nothing to split: the suite holds no test")
        return kernel.ESCALATE

    keys = {i: key_of(i) for i in ids}
    known = {i: past[keys[i]] for i in ids if keys[i] in past}
    gone = len(set(past) - set(keys.values()))
    unit = (lambda i: i.split("::")[0]) if opt["by"] == "file" else (lambda i: i)
    if opt["default"] is not None:
        dflt, how = opt["default"], "from --default"
    elif known:
        dflt, how = (
            median(list(known.values())),
            "the median of the tests that have one",
        )
    else:
        dflt, how = 1000, "no test has one, so the fixed default"
    pieces: dict[str, int] = {}
    unknown: dict[str, int] = {}
    count: dict[str, int] = {}
    for i in ids:
        u = unit(i)
        pieces[u] = pieces.get(u, 0) + known.get(i, dflt)
        count[u] = count.get(u, 0) + 1
        if i not in known:
            unknown[u] = unknown.get(u, 0) + 1
    parts = split(pieces, opt["n"])

    if opt["k"] is not None:
        for p in parts[opt["k"] - 1]:
            print(p)
        return kernel.ALIVE
    n = opt["n"]
    totals = [sum(pieces[p] for p in part) for part in parts]
    noun = "files" if opt["by"] == "file" else "tests"
    what = f"{len(pieces)} files, " if opt["by"] == "file" else ""
    print(f"{n} parts, {what}{len(ids)} tests, expected {secs(sum(totals))} in all")
    for j, part in enumerate(parts, 1):
        label = f"{len(part)} {noun}" if part else "empty: fewer pieces than parts"
        print(f"part {j}/{n}  {secs(totals[j - 1])}  {label}")
        if opt["by"] == "file":
            for p in part:
                note = (
                    f"  ({unknown[p]} of {count[p]} tests with no past time)"
                    if p in unknown
                    else ""
                )
                print(f"  {p}  {secs(pieces[p])}{note}")
    print(
        f"spread: slowest {secs(max(totals))}, fastest {secs(min(totals))}, "
        f"{secs(max(totals) - min(totals))} apart"
    )
    n_unknown = len(ids) - len(known)
    if n_unknown:
        print(
            f"{n_unknown} tests with no past time, counted as {secs(dflt)} each ({how})"
        )
    else:
        print("every test has a past time")
    print(f"{gone} tests in the past run are no longer in the suite, left out")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
