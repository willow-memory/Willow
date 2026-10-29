<!-- willow-addon
section: Trust and proof
line: The licence of every installed dependency, read from its own metadata on this machine: which are copyleft, and which file says so.
source: new
added: 2026-10-29
writes: nothing
network: none
tags: no-install, offline, read-only, trust
-->
# licenses

What every installed dependency says its licence is, and which of them copyleft.

    python adapters/stdlib/licenses/licenses.py --site
    python adapters/stdlib/licenses/licenses.py --from FOLDER
    python adapters/stdlib/licenses/licenses.py --box DIR

    strong copyleft
        somepkg 1.2   lib/site-packages/somepkg-1.2.dist-info/METADATA:9   GPL-3.0-or-later
    weak copyleft
        libthing 4.0   node_modules/libthing/package.json:5                LGPL-2.1
    undeclared
        oddity 0.1     lib/site-packages/oddity-0.1.dist-info/METADATA:3   (none)

    41 packages: 37 permissive, 1 weak copyleft, 1 strong copyleft, 2 undeclared.

Two kinds of installed package are read, at any depth: a Python package from
its metadata (the `License-Expression` line, else its `License ::`
classifiers, else its `License` line), and an npm package from the `license`
in its package.json, inside a node_modules folder. `--site` reads the
site-packages of the Python that runs it. Each licence lands in one class:

| Class | Examples |
|---|---|
| permissive | MIT, BSD, Apache, ISC, PSF, Unlicense, CC0 |
| weak copyleft | LGPL, MPL, EPL, CDDL |
| strong copyleft | GPL, AGPL, EUPL, OSL |
| undeclared | none given, or a licence this doesn't know |

An SPDX expression is read through: `MIT OR GPL-3.0` is permissive, since
you may pick MIT; `MIT AND GPL-3.0` is strong, since both apply. Two
classifiers on one package are read as a choice. Old free text ("GNU General
Public License v3") is read by its words. Only what is not permissive is
listed, each with the file and line that says so.

This is what each package says about itself. It is a lead for you to read
and never legal advice, and a licence file inside a package is not read.

Exit codes, the kernel's: 0 every package is permissive (or none installed);
42 a copyleft or undeclared licence, which waits on you; 2 refused.

**Uses:** the kernel's box, to find the pile.

**Never:** installs, fetches or writes anything.
