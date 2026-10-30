# deps

Add-ons that need something installed: [pdf](pdf/) and [mcp](mcp/) so far.
The planned ones are in [ADDONS.md](../../ADDONS.md), each saying what it needs installed.

The kernel needs nothing but Python, so anything here says plainly what it
adds. Each add-on in this folder carries:

- **`requirements.txt`**, every Python package pinned with `==` to one
  version, and nothing unpinned;
- **`needs:` in its card's header**, naming each package and any outside
  program (`tesseract`, `gpg`, `git`) or service (a local model server), with
  its licence. The licence must be one an Apache-2.0 project can depend on;
  a program that is only run, never linked, says so;
- **`network:` in the header**, as every add-on has, saying where it goes
  if it goes online at all, even once to download a model, and the same on
  the first line of its card;
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
| photos | Pillow 8.0.1 (2020) | Pillow 11.0.0 | 8.0.1 has no wheel for Python 3.13 and won't build there; 11.0.0 is the first with one |
| record-sql | duckdb 0.2.3 (2020) | duckdb 1.1.1 | 0.2.3 is built for Python 3.6 to 3.9; 1.1.1 is the first with a wheel for 3.13 |
| dialect | wordfreq 2.3.2 (2020) | wordfreq 3.1.0 | every release before 3.1.0 imports pkg_resources, which a 3.13 environment doesn't have |
| static-search | pagefind 1.2.0a4, pagefind-bin 1.2.0a5 (their first, 2024) | 1.3.0 of each | the first uploads are alphas, and 1.2.0's index differs from build to build; 1.3.0 is the first to give the same bytes |
| ocr | Pillow 8.0.1, pypdf 1.9 | Pillow 11.0.0, pypdf 3.1.0 | neither rule version runs on Python 3.13: no wheel, Python 2 |

An install that isn't there makes the add-on refuse with a message naming it,
never skip quietly: a check that skips still looks like a pass.
