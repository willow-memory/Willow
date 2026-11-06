"""dotfiles.py: your dotfiles repository as passages, which file sets what. Python 3.9+.

    python adapters/stdlib/dotfiles/dotfiles.py mirror --from FOLDER --to MIRROR

Point it at a dotfiles repository, or a copy of the files, never at your home
folder: hidden files and folders are skipped, as by every reader here, and
~/.ssh, ~/.aws and their kind hold keys. A repository keeps its files without
the dot (`bashrc`, `gitconfig`, `config/nvim/init.vim`), or with chezmoi's
`dot_` (`dot_bashrc`), and both are read.

A file is known by its name, never by guessing at what it holds:

    shell   bashrc, bash_profile, zshrc, zshenv, zprofile, profile, aliases,
            exports, functions, and .sh, .bash, .zsh, .fish
    vim     vimrc, gvimrc, init.vim, .vim, and .lua under an nvim folder
    git     gitconfig, git/config
    set     tmux.conf, inputrc: `set -g mouse on`
    ini     .ini, .cfg, .properties, editorconfig, npmrc, pypirc, wgetrc
    conf    other .conf: `key = value` or `key value`
    toml    .toml, read with tomllib (Python 3.11 or newer; before that a
            .toml file is skipped and counted)

Each setting is written on its own line of the file, in the file's own words
with the keyword that only says "this is a setting" taken off, and every other
line is left blank, so a passage found in the mirror is on that line of the
source:

    export EDITOR="nvim"      ->  EDITOR=nvim
    alias ll='ls -la'         ->  ll=ls -la
    mkcd() {                  ->  mkcd()
    [core] editor = nvim      ->  core.editor = nvim
    set -g mouse on           ->  mouse on
    set number tabstop=4      ->  number tabstop=4

Comments, if-blocks and commands are left out: ask the file itself. A value
whose name says it is a secret (TOKEN, PASSWORD, SECRET, API_KEY and their
kind), a value shaped like a known token, and the password in a web address
are written `[withheld]`, never copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read. A file with no setting, or that cannot be read, is
skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

try:
    import tomllib
except ImportError:  # Python 3.9 and 3.10 have no TOML reader
    tomllib = None

USAGE = "usage: dotfiles.py mirror --from FOLDER --to MIRROR"
ERRORS = (OSError, UnicodeDecodeError, ValueError)
LONGEST = 200  # characters of a value shown; a longer one ends in "…"

CHEZMOI = ("private_", "executable_", "readonly_", "exact_", "empty_")
SHELL_NAMES = {"bashrc", "bash_profile", "bash_aliases", "bash_login", "profile",
               "zshrc", "zshenv", "zprofile", "zlogin", "aliases", "exports", "functions"}  # fmt: skip
VIM_NAMES = {"vimrc", "gvimrc", "exrc", "init.vim"}
INI_NAMES = {"editorconfig", "npmrc", "pypirc", "wgetrc"}
SET_NAMES = {"tmux.conf", "inputrc"}
BY_EXT = {".sh": "shell", ".bash": "shell", ".zsh": "shell", ".fish": "fish",
          ".vim": "vim", ".gitconfig": "git", ".ini": "ini", ".cfg": "ini",
          ".properties": "properties", ".conf": "conf", ".toml": "toml"}  # fmt: skip

#: a name that says its value is a secret; `_` stands for any of `-`, `.`
SECRET_NAME = re.compile(
    r"token|passw|secret|api_?key|private_?key|access_?key|credential|passphrase"
    r"|auth(?!or)|(?:^|_)key$",
    re.I,
)
#: a value shaped like a known token, whatever its name
SECRET_VALUE = re.compile(
    r"\b(?:ghp_|gho_|ghs_|github_pat_|glpat-|sk-|xox[abps]-|AKIA)[A-Za-z0-9_-]{8,}"
    r"|bearer\s+[A-Za-z0-9._~+/-]{8,}",
    re.I,
)
URL_PASSWORD = re.compile(r"(\w+://)[^/\s:@]+:[^/\s@]+@")


# ── which files ─────────────────────────────────────────────────────────────
def plain(name: str) -> str:
    """A name without chezmoi's markers: `private_dot_zshrc.tmpl` is zshrc."""
    if name.endswith(".tmpl"):
        name = name[: -len(".tmpl")]
    while name.startswith(CHEZMOI):
        name = name[name.index("_") + 1 :]
    return name[len("dot_") :] if name.startswith("dot_") else name


