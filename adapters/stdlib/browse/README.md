<!-- willow-addon
section: Ways to use it
line: Your folder in your web browser: ask, read each answer at its file and line, and approve suggestions with a click, from this machine only.
source: new
added: 2026-10-24
version: 0.3.0
writes: record
network: loopback
role: ways
tags: everyday
looks-for: digest, stack, words-de, words-es, words-fr, words-pt
-->
# browse

Your folder in your web browser. Ask in your own words, read the passages
that answer (each with its file and line), see the suggestions waiting for
you, and approve one with a click. The front page shows what's waiting,
what went stale and what's coming up. Nothing to install, and no commands
to type once it's open.

    python adapters/stdlib/browse/browse.py --box DIR [--stack FILE]

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

**Who can reach it:**

| Way in | What stops it |
|---|---|
| Another computer | It listens on 127.0.0.1 only. |
| Another website, in a browser you've opened willow in | Each start makes a new secret. The link hands it to your browser as an HttpOnly, SameSite=Strict cookie, and every form carries it as well. Without both, a request gets 403. A form whose Origin isn't this page (or is `null`, as a sandboxed frame's is) gets 403. |
| A website that renames itself as this machine (DNS rebinding) | A Host header that isn't `127.0.0.1:PORT` or `localhost:PORT` gets 403. |
| A website that frames it and lays a button over Approve | `frame-ancestors 'none'` and `X-Frame-Options: DENY`. |
| Something injected into a passage | Every passage is HTML-escaped, and the page allows no scripts (`default-src 'none'`). |
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
script in your browser, or approves anything you didn't click.
