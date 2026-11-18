# Design note: my-installs, what is already installed here

**Status: an idea, 2026-11-18; nothing is built.** One entry on
`adapters/planned.json`.

## The idea, in one line

List the skills, plugins, extensions and hooks installed on this machine,
say what each can touch, and say what changed since the last time you looked.
It only prints.

## Why it is missing

[skill-picks](skill-picks.md) looks outward, at what to install. Nothing looks
at what is already there. The research found most harm comes from things
people already trusted: marketplace installs update on their own, so a skill
vetted once can change. A signature shows a folder is unchanged since it was
published, not that it is safe.

## What it reads

- The usual install places for the assistants and editors on this machine
  (each assistant's skills folder, plugin folder, hook settings).
- For each item: its name, where it came from, its version or commit, its
  licence, and the tools it asks for (shell, network, files, spending).
- A saved list of what it saw last time, kept by the person, so it can
  show what is new, gone or changed.

## What it says

A table of what is installed, then the changes since last time. Anything that
asks for more than its own instructions mention gets a line. It never
removes, updates or approves anything.

## Edges

- Network: none. It reads local folders only. Looking up whether an item is
  still kept is `still-kept`'s job.
- It reads folders in the person's home. It never reads a key or a secret,
  and it prints no file contents beyond the declared tool list.
