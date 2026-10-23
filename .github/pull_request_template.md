## What this changes

<!-- One idea per pull request. Say what it does in a sentence or two. -->

## Which add-on or idea

<!-- The add-on's folder, or the planned.json entry this builds or adds.
     Leave out if this touches neither. -->

## Its promises

<!-- For an add-on: its card's `writes` and `network`, and whether this
     changes them. If it does, say why here, where the maintainer sees it. -->

## What CI said

<!-- Paste the output of:
       python adapters/stdlib/ci/ci.py run --box /tmp/ci-record
       python adapters/stdlib/ci/ci.py show --box /tmp/ci-record
     A run you can show is worth more than a sentence saying it passed. -->

## Before you open it

- [ ] The tests can fail: I broke the thing on purpose and watched them go red
      (`python adapters/stdlib/mutants/mutants.py run NAME` does it for you)
- [ ] A new file is in the README's tree; a new add-on has its card and tests
- [ ] A built idea's entry is out of `adapters/planned.json` in this change
- [ ] `python adapters/stdlib/readme/readme.py write` was run, not hand edits
- [ ] Nothing here writes an approval, or reads the key
