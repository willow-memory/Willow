"""night_batch.py: questions waiting for suggestions, asked of a local model in
one run overnight, stopped the moment you're back.

    python adapters/stdlib/night-batch/night_batch.py run --box DIR --questions FILE
        [--url URL ...] [--model NAME] [--until TS]

FILE holds the questions, one a line. Each is asked as local-model asks: the
kernel bites, only the passages served go to the first local server
answering, and its reply is proposed for your seal. A question already
answered by a seal of yours, or with a suggestion already waiting on your
seal, is skipped.

It stops before the next question the moment you're back: when a row
appears on the record that this run didn't write (you bit, sealed or
declined something), or once it is past `--until` (a time like
2026-11-03T07:00:00Z). A question already asked runs to its end.

    asked    what goes in biscochitos
             pass  proposal:cdd2…  waiting on your seal
    skipped  when does the gate stick: waiting on your seal already
    stopped  you're back: row 9 (seal) isn't this run's
    1 asked, 1 skipped, 1 not reached

Exit codes, the kernel's: 0 every question waiting was asked and got a
suggestion, or none was waiting; 42 it stopped before the end, no local
server ran, or a question got no suggestion; 2 refused (a bad command line,
not a box, a record that doesn't verify, a URL off this machine, a
questions file that can't be read, an `--until` that isn't a time).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_local_model_for_night", HERE.parent / "local-model" / "local_model.py"
)
lm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lm)

USAGE = (
    "usage: night_batch.py run --box DIR --questions FILE [--url URL ...]"
    " [--model NAME] [--until TS]"
)
TS = "%Y-%m-%dT%H:%M:%SZ"


def when(ts: str) -> datetime | None:
    try:
        return datetime.strptime(ts, TS).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def settled(box: Path, rows: list[dict]) -> tuple[set[str], set[str]]:
    """(questions answered by a seal, questions with a suggestion waiting), by bite key."""
    good, no = kernel.sealed(box, rows), kernel.declined(box, rows)
    answered = set()
    for subj, seal in good.items():
        _, asked, why = kernel.standing(box, rows, subj, seal)
        if why is None:
            answered.add(asked)
    waiting = set()
    for r in rows:
        if r["kind"] == "proposal" and r.get("verdict") == "pass":
            if r["subject"] not in good and r["subject"] not in no:
                key = kernel.proposed_under(rows, r["subject"])
                if key is not None:
                    waiting.add(key)
    return answered, waiting


def foreign(rows: list[dict], start: int, key: str | None) -> dict | None:
    """The first row from `start` on that this run's ask for `key` didn't
    write: its own are one bite of that question and what was proposed under
    it. With `key` None, every row from `start` on is someone else's."""
    bite = None
    for r in rows[start:]:
        if (
            key is not None
            and bite is None
            and r["kind"] == "bite"
            and r.get("bite_key") == key
        ):
            bite = r["n"]
        elif not (
            r["kind"] == "proposal"
            and bite is not None
            and r.get("bite_row", bite) == bite
        ):
            return r
    return None


def main(argv: list[str]) -> int:
    opts, urls, rest, it = {}, [], [], iter(argv[1:])
    for a in it:
        if a == "--url":
            urls.append(next(it, ""))
        elif a in ("--box", "--questions", "--model", "--until") and a not in opts:
            opts[a] = next(it, "")
        else:
            rest.append(a)
    if (argv[:1] != ["run"] or rest or not opts.get("--box") or not opts.get("--questions")
            or "" in urls or "" in opts.values()):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    until = when(opts["--until"]) if "--until" in opts else None
    if "--until" in opts and until is None:
        print(f"refused: --until is a time like 2026-11-03T07:00:00Z, not {opts['--until']}",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    off = [u for u in urls if not lm.on_this_machine(u)]
    if off:
        print(f"refused: not on this machine: {', '.join(off)}", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    try:
        text = Path(opts["--questions"]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: can't read the questions: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    questions = list(dict.fromkeys(q.strip() for q in text.splitlines() if q.strip()))
    answered, waiting = settled(box, rows)
    seen, last = len(rows), None  # rows read so far; the bite key last asked
    asked = skipped = 0
    stopped, failed = "", False
    for i, q in enumerate(questions):
        rows, _ = kernel.read(box / "record.jsonl")
        theirs = foreign(rows, seen, last)
        seen, last, key = len(rows), None, kernel.bite_key(q)
        if theirs is not None:
            stopped = (
                f"you're back: row {theirs['n']} ({theirs['kind']}) isn't this run's"
            )
        elif until is not None and datetime.now(timezone.utc) >= until:
            stopped = f"it is past {opts['--until']}"
        if stopped:
            print(f"stopped  {stopped}")
            print(f"{asked} asked, {skipped} skipped, {len(questions) - i} not reached")
            return kernel.ESCALATE
        if key in answered:
            skipped += 1
            print(f"skipped  {q}: answered by your seal already")
            continue
        if key in waiting:
            skipped += 1
            print(f"skipped  {q}: waiting on your seal already")
            continue
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            code = lm.main(["ask", "--box", str(box), *(a for u in urls for a in ("--url", u)),
                            *(["--model", opts["--model"]] if "--model" in opts else []), q])  # fmt: skip
        out = said.getvalue()
        if out.startswith("no local model server is running"):
            print(out, end="")
            print(f"{asked} asked, {skipped} skipped, {len(questions) - i} not reached")
            return kernel.ESCALATE
        asked += 1
        failed = failed or code != kernel.ALIVE
        print(f"asked    {q}")
        for line in out.splitlines():
            print(f"         {line}")
        waiting.add(key)
        last = key
    print(f"{asked} asked, {skipped} skipped, 0 not reached")
    return kernel.ESCALATE if failed else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
