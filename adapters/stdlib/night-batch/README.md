<!-- willow-addon
section: Assistants
line: Questions waiting for suggestions batched into one local-model run overnight, stopped the moment you're back.
source: new
added: 2026-11-02
version: 0.1.0
writes: record
network: loopback
role: suggests
uses: local-model
output: suggestions
-->
# night-batch

The questions you want suggestions for, asked of a model on this machine in
one run while you're away, and stopped the moment you're back, so the
machine is yours again.

```
python adapters/stdlib/night-batch/night_batch.py run --box DIR --questions waiting.txt \
    [--url URL ...] [--model NAME] [--reasoning EFFORT] [--until 2026-11-03T07:00:00Z]

asked    what goes in biscochitos
         Lard, not butter, and a spoonful of anise seed [1].
         pass  proposal:cdd2…  waiting on your seal
skipped  when does the gate stick: waiting on your seal already
stopped  you're back: row 9 (seal) isn't this run's
1 asked, 1 skipped, 1 not reached
```

**Each question** in the file (one a line) is asked as
[local-model](../local-model/) asks: the kernel bites, only the passages
served go to the first local server answering, and a reply citing them is
proposed through `kernel.py propose`, to wait for your seal in the morning,
its claim in [the suggestions contract](../ci/README.md#the-suggestions-contract)'s
one form. `--reasoning none|low|medium|high` goes to each ask as local-model
takes it; any other value is refused before the first.
A question already answered by a seal of yours, or with a suggestion
already waiting on your seal, is skipped; one you declined is asked again.

**You're back** when a row appears on the record that this run didn't
write: you bit, sealed or declined something. The run's own rows are its
bite of the question it asked and what was proposed under it; anything
else is yours, and it stops before the next question. A question being
asked runs to its end. If you bite while the model is working, the kernel
refuses the run's suggestion (it no longer answers the last bite), which
is the kernel keeping its promise, and you'll see that line. It also stops
before the next question once it is past `--until`, a time written as the
record writes them, in UTC.

**Built in stdlib**, like [local-model](../local-model/): the idea was
filed as needing a local model server, which is a program you run, reached
over HTTP, not a package this imports. To run it overnight, start it before
bed, or from your own scheduler.

Exit codes, the kernel's: 0 every question waiting was asked and got a
suggestion, or none was waiting; 42 it stopped before the end, no local
server ran, or a question got no suggestion; 2 refused (a bad command line,
not a box, a record that doesn't verify, a URL off this machine, a
questions file that can't be read, an `--until` that isn't a time).

**Uses:** the kernel's `read`, `sealed`, `declined`, `standing`,
`proposed_under` and `bite_key`; [local-model](../local-model/)'s ask.

**Never:** sends anything off this machine, asks after you're back, seals,
declines, or reads your key (the kernel checks your seals).
