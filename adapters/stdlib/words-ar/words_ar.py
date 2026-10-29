"""words_ar.py: questions in Arabic, without Arabic's common words. Python 3.9+.

    python adapters/stdlib/words-ar/words_ar.py bite --box DIR [--now TS] "متى موعدي عند طبيب الأسنان؟"
    python adapters/stdlib/words-ar/words_ar.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Arabic keeps every word, so its common words count toward
a match too, and nearly every Arabic passage holds them. `bite` takes Arabic's
common words out first and asks the kernel with what's left: "متى موعدي عند طبيب الأسنان؟" is
asked as "موعدي طبيب الأسنان". The kernel's own bite does the rest: the record, the
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
import re
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: Arabic's conjunctions, prepositions, particles, pronouns, the verb "be",
#: question words, yes and no: what the kernel's own FUNCTION list holds for
#: English
COMMON = frozenset(
    """
    أن أنا أنت أنتم أو أي أيضا أين إذا إلى إن التي الذي الذين اللذان الى بعد
    بل بين تكون تلك ثم حتى ذلك على عن عند فقط في قبل قد كان كانت كل كيف لا
    لكن لم لماذا لن لو ليس ما ماذا متى مع من نحن نعم هذا هذه هل هم هن هنا
    هناك هو هي و يكون
    """.split()
)


#: short vowel marks, the dagger alef and the tatweel stretch
MARKS = re.compile("[\u064b-\u065f\u0670\u0640]")


def kept(question: str) -> list[str]:
    """The question's words, in order, less Arabic's common ones."""
    text = MARKS.sub("", unicodedata.normalize("NFC", question))
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
