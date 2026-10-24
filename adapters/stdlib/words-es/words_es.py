"""words_es.py: questions in Spanish, without Spanish's common words. Python 3.9+.

    python adapters/stdlib/words-es/words_es.py bite --box DIR [--now TS] "¿Cuándo es la cita con el dentista?"
    python adapters/stdlib/words-es/words_es.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Spanish keeps every word, so its common words count
toward a match too, and nearly every Spanish passage holds them. `bite` takes
Spanish's common words out first and asks the kernel with what's left:
"¿Cuándo es la cita con el dentista?" is asked as "cita dentista". The kernel's own bite does the rest: the record,
the passages, the exit code. An answer you approve is kept for the words
asked, so ask through here each time.

Letters typed as a letter and an accent mark (some keyboards send them that
way) are joined before anything is compared, so "cuándo" matches however
it was typed. A question of nothing but common words is refused: name the
thing you mean. "son" (they are) is an English word too: in a Spanish question it's left out.

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

#: Spanish's articles, conjunctions, prepositions, pronouns, the verbs "be",
#: "have" and the modals, question words, yes and no: what the kernel's own
#: FUNCTION list holds for English
COMMON = frozenset(
    """
    a ahí al allí aquí como con contra cuando cuál cuáles cuándo cuánta
    cuántas cuánto cuántos cómo de debe deben debo del desde donde dónde
    e el ella ellas ellos en entre era eran es esa esas ese eso esos
    esta estaba estaban estar estas este esto estos estoy está están
    estás fue fueron ha había hacia han has hasta hay he hemos la las le
    les lo los me mi mis mucho muchos muy más ni no nos nosotras
    nosotros nuestra nuestras nuestro nuestros o os para pero podría por
    porque puede pueden puedo que quién quiénes qué se según ser si sin
    sobre son su sus sí te tu tú u un una unas unos usted ustedes
    vosotras vosotros y ya yo él
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Spanish's common ones."""
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
