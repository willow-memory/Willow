"""daily_word.py: the day's word from your own files, guesses on the record.

    python adapters/stdlib/daily-word/daily_word.py --box DIR today  [--now TS]
    python adapters/stdlib/daily-word/daily_word.py --box DIR guess WORD [--now TS]

Each day your folder sets one five-letter word of its own, and you get six
guesses. A guess is marked letter by letter — G in its place, y elsewhere in
the word, a dot not in it — and written to the record, so the score is kept
where nothing is lost:

    crane  .y..G
    frame  .GGGG
    flame  GGGGG
    Solved in 3. Back tomorrow.

**The same box asks everyone the same word.** The day's word is drawn from
the folder's own five-letter words (letters only, the kernel's common words
left out) by the seeded stream, seeded with the day and those words
themselves: two copies of the same folder ask the same word on the same
day, whatever either record holds. Your folder is the dictionary too: a
guess must be a five-letter word the folder holds, the same rule the answer
keeps, and one it doesn't hold is refused without costing a guess.

**The record keeps the honest score, not the secret.** Anyone who holds the
folder can derive the day's word, so the game is played on honour, as a
crossword is; what the record holds is each day's guesses and marks, through
the kernel's own append, and the word is shown only when the day is done —
solved, or six guesses out. Marking follows the familiar rule for doubled
letters: each letter of the answer is spent once, greens first.

Exit codes, the kernel's: 0 marked, or the day shown; 42 the day is done,
or the folder has no five-letter words to play; 2 refused, a guess the
folder doesn't hold among the refusals.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

TRIES = 6


class Stream:
    """willow-bot's onescript/stream.py Stream: SHA-256 over seed || counter
    (8 bytes, big-endian), the first four bytes a u32; below() by rejection."""

    def __init__(self, seed: bytes):
        self.seed, self.n = seed, 0

    def u32(self) -> int:
        d = hashlib.sha256(self.seed + self.n.to_bytes(8, "big")).digest()
        self.n += 1
        return int.from_bytes(d[:4], "big")

    def below(self, k: int) -> int:
        cap = (1 << 32) - (1 << 32) % k
        while (x := self.u32()) >= cap:
            pass
        return x % k


def field(pile: list[dict]) -> list[str]:
    """The folder's five-letter words, letters only, the kernel's common
    words left out, each once, sorted: the puzzle's field and its dictionary."""
    out = set()
    for c in pile:
        for w in kernel.words(c["text"]):
            if len(w) == 5 and w.isalpha() and w not in kernel.FUNCTION:
                out.add(w)
    return sorted(out)


def word_of(day: str, words: list[str]) -> str:
    """The day's word: drawn by the stream seeded with the day and the
    folder's own words, so the same folder asks the same word anywhere."""
    seed = f"{day}\n" + "\n".join(words)
    return words[Stream(seed.encode()).below(len(words))]


def marks(guess: str, answer: str) -> str:
    """G in its place, y elsewhere in the word, a dot not in it; each letter
    of the answer spent once, greens first."""
    left = list(answer)
    out = ["."] * len(guess)
    for i, g in enumerate(guess):
        if g == answer[i]:
            out[i] = "G"
            left[i] = ""
    for i, g in enumerate(guess):
        if out[i] == "." and g in left:
            out[i] = "y"
            left[left.index(g)] = ""
    return "".join(out)


def todays(rows: list[dict], day: str) -> list[dict]:
    return [r for r in rows if r["kind"] == "guess" and r.get("day") == day]


def board(said: list[dict], answer: str) -> list[str]:
    out = [f"{r['said']}  {r['marks']}" for r in said]
    if said and said[-1]["marks"] == "G" * 5:
        out.append(f"Solved in {len(said)}. Back tomorrow.")
    elif len(said) >= TRIES:
        out.append(f"Out of guesses. The word was {answer}. Back tomorrow.")
    else:
        left = TRIES - len(said)
        out.append(f"{left} guess{'es' if left != 1 else ''} left.")
    return out


def done(said: list[dict]) -> bool:
    return len(said) >= TRIES or bool(said) and said[-1]["marks"] == "G" * 5


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    showing = args == ["today"]
    guessing = len(args) == 2 and args[0] == "guess" and not args[1].startswith("-")
    if not opts.get("--box") or not (showing or guessing):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused: the record doesn't verify:", *breaks, sep="\n  ",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    day = ts[:10]
    words = field(kernel.chunks(Path(kernel.config(box)["pile"])))
    if not words:
        print("Your folder has no five-letter words to play.")
        return kernel.ESCALATE
    answer = word_of(day, words)
    said = todays(rows, day)
    if showing:
        if not said:
            print(f"No guesses yet today; {TRIES} left.")
            return kernel.ALIVE
        for line in board(said, answer):
            print(line)
        return kernel.ALIVE
    if done(said):
        for line in board(said, answer):
            print(line)
        return kernel.ESCALATE
    got = kernel.words(args[1])
    guess = got[0] if len(got) == 1 else ""
    if len(guess) != 5 or not guess.isalpha():
        print("refused: a guess is one five-letter word", file=sys.stderr)
        return kernel.REFUSED
    if guess not in words:
        print(f"refused: your folder doesn't hold {guess!r}; it costs no guess",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    row = {"day": day, "said": guess, "marks": marks(guess, answer)}
    kernel.append(box, ts, "guess", who="daily-word", **row)
    said = said + [row]
    for line in board(said, answer):
        print(line)
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
