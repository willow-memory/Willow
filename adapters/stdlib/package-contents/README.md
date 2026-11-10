<!-- willow-addon
section: Privacy and safety
line: What's inside a wheel, sdist, npm tarball or .crate before you install it: every file, and any code it runs on install.
source: new
added: 2026-10-29
version: 0.1.0
writes: nothing
network: none
role: page
output: report
-->
# package-contents

What a package holds, and what it runs, before you install it.

A package file is an archive. This opens one and lists every file in it,
with its size, then the code that would run because you installed it, by the
file and line that makes it run. Nothing is unpacked, run, fetched or written.

    python adapters/stdlib/package-contents/package_contents.py --box DIR [--json]
    python adapters/stdlib/package-contents/package_contents.py --from ANY-FILE-OR-FOLDER [--json]

    package-contents: populated, 1 of 1 package would run code on install or write outside its folder; none was run here
    ## evil-1.0-py3-none-any.whl: wheel, 2 files
      evil/__init__.py  6 B
      evil.pth          38 B
    ## evil-1.0-py3-none-any.whl runs on install
      evil.pth:2        import: the line runs at every Python start

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a line saying what it found, then for each package a
group of its files, each with its size, and, when there are any, a group of
the code it runs on install (by the file and line that makes it run) and one
of its paths that escape. `--json` gives the same report as one JSON object.
Read each flagged package before you install it; none was run here.

| Package | What runs |
|---|---|
| wheel (.whl) | nothing while it installs; a `.pth` line that starts with `import` runs at every Python start |
| sdist (.tar.gz, .zip) | its setup.py, and the build backend its pyproject.toml names (marked in-tree when it sets `backend-path`) |
| npm tarball (.tgz) | its preinstall, install and postinstall scripts; and node-gyp, when there is a binding.gyp and no install script |
| crate (.crate) | its build script (build.rs, or the file `build =` names), and a procedural macro |

The kind is read from the file's name and its contents: a `.whl` is a wheel, a
`.crate` or an archive holding a Cargo.toml is a crate, one holding a
package.json is an npm tarball, one holding a PKG-INFO, setup.py or
pyproject.toml is an sdist. Any other archive is listed and called an
archive. A package file inside a folder is found at any depth. A path that is
absolute or climbs out with `..` is flagged in its own group, since an
unpacker that trusts it writes outside its folder. A file that can't be opened
as an archive is noted on stderr, counted in the report's first line, and not
checked.

Exit codes, the kernel's: 0 packages listed and nothing would run
(populated), or no package file (empty); 42 code would run, or a path
escapes, and waits on you (populated), or no package file here could be
opened (unreachable); 2 refused.

**What it doesn't do:** read the code it points to, or judge whether it is
harmful. A `.pth` import is often harmless; this says where to look. Code a
package runs only when you use it (an entry point, say) isn't install-time
code and isn't listed.

**Uses:** the kernel's box, to find the pile.

**Never:** unpacks, runs, fetches or writes anything. The archive is read in
memory, a file at a time, and only to its first megabyte.
