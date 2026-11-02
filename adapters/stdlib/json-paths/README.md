<!-- willow-addon
section: Reading more kinds of files
line: Any JSON or JSON Lines file as plain lines, one passage per record, each value beside its key.
source: new
added: 2026-11-02
writes: to
network: none
-->
# json-paths

Any JSON file, read as it is: a value to a line, a record to a passage.

    python adapters/stdlib/json-paths/json_paths.py mirror --from FOLDER --to MIRROR

The kernel reads a .json file as raw text. Minified, it is one long line, cut
every 500 characters with keys torn from their values; pretty-printed, one
record is spread over lines of brackets and runs into the next. This writes
each value on a line of its own, beside its key, and each record as one
passage headed by its place in the file:

    shop: Hollow Lane Grocer

    orders
    [0].id: 7
    [0].items[0].name: leeks

It reads .json, and .jsonl and .ndjson (one value per line, each line a
record headed `#12`, its line in the file).

- **A record to a passage.** The records are the elements of the first array,
  from the top, that is too big for one passage (a top-level array, or
  `orders` in `{"orders": [...]}`), so "what was in order 103" lands on that
  order alone, its fields together. Above them, the top's plain values run
  together and each array or object is its own passage. A record too big
  for a passage fills several under the same heading, cut between lines,
  never inside one.
- **Keys every record has are left out.** A key in more than half a file's
  records, or more than half its passages (three at least), would put its
  words in passage after passage, and a question pairing one of them with
  anything else ("volcano date") would be answered with an unrelated record.
  So a chat export's messages are written as their values: the date, who,
  the text. A key that names its value (a file's path, in a map of them) is
  in one record and stays. The cost: a question needing two such keys to
  reach half its words ("bluesky kind section network") is not found.
- **Values as the file writes them.** Numbers digit for digit (`1.50` stays
  `1.50`), `true`, `false`, `null`; strings without quotes, but an empty one
  as `""`. A key with a space, dot, bracket, quote, colon or backslash is
  written in brackets as a JSON string, `["first name"]`. A key given twice
  keeps both values. A string's own lines are lines here too, wrapped at a
  space past 240 characters; control characters are written as JSON escapes.
- **Caps.** Arrays and objects nested deeper than 32 levels are written as
  compact JSON on one line; a string is kept to 10,000 characters and says
  how many more there were; a file over 50 MB is not read. A mirror bigger
  than the kernel reads from one file (1 MB) is cut between passages into
  `<name>.txt`, `<name>.part2.txt` and on; parts a shorter earlier run left
  behind are removed.

The readers for one program's export (day-one, trello, karakeep, sbom,
gh-json and the rest) read their own files with meaning: whose post, which
card, which package. This one knows no program; it reads any JSON as it is.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that isn't UTF-8 (a BOM is fine), isn't JSON, or
holds only `[]` or `{}` is skipped and counted, never a crash. In a JSON
Lines file a bad or empty line is skipped and counted in a passage of its
own at the end, `skipped 2: 4, 9`:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) and
`MAX_CHUNK` and `MAX_FILE`; Python's standard library `json` for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
