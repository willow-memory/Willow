"""surprise.py: one passage from your folder, drawn at random, and replayable.

    python adapters/stdlib/surprise/surprise.py --box DIR [--seed HEX] [--now TS]

Note apps sell this as "resurfacing": something you wrote and forgot, brought
back. It draws one passage of at least eight words from your folder:

    From notes/2024-03-11.md, line 4:
        ...
    seed 9f2c…  (the same seed and folder always draw this passage)

The draw is willow-bot's `sha256-stream/v1` (from `onescript/stream.py`):
SHA-256 over the seed and a counter, the first four bytes as a number, and a
pick by rejection so no passage is likelier than another. With no `--seed`,
the seed is the SHA-256 of "willow surprise" and today's date, so it is the
same passage all day and a new one tomorrow; pass the seed it printed to see
that passage again.

The draw is written to the record through the kernel's `append`, as a
`surprise` row: the seed, the generator, and the passage's id and place,
never its words. So what was shown is on the record like any answer.

Exit codes, the kernel's: 0 a passage was drawn; 42 the folder has none long
enough; 2 refused.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

GENERATOR = "sha256-stream/v1"
LABEL = b"willow surprise"
MIN_WORDS = 8


class Stream:
    """willow-bot's `sha256-stream/v1`: SHA-256 over seed + an 8-byte counter."""

    def __init__(self, seed: bytes):
        self.seed, self.n = seed, 0

    def u32(self) -> int:
        d = hashlib.sha256(self.seed + self.n.to_bytes(8, "big")).digest()
        self.n += 1
        return int.from_bytes(d[:4], "big")

    def below(self, k: int) -> int:
        """Uniform in 0..k-1, by rejection: no modulo bias."""
        cap = (1 << 32) - (1 << 32) % k
        while (x := self.u32()) >= cap:
            pass
        return x % k


def day_seed(ts: str) -> str:
    return hashlib.sha256(b"willow surprise " + ts[:10].encode()).hexdigest()


def draw(pile: list[dict], seed: str) -> dict | None:
    """The one passage `seed` draws from `pile`'s long enough passages."""
    long = [c for c in pile if len(kernel.words(c["text"])) >= MIN_WORDS]
    if not long:
        return None
    return long[Stream(bytes.fromhex(seed) + LABEL).below(len(long))]


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--seed", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    seed = opts.get("--seed", "")
    if (
        not opts.get("--box")
        or args
        or (seed and not re.fullmatch(r"[0-9a-f]{2,128}", seed))
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, ts = Path(opts["--box"]), opts.get("--now") or kernel.now()
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if kernel.read(box / "record.jsonl")[1]:
        print("refused: the record doesn't verify", file=sys.stderr)
        return kernel.REFUSED
    seed = seed or day_seed(ts)
    c = draw(kernel.chunks(Path(kernel.config(box)["pile"])), seed)
    if c is None:
        print(f"No passage in your folder has {MIN_WORDS} words or more.")
        return kernel.ESCALATE
    where = f"{c['path']}:{c['line']}"
    kernel.append(
        box, ts, "surprise", seed=seed, generator=GENERATOR,
        served=[{"id": c["id"], "where": where}],
    )  # fmt: skip
    body = "\n".join("    " + line for line in c["text"].splitlines())
    print(f"From {c['path']}, line {c['line']}:\n{body}\n")
    print(f"seed {seed}  (the same seed and folder always draw this passage)")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
