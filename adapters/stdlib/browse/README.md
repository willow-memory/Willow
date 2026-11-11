<!-- willow-addon
section: Ways to use it
line: Your folder in your web browser: ask, read each answer at its file and line, and approve suggestions with a click, from this machine only.
source: new
added: 2026-10-24
version: 0.5.0
writes: record
network: loopback
role: ways
tags: everyday
looks-for: boxes-here, digest, fair-merge, index-cache, look, projects, say, scan, stack, why-not, words-de, words-es, words-fr, words-pt
-->
# browse

Your folder in your web browser. Ask in your own words, read the passages
that answer (each with its file and line), see the suggestions waiting for
you, and approve one with a click. The front page shows what's waiting,
what went stale and what's coming up. Nothing to install, and no commands
to type once it's open.

    python adapters/stdlib/browse/browse.py --box DIR [--stack FILE] [--run FOLDER] [--index INDEX] [--beside INDEX ...] [--home FOLDER] [--say MODEL]

It prints a link and opens it. Ctrl-C stops it. `--lang de` (or `es`,
`fr`, `pt`) sends each question through that language's words add-on first.
`--port N` picks the port; otherwise it takes any free one. `--no-open`
prints the link without opening a browser.

**To start it with a double-click:**

    python adapters/stdlib/browse/browse.py launcher --box DIR

This prints a file for macOS, Windows and Linux, and says where to save
each one. It writes nothing itself.

**What it does, in the kernel's own words:** asking is the kernel's `bite`,
and approving is its `seal`, run in this process. Both are on the record
exactly as if you'd typed them. An approval is signed with your key, which
the page never shows or sends anywhere.

**How a suggestion is shown.** Each waiting suggestion is a card you can
read without knowing how it was made: what kind of thing it is, the thing in
a sentence, why, and what it stands on.

- **A choice** (a JSON object saying which was chosen for one of your words,
  and over what) reads "For “repos”, use git-history", then what it was
  chosen over, that add-on's own line, and the reason given.
- **A stack** (a file of `- NAME -- ARGS` steps under a heading) reads as
  its title and its steps, one a line.
- **An answer** is its words, with `# ` lines as headings, `- ` lines as a
  list and `**bold**` as bold. Every character is escaped first, so a
  suggestion can never write markup of its own.

Which it is, is told by the shape of what the suggestion holds, never by who
made it. The passages it cites are folded under "It cites N passages of your
folder", and one that cites none says so. "Exactly what you'd be approving"
unfolds the suggestion's own bytes and its name on the record, since those,
not the sentence above them, are what your key signs. The button says what
it approves: this choice, this stack, this answer.

The page wears the colours, type and corners of [the canvas](../../../ui/),
willow's main page, and `ui/test_ui.py` holds the two together.

**What your stack found.** With `--stack FILE`, a stack file as
[stack](../stack/) runs it, the page gains a third link. Each step whose card
says it prints a report is run and drawn as a card:

- whose report it is, and its state in words: found, nothing found, or
  couldn't look. A report that found things and waits on you says so;
- the one thing it said, as the card's headline;
- its rows, where and then what, under their groups' names. The first eight
  are in sight and the rest fold under "All N rows".

