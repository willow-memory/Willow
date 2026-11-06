The suggestions contract (`adapters/stdlib/ci/README.md`): an add-on that
proposes a model's reply for your seal says in its claim who answered,
where, at what settings and what it did, in one form: `gemma at URL
(temperature 0, seed 0, reasoning low) answered from 1 of the 2 passages
served`. A card says `output: suggestions` (`readme` takes `report,
suggestions` too, and `stack` still finds a report among them);
openai-compatible's `claim()` writes it and `read_claim()` reads it, a claim
from before the settings were said too. openai-compatible, local-model,
translate, sort-ask and in-process keep it, saying the reasoning when asked
for and a `--system` voice and in-process's weights by SHA-256; before, two
suggestions asked at different reasoning read the same on the record.
sent-log reads every proposer's claim through it and says what each was
asked at, where it named only openai-compatible's; test_contract.py asks
each stdlib one of a stand-in model and holds its claim to the form
