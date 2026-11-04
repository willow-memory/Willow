<!-- willow-addon
section: Assistants
line: A local model asked each of your box's questions three times, and how often its answer flips, since a model that answers the same way every time is one you can build on.
source: new
added: 2026-11-02
writes: nothing
network: loopback
role: suggests
uses: openai-compatible
-->
# same-way

A model on this machine asked each of your questions three times, the same
way each time, and how often its answer flips. A model that answers the
same way every time is one you can build on.

```
python adapters/stdlib/same-way/same_way.py --box DIR --url http://127.0.0.1:8080/v1 \
    --model gemma-3-4b-it --questions questions.txt [--times N]

same     3 of 3  what goes in biscochitos  (cites [1])
flipped  2 ways in 3  when does the gate stick  (cites [2] / [1, 2])
not asked  how tall is the moon: nothing in your folder holds that
2 asked, 1 the same every time, 1 flipped (50%)
```

**Your questions** are a file, one a line; the record keeps a bite's key,
never its words, so it can't give them back. Each is ranked against your
folder as a bite would be, by the kernel's own `rank`, but no bite goes on
the record: this writes nothing.

**Each question with passages under it** is sent N times (three unless
`--times` says, two at least) with exactly the chat
[openai-compatible](../openai-compatible/) sends: the passages, numbered,
under the rule to answer only from them, at temperature 0 with a fixed
seed. A server that honours those says the same thing every time; one that
batches, or ignores the seed, flips. Answers are compared with their spaces
closed up, and a change in which passages an answer cites is a flip even
when its words hold.

**Only this machine.** The URL must be 127.0.0.1 (or any loopback
address), `::1` or `localhost`: the idea is a local model, and your
passages go nowhere else. The idea said `this-machine`; the card promises
`loopback`, which is that, and what the guard holds it to.

Exit codes, the kernel's: 0 every question asked was answered the same way
every time; 42 one flipped, none could be asked, or the endpoint didn't
answer; 2 refused (a bad command line, not a box, a record that doesn't
verify, a URL off this machine, a questions file that can't be read).

**Uses:** the kernel's `read`, `config`, `read_words`, `chunks`, `rank` and
`echo`; [openai-compatible](../openai-compatible/)'s chat, its asking and
its reading of cites.

**Never:** writes the record or anything else, sends a passage the rank
didn't serve, asks a model off this machine, seals, or reads your key.
