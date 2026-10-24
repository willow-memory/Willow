"""vim.py: willow in Vim and Neovim. Python 3.9+.

    python adapters/stdlib/vim/vim.py --box DIR

Prints a :Willow command: your question goes to pipe on standard input, and its file:line: answers fill the quickfix list, each a jump. The lines go in your vimrc (~/.vimrc, or init.vim for Neovim); it changes nothing itself.
Each answer comes from pipe (adapters/stdlib/pipe/pipe.py --grep), so every
question is the kernel's own bite, on the record.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

PIPE = Path(__file__).resolve().parents[1] / "pipe" / "pipe.py"


def vim_string(text: str) -> str:
    """A Vim single-quoted string: nothing inside is special but '' for '."""
    return "'" + text.replace("'", "''") + "'"


def snippet(box: Path, py: str) -> str:
    argv = [py, str(PIPE), "--box", str(box.resolve()), "--grep"]
    words = ", ".join(vim_string(a) for a in argv)
    return (
        "function! s:Willow(question) abort\n"
        f"  let cmd = join(map([{words}], 'shellescape(v:val)'))\n"
        "  cgetexpr system(cmd, a:question)\n"
        "  copen\n"
        "endfunction\n"
        "command! -nargs=+ Willow call s:Willow(<q-args>)\n"
    )


def render(box: Path, py: str = None) -> str:
    return "Add this to your vimrc (~/.vimrc, or init.vim for Neovim):\n\n" + snippet(
        box, py or sys.executable or "python3"
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(argv[1])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    print(render(box), end="")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