def kind_of(rel: PurePosixPath) -> str | None:
    """Which reader a file gets, by its name, or None: not a dotfile."""
    parts = [plain(p).lower() for p in rel.parts]
    name = parts[-1]
    if name.endswith(".local"):
        name = name[: -len(".local")]
    if name in SHELL_NAMES:
        return "shell"
    if name in VIM_NAMES:
        return "vim"
    if name == "gitconfig" or (name == "config" and parts[-2:-1] == ["git"]):
        return "git"
    if name in SET_NAMES:
        return "set"
    if name in INI_NAMES:
        return "ini"
    ext = PurePosixPath(name).suffix
    if ext == ".lua" and "nvim" in parts:
        return "lua"
    return BY_EXT.get(ext)


# ── values ──────────────────────────────────────────────────────────────────
def shown(key: str, value: str) -> str:
    """A value as written in the mirror: a secret withheld, a long one cut."""
    if SECRET_NAME.search(re.sub(r"[-.]", "_", key)) or SECRET_VALUE.search(value):
        return "[withheld]"
    if not value.strip():
        return f'"{value}"'  # empty, or a space: as it is, in quotes
    value = " ".join(URL_PASSWORD.sub(r"\1[withheld]@", value).split())
    return value if len(value) <= LONGEST else value[:LONGEST] + "…"


def sets(key: str, value: str, sep: str = "=") -> str:
    """`key=value`, the value `shown`, a password in a key's address withheld."""
    return URL_PASSWORD.sub(r"\1[withheld]@", key) + sep + shown(key, value)


def unquote(value: str) -> str:
    """A value without the quotes around it: one quoted string, not two."""
    value = value.strip()
    q = value[:1]
    if len(value) >= 2 and q in "\"'" and value[-1] == q and q not in value[1:-1]:
        return value[1:-1]
    return value


def uncomment(line: str, marks: str = "#") -> str:
    """A line without its comment: a mark at the start or after a space,
    outside quotes."""
    quote = ""
    for i, ch in enumerate(line):
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch in marks and (i == 0 or line[i - 1].isspace()):
            return line[:i].rstrip()
    return line.rstrip()


def words_of(text: str) -> list[str]:
    try:
        return shlex.split(text)
    except ValueError:  # an unclosed quote: split on spaces
        return text.split()


# ── shell ───────────────────────────────────────────────────────────────────
ASSIGN = re.compile(
    r"(?:(export|declare\s+-\w+|typeset\s+-\w+|readonly)\s+)?([A-Za-z_]\w*)(\+?=)"
)
FUNCTION = re.compile(
    r"(?:function\s+([\w:.-]+)\s*(?:\(\s*\))?|([\w:.-]+)\s*\(\s*\))\s*\{?\s*$"
)
ALIAS = re.compile(r"alias\s+(?:-\w\s+)*([^=\s]+)=(.*)")
OPTION = re.compile(
    r"(setopt|unsetopt|shopt\s+-s|shopt\s+-u|set\s+-o|set\s+\+o)\s+(.+)"
)
UNSET = ("unsetopt", "shopt -u", "set +o")


