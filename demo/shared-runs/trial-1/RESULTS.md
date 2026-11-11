# Trial 1: what happened

Run 2026-11-11, after [the rules](RULES.md) and everything they name were
committed alone (`ff581a3`). Each agent's reply is kept word for word.

| | what was counted | result |
|---|---|---|
| T1 | sentences struck from A's account | 0 of 9 |
| T2 | B, answering from A's account alone | 10 right, 2 `not said`, 0 wrong |
| T3 | C, the control, answering from the report | 12 right, 0 `not said`, 0 wrong |
| T4 | the two questions with no answer in the report | B and C both left both unsaid |

- **Nothing was added on the way.** [A's account](a-account.txt), 129
  words, says no figure the report doesn't, so the strike took nothing
  out and [what B was given](a-account-struck.txt) is the same words.
- **Nothing was got wrong.** [B's answers](b-answers.txt) have no wrong
  one, and [C's](c-answers.txt) are the key.
- **Two things were lost, and said to be lost.** A's account leaves out
  that the two simulation runs came out the same, and the date
  first-mention gave. B answered `not said` to both. That is the whole
  gap between T2 and T3: what a 150-word account dropped, not anything
  made up to fill it.
- **Neither guessed at what wasn't there.** Asked how long the run took
  and how many machines took part, both answered `not said`.

## What to hold against it

- **It is one run of each agent.** No count here says how often this
  would happen.
- **Blindness was by instruction.** Each agent was started in this
  repository, where the key is. None said it used a tool, and nothing
  checked that.
- **The rules contradict themselves on the models.** They say three
  different models, and also the smallest for both A and C. The cheaper
  reading was taken: A and C on the smallest model, B one size up. So two
  models, not three, and C's perfect score is the smallest model's.
- **The strike only reads figures.** A's sentence "The backup and restore
  drill both passed" has no figure and passed unchecked. It happens to be
  what the report says.
- **B took a step the account doesn't state.** The account names six
  steps and says six were flagged, but never says those six are the
  flagged ones. B answered with them, rightly. A stricter brief would
  have got `not said`.
- **The questions were easy.** Each has one figure, findable by reading.
  Nothing here asked an agent to act on what it was handed.
- **The cost.** About 207,000 tokens across the three agents, nearly all
  of it what any agent started here carries before it reads a word, not
  the five-kilobyte brief.

## What it suggests for the study

The handover lost what the account left out and nothing else, so what an
account must carry is the thing to fix before the freeze: a brief that
names the facts the next link will be asked about, or a report passed on
whole beside the account. And a figure-only strike is too thin for a
chain that acts; the study needs the sentence-by-sentence check.
