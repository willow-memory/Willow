# five repos in one box

One willow box whose pile is the folder holding all five repositories:
Willow, socratic-fork, redential-cli, glapagos and NaturalConvDataSet-fork.
Every step reads the box, or a repo folder by name, and writes nothing into
any of them. The stack reorders the pools tallest first; this is reading order.

    python adapters/stdlib/stack/stack.py --box BOX --stack five-repos.md

## what each repo tells an agent before its first change
- instruction-files -- --from <repos>/Willow
- instruction-files -- --from <repos>/redential-cli
- instruction-files -- --from <repos>/socratic-fork
- instruction-files -- --from <repos>/glapagos
- instruction-files -- --from <repos>/NaturalConvDataSet-fork
- agents-md-check -- --from <repos>/Willow
- agents-md-check -- --from <repos>/redential-cli
- codeowners -- --from <repos>/glapagos CONSTITUTION.md main.py src/glapagos/__init__.py

## what the code still owes
- todo -- --box {box}
- risky-code -- --box {box}
- pins -- --box {box}
- install-scripts -- --box {box}
- xref -- --box {box}
- format-rot -- --from <repos>

## what shouldn't be sitting in plain files
- secrets-audit -- --box {box}
- pii-audit -- --box {box}
- a11y-check -- --box {box}

## one question, each repo answering in turn
- fair-merge -- --box {box} "what never leaves the machine"
- fair-merge -- --box {box} "who may approve"
- fair-merge -- --box {box} "what is the key for"
- fair-merge -- --box {box} "what does the agent never do"
- why-not -- --box {box} "where is the vault"
- first-mention -- --box {box} "vault"

## what the folders agree and disagree on
- duplicates -- --box {box}
- contradictions -- --box {box}
- people -- --box {box}
- said -- --box {box}
- amounts -- --box {box}
- coming-up -- --box {box} --days 90

## what the box itself needs from you
- digest -- --box {box}
- box-health -- --box {box} --long
- history -- --box {box}
- export -- --box {box} --log

## names the rest of the world already uses
- ids -- --box {box} Willow/kernel.py
- ids -- --box {box} socratic-fork/SKILL.md
- ids -- --box {box} redential-cli/taxonomy.json

## play
- pile-poetry -- --box {box} --seed "five repos"
- pile-poetry -- --box {box} --seed "the vault is sean's key" --lines 4
