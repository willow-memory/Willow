<!-- willow-addon
section: For maintainers
line: Which venv has what CI needs, willow-bot's own by its rule or any you name, and the line that runs CI with its Python.
source: bot
added: 2026-10-26
writes: nothing
network: none
-->
# bot-venv

[ci](../ci/) calls pytest and ruff through the Python that runs it, not
whichever is first on the path. Run it with a Python that lacks them and
every lint, tests and mutants row comes back unreachable, which looks like a
broken repo when it's a missing install. willow-bot keeps its tools in a
venv of its own, and its one script runs CI's tools from there. `bot-venv`
asks that venv, or any you name, whether it has what CI needs, and prints
the line that runs CI with its Python.

    python adapters/stdlib/bot-venv/bot_venv.py [--bot] [--venv DIR ...] \
        [--needs NAME[==VERSION] ...]

    $ python adapters/stdlib/bot-venv/bot_venv.py --bot --venv ~/venvs/old --needs ruff==0.16.7
    /box/willow-bot/venvs/willow-bot
      python 3.14.4
      pytest 9.1.1
      ruff 0.16.7
      ready: /box/willow-bot/venvs/willow-bot/bin/python adapters/stdlib/ci/ci.py run --box BOX
    ~/venvs/old
      python 3.14.4
      pytest 9.1.1
      ruff 0.15.0, but ruff==0.16.7 wanted
      not ready
    1 of 2 ready

## The bot's venv

`--bot` finds it by willow-bot's own rule, the one its `paths.env_box` and
its one script's `_bot_venv` keep:

- the box is `$WILLOW_HOME`, else `$WILLOW_VAULT_BOX` (a blank one counts as
  unset), and it must be an absolute path to an existing folder;
- the venv is `<box>/willow-bot/venvs/willow-bot` (the venvs live in the
  bot), or the old `<box>/venvs/willow-bot` while only that one exists.

With no box it refuses and says why; it never guesses one. `--venv DIR`
names any other venv, and both can be given.

## What it says

It always asks for pytest and ruff. `--needs` asks for one more package, or
holds one to a version: `--needs ruff==0.16.7` holds ruff to the version CI
pins, since a different ruff can format the same file differently.

- **ready**, with the line to run, when the venv's Python is 3.9 or newer and
  has every package, at the version pinned if one is;
- **not ready**, with what's missing: a package not installed, one at
  another version, or a Python older than 3.9;
- **no Python in it** when the folder has no `<venv>/bin/python` (or
  `<venv>/Scripts/python.exe` on Windows);
- **didn't answer** when it has one that doesn't run or says nothing it can
  read.

The last two are kept apart from "not ready": a folder that isn't a venv and
a venv without ruff are different answers.

## What it uses

Nothing of the kernel's beyond its exit codes. Each venv's own Python is run
once, isolated (`-I`), to say its version and its packages' versions from
their installed metadata; nothing in the folder you run it from is imported.
It reads the two box variables and nothing else of the bot's.

## What it never does

- **It runs nothing else.** It prints the line that runs CI; it never runs
  CI, installs a package or changes a venv.
- **It writes nothing**, touches no box and no key, and reaches no network.
  It looks for the bot's venv inside the box; it never opens the box's
  record.

Exit codes, the kernel's: 0 some venv is ready; 42 none is; 2 refused (a bad
command line, no box for `--bot`, or a venv that is not a folder).
