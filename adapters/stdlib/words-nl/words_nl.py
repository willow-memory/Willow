"""words_nl.py: questions in Dutch, without Dutch's common words. Python 3.9+.

    python adapters/stdlib/words-nl/words_nl.py bite --box DIR [--now TS] "Wanneer is de afspraak bij de tandarts?"
    python adapters/stdlib/words-nl/words_nl.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Dutch keeps every word, so its common words count
toward a match too, and nearly every Dutch passage holds them. `bite` takes
Dutch's common words out first and asks the kernel with what's left:
"Wanneer is de afspraak bij de tandarts?" is asked as "afspraak tandarts". The kernel's own bite does the rest: the record,
the passages, the exit code. An answer you approve is kept for the words
asked, so ask through here each time.

Letters typed as a letter and an accent mark (some keyboards send them that
way) are joined before anything is compared, so "café" matches however
it was typed. A question of nothing but common words is refused: name the
thing you mean. "die" is an English word too: in a Dutch question it's left out.

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

#: Dutch's articles, conjunctions, prepositions, pronouns, the verbs "be",
#: "have" and the modals, question words, yes and no: what the kernel's own
#: FUNCTION list holds for English
COMMON = frozenset(
    """
    aan al als ben bent bij daar dan dat de deze die dit door een en er
    geen haar had hadden heb hebben hebt heeft hem het hier hij hoe hun
    ik in is ja je jij jouw jullie kan kunnen maar mag me meer met mij
    mijn moet moeten naar nee niet nog of om omdat onder ons onze ook op
    over s t te tegen tot tussen u uit uw van veel voor waar waarom
    wanneer want waren was wat we welk welke werd wie wij wil willen
    worden wordt zal ze zij zijn zo zonder zullen
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Dutch's common ones."""
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
