# SOIL-PHYS-001: can willow's tools stand in for reading?

**DRAFT: not frozen.** Nothing has been asked of the sources but nonsense
(the dry run below). The freeze is a commit of its own, made before any
real quote, claim or question is asked.

SOIL-PHYS-001 is a speculative ledger on zero, symmetry breaking and
holography, written in DispatchesFromReality
(`research/soil-phys-001`). Its lines were checked by reading: for each line
whose source is held in full, the source's deciding words were quoted, and
every quote was then found in its file or read on the page. That gave 35
verdicts: 19 hold, 11 hold once reworded, 3 don't hold, 2 weren't in the
text first held (both since settled by a later text). Those verdicts, with
their quotes, are this study's answer key ([key.json](key.json)).

Willow has tools that claim parts of the same job. This asks three of them,
on the same 28 sources, and scores them against the key.

## The claim

> Over the ledger's sources as willow's readers turn them into text,
> `misquote` finds each deciding quote in the right source; `claim-check`
> finds, in the right source, a passage holding every part of each line
> that holds; and the kernel, asked a plain question for each such line,
> serves a passage from the right source among its top three; while
> off-topic claims and questions get nothing.

## The rules

Set before the run. A quote, claim or question whose source has no text
layer (a scan, or a font no reader turns into words: Casimir, Klein,
Goldstone's preprint, Solomonoff; `text_layer: false` in
[sources.json](sources.json)) is reported, never counted.

| Rule | What | Needed |
|---|---|---|
| R1 | `misquote` finds each deciding quote, as written or with its closest passage, in the right source | at least 90% of the 30 readable quotes |
| R2 | `claim-check` gives "all parts" from a passage in the right source to each line that holds (or holds once reworded) | at least 60% of the 25 readable such lines |
| R3 | The kernel, asked each such line's question, serves a passage from the right source among its top 3 | at least 50% of the 25 |
| R4 | Off-topic: `claim-check` gives "all parts" to at most 1 of 10 off-topic claims, and the kernel serves anything to at most 2 of 10 off-topic questions | both |

Reported, never counted, each with its prediction written here first:

- **P1**: of revision 1's 3 false claims, how many `claim-check` gives "all
  parts". Predicted at least 1: its card says it "finds where to read, and
  never reads for you", so a passage holding every word of a false claim
  backs it.
- **P2**: of the 5 quotes from sources with no text layer, how many
  `misquote` finds. Predicted 0.

## How it could be wrong

- **The claims share the sources' words.** They were written by the person
  who had read the quotes, close to the quotes, so `claim-check` is given an
  easy version of the job. R2 holding says the tool works when the claim is
  worded as the source words it; it says less about a claim worded freshly.
  The questions are plainer, which is what R3 tests.
- **The key was made by readers, not by an oracle.** Four agents read the
  texts and quoted them; every quote was then searched for in its file, or
  read on the rendered page; the verdicts were then a person's reading of
  what each quote decides. A wrong verdict is in the key as made.
- **"The right source" is a file name match.** A passage from another work
  saying the same thing counts against the tool here, though a reader might
  accept it.
- **Readers are part of the test.** The pdf reader's text decides what the
  tools can find: a garbled equation or a broken line is a miss for the tool
  that reads it.

## The dry run

`run.py --dry` (2026-11-06): every quote, claim and question replaced by
nonsense, over the same pile plus one nonsense passage the nonsense finds.
The pile built (24 PDFs, 2 HTML pages, 2 TEI transcriptions); `misquote`,
`claim-check` and the kernel each found the nonsense passage, so every
step's wiring after the tool ran; the denominators came out as above (30
readable quotes, 25 readable lines that hold); seven verdict rows named
`soil-phys-001:dry:`, and the box verifies. It found one break before it
mattered, in a test: the TEI transcriptions' first paragraph kept the end of
the opening tag; now cut after it.

## Running it

    python demo/soil-phys-001/fetch.py --to KEEP            # the open sources
    python demo/soil-phys-001/fetch.py --to KEEP --check    # offline
    python demo/soil-phys-001/run.py --keep KEEP --work WORK --out OUT.json --box BOX
    python kernel.py verify --box BOX

Four sources were downloaded in a browser where the publisher refuses
scripts (the three 1964 Physical Review Letters, and Goldstone's CERN
preprint); `fetch.py` says where from, and they go into KEEP by hand.
KEEP, WORK, OUT.json and BOX are outside the repo. The pdf reader needs
pypdf.
