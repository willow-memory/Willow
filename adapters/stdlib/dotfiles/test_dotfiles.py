"""dotfiles: a dotfiles repository's settings, each on its own line in the
file's own words; secrets withheld; hidden files and folders skipped, an
unreadable file skipped and counted, the same bytes twice, originals
unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "dotfiles.py"
spec = importlib.util.spec_from_file_location("dotfiles", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

BASHRC = """# ~/.bashrc
case $- in
    *i*) ;;
esac
HISTSIZE=10000
shopt -s histappend
export EDITOR="nvim"
export PATH="$HOME/go/bin:$PATH"
export GITHUB_TOKEN="ghp_abcdefghijklmnopqrstuvwxyz0123"
alias ll='ls -alF'
alias gs='git status'
mkcd() {
    mkdir -p "$1" && cd "$1"
}
LANG=C sort names.txt
eval "$(starship init bash)"
"""
GITCONFIG = """[user]
\tname = Ana Lopez
\temail = ana@example.org
[core]
\teditor = nvim   # the one I use
[alias]
\tco = checkout
[remote "origin"]
\turl = https://ana:hunter2@git.example.org/ana/dotfiles.git
"""
TMUX = """# prefix
unbind C-b
set -g prefix C-a
set -g mouse on
setw -g mode-keys vi
bind r source-file ~/.tmux.conf
bind -T copy-mode-vi v send -X begin-selection
run '~/.tmux/plugins/tpm/tpm'
"""
STARSHIP = """# prompt
add_newline = false

[character]
success_symbol = "[>](bold green)"

[[profiles]]
name = "work"
"""
REPO = {
    "bashrc": BASHRC,
    "gitconfig": GITCONFIG,
    "tmux.conf": TMUX,
    "config/nvim/init.vim": '" basics\nset number tabstop=4\nlet mapleader = ","\n'
    "colorscheme gruvbox\nnnoremap <leader>w :w<CR>\nPlug 'tpope/vim-fugitive'\n",
    "config/fish/config.fish": "set -gx PAGER less\nabbr -a gco git checkout\n"
    "fish_add_path ~/.cargo/bin\nfunction mkcd\nend\n",
    "config/kitty/kitty.conf": "font_family JetBrains Mono\nfont_size 12.0\n",
}


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def write(folder: Path, files: dict[str, str | bytes]) -> Path:
    for rel, data in files.items():
        p = folder / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data.encode() if isinstance(data, str) else data)
    return folder


def mirror_of(tmp_path: Path, files: dict) -> tuple[subprocess.CompletedProcess, Path]:
    src = write(tmp_path / "src", files)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def lines(name: str, text: str) -> dict[int, str]:
    """The mirror's settings by line number."""
    out = mod.convert(PurePosixPath(name), text.encode())
    return {n: x for n, x in enumerate(out.split("\n"), 1) if x}


def test_a_shell_rc_gives_each_setting_in_its_own_words_on_its_own_line():
    got = lines("bashrc", BASHRC)
    assert got == {
        5: "HISTSIZE=10000",
        6: "histappend",
        7: "EDITOR=nvim",
        8: "PATH=$HOME/go/bin:$PATH",
        9: "GITHUB_TOKEN=[withheld]",
        10: "ll=ls -alF",
        11: "gs=git status",
        12: "mkcd()",
    }, "comments, case blocks, eval and a one-command LANG=C are left out"
    out = mod.convert(PurePosixPath("bashrc"), BASHRC.encode())
    assert len(out.split("\n")) <= len(BASHRC.split("\n")), "never more lines"


def test_zsh_options_arrays_and_several_exports_on_one_line():
    got = lines("zshrc", "setopt AUTO_CD\nunsetopt BEEP\npath+=($HOME/bin)\n"
                "export A=1 B='two words'  # both\nfunction gco {\n")  # fmt: skip
    assert got == {1: "AUTO_CD", 2: "no BEEP", 3: "path+=($HOME/bin)",
                   4: "A=1 B=two words", 5: "gco()"}  # fmt: skip


def test_git_config_keys_carry_their_section_and_subsection():
    got = lines("gitconfig", GITCONFIG)
    assert got[3] == "user.email = ana@example.org"
    assert got[5] == "core.editor = nvim", "an inline comment is not the value"
    assert got[7] == "alias.co = checkout"
    assert (
        got[9]
        == "remote.origin.url = https://[withheld]@git.example.org/ana/dotfiles.git"
    )
    assert 1 not in got and 4 not in got, "a section line is not a setting"


def test_tmux_set_lines_lose_the_set_and_bind_lines_keep_the_key():
    got = lines("tmux.conf", TMUX)
    assert got == {3: "prefix C-a", 4: "mouse on", 5: "mode-keys vi",
                   6: "bind r source-file ~/.tmux.conf",
                   7: "bind v send -X begin-selection"}  # fmt: skip
    assert lines("inputrc", "set editing-mode vi\n") == {1: "editing-mode vi"}


