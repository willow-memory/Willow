<!-- willow-addon
section: Ways to use it
line: Answers in Vim and Neovim's quickfix list, each a jump to its file and line.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# vim

Willow in Vim and Neovim: a :Willow command: your question goes to pipe on standard input, and its file:line: answers fill the quickfix list, each a jump.

    python adapters/stdlib/vim/vim.py --box DIR

It prints the lines to paste into your vimrc (~/.vimrc, or init.vim for Neovim), and changes nothing itself.
Then: `:Willow when is the dentist`, then `:cnext` and `:cprev`, or Enter on a line.

The answers come from [pipe](../pipe/) with `--grep`, one `file:line: text`
a line, the form every editor already reads for grep. Each question is the
kernel's own bite, so it's on the record as if you'd typed it.

**Uses:** nothing of the kernel's but its exit codes; pipe asks.

**Never:** edits Vim and Neovim's settings for you, approves, reads your key,
or goes online.
