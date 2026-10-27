"""words_sv.py: questions in Swedish, without Swedish's common words. Python 3.9+.

    python adapters/stdlib/words-sv/words_sv.py bite --box DIR [--now TS] "När är tiden hos tandläkaren?"
    python adapters/stdlib/words-sv/words_sv.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Swedish keeps every word, so its common words count
toward a match too, and nearly every Swedish passage holds them. `bite`
takes Swedish's common words out first and asks the kernel with what's left:
"När är tiden hos tandläkaren?" is asked as "tiden tandläkaren". The
kernel's own bite does the rest: the record, the passages, the exit code. An
answer you approve is kept for the words asked, so ask through here each
time.

Letters typed as a letter and an accent mark (some keyboards send them that
way) are joined before anything is compared, so "för" matches however it was
typed. A question of nothing but common words is refused: name the thing you
mean. "men" and "all" are English words too: in a Swedish question they're
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

#: Swedish's articles, conjunctions, prepositions, pronouns, the verbs "be",
#: "have" and "become" and the modals, question words, yes and no: what the
#: kernel's own FUNCTION list holds for English
COMMON = frozenset(
    """
    alla allt all att av bakom bara bli blir blev blivit borde bör bredvid
    de dem den denna denne dess dessa det detta dig din dina ditt du då där
    efter ej eller en er era ert ett fast fick framför från få får
    för genom ha hade haft han hans har henne hennes hon honom hos hur här
    i inga inget ingen inom inte ja jag ju kan kunde kunna man med mellan
    men mig min mina mitt mot måste nej ni nu någon något några när och om
    oss varför
    på redan samt sedan sig sin sina sitt ska skall skulle som så till ur
    utan vad var vara varit vars vart vem vi vid vilka vilken vilket vill
    ville vilja vem väl vår våra vårt än ännu är även också över åt
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Swedish's common ones."""
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