def test_vim_and_neovim_options_variables_maps_and_plugins():
    got = lines("config/nvim/init.vim", REPO["config/nvim/init.vim"])
    assert got == {2: "number tabstop=4", 3: "mapleader=,", 4: "colorscheme gruvbox",
                   5: "nnoremap <leader>w :w<CR>", 6: "tpope/vim-fugitive"}  # fmt: skip
    lua = 'vim.opt.number = true\nvim.g.mapleader = " "  -- space\nlocal x = 1\n'
    assert lines("config/nvim/lua/options.lua", lua) == {
        1: "number=true",
        2: 'g:mapleader=" "',
    }, "a value of one space is shown as a space, in quotes"
    assert mod.kind_of(PurePosixPath("scripts/build.lua")) is None, "lua only for nvim"


def test_fish_set_abbr_paths_and_functions():
    got = lines("config/fish/config.fish", REPO["config/fish/config.fish"])
    assert got == {1: "PAGER=less", 2: "gco=git checkout",
                   3: "fish_add_path ~/.cargo/bin", 4: "mkcd()"}  # fmt: skip


def test_ini_conf_and_properties_files():
    ini = "[server]\nport = 8080\nhost: example.org\n"
    assert lines("app.ini", ini) == {
        2: "server.port = 8080",
        3: "server.host = example.org",
    }
    conf = "font_size 12.0\nName: config\n[fs_types]\next4 = {\n  features = has_journal\n}\nblocksize = 4096\n"
    assert lines("x.conf", conf) == {1: "font_size = 12.0", 2: "Name = config",
                                     5: "fs_types.ext4.features = has_journal",
                                     7: "fs_types.blocksize = 4096"}  # fmt: skip
    props = "! a comment\napp.name=Willow\napp.title: Memory\napp.color blue\n"
    assert lines("app.properties", props) == {
        2: "app.name = Willow",
        3: "app.title = Memory",
        4: "app.color = blue",
    }
    assert lines("x.conf", 'chip "lm78-*" "lm79-*"\n') == {
        1: 'chip = "lm78-*" "lm79-*"'
    }


def test_toml_is_read_when_python_has_a_reader_and_skipped_and_counted_when_not(
    tmp_path, monkeypatch, capsys
):
    if mod.tomllib is not None:
        assert lines("starship.toml", STARSHIP) == {
            2: "add_newline = false",
            5: "character.success_symbol = [>](bold green)",
            8: "profiles.1.name = work",
        }
    src = write(tmp_path / "src", {"starship.toml": STARSHIP, "bashrc": "X=1\n"})
    out = tmp_path / "out"
    monkeypatch.setattr(mod, "tomllib", None)
    assert mod.convert(PurePosixPath("starship.toml"), STARSHIP.encode()) is None
    argv = ["mirror", "--from", str(src), "--to", str(out)]
    monkeypatch.setattr(sys, "argv", ["dotfiles.py", *argv])
    assert mod.main(argv) == 0
    said = capsys.readouterr()
    assert "skipped 1 .toml: reading TOML needs Python 3.11" in said.err
    assert said.out.strip().endswith("wrote 1 files to " + str(out) + "; skipped 1")


def test_a_secret_is_withheld_never_copied(tmp_path):
    secrets = {
        "bashrc": "export GITHUB_TOKEN=s3cr3tvalue1\nexport DB_PASSWORD='pw-s3cr3t-2'\n"
        "export OPENAI_API_KEY=s3cr3t-3\nexport GH=ghp_abcdefghij0123456789\n"
        "alias api='curl -H \"Authorization: Bearer abcdefghijkl\"'\n",
        "gitconfig": '[remote "o"]\n\turl = https://ana:hunter2-s3cr3t@git.example.org/r.git\n'
        '[url "https://ana:tok-s3cr3t@github.com/"]\n\tinsteadOf = https://github.com/\n',
        "npmrc": "//registry.npmjs.org/:_authToken=npm_s3cr3t4\n",
        "pypirc.ini": "[pypi]\nusername = __token__\npassword = pypi-s3cr3t5\n",
        "config/tmux.conf": "set -g @secret_key s3cr3t6\n",
    }
    got, out = mirror_of(tmp_path, secrets)
    assert got.returncode == 0, got.stderr
    text = "".join(p.read_text() for p in sorted(out.rglob("*.txt")))
    for leak in ("s3cr3t", "ghp_", "hunter2", "abcdefghijkl"):
        assert leak not in text, leak
    assert "GITHUB_TOKEN=[withheld]" in text and "DB_PASSWORD=[withheld]" in text
    assert "GH=[withheld]" in text and "api=[withheld]" in text
    assert "url.https://[withheld]@github.com/.insteadOf = https://github.com/" in text
    assert "pypi.username = __token__" in text, "a name that isn't a secret is kept"
    assert "GIT_AUTHOR_EMAIL=ana@example.org" in mod.shell_line(
        "export GIT_AUTHOR_EMAIL=ana@example.org"
    ), "an author is not an auth"


