# deps

Add-ons that need something installed: [pdf](pdf/) and [mcp](mcp/) so far.
The planned ones are marked 📦 in the main README's list.

The kernel needs nothing but Python, so anything here says plainly what it
adds. Each add-on in this folder carries:

- **`requirements.txt`**, every Python package pinned with `==` to one
  version, and nothing unpinned;
- **`needs:` in its card's header**, naming each package and any outside
  program (`tesseract`, `gpg`, `git`) or service (a local model server), with
  its licence. The licence must be one an Apache-2.0 project can depend on;
  a program that is only run, never linked, says so;
- **`network:` in the header** if it goes online at all, even once to download
  a model, and the same on the first line of its card;
- **`requirements-floor.txt`**, the same packages pinned at their floor, the
  oldest version it is tested against (the floor rule, below);
- **`floor:` in the header**, naming each floor version, and why, when it is
  above the rule's;
- tests that run in CI with its requirements installed, in a job of its own,
  so one add-on's packages never decide whether another's tests pass, and run
  twice: once at its pins and once at its floor.

## The floor rule

Every dependency is also tested at the last version released on or before
2020-12-31, or at its first release if it had none by then. A pin says the
add-on works today; a floor says how far back it still works, which is what
someone with an older install needs to know.

When an add-on can't run at the rule's version, it raises its floor, and the
`floor:` line says why in a sentence. CI's `deps:floors` gate reads each
release's upload date from PyPI and fails a floor that is above the rule's
version without a reason; `test_docs.py` fails a deps add-on with no floor
file, or a `floor:` line that doesn't name each floor version.

| Add-on | Rule's version | Floor | Why |
|---|---|---|---|
| pdf | pypdf 1.9 (2014) | pypdf 3.1.0 | 1.9 is a Python 2 release; 3.1.0 is the first since the name was revived |
| mcp | mcp 0.9.1 (its first, 2024) | mcp 2.0.0 | the server is built on MCPServer, which arrived in 2.0.0; 2.x removed 1.x's server API |

An install that isn't there makes the add-on refuse with a message naming it,
never skip quietly: a check that skips still looks like a pass.
