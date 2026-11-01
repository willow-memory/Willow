<!-- willow-addon
section: Keeping track
line: Write a prediction before the outcome, settle it later with your seal, see your Brier score.
source: bot
added: 2026-11-01
writes: record
network: none
tags: no-install, offline, records, tracking
-->
# forecasts

A prediction written down before the outcome, settled by your seal, and
scored.

    python adapters/stdlib/forecasts/forecasts.py wager  --box DIR --p 0.8 "the bees swarm before June"
    python adapters/stdlib/forecasts/forecasts.py settle --box DIR 1 yes
    python adapters/stdlib/forecasts/forecasts.py score  --box DIR

    2 settled, 1 open of 3 wagers
    Brier 0.065  log score 0.290  over 2 settled
      said 0.7-0.8: right 100% of 1
      said 0.8-0.9: right 100% of 1

**`wager`** writes a `wager` row: how likely you think the claim is (`--p`,
from 0.01 to 0.99) and the claim's SHA-256. The record keeps no words, so
keep the claim yourself; its hash says later that it was this claim and no
other, and its place on the chain that it came before the outcome.

**`settle`** proposes what happened through the kernel's own door, like any
suggestion, and writes a `settle` row naming the wager and the proposal. It
waits for your seal, made with `kernel.py seal` and your key. Code never
settles a wager: an outcome counts only once you've sealed it, and not
sealing it is the No.

**`score`** reads the record back. Each wager is `open`, `waiting` on your
seal, `settled`, `conflicting` (you sealed both outcomes), or `broken` (a
sealed outcome whose file is no longer the bytes you sealed). Over the
settled ones: the Brier score (0 is prophecy, 0.25 is a coin at 50%, 1 is
confidently wrong), the log score, which punishes confident mistakes harder,
and for each band of confidence how often you were right. A wager you
thought unlikely is counted in its band as the opposite claim: 0.3 that it
rains is 0.7 that it doesn't. It writes nothing.

Exit codes, the kernel's: `wager` 0; `settle` 42, waiting on your seal;
`score` 0, or 42 when an outcome waits on your seal or nothing is settled
yet; 2 refused (a broken outcome, a record that doesn't verify, a row that
isn't a wager, one already settled, a bad command line).

**Uses:** the kernel's `read`, `append`, `bite`, `propose`, `sealed`,
`standing`, `subject_of` and its exit codes.

**Never:** reads your key, seals, or writes anything but the record's rows
and the proposal, through the kernel. Never keeps the claim's words.

**Where it comes from:** [willow-bot's one script](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/calibration.py),
whose checkout scores wagers against outcomes a person sealed. The Brier,
log score, bands and fold are its calibration module, unchanged, itself
vendored from the Forge. Its wagers carry a distribution over several paths
and a sealed tip; here a wager is one claim and one p.
