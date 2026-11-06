<!-- willow-addon
section: Assistants
line: Your frozen questions asked again of a model now and then, flagging when its answers change while its name and card stay the same.
source: new
added: 2026-11-02
writes: nothing
network: the endpoint you configure, to ask your questions again
role: suggests
uses: openai-compatible
-->
# model-drift

Your questions asked of a model once and frozen, then asked again now and
then, flagging an answer that changed while the model's name and card
stayed the same: a model swapped or retuned behind the same name.

```
python adapters/stdlib/model-drift/model_drift.py freeze --box DIR --url URL \
    --model gemma-3-4b-it --questions questions.txt [--card gemma.md] \
    [--reasoning EFFORT] > frozen.json
python adapters/stdlib/model-drift/model_drift.py again --box DIR --url URL \
    --frozen frozen.json [--card gemma.md]

same       what goes in biscochitos
drifted    when does the gate stick
           then: It sticks in winter [1].
           now:  It sticks when it rains [1].
not held   how many cups of flour: your folder serves other passages now
1 of 2 held drifted, with the name gemma-3-4b-it and its card the same
```

**`freeze`** asks each question in the file (one a line) that your folder
serves passages for, once, in exactly the chat
[openai-compatible](../openai-compatible/) sends (the passages, numbered,
under the rule to answer only from them, at temperature 0 with a fixed
seed), and prints JSON: the model's name, the SHA-256 of its card when
`--card` names one (a [model-card](../model-card/) card, say), and for each
question the passages served and the answer, and the settings it asked at,
as [the suggestions contract](../ci/README.md#the-suggestions-contract) says
them: temperature, seed, and the reasoning when `--reasoning
none|low|medium|high` asked for one. It writes nothing, not even a
bite on the record: keep what it prints where you keep things.

**`again`** asks the frozen model the frozen questions now, and holds each
answer to the frozen one with its spaces closed up. A change is **drift**
only when nothing else moved:

- the passages served are the same ones, by id (otherwise `not held`: your
  folder changed under the question, and a new answer is no surprise);
- the model's name is the frozen one, since it is asked of that name;
- its card hashes the same, given to both runs or to neither. When the card
  differs, or one run names a card and the other doesn't, changes are
  counted but nothing is flagged: a new card says a new model;
- the settings are the frozen ones, since it asks at them: a reasoning level
  never reads as drift. A file frozen before settings were kept was asked at
  temperature 0 and seed 0 with no reasoning, and is asked so again; one
  frozen at settings this can't ask at is `nothing asked`, and flags nothing.

Run `again` when you like: after an update to the runtime, or on a schedule
of your own.

Exit codes, the kernel's: 0 frozen, or no held answer drifted (or the card
changed, so none is flagged); 42 one drifted, nothing could be asked or
held, frozen settings it can't ask at, or the endpoint didn't answer; 2 refused (a bad command line, not a
box, a record that doesn't verify, a file that can't be read or a frozen
file that isn't one).

**Uses:** the kernel's `read`, `config`, `read_words`, `chunks`, `rank` and
`echo`; [openai-compatible](../openai-compatible/)'s chat and its asking.

**Never:** writes the record or any file, sends a passage the rank didn't
serve, seals, or reads your key.
