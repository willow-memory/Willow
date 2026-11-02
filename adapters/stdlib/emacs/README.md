<!-- willow-addon
section: Ways to use it
line: Answers in an Emacs compilation buffer, each a jump to its file and line.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# emacs

Willow in Emacs: an M-x willow command: the answers fill a grep-mode buffer, each line a jump to its file and line.

    python adapters/stdlib/emacs/emacs.py --box DIR

It prints the lines to paste into your init file (~/.emacs.d/init.el), and changes nothing itself.
Then: `M-x willow`, then Enter (or `next-error`) on a line.

The answers come from [pipe](../pipe/) with `--grep`, one `file:line: text`
a line, the form every editor already reads for grep. Each question is the
kernel's own bite, so it's on the record as if you'd typed it.

**Uses:** nothing of the kernel's but its exit codes; pipe asks.

**Never:** edits Emacs's settings for you, approves, reads your key,
or goes online.
