# willow

**Ask questions of your own files, and get back only what you wrote or what
you approved.**

`kernel.py` is a single Python file that searches a folder you choose, answers
in your files' own lines with the file and line number for each, and refuses
to guess when your files don't hold an answer. Answers from anywhere else (an
AI model, a script, another person) are held until you approve them with a
private key. Every step is written to a tamper-evident log you can audit at
any time.

- **One file, no dependencies:** Python 3.9 or newer, standard library only.
  Copy `kernel.py` anywhere and run it.
- **Local only:** it has no network code at all, and a test enforces that.
- **Verifiable:** the log is a hash chain. Any edit to a past entry is
  detected, and a forged approval is never accepted.
- **Portable:** reimplemented in Java, TypeScript and C#, and all four are held
  to the same 4,463 test cases.

## Your first five minutes

Everything below runs from a fresh clone with nothing installed beyond Python.
The output shown is real.

### 1. Check it works on your machine

```
$ git clone https://github.com/willow-memory/willow && cd willow
$ python kernel.py test
kernel: the eight beats held
```

`test` sets up a throwaway folder, runs every command, and checks eight
properties, among them that an unapproved suggestion is never given as an
answer, a forged approval is rejected, and an edited log is refused.

### 2. Ask questions of someone else's files

The repo includes made-up people to try it on. Odile is a piano tuner and
beekeeper with six years of notes, logs, texts, letters and receipts.

```
$ python demo/odile/make_life.py           # writes her 254 files into demo/odile/life/
$ python kernel.py init --box odile-record --pile demo/odile/life --key odile.key
ready: record started, row 0 6ecb8f01be3521d6

$ python kernel.py bite --box odile-record "how are the bees"
```

`init` made two things: `odile-record/`, the folder where the log is kept,
and `odile.key`, the private key that approves answers. Odile's own folder is
only read.

The answer is JSON: up to three passages, each with its file, line and text.
Here they are the three most recent hive inspections from `hives/2026.txt`,
newest first, because her log has a date over every entry.

### 3. Ask something her files don't say

```
$ python kernel.py bite --box odile-record "when is the county deadline"
```

```json
{
  "state": "populated",
  "served": [
    { "where": "mail/2026-03-20-county.txt:12",
      "text": "... You may file a response or an\nobjection within 180 days of the date of this notice. ..." },
    { "where": "mail/2026-03-20-county.txt:10", "text": "NOTICE OF PROPOSED DETERMINATION OF WATER RIGHT" },
    { "where": "mail/2026-03-20-county.txt:8",  "text": "RE: Case No. WR-2026-0117" }
  ],
  "look": [
    { "why": "no file in your folder has deadline",
      "where": "it may be called something else there",
      "next": "add it to your words list, or use a search that matches by meaning" }
  ]
}
```

(Trimmed: each passage also carries an `id` and an `echo` flag.) Her files
never say "deadline", and the output says so rather than pretending. The
county's letter is still found from the other words. When no passage holds
enough of the question, the exit code is 42 and nothing is served.

### 4. Teach it her words

"Who still owes me money" brings back a text message about money, because her
files never say "owes": her invoices do. A words list connects the two:

```
$ printf 'owes = invoice, outstanding\n' > words.txt && chmod 600 words.txt
$ python kernel.py init --box odile-record-2 --pile demo/odile/life --key odile.key --words words.txt
$ python kernel.py bite --box odile-record-2 "who still owes me money"
```

Now two of the three passages are her unpaid school-district invoices, and
the output says why: `"read owes as invoice, from your words list"`.

### 5. Approve an answer

