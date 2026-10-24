<!-- willow-addon
section: Finding things
line: Index a big folder once, then ask it a list of questions in seconds, with the kernel's own answers, and see which passages another index lacks.
source: box
added: 2026-10-24
writes: to
network: none
tags: no-install, offline, writes-output, search, index
-->
# scan

Index a folder once, then ask it a list of questions in seconds.

    python adapters/stdlib/scan/scan.py index --from FOLDER --to INDEX
    python adapters/stdlib/scan/scan.py scan --index INDEX [--index INDEX ...]
        --questions FILE [--words FILE] [--top N]

The kernel reads your whole folder on every question, so nothing it says is
ever stale; the cost is time. On a programming language's source (26,000
files, 400,000 passages) one question takes it a minute and a half. `index`
does that reading once, and `scan` then answers each question in a fraction
of a second: the same passages, in the same order, as a `bite`.

**Exactly the kernel's answers.** The index keeps the kernel's own passages,
the date the kernel gives each one, and which passages hold each word, by
the kernel's `toks`. A question only narrows which passages the kernel's own
`rank` looks at: those holding at least half its words, the way `held_by`
holds them (word forms, a serial's ending, your words list), and every copy
of their text, since `rank` counts copies. `rank` then does the rest. The
tests hold it to every ranking case in [vectors/](../../../vectors/), the
ones the Java, TypeScript and C# kernels are held to, and to `rank` itself at
every depth.

**Questions:** one a line, or `name<TAB>question`; blank and `#` lines are
skipped. Each answer is a JSON line, every index's answers in turn:

    {"index": "8.5.11", "question": "618c", "state": "populated", "served": [
      {"rank": 2, "where": "main/rfc1867.c:622", "id": "5731…", "echo": false,
       "text": "…", "held_in": [], "gone_from": ["8.5.12"]}, …]}

**Across indexes:** a passage's id is the SHA-256 of its words, as
[stale](../stale/) uses it, so `gone_from` names each other index that
doesn't hold those exact words, and `held_in` each that does. Index two
releases, two backups or two drafts, and a passage gone from one is one that
changed there or went. Nothing else is compared.

**What an index is:** three files in `--to`: chunks.jsonl (each passage
and its date), words.tsv (each word and its passages) and index.json
(how many, which kernel, and a hash of the passages), written last. It holds
your folder's text, so keep it where you keep the folder. It is the folder
as it was read: index again after the folder changes. The same folder gives
the same bytes. One made with another `kernel.py` is refused, since its
passages and dates were that kernel's; so is one whose passages don't match
its index.json.

**Exit codes:** 0 something holds a question; 42 nothing holds any, or the
folder had nothing to read; 2 refused.

**Uses:** the kernel's `chunks`, `toks`, `dates`, `rank`, `words`, `stem`,
`echo`, `parse_words`, `canon` and `h256`. For one call it lifts the
kernel's `TOP` to `--top`, as [all](../all/) does, and answers `dates` from
the index, then puts both back; `kernel.py` is never changed.

**Never:** writes your folder or the record, or writes an index inside the
folder or around it, or over a folder that isn't an index. `scan` writes
nothing.
