# Why a question found nothing

Exit 42 is an answer, not a fault: your files don't hold enough to say a
person said it. The usual reasons:

- **It matches words, not meanings.** Ask "who owes me money" when your
  files say "invoice outstanding" and nothing comes back until a words list
  connects them ([kernel.md](kernel.md)).
- **A passage needs half the question's content words.** That is what
  keeps it from answering with something you didn't write, and it is not
  loosened. To be pointed at where to look instead, `scan --rank bm25`
  always serves its top passages ([scan](../../adapters/stdlib/scan/)).
- **English is built in.** Its common words are dropped from a question;
  in other languages every word counts, unless a words add-on for that
  language is in your stack.
- **A date counts only when written in full.** "Nov 17" with no year, or
  a file name with only a year and month, dates nothing: the kernel never
  guesses a day.

What it falls short of, and why, is in [LIMITS.md](../../LIMITS.md); the
known bugs, each shown by a test, are in [BUGS.md](../../BUGS.md).
