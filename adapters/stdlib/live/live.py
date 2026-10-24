"""live.py: each way-in add-on run through the real program it's for. Python 3.9+.

    python adapters/stdlib/live/live.py run [CHECK ...]
    python adapters/stdlib/live/live.py list

The other add-ons' own tests check the lines they print parse as the format
they name. That says nothing about whether the program reads them. This
runs the program: it makes a box in a scratch folder (under a folder with a
space in its name, which is where quoting breaks), hands each program the
lines its add-on prints, and reads back what the program did.

    works     the program read the lines and did the thing
    fails     it ran and didn't, and why
    not here  the program isn't on this machine: not a pass, not a failure

One line a check. `run` with no CHECK runs every one. What each check runs is in
CHECKS below; `list` prints them. Each program it starts is given a home
folder inside the scratch folder, so nothing of yours is read or changed.

Exit codes, the kernel's: 0 every check works; 42 one isn't here and none
fails; 2 one fails, or a bad command line.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STDLIB = ROOT / "adapters" / "stdlib"
WORKS, FAILS, ABSENT = "works", "fails", "not here"
#: how long one program gets before it counts as failing
TIMEOUT = 120
QUESTION = "when is the dentist"
NOTES = {
    "dentist.txt": "The dentist is on Tuesday at 3pm.\nBring the insurance card.\n",
    # a passage quoting a file:line of its own, which a greedy matcher misreads
    "moved.txt": "Moved from old.txt:4: to here, the dentist\n",
}


def addon(folder: str, module: str):
    """An add-on's module, compiled from its source as it is now: never a
    cached build, which can outlive an edit made within the same second."""
    path = STDLIB / folder / f"{module}.py"
    mod = types.ModuleType(f"live_{module}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


class Place:
    """The scratch folder one check runs in: a box over NOTES, a home folder
    for the program, and the environment that points the program there."""

    def __init__(self, tmp: Path):
        self.root = tmp / "with space"
        self.home = self.root / "home"
        notes = self.root / "notes"
        for d in (self.home, notes):
            d.mkdir(parents=True)
        for name, text in NOTES.items():
            (notes / name).write_text(text, encoding="utf-8")
        self.notes = notes.resolve()
        self.box = self.root / "box"
        made = subprocess.run(
            [sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(self.box),
             "--pile", str(notes), "--key", str(self.root / "box.key")],
            capture_output=True, text=True,
        )  # fmt: skip
        if made.returncode != 0:
            raise RuntimeError(f"couldn't make the box: {made.stderr.strip()}")
        self.env = {**os.environ, "HOME": str(self.home), "USERPROFILE": str(self.home),
                    "XDG_CONFIG_HOME": str(self.home / ".config"),
                    "XDG_DATA_HOME": str(self.home / ".local" / "share"),
                    "WILLOW_BOX": str(self.box), "NO_COLOR": "1"}  # fmt: skip

    def put(self, rel: str, text: str) -> Path:
        path = self.home / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run(
        self, argv: list[str], stdin: str = "", cwd: Path = None, env: dict = None
    ) -> str:
        got = subprocess.run(
            argv, input=stdin, cwd=str(cwd or self.home), env={**self.env, **(env or {})},
            capture_output=True, text=True, timeout=TIMEOUT,
        )  # fmt: skip
        return got.stdout + got.stderr

    def expect(self, name: str = "dentist.txt", line: int = 1) -> str:
        return f"{self.notes / name}:{line}"


def config(folder: str, module: str, place: Place, index: int = 0) -> str:
    """The text an AI-tool add-on prints for its `index`th place."""
    _, kind, value = addon(folder, module).places(place.box, sys.executable)[index]
    return value if kind == "toml" else json.dumps(value, indent=2)


def has(said: str, *words: str) -> str | None:
    """None when every word is in what the program said, else why not."""
    gone = [w for w in words if w not in said]
    tail = " ".join(said.split())[-200:]
    return f"didn't say {gone[0]!r}: {tail}" if gone else None


def lines(said: str, *wanted: str) -> str | None:
    """None when each wanted is a whole line of what the program said: a
    file and line misread as a longer one still holds the right text."""
    got = set(said.splitlines())
    gone = [w for w in wanted if w not in got]
    tail = " ".join(said.split())[-200:]
    return f"no line {gone[0]!r}: {tail}" if gone else None


def bite_works(said: str) -> str | None:
    return has(said, '"state": "populated"', "dentist.txt")


# ── the checks: each returns None when it works, else why not ───────────────
def sh_line(shell: str, place: Place) -> str:
    return addon("shell", "shell").script(shell, sys.executable)


def check_bash(place: Place) -> str | None:
    rc = place.put(".willow.bash", sh_line("bash", place))
    said = place.run(["bash", "-c", f"source {shlex.quote(str(rc))}; "
                      f"willow bite {shlex.quote(QUESTION)}; echo; "
                      "eval \"$(complete -p willow | sed 's/^complete/compgen/; s/ willow$//')\" -- se"])  # fmt: skip
    return bite_works(said) or has(said, "\nseal")


ZPTY = """zmodload zsh/zpty
zpty z zsh -fi
zpty -w z "PS1='>'; autoload -Uz compinit; compinit -u; source %s"
sleep 1; while zpty -r -t z junk; do :; done
zpty -w -n z "willow se"$'\\t'
sleep 2
all=; while zpty -r -t z out; do all+=$out; done
print -r -- "$all"
zpty -d z
"""


def check_zsh(place: Place) -> str | None:
    rc = place.put(".willow.zsh", sh_line("zsh", place))
    said = place.run(
        [
            "zsh",
            "-fc",
            f"source {shlex.quote(str(rc))}; willow bite {shlex.quote(QUESTION)}",
        ]
    )
    driver = place.put("complete.zsh", ZPTY % shlex.quote(str(rc)))
    typed = place.run(["zsh", "-f", str(driver)])
    return bite_works(said) or has(typed, "willow seal")


def check_fish(place: Place) -> str | None:
    rc = place.put(".willow.fish", sh_line("fish", place))
    said = place.run(["fish", "-c", f"source {shlex.quote(str(rc))}; willow bite {shlex.quote(QUESTION)}; "
                      "complete -C 'willow se'"])  # fmt: skip
    return bite_works(said) or has(said, "\nseal")


def check_pwsh(place: Place) -> str | None:
    rc = place.put("willow.ps1", sh_line("powershell", place))
    quoted = "'" + str(rc).replace("'", "''") + "'"
    said = place.run(["pwsh", "-NoProfile", "-NonInteractive", "-Command",
                      f". {quoted}; willow bite '{QUESTION}' | Out-String; "
                      "(TabExpansion2 -inputScript 'willow se' -cursorColumn 9)"
                      ".CompletionMatches.CompletionText"])  # fmt: skip
    return bite_works(said) or has(said, "seal")


VIM = ("source {rc}\nWillow {q}\n"
       "call writefile(map(getqflist(), 'fnamemodify(bufname(v:val.bufnr), \":p\").\":\".v:val.lnum'), {out})\n"
       "qa!\n")  # fmt: skip


def vim_like(exe: str, place: Place) -> str | None:
    rc = place.put("willow.vim", addon("vim", "vim").snippet(place.box, sys.executable))
    out = place.home / "qf.txt"
    vs = addon("vim", "vim").vim_string
    script = place.put(
        "run.vim",
        VIM.format(rc=str(rc).replace(" ", "\\ "), q=QUESTION, out=vs(str(out))),
    )
    said = place.run([exe, "-Nu", "NONE", "-i", "NONE", "-es", "-S", str(script)])
    got = out.read_text(encoding="utf-8") if out.exists() else ""
    return lines(got + "\n" + said, place.expect(), place.expect("moved.txt"))


def check_vim(place: Place) -> str | None:
    return vim_like("vim", place)


def check_nvim(place: Place) -> str | None:
    return vim_like("nvim", place)


EMACS = """(progn
  (load-file {el})
  (willow "{q}")
  (dolist (n '(0 1))
    (with-current-buffer "*willow*" (goto-char (point-min)) (forward-line n) (compile-goto-error))
    (with-current-buffer (window-buffer (selected-window))
      (princ (format "%s:%d\\n" (buffer-file-name) (line-number-at-pos))))))"""


def check_emacs(place: Place) -> str | None:
    text = addon("emacs", "emacs").snippet(place.box, sys.executable)
    el = place.put("willow.el", text)
    form = EMACS.format(el=json.dumps(str(el)), q=QUESTION)
    said = place.run(["emacs", "-Q", "--batch", "--eval", form])
    return lines(said, place.expect(), place.expect("moved.txt"))


def check_vscode(place: Place) -> str | None:
    """VS Code reads its problemMatcher with JavaScript's regular expressions;
    this runs the add-on's pattern in Node over what pipe prints, and each
    match must name a real file and line. VS Code itself has no headless run."""
    regexp = json.loads(addon("vscode", "vscode").snippet(place.box, sys.executable))
    regexp = regexp["tasks"][0]["problemMatcher"]["pattern"]["regexp"]
    grep = place.run([sys.executable, str(STDLIB / "pipe" / "pipe.py"), "--box",
                      str(place.box), "--grep", "dentist"])  # fmt: skip
    js = ("const re=new RegExp(process.argv[1]);"
          "for (const l of require('fs').readFileSync(0,'utf8').split('\\n').filter(Boolean))"
          "{const m=l.match(re); console.log(m ? m[1]+':'+m[2] : 'NO MATCH '+l)}")  # fmt: skip
    said = place.run(["node", "-e", js, regexp], stdin=grep)
    return lines(said, place.expect(), place.expect("moved.txt")) or (
        f"a line didn't match: {said}" if "NO MATCH" in said else None
    )


def check_codex(place: Place) -> str | None:
    home = place.home / ".codex"
    place.put(".codex/config.toml", config("codex-cli", "codex_cli", place))
    said = place.run(["codex", "mcp", "get", "willow"], env={"CODEX_HOME": str(home)})
    return has(said, "mcp-lite/server.py", str(place.box.resolve()), "enabled: true")


def check_gemini(place: Place) -> str | None:
    place.put(".gemini/settings.json", config("gemini-cli", "gemini_cli", place))
    # Gemini starts no server in a folder its person hasn't trusted
    place.put(
        ".gemini/trustedFolders.json", json.dumps({str(place.home): "TRUST_FOLDER"})
    )
    said = place.run(["gemini", "mcp", "list"])
    return has(said, "willow", "Connected")


def check_opencode(place: Place) -> str | None:
    project = place.home / "project"
    project.mkdir()
    (project / "opencode.json").write_text(
        config("opencode", "opencode", place), encoding="utf-8"
    )
    said = place.run(["opencode", "mcp", "list"], cwd=project)
    return has(said, "willow", "connected")


def check_copilot(place: Place) -> str | None:
    """Copilot CLI's piece; the VS Code piece needs VS Code. `mcp list` reads
    the file without starting the server."""
    place.put(".copilot/mcp-config.json", config("copilot", "copilot", place, 1))
    said = place.run(["copilot", "mcp", "list"])
    return has(said, "willow (local)")


def check_claude(place: Place) -> str | None:
    hook = addon("claude-code", "hook")
    text = hook.setup(place.box)
    settings = json.loads(text.split("\n\n")[1])
    command = settings["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    said = place.run(["sh", "-c", command], stdin=json.dumps({"prompt": QUESTION}))
    why = has(said, "<willow-passages>", "dentist.txt:1")
    if why:
        return f"the hook: {why}"
    project = place.home / "project"
    project.mkdir()
    add = text.split("    claude mcp add", 1)[1].splitlines()[0]
    place.run(["sh", "-c", "claude mcp add" + add], cwd=project)
    said = place.run(["claude", "mcp", "list"], cwd=project)
    return has(said, "willow", "Connected")


def inspect(place: Place, *call: str) -> str:
    server = [
        sys.executable,
        str(STDLIB / "mcp-lite" / "server.py"),
        "--box",
        str(place.box),
    ]
    return place.run(
        ["mcp-inspector", "--cli", *server, "--method", "tools/call", *call]
    )


def check_mcp(place: Place) -> str | None:
    """Every tool called through the protocol's own reference client."""
    asked = inspect(place, "--tool-name", "ask", "--tool-arg", f"question={QUESTION}")
    why = has(asked, '"state": "populated"', '"isError": false')
    if why:
        return f"ask: {why}"
    cite = json.loads(asked[asked.index("{") :])["structuredContent"]["served"][0]["id"]
    handed = inspect(place, "--tool-name", "suggest", "--tool-arg", "path=dentist.md",
                     "--tool-arg", "answer=Tuesday at 3pm", "--tool-arg", f'cites=["{cite}"]',
                     "--tool-arg", "reason=the note says so")  # fmt: skip
    why = has(handed, '"waiting": "proposal:')
    if why:
        return f"suggest: {why}"
    waiting = inspect(place, "--tool-name", "waiting")
    proposal = handed.split('"waiting": "', 1)[1].split('"', 1)[0]
    why = has(waiting, proposal)
    if why:
        return f"waiting: {why}"
    refused = inspect(place, "--tool-name", "suggest", "--tool-arg", "path=../out",
                      "--tool-arg", "answer=x", "--tool-arg", 'cites=["x"]',
                      "--tool-arg", "reason=x")  # fmt: skip
    why = has(refused, '"isError": true')
    return f"a refused suggest: {why}" if why else None


#: name: (what the check runs, the program it needs, the check)
CHECKS = {
    "bash": ("shell: the willow command and its completion", "bash", check_bash),
    "zsh": ("shell: the willow command and Tab completing it", "zsh", check_zsh),
    "fish": ("shell: the willow command and its completion", "fish", check_fish),
    "powershell": ("shell: the willow command and Tab completing it", "pwsh", check_pwsh),
    "vim": ("vim: the quickfix list, each answer at its file and line", "vim", check_vim),
    "nvim": ("vim's lines in Neovim: the quickfix list", "nvim", check_nvim),
    "emacs": ("emacs: each answer jumps to its file and line", "emacs", check_emacs),
    "vscode": ("vscode: its problem matcher, in JavaScript's regular expressions", "node", check_vscode),
    "codex": ("codex-cli: Codex reads the server from config.toml", "codex", check_codex),
    "gemini": ("gemini-cli: Gemini connects to the server", "gemini", check_gemini),
    "opencode": ("opencode: opencode connects to the server", "opencode", check_opencode),
    "copilot": ("copilot: Copilot CLI reads the server", "copilot", check_copilot),
    "claude": ("claude-code: the hook serves passages; Claude Code connects", "claude", check_claude),
    "mcp": ("mcp-lite: ask, suggest, waiting and a refusal, through MCP Inspector", "mcp-inspector", check_mcp),
}  # fmt: skip


def one(name: str) -> tuple[str, str]:
    """(state, why) for one check, in a scratch folder of its own."""
    _, needs, check = CHECKS[name]
    if shutil.which(needs) is None:
        return ABSENT, f"{needs} not on PATH"
    with tempfile.TemporaryDirectory() as tmp:
        try:
            why = check(Place(Path(tmp)))
        except subprocess.TimeoutExpired:
            return FAILS, f"{needs} took more than {TIMEOUT}s"
        except (OSError, RuntimeError, ValueError, KeyError, IndexError) as exc:
            return FAILS, f"{type(exc).__name__}: {exc}"[:300]
    return (FAILS, why) if why else (WORKS, "")


def code_of(states: list[str]) -> int:
    if FAILS in states:
        return kernel.REFUSED
    return kernel.ESCALATE if ABSENT in states else kernel.ALIVE


def main(argv: list[str]) -> int:
    if argv == ["list"]:
        for name, (what, needs, _) in CHECKS.items():
            print(f"{name:<11} needs {needs:<14} {what}")
        return kernel.ALIVE
    if argv[:1] != ["run"]:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    names = argv[1:] or list(CHECKS)
    unknown = [n for n in names if n not in CHECKS]
    if unknown:
        print(
            f"refused: no check {unknown[0]!r}; `live.py list` names them",
            file=sys.stderr,
        )
        return kernel.REFUSED
    states = []
    for name in names:
        state, why = one(name)
        states.append(state)
        print(f"{state:<9} {name:<11} {why}".rstrip(), flush=True)
    return code_of(states)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
