"""again.py: the questions you keep asking, counted from the record.

    python adapters/stdlib/again/again.py --box DIR            every repeat
    python adapters/stdlib/again/again.py --box DIR "words"    one question

The record keeps a question as the SHA-256 of its words (its bite key), never
the words, so this can't print a question back. What it can say, exactly:

    asked 4 times, last 2026-10-22, answered from hives/2026.txt:143
      make it standing? approve an answer for it, and it's served as yours
    asked 2 times, last 2026-10-20, answered by your approval proposal:0a6f…

and, given your words, how often you've asked that one.

willow-bot's repetition ladder, by count: asked once, it's answered; twice,
noticed; three times, and every third time after, offered: "make it
standing?" An approved answer is the standing one, and once there is one the
offer stops. Offering is all it does: approving stays yours.

It only reads. Exit codes, the kernel's: 0 nothing waits on you; 42 a
question is at an offer; 2 refused.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

NOTICE_AT = 2  # willow-bot's ladder: the second ask is noticed
OFFER_AT = 3  # and every third ask is offered


def repeats(rows: list[dict]) -> dict[str, dict]:
    """Per bite key: how often asked, when last, and the last thing served."""
    out: dict[str, dict] = {}
    for r in rows:
        if r["kind"] != "bite" or not r.get("bite_key"):
            continue
        e = out.setdefault(r["bite_key"], {"times": 0})
        e["times"] += 1
        e["last"] = r["ts"]
        e["by"] = r.get("answered_by")
        e["served"] = [s["where"] for s in r.get("served", []) if not s.get("echo")]
    return out


def rung(e: dict) -> str:
    if e.get("by"):
        return "standing"
    if e["times"] >= OFFER_AT and e["times"] % OFFER_AT == 0:
        return "offer"
    return "noticed" if e["times"] >= NOTICE_AT else "asked"


def line(key: str, e: dict) -> str:
    out = f"asked {e['times']} time{'s' * (e['times'] != 1)}, last {e['last'][:10]}, "
    if e.get("by"):
        out += f"answered by your approval {e['by'][:21]}…"
    elif e["served"]:
        out += f"answered from {', '.join(e['served'])}"
    else:
        out += "nothing in your folder answered it"
    if rung(e) == "offer":
        out += (
            "\n  make it standing? approve an answer for it, and it's served as yours"
        )
    return out + f"\n  (question {key[:12]})"


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3) or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    every = repeats(rows)
    if len(argv) == 3:
        key = kernel.bite_key(argv[2])
        e = every.get(key or "")
        print(line(key, e) if e else "You haven't asked that before.")
        return kernel.ESCALATE if e and rung(e) == "offer" else kernel.ALIVE
    shown = sorted(
        ((k, e) for k, e in every.items() if e["times"] >= NOTICE_AT),
        key=lambda x: (-x[1]["times"], x[1]["last"]),
    )
    for k, e in shown:
        print(line(k, e))
    if not shown:
        print("No question asked more than once.")
    return (
        kernel.ESCALATE if any(rung(e) == "offer" for _, e in shown) else kernel.ALIVE
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
