<!-- willow-addon
section: For maintainers
line: Commands and paths named in AGENTS.md, CLAUDE.md or GEMINI.md that no longer exist in the repo.
source: new
added: 2026-10-29
writes: nothing
network: none
role: page
output: report
-->
# agents-md-check

The instructions you wrote for coding agents, checked against the repo.

An AGENTS.md, CLAUDE.md or GEMINI.md tells an agent which commands to run
and which files matter. When a script is renamed or a make target dropped,
the file keeps saying the old thing and the agent follows it. This lists
what the file names that the repo no longer has, by file and line.

    python adapters/stdlib/agents-md-check/agents_md_check.py --box DIR [--json]
    python adapters/stdlib/agents-md-check/agents_md_check.py --from REPO [--json]

    agents-md-check: populated, 3 things named in 2 instruction files not found; each is a lead: a path a build makes shows here too
    ## path
      AGENTS.md:57  adapters/old/old.py: no such file
    ## import
      CLAUDE.md:3   RULES.md: no such file
    ## make target
      AGENTS.md:60  make lint: not in the Makefile

It prints [a report](../ci/README.md#the-report-contract): a group per kind
of thing named (path, import, make target, script), each row the line of the
instruction file and then what it names and why it is dead. `--json` gives
the same report as one JSON object.

| Named as | Checked against |
|---|---|
| a path in backticks or a code block (it has a slash, or ends in a file extension) | the repo from its top, then the file's own folder |
| a relative link, with any `#fragment` left off | the same |
| the script a command runs (python, node, bash, sh, a leading `./`) | the same |
| `make TARGET` | the targets in the Makefile, when there is one |
| `npm run NAME` (also pnpm and yarn) | the scripts in package.json, when there is one |
| an `@path` import on a line of its own | the same |

Every AGENTS.md and CLAUDE.md under the folder is read, except inside
node_modules, vendor and .git. Left alone, since they say nothing about this
repo: URLs, absolute and `~` paths, a path holding `<`, `{`, `*`, `$` or
`...`, and a path whose first part is a CAPITALISED placeholder such as `DIR`
or `VENV`. A bare name with no slash counts as a file only when it ends in a
known file extension, so `sys.argv` is not one.

What it lists is a lead, not proof: a file a build makes, or one the command
itself creates, shows up here too.

Exit codes, the kernel's: 0 everything named is there, or no instruction
file (empty); 42 something named is gone (populated), which waits on you; 2
refused.

**Uses:** the kernel's box, to find the pile.

**Never:** runs the commands it reads, or writes anything.
