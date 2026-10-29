<!-- willow-addon
section: Assistants
line: A command split the way the shell will split it, quotes, variables and chained commands included, before any rule judges it, so a rule can't be dodged by spelling.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, assistant, hooks
-->
# hook-shell

A rule about a command has to see the command the shell will run.

Ban `rm -rf` by looking for those letters and it is dodged by spelling: the
shell reads `r""m`, a backslash before the name, a full path, `$'\x72m'`,
variables put together, a payload in `bash -c`, `eval`, `$(...)`, or the
command after `sudo`, `env`, `nohup` or `xargs` as the same command. This
reads a command the way the shell does first, and only then judges it.

    python adapters/stdlib/hook-shell/hook_shell.py split "COMMAND"
    python adapters/stdlib/hook-shell/hook_shell.py run --deny "rm -rf" --deny "git push --force"

`split` prints each simple command the shell would run, words unquoted and
variables filled in:

    $ hook_shell.py split 'x=r; sudo "${x}m" -rf /tmp/a && echo $(id)'
    top      rm -rf /tmp/a
    subst    id
    top      echo '$(id)'

The first column is where it came from: `top` (what was typed), `subst`
(inside a substitution) or `sh -c` and `eval` (a payload the shell runs
again). A command is listed after the ones inside it. A command word that
can't be known before it runs (an unset variable, a glob, a substitution) is
marked `dynamic`.

`run` is a PreToolUse hook for Bash: it reads the call on standard input and
refuses it (exit 2, the reason on standard error) when any command it would
run matches a deny rule, or has a dynamic command word, since no rule can
judge that. Calls to other tools pass, and input that is not a JSON object is
refused.

| A rule | Matches |
|---|---|
| rm -rf | rm with the flags r and f, as -rf, -fr or -r -f |
| git push --force | git, then push, and the flag --force (also --force=1) |
| curl | any curl at all, by its name and not its path |

Flags match as a set, and the words that are not flags must come first, in
order. After a bare double dash a word is not a flag. A rule is a command, not
a regular expression. `--rules FILE` reads one rule a line, with `#` for
comments, and `--deny` can be given as often as needed.

**What it reads:** single and double quotes, backslashes and line
continuations, `$'...'` escapes, `$VAR` and `${VAR}` from assignments earlier
in the same command (an unquoted value splits on blanks, a quoted one does
not), `$(...)` and backticks, `;`, `&&`, `||`, `|`, `&`, newlines,
parentheses, `if`, `then` and `do`, and a redirection like 2>&1 as part of a
word. It follows `sh -c`, `eval` and the wrappers up to five deep, and
refuses a command it can't read (an unclosed quote) rather than guess.

**What it doesn't:** know what a script file does, or a variable set outside
the command. A command that runs a script file is judged by the script's name, not by
what is in the file.

Exit codes: 0 allowed (or `split` printed); 2 refused, or a bad command line.

**Uses:** the kernel's exit codes.

**Never:** runs the command it reads, or writes anything.
