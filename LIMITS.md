# Limits

What willow doesn't do. Some of it is on purpose, and asking for it is
asking to reopen a decision in [DECISIONS.md](DECISIONS.md). The rest is
where it falls short today, and a fix is welcome.

## On purpose

- **It doesn't go online,** or send anything anywhere. An add-on can, and
  its card says where and why.
- **It doesn't make up an answer.** No model writes one; when your files
  don't hold it, it says so (exit 42).
- **It answers; it doesn't point.** A passage is served only when it holds
  half your question's words, so a long or roundabout question can find
  nothing where a looser search would point at the right file. Pointing at
  where to look is `scan --rank bm25`, which always serves its top passages:
  on demo/php2shell's out-of-sample CVEs it found 7 of 7 to the kernel's 1.
  Loosening the kernel's rule found a few more there but answered questions
  about other bugs several times as often (`demo/php2shell/hold.py`; its
  table is in that study's README).
- **It doesn't approve anything itself.** Suggestions wait until a person
  approves them with their key.
- **It doesn't keep your words.** The record holds fingerprints and places,
  never what you asked or what was found.
- **It doesn't write to your folder.** It only ever reads it.
- **It doesn't keep an index** of your folder; it reads it fresh each time.

## Where it falls short

- **It matches words, not meanings.** Ask "who owes me money" when your
  files say "invoice outstanding" and it finds nothing until a words list
  connects them.
- **English is built in.** The kernel's common-word list and word-form
  rules are English. The words-de, words-es, words-fr, words-it, words-nl
  and words-pt add-ons set German, Spanish, French, Italian, Dutch and
  Portuguese common words aside before a question reaches it; other
  languages keep every word. Word forms are English's only, and words in
  other scripts are matched only as written.
- **No index, so time grows with the size of the folder.** On Odile's
  folder a question takes about a quarter of a second; a very large folder
  would want an index, in an add-on.

A shortfall with a test that shows it is a known bug, and is listed in
[BUGS.md](BUGS.md).
