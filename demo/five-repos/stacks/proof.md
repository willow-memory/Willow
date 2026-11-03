# prove the box to the outside world

A box over the five repos with six suggestions waiting on a person's seal.
What a stranger could verify without trusting us.

## the record hashed and pinned
- fixity -- --box {box}
- merkle -- root --box {box}
- merkle -- prove --box {box} --row 7 --to <scratch>/proof/row7.json
- tip-pin -- pin --box {box} --to <scratch>/proof/tip.txt
- tip-pin -- check --box {box} --pin <scratch>/proof/tip.txt

## a copy that checks itself
- backup -- --box {box} --to <scratch>/proof/backup

## in the envelopes the world reads
- ro-crate -- --box {box} --to <scratch>/proof/crate --licence Apache-2.0
- in-toto -- --box {box} --to <scratch>/proof/intoto.jsonl
- prov -- --box {box} --to <scratch>/proof/prov.json
- ids -- --box {box} Willow/CONSTITUTION.md

## what the record says of itself
- history -- --box {box}
- export -- --box {box} --log
- box-health -- --box {box} --long
