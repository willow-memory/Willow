<!-- willow-addon
section: Trust and proof
line: Your approved answers as Jeles nuggets, with question, answer, sources and who sealed it, and Jeles' own verified nuggets read back as passages.
source: new
added: 2026-11-01
writes: to
network: none
tags: no-install, offline, writes-output, trust
-->
# jeles

[Jeles](https://github.com/hornbook-knowledge/jeles) keeps verified
question-and-answer pairs, nuggets, each with its sources and who verified it.
This reads them as passages, and writes your approved answers out as nuggets.

    python adapters/stdlib/jeles/jeles.py mirror --from FOLDER --to MIRROR
    python adapters/stdlib/jeles/jeles.py export --box DIR --questions FILE --to OUT.json

## mirror

Walks FOLDER, skipping hidden folders and files, for Jeles' two shapes:

- a **seed file** (a .json file): a `pairs` list of `source_text` (the question) and
  `target_text` (the answer), or a bare list of them, as the seed Jeles ships;
- a **corpus store** (a .db file): the SQLite `records` table whose rows hold a
  question and an answer, as Jeles keeps them under its store root.

Each nugget becomes one paragraph:

    What is a black hole?
    A region where gravity lets nothing escape.
    sources: https://science.example.gov/black-holes
    verified: human, by ada, 2026-10-01

The `verified` line is Jeles' own word for how far a nugget has been checked
(its rung, who and when). A seed pair nobody has signed says `asserted (a seed
pair nobody has signed)`, as Jeles itself treats it. A signature is never
copied, a deleted record is left out, and so is a logged gap (a question with
no answer yet). Each file goes to MIRROR at the same relative path with .txt
added; a file that isn't either shape is skipped and counted. Point the kernel
at MIRROR to ask what Jeles knows.

## export

Your approved answers, as a Jeles seed file. willow's record never holds a
question's words, only their hash, so you give the questions, one per line,
in FILE. A question is paired with an approval **only when its words hash to
the key the approval was sealed under**, the kernel's own `bite_key`; nothing
is matched by guessing. The line you typed is kept as you typed it.

Each pair has the answer, the reason the suggestion gave, the passages it
cited (as `evidence`), and when it was sealed. Its `verified_by` says it's a
willow seal and not a Nestor seal, so Jeles installs it at its `asserted`
rung: your key's proof is something only your box can check. Only approvals
whose proof holds under your key, and whose proposal still holds the sealed
bytes, are exported. OUT.json must not exist yet, and its folder must.

    wrote 1 pairs to willow.json; 0 approvals had no question here; 1 questions matched no approval

**Exit codes:** mirror, 0 wrote some, 42 nothing readable; export, 0 wrote
some, 42 no question matched an approval; 2 refused.

**Uses:** the kernel's `read`, `sealed`, `standing` and `bite_key`.

**Never:** writes inside FOLDER, copies a signature, reads the key, or
marks anything verified that Jeles can't check.
