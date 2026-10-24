<!-- willow-addon
section: Ways to use it
line: A VS Code task whose answers land in the Problems panel, each a jump to its file and line.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, interface
-->
# vscode

Willow in VS Code: a task, willow: ask, that prompts for a question and puts each answer in the Problems panel, a click away from its file and line.

    python adapters/stdlib/vscode/vscode.py --box DIR

It prints the lines to paste into .vscode/tasks.json in your project, and changes nothing itself.
Then: Terminal, Run Task, willow: ask.

The answers come from [pipe](../pipe/) with `--grep`, one `file:line: text`
a line, the form every editor already reads for grep. Each question is the
kernel's own bite, so it's on the record as if you'd typed it.

**Uses:** nothing of the kernel's but its exit codes; pipe asks.

**Never:** edits VS Code's settings for you, approves, reads your key,
or goes online.
