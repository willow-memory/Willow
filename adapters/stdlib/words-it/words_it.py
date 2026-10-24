"""words_it.py: questions in Italian, without Italian's common words. Python 3.9+.

    python adapters/stdlib/words-it/words_it.py bite --box DIR [--now TS] "Quando è l'appuntamento dal dentista?"
    python adapters/stdlib/words-it/words_it.py list

The kernel leaves English's common words ("the", "when", "is") out of a
match. A question in Italian keeps every word, so its common words count
toward a match too, and nearly every Italian passage holds them. `bite` takes
Italian's common words out first and asks the kernel with what's left:
"Quando è l'appuntamento dal dentista?" is asked as "appuntamento dentista". The kernel's own bite does the rest: the record,
the passages, the exit code. An answer you approve is kept for the words
asked, so ask through here each time.

Letters typed as a letter and an accent mark (some keyboards send them that
way) are joined before anything is compared, so "perché" matches however
it was typed. A question of nothing but common words is refused: name the
thing you mean. "l'", "dell'" and the other joined articles are left out as their own words.

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

#: Italian's articles, conjunctions, prepositions, pronouns, the verbs "be",
#: "have" and the modals, question words, yes and no: what the kernel's own
#: FUNCTION list holds for English
COMMON = frozenset(
    """
    a abbiamo agli ai al all alla alle allo anche avere avete c che chi
    ci col come con cosa d da dagli dai dal dall dalla dalle dallo degli
    dei del dell della delle dello deve devo devono di dove e ed era
    erano essere fra gli ha hai hanno ho i il in io l la le lei lo loro
    lui là lì ma mi mia mie miei mio molto ne negli nei nel nell nella
    nelle nello no noi non nostra nostre nostri nostro o od per perché
    più posso possono può qua quale quali quando quanta quante quanti
    quanto quella quelle quelli quello questa queste questi questo qui
    se si sono sta stata stato su sua sue sugli sui sul sull sulla sulle
    sullo suo suoi sì ti tra tu tua tue tuo tuoi un una uno vi voglio
    voi vostra vostro vuole è
    """.split()
)


def kept(question: str) -> list[str]:
    """The question's words, in order, less Italian's common ones."""
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
