<!-- willow-addon
section: Assistants
line: Claude Code sees cited passages from your folder with each prompt, through its prompt hook.
source: bot
added: 2026-10-24
version: 0.3.0
writes: record
network: none
hands: the passages served for each prompt, to Claude Code's model
role: ways
uses: mcp-lite
looks-for: batch-ask, index-cache
-->
# claude-code

The **prompt-hook** way in (see [hosts](../hosts/)): Claude Code reads what
your own files say about each prompt, before it answers, with each passage's
file and line. MCP tools are the other way; `setup` prints both.

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

**A big folder:** the kernel reads every file at every prompt, so on tens
of thousands of files a prompt waits half a minute. Name
[batch-ask](../batch-ask/)'s index of the folder and the hook answers from it, in a
few seconds, with the same passages and the same row on the record:

    python adapters/stdlib/claude-code/hook.py setup --box DIR --index INDEX

prints the hook with `--index`, and the [index-cache](../index-cache/) line
that keeps the index current: run it now, and when your folder changes. An
index that isn't current (index-cache's manifest says a file moved) is never
asked; the kernel reads the folder, as without one. A box laid from several
places (`init --from`) is indexed whole, its pile and every source, by
`index-cache --box`, and answered from that index the same way.

**The same bite, for another program:**

    python adapters/stdlib/claude-code/hook.py bite --box DIR [--index INDEX [--keep]] "question"

prints what `kernel.py bite` prints, the same JSON and the same exit code
(0 an answer, 42 none, 2 refused), and puts the same row on the record:
from the index while it is current, else by the kernel reading the folder. With
`--keep`, the index is brought current first, in the same program
(index-cache's own check, a rebuild only when a file the box reads moved),
so a caller asks once where it ran index-cache and then this.
Only the kernel's `look` hints, printed for a person, aren't given from an
index.

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
