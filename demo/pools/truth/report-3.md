# What the stacks change

changes.py, written after the first report: the same run's baseline, fired against an empty pile, bridges held, kinds, pools.

## Fired, against an empty pile

| pile | printed | fired | differs from empty |
|---|---|---|---|
| climate-almanac | 295 | 84 | 211 print the same on nothing |
| forge | 296 | 120 | 176 print the same on nothing |
| homestead-law | 295 | 81 | 214 print the same on nothing |
| jeles | 295 | 83 | 212 print the same on nothing |
| known-gaps | 289 | 89 | 200 print the same on nothing |
| nestor | 294 | 130 | 164 print the same on nothing |
| willow | 303 | 161 | 142 print the same on nothing |
| willows-grove | 296 | 113 | 183 print the same on nothing |

## Bridges held

- Bridges: the taker changed in 12 of 1608; no-bridge pairs: the second changed in 0 of 7796; one-sided Fisher p 6.037569857547805e-10.
  - held on climate-almanac: `dice` then `game-master`
  - held on forge: `openai-compatible` then `sent-log`
  - held on forge: `dice` then `game-master`
  - held on homestead-law: `dice` then `game-master`
  - held on jeles: `dice` then `game-master`
  - held on known-gaps: `openai-compatible` then `sent-log`
  - held on known-gaps: `dice` then `game-master`
  - held on nestor: `openai-compatible` then `sent-log`
  - held on nestor: `dice` then `game-master`
  - held on willow: `openai-compatible` then `sent-log`
  - held on willow: `dice` then `game-master`
  - held on willows-grove: `dice` then `game-master`

## Kinds: which writer moves which reader

- 882 of 7864 kind stacks moved their reader.
  - `catgrid` (catgrid) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `changed` (changed) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `dice` (roll) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `game-master` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `dice5e` (roll5e) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `fixity` (fixity) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `forecasts` (wager) moved: `box-health` (8 piles), `cloudevents` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `hook-replay` (hook-replay) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `life` (life) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `llm-cli` (bite) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `sent-log` (1 piles), `serve` (1 piles), `three-two-one` (8 piles)
  - `nightstand` (nightstand) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `predict` (bite, graded, predict) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `prov` (8 piles), `sent-log` (4 piles), `serve` (4 piles), `three-two-one` (8 piles)
  - `quiz` (quiz) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `session-seal` (bite, proposal, session) moved: `assistant-scores` (8 piles), `box-health` (8 piles), `cloudevents` (8 piles), `digest` (8 piles), `forecasts` (8 piles), `hook-compact` (8 piles), `hook-start` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `sent-log` (8 piles), `serve` (8 piles), `three-two-one` (8 piles)
  - `surprise` (surprise) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)
  - `tarot` (draw) moved: `box-health` (8 piles), `cloudevents` (8 piles), `forecasts` (8 piles), `nightstand` (8 piles), `predict` (8 piles), `prov` (8 piles), `three-two-one` (8 piles)

## Readers, grouped by the writers that move them

- moved by dice: `game-master`
- moved by llm-cli, predict, session-seal: `sent-log`, `serve`
- moved by session-seal: `assistant-scores`, `digest`, `hook-compact`, `hook-start`
- moved by the whole record: `box-health`, `cloudevents`, `forecasts`, `nightstand`, `predict`, `prov`, `three-two-one`

## Pools: steps joined by a change one made in the other

- 27: `assistant-scores`, `box-health`, `catgrid`, `changed`, `cloudevents`, `dice`, `dice5e`, `digest`, `fixity`, `forecasts`, `game-master`, `hook-compact`, `hook-replay`, `hook-start`, `life`, `llm-cli`, `nightstand`, `openai-compatible`, `predict`, `prov`, `quiz`, `sent-log`, `serve`, `session-seal`, `surprise`, `tarot`, `three-two-one`
