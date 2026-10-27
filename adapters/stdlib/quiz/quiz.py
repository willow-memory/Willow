"""quiz.py: a passage of your own files with a word missing, on the record.

    python adapters/stdlib/quiz/quiz.py --box DIR ask [--now TS]
    python adapters/stdlib/quiz/quiz.py --box DIR answer WORD [--now TS]

`ask` cuts a puzzle from your own folder: one passage, one word blanked, for
you to fill in from memory of your own life.

    hives/2021.txt:4
    Ferris came by for the ______. Two supers on the strong hive.
    (row 13; answer with: quiz.py --box DIR answer WORD)

The passage and the word are drawn by the record's tip, the hash of the row
before, through willow-bot's seeded stream (`sha256-stream/v1`), so no one
picks the puzzle and the same box asks everyone the same one. The row
written holds where the passage is and the SHA-256 of the answer, never the
answer: the record can't tell you, and anyone can check the answer against
it later. One quiz is open at a time; `ask` again shows it again, byte for
byte.

`answer` takes one guess, says right or not, shows the word either way, and
writes the outcome; the next `ask` cuts a new puzzle from the new tip. The
word is read back from your folder at answering, held to the committed
hash, so a folder that changed under the quiz is said, never marked wrong.
The score so far is the record's own count of its answer rows.

What can be quizzed: a passage of your own writing (no line of it opening
as markup or a field, none shouting throughout) with eight words or more.
What can be blanked: a word of four letters or more, no digit in it, not
one of the kernel's common words, standing exactly once in its passage. Exit codes, the kernel's: 0
asked, shown again, or answered, right or not; 42 nothing to quiz, or no
quiz open; 2 refused.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

GENERATOR = "sha256-stream/v1"
LEAST = 8  # words a passage needs before it can carry a blank


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


def blankable(words: list[str]) -> list[int]:
    """Which of the passage's words can be blanked: four letters or more, no
    digit, not a common word, standing exactly once in the passage."""
    return [
        i
        for i, w in enumerate(words)
        if len(w) >= 4
        and w.isalpha()
        and w not in kernel.FUNCTION
        and words.count(w) == 1
    ]


def yours(text: str) -> bool:
    """Whether the passage is the person's own writing: no line of it opens
    as markup or as a field (its first word carrying a : ; or =), and none
    shouts throughout. An email's font-family and a note's frontmatter are
    nobody's memory, and a quiz asks what you lived, not what a machine
    wrote."""
    for line in text.splitlines():
        bare = line.strip()
        if not bare:
            continue
        first = bare.split(" ", 1)[0]
        if bare.startswith("<") or any(c in ":;=" for c in first):
            return False
        if not any(c.islower() for c in bare):
            return False
    return True


def cut(pile: list[dict], tip: str) -> dict | None:
    """The puzzle the tip cuts: a passage and a word, drawn by the seeded
    stream from the person's own passages that can carry a blank; None when
    none can."""
    able = [
        (c, blanks)
        for c in pile
        if yours(c["text"])
        and len(ws := kernel.words(c["text"])) >= LEAST
        and (blanks := blankable(ws))
    ]
    if not able:
        return None
    rng = Stream(f"{tip}:quiz".encode())
    c, blanks = able[rng.below(len(able))]
    word_at = blanks[rng.below(len(blanks))]
    word = kernel.words(c["text"])[word_at]
    return {"seed": tip, "generator": GENERATOR, "path": c["path"],
            "line": c["line"], "word_at": word_at,
            "answer_sha256": kernel.h256(word)}  # fmt: skip


def word_of(pile: list[dict], quiz: dict) -> str | None:
    """The blanked word, read back from the folder; None when the folder has
    changed under the quiz (no such passage, or the word no longer hashes to
    what the row committed to)."""
    for c in pile:
        if c["path"] == quiz["path"] and c["line"] == quiz["line"]:
            words = kernel.words(c["text"])
            if quiz["word_at"] < len(words):
                word = words[quiz["word_at"]]
                if kernel.h256(word) == quiz["answer_sha256"]:
                    return word
    return None


def shown(pile: list[dict], quiz: dict) -> str | None:
    """The passage with its word blanked to its length, or None when the
    folder has changed under the quiz."""
    word = word_of(pile, quiz)
    if word is None:
        return None
    for c in pile:
        if c["path"] == quiz["path"] and c["line"] == quiz["line"]:
            text = " ".join(c["text"].split())
            return re.sub(
                rf"\b{re.escape(word)}\b", "_" * len(word), text, count=1,
                flags=re.IGNORECASE,
            )  # fmt: skip
    return None


def open_quiz(rows: list[dict]) -> dict | None:
    """The quiz row no answer row has answered, or None."""
    answered = {r.get("quiz") for r in rows if r["kind"] == "answer"}
    quizzes = [r for r in rows if r["kind"] == "quiz" and r["n"] not in answered]
    return quizzes[-1] if quizzes else None


def score_of(rows: list[dict]) -> tuple[int, int]:
    said = [r for r in rows if r["kind"] == "answer"]
    return sum(1 for r in said if r.get("right")), len(said)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    asking = args == ["ask"]
    answering = len(args) == 2 and args[0] == "answer" and not args[1].startswith("-")
    if not opts.get("--box") or not (asking or answering):
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
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    ts = opts.get("--now") or kernel.now()
    standing = open_quiz(rows)
    if asking:
        if standing:
            text = shown(pile, standing)
            if text is None:
                print("refused: your folder has changed under the open quiz;"
                      " answer it to close it", file=sys.stderr)  # fmt: skip
                return kernel.REFUSED
            print(f"{standing['path']}:{standing['line']}\n{text}")
            print(f"(row {standing['n']}, still open; answer it first)")
            return kernel.ALIVE
        got = cut(pile, rows[-1]["hash"] if rows else kernel.GENESIS)
        if got is None:
            print("Nothing to quiz: no passage of eight words carries a blank.")
            return kernel.ESCALATE
        row = kernel.append(box, ts, "quiz", who="quiz", **got)
        print(f"{got['path']}:{got['line']}\n{shown(pile, got)}")
        print(f"(row {row['n']}; answer with: quiz.py --box DIR answer WORD)")
        return kernel.ALIVE
    if not standing:
        print("No quiz open; ask for one first.")
        return kernel.ESCALATE
    word = word_of(pile, standing)
    if word is None:
        guessed = kernel.words(args[1])
        right = False
        outcome = "your folder has changed under the quiz; no one is marked wrong"
    else:
        guessed = kernel.words(args[1])
        right = guessed == [word]
        outcome = (
            f"Right: the word is {word}." if right else f"Not it: the word is {word}."
        )
    kernel.append(box, ts, "answer", who="quiz", quiz=standing["n"],
                  said=" ".join(guessed), right=right)  # fmt: skip
    rows, _ = kernel.read(box / "record.jsonl")
    right_n, said_n = score_of(rows)
    print(outcome)
    print(f"{right_n} right of {said_n} answered on this record.")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
