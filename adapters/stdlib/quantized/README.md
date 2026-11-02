<!-- willow-addon
section: Assistants
line: Finds the smallest quantized local model that still gets your box's own questions right, so suggestions come faster.
source: new
added: 2026-11-02
writes: nothing
network: loopback
uses: local-model, model-exam
-->
# quantized

The smallest model on your local server that still gets your own questions
right, so suggestions come faster from a model no bigger than it needs to
be.

```
python adapters/stdlib/quantized/quantized.py --box DIR --questions exam.txt \
    [--url URL ...] [--model NAME ...]

gemma3:1b   815319791 bytes  Q4_K_M  passed 1 of 2
gemma3:4b   3338801804 bytes  Q4_K_M  passed 2 of 2
gemma3:12b  8149190253 bytes  Q4_K_M  passed 2 of 2
smallest passing all 2: gemma3:4b, 3338801804 bytes
```

**The exam** is [model-exam](../model-exam/)'s: each question in the file
that you sealed an answer for, and that your folder still serves passages
for, is asked of each model with those passages, in openai-compatible's
chat. A reply passes when it cites a passage your answer cites and holds
half the content words of the shorter of the two. Nothing is written, not
even a bite.

**The models** are those the first local server answering offers (found as
[local-model](../local-model/) finds one), or those `--model` names.
**Their sizes** come from the server: Ollama's own list gives each model's
size and quantization, and they are sorted by it; a server that gives none
leaves a model `size not said`, listed after those with one and named only
when none with a size passes. Every model sits the whole exam, so the list
also shows how far each smaller one falls short.

**Built in stdlib**, like [local-model](../local-model/): the idea was
filed as needing a local model server, which is a program you run, reached
over HTTP, not a package this imports.

Exit codes, the kernel's: 0 a model passed every marked question; 42 none
did, no question could be marked, no local server ran, or one stopped
answering; 2 refused (a bad command line, not a box, a record that doesn't
verify, a URL off this machine, a questions file that can't be read, a
server offering no model when none is named).

**Uses:** the kernel's `read`, `bite_key` and `HOLD`;
[model-exam](../model-exam/)'s sealed answers, ranking and marking;
[local-model](../local-model/)'s finding of a server.

**Never:** writes the record or anything else, sends anything off this
machine, downloads or deletes a model, seals, or reads your key (the kernel
checks your seals).
