<!-- willow-addon
section: Assistants
line: A PreToolUse hook that refuses a write or a command holding a key, password or card number, by the privacy add-on's shapes, naming only the kind.
source: box
added: 2026-10-29
writes: nothing
network: none
tags: hooks
-->
# hook-leaks

Stops an assistant writing a secret into a file or a command.

An assistant that has seen a key can paste it into a file it writes, a
command it runs, or a notebook cell, and from there it is in your history and
maybe your repository. This is a PreToolUse hook that looks at the text a
call would write or run, and refuses the call if that text holds a key, a
password or a card number.

    python adapters/stdlib/hook-leaks/hook_leaks.py run

It reads the JSON the assistant sends on standard input. A call it refuses
exits 2, and the reason on standard error says only the kind, so a refusal
can't leak what it stopped:

    refused: this Write holds a key and a card number; the value is not shown.
    Take it out, or leave it for the person to put there.

To use it, put that command where the assistant's settings name a PreToolUse
hook (for Claude Code, a hook entry in its settings file, matching Write,
Edit, MultiEdit, NotebookEdit and Bash).

| What it looks at | What it leaves alone |
|---|---|
| a Write's content, an Edit's or MultiEdit's new text, a notebook cell, a Bash command | the text an Edit takes out, so a secret can still be removed; every other tool; an email, a phone number, an address |

The shapes are [privacy](../privacy/)'s: the key formats of the model
providers, GitHub, AWS, Slack, Google and Stripe, a private key block, a JWT,
a password after its label, and a card number that passes the Luhn check. It
catches what has a shape; a secret with none gets through. Input that is not
a JSON object is refused as well, since a hook that can't read the call can't
say it is safe; [hook-fail-closed](../hook-fail-closed/) puts that rule round
any hook that breaks.

`check --from FILE` is the same look at a file, for a person: it lists each
kind and how many, never the value, and exits 42 when there is any.

Exit codes: 0 allowed (or `check` found nothing); 42 `check` found something,
which waits on you; 2 refused, or a bad command line.

**Uses:** the privacy add-on's `scrub`.

**Never:** shows the value it refused, or writes anything.
