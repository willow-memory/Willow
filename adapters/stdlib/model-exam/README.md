<!-- willow-addon
section: Assistants
line: Any model scored against the answers you sealed, your own questions as its exam, before you trust its suggestions.
source: new
added: 2026-11-02
writes: nothing
network: the endpoint you configure, to ask your sealed questions
uses: openai-compatible
-->
# model-exam

A model sits an exam of your own questions, marked against the answers you
sealed, before you trust its suggestions.

```
python adapters/stdlib/model-exam/model_exam.py --box DIR --url http://127.0.0.1:8080/v1 \
    --model gemma-3-4b-it --questions exam.txt

pass      what goes in biscochitos  (cites [1] as you did; 4 of 4 words)
fail      when does the gate stick  (cites [2], you cited [1]; 1 of 4 words)
unmarked  how tall is the moon: no answer you sealed
scored 1 of 2 marked (50%); 1 unmarked
```

**The exam** is a file of your questions, one a line. A question is marked
when you sealed an answer for its words (the kernel's `sealed` and
`standing`: a seal whose proof holds, over a proposal file still the bytes
you sealed); the rest are said `unmarked`, and never asked.

**Each marked question** is ranked against your folder as a bite would be,
by the kernel's own `rank`, with no bite on the record, and the passages go
to the model once, in exactly the chat
[openai-compatible](../openai-compatible/) sends: numbered, under the rule
to answer only from them, at temperature 0 with a fixed seed.

**A reply passes** when it does both things your sealed answer did:

- it **cites** a passage your answer cites; and
- it **says it**: of whichever text has fewer content words, the reply or
  your answer, the other holds at least half (the kernel's `HOLD`, word
  forms counted as the kernel counts them, citations like `[1]` not
  counted). Counted against the shorter, so a long reply can't hide your
  short answer inside it, and can't pad past it either.

A sealed answer whose passages your folder no longer serves is said, and
left unmarked; a cite of a passage not served now is shown as such.

Exit codes, the kernel's: 0 every marked question passed; 42 one failed,
none could be marked, or the endpoint didn't answer; 2 refused (a bad
command line, not a box, a record that doesn't verify, a questions file
that can't be read).

**Uses:** the kernel's `read`, `sealed`, `standing`, `bite_key`, `config`,
`read_words`, `chunks`, `rank`, `echo`, `words`, `forms`, `holds` and
`HOLD`; [openai-compatible](../openai-compatible/)'s chat, its asking and
its reading of cites.

**Never:** writes the record or anything else, sends the model your sealed
answers or a passage the rank didn't serve, asks a question you sealed no
answer for, seals, or reads your key (the kernel checks your seals).