Every report add-on prints the one shape (the report contract, in the
[ci](../ci/) add-on's card), so one way of drawing serves them all, and a
report add-on written tomorrow is drawn without this changing. A step that
prints something else (a reader's mirror, a model's suggestion) is named
under the cards and left to stack. The steps are run when you open the
page, each time: it shows what they find now, not what a run kept.

**The run.** With `--run FOLDER`, a run the stack add-on kept with its
`--to`, the page gains a link that shows that run and runs nothing:

- each step in the order it ran, with its number, and whether it has ended:
  its exit code, `flagged`, `kept from before` when the run was resumed, or
  `running`;
- a report step drawn from the data the run kept for it, the same card as
  above, so a step that took an hour is read, not waited for again;
- any other step as the words it printed, the first eight lines in sight.

While the run is still going, the page says so and looks again every three
seconds, with no script: a step's lines show up as it prints them. When the
run's log says it is done, the page says how many steps were flagged and
stops asking. It reads the folder only, and writes nothing, not the record.

**A question goes to the step whose job it is.** With `--run FOLDER`, the
ask box does one more thing. Your question is still the kernel's own
`bite`, on the record, and its passages are still shown. Above them, the
[look](../look/) add-on says what kind of question it is and shows what the
run's steps already found for that kind:

- "who still owes me money" shows the lines the run's debts and invoices
  steps kept, each with its file and line in the run;
- a question no one passage answers, but a step did, is not called a miss:
  the page says "No one passage in your folder says that", under the
  step's lines;
- a step whose job it is that the run doesn't have is named, with
  `waits on you`: that is a step to add to your stack;
- a thing you wrote down ("the wifi password") is the kernel's alone, and
  the page is as it was.

Nothing is run again; the run's kept files are only read.

**A miss says why.** When nothing in your folder holds a question, the
[why-not](../why-not/) add-on's report is drawn under it: which words no
passage holds, the nearest passages and what they lacked, a close spelling.
Without the look or the why-not add-on, the page is as it was.

**The middle is a stream.** Asking doesn't replace the page: each
question and its answer is added under the last, in the order they were
said, with the ask box at the bottom.

- **Your line is plain,** as you typed it, with the time.
- **What the page says back is marked `willow · code`.** It is one line,
  made by code from what the boxes under it hold: "Your files hold 3
  passages for that; the first is at notes/recipes.txt:12." No model is
  asked, and nothing is said that a box doesn't hold.
- **The boxes are under the line:** the first in sight, the rest behind
  `more?`.
- **The newest answer is open; the ones before fold to their line.** Click
  a line to open it again.
- **A question asked before says so:** "asked before: first on 2026-11-10
  at 22:58", read from your record by the question's key, and the answer
  is shown again. The record keeps that key and never your words.
- **Small talk is answered by code** with one of a few fixed words
  ("thanks", "Anytime."). Nothing is asked of your folder and nothing goes
  on your record.
- **The stream opens with what waits and what is coming up,** the front
  page's summary, folded once you've asked something.

The stream lasts as long as the page runs. It is kept nowhere else: stop
browse and it is gone, and your record still holds every ask, by its key.

**A model may say it too, and never the last word.** With `--say MODEL`,
an [Ollama](https://ollama.com) tag on this machine, each answer also gets
a sentence from that model, under code's line:

- **It is marked with the model's name,** `willow · llama3.2:3b`, never as
  code's.
- **It is given only what code said:** your line, and the same facts
  code's line was made from.
- **The [say-check](../say-check/) add-on holds it to those facts.** A
  sentence that keeps to them stands. One that adds a word or a number,
  or misquotes you, is struck: shown struck through, with what failed,
  and code's line above it stands.
- **It comes after the page is up.** Code's line is there at once; the
  page's script asks for the model's sentence, which can take seconds. With
  scripts off there is no model's sentence, and code's line is the reply.
- **It is asked once a turn,** kept with the turn while the page runs, and
  goes nowhere near your record.
- **Small talk and the opening are code's alone.**

The model is asked by the [say](../say/) add-on, on this machine only. A
model that can't be asked is said in a word, and nothing else changes.

**Three panels.** Every page is laid out the same way:

- **Left, where you are:** the project's name, then each section there is
  to open: Ask, Waiting for you (with how many wait), What your stack
  found, The run. Under the run, each of its steps, marked when it was
  flagged or is still running; a step's link goes to its card. With
  `--home FOLDER`, the folder your projects are under, the other projects
  the [projects](../projects/) add-on finds there are listed too. Click
  one and the page opens it: its box, its newest run, and its own stream.
  Only a project found under that folder can be opened.
  With `--boxes FILE`, a list of boxes kept somewhere else on this machine,
  those are listed under "Elsewhere", each with how many suggestions wait
  on it, and a click opens one where it is. "Find boxes in a folder" looks
  through a folder you name for boxes already there (the
  [boxes-here](../boxes-here/) add-on), and the ones you tick go on the
  list. Nothing is copied or moved, a box that is there is never made
  again, and the list is written by boxes-here, not by this page. Each box
  on it is marked "not for cloud": yours to keep from a model that isn't on
  this machine. Only a box on the list can be opened this way.
- **Middle, the section that is open.**
- **Right, what is at a place.** A file and line anywhere on a page
  (`notes/iou.txt:3`) is a link. Click it and the right panel shows the
  passage of your folder that holds that line, or, for a line of the run's
  kept files, the lines around it. `Close` shuts the panel. Only a file the
  kernel reads into your folder's passages, or one of the run's kept
  files, is ever opened this way.

On a narrow screen the three stack, top to bottom.

**One script, its own.** The right panel fills without leaving the page
because of one small script, `page.js`, beside `browse.py`. The same
script asks for a model's sentence when you named one with `--say`. The page allows
that file and no other: no script from anywhere else, and none written into
a page. It asks only this page for anything. With scripts off, every link
it handles is still a link: the place opens as a page of its own.
Approving stays a plain form.

**An index, if you keep one.** With `--index INDEX`, an index of your
folder that [index-cache](../index-cache/) keeps current, a question is
answered from the index instead of by reading every file again. The answer
is the kernel's own, passage for passage, and the ask is on your record the
same way. When the index isn't current (a file changed since it was built),
or the [scan](../scan/) or index-cache add-on isn't here, the kernel reads
the folder as before.

A passage is shown when it holds half your question's words, so it can
answer and still lack the thing you asked about. With an index and the
[fair-merge](../fair-merge/) add-on, the page says which of your words no
passage in your folder holds at all: "No passage in your folder holds:
violin." That line is true without any ranking.

**Other piles, beside your folder.** With `--beside INDEX`, once for each,
other piles' indexes ([scan](../scan/) makes one) are asked the same
question by fair-merge. What they hold is shown under your folder's answer
in a box of its own, "Other piles, not your folder": each pile ranked alone
and taking turns, a passage two piles hold shown once, and each pile's own
line, "found nothing" or the words it lacks. None of it goes on your
record, none of it can be approved, and its places are not links: they are
not in your folder.

**Drag a project onto the open one** (with `--home`) and it is asked beside
it the same way: every index found in that project is a pile, named
`project: index`. It is marked "beside" in the left panel, and its × takes
it away again. The small + does the same with scripts off. Nothing is
copied, merged or written, in either project: it is a way to see whether
two projects belong together before anything is done about it, and it lasts
while the page runs. A project with no index says so and isn't asked: a
folder is never read whole for this.

**Who can reach it:**

| Way in | What stops it |
|---|---|
| Another computer | It listens on 127.0.0.1 only. |
| Another website, in a browser you've opened willow in | Each start makes a new secret. The link hands it to your browser as an HttpOnly, SameSite=Strict cookie, and every form carries it as well. Without both, a request gets 403. A form whose Origin isn't this page (or is `null`, as a sandboxed frame's is) gets 403. |
| A website that renames itself as this machine (DNS rebinding) | A Host header that isn't `127.0.0.1:PORT` or `localhost:PORT` gets 403. |
| A website that frames it and lays a button over Approve | `frame-ancestors 'none'` and `X-Frame-Options: DENY`. |
| Something injected into a passage | Every passage is HTML-escaped. Past that, the only script the page allows is its own file (`script-src 'self'`): one written into a page, as an injected one would be, never runs. |
| A program already running as you | Nothing. That program could run `kernel.py seal` itself, so the page gives it no reach it didn't already have. |

Checked in a real Chromium as well as in the tests. With willow open in one
tab, a page on another port tried to frame it (refused by the CSP) and to
submit an approval (403, and the record had no seal). The person's own ask,
read, approve and ask-again worked. That run also caught a bug the tests
couldn't: under `Referrer-Policy: no-referrer`, Chromium sends `Origin: null`
on the page's own forms, so they were refused. It's `same-origin` now.

**What it leaves out:** turning a suggestion down (the kernel's `decline`
does it, from a terminal; the page has no button for it, so there it just
keeps waiting), and words in the page in a language other than English.

**Uses:** the kernel's `bite`, `seal`, `read`, `sealed` and `chunks`; the
[digest](../digest/) add-on for the front page, and a
[words](../words-de/) add-on with `--lang`. Each is optional: if it was
deleted, the page says so.

**Never:** listens beyond this machine, shows or sends your key, runs a
script in your browser that isn't its own one file, or approves anything
you didn't click.
