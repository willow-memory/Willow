"""words_pl.py: questions in Polish, without Polish's common words. Python 3.9+.

    python adapters/stdlib/words-pl/words_pl.py bite --box DIR [--now TS] "Kiedy jest termin u dentysty?"
    python adapters/stdlib/words-pl/words_pl.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Polish keeps every word, so its common words count
toward a match too, and nearly every Polish passage holds them. `bite` takes
Polish's common words out first and asks the kernel with what's left:
"Kiedy jest termin u dentysty?" is asked as "termin dentysty". The kernel's
own bite does the rest: the record, the passages, the exit code. An answer
you approve is kept for the words asked, so ask through here each time.

Letters typed as a letter and an accent mark (some keyboards send them that
way) are joined before anything is compared, so "się" matches however it was
typed. A question of nothing but common words is refused: name the thing you
mean. "i", "to" and "a" are English words too: in a Polish question they're
left out.

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

#: Polish's conjunctions, prepositions, pronouns, demonstratives, the verbs
#: "be" and "have" and the modals, question words, yes and no: what the
#: kernel's own FUNCTION list holds for English
COMMON = frozenset(
    """
    a aby albo ale bez bo być będzie będą będę by czemu czy czyj ci cię
    ciebie co dla dlaczego do gdy gdzie go i ile im ich jak jaka jaki jakie
    ja jest jestem jesteśmy jesteście jesteś jego jej jemu jeszcze jeśli ją
    kiedy kto która które którego której który którym lub ma macie mam mamy
    masz mają miał miała miało miały mieli mieć mi mnie mogę może możesz
    można mu musi musisz muszę my na nad nam nas nasz nasza nasze nie niej
    nich nim niż o od około on ona one oni ono oraz po pod powinien powinna
    przed przez przy się siebie sobie swoja swoje swój są tak tam tamta
    tamten tamto te tego tej temu ten teraz to tobie trzeba tu tutaj twoi
    twoja twoje twój ty tylko tym tą tę u w wam was wasz wasza wasze we
    wolno wśród wy więc z za ze że żeby też także już
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Polish's common ones."""
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
