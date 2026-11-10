# A stack, for agents

Putting add-ons together for someone, and sharing what they settle. Part of
[AGENTS.md](../../AGENTS.md); the rule is CONTRIBUTING.md's "A chain of
add-ons starts at the Forge".

A stack is a runbook for a pile: the add-ons a person runs, in order, and
why each is there. The forge add-on builds it from their words and keeps
their reasons on their record; you propose, they seal.

1. **Ask with their words.**
   `python adapters/deps/forge/suggest.py suggest --box DIR "their sentence"`
   names the add-ons the words reach, and a fork for each word that reaches
   several. Don't pick between them for the person.
2. **When a word misses**, the add-on they meant isn't reached because no
   line of `ui/search-words.txt` points their word at its card. Add the
   line (their word, then the card's words), and ask again. That fixes it
   for everyone, where working around it fixes it once.
3. **Settle each fork with a reason.**
   `propose --choose WORD=NAME --why WORD=...` puts each choice, what it
   beat and why, and the stack, on their record as proposals. A reason is
   what the next person needs: what each add-on misreads on this kind of
   folder, as much as what it finds.
4. **Leave the seal to them.** Nothing runs and nothing is shared until they
   seal it with their key (`python kernel.py seal`). An agent never seals,
   and never reads the key (AGENTS.md, Never).
5. **Run it:** `suggest.py build` runs only the stack they sealed.
6. **Share it:** `python adapters/stdlib/stack-share/stack_share.py --box DIR`
   prints the page Show your stack (#87) asks for: their sentence, each step
   with its card's line, promises and reason, and the stack file. Only what
   they sealed is on it, and nothing of their folder; they read it and post
   it.

## One want at a time

A stack is a row of wants, in the order the person had them: each want, the
card that answers it, and the yes that put it there. It is built the way it
reads, one want at a time, and never written whole from an agent's own idea
of what the job needs. The steps above are one turn of this; the whole of it
is the turn repeated:

1. **Take one want, in their words.** "I want to do X." One thing they want
   done, not the whole job.
2. **Look for the card.** Ask the forge add-on with that sentence. Where the
   Forge can't run, ask the list (`python adapters/stdlib/similar/similar.py
   near "their sentence"`) and the roles (`python ui/canvas.py pieces --role
   ROLE`).
3. **Propose it.** The card, why it answers the want, and what it misreads
   on this kind of folder. A fork is theirs to settle. **No card is an
   answer too:** say so, and propose the line of `ui/search-words.txt` their
   word was missing, or the idea for `adapters/planned.json`. A want no card
   answers is never a step written by hand around the gap.
4. **On their yes, it goes on the stack:** one step, with the want kept
   beside it, as a note above the step in the stack file.
5. **Run the stack as it now stands,** from a fresh box (the box, their
   words list on it, the stack, then `verify`), and say what the new step
   found and what it got wrong.
6. **The next want.** "Next I want to do Y." Down the row.

It holds whether the forge add-on is there or not: the Forge follows a chain
of thoughts the same way every time, and an agent working here follows the
same chain by hand when it isn't in play.

What this rules out:

- **A whole stack at once.** Ten steps the person never asked for, proposed
  together, is the agent's plan with their name on it.
- **Running an add-on beside the stack.** If it is worth running, it is a
  step, with its want and its reason; run from the stack, what it printed is
  on the page with the rest.
- **Reading a file in full to find out what it says.** If you need to, the
  stack is missing a step: a reader, an index, a question.

**A pile can have more than one stack, and no one of them is the right
one.** Each is a different question of the same folder, and good answers
come from many arrangements. What they share is being full: something that
turns each kind of file into words, the person's own words list, a way of
finding, and a check on what was found. One add-on over raw files is a
step, not a stack. `demo/five-repos` is the worked example: one folder,
seven stacks, a words list, and a report for each run saying what it found
and what it got wrong.

That demo kept to this by a narrow task and explicit prompting, the person
carrying the row from prompt to prompt. This section is so that it holds
without that. Whatever is built to carry the row (the forge taking one want
and adding to the stack that is already there, say) is held to this page.

Where the Forge can't run (it needs forge-play and Python 3.11 or newer),
say so, and write the stack file by hand, each step with its reason beside
it, so what's shared still says why.
