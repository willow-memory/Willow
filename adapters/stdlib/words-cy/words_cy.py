"""words_cy.py: questions in Welsh, without Welsh's common words. Python 3.9+.

    python adapters/stdlib/words-cy/words_cy.py bite --box DIR [--now TS] "Pryd mae fy apwyntiad deintydd?"
    python adapters/stdlib/words-cy/words_cy.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Welsh keeps every word, so its common words count toward
a match too, and nearly every Welsh passage holds them. `bite` takes Welsh's
common words out first and asks the kernel with what's left: "Pryd mae fy apwyntiad gyda'r deintydd?" is
asked as "apwyntiad deintydd". The kernel's own bite does the rest: the record, the
passages, the exit code. An answer you approve is kept for the words asked,
so ask through here each time.

A question of nothing but common words is refused: name the thing you mean.
Letters typed as a letter and an accent mark are joined first.

`list` prints the words, one a line.

Exit codes, the kernel's bite's: 0 your files hold it; 42 they don't; 2 a bad
command line, or a question of only common words.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: Welsh's conjunctions, prepositions, particles, pronouns, the verb "be",
#: question words, yes and no: what the kernel's own FUNCTION list holds for
#: English
COMMON = frozenset(
    """
    a ac ai am ar at ayb beth ble bod bron byth dan dim dros drwy dy dyma
    dyna ei eich ein ers eu fe fel fod fy fydd fyddai gan gyda hefyd
    hi hon hwn hwy hyd hyn hynny i ie mae mewn mi mor na nac nad neu ni nid
    o oddi oedd oes oll ond os pa pam pryd pwy rhag rhwng roedd rwy rydw
    rydych rydyn sut tu tua un wedi wrth y ydw ydy ydych ydyn ydyw ym yma
    r ymlaen yn yng yno ynte yr yw
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Welsh's common ones."""
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
