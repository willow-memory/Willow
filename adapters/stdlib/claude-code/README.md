<!-- willow-addon
section: Assistants
line: Claude Code sees cited passages from your folder with each prompt, through its prompt hook.
source: bot
added: 2026-10-24
writes: record
network: none
-->
# claude-code

Claude Code reads what your own files say about each prompt, before it
answers, with each passage's file and line.

    python adapters/stdlib/claude-code/hook.py setup --box DIR

`setup` prints two things to paste, and changes nothing itself:

- a **UserPromptSubmit hook** for `~/.claude/settings.json`. At every
  prompt, Claude Code runs `hook.py prompt`, which asks your folder with the
  kernel's bite and prints the passages as one framed block of data;
- the **`claude mcp add`** line that registers [mcp-lite](../mcp-lite/), so
  Claude Code can also ask on its own and hand in suggestions for you to
  approve.

| State | What Claude Code gets |
|---|---|
| your files hold the question | the passages, framed as data from your files, each with its file and line |
| they don't | nothing |
| the folder can't be read | one line saying why |

The hook always exits 0. In Claude Code a hook that exits 2 blocks the
prompt, and your folder being unreadable is no reason to stop you typing.

**Source:** [willow-bot's one script, its prompt hook](https://github.com/willow-memory/willow-bot/blob/main/one-script/scripts/prompt-hook): what was served goes into
the prompt as one framed block of data, never instructions. Rebuilt over the
kernel's bite.

**Uses:** the kernel's `main` (its own bite, so each prompt asked is on the
record).

**Never:** approves, reads your key, writes Claude Code's settings for you,
or goes online. The record keeps the prompt's fingerprint and the places it
found, never its words.
