<!-- willow-addon
section: Assistants
line: How often each assistant's suggestions were sealed or set aside, from the record.
source: new
added: 2026-11-06
writes: nothing
network: none
role: suggests
uses: openai-compatible
output: report
-->
# assistant-scores

How often each assistant's suggestions were sealed or set aside, from the record.

    python adapters/stdlib/assistant-scores/assistant_scores.py --box DIR [--json]

Every suggestion an assistant made is on your record, and so is what you did
with it. This counts them: for each assistant, how many you sealed, how many
you declined, and how many still wait.

    assistant-scores: populated, 9 suggestions from 2 assistants, 6 decided by you
    ## assistants
      qwen3:8b at http://127.0.0.1:11434/v1 (temperature 0, seed 0, reasoning low)  4 sealed, 1 declined, 1 waiting; 4 of the 5 decided sealed
      qwen3:8b at http://127.0.0.1:11434/v1 (temperature 0, seed 0)                  1 sealed, 0 declined, 2 waiting; 1 of the 1 decided sealed

**An assistant is who, where and its settings together**, read from each
suggestion's claim in [the suggestions contract](../ci/README.md#the-suggestions-contract)'s
one form, by [openai-compatible](../openai-compatible/)'s `read_claim`. So one
model asked at two reasoning levels is two rows, and you can see which you
seal more often. A claim from before the contract said its settings is
counted with `(settings not said)`.

**Each suggestion counts once**, however many times it was proposed, and only
when its proposal file is still the bytes its subject names; one that isn't
is listed under `not read`. A suggestion whose claim names no assistant (one
you wrote yourself, or another tool's) is counted under `no assistant named`,
never guessed at.

**A seal or a No counts only while its proof holds under your key**: the
kernel's `sealed` and `declined` check it, so the key is read there and
nowhere here.

**It judges no model.** A claim is the proposer's own words, not an attested
card, and a model you seal more often may only have been asked easier
questions. [model-exam](../model-exam/) scores a model against the answers
you sealed, on the same questions.

It prints a report ([the report contract](../ci/README.md#the-report-contract)),
the same as JSON with `--json`.

**Exit codes:** 0 a report, populated or empty; 2 refused (a bad command
line, not a box, a record that doesn't verify).

**Never:** writes anything, reads your key, or goes online.
