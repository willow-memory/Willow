# Design note: the forge, and the pages a person approves on

**Status: findings, written 2026-11-09, with the first two fixes in the
same pull request.** The rest is not built and not yet decided; the last
section says what is open.

## Where this came from

One job was run end to end the way [stacks](../agents/stacks.md) says to: a
person asked, in their own words, for a document made from the repositories
on their machine; the forge add-on was asked with that sentence; its forks
were settled with a reason each; the lines of the document were proposed to
a box, each citing the passages it stood on; and the person sealed them on
the browse add-on's page. Thirty-eight suggestions were sealed in one
sitting.

It worked, and it showed where the forge's plan and the work came apart,
and where the page a person approves on is hard to read. Each finding below
says whether it was **seen** (run, and the result read) or only **read**
(in the code, not exercised).

## The forge

### 1. A sentence that names no card gets "empty" and nothing more (seen)

The first ask returned `forge: empty, nothing named`. The Forge's card
table matches exact words on purpose, and says ranking by closeness stays
on willow's side. So the place to help is this repository's
`adapters/deps/forge/suggest.py`: on empty, show what
[similar](../../adapters/stdlib/similar/) finds near the sentence, marked as
near and not as a hit, so the person can add the alias line knowing which
cards they meant.

### 2. One alias file, three readers, three sets of rules (seen)

`ui/search-words.txt` is read by:

- the Forge's own reader, which takes any target, hyphens included;
- the kernel's `parse_words`, which refuses a hyphenated target;
- the canvas, which uses the kernel's parser and, when it objects, goes on
  with no aliases at all.

A line written `repos = git-history, codebase-memory` worked in the forge
and silently turned off every alias on the canvas. One ranking test in
`ui/test_ui.py` was the only thing that noticed. Wanted: one parser, or a
test that holds the file to every reader; and the canvas saying which line
is bad, never going quiet.

### 3. An alias reaches a card by any part of its hyphenated name (seen)

The Forge's card table lets a target reach a card by its whole name or by
one part of it (three letters or more, a short list of plain words left
out). So `export` also reached the idea gitlab-export, `git` also reached
the idea git-notes, and `commit` reached nothing. Whoever writes an alias
line cannot tell from the file what it will reach. A forge command that
prints what one line reaches would settle it.

### 4. An idea not yet built is offered as a fork's option (seen)

The fork for "cv" listed gitlab-export beside export and timeline, tagged
"an idea, not built". The forge's card says ideas are a group of their own.
Inside a fork they are not. Choosing one was not tried.

### 5. A reader's step points at the pile (read)

The sealed stack's first step mirrors from the box's own pile with
git-history. The pile is a folder of text, not a repository, so `build`
would be expected to find nothing there. It was never run. What the job
needed was twenty-six repositories elsewhere on the machine, and that was
done by a script written beside the box. The forge has no way to say it.

### 6. One choice a fork (read)

`--choose` was given one name a word. Whether a word can take two (two
readers for "repos") is not known.

### 7. What was used never reached the stack (seen)

The office add-on read two documents into the pile, and two programs
outside willow supplied counted facts. None is in the sealed stack, because
the sentence did not name documents. The stack on the record is
git-history then export; that is not what made the document.

### 8. The forge settled a plan the work then went around (seen)

The pile was built by a script and the lines were proposed by scripts
beside the box. The forge was asked, the forks were settled and sealed, and
that was all of its part. Items 5 to 7 are three faces of this one.

### 9. Not looked at

The Forge's checkpoint, its build loop and its entry: where asking once and
remembering lives. Nothing here speaks to them.

## The pages

There are two: [the canvas](../../ui/), willow's main page, where a stack
is put together and sealed, and [browse](../../adapters/stdlib/browse/),
where a box is asked and what waits on it is approved.

### What the person said

- **Browse does not match the main page.** They look like two products.
- **A card is very hard to read.** The reference for a readable card is
  Nestor's page: the headline is a question a person can answer, state is
  a row of small labels, detail is folded away, the list is on one side
  with the opened item on the other, and each action is named, with one
  line saying how it differs from the others.
- **It could do more with what add-ons put out.** They print reports (rows,
  groups, states) that never reach a page.
- **A dashboard, not two pages.**

### What was seen on browse, before this change

- **A choice was a block of bold JSON.** The card's headline was the
  suggestion's data as written: the card's hash and all, running past the
  card's edge. The sentence a person could read was the small grey "Why"
  under it.
- **A stack was its file run together** into one bold paragraph.
- **An answer showed its asterisks.**
- **"It cites:" with nothing under it** on every suggestion that cited
  nothing.
- **Every button said "Approve this answer"**, for a choice and a stack
  too. No name on the card, no count, no grouping, no order but arrival.
- **"Coming up" on the front page filled with commit messages** dated the
  day they were mirrored. A pile of history reads as a diary of deadlines.
  Whether that is [coming-up](../../adapters/stdlib/coming-up/) misreading
  or the front page's use of it is not traced.

### Fixed in this pull request

1. **A card a person can read.** Browse now shows a choice as "For “repos”,
   use git-history", what it was chosen over, that add-on's line and the
   reason; a stack as its title and steps; an answer as its words, with
   headings, lists and bold shown as such and every character escaped
   first. Citations are folded under a count, and a suggestion that cites
   nothing says so. The suggestion's own bytes and its name on the record
   are one click away under "Exactly what you'd be approving", because
   those are what the key signs. The button names what it approves.
2. **One look.** Browse wears the canvas's colours, type and corners, light
   and dark, and a test in `ui/test_ui.py` holds the two together.

It is still one column and two links. That is the next section's.

## Open: one dashboard

Settled by the person: **the canvas is the main page**, so the dashboard
grows from it; Nestor's page is the reference for how a card reads, not for
how willow looks.

Not settled, and to be talked through before anything is built:

- **What is always in view.** A guess: what waits on you, what you have
  sealed, and the stack's steps with each one's last output.
- **Which box it opens.** The canvas builds a stack under a folder of its
  own; browse opens any box. One page means choosing.
- **How a step's output is shown.** The report contract (in the
  [ci](../../adapters/stdlib/ci/) add-on's card) already gives every
  add-on's output one shape: a state, a sentence, groups of rows. That is
  most of a panel.
- **Suggestions that replace one another.** Three drafts of one line were
  all waiting, and all were sealed. The kernel serves the first standing
  seal for a question, so the oldest draft answers where two shared one.
  The page had no way to show that, and has none now.
- **A document, not a receipt.** [export](../../adapters/stdlib/export/)
  prints every approved answer with its reason, its citations and its
  name: provenance. The document itself had to be put together by a script
  from the sealed lines. Export cannot yet print chosen answers, in an
  order, as the thing to hand someone.
- **Turning one down.** The kernel has `decline`; neither page offers it.
