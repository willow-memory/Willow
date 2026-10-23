# deps

Add-ons that need something installed. Nothing here is built yet; the planned
ones are marked 📦 in the main README's list.

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
- tests that run in CI with its requirements installed, in a job of its own,
  so one add-on's packages never decide whether another's tests pass.

An install that isn't there makes the add-on refuse with a message naming it,
never skip quietly: a check that skips still looks like a pass.
