"""words_ru.py: questions in Russian, without Russian's common words. Python 3.9+.

    python adapters/stdlib/words-ru/words_ru.py bite --box DIR [--now TS] "Когда у меня приём у стоматолога?"
    python adapters/stdlib/words-ru/words_ru.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Russian keeps every word, so its common words ("и",
"в", "на") count toward a match too, and nearly every Russian passage holds
them. `bite` takes Russian's common words out first and asks the kernel with
what's left: "Когда у меня приём у стоматолога?" is asked as "приём
стоматолога". The kernel's own bite does the rest: the record, the passages,
the exit code. An answer you approve is kept for the words asked, so ask
through here each time.

Letters typed as a letter and an accent mark (й as и and a breve, say) are
joined before anything is compared, so "что" and "й" match however they
were typed. "е" and "ё" stay two letters, as the kernel has them. A question
of nothing but common words is refused: name the thing you mean.

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

#: Russian's conjunctions, prepositions, particles, pronouns, the verb "be",
#: question words, yes and no: what the kernel's own FUNCTION list holds for
#: English
COMMON = frozenset(
    """
    а без более бы был была были было быть в вам вас ведь весь во вот все всё
    вы где да даже для до его ее её если есть еще ещё же за здесь и из или им
    их к как какая какие какой когда кто ли либо мне мной мой мы на над надо
    нам нас себя тебе тебя меня не него нее неё ней нет ни них но ну о об один он она они оно от
    отчего по под после при про с со так также там те тем то того тоже той
    только том ты у уж уже хотя чего чей чем что чтоб чтобы чуть эта эти это
    этого этой этом я
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Russian's common ones."""
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
