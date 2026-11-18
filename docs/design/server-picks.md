# Design note: server-picks, the best current MCP servers

**Status: an idea, 2026-11-18; nothing is built.** One entry on
`adapters/planned.json`. The name avoids a `mcp-` first word, which
`mcp-lite`, `mcp-sampling` and `mcp-by-hash` already use.

## The idea, in one line

The same job as [skill-picks](skill-picks.md), for MCP servers: the best and
most current for a given job, ranked on upkeep and source, with what each can
touch, pinned to the version checked. It only prints.

## Why it is missing

There are thousands of MCP servers and the trust problem is the same as for
skills, with a sharper edge: a server runs code and holds credentials. `hosts`
registers a server and `mcp-by-hash` pins one, but nothing helps a person
choose one.

## What it reads

- Upkeep signals from [still-kept](still-kept.md).
- Official or not: the vendor's own server, or someone else's wrapper.
- What the server asks for: files, shell, network hosts, accounts, and
  anything that can spend money or write.
- The tools it declares against what its code does, as a mismatch line.

## What it says

A short ranked list per job with the evidence, and a warning on anything
that holds credentials. It never registers or installs a server; `hosts`
does that, on the person's yes.

## Edges

- Online only to read public repositories (`api.github.com`).
- Directory counts are self-reported, so it counts what it finds itself.
- Same unchecked-claims warning as `skill-picks`: scanners miss malicious
  plain-language instructions, so the README is read as text.
