"""ci_why.py: why CI went red, from the log alone.

    python adapters/stdlib/ci-why/ci_why.py LOG [--record RECORD.JSONL]
    python adapters/stdlib/ci-why/ci_why.py --record RECORD.JSONL
    ... | python adapters/stdlib/ci-why/ci_why.py -

LOG is what `ci.py run` printed, or a CI job's raw log (`-` reads it from
standard input, so `gh run view JOB --log-failed | ci_why.py -` works).
RECORD is the CI record (`record.jsonl`, one verdict row per gate). Nothing
is fetched and nothing is written: this reads what it is given.

Which gates failed is read from the record when one is given, else from the
summary `ci.py run` prints at the end of its log (`gate  failing  (exit 1)`).
Only a failing gate is looked at: a gate that is `unreachable` (a tool isn't
installed) did not fail, and a passing gate's noise is left alone. For each
failing gate, the failing block is pulled out of its section of the log and
printed plain:

- pytest: the test, the line that failed, its `E` lines (the assertion and
  its diff), and where; not the source around it, the dots or the timings;
- mutants: the `stale ...` / `survived ...` lines and the add-on's count;
- ruff: the rule, the place, the offending line, and the diff of a format;
- a Python traceback: its last frame and the error.

A gate that failed in a shape none of these knows is said so, with the
section's last lines marked as such. No cause is ever guessed.

With no record and no summary (a bare pytest log, say) a section counts as
failing when it holds one of those shapes.

The first line says which answer it is: `nothing failed` (the log or record
says every gate passed or couldn't run), `N failing`, or `couldn't find a
failing block`.

Exit codes, the kernel's: 0 nothing failed, or every failing gate's block is
printed; 42 couldn't find a failing block for a failing gate (or any gate,
when nothing says which failed); 2 refused (no such file, a record that
doesn't verify, a bad command line).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: ci_why.py LOG [--record RECORD.JSONL] | ci_why.py --record RECORD.JSONL | ci_why.py -"  # fmt: skip
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
STAMP = re.compile(r"^﻿?\d{4}-\d\d-\d\dT[\d:.]+Z ?")  # GitHub's, on every line
HEAD = re.compile(r"^── (\S+)\s*$")
VERDICT = re.compile(r"^(\S+)\s+(satisfied|failing|unreachable)\b(?:\s+\((.*)\))?")
PASSED = re.compile(r"^(?:=+ )?(\d+) passed\b(?!.*\b(?:failed|error))")
#: the most `E` lines one failure shows; the rest are counted, never hidden
CAP = 25
HEAD_E, TAIL_E = 15, 8
TAIL = 8


def clean(text: str) -> list[str]:
    """The log's lines less colour, GitHub's time stamps and its markers."""
    out = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = STAMP.sub("", ANSI.sub("", line)).rstrip()
        if not line.startswith(("##[error]", "##[group]", "##[endgroup]")):
            out.append(line)
    return out


def sections(lines: list[str]) -> tuple[dict, dict]:
    """({gate: its lines}, {gate: (state, why)} from the summary at the end).
    A log with no `── gate` headers is one section, named ''."""
    if not any(HEAD.match(x) for x in lines):
        return {"": lines}, {}
    found: dict[str, list[str]] = {}
    gate = None
    for line in lines:
        m = HEAD.match(line)
        if m:
            gate = m.group(1)
            found.setdefault(gate, [])
        elif gate is not None:
            found[gate].append(line)
    said = {}
    for body in found.values():
        keep = []
        for line in body:
            m = VERDICT.match(line)
            if m and m.group(1) in found:
                said[m.group(1)] = (m.group(2), m.group(3))
            else:
                keep.append(line)
        body[:] = keep
    return found, said


def record_verdicts(path: Path) -> dict:
    """{gate: (state, why)}: each gate's latest verdict row."""
    rows, breaks = kernel.read(path)
    if breaks:
        raise ValueError("the record doesn't verify: " + "; ".join(breaks))
    return {
        r["gate"]: (r["state"], r.get("why"))
        for r in rows
        if r.get("kind") == "verdict" and "gate" in r and "state" in r
    }