Suppose an assistant read the county letter and suggests an answer. It hands
it in, citing the passage it relied on (the passage's `id` from step 3):

```
$ cat rows.jsonl                           # one suggestion per line; wrapped here
{"path": "county.md", "data": "Reply by 2026-09-16: 180 days from the 2026-03-20 notice.",
 "cites": ["0e4ba2df…"], "claim": "the notice gives 180 days to file"}

$ python kernel.py propose --box odile-record --file rows.jsonl
pass  proposal:0a6fde95…  waiting on your seal          (exit 42: waiting on you)

$ python kernel.py out --box odile-record
waiting on your seal: proposal:0a6fde95…
5 rows; 0 sealed; 1 waiting

$ python kernel.py seal --box odile-record proposal:0a6fde95…
sealed proposal:0a6fde95…; written to written/county.md

$ python kernel.py bite --box odile-record "When is the county deadline?"
{"state": "sealed", "answer": "Reply by 2026-09-16: 180 days from the 2026-03-20 notice.", "by": "proposal:0a6fde95…"}

$ python kernel.py verify --box odile-record
the chain holds: 7 rows, 1 sealed
```

The same question, typed with different case and punctuation, now returns the
approved answer. Until `seal` ran it was only a suggestion, and it was never
given as an answer.

Then point it at a folder of your own:

```
$ python kernel.py init --box my-record --pile path/to/your/folder --key my.key
$ python kernel.py bite --box my-record "your own question"
```

Keep the key somewhere other than the record folder; `init` refuses a key
inside it.

## How it works

```
your folder ──read on every question──▶ paragraphs ──ranked──▶ top 3 passages
(--pile)                                                          │
                                                                  ▼
suggested answers ──checked──▶ held, waiting ──you approve──▶ given as the answer
(propose)          (cites must be       (out lists them)   (seal, with your key)
                    passages just shown)
                                  every step ──▶ hash-chained log (--box)
```

### Reading your folder: there is no index

Nothing is copied or indexed. On every question `kernel.py` walks the folder
fresh, so it always sees the files as they are now and leaves nothing behind
to fall out of date or leak. On Odile's 254 files (1.3 MB, about 1,100
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

### Finding answers

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

### Your own words

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

### Your key

`init` creates the key: 32 random bytes, written as hex to the file you name,
readable only by you (mode `600`). An approval is an HMAC-SHA-256 of the exact
suggested answer, made with that key.

- Only someone with the key file can approve an answer.
- `kernel.py` refuses a key stored inside the record folder, so copying the
  record never copies the means to approve.
- If the key is lost, past approvals can no longer be checked: they stop
  being given as answers, and `verify` reports them as unproven. Back it up
  like any private key.

### The record folder

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

### Suggestions and approvals

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
for the same words in the same order, regardless of case and punctuation.

## Commands

```
python kernel.py init    --box DIR --pile FOLDER --key FILE [--words FILE]
python kernel.py bite    --box DIR "your question"
python kernel.py propose --box DIR --file SUGGESTIONS.jsonl
python kernel.py seal    --box DIR proposal:<sha256>
python kernel.py verify  --box DIR
python kernel.py out     --box DIR
python kernel.py test
```

| Command | Does |
|---|---|
| `init` | creates the record folder and your key, and links your folder |
| `bite` | answers a question: an approved answer if there is one, else up to three passages from your files |
| `propose` | takes suggested answers and holds the ones that pass |
| `seal` | approves one suggestion with your key |
| `verify` | checks every line of the log and every approval |
| `out` | lists what is waiting for your approval |
| `test` | runs the whole cycle in a temporary folder and checks eight properties |

The commands that write to the log also take `--now TIMESTAMP`, to fix the
time recorded (for scripts and tests).

The exit code is meant for scripts and for other programs calling it:

| Code | Means |
|---|---|
| `0` | a person said it: your files hold it, or you approved it |
| `42` | not enough to say a person said it: nothing matched, or something waits on you |
| `2` | refused: a bad command, a key or record that isn't right, a log that has been changed |

## Guarantees, and the tests behind them

Each is a test that fails if it stops being true.

| Guarantee | Enforced by |
|---|---|
| Never goes online | `test_kernel.py` parses the file and fails on any network module, `eval`, `exec`, `compile` or `__import__` |
| Never stores your words | the log is checked for the question's and answer's words after a full cycle |
| Never gives a suggestion as an answer until it's approved | `kernel.py test`: a suggestion without a seal is listed as waiting, not given |
| Never accepts a forged approval | `kernel.py test`: a seal with the right shape and a re-hashed chain is still rejected |
| Never writes past a change | `kernel.py test`: one edited field in one past line, and every command refuses |
| Same answer every run | the ranking is checked under different hash seeds |

## Where it falls short

- **It matches words, not meanings.** Ask "who owes me money" when your files
  say "invoice outstanding" and it finds nothing until a words list connects
  them.
- **English is built in.** The common-word list and the word-form rules are
  English. Questions in other languages work, but no common words are set
  aside, and words with accents or in other scripts are matched only as
  written.
- **No index,** so time grows with the size of the folder.
- **One writer at a time on Windows.** File locking uses `fcntl`, which
  Windows doesn't have.

It was tested blind. For two of the three characters, a separate AI agent
that never saw the code wrote the files, the needs hidden in them, and the
questions the person would ask; the answers were then scored against what was
hidden. It found what was asked in the files' own
words and missed the rest. The full results, misses included, are in
`demo/*/STRIP.md`.

## How it's verified

- **CI on every push:** the tests on Python 3.9 through 3.14, lint, every
  port, and every demo rebuilt and checked.
- **Four implementations, one behaviour.** `vectors/gen.py` reads 4,463 cases
  out of `kernel.py`, covering canonical JSON, word splitting, HTML text,
  ranking, dates, word forms and every refusal. The Java, TypeScript and C#
  ports must give byte-identical answers. Then the same session runs through
  all four command lines, and every implementation's log is verified by every
  other.
- **The tests were tested.** Bugs were planted deliberately in copies of the
  ports (sorting by UTF-16 instead of code points, floating-point scores, a
  BOM dropped by Node's decoder, and more). A case was added for each one the
  tests missed. The table is in [vectors/README.md](vectors/README.md).
- **Old runtimes, not assumed:** the tests and every port have also been run
  on Python 3.9.0, JDK 11, Node 14 and .NET 5, all from 2020.

## What's in this repo

```
willow/
├── kernel.py                 the whole program (about 910 lines)
├── test_kernel.py            its tests
├── adapters/                 add-ons built on top of kernel.py
│   ├── README.md             the rule every add-on follows
│   └── readings/
│       ├── readings.py       notes beside an answer: numbers over time, dates gone by
│       ├── test_readings.py
│       └── README.md         what it adds, what it uses, what it never does
├── ports/                    kernel.py rewritten in other languages
│   ├── java/Kernel.java      JDK 11+, standard library only
│   ├── ts/kernel.ts          Node 14+; TypeScript only to compile
│   └── csharp/Kernel.cs      .NET 5+, no packages
├── vectors/                  what keeps the four implementations identical
│   ├── gen.py                reads the test cases out of kernel.py
│   ├── cases.json            4,463 cases, with the answers kernel.py gives
│   ├── kernel_tables.json    Python's Unicode and HTML rules, so ports don't use their own
│   ├── compare.py            runs every port against the cases and each other's logs
│   ├── test_vectors.py       fails if the cases are stale or a port disagrees
│   └── README.md             how the ports were built and what testing them found
├── demo/                     three made-up people to try it on
│   ├── odile/                piano tuner and beekeeper, caring for her father
│   │                         (her questions are in her STRIP.md, not a QUESTIONS.md)
│   ├── hollis/               built blind, by an agent that never saw the code
│   └── teodora/              built blind, from a different line of work
│       ├── make_life.py      writes the person's files into life/, the same bytes every run
│       ├── CHARACTER.md      who they are and how their life is written down
│       ├── PLANTED.md        the needs hidden in their files, and the traps
│       ├── QUESTIONS.md      the questions they would ask
│       └── STRIP.md          what kernel.py found and missed, scored against PLANTED.md
├── .github/workflows/
│   ├── kernel.yml            tests on Python 3.9 to 3.14, and lint
│   ├── vectors.yml           every port; fails if any port didn't run
│   └── demo.yml              rebuilds each person's files and checks them
├── ruff.toml                 lint settings
└── LICENSE                   Apache-2.0
```

## Building on it

**Add-ons** go in `adapters/`. An add-on may use `kernel.py`; `kernel.py`
never uses an add-on, and runs the same without any. An add-on writes to the
log only through `kernel.py`, so `verify` still holds. Each one has its code,
a short card saying what it's for and what it never does, and tests that CI
runs. [adapters/readings](adapters/readings/) is the first: it adds notes
beside an answer, such as how a number in a dated table has moved, or a date
in a log that has passed with nothing written since.

**Ports** to another language go in `ports/` and must pass
`python vectors/compare.py` with zero unexplained differences. Go and Rust are
the obvious next ones; [vectors/README.md](vectors/README.md) explains how the
existing three were made to agree.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
