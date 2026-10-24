"""words_fr.py: questions in French, without French's common words. Python 3.9+.

    python adapters/stdlib/words-fr/words_fr.py bite --box DIR [--now TS] "Quand est le rendez-vous chez le dentiste ?"
    python adapters/stdlib/words-fr/words_fr.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in French keeps every word, so its common words count
toward a match too, and nearly every French passage holds them. `bite` takes
French's common words out first and asks the kernel with what's left:
"Quand est le rendez-vous chez le dentiste ?" is asked as "rendez dentiste". The kernel's own bite does the rest: the record,
the passages, the exit code. An answer you approve is kept for the words
asked, so ask through here each time.

Letters typed as a letter and an accent mark (some keyboards send them that
way) are joined before anything is compared, so "où" matches however
it was typed. A question of nothing but common words is refused: name the
thing you mean. "or" (now) and "car" (because) are kept: they're English words a French folder may hold too, and a French question rarely needs them.

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

#: French's articles, conjunctions, prepositions, pronouns, the verbs "be",
#: "have" and the modals, question words, yes and no: what the kernel's own
#: FUNCTION list holds for English
COMMON = frozenset(
    """
    ai après as au aux avait avant avec avez avons c ce cela ces cet
    cette chez combien comme comment d dans de depuis des doit doivent
    donc du elle elles en entre es est et ici il ils j je l la laquelle
    le lequel les leur leurs lui là m ma mais me mes mon ne ni non nos
    notre nous on ont ou oui où par pas peut peuvent plus pour pourquoi
    pourrait qu quand que quel quelle quelles quels qui quoi s sa sans
    se ses si son sont sous suis sur t ta te tes ton très tu un une vers
    vos votre vous y à ça étaient était été être
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less French's common ones."""
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
