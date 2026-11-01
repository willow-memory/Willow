# Small models: what Gemma 3 and Qwen2.5 did with willow, in one box

One night of handing small local models willow itself: its 270 add-on cards
to assemble, and a demo person's files to act on. Every result is here, the
code that made it, and one command that puts all of it, with the session
that ran it, into a willow box you can ask.

The models: Gemma 3 4B and 1B and Qwen2.5 3B, Q4_K_M GGUF, served by
llama.cpp (`llama-cpp-python` 0.3.36) on 127.0.0.1, on four CPU cores. The
person: [teodora](../teodora/), a bookkeeper, whose
[PLANTED.md](../teodora/PLANTED.md) is the answer key.

## What was tried, and what came of it

Each step's results are in [runs/](runs/); the code is in
[experiments/](experiments/).

1. **Picking from the cards** ([assemble.py](experiments/assemble.py)):
   each model was fed the 270 cards in batches of about 20 and picked 2 to
   4 that work together. In 36 batches neither invented an add-on name.
   Assembled into one pipeline, each plan had a sound core and a step that
   didn't belong. (`assemble-*.json`)
2. **A pipeline for a person** ([forperson.py](experiments/forperson.py)):
   built from the picked cards for Teodora, then run on her files. About
   half the steps did something useful; Qwen named `letters`, which it
   wasn't given, and the check threw it out. Qwen chose `bank` for her, which
   read 0 of her 58 statements: fixed in #132. (`person-*.json`)
3. **Willow picks the cards** ([cardpick.py](experiments/cardpick.py)): the
   model writes her needs, `scan --rank bm25` serves each need its cards from
   an index of all 270, and the plan may use only those. No inventions. With
   each card's opening paragraph added (`CARD_USES=1`), Qwen's plan was
   `bank`, `subscriptions` and `renewals`. `renewals` missed her MOT and her
   indemnity cover because the kernel won't guess a date like 09/11/2026:
   issue #133. (`pick-*.json`, `pick2-*.json`)
4. **A cited "this week" note, written by the model**
   ([weeknote.py](experiments/weeknote.py)): her add-ons' 191 lines, kept in
   chunks, then written up citing `[n]`. Qwen kept by position, not urgency,
   and nothing it wrote survived the checks. Gemma 4B chose well but wrote
   every invoice backwards ("Pay the…" for money owed *to* her). Two checks
   came out of it: a point's cited lines must hold half its words, and a
   point with no words is struck. (`weeknote*.json`)
5. **Code ranks, the model phrases** ([ranked.py](experiments/ranked.py)):
   rules label each fact with who owes whom (invoices you sent, unpaid, held
   against the bank) and rank them. Gemma 4B then wrote a note with her
   £2,140 owed first and the right way round, the paid Hargreaves invoice
   (her trap T2) marked to check rather than chase, and the insurance
   renewal. (`ranked*.json`)

## The box

    python demo/small-models/build.py --to DIR [--session FILE]
    python adapters/stdlib/plain/plain.py bite --box DIR/box "who owes teodora money"

[build.py](build.py) puts into one pile every result here and in
[../ofrenda/results/](../ofrenda/results/), flattened to one `where: what`
line a value, the ofrenda README and screenshots' text, and the
experiments' code, then makes a kernel box over it. Nothing goes online.

**The session is kept by its hash, never its text.** The Claude Code session
that ran all of this holds its user's own context and the assistant's
instructions, so it is not in this repository. [SESSION.json](SESSION.json)
names it by its first 5,944,224 bytes and their SHA-256; a session file only
grows, so a later copy of the same session still holds that part, and only
that part is read. `--session` takes the user's copy and, through willow's
own add-ons, [transcript-redact](../../adapters/stdlib/transcript-redact/)
takes out keys, home paths and emails, then
[agent-transcript](../../adapters/stdlib/agent-transcript/) writes its 169
spoken turns, numbered. Tool calls and their output are not turns, so they
are not in it: the runs hold what came out, the session why.

Building it found a bug in transcript-redact, fixed here: in a JSON
transcript a line break is the two characters `\n`, so a line starting
`@AGENTS.md` or `@pytest.mark` read as the email `n@AGENTS.md`, and taking
it out left `\[redacted:email]`, which no JSON reader accepts. Four lines of
this session came out unreadable, and agent-transcript skipped the file.

## Asking it

Asked with plain of the box built with the session, 2026-11-01:

| question | the passage served first | |
|---|---|---|
| which model told the biscochitos secret | session turn 50: Qwen, the only one | ✔ |
| why did bank skip teodora's statements | session: lower-case headers; and the run where bank exited 42 | ✔ |
| why does the kernel not read 09/11/2026 | session: a day and month that could swap; issue #133 | ✔ |
| who owes teodora money | session: the invoices are hers, owed to her | ✔ |
| how is a point struck in the week note | weeknote.py's own docstring, and a struck point | ✔ |
| which add-on name did qwen invent | session lines about inventing; `letters` not in the top three | ½ |
| what did the 1B ghost say about the analytical engine originating anything | the ofrenda README's opening, not the 1B's "Yes" | ✘ |
| why does openai-compatible wait fifteen minutes | nothing served: said beside a tool call, so not a turn | ✘ |
| why was the session kept by hash | passages about other hashes: it was decided after the frozen bytes end | ✘ |

Without `--session`, the box still answers the first from the ofrenda
README's run 2 ("Qwen told the secret … Neither Gemma did"), which
[test_small_models.py](test_small_models.py) holds.

## What wasn't checked

- The runs are one run each, at temperature 0 with seed 0; two of the
  ofrenda replies came back worded differently after a server restart.
- The experiments' scripts are kept as they ran, paths aside; they need the
  model servers to run again, and their outputs would land in `WORK`.
- `ranked.py`'s rules were written after reading Teodora's files, though
  each is about a kind of fact, not about her; on another person they are
  untried.
