<!-- willow-addon
section: Assistants
line: A Stop hook that won't let an assistant's turn end while the record doesn't verify or its changes aren't committed, and says which.
source: box
added: 2026-10-29
writes: nothing
network: none
tags: hooks
-->
# hook-stop

Won't let an assistant say it is done while the record is broken or its work is
sitting uncommitted, and says which.

```
python adapters/stdlib/hook-stop/hook_stop.py run --box DIR [--repo DIR]
python adapters/stdlib/hook-stop/hook_stop.py check --box DIR [--repo DIR]
```

`run` is a Stop hook: it runs when an assistant is about to end its turn. It
reads the JSON the assistant sends on standard input and checks two things, by
rule:

| It checks | Passes when |
|---|---|
| the record | the box's chain verifies (the kernel's own check) |
| the work | the repository has no modified, deleted or untracked file, as `git status` counts them |

If either fails, the turn may not end: exit 2, and the reason on standard
error says which, and what:

```
Not done yet: the record does not verify (row 12 breaks the chain).
Not done yet: 3 files have changes that are not committed: kernel.py, notes/a.md, notes/b.md. Commit them, or say why they stay.
```

Five files are named, then a count. The repository is `--repo`, else the `cwd`
the hook is sent, else the current folder; a folder that is not a git
repository, or no git at all, is not checked and nothing is said of it.

**It can't trap an assistant.** When the hook is sent `stop_hook_active` true,
it has already held the turn once this round and lets it end, so a rule that
can't be met never loops. Input that is not a JSON object is allowed too: a Stop
hook that blocked on what it can't read could not be left running.

`check` is the same look for a person: both results, and exit 42 when either
fails.

It asks git for its status with `--no-optional-locks`, so even git writes
nothing, and it reads the record through the kernel; it never reads the key.
To use it, put the `run` command where the assistant's settings name a Stop
hook. Exit codes: 0 the turn may end (or `check` is clean); 42 `check` found a
failure; 2 a turn that must not end, or a bad command line.

**Uses:** the kernel's `read`, and `git status`.

**Never:** commits, stages or changes anything; reads the key; writes anything.
