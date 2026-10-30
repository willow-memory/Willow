"""words_tlh.py: questions in Klingon, without Klingon's common words. Python 3.9+.

    python adapters/stdlib/words-tlh/words_tlh.py bite --box DIR [--now TS] "nuqDaq 'oH yIH'e'?"
    python adapters/stdlib/words-tlh/words_tlh.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Klingon keeps every word, so its common words count
toward a match too. `bite` takes Klingon's common words out first and asks
the kernel with what's left: "nuqDaq 'oH yIH'e'?" is asked as "yih". The
kernel's own bite does the rest: the record, the passages, the exit code. An
answer you approve is kept for the words asked, so ask through here each time.

A question of nothing but common words is refused: name the thing you mean.
Letters typed as a letter and an accent mark are joined first.

`list` prints the words as the kernel reads them, one a line.

Exit codes, the kernel's bite's: 0 your files hold it; 42 they don't; 2 a bad
command line, or a question of only common words.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: Klingon's pronouns (which also stand for "be"), conjunctions, question
#: words, yes and no, as spelled in the sources on the card, each one in two
#: of them
SPELLED = (
    "jIH SoH ghaH 'oH maH tlhIH chaH bIH 'e' "
    "je joq ghap 'ej qoj pagh 'ach 'a "
    "nuq 'Iv nuqDaq ghorgh qatlh chay' 'ar "
    "HIja' HISlaH ghobe'"
).split()

#: Each word as the kernel reads it, typed with a plain apostrophe (which the
#: kernel splits on, as it does a curly one) and with the modifier letter ʼ
#: (which it keeps as a letter)
COMMON = frozenset(
    w for s in SPELLED for w in kernel.words(s) + kernel.words(s.replace("'", "ʼ"))
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Klingon's common ones."""
    text = unicodedata.normalize("NFC", question)
    return [w for w in kernel.words(text) if w not in COMMON]


def bite(argv: list[str]) -> int:
    opts, words, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            words.append(a)
    if not opts.get("--box") or len(words) != 1 or words[0].startswith("--"):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
    ask = kept(words[0])
    if not ask:
        print("refused: every word is a common one; name the thing you mean",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    return kernel.main(["bite", "--box", opts["--box"], *now, " ".join(ask)])


def main(argv: list[str]) -> int:
    if argv[:1] == ["bite"]:
        return bite(argv[1:])
    if argv == ["list"]:
        print("\n".join(sorted(COMMON)))
        return kernel.ALIVE
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
