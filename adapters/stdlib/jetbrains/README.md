<!-- willow-addon
section: Ways to use it
line: An external tool for IntelliJ, PyCharm and the rest, with answers as links to file and line.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# jetbrains

Willow in IntelliJ, PyCharm and the other JetBrains IDEs: an external tool, willow, that asks for a question and prints each answer as a link to its file and line.

    python adapters/stdlib/jetbrains/jetbrains.py --box DIR

It prints the lines to paste into External Tools.xml in the IDE's config folder, under tools/ (or Settings, Tools, External Tools, with the same values), and changes nothing itself.
Then: Tools, External Tools, willow.

The answers come from [pipe](../pipe/) with `--grep`, one `file:line: text`
a line, the form every editor already reads for grep. Each question is the
kernel's own bite, so it's on the record as if you'd typed it.

**Uses:** nothing of the kernel's but its exit codes; pipe asks.

**Never:** edits IntelliJ, PyCharm and the other JetBrains IDEs's settings for you, approves, reads your key,
or goes online.
