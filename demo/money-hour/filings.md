# the filings desk

What the table asks of the 55 companies' latest 10-Ks: which talk about
which of Hollis's themes, and what each says about buying back its own
stock. Run on a box of the 10-Ks with every line folded.

    python adapters/stdlib/stack/stack.py --box DIR --stack demo/money-hour/filings.md

## by Hollis's themes
- sort -- --box {box} --categories demo/money-hour/themes.txt

## buybacks, as each company words them
- all -- --box {box} --top 20 "repurchased common stock during"

## where a filing quotes a figure the table repeated
- all -- --box {box} --top 10 "federal funds rate"
