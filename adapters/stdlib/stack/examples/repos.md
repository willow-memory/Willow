# a folder of repositories

Several repositories cloned side by side under one folder, yours or ones
you watch, with the box's pile set to that folder. Run it before a review,
or when one of them moves. The audits read every repo at once; the
questions go through fair-merge, which ranks each repo on its own and
deals the answers out in turns, so a large repo can't bury a small one.

    python adapters/stdlib/stack/stack.py --box DIR --stack adapters/stdlib/stack/examples/repos.md

## what the code still owes
- todo -- --box {box}
- risky-code -- --box {box}
- xref -- --box {box}
- pins -- --box {box}
- install-scripts -- --box {box}

## what shouldn't be sitting in plain files
- secrets-audit -- --box {box}
- pii-audit -- --box {box}
- a11y-check -- --box {box}

## one question, each repo answering in turn
- fair-merge -- --box {box} "what never leaves the machine"
- fair-merge -- --box {box} "who may approve"
- fair-merge -- --box {box} "what does the agent never do"

## what the repos say twice, and who they name
- duplicates -- --box {box}
- people -- --box {box}
