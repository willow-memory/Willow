"""words_tr.py: questions in Turkish, without Turkish's common words. Python 3.9+.

    python adapters/stdlib/words-tr/words_tr.py bite --box DIR [--now TS] "Benim diş hekimi randevum ne zaman?"
    python adapters/stdlib/words-tr/words_tr.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Turkish keeps every word, so its common words ("ve",
"bir", "bu") count toward a match too, and nearly every Turkish passage holds
them. `bite` takes Turkish's common words out first and asks the kernel with
what's left: "Benim diş hekimi randevum ne zaman?" is asked as "diş hekimi
randevum zaman". The kernel's own bite does the rest: the record, the passages, the
exit code. An answer you approve is kept for the words asked, so ask through
here each time.

A capital dotted İ is read as i before anything is compared, since lowercased
it would split the word in two ("İstanbul" would be "i" and "stanbul").
Letters typed as a letter and an accent mark are joined first. A question of
nothing but common words is refused: name the thing you mean.

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

#: Turkish's conjunctions, postpositions, particles, pronouns, the verb
#: "be", question words, yes and no: what the kernel's own FUNCTION list holds for
#: English
COMMON = frozenset(
    """
    acaba ama ancak artık aslında az bana bazı ben beni benim bile bir biz
    bize bizim böyle bu bunu bunun bunlar burada çok çünkü da daha de değil
    diye en gibi hangi hem henüz her herhangi hiç için ile ise kadar kim
    mı mi mu mü nasıl ne neden nerede nereye niçin niye o olan olarak
    oldu olduğu olmak olsun ona onu onun onlar orada öyle şey şu siz size
    sizin sonra tüm ve veya ya yani yoksa
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Turkish's common ones."""
    text = unicodedata.normalize("NFC", question).replace("İ", "i")
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
