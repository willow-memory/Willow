<!-- willow-addon
section: Assistants
line: A PreToolUse hook that blocks, by fixed rule and never by judgment, a tool call that would read your key or write willow's record behind its back, naming the rule.
source: box
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, assistant, hooks
-->
# hook-guard

Keeps an assistant out of the two places a box is the person's alone: its key,
and its record.

```
python adapters/stdlib/hook-guard/hook_guard.py run --box DIR
python adapters/stdlib/hook-guard/hook_guard.py rules

key        the call names the box's key file
box-write  the call would change a file inside the box other than through kernel.py
```

`run` is a PreToolUse hook. It reads what the assistant is about to do (the
JSON Claude Code, Gemini CLI and Cursor send on standard input) and holds it to
two rules. A call that breaks one exits 2, and the reason on standard error
names the rule:

```
refused: rule box-write: this Write is inside the box; only kernel.py writes there.
refused: rule key: this command names the key file; the key is the person's.
```

| Rule | It refuses | It leaves alone |
|---|---|---|
| `key` | a Read, Grep or Glob whose path is the key; a command with the key's path in it, or a word that resolves to it | every other file; the key's folder; the record |
| `box-write` | a Write, Edit, MultiEdit or notebook edit of a file in the box; a command that redirects into it, or runs rm, mv, cp, tee, touch, mkdir, ln, truncate, chmod, install, dd or sed -i on it (for mv, cp, ln, install the place it puts something) | reading the box, copying out of it, `kernel.py` run on it, a box's sibling folder |

The key's path is the one the box's own config names (the kernel's `config`);
the key itself is never opened. A relative path is read against the call's own
`cwd` when it sends one, and `..` and links are resolved first, so they do not
hide a path.

**A rule is a test of paths and words, not a reading of the assistant's
meaning.** The same call gets the same answer, and a call it can't tell is
allowed, not guessed at: a command that builds the path at run time or hides it
in a script gets through. That is the kernel's job, which never trusts a file in
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
