# How it works

```
your folder ──read on every question──▶ paragraphs ──ranked──▶ top 3 passages
(--pile)                                                          │
                                                                  ▼
suggested answers ──checked──▶ held, waiting ──you approve──▶ given as the answer
(propose)          (cites must be       (out lists them)   (seal, with your key)
                    passages just shown)
                                  every step ──▶ hash-chained log (--box)
```

## Reading your folder: there is no index

Nothing is copied or indexed. On every question `kernel.py` walks the folder
fresh, so it always sees the files as they are now and leaves nothing behind
to fall out of date or leak. On Odile's 254 files (310 KB, about 1,100
paragraphs) a question takes about a quarter of a second. The cost grows with
the folder, so a very large folder would want an index, which belongs in an
add-on, not the kernel.

What it reads:

- **Any text file, whatever its name or extension.** A file is text if it is
  UTF-8 with no NUL byte in its first 8 KB. Binaries, files over 1 MB and
  hidden files and folders (names starting with `.`) are skipped.
- **Web pages as the text they show.** Scripts, styles, comments and tags are
  stripped, entities decoded, and line numbers still point at the original.
- **Paragraph by paragraph.** A blank line ends a passage, and no passage runs
  past 500 characters, so one long file can't match every question.

Your folder is never written to.

## Finding answers

A question is split into words. Common English words ("the", "how", "do",
"when", …) are set aside, and a passage must contain at least half of the
rest to count. Matching passages are scored so that **rarer words count for
more**: a word that appears in two passages outweighs one in fifty. Ties are
broken in this order:

1. something written once before something repeated every week,
2. **newer before older,**
3. the file path, then the later line in a log.

At most three passages are returned, never the same text twice. Scores are
exact fractions, not floating point, so the same folder and question give the
same order on every run, every Python version, and in every port.

It adapts to how people actually write:

| It handles | Example |
|---|---|
| Word forms | "owe", "owes", "owed" and "owing" match each other (English suffix rules) |
| Folder names | a file in `dad/` matches "Dad's weight" even if the file never says "Dad" |
| Dates, for "newest first" | `2026-10-14`, `20261014`, `21/10/2026`, `10.21.2026`; a date that could be read either way round (`11/03/2023`) is left undated, never guessed. A log's date heading covers the lines under it |
| Serial and case numbers | "the one ending 672841" finds `1HGEJ6672841` |
| Questions echoed back | an FAQ line that only repeats your question is marked `"echo": true` and doesn't count as an answer |
| Your own vocabulary | a words list (below) |
| Code | if a returned passage defines a function, it says where else in the folder that name appears |

When nothing matches, it exits with code 42 and says which of your words no
file contains.

## Your own words

People don't use the same words as their files. A words list teaches
`kernel.py` yours:

```
# words.txt — one word, then the words your files use for it
owes = invoice, outstanding
due = next
```

Give it at setup with `init --words words.txt`. Like the key, it must be
readable only by you (`chmod 600`) and kept outside the record folder. When
the list changes an answer, the output says so ("read owes as invoice, from
your words list"), and the log records a fingerprint of the list, never its
contents.

## Your key

`init` creates the key: 32 random bytes, written as hex to the file you name,
readable only by you (mode `600`). An approval is an HMAC-SHA-256 of the exact
suggested answer, made with that key.

- Only someone with the key file can approve an answer.
- `kernel.py` refuses a key stored inside the record folder, so copying the
  record never copies the means to approve.
- If the key is lost, past approvals can no longer be checked: they stop
  being given as answers, and `verify` reports them as unproven. Back it up
  like any private key.

## The record folder

`--box` names the folder where `kernel.py` keeps its record. `init` creates
it:

```
odile-record/
├── kernel.json        where your folder, key and words list are
├── record.jsonl       the log: one JSON line per step, hash-chained
├── proposals/         suggested answers, one file each, named by their hash
└── written/           approved answers, written out as files
```

Each log line holds what happened (setup, question, suggestion, approval,
check), when, and the hash of the line before it. A question is recorded as a
fingerprint of its words plus the file and line of each passage returned,
**never the words of the question or the passages**. Any edit to a past line
breaks the chain, and from then on every command refuses to write until a
person looks. Writes take a file lock and are flushed to disk, and a
half-written last line is detected rather than repaired silently.

## Suggestions and approvals

A suggestion is one JSON line with exactly four fields:

| Field | Rule |
|---|---|
| `path` | where the approved answer will be written, a plain relative path inside the record folder |
| `data` | the answer itself |
| `cites` | ids of passages it relies on, which must come from the most recent question's results |
| `claim` | a non-empty reason |

Anything else is refused, line by line, with the reason logged. A suggestion
that passes waits. `seal` approves one by its hash; if its file has changed
since it was suggested, the approval is refused. An approved answer is given
for the same words in the same order, regardless of case and punctuation, and
only while its file still holds the bytes you approved and the record still
says which question it was approved for; `verify` says when it doesn't.

Back to the [README](../README.md).
