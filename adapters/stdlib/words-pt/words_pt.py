"""words_pt.py: questions in Portuguese, without Portuguese's common words. Python 3.9+.

    python adapters/stdlib/words-pt/words_pt.py bite --box DIR [--now TS] "Quando é a consulta no dentista?"
    python adapters/stdlib/words-pt/words_pt.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Portuguese keeps every word, so its common words count
toward a match too, and nearly every Portuguese passage holds them. `bite` takes
Portuguese's common words out first and asks the kernel with what's left:
"Quando é a consulta no dentista?" is asked as "consulta dentista". The kernel's own bite does the rest: the record,
the passages, the exit code. An answer you approve is kept for the words
asked, so ask through here each time.

Letters typed as a letter and an accent mark (some keyboards send them that
way) are joined before anything is compared, so "você" matches however
it was typed. A question of nothing but common words is refused: name the
thing you mean. "no" and "nos" are left out whichever they mean ("in the", "us").

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

#: Portuguese's articles, conjunctions, prepositions, pronouns, the verbs "be",
#: "have" and the modals, question words, yes and no: what the kernel's own
#: FUNCTION list holds for English
COMMON = frozenset(
    """
    a ali ao aos aqui as até com como da das de desde deve devem do dos
    e ela elas ele eles em entre era eram essa essas esse esses esta
    estar estas estava este estes estou está estão eu foi foram há isso
    isto já lhe lhes lá mais mas me meu meus minha minhas muito muitos
    na nas nem no nos nossa nossas nosso nossos num numa não nós o onde
    os ou para pela pelas pelo pelos pode podem por porque porquê quais
    qual quando quanta quantas quanto quantos que quem se sem ser seu
    seus sim sobre sua suas são te tem ter tinha tu têm um uma umas uns
    você vocês à às é
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Portuguese's common ones."""
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
