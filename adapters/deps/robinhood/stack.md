# your Robinhood account, read back

Run on a box over the folder `robinhood.py snapshot --to` writes, after a
few snapshots on different days. It reads; it asks Robinhood nothing. The
timeline goes to robinhood-timeline.txt, where you run it.

    python adapters/stdlib/stack/stack.py --box DIR --stack adapters/deps/robinhood/stack.md

## what you held, day by day
- timeline -- --box {box} --to robinhood-timeline.txt "symbol quantity average_cost"

## when a holding first appears
- first-mention -- --box {box} "symbol"

## the portfolio's value, and how far it moved
- readings -- bite --box {box} "total_value"

## each day's portfolio value
- all -- --box {box} --top 40 "total_value"
