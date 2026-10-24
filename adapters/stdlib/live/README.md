<!-- willow-addon
section: For maintainers
line: Each way-in add-on run through the real program it's for, a shell, an editor or an AI tool: works, fails, or not here.
source: new
added: 2026-10-24
writes: nothing
network: only what the programs it starts reach on their own; it reaches nothing itself
tags: no-install, maintainers, tests, interface, assistant
-->
# live

The other add-ons' tests check that what they print parses as the format they
name. That doesn't prove the program reads it. This runs the program.

    python adapters/stdlib/live/live.py run [CHECK ...]
    python adapters/stdlib/live/live.py list

Each check makes a box in a scratch folder, under a folder with a space in
its name (quoting breaks there). It hands the program the lines its add-on
prints, then reads back what the program did. Each program gets a home folder
inside the scratch folder, so nothing of yours is read or changed.

| Check | Runs | Holds |
|---|---|---|
| bash, zsh, fish, powershell | the [shell](../shell/) lines | `willow bite` answers; Tab turns `willow se` into `seal` (zsh through a real terminal) |
| vim, nvim | the [vim](../vim/) lines | the quickfix list holds each answer at its own file and line |
| emacs | the [emacs](../emacs/) lines | each answer jumps to its own file and line |
| vscode | the [vscode](../vscode/) problem matcher, in Node | JavaScript reads each line's file and line right, even a passage that quotes a `name:4:` of its own |
| codex | [codex-cli](../codex-cli/)'s config.toml | `codex mcp get willow` names mcp-lite over the box |
| gemini | [gemini-cli](../gemini-cli/)'s settings.json | `gemini mcp list` says Connected |
| opencode | [opencode](../opencode/)'s opencode.json | `opencode mcp list` says connected |
| copilot | [copilot](../copilot/)'s Copilot CLI file | `copilot mcp list` names willow (local) |
| claude | [claude-code](../claude-code/)'s hook and add line | the hook serves passages through `sh`; `claude mcp list` says Connected |
| mcp | [mcp-lite](../mcp-lite/), through MCP Inspector's CLI | ask answers; suggest waits; waiting lists it; a bad suggest is a tool error |
| chrome | a page saved by headless Chrome over its DevTools pipe, as .mhtml (its own snapshot) and as drawn (.html), read by [web-pages](../web-pages/) | each is read under its address, with the paragraph only the page's script wrote |

Each check gives one of three states, kept apart:

- **works:** the program read the lines and did the thing.
- **fails:** the program ran but didn't, and the line says why.
- **not here:** the program isn't on this machine. That's neither a pass nor a failure.

The exit code is the worst of these: 0 everything works; 42 something
isn't here and nothing fails; 2 something fails, or the command line was bad.

In CI the `tools` job installs every program at a pinned version and runs
each check as a gate (`tools:bash`, `tools:zsh`, …). A program that didn't
install is unreachable, which fails the job, so a missing program can't
pass as green.

**What it can't check:** Cursor, Windsurf, Zed, JetBrains IDEs, VS Code's
own MCP file, Aider's chat and Windows' cmd. Each needs a desktop
or an account, and has no headless way to ask whether it read a file. Those
add-ons are held to their formats by their own tests and nothing more.

**What it found the first time it ran:** VS Code's matcher read a passage
quoting `old.txt:4:` as that file and line. Claude Code's hook, its
`claude mcp add` line, Aider's run line and JetBrains' parameters split
a folder with a space in its name into two words. Gemini starts no server
in a folder its person hasn't trusted. Each is fixed or said on its card,
and has a test. The chrome check, its first time, found web-pages reading
Chrome's own .mhtml wrongly: Chrome names no charset on the page's part, so
its curly quotes came out garbled; web-pages now reads the page's own.

**Uses:** the kernel's `init` for the scratch box and its exit codes; each
add-on's own functions for the lines it prints.

**Never:** runs a program with your home folder, or writes outside its
scratch folder.
