# What the stacks change

changes.py, written after the first report: the same run's baseline, fired against an empty pile, bridges held, kinds, pools.

## Fired, against an empty pile

| pile | printed | fired | differs from empty |
|---|---|---|---|
| willow | 303 | 161 | 142 print the same on nothing |
| willows-grove | 296 | 113 | 183 print the same on nothing |

## Bridges held

- Bridges: the taker changed in 3 of 402; no-bridge pairs: the second changed in 0 of 1946; one-sided Fisher p 0.004987595530429021.
  - held on willow: `openai-compatible` then `sent-log`
  - held on willow: `dice` then `game-master`
  - held on willows-grove: `dice` then `game-master`

## Kinds: which writer moves which reader

- 222 of 1966 kind stacks moved their reader.
  - `catgrid` (catgrid) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `changed` (changed) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `dice` (roll) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `game-master` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `dice5e` (roll5e) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `fixity` (fixity) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `forecasts` (wager) moved: `box-health` (2 piles), `cloudevents` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `hook-replay` (hook-replay) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `life` (life) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `llm-cli` (bite) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `sent-log` (1 piles), `serve` (1 piles), `three-two-one` (2 piles)
  - `nightstand` (nightstand) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `predict` (bite, graded, predict) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `prov` (2 piles), `sent-log` (1 piles), `serve` (1 piles), `three-two-one` (2 piles)
  - `quiz` (quiz) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `session-seal` (bite, proposal, session) moved: `assistant-scores` (2 piles), `box-health` (2 piles), `cloudevents` (2 piles), `digest` (2 piles), `forecasts` (2 piles), `hook-compact` (2 piles), `hook-start` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `sent-log` (2 piles), `serve` (2 piles), `three-two-one` (2 piles)
  - `surprise` (surprise) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)
  - `tarot` (draw) moved: `box-health` (2 piles), `cloudevents` (2 piles), `forecasts` (2 piles), `nightstand` (2 piles), `predict` (2 piles), `prov` (2 piles), `three-two-one` (2 piles)

## Readers, grouped by the writers that move them

- moved by dice: `game-master`
- moved by llm-cli, predict, session-seal: `sent-log`, `serve`
- moved by session-seal: `assistant-scores`, `digest`, `hook-compact`, `hook-start`
- moved by the whole record: `box-health`, `cloudevents`, `forecasts`, `nightstand`, `predict`, `prov`, `three-two-one`

## Pools: steps joined by a change one made in the other

- 27: `assistant-scores`, `box-health`, `catgrid`, `changed`, `cloudevents`, `dice`, `dice5e`, `digest`, `fixity`, `forecasts`, `game-master`, `hook-compact`, `hook-replay`, `hook-start`, `life`, `llm-cli`, `nightstand`, `openai-compatible`, `predict`, `prov`, `quiz`, `sent-log`, `serve`, `session-seal`, `surprise`, `tarot`, `three-two-one`
