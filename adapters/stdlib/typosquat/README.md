<!-- willow-addon
section: Privacy and safety
line: Dependency names a letter off from a popular one (reqeusts, lodahs), checked against a list of top packages you downloaded.
source: new
added: 2026-10-24
writes: nothing
network: none
-->
# typosquat

Which of your locked dependencies has a name one letter off a popular
package's -- a likely typosquat -- checked against a list of top packages you
downloaded, with no network of its own.

    python adapters/stdlib/typosquat/typosquat.py --box DIR  [--top FILE]
    python adapters/stdlib/typosquat/typosquat.py --from ANY-FOLDER [--top FILE]

    npm       reqeusts -> looks like requests  (locked 1.0.0)
    npm       lodahs -> looks like lodash  (locked 4.17.4)

    2 of 9 dependencies look like a popular name -- check the spelling before you install.

Two things it reads:

- **Your lockfiles**, found in the folder (the box's pile, or any folder with
  `--from`): package-lock.json (npm), requirements.txt (the name==version pins,
  PyPI), poetry.lock (PyPI) and Cargo.lock (crates.io). It uses the same reader
  as [advisories](../advisories/), so the dependencies are the same set. A
  lockfile inside a node_modules, vendor or .git folder is skipped.
- **The top list** given with `--top`: a plain text file of popular package
  names you downloaded, one per line. A line is either `ecosystem name` (npm,
  PyPI or crates.io), which is compared only to dependencies in that ecosystem,
  or just a name, which is compared to any. Download it yourself; this add-on
  never fetches.

A dependency is flagged when its name is exactly one edit from a popular name
and is not itself on the list. One edit is an insert, a delete, a substitution,
or a swap of two adjacent letters (optimal string alignment distance), so a
transposition like reqeusts for requests counts as one, not two -- those are a
common typosquat. A name equal to a popular one is never flagged, and a name
two or more edits away is not flagged.

With no `--top` it lists the dependencies it found and stops: an inventory,
with nothing to compare against.

Exit codes, the kernel's: 0 nothing looks like a popular name, or there are no
lockfiles to check; 42 one does, and waits on you; 2 refused.

**Never:** fetches anything, or writes anything. It reads your lockfiles and
the top list you point it at; the list is yours to keep current.
