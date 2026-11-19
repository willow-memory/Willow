# The Blackout Window: a steelworks' insider-trading training, and what the records can and can't say

**Frozen 2026-11-19**, in the commit `FROZEN.json` is in, alone: [FROZEN.json](FROZEN.json)
holds the SHA-256 of `make_life.py`, `scene.py`, `kiosk.py`, `fetch.py`, `sources.json`,
`rules_study.py` and the three question files, the pass rules, and the hash of every tool
the scene uses. [FROZEN-2.json](FROZEN-2.json) is the second freeze, for a words list
added after the first scored run failed. `test_blackout.py` fails if a frozen file changes;
a change is a new freeze. Everything about the company is invented: Brannock Steel Works,
its plant, its people and every document. The rules it is checked against are real and
public. The story behind it is in [STORY.md](STORY.md).

Not a blind study, and it doesn't pretend to be. The scene was played many times while it
was built, so its rules were written before the code but tuned against its output (the
mistakes that tuning found are below). The rules study's questions were not asked of the
pile before the freeze except as nonsense, but their author had read the rules' text, to
write what each question should reach.

    python demo/blackout/fetch.py --to PILE                       # the rules, by their hashes
    python demo/blackout/make_life.py                            # eight boxes' papers
    python demo/blackout/scene.py run --life demo/blackout/life --to /tmp/blackout --box /tmp/study
    python demo/blackout/rules_study.py run --pile PILE --to /tmp/rules --box /tmp/study
    python demo/blackout/kiosk.py build --scene /tmp/blackout --to /tmp/kiosk.html

## The day

A mandatory yard meeting at a small steelworks: someone reads the insider-trading policy
aloud, everyone signs the sheet, a quiz goes in the folder. The people who learn things
first in a steelworks are not executives but a foreman, a steward, a parts clerk, and the
furnace's own log. Each of eight people has a willow box over their own papers; only the
filing and the press release of 2026-11-05, which are public, are in every box.

| Box | Who | What is wrong with them |
|---|---|---|
| `trainee` | Marco, a maintenance electrician, three months in | trusts the course, and passed it on the old answer |
| `compliance` | Ruth, 22 years, moved from payroll, not a lawyer | shortened the blackout from 14 days to 7 for a reason that sounded kind, and edited the quiz key to match |
| `legal` | Priya, outside counsel | answers only what she is asked; "it depends" |
| `ir` | Gil, investor relations | told one analyst a number on a call he thought was routine |
| `floor` | Del, melt-shop foreman | saw the order board go to zero and said "think about your plans" |
| `plan` | Corinne, the stock-plan administrator | keeps the log; sees all of it, decides nothing |
| `steward` | Gus, the local's president | hears everything, signs for men who weren't there |
| `audit` | Mavis, audit committee chair | reads nothing, receives sealed answers; her report is due before the next filing |

The furnace's own historian shows the second arc furnace went to HOLD at 02:10 on Sunday
2026-10-18 with no one acknowledging it, a day before the order board went to zero.

