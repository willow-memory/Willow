<!-- willow-addon
section: Ways to use it
line: A willow command and tab completion for bash, zsh, fish and PowerShell, on Linux, macOS and Windows.
source: new
added: 2026-10-24
writes: record
network: none
tags: no-install, offline, records, interface
-->
# shell

`willow` as a command in your shell, with its verbs tab-completed, on Linux,
macOS and Windows.

    python adapters/stdlib/shell/shell.py script bash >> ~/.bashrc
    export WILLOW_BOX=~/willow-box
    willow bite "when is the dentist"

| Shell | Load it with |
|---|---|
| bash | `shell.py script bash >> ~/.bashrc` |
| zsh | `shell.py script zsh >> ~/.zshrc` |
| fish | `shell.py script fish > ~/.config/fish/conf.d/willow.fish` |
| PowerShell (Windows, macOS, Linux) | `shell.py script powershell >> $PROFILE` |
| Windows cmd | `shell.py script cmd > willow.cmd`, in a folder on your PATH (no completion) |

`willow VERB ...` is the kernel's own command line. When `WILLOW_BOX` is set
and you give no `--box`, it adds `--box $WILLOW_BOX`. The record and the
exit codes are the kernel's.

**Uses:** the kernel's `main`.

**Never:** edits your shell's files (you choose where its lines go),
approves on its own, or goes online.