def shell_word(s: str, i: int) -> tuple[str, int]:
    """One shell word from s[i]: quotes taken off, `$(...)` and `(...)` whole."""
    out = []
    while i < len(s) and not s[i].isspace() and s[i] not in ";&|":
        ch = s[i]
        if ch in "\"'":
            j = s.find(ch, i + 1)
            while ch == '"' and j > 0 and s[j - 1] == "\\":
                j = s.find(ch, j + 1)
            j = len(s) if j < 0 else j
            out.append(s[i + 1 : j])
            i = j + 1
        elif ch == "(" or s.startswith("$(", i):
            depth, j = 0, i
            while j < len(s):
                depth += {"(": 1, ")": -1}.get(s[j], 0)
                if s[j] == ")" and depth == 0:
                    break
                j += 1
            out.append(s[i : j + 1])
            i = j + 1
        else:
            out.append(ch)
            i += 1
    return "".join(out), i


def assignments(line: str) -> list[str]:
    """`export A=1 B=2` and `A=1`, each as `A=1`; `+=` kept. None for a
    setting given to one command (`LANG=C sort`)."""
    out = []
    m = ASSIGN.match(line)
    exported = bool(m and m.group(1))
    while m:
        name, op = m.group(2), m.group(3)
        value, i = shell_word(line, m.end())
        line = line[i:].lstrip()
        if line and not line.startswith(("#", ";", "&&", "||")) and not exported:
            return []
        out.append(sets(name, value, op))
        m = ASSIGN.match(line) if exported else None
    return out


def shell_line(line: str) -> list[str]:
    m = FUNCTION.match(line)
    if m:
        return [f"{m.group(1) or m.group(2)}()"]
    m = ALIAS.match(line)
    if m:
        return [sets(m.group(1), shell_word(m.group(2), 0)[0])]
    m = OPTION.match(line)
    if m:
        no = "no " if m.group(1) in UNSET else ""
        return [no + w for w in uncomment(m.group(2)).split()]
    return assignments(line)


def fish_line(line: str) -> list[str]:
    ws = words_of(uncomment(line))
    rest = [w for w in ws[1:] if not w.startswith("-")]
    if not ws or not rest:
        return []
    if ws[0] == "function":
        return [f"{rest[0]}()"]
    if ws[0] in ("alias", "abbr"):
        if len(rest) == 1 and "=" in rest[0]:
            rest = rest[0].split("=", 1)
        return [sets(rest[0], " ".join(rest[1:]))] if len(rest) > 1 else []
    if ws[0] == "fish_add_path":
        return ["fish_add_path " + " ".join(shown("PATH", w) for w in rest)]
    if ws[0] == "set":
        return [sets(rest[0], " ".join(rest[1:]))]
    return []


# ── vim, neovim ─────────────────────────────────────────────────────────────
VIM_SET = re.compile(r"(?:set|se|setlocal|setl|setglobal|setg)\s+(.+)")
VIM_LET = re.compile(r"let\s+([\w:&@$]+)\s*([.+-]?=)\s*(.+)")
VIM_MAP = re.compile(r"[nvxsoilct]?(?:nore)?map!?\s+\S+\s+\S")
VIM_PLUG = re.compile(r"Plug(?:in)?\s+['\"]([^'\"]+)['\"]")
LUA_SET = re.compile(r"vim\.(opt|o|g|wo|bo|opt_local)\.(\w+)\s*=\s*(.+)")


def vim_line(line: str) -> list[str]:
    m = VIM_SET.match(line)
    if m:
        out = []
        for opt in uncomment(m.group(1), '"').split():
            k = re.match(r"([\w&]+)([+^-]?[=:])(.*)", opt)
            out.append(sets(k.group(1), k.group(3), k.group(2)) if k else opt)
        return [" ".join(out)]
    m = VIM_LET.match(line)
    if m:
        return [sets(m.group(1), unquote(uncomment(m.group(3), '"')), m.group(2))]
    if re.match(r"colo(?:rscheme)?\s+\S", line) or VIM_MAP.match(line):
        return [uncomment(line, '"')]  # the line is its own best words
    m = VIM_PLUG.match(line)
    return [m.group(1)] if m else []


