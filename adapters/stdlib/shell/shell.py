"""shell.py: a willow command and tab completion for your shell. Python 3.9+.

    python adapters/stdlib/shell/shell.py script bash|zsh|fish|powershell|cmd
    python adapters/stdlib/shell/shell.py run VERB [ARGS ...]

`script` prints a few lines for your shell to load: a `willow` command and,
for all but cmd, tab completion of the kernel's verbs. Where to put them:

    bash        python .../shell.py script bash >> ~/.bashrc
    zsh         python .../shell.py script zsh >> ~/.zshrc
    fish        python .../shell.py script fish > ~/.config/fish/conf.d/willow.fish
    powershell  python .../shell.py script powershell >> $PROFILE
    cmd         python .../shell.py script cmd > willow.cmd   (a folder on PATH)

It writes nothing itself: you choose the file. `willow VERB ...` then runs
`run`, which is the kernel's own command line, except that when WILLOW_BOX
is set and you gave no --box, it adds `--box $WILLOW_BOX`. So

    export WILLOW_BOX=~/willow-box
    willow bite "when is the dentist"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

HERE = Path(__file__).resolve()
VERBS = ("init", "bite", "propose", "seal", "verify", "out", "test")
#: every verb takes --box but test, which makes its own
NEEDS_BOX = set(VERBS) - {"test"}
SHELLS = ("bash", "zsh", "fish", "powershell", "cmd")


def script(shell: str, py: str = None) -> str:
    """The lines that give `shell` a willow command and completion."""
    py = py or sys.executable or "python3"
    run = f'"{py}" "{HERE}" run'
    verbs = " ".join(VERBS)
    if shell == "bash":
        return (f"willow() {{ {run} \"$@\"; }}\n"
                f"complete -W \"{verbs}\" willow\n")  # fmt: skip
    if shell == "zsh":
        return (f"willow() {{ {run} \"$@\"; }}\n"
                f"_willow() {{ _arguments \"1: :({verbs})\" \"*::arg:_files\"; }}\n"
                "(( $+functions[compdef] )) && compdef _willow willow\n")  # fmt: skip
    if shell == "fish":
        return (f"function willow; {run} $argv; end\n"
                f"complete -c willow -f -n __fish_use_subcommand -a \"{verbs}\"\n")  # fmt: skip
    if shell == "powershell":
        quoted = ", ".join(f"'{v}'" for v in VERBS)
        return ("function willow {\n"
                f"  param([Parameter(Position=0)][ValidateSet({quoted})][string]$Verb,\n"
                "        [Parameter(ValueFromRemainingArguments=$true)]$Rest)\n"
                f"  & '{py}' '{HERE}' run $Verb @Rest\n"
                "}\n")  # fmt: skip
    return f'@echo off\r\n"{py}" "{HERE}" run %*\r\n'  # cmd


def with_box(argv: list[str], env: dict) -> list[str]:
    """The kernel's command line, with --box $WILLOW_BOX added when it's set,
    the verb takes one and none was given."""
    box = env.get("WILLOW_BOX", "").strip()
    if box and argv and argv[0] in NEEDS_BOX and "--box" not in argv:
        return [argv[0], "--box", box, *argv[1:]]
    return argv


def main(argv: list[str], env=None) -> int:
    if len(argv) == 2 and argv[0] == "script" and argv[1] in SHELLS:
        print(script(argv[1]), end="")
        return kernel.ALIVE
    if argv[:1] == ["run"] and len(argv) > 1:
        return kernel.main(with_box(argv[1:], os.environ if env is None else env))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
