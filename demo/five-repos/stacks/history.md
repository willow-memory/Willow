# the five repos in time, and in their own words

Two mirrors, written outside every repo: each repo's commits as dated
files (git-history) and its comments and docstrings as passages
(code-comments). A second box, hist-box, has the mirror folder as its
pile. Then: when each repo moved, what each first said when, and what the
code admits about itself, each repo answering in turn.

    rebuild.sh history.md

## the commits and the comments as piles
- git-history -- mirror --from <repos>/Willow --to <scratch>/mirror/commits/Willow
- git-history -- mirror --from <repos>/socratic-fork --to <scratch>/mirror/commits/socratic-fork
- git-history -- mirror --from <repos>/redential-cli --to <scratch>/mirror/commits/redential-cli
- git-history -- mirror --from <repos>/glapagos --to <scratch>/mirror/commits/glapagos
- git-history -- mirror --from <repos>/NaturalConvDataSet-fork --to <scratch>/mirror/commits/NaturalConvDataSet-fork
- code-comments -- mirror --from <repos>/Willow --to <scratch>/mirror/comments/Willow
- code-comments -- mirror --from <repos>/socratic-fork --to <scratch>/mirror/comments/socratic-fork
- code-comments -- mirror --from <repos>/redential-cli --to <scratch>/mirror/comments/redential-cli
- code-comments -- mirror --from <repos>/glapagos --to <scratch>/mirror/comments/glapagos
- code-comments -- mirror --from <repos>/NaturalConvDataSet-fork --to <scratch>/mirror/comments/NaturalConvDataSet-fork

## when each repo first said it
- first-mention -- --box <scratch>/hist-box "privacy"
- first-mention -- --box <scratch>/hist-box "secret"
- first-mention -- --box <scratch>/hist-box "constitution"
- first-mention -- --box <scratch>/hist-box "vault"
- first-mention -- --box <scratch>/hist-box "signature"
- first-mention -- --box <scratch>/hist-box "license"
- first-mention -- --box <scratch>/hist-box "Claude"
- first-mention -- --box <scratch>/hist-box "words list"
- first-mention -- --box <scratch>/hist-box "proof graph"
- first-mention -- --box <scratch>/hist-box "revert"
- on-this-day -- --box <scratch>/hist-box

## what the commits say, each repo in turn
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "the first commit"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "revert"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "security fix"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "privacy test"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "breaking change"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "rename"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "typo"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "release version"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "CI failed"
- fair-merge -- --from <scratch>/mirror/commits/Willow --from <scratch>/mirror/commits/socratic-fork --from <scratch>/mirror/commits/redential-cli --from <scratch>/mirror/commits/glapagos --from <scratch>/mirror/commits/NaturalConvDataSet-fork "reviewer asked"

## what the code admits about itself, each repo in turn
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "workaround"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "hack"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "deprecated"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "not implemented yet"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "we assume"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "false positive"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "edge case"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "slow"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "never"
- fair-merge -- --from <scratch>/mirror/comments/Willow --from <scratch>/mirror/comments/socratic-fork --from <scratch>/mirror/comments/redential-cli --from <scratch>/mirror/comments/glapagos --from <scratch>/mirror/comments/NaturalConvDataSet-fork "on purpose"

## who the histories name
- people -- --box <scratch>/hist-box
- said -- --box <scratch>/hist-box

## the histories as verse
- pile-poetry -- --box <scratch>/hist-box --seed "git log"
- pile-poetry -- --box <scratch>/hist-box --seed "code comments" --lines 4