def lua_line(line: str) -> list[str]:
    m = LUA_SET.match(line)
    if not m:
        return []
    name = ("g:" if m.group(1) == "g" else "") + m.group(2)
    value = re.sub(r"\s--.*$", "", m.group(3)).rstrip(" ,;")
    return [sets(name, unquote(value))]


# ── set-style: tmux.conf, inputrc ───────────────────────────────────────────
SET_VERBS = ("set", "set-option", "setw", "set-window-option")
TAKES_ARG = {"-t", "-T", "-N", "-p"}


def set_line(line: str) -> list[str]:
    """`set -g mouse on` as `mouse on`; a `bind` line as itself, its flags off."""
    ws = words_of(uncomment(line))
    if not ws or ws[0] not in (*SET_VERBS, "bind", "bind-key"):
        return []
    rest, i = [], 1
    while i < len(ws):
        if ws[i] in TAKES_ARG and not rest:
            i += 2
        elif ws[i].startswith("-") and len(ws[i]) > 1 and not rest:
            i += 1
        else:
            rest.append(ws[i])
            i += 1
    if not rest or (ws[0] not in SET_VERBS and len(rest) < 2):
        return []
    lead = "" if ws[0] in SET_VERBS else "bind "
    return [lead + (sets(rest[0], " ".join(rest[1:]), " ") if rest[1:] else rest[0])]


# ── key = value: git, ini, conf, properties ─────────────────────────────────
SECTION = re.compile(r"\[\s*([^\]\"]*?)\s*(?:\"(.*)\")?\s*\]$")


def ini_lines(text: str, kind: str) -> list[tuple[int, str]]:
    """`section.key = value` for each key; a git `[remote "origin"]` is
    remote.origin, and a `name = {` block (mke2fs.conf) adds its name."""
    out, section, block = [], "", []
    comments = "#;!" if kind == "properties" else "#;"
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line[0] in comments:
            continue
        m = SECTION.match(line)
        if m and kind != "properties":
            section = ".".join(x for x in (m.group(1).strip(), m.group(2)) if x)
            continue
        if line == "}" and block:
            block.pop()
            continue
        cut = line.find("=")
        if cut < 0 and kind in ("properties", "ini"):
            cut = line.find(":")
        if cut > 0:
            key, value = line[:cut].strip(), line[cut + 1 :].strip()
        elif kind in ("properties", "conf") and len(line.split(None, 1)) == 2:
            key, value = line.split(None, 1)
            key = key[:-1] if key.endswith(":") else key  # debconf's `Name: config`
        else:
            continue
        if kind in ("git", "conf"):
            value = uncomment(value, "#;")
        full = ".".join(x for x in (section, *block, key) if x)
        if value.endswith("{") and kind != "properties":
            block.append(" ".join(f"{key} {value[:-1]}".split()))
            continue
        out.append((n, sets(full, unquote(value), " = ")))
    return out


# ── toml ────────────────────────────────────────────────────────────────────
TOML_PART = re.compile(r"\s*(?:\"([^\"]*)\"|'([^']*)'|([A-Za-z0-9_-]+))\s*")
TOML_TABLE = re.compile(r"(\[\[?)(.+?)\]\]?\s*(?:#.*)?$")


def toml_key(text: str) -> tuple[str, ...] | None:
    """A dotted TOML key's parts, or None if `text` isn't one."""
    parts, i = [], 0
    while True:
        m = TOML_PART.match(text, i)
        if not m:
            return None
        parts.append(next(g for g in m.groups() if g is not None))
        i = m.end()
        if i == len(text):
            return tuple(parts)
        if text[i] != ".":
            return None
        i += 1


