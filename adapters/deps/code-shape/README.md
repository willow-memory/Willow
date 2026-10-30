<!-- willow-addon
section: Finding things
line: Search code by its shape, not its words: every call of a kind, whatever it's named.
source: new
added: 2026-10-30
needs: the ast-grep program, from ast-grep-cli on PyPI or your own ast-grep; MIT
floor: ast-grep-cli 0.14.1
writes: nothing
network: none
tags: needs-install, offline, read-only, search
-->
# code-shape

Words find a name; a shape finds every use of it, however it's written.
ast-grep reads your code as code, and a pattern with holes matches every
piece of code of that shape.

    pip install -r adapters/deps/code-shape/requirements.txt
    python adapters/deps/code-shape/code_shape.py --box DIR --lang python \
        'subprocess.run($$$, shell=True)'
    demo/redteam/target/app/views.py:9  eec228a8e4b0  return subprocess.run("ping -c1 " + host, shell=True)
    1 match in 1 passage

That is willow's own repo as a pile: the red-team demo's command injection,
found by its shape, where a word search for `shell=True` also finds every
line that only talks about it.

**A pattern** is code with holes: `$NAME` matches one piece, `$$$` any
number. `requests.get($$$)` is every call of it, its arguments on one line
or many; a comment naming it is no match. `--lang` is one ast-grep parses
(python, javascript, typescript, tsx, go, rust, java, c, cpp, csharp,
ruby, kotlin, swift, html, css and more), each file read by its extension.
A pattern ast-grep can't parse is refused with what it said.

**Checked against the kernel**, as the ripgrep add-on checks its hits: each
match is shown as its first line, with the id of the kernel's passage that
holds that line, the one the kernel would serve and cite. Hidden files and
folders are skipped and `.gitignore` is not obeyed, as the kernel does; a
match the kernel doesn't read as written is counted, never shown.

On willow's repo `kernel.rank($$$)` gives 18 matches in 17 passages, the
same at the pins and at the floor.

**The guard sees Python, not ast-grep.** ast-grep is a program. It
is run with `run --pattern --lang --json=stream` and the pile, never with
`--rewrite` or `--update-all`, so it writes nothing.

**Without ast-grep** it refuses and names the install: exit 2, never a quiet
skip.

**Uses:** `chunks`, `read`, `config`, and the kernel's exit codes: 0 a match
in a passage; 42 none; 2 refused.

**Never:** writes anything, not even the record, changes a line of your
code, or goes online.
