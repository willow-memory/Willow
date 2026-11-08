# the Fed desk

What the table asks of the FOMC's own words, 2023 to 2026, run on a box of
its statements and minutes with every line folded (the kernel reads 500
characters of a line, and minutes are long paragraphs).

    python adapters/stdlib/stack/stack.py --box DIR --stack demo/money-hour/fed.md

## when the minutes first said it
- first-mention -- --box {box} "tariffs"
- first-mention -- --box {box} "artificial intelligence"

## who voted against, and for what
- all -- --box {box} --top 12 "voting against preferred"

## every rate decision, ranked
- all -- --box {box} --top 40 "Committee decided target range federal funds rate"
