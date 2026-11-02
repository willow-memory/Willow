<!-- willow-addon
section: Assistants
line: Aider reads answers from your folder with its /run command, file and line included.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# aider

Willow in Aider: the /run line that asks your folder: Aider runs it and offers to add the answers, each with its file and line, to the chat.

    python adapters/stdlib/aider/aider.py --box DIR

It prints the lines to paste into Aider's chat, as a /run command, and changes nothing itself.
Then: paste the line into Aider's chat with your question in place of 'your question'.

The answers come from [pipe](../pipe/) with `--grep`, one `file:line: text`
a line, the form every editor already reads for grep. Each question is the
kernel's own bite, so it's on the record as if you'd typed it.

**Uses:** nothing of the kernel's but its exit codes; pipe asks.

**Never:** edits Aider's settings for you, approves, reads your key,
or goes online.