def test_files_are_known_by_name_with_or_without_chezmoi_dot():
    known = {"bashrc": "shell", "dot_zshrc": "shell", "private_dot_bash_profile.tmpl": "shell",
             "bashrc.local": "shell", "aliases.zsh": "shell", "install.sh": "shell",
             "dot_config/git/config": "git", "gitconfig": "git", "work.gitconfig": "git",
             "dot_vimrc": "vim", "config/nvim/init.vim": "vim", "tmux.conf": "set",
             "npmrc": "ini", "setup.cfg": "ini", "kitty.conf": "conf", "starship.toml": "toml"}  # fmt: skip
    for name, kind in known.items():
        assert mod.kind_of(PurePosixPath(name)) == kind, name
    for name in ("zsh_history", "bash_history", "README.md", "config", "ssh/config",
                 "notes.txt", "config/git/ignore"):  # fmt: skip
        assert mod.kind_of(PurePosixPath(name)) is None, name


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {**REPO, "README.md": "# mine\n"})
    assert got.returncode == 0, got.stderr
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*.txt")) == sorted(
        f"{rel}.txt" for rel in REPO
    )
    assert got.stdout.strip() == f"wrote {len(REPO)} files to {out}; skipped 0"


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(tmp_path, {"bashrc": "A=1\n", ".bashrc": "B=2\n",
                                    ".config/zshrc": "C=3\n"})  # fmt: skip
    assert got.returncode == 0
    assert [p.name for p in out.rglob("*.txt")] == ["bashrc.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    src = write(tmp_path / "src", REPO)
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    for out in ("a", "b"):
        run("mirror", "--from", str(src), "--to", str(tmp_path / out))
    snap = [{p.relative_to(tmp_path / o): p.read_bytes()
             for p in (tmp_path / o).rglob("*") if p.is_file()} for o in "ab"]  # fmt: skip
    assert snap[0] == snap[1] and snap[0]
    assert before == {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}


def test_a_file_it_cannot_read_or_with_no_setting_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(tmp_path, {"bashrc": "A=1\n", "zshrc": b"\xff\xfeA=1\n",
                                    "profile": "# only a comment\nmesg n\n"})  # fmt: skip
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {out}; skipped 2"


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"README.md": "# nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    src = write(tmp_path / "src", {"bashrc": "A=1\n"})
    for dst in (src / "inside", tmp_path):
        got = run("mirror", "--from", str(src), "--to", str(dst))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    got = run(
        "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
    )
    assert got.returncode == 2 and got.stderr.startswith("refused: not a folder")
    assert not (src / "inside").exists()


def test_a_bad_command_line_says_how_to_run_it():
    for argv in ([], ["mirror", "--from", "x"], ["copy", "--from", "a", "--to", "b"]):
        got = run(*argv)
        assert got.returncode == 2 and "usage: dotfiles.py" in got.stderr


def test_a_question_lands_on_its_setting_and_a_word_on_every_line_answers_nothing(
    tmp_path,
):
    """The owner's rule: no word of the reader's own in passage after passage,
    so a question about something the folder doesn't hold gets nothing."""
    got, out = mirror_of(tmp_path, REPO)
    assert got.returncode == 0, got.stderr
    pile = kernel.chunks(out)
    for c in pile:  # every word written is the source's, but a withheld one
        source = set(kernel.words((tmp_path / "src" / c["path"][:-4]).read_text()))
        assert set(kernel.words(c["text"])) - source <= {"withheld"}, c
    by_file: dict[str, list[set]] = {}
    for c in pile:
        by_file.setdefault(c["path"], []).append(set(kernel.words(c["text"])))
    several = {path: ps for path, ps in by_file.items() if len(ps) > 2}
    assert "gitconfig.txt" in several, "a file of several passages to look in"
    for path, passages in several.items():
        n = Counter(w for p in passages for w in p)
        for w in [w for w, k in n.items() if k > len(passages) / 2]:
            assert kernel.rank(pile, f"volcano {w}") == [], (path, w)
    assert kernel.rank(pile, "volcano marathon") == []
    editor = {c["path"]: c for c in kernel.rank(pile, "where did I set my editor")}
    assert "EDITOR=nvim" in editor["bashrc.txt"]["text"].split("\n")
    assert editor["gitconfig.txt"]["line"] == 5, "a run of settings is one passage"
    assert editor["gitconfig.txt"]["text"] == "core.editor = nvim"
    email = kernel.rank(pile, "what is my git email")
    assert (email[0]["path"], email[0]["line"]) == ("gitconfig.txt", 2)
    assert "user.email = ana@example.org" in email[0]["text"]
    prefix = kernel.rank(pile, "where is my tmux prefix")
    assert [(c["path"], c["line"]) for c in prefix] == [("tmux.conf.txt", 3)]
