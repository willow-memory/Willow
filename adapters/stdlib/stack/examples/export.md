# a box handed to someone else

What leaves with a box when its person hands it on: to a colleague, an
archive, a future machine. Every line is a check they can run or a file
they can read without trusting the one who made it. Make the folder first
(`mkdir DIR-export`); a step that writes refuses to make it.

    python adapters/stdlib/stack/stack.py --box DIR --stack adapters/stdlib/stack/examples/export.md

## what the record says of itself
- history -- --box {box}
- export -- --box {box}
- export -- --box {box} --log
- box-health -- --box {box} --long

## the hashes a stranger can check
- merkle -- root --box {box}
- tip-pin -- pin --box {box} --to {box}-export/tip.txt
- fixity -- --box {box}

## in the envelopes the world reads
- prov -- --box {box} --to {box}-export/prov.json
- in-toto -- --box {box} --to {box}-export/in-toto.jsonl
- ro-crate -- --box {box} --to {box}-export --licence CC-BY-4.0

## a copy that checks itself
- backup -- --box {box} --to {box}-export
