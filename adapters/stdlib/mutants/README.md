<!-- willow-addon
section: For maintainers
line: Breaks each add-on's code on purpose and checks its tests notice.
source: new
added: 2026-10-23
writes: nothing
network: none
-->
# mutants

A test that can't fail checks nothing. This checks that each add-on's tests
can: it breaks the add-on's code in small ways, one at a time, and runs its
tests against each break.

    python adapters/stdlib/mutants/mutants.py run [NAME ...] [--per N]
    python adapters/stdlib/mutants/mutants.py list NAME

| Break | What changes |
|---|---|
| `compare` | `==` and `!=`, `<` and `>=`, `>` and `<=`, `in` and `not in`, `is` and `is not` swap |
| `and-or` | an `and` becomes `or`, or the reverse |
| `number` | a whole number becomes one larger |

A break the tests fail on is **killed**. One they pass on **survived**: the
tests can't tell the add-on from a broken one.

**Which breaks.** Every place a break can be made has an id: the SHA-256 of
the file, the kind, the code there and which time that code repeats. Line
numbers aren't part of it, so an id stays put when code above it moves. The
six (or `--per`) lowest ids are made. Nobody picks them, and anyone can redo
the choice: `list` shows every one.

**What may survive.** Some breaks change nothing a person could notice: an
import path the test layout hides, a cap no folder reaches. Each is listed in
[accepted.json](accepted.json) by id, with its reason in one sentence. An add-on
fails when a break survives that isn't listed, when a listed one is no longer
made or no longer survives, or when its tests end any way but passing or
failing (no tests found, a collection error), which killed nothing.

**Where.** In a copy of the repo, never the repo itself: each break is made,
tested and put back in the copy. Each add-on's own tests run, with its share
of the checks every add-on keeps
([ci/test_contract.py](../ci/test_contract.py)), narrowed by `WILLOW_ONLY`.
Only `adapters/stdlib`: a deps add-on's tests need its own installs.

**In CI:** the `mutants` part, one gate per add-on (`mutants:NAME`).

**Uses:** the kernel's `h256` and its exit codes: 0 every break killed or
accepted; 42 pytest isn't installed; 2 an add-on failed, or a bad command
line.

**Never:** changes a file in the repo, or decides by itself that a survivor
is harmless.
