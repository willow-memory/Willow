<!-- willow-addon
section: Ways to use it
line: A stack you sealed with the Forge, written out to share: your sentence, each choice and why, each step's promises, and the stack to run.
source: new
added: 2026-11-06
version: 0.1.0
writes: nothing
network: none
role: ways
uses: forge, stack
-->
# stack-share

A [stack](../stack/) you settled with the [forge](../../deps/forge/) add-on,
written out so someone else can see what you run, why, and run it on their
own folder. It's a runbook for a pile: each step is an add-on with its card's
line and promises, and the reason it is there, in your words when you gave
one. The page is what [Show your stack](https://github.com/willow-memory/Willow/issues/87)
asks for.

    python adapters/stdlib/stack-share/stack_share.py --box DIR [--sentence TEXT]

    # read my mail and tell me what is due

    A willow stack, sealed with the Forge, shared with stack-share. It holds
    the add-ons and the reasons they were chosen, never a file of the folder.

    | Step | What it does | Promises | Why this one |
    |---|---|---|---|
    | mail | .eml and .mbox files, with sender, date and subject kept. | writes to; network none | your words reached it alone |
    | coming-up | Dates written in your files in the next N days: appointments, renewals, deadlines. | writes nothing; network none | chosen for “due” over renewals: the boiler isn't a subscription |

    ## The stack, to run
    ...

Each stack you sealed is a page, in the order you sealed them; `--sentence`
picks the one sealed for those words, retyped in any case or punctuation.
A step's reason is each fork it settled, what it was chosen over and your
`--why`; a step no fork chose is there because your words reached it alone.
When a card has changed since you chose it (its SHA-256 isn't the one you
sealed), the reason says so: read the card again before you trust the
choice.

**Only what you sealed.** A stack or a choice is on the page only while the
kernel says its seal proves under your key and its proposal still hashes to
what you sealed (`kernel.sealed` and `kernel.standing`, as forge reads them).
A proposal still waiting on you, one you declined, or one whose file was
changed after you sealed it, is not shared. This reads no key itself; the
kernel does the proving.

**What it holds.** Your sentence as you wrote it, the add-ons' names, their
cards' lines and promises, your reasons, and the stack file. Never a file of
your folder, nor a passage, a date or a name from it. Your sentence and your
reasons are your own words, though: read the page before you post it, and
say the kind of folder, not what's in it.

Exit codes, the kernel's: 0 a page printed; 42 nothing sealed to share; 2
refused (a bad command line, a folder that isn't a box, a record that
doesn't verify, or no sealed stack for `--sentence`).

**Never:** writes anything, goes online, or seals. It prints the page; where
it goes is yours.
