<!-- willow-addon
section: Reading more kinds of files
line: Your dotfiles as passages: which file sets what, for 'where did I set my editor?'
source: new
added: 2026-11-02
writes: to
network: none
role: reads
output: mirror
reads: .bash, .cfg, .conf, .fish, .gitconfig, .ini, .lua, .properties, .sh, .toml, .vim, .zsh
-->
# dotfiles

Your dotfiles repository as passages: each setting on the line it's on in its
file, in the file's own words, so "where did I set my editor" finds
`EDITOR=nvim` in bashrc and `core.editor = nvim` in gitconfig.

    python adapters/stdlib/dotfiles/dotfiles.py mirror --from FOLDER --to MIRROR

**Point it at a dotfiles repository or a copy, not your home folder.** Hidden
files and folders are never read, by this reader or any other here, and your
home folder's hidden ones include ~/.ssh, ~/.aws and others that hold keys.
A repository keeps its files without the dot (`bashrc`, `config/nvim/<init.vim>`)
or with chezmoi's `dot_` (`dot_bashrc`, `private_dot_zshrc.tmpl`), and both
are read. A repository that keeps the dot (GNU stow's `bash/<.bashrc>`) is
skipped: copy the files in without it, `cp ~/.gitconfig FOLDER/gitconfig`.

A file is known by its name, never by guessing at what it holds:

| Kind | Files | In the mirror |
|---|---|---|
| shell | bashrc, bash_profile, bash_aliases, zshrc, zshenv, zprofile, profile, aliases, exports, functions; .sh, .bash, .zsh, .fish | `export EDITOR="nvim"` is `EDITOR=nvim`; `alias ll='ls -la'` is `ll=ls -la`; `mkcd() {` is `mkcd()`; `setopt AUTO_CD` is `AUTO_CD`, `unsetopt BEEP` is `no BEEP`; fish's `set -gx EDITOR nvim` is `EDITOR=nvim` |
| vim | vimrc, gvimrc, init.vim, .vim; .lua under an nvim folder | `set number tabstop=4` is `number tabstop=4`; `let mapleader = ","` is `mapleader=,`; a colorscheme or map line as written; `Plug 'tpope/vim-fugitive'` is the plugin's name; `vim.opt.number = true` is `number=true` |
| git | gitconfig, git/config | `[core] editor = nvim` is `core.editor = nvim`; `[remote "origin"]` is remote.origin |
| set | tmux.conf, inputrc | `set -g mouse on` is `mouse on`; a bind line keeps `bind` and its key, its flags off |
| ini | .ini, .cfg, .properties, editorconfig, npmrc, pypirc, wgetrc | `section.key = value` |
| conf | any other .conf | `key = value`, from `key = value`, `key value` (kitty) or `Key: value`; a `name = {` block adds its name |
| toml | .toml | every value by its dotted path, `character.success_symbol = [➜](bold green)` |

Every other line is left blank, so the mirror has the source's line numbers
and a passage found in it is at that line of the file. Settings on lines next
to each other are one passage, cited by its first line, as they sit together
in the file. Comments, if-blocks, commands and `source` lines are left out:
ask the file itself for those. The vim add-on is about asking willow from
inside Vim, not reading a vimrc, so vimrc is read here.

**Only the file's words, no labels of its own.** Nothing is written beside a
setting (no "sets", "line" or file name: the mirror's path names the file),
so a word the reader added can't make a question about something you don't
have land on every passage. The cost: `alias` and `export` are gone, so
"where did I alias ll" finds `ll=ls -alF` by `ll`, alongside gitconfig's
aliases. A key the source repeats is kept: in a short editorconfig, `indent`
and `style` are in most passages, which "what is my indent size" needs.

**Secrets are withheld.** A value whose name says it's a secret (TOKEN,
PASSWORD, SECRET, API_KEY, AUTH, a name ending in KEY), a value shaped like a
known token (`ghp_`, `sk-`, `xoxb-`, `AKIA`, a bearer token), and the password
in a web address (`https://ana:<password>@host`) are written `[withheld]`,
never copied. It errs on the side of withholding: git's
`http.proxyAuthMethod` is withheld too.

**TOML needs Python 3.11 or newer**, whose tomllib reads it. On 3.9 and
3.10 a .toml file is skipped and counted, and the run says how many on its
error output.

A value is cut at 200 characters, ending in "…". Each file is written to
MIRROR at the same relative path with .txt added. FOLDER is only read: hidden
folders and files are skipped, and nothing is written inside it. A file with
no setting in it, or that can't be read, is skipped and counted, never a
crash:

    wrote 6 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the formats (tomllib for TOML, shlex for a shell line).

**Never:** copies a secret it recognises, writes inside FOLDER, modifies an
original, writes anything outside MIRROR, or goes online.