def toml_lines_of(text: str) -> dict[tuple, int]:
    """Where each table and key starts, by its path: [[arrays]] counted from 1."""
    where: dict[tuple, int] = {}
    counts: dict[tuple, int] = {}
    table: tuple = ()
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        m = TOML_TABLE.match(line)
        key = toml_key(m.group(2)) if m else None
        if key is not None:
            if m.group(1) == "[[":
                counts[key] = counts.get(key, 0) + 1
                key = (*key, str(counts[key]))
            table = key
            where.setdefault(table, n)
        elif "=" in line:
            key = toml_key(line.split("=", 1)[0])
            if key is not None:
                where.setdefault((*table, *key), n)
    return where


def scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def flat(value, path: tuple = ()):
    """(path, text) for each leaf: a list of plain values is one leaf."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from flat(v, (*path, k))
    elif isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
        for i, v in enumerate(value, 1):
            yield from flat(v, (*path, str(i)))
    elif isinstance(value, list):
        yield path, ", ".join(scalar(v) for v in value) if value else "[]"
    else:
        yield path, scalar(value)


def toml_settings(text: str) -> list[tuple[int, str]]:
    where = toml_lines_of(text)
    out = []
    for path, value in flat(tomllib.loads(text)):
        at = [where[path[:i]] for i in range(len(path), 0, -1) if path[:i] in where]
        out.append((at[0] if at else 1, sets(".".join(path), value, " = ")))
    return out


# ── a file ──────────────────────────────────────────────────────────────────
BY_LINE = {"shell": shell_line, "fish": fish_line, "vim": vim_line,
           "lua": lua_line, "set": set_line}  # fmt: skip
LEAD = {"vim": '"', "lua": "--"}  # a comment line, by kind; else "#"


def settings(kind: str, text: str) -> list[tuple[int, str]]:
    """(line, the setting in the file's words) for each one in a file."""
    if kind == "toml":
        return toml_settings(text)
    if kind not in BY_LINE:
        return ini_lines(text, kind)
    out = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line and not line.startswith(LEAD.get(kind, "#")):
            out.extend((n, said) for said in BY_LINE[kind](line))
    return out


def convert(rel: PurePosixPath, data: bytes) -> str | None:
    """The mirror of one file, line for line, or None: not a dotfile, TOML
    with no reader for it, or no setting in it."""
    kind = kind_of(rel)
    if kind is None or (kind == "toml" and tomllib is None):
        return None
    found = settings(kind, data.decode("utf-8-sig"))
    if not found:
        return None
    lines = [""] * max(n for n, _ in found)
    for n, said in found:
        lines[n - 1] = f"{lines[n - 1]} {said}".strip()
    return "\n".join(lines) + "\n"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            rel = PurePosixPath(p.relative_to(folder).as_posix())
            if not name.startswith(".") and kind_of(rel) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def places(text: str) -> dict[str, str]:
    """The mirror contract's places (adapters/stdlib/ci/README.md): the
    mirror is line for line, so the line each passage starts on is the
    source's same line."""
    lines = text.splitlines()
    return {str(i): f"line {i}" for i, s in enumerate(lines, 1)
            if s.strip() and (i == 1 or not lines[i - 2].strip())}  # fmt: skip


def write_places(dst: Path, rel: str, found: dict[str, str]) -> None:
    """The map, hidden beside the mirror, where the kernel never reads."""
    out = dst / ".places" / (rel + ".txt.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = {"source": rel, "places": found}
    out.write_bytes((json.dumps(doc, ensure_ascii=False) + "\n").encode("utf-8"))


# differs on purpose: convert needs the dotfile's path, for its kind
def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(PurePosixPath(rel.as_posix()), path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
            write_places(dst, rel.as_posix(), places(text))
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    toml = sum(kind_of(PurePosixPath(p.name)) == "toml" for p in _sources(src))
    if toml and tomllib is None:
        print(f"skipped {toml} .toml: reading TOML needs Python 3.11 or newer",
              file=sys.stderr)  # fmt: skip
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
