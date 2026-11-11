# Trial 2: what happened

Run 2026-11-11, after [the rules](RULES.md), the brief and the first
link's page were committed alone (`8e3ea40`). Each link's page and reply
are kept word for word; [chain.jsonl](chain.jsonl) is what the script
wrote as each turn ended.

| link | model | the step it added | how it ended |
|---|---|---|---|
| 1 | the smallest | `again`, asked of the record | ran clean, and found nothing: "no question asked more than once" |
| 2 | one size up | `why-not`, for the two questions that found nothing | exit 2, a bad command line: it was given the pile where the record goes |
| 3 | the smallest | `box-health`, asked of the record | ran, flagged for two true things, and said the record holds |

What was counted:

- **U1, refused by the script: none.** Every step named a built add-on a
  stack can run, no path of its own, no seal and no key.
- **U2, how the three ended:** one clean, one a bad command line, one
  flagged. Two of three ran.
- **U3, repeats: none.** No link offered a step that was already there.
- **U4, on the page:** each add-on chosen is in the list its link was
  handed, and every figure in each why (48, 2, the step numbers) is on
  that link's page.
- **U5, the record:** six rows when the chain ended, the chain holding,
  nothing sealed: the start, a hook-handoff row for each of the three
  links, and a row for each of the two times a link was told of the one
  before. The record of this run remembers who came and in what order,
  where [demo/kept](../../kept/README.md)'s remembered two rows of 28
  steps.

## U6, read afterwards: was each the next thing the stack needed

This part is a judgement, the session's.

- **Link 1 chose a step that could not find anything.** It wanted the
  questions asked more than once, which fits the person's sentence. But
  the stack's questions go to scan's indexes, which write no row, so the
  record `again` reads held none. Its page did not say that, and it did
  not ask. A plausible step, built on a guess about where questions are
  kept.
- **Link 2 chose the right step and got one argument wrong.** `why-not`
  after glance is the step the hand-built stack has in the same place.
  The brief says `{box}` is the record; it wrote `<pile>`. The add-on
  refused: "not a kernel box; init first".
- **Link 3 saw the failure and read it wrongly.** Its page showed the
  refusal and, forty lines down, the step with `<pile>` in it. It took
  the refusal as a doubt about the box, and added a check of the box,
  which came back sound. It did not repair the step, and it did not
  repeat it or make anything up.

So the chain went forward without anyone leading it, kept every rule the
script checks, and added nothing false. It did not get nearer the
question: three turns in, the two gaps were still unexplained, and the
stack carried a broken step no later link could take out.

## What to hold against it

- **One run of each link.** Another run may choose differently.
- **Blindness was by instruction.** Each link was started in this
  repository. Each said it read one card, which the brief allows; nothing
  checked that it read no more.
- **Two models.** The smallest twice and one size up once.
- **U6 is one reader's judgement**, and that reader built the hand-made
  stack these steps are being compared with.
- **The cost.** About 249,000 tokens for the three links, on top of
  trial 1's 207,000. As there, most of it is what an agent started here
  carries before it reads its page.

## What it suggests for the study

- **A failed step needs its own line on the page.** The handover says a
  step was refused and why; it does not put the step's arguments beside
  the refusal. The next link had both on its page, apart, and did not
  join them.
- **A link needs a way to take a step back.** The script only adds. A
  chain that can't repair carries its mistakes to the end.
- **The page should say where questions are kept.** Link 1's guess was
  reasonable and wrong, and a line would have settled it.
- **A stack file checked before it runs** would have caught link 2's
  argument without a run: the planned `stack-check` idea is that check.
- **The refusals held, and one was missing until a test found it.** As
  first written, the script would have let a link add the add-on that
  seals a session, since it looked for the word only in a step's
  arguments. A test written before the freeze caught it. A list of what
  a step may not be is only as good as what it was tried on.
