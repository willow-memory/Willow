<!-- willow-addon
section: Keeping track
line: Market calls kept as wagers on the record ('SPY closes up on Friday'), settled later by your seal, with the losers kept.
source: bot
added: 2026-11-01
writes: record
network: none
-->
# market-calls

A signal app shows its winners and drops its losers; nobody can check what it
called before the market moved. Here a market call is a [forecasts](../forecasts/)
wager, so its record can't be edited and its losers can't be dropped.

    python adapters/stdlib/market-calls/market_calls.py call  --box DIR --p 0.7 SPY up 2026-11-06
    python adapters/stdlib/market-calls/market_calls.py call  --box DIR --p 0.4 SPY above:600 2026-11-06
    python adapters/stdlib/market-calls/market_calls.py close --box DIR SPY 2026-11-06 589.50 585.10
    python adapters/stdlib/market-calls/market_calls.py score --box DIR

    right       row 1  SPY up 2026-11-06  p 0.7
    wrong       row 2  SPY above:600 2026-11-06  p 0.8
    even        row 3  QQQ up 2026-11-06  p 0.5
    open        row 4  DIA up 2026-11-06  p 0.6
    1 of 3 settled calls right, Brier 0.327

**`call`** writes forecasts' own `wager` row, naming the market: `up` is P
that the symbol closes above the close before it on that day, `above:PRICE`
P that it closes above PRICE. One call per question: a second on the same
symbol, kind, threshold and day is refused, so no one holds both sides. A
call is made before 13:00 UTC on its close date (before the New York open,
summer and winter) and before that day's close is on the record. The time is
the record's own, as honest as the clock `--now` gives it: keep a
[tip-pin](../tip-pin/) from before the open if the timing must be shown.

**`close`** writes the day's closes, as you read them, in a `close` row, and
proposes each open call's outcome on that symbol and day through forecasts'
`settle`: the kernel's own door, waiting on your seal. Code never settles a
call. Prices are decimals, compared exactly; a second close for the same day
must say the same prices.

**`score`** lists every call, settled, waiting or open, losers kept: `right`
when a call over even odds happened or one under didn't, `wrong` otherwise,
`even` at 0.5. Then the Brier score over the settled ones. It writes nothing.
forecasts' `score` counts these calls among all your wagers.

Paper only: nothing here trades, fetches a price, or has an edge. What it
gives is a record that says, without being able to lie, whether a way of
calling the market has any.

Exit codes, the kernel's: `call` 0; `close` 42 when an outcome waits on your
seal, 0 when no call was open; `score` 0, or 42 when a call waits on your seal
or nothing is settled yet; 2 refused (a late or second call, two closes for
one day, a broken outcome, a record that doesn't verify, a bad command line).

**Uses:** the kernel's `read` and `append`, and forecasts' `settle`,
`outcomes` and `brier`.

**Never:** reads your key, seals, or reaches the network.

**Where it comes from:** [willow-bot's one script](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/market.py),
whose market calls wait on drand's clock and read closes from stooq.com.
Here, offline, the closes are yours to type and the time is the record's.
