"""hook_compact.py: a PreCompact hook that prints what the record still holds
open, so it survives the assistant's summary. Python 3.9+.

    python adapters/stdlib/hook-compact/hook_compact.py --box DIR

When an assistant's conversation is about to be summarised, the summary keeps
what the assistant chose to keep. This prints, in plain sentences, what the
box still holds open, read the way [digest](../digest/) reads it:

    Before this conversation is summarised, the person's willow box still holds open:
    - 2 suggestions waiting for their seal (only the person approves; an assistant never does):
      - Six hours of sun. (why: the garden notes)
    - 1 question asked more than once and never answered (2 times).
    Keep these in the summary.

The seals waiting are the suggestions that passed the door and that the person
has neither sealed nor declined. The questions unanswered are those asked twice
or more that were never served an answer and never answered by an approval;
the record keeps no question's words, so only the count is said. A quiet box
prints nothing at all.

It writes nothing, not even the row `kernel.py out` appends, and never reads
the key. Whether a host takes a PreCompact hook's output into its summary is
the host's to say: this only prints, and [hook-start](../hook-start/) hands the
same facts back when the next session opens.

Exit codes: 0 printed (or nothing to say); 2 refused (a record that doesn't
verify, a bad command line). A hook should fail open here: a refusal prints its
reason on standard error and adds nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
sys.path.insert(0, str(STDLIB / "digest"))
import digest  # noqa: E402
import kernel  # noqa: E402

SHOWN = 5  # suggestions listed; the count says the rest


def plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def sentences(doc: dict) -> list[str]:
    """What the box holds open, one bullet for each, or [] when nothing."""
    out = []
    waiting = doc["waiting"]["items"]
    if waiting:
        out.append(
            f"- {plural(len(waiting), 'suggestion', 'suggestions')} waiting for their seal "
            "(only the person approves; an assistant never does):"
        )
        for w in waiting[:SHOWN]:
            out.append(
                f"  - {digest.short(w['answer'], 80)} (why: {digest.short(w['why'], 60)})"
            )
        if len(waiting) > SHOWN:
            out.append(f"  - and {len(waiting) - SHOWN} more")
    again = doc["again"]["items"]
    if again:
        times = ", ".join(f"{n} times" for n in again)
        out.append(
            f"- {plural(len(again), 'question', 'questions')} asked more than once and never answered ({times})."
        )
    return out


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--box":
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    doc = {"waiting": digest.waiting(box, rows), "again": digest.asked_again(rows)}
    lines = sentences(doc)
    if lines:
        print(
            "Before this conversation is summarised, the person's willow box still holds open:"
        )
        print("\n".join(lines))
        print("Keep these in the summary.")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
