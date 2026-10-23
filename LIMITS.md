# Limits

What willow doesn't do. Some of it is on purpose, and asking for it is
asking to reopen a decision in [DECISIONS.md](DECISIONS.md). The rest is
where it falls short today, and a fix is welcome.

## On purpose

- **It doesn't go online,** or send anything anywhere. An add-on can, and
  its card says where and why.
- **It doesn't make up an answer.** No model writes one; when your files
  don't hold it, it says so (exit 42).
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
- **English is built in.** The common-word list and the word-form rules are
  English. Questions in other languages work, but no common words are set
  aside, and words with accents or in other scripts are matched only as
  written.
- **No index, so time grows with the size of the folder.** On Odile's
  folder a question takes about a quarter of a second; a very large folder
  would want an index, in an add-on.
- **One writer at a time on Windows.** File locking uses `fcntl`, which
  Windows doesn't have.

A shortfall with a test that shows it is a known bug, and is listed in
[BUGS.md](BUGS.md).
