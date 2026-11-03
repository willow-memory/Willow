<!-- willow-addon
section: Privacy and safety
line: The install scripts the packages in node_modules would run (preinstall, install, postinstall), each cited by file and line.
source: new
added: 2026-10-24
writes: nothing
network: none
output: report
-->
# install-scripts

What runs when you run `npm install`, before you trust the packages.

A package can declare scripts that npm runs on install: `preinstall` before
it is installed, `install` while it is, and `postinstall` after. Those run
arbitrary code on your machine. This lists every one the packages in a
node_modules folder would run, by package, and by the file and line where
each is written, so you can read the code first.

    python adapters/stdlib/install-scripts/install_scripts.py --box DIR [--json]
    python adapters/stdlib/install-scripts/install_scripts.py --from ANY-FOLDER [--json]

    install-scripts: populated, 1 install script in 1 package would run on npm install; none was run here
    ## esbuild
      web/node_modules/esbuild/package.json:5  postinstall  node install.js

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a line saying what it found, then a group per package,
each row the file and line a hook is written on and then the hook and its
command. `--json` gives the same report as one JSON object. Read each script
before you trust its package; none was run here.

| Hook | When npm runs it |
|---|---|
| preinstall | before the package is installed |
| install | while the package is installed |
| postinstall | after the package is installed |

Every package.json under the folder that sits inside a node_modules folder is
read, at any depth, including a package's own nested node_modules. A
package.json outside node_modules, such as your own project's, is not read:
this is about what the packages you installed would run. The command is shown
as it is written, on one line (a newline shows as `\n`). A key written with
escapes can't be placed, so it is cited at line 1. A package.json that isn't
valid JSON is noted on stderr, counted in the report's first line, and not
checked. A name is the package's own `name`, or else its folder's.

Exit codes, the kernel's: 0 nothing would run, or no node_modules folder
(empty); 42 an install script is there, and waits on you (populated), or no
package.json in node_modules could be read (unreachable); 2 refused.

**Never:** runs, fetches or writes anything. The commands are shown, never run.
