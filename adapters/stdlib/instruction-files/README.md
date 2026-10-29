<!-- willow-addon
section: Assistants
line: For a folder, which instruction files each coding agent would load (AGENTS.md, CLAUDE.md, GEMINI.md, rules folders), in what order, with each file's size and hash.
source: box
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, assistant
-->
# instruction-files

Which instruction files each coding agent would load here.

Claude Code reads CLAUDE.md, Codex and Cursor read AGENTS.md, Gemini reads
GEMINI.md, and each has its own rules folders. This lists, for a folder, what
each would read, general first and most specific last, with every file's size
and the start of its SHA-256, so you can see what an agent was told.

    python adapters/stdlib/instruction-files/instruction_files.py --box DIR
    python adapters/stdlib/instruction-files/instruction_files.py --from REPO --at SUBFOLDER

    claude-code
        1  CLAUDE.md                    11 B   sha256:336cc4fbf19b
        2    @AGENTS.md (imported)   11.3 KB   sha256:84a1e7b619d9
    codex-cli
        1  AGENTS.md                 11.3 KB   sha256:84a1e7b619d9

| Agent | Files |
|---|---|
| claude-code | CLAUDE.md, .claude/CLAUDE.md and CLAUDE.local.md in each folder from the top down; .claude/rules; the files an `@path` import pulls in |
| codex-cli | in each folder from the top down, AGENTS.override.md, or else AGENTS.md |
| gemini-cli | GEMINI.md in each folder from the top down |
| cursor | AGENTS.md in each folder; .cursor/rules; .cursorrules |
| copilot | .github/copilot-instructions.md; .github/instructions; AGENTS.md in each folder |
| windsurf | AGENTS.md in each folder; .windsurfrules; .windsurf/rules |
| opencode | in each folder, AGENTS.md, or else CLAUDE.md |
| cline | .clinerules, a file or a folder of them |

Without `--at` it is the top of the folder; with it, each folder down to
that one adds its own files after the ones above. An `@path` import inside a
code span or block, outside the folder, or already read is not followed, and
imports go five deep. Two files with the same bytes are said to be the same.

It lists what each tool documents reading. An agent's version, its settings,
and any global file in your home folder can add more, and are not read here.

Exit codes, the kernel's: 0 at least one instruction file would load; 42 none
would, which waits on you; 2 refused.

**Uses:** the kernel's box, to find the pile.

**Never:** writes anything, or runs a file it lists.
