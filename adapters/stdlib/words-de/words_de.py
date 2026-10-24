"""words_de.py: questions in German, without German's common words. Python 3.9+.

    python adapters/stdlib/words-de/words_de.py bite --box DIR [--now TS] "Wann ist der Termin beim Zahnarzt?"
    python adapters/stdlib/words-de/words_de.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in German keeps every word, so its common words count
toward a match too, and nearly every German passage holds them. `bite` takes
German's common words out first and asks the kernel with what's left:
"Wann ist der Termin beim Zahnarzt?" is asked as "termin zahnarzt". The kernel's own bite does the rest: the record,
the passages, the exit code. An answer you approve is kept for the words
asked, so ask through here each time.

Letters typed as a letter and an accent mark (some keyboards send them that
way) are joined before anything is compared, so "für" matches however
it was typed. A question of nothing but common words is refused: name the
thing you mean. "die" and "will" are English words too: in a German question they're left out.

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

#: German's articles, conjunctions, prepositions, pronouns, the verbs "be",
#: "have" and the modals, question words, yes and no: what the kernel's own
#: FUNCTION list holds for English
COMMON = frozenset(
    """
    aber als am an ans auch auf aus bei beim bin bis bist da darf das
    dass dein deine deinen dem den denn der des dich die dies diese
    diesem diesen dieser dieses dir dort du durch dürfen ein eine einem
    einen einer eines er es euch euer eure für gegen habe haben hast hat
    hatte hatten hier hinter ich ihm ihn ihnen ihr ihre ihren im in ins
    ist ja kann kein keine keinem keinen keiner konnte können mag man
    mein meine meinem meinen meiner mich mir mit muss möchte müssen nach
    neben nein nicht noch nur ob oder ohne schon seid sein seine seinem
    seinen seit sich sie sind so soll sollen sondern um und uns unser
    unsere unter viel viele vom von vor wann war waren warum was weil
    welche welchem welchen welcher welches wem wen wenn wer werden
    weshalb wessen wie wieso will wir wird wo woher wohin wollen wurde
    wurden zu zum zur zwischen über
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less German's common ones."""
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
