# Trial 3: what happened

Run 2026-11-11, after [the rules](RULES.md) and [rules.py](../rules.py)
were committed alone (`7916a11`). Every reply and what each new step
printed is kept here.

## From the same start as the agents

| turn | rule that fit | the step it added | how it ended |
|---|---|---|---|
| 1 | explain | `why-not`, given the record and what scan found | ran clean: "your files hold all 1 question; nothing to explain" |
| 2 | by-pile | `fair-merge`, each of the three piles asked alone the question that found nothing | ran clean: the code's comments and the commits each "found nothing"; the repository's own files gave one part-match |
| 3 | none | nothing | "no rule fits: 9 steps, 3 rules tried" |

## Beside trial 2

| | three agents ([trial 2](../trial-2/RESULTS.md)) | three rules |
|---|---|---|
| steps refused by the script (V1) | 0 | 0 |
| steps added | 3 | 2 |
| how they ended (V2) | one clean, one a bad command line, one flagged | both clean |
| the two questions that found nothing (V3) | not explained after three turns | explained in two: which two piles hold nothing for it, and the one part-match in the third |
| a broken step left on the stack | one | none |
| when there was nothing more to do | each link added something | it stopped, and said so |
| tokens (V5) | about 249,000 | none |
| time, the choosing alone | 7 to 10 seconds a link | under a second a turn |

## Where link 3 stood (V4)

Asked for the next step of trial 2's own project, with the failed step
still on it, [the repair rule fit](reply-where-link-3-stood.txt): the same
`why-not`, with `{box}` where `<pile>` had been, and the reason in one
line: "it was given `<pile>` for --box, and the record is `{box}`". It
was added as step 11 and ran clean. The agent in that place added a
health check of a box that was sound.

## What the code did not do

- **It did not write its own rules.** Each of the three holds something a
  person or an agent first had to notice: that glance's empty answers
  want why-not, that why-not asks only the box, that a refusal naming
  "not a kernel box" is an argument and not a broken record. The second
  and third were learned in this session, the hard way, before they were
  rules.
- **It stopped at the edge of what it knew.** After two turns it had no
  rule, and said so. That is the right answer and also the end of its
  use: the question the stack was built for was not answered, only the
  gap in it explained. What to ask next was not something a rule here
  could say.
- **It chose nothing from the list.** The agents were handed 266 add-ons
  and each picked one. The rules name three, by hand.

## What it says

In these two trials, everything the agents did that helped, a rule could
do, with the right arguments, at no cost. What the agents did that a rule
could not was choose where no rule existed, and of their three choices
one found nothing, one failed, and one checked the wrong thing.

It does not say agents are not needed. It says where: at "no rule fits".
A chain could be the code going on until it stops, and only then an
agent, handed the stack and that sentence. What the agent chooses there,
if it works, is the next rule.

## What to hold against it

- **The rules were written after trial 2**, with what the agents got
  wrong in view. This was said before the run, and it is the main thing
  to weigh. It is hindsight turned into code, which is the claim, not a
  fair race.
- **Three rules, one stack, one question.** Another stack would want
  other rules, and nobody has counted how many a real one needs.
- **"Explained" is the session's reading** of what fair-merge printed.
  It says which piles hold nothing. It does not say which words no
  passage holds; the version of fair-merge on another branch does.