# ── the shapes a failure comes in ────────────────────────────────────────────
PYTEST_BLOCK = re.compile(r"^_{2,} (.+?) _{2,}$")
PYTEST_WHERE = re.compile(r"^[\w./-]+\.py:\d+: \S")
PROGRESS = re.compile(r"^E\s+[.sFEx]+\s+\[\s*\d+%\]$")  # a nested run's dots
PYTEST_FAILED = re.compile(r"^(FAILED|ERROR) (\S+)(?: - (.*))?$")


def pytest_blocks(body: list[str]) -> list[tuple[str, list[str]]]:
    start = next((i for i, x in enumerate(body) if re.fullmatch(r"=+ (FAILURES|ERRORS) =+", x)), None)  # fmt: skip
    summary = {}
    for x in body:
        m = PYTEST_FAILED.match(x)
        if m:
            summary[m.group(2).split("::")[-1]] = m.group(2)
    blocks, seen = [], set()
    if start is not None:
        raw: list[tuple[str, list[str]]] = []
        for x in body[start + 1 :]:
            m = PYTEST_BLOCK.match(x)
            if m:
                raw.append((m.group(1), []))
            elif x.startswith("=") and x.endswith("="):
                break
            elif raw:
                raw[-1][1].append(x)
        for name, lines in raw:
            keep = [x for x in lines if x.startswith(">") or re.match(r"E( |$)", x) or PYTEST_WHERE.match(x)]  # fmt: skip
            keep = [x for x in keep if not PROGRESS.match(x)]
            errs = [x for x in keep if x.startswith("E")]
            if len(errs) > CAP:  # keep both ends: a nested report ends with its verdict
                cut = errs[HEAD_E : len(errs) - TAIL_E]
                drop = set(id(x) for x in cut)
                at = next(i for i, x in enumerate(keep) if id(x) == id(cut[0]))
                keep = [x for x in keep if id(x) not in drop]
                keep.insert(at, f"E   ... {len(cut)} E lines left out ...")
            short = name.split(".")[-1]
            seen.add(short)
            blocks.append((summary.get(short, name), keep))
    for short, full in summary.items():  # a failure with no block (a short -tb)
        if short not in seen:
            line = next(x for x in body if x.startswith((f"FAILED {full}", f"ERROR {full}")))  # fmt: skip
            blocks.append((full, [line]))
    return blocks


def mutants_blocks(body: list[str]) -> list[tuple[str, list[str]]]:
    count = next((x for x in body if re.match(r"^[\w.-]+: \d+ of \d+ killed", x)), "")
    bad = [x.strip() for x in body if re.match(r"^  (stale|survived|couldn't run) ", x)]
    return [(count or "mutants", bad)] if bad else []


RUFF_HEAD = re.compile(r"^([A-Z]+\d+|unformatted)\b ?(?:\[\*\] )?(.*)$")
RUFF_AT = re.compile(r"^\s*--> (\S+?):(\d+):(\d+)$")


def ruff_blocks(body: list[str]) -> list[tuple[str, list[str]]]:
    blocks = []
    for i, x in enumerate(body):
        at = RUFF_AT.match("".join(body[i + 1 : i + 2]))
        head = RUFF_HEAD.match(x)
        if not (head and at):
            continue
        place = f"{at.group(1)}:{at.group(2)}"
        lines, rest = [], body[i + 2 :]
        for y in rest:
            if not y.strip() or y.startswith("help:"):
                break
            m = re.match(rf"^\s*{at.group(2)} \| (.*)$", y)
            if m and head.group(1) != "unformatted":
                lines.append(m.group(1))
            elif head.group(1) == "unformatted" and re.match(r"^\s*(\d+ )?\s*[-+] ", y):
                lines.append(re.sub(r"^\s*\d* *", "", y))
        blocks.append((f"{place}  {x.strip()}", lines))
    return blocks