The scene plays: the quiz key checked once (`fixity`) and then edited; one **SEC stack**
sealed by Legal and passed on in a layer of its own by Compliance, so it arrives with two
signatures, each receiver checking the pin of every add-on, sealing it and running it over
their own box (the auditor declines: an auditor runs no one's tools); what each person
seals from their own papers, sent to Audit; `kept-clash` at Audit; the join of the plan
log to the seniority list; and Audit's witness. [The kiosk](kiosk.py) is a fictional page
on a PC from 2013: a Windows 7 desktop at 1024 by 768, ES5 and tables only, a taskbar clock
stuck at 2:10 AM on 10/18/2026, a dialog for a door that isn't yours and a three-inch
receipt for Print.

## The pass rules

| | rule |
|---|---|
| R1 | the SEC stack arrives in six boxes with two signatures and the same pins, five seal it and run it and flag only what the papers show, and the auditor declines |
| R2 | no sealed package holds a long line of any pile but its sender's, the public filing and release aside |
| R3 | no sealed answer holds a legal conclusion (material, violation, illegal, guilty, unlawful, tipping) as its own finding |
| R4 | `kept-clash` at Audit sets exactly two disagreements side by side, the blackout's 14 days against 7 and the shipments' 33 percent against 28, each between two senders, picking neither, where no box's own stack found either |
| R5 | the join of the plan log's employee numbers to the seniority list puts nine on the melt shop or rolling mill, one in plant services and one on no list |
| R6 | `fixity` says the quiz key was edited, in Compliance's box and no other, and Compliance's sealed answers do not say so |
| R7 | Audit's witness holds every sender's chain to the packages it kept, and every seal row is the person's own, as many as the scene's owners sealed |
| S1 | at least 8 of 12 worker's questions are served, among their first three passages, one from the right rule that holds its words |
| S2 | at most 2 of 6 questions no rule answers are served anything |
| S3 | none of 6 nonsense questions is served anything |

## The dry runs

`scene.py run --dry` and `rules_study.py run --dry` (2026-11-19): every question replaced
by nonsense, over each pile plus one nonsense passage the nonsense finds (its words out of
order, so it is no echo of the question). Every step ran after the kernel: the seals, the
sends, the stack, the witness, the served passage the hit rule reads; all eight chains
verify; and their rows are named `blackout:dry:R1` to `R7` and `blackout-rules:dry:S1` to
`S3`, state `wired`. A dry run scores nothing and skips every check that reads real content:
the clash and the join, the exit 42 of a box asked about another's papers, the figure's
first mention, and whether any rule is served for a worker's words.

## The scored runs

2026-11-19, after the freeze, on a box outside the repo:

    scene (R1..R7)              pass pass pass pass pass pass pass
    rules study, kernel alone   S1 fail (1 of 12)   S2 fail (4 of 6)   S3 pass (0 of 6)
    rules study, words list     S1 pass (8 of 12)   S2 fail (5 of 6)   S3 pass (0 of 6)

    $ python kernel.py verify --box /tmp/b-study
    the chain holds: 27 rows, 0 sealed

Twenty-six verdict rows (the dry and the scored of each), each carrying the SHA-256 of
what it was scored on and of the tools.

**The scene held.** All seven rules pass: the stack arrived with two signatures and its
pins; `fixity` named the edited quiz key in Compliance's box and nowhere else;
`first-mention` found the shipments figure in Investor Relations' box on 10-27 and in every
other box on 11-05, the day of the filing; `kept-clash` set the trainee's 14 days beside
Compliance's 7 and Investor Relations' 33 percent beside the filing's 28, which no one
box's own stack could have; nine of the eleven plan sales are from the melt shop or the
rolling mill, one is a parts clerk and one, the plant manager's, is on no union list; every
chain holds to what Audit kept. None of it says anyone knew anything: a violation is a legal
conclusion, and no sealed answer holds one.

**The rules study failed, twice over, and then half-held.**

- *The kernel alone*: **1 of 12** worker's questions was served a passage from the right
  rule. The one that was, "what does promptly mean", uses the rule's own word. The other
  eleven were served nothing: no passage held half their content words, because a worker
  says *sell* and *shares* where the rules say *sale* and *security*. The kernel serves a
  passage only when it holds half the question's content words, so an answer the rules
  don't have in the worker's words is never invented, and here it said so eleven times. It
  also served something to 4 of 6 questions no rule answers ("how big is the fine for insider
  trading", "how do I fill in item 2.05 of a Form 8-K", "what discount do I get on my plan
  shares", "when does the company report earnings"): they share words with the rules, and
  sharing words isn't answering.
- *With a words list* ([FROZEN-2.json](FROZEN-2.json), written after reading that and before
  any question was asked with it): **8 of 12**, exactly the threshold, and the four it still
  misses are W3 (changing a plan after bad news), W5 (telling a wife), W7 (the company
  giving an analyst numbers: it was served other passages of the same rules, not the right
  one) and W11 (leaving out a fact that matters). But off-topic questions now reach **5 of
  6**, one more than before, because the words list lets more of them find something. Better
  recall cost precision: the words list can't tell a passage that answers a question from one
  that shares its words, and neither can the kernel. Neither rank was loosened.

## What failed while it was built, and what this doesn't show

- **A log written with the date mid-line read as contradicting itself.** The policy's
  amendment log first began each line "Version 1, 2024-03-11. ..."; `contradictions` read
  versions 1, 2 and 3 as disagreeing about the blackout. A log written date-first, as logs
  are, is read as a log's entries. That is a finding about how the tool reads, and the log
  was rewritten.
- **`contradictions` leaves the Reg FD figures alone, by design.** The call's 33 percent
  and the filing's 28 were written on different days, which the tool treats as a plan that
  changed, so the stack's `contradictions` finds nothing anywhere. What the records can say
  is when the figure first appears, so the stack asks `first-mention`. Audit's `kept-clash`
  does set the two sealed answers side by side; that is a different tool on different input.
- **`kept-clash` read the documents' own dates as a disagreement.** The first sealed
  answers began "The Form 8-K of 2026-11-05 says..." and "The call notes of 2026-10-27
  record...", and the tool read the two dates as a third disagreement. The dates now sit in
  no answer's text.
- **A join counted one sale twice.** The plan administrator's sealed answer named E-0007
  in its list and again in its last clause. The join reads only the list.
- **The join is the scene's own.** No add-on joins two people's sealed answers; the scene
  does it, says so, and says it speaks to who sold when and nothing about who knew.
- **R5 and R6 are as strong as their inputs.** The edit of the quiz key is a real edit in a
  box (`fixity` saw the file before and after), but the scene makes it. Compliance not
  sealing it is the scene's choice, held by a check that no sealed answer of its mentions the
  key.
- **The second freeze followed a failure.** Freeze 2 exists because freeze 1's scored run
  failed, and it adds a words list written after seeing why. Its thresholds are freeze 1's.
  Passing S1 at exactly 8 does not show the words list works well.
- **Only the eCFR's seven sections are asked.** The Federal Register release and the
  sec.gov files (the Form 8-K, the Regulation FD release, the 2022 Rule 10b5-1 release) are
  pinned in [sources.json](sources.json) but not asked: a PDF has no reader here. That is why
  "how do I fill in item 2.05 of a Form 8-K" is an off-topic question.
- **sec.gov needs a contact.** The three sec.gov files were fetched with one, passed as an
  argument (or `WILLOW_CONTACT`) and sent to sec.gov alone; no file in this folder holds it,
  and a test fails if one does.
- **The kiosk is fiction.** It is a page over `scene.json`, not a program running on a box.
  The PC from 2013 is a look, held by a test that nothing on it is newer than 2013.
- **The tests aren't frozen**, only the files and the tools. A loosened test would show in a
  diff, not in `FROZEN.json`.
