<!-- willow-addon
section: Assistants
line: A PreToolUse hook that blocks, by fixed rule, never judgment, a call that would read your key, seal with it, or write your record.
source: box
added: 2026-10-29
version: 0.2.1
writes: nothing
network: none
role: guards
tags: hooks
-->
# hook-guard

Keeps an assistant out of the two places a box is the person's alone: its key,
and its record; and off the one act that is the person's alone, the seal.

```
python adapters/stdlib/hook-guard/hook_guard.py run --box DIR [--also DIR]...
python adapters/stdlib/hook-guard/hook_guard.py rules

key        the call names the box's key file
box-write  the call would change a file inside the box other than through kernel.py
beside-write  with --also DIR, the call would change a file inside that folder
seal       the call runs a kernel's seal or decline, which read the key themselves
```

`run` is a PreToolUse hook. It reads what the assistant is about to do (the
JSON Claude Code, Gemini CLI and Cursor send on standard input) and holds it to
its rules. A call that breaks one exits 2, and the reason on standard error
names the rule:

```
refused: rule box-write: this Write is inside the box; only kernel.py writes there.
refused: rule beside-write: this Write is inside a folder kept beside the box; only the runtime writes there.
refused: rule key: this command names the key file; the key is the person's.
refused: rule seal: this command runs the kernel's seal or decline; a seal is the person's, never an assistant's.
```

| Rule | It refuses | It leaves alone |
|---|---|---|
| `key` | a Read, Grep or Glob whose path is the key; a Grep whose path (the call's own folder, when it names none) is the key's folder or one above it, or a recursive Glob there whose pattern could name the key, since a Grep reads every file it finds; a command with the key's path in it, a word that resolves to it, a glob the shell would expand to it (a star or a question mark in the key's folder or its name), or a recursive read of its folder or one above it (`grep -r`, `rg`, `cp -r`, `rsync -a`, `zip -r`, `tar` making an archive; with no folder named, the one it runs in) | every other file; a listing of the key's folder; a search there whose own `glob` or pattern leaves the key out (`*.md`, or a folder the key is not in); a glob the shell expands beside the key's folder, not into it; `ls -R`, `du`, `tar x`; the record |
| `box-write` | a Write, Edit, MultiEdit or notebook edit of a file in the box; a command that redirects into it, or runs rm, mv, cp, tee, touch, mkdir, ln, truncate, chmod, install, dd or sed -i on it (for mv, cp, ln, install the place it puts something; for mv also what it moves, since a file moved out of the box changes it); `find` from it with `-delete`, or `-exec` of one of those; `git -C` or `--work-tree` on it with a command that changes files (`clean`, `checkout`, `reset`, `restore` and the like); `tar` extracting, or `unzip`, into it (its `-C` or `-d`, else the folder the command runs in) | reading the box, copying out of it, `kernel.py` run on it, a box's sibling folder, `find`, `git status` or `git log` on it, `tar -c` or `-t` from it, `unzip -l` |
| `beside-write` | with `--also DIR`: the same as `box-write`, for that folder; the folder need not exist yet | reading it, copying out of it, a folder whose name only starts with the same letters |
| `seal` | a command that runs a kernel with `seal` or `decline` as its verb: `kernel.py`, or a port's (TypeScript's, Java's, C#'s, Go's and Rust's, built or run from source), by the file's name wherever it is, on any box | every other kernel command (`bite`, `propose`, `verify`, `out`); "seal" or "decline" as any other word, a question's included |

`seal` is there because `seal` and `decline` read the key themselves, from the
box's config: a command that runs them names no key and changes nothing by
hand, so `key` and `box-write` both let it by, and it writes the person's yes
or no (#91). It is a test of words like the rest. A seal from a script the
assistant writes, or from code that imports the kernel, gets through. The one
guarantee no hook can give itself is the machine's: **keep the key where the
account the assistant runs as can't read it**, and a seal it reaches for
fails at the kernel.

`--also DIR` may be given more than once. It is for a program that keeps its
own files beside the box and writes them itself: the assistant's tool calls are
held off that folder, the program's own code is not, since the hook judges only
the assistant's calls.

The key's path is the one the box's own config names (the kernel's `config`);
the key itself is never opened. A relative path is read against the call's own
`cwd` when it sends one, and `..` and links are resolved first, so they do not
hide a path.

**A rule is a test of paths and words, not a reading of the assistant's
meaning.** The same call gets the same answer, and a call it can't tell is
allowed, not guessed at: a command that builds the path at run time or hides it
in a script gets through. What gets through, plainly: a path built at run time
(`$VAR`, a command substitution, a script or program the assistant writes and
runs), and a `cd` earlier in the same command that a later path is read against.
So it stops a careless or direct tool call, not code written to get round it.
For the box that is the kernel's job, which never trusts a file in
the box (a proposal's bytes must still hash to what was sealed). Input that is
not a JSON object is refused: a hook that can't read the call can't say it is
safe ([hook-fail-closed](../hook-fail-closed/) puts the same rule round any
hook).

To use it, put the `run` command where the assistant's settings name a
PreToolUse hook (for Claude Code, a hook entry matching Write, Edit, MultiEdit,
NotebookEdit, Read, Grep, Glob and Bash).

It writes nothing and opens neither the key nor the record. Exit codes: 0
allowed (or `rules`); 2 refused, or a bad command line.

**Uses:** the kernel's `config`.

**Never:** reads the key; writes anything; judges what an assistant meant.
