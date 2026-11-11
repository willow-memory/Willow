<!-- willow-addon
section: Assistants
line: One sentence a model on this machine says about your boxes, struck and left to code when it adds a word or number they lack.
source: new
added: 2026-11-11
version: 0.1.0
writes: nothing
network: loopback
role: suggests
output: report
uses: say-check
from: code, https://github.com/willow-memory/willows-grove, Apache-2.0
-->
# say

One sentence a model on this machine says about your boxes, struck and left to code when it adds a word or number they lack.

    python adapters/stdlib/say/say.py --boxes FILE [--you "your line"] [--earlier FILE] [--model TAG] [--host HOST:PORT] [--timeout SECONDS] [--json]

    say: populated, the sentence stands, said by qwen3:4b
      said                       You need to ratify the work order [b5]. PR 712's still waiting [b4].
      every cite was served      held
      every box cited            held
      nothing the boxes lack     held
      your words quoted exactly  nothing quoted

Code finds things and says them plainly. A small model can say the same
things in a sentence you would rather read. This asks one, on this
machine, for one sentence about the boxes you give it. Then it holds that
sentence to the boxes with [say-check](../say-check/)'s four checks. The
model is a writer, never an authority.

## A sentence that adds anything is struck

    say: populated, struck: 1 of 4 checks failed; code's own line stands
      struck                  You need to ratify the work order [b5]. PR 712's waiting, 140 tests pass [b4].
      nothing the boxes lack  failed: 140 is no box's

A sentence is struck when it adds a number or a word the boxes lack, cites
a box it wasn't given, leaves a box out, or misquotes you. The struck
sentence is shown with the checks it failed, and the exit code is 42.
Whatever asked for the sentence shows code's own line in its place.

Small models are struck often. That is the add-on working: a sentence
that says "the person still owes money" about boxes that never say
"person" or "owes" has added to what was found.

## What the model is told

- Say one short sentence about the boxes, and nothing else.
- Use only their facts: no number, name or status they lack.
- Put each box's tag after its fact, like `[b1]`. Cite every box once.
- Say them in the order given.
- The only free words are say-check's glue words.
- Quote the person only word for word, or not at all.

`--you "your line"` is what you asked. `--earlier FILE` is boxes shown
earlier in the same sitting; the sentence may refer back to one by its
tag. `--boxes FILE` is the boxes, as say-check reads them: a list of
`{"id", "text"}`, or any report add-on's `--json`.

## The model is on this machine, or it isn't asked

The model is [Ollama](https://ollama.com)'s. `--host` (or Ollama's own
`OLLAMA_HOST`, or `127.0.0.1:11434`) must be this machine: `127.0.0.1`,
`localhost` or `::1`. Any other address is not asked, and the report says
so. `--model` is the tag, `qwen3:4b` unless you give one. `--timeout` is
how many seconds to wait for the sentence, 60 unless you give more; a
model loading for the first time can take longer.

When nothing answers, the tag isn't installed, or the wait runs out, the
report is `unreachable` with the reason, and the exit code is 42:

    say: unreachable, qwen3:4b at http://127.0.0.1:11434: that model isn't installed

It reads the files it is given and asks the model on this machine. It
writes nothing: no row on your record, no file. It prints
[a report](../ci/README.md#the-report-contract); `--json` gives the same as
one JSON object.

Exit codes, the kernel's: 0 the sentence stands; 42 it was struck, or the
model couldn't be asked; 2 refused.

The prompt, the voice and the way Ollama is asked are
[willows-grove](https://github.com/willow-memory/willows-grove)'s, from the
part of it that says boxes aloud.
