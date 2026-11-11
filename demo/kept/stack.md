# remembered, not recomputed: this repository asked what it keeps
# <pile> is the repository as it was at one commit, cloned outside itself, so
# the stack reads what was there before it was and never its own write-up.
# <repo> is this checkout, for the one add-on that runs code from it.

## its words
# want 1: read what the code says of itself, not only the prose around it.
- code-comments -- mirror --from <pile> --to {box}-code
# want 2: read when each thing was decided, from the commits, dated by the commit.
- git-history -- mirror --from <pile> --to {box}-commits --messages

## found once, kept
# want 3: stop reading 20 MB again for every question: one index each of the
# prose, the code's comments and the commits, kept between runs, rebuilt
# only when a file's bytes changed. Needs steps 1 and 2: it indexes what they wrote.
- index-cache -- --from <pile> --to <scratch>/kept/index-repo
- index-cache -- --from {box}-code --to <scratch>/kept/index-code
- index-cache -- --from {box}-commits --to <scratch>/kept/index-commits
# want 4: ask every question of all three at once, with the kernel's own answers.
# Needs steps 3 to 5: their indexes.
- scan -- scan --index <scratch>/kept/index-repo --index <scratch>/kept/index-code --index <scratch>/kept/index-commits --questions <scratch>/questions.txt --words <scratch>/words.txt

## what was found, and what wasn't
# want 5: one line a question, so 48 answers can be read at a look. Needs step 6's answers.
- glance -- --of {06} --questions <scratch>/questions.txt --words <scratch>/words.txt
# want 6: for each question that found nothing, why: which words no file holds,
# so the words list is written from what was missed. Needs step 6's answers.
- why-not -- --box {box} --questions <scratch>/questions.txt --of {06}
# want 7: the prose is 42,000 passages and the commits 6,500, so one ranked
# list is mostly prose. Each of the three ranked on its own and dealt in turns.
# Needs steps 1 and 2's folders.
- fair-merge -- --from <pile> --from {box}-code --from {box}-commits --top 9 "a result kept so it is not computed again"
# want 8: when the repository first said it. Asked of the box, so the words list reads.
- first-mention -- --box {box} "cached"

## held to what the files say
# want 9: the claim from the conversation, checked part by part: does any one
# place here hold all of it, and which parts does nothing hold.
- claim-check -- --box {box} "a result named by the hash of its inputs is kept and shared so nobody computes it twice"
# want 10: the same for the promise the kept index rests on.
- claim-check -- --box {box} "the same folder gives the same bytes"
# want 11: every link and quoted line in the repository still there and still
# saying it, since a remembered thing that points nowhere is worse than none.
- xref -- --box {box}

## asked another way
# want 12: the passages themselves read once and kept in one file, so the
# next step (and any later add-on) doesn't read the folder again.
- pile-store -- --from <pile> --to <scratch>/kept/store.sqlite
# want 13: a question the strict word match half-answers, climbed rung by rung,
# saying which rung answered and why the others didn't. Needs step 14's store.
- pile-rungs -- --from <pile> --store <scratch>/kept/store.sqlite "computed once and kept"

## kept, and named
# want 14: every file's hash on the record, so a later run can say which
# files are as they were and which moved with no edit.
- fixity -- --box {box}
# want 15: the kernel's own file named as the archives name it: a name any
# machine computes from the bytes alone, with nothing sent.
- ids -- --box {box} kernel.py

## computed twice, to see that once would do
# want 16: a real computation to try the idea on: an N-body simulation, run by
# its fixed-step integrator, its results written as lines a box can hold.
- star-system -- --repo <repo>/adapters/deps/star-system/example_repo --to <scratch>/out/sim-a/star-system.md
# want 17: the same computation again, from nothing, into a second folder.
- star-system -- --repo <repo>/adapters/deps/star-system/example_repo --to <scratch>/out/sim-b/star-system.md
# want 18: where the two runs part, down to the line. If nowhere, the second
# run bought nothing the first hadn't. Needs steps 18 and 19's folders.
- diverge -- <scratch>/out/sim-a <scratch>/out/sim-b

## so someone else needn't take it on trust
# want 19: one hash that stands for the whole record, so a single row can be
# shown to someone who holds only that hash. After fixity, so its row is under it.
- merkle -- root --box {box}
# want 20: the record as W3C PROV, the form provenance tools already read:
# what came from what, by which step.
- prov -- --box {box} --to <scratch>/out/prov.json
# want 21: where the record ends, written outside the box, so rows cut off
# the end are caught where verify can't.
- tip-pin -- pin --box {box} --to <scratch>/out/away/pin.json
# want 22: the record in one zip, checked before it is kept. The time is
# pinned so the next step can name the file.
- backup -- --box {box} --to <scratch>/out/usb --now 2026-11-11T12:00:00Z
# want 23: that zip restored into scratch and verified there, so it is known
# to restore before the day it is needed. Needs step 24's zip.
- restore-drill -- --from <scratch>/out/usb/willow-backup-20261111-120000.zip
# want 24: how many verified copies there are, held to three copies, two
# kinds of storage, one away. Needs step 24's zip.
- three-two-one -- --box {box} --copy usb:<scratch>/out/usb/willow-backup-20261111-120000.zip

## where it stands
# want 25: one line on whether the box is all right: what it can't read,
# what waits, when its record was last checked.
- box-health -- --box {box}
# want 26: the record in plain sentences, to see what this whole run left on it.
- history -- --box {box}
