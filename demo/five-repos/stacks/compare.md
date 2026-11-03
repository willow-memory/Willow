# five repos compared, without an agent, with a words list

What the five share, what each could solve for another, and which of
Willow's 192 unbuilt ideas the other four already hold a piece of. Every
step is kernel search over the box or over an index of one repo; nothing
is generated, and nothing is written into any repo.

    rebuild.sh compare.md

## what each repo is, and what is near it on Willow's own list
- similar -- near "turn private git history into a metadata-only proof bundle of the skills detected locally, uploaded only on explicit confirmation"
- similar -- near "detect which libraries a repository uses from imports and config files against a versioned signature database"
- similar -- near "scan a payload for secrets before any output or upload"
- similar -- near "a graph of which function calls which in a codebase, anchored by file and line"
- similar -- near "a self-interrogation skill: a question bank per engineering domain and decision cards an agent reads before building"
- similar -- near "ask the person only the decisions that need human authority, and answer the rest from the repo"
- similar -- near "a grade for a plan: would an on-call engineer accept ownership of this at 3am"
- similar -- near "an AI governance dashboard with scores by domain and region and a trend"
- similar -- near "data governance standards: a manifest, provenance record, open licence and checksums for every dataset"
- similar -- near "download the grounding documents of a dialogue dataset from a list of urls"

## what the five share, each answering in turn
- fair-merge -- --box {box} "an append-only log whose entries are hash chained"
- fair-merge -- --box {box} "scan for secrets before anything is output"
- fair-merge -- --box {box} "the source code never leaves the machine"
- fair-merge -- --box {box} "a schema version bump when what leaves the machine changes"
- fair-merge -- --box {box} "licence Apache-2.0"
- fair-merge -- --box {box} "a constitution that the code is written to enforce"
- fair-merge -- --box {box} "the same bytes every run, deterministic"
- fair-merge -- --box {box} "tests that must pass before a merge, no exceptions"
- fair-merge -- --box {box} "a closed list of allowed names, anything else refused"
- fair-merge -- --box {box} "what an agent may never do"

## claims each repo makes, checked against all five
- claim-check -- --box {box} "source code never leaves the machine"
- claim-check -- --box {box} "an append-only hash chain detects a rewritten entry"
- claim-check -- --box {box} "secret scan of the payload before any output or upload"
- claim-check -- --box {box} "the agent asks only the decisions that need human authority"
- claim-check -- --box {box} "every dataset has a manifest, provenance, licence and checksums"
- claim-check -- --box {box} "approval needs a private key the code never reads"
- claim-check -- --box {box} "a closed vocabulary of slugs validated against a public list"

## the same text in two repos
- duplicates -- --box {box}

## each repo indexed once
- scan -- index --from <repos>/Willow --to <scratch>/index/willow
- scan -- index --from <repos>/redential-cli --to <scratch>/index/redential-cli
- scan -- index --from <repos>/socratic-fork --to <scratch>/index/socratic-fork
- scan -- index --from <repos>/glapagos --to <scratch>/index/glapagos
- scan -- index --from <repos>/NaturalConvDataSet-fork --to <scratch>/index/naturalconv

## Willow's 192 unbuilt ideas, asked of the other four
- scan -- scan --index <scratch>/index/redential-cli --index <scratch>/index/socratic-fork --index <scratch>/index/glapagos --index <scratch>/index/naturalconv --questions <scratch>/ideas.txt --top 2 --words <scratch>/five-words.txt

## what the other four say they need, asked of Willow
- scan -- scan --index <scratch>/index/willow --questions <scratch>/needs.txt --top 3 --todo --words <scratch>/five-words.txt