def traceback_blocks(body: list[str]) -> list[tuple[str, list[str]]]:
    last = None
    for i, x in enumerate(body):
        if x.startswith("Traceback (most recent call last):"):
            last = i
    if last is None:
        return []
    frames, error = [], None
    for x in body[last + 1 :]:
        if x.startswith(" "):
            frames.append(x.strip())
        else:
            error = x.strip()
            break
    return [("a traceback", frames[-2:] + ([error] if error else []))]


SHAPES = (pytest_blocks, mutants_blocks, ruff_blocks, traceback_blocks)


def blocks_of(body: list[str]) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []
    for shape in SHAPES:
        out += shape(body)
    return out


# ── the answer ───────────────────────────────────────────────────────────────
def why(log: str | None, verdicts: dict) -> tuple[int, list[str]]:
    """(exit code, the lines to print)."""
    found, summary = sections(clean(log)) if log is not None else ({}, {})
    states = verdicts or summary
    if states:
        failing = sorted(g for g, (s, _) in states.items() if s == "failing")
        if not failing:
            n = {k: sum(1 for s, _ in states.values() if s == k) for k in ("satisfied", "unreachable")}  # fmt: skip
            more = f", {n['unreachable']} couldn't run (not a failure)" if n["unreachable"] else ""  # fmt: skip
            return kernel.ALIVE, [f"ci-why: nothing failed: {n['satisfied']} satisfied{more}"]  # fmt: skip
    else:
        failing = [g for g, body in found.items() if blocks_of(body)]
        if not failing:
            if log is not None and any(PASSED.match(x) for x in clean(log)):
                return kernel.ALIVE, ["ci-why: nothing failed: the log says it passed"]  # fmt: skip
            return kernel.ESCALATE, ["ci-why: couldn't find a failing block, and nothing says which gate failed"]  # fmt: skip
    out, missing, count = [], [], 0
    for gate in failing:
        state, reason = states.get(gate, ("failing", None))
        head = f"── {gate or 'log'}  failing" + (f"  ({reason})" if reason else "")
        body = found.get(gate)
        blocks = blocks_of(body) if body is not None else []
        out += ["", head]
        if body is None:
            out.append("   no log was given" if log is None else "   the log has no section for this gate")  # fmt: skip
        for title, lines in blocks:
            out.append(f"   {title}")
            out += [f"      {x}" for x in lines]
            count += 1
        if not blocks:
            missing.append(gate)
            if body:
                tail = [x for x in body if x.strip()][-TAIL:]
                out.append("   no failure shape this knows; the section's last lines, as printed:")  # fmt: skip
                out += [f"      {x}" for x in tail]
            elif body is not None:
                out.append("   the section is empty")
    names = f" ({', '.join(g or 'log' for g in failing)})" if len(failing) <= 3 else ""
    top = f"ci-why: {len(failing)} failing{names}; {count} block{'s' * (count != 1)} found"  # fmt: skip
    if missing:
        top += f"; couldn't find one for {len(missing)}"
    return (kernel.ESCALATE if missing else kernel.ALIVE), [top, *out]


def main(argv: list[str]) -> int:
    log, record, it = None, None, iter(argv)
    for a in it:
        if a == "--record" and record is None:
            record = next(it, None)
            if record is None:
                break
        elif a == "-" and log is None:
            log = "-"
        elif not a.startswith("-") and log is None:
            log = a
        else:
            print(USAGE, file=sys.stderr)
            return kernel.REFUSED
    if log is None and record is None:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    try:
        text = None
        if log == "-":
            text = sys.stdin.buffer.read().decode("utf-8", "replace")
        elif log is not None:
            text = Path(log).read_bytes().decode("utf-8", "replace")
        verdicts = {}
        if record is not None:
            if not Path(record).is_file():
                raise ValueError(f"{record} isn't a file")
            verdicts = record_verdicts(Path(record))
    except (OSError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    if record is not None and not verdicts and text is None:
        print("ci-why: the record holds no verdicts, so there is nothing to say")
        return kernel.ESCALATE
    code, lines = why(text, verdicts)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
