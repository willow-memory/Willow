<!-- willow-addon
section: For maintainers
line: Where your venvs are, in willow-bot or out, their locks and the services running them; and which one has what CI needs, and how to run it.
source: bot
added: 2026-10-26
writes: nothing
network: none
role: tools
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

## Where your venvs are: `--find`

The bot's other half of the same question, its `willow-bot-steward venvs`:
every venv under the folders you name, three levels down (a venv behind a
symlink counted once, under its real path, the link said).

    $ python adapters/stdlib/bot-venv/bot_venv.py --find ~/github --find $WILLOW_HOME
    /box/willow-bot/venvs/willow-bot
      inside the bot
      67 packages; lock: none
      runs: willow-bot.service, willow-bot-steward.service
      python 3.14.4
    ~/github/org/repo/.venv
      also ~/github/org/linked/.venv
      outside the bot
      81 packages; lock: drifted, 1 missing, 1 changed
      runs: nothing running
      python 3.14.4
    found 2 venvs under ~/github, /box: 1 inside the bot, 1 outside; 1 run by a service

- **Inside or outside the bot:** inside is under the box's willow-bot folder,
  where the bot keeps its venvs; anywhere else is outside. Said only when
  there's a box.
- **Packages** are counted from site-packages' `*.dist-info` folders; nothing
  is run.
- **The lock** is the one the bot reads, `<box>/willow-bot/locks/<name>.requirements.lock`
  (pip-compile's), named for the checkout when the venv is its `.venv`:
  `none`, `holds`, or `drifted` with how many are missing, changed and extra
  (pip, setuptools and wheel, and packages installed with `-e`, aren't
  extra).
- **Runs** names each service with a process running from the venv's bin folder,
  from /proc: the process's command line, and the unit its cgroup names,
  so a child process counts for the service that started it. Your session's
  own manager isn't a service. With no /proc, it says unknown.
- **Python** is read from the venv's `pyvenv.cfg`. Add `--needs` and each
  venv found is asked, as `--venv` asks, whether it's ready.

## What it uses

Nothing of the kernel's beyond its exit codes. Each venv's own Python is run
once, isolated (`-I`), to say its version and its packages' versions from
their installed metadata; nothing in the folder you run it from is imported.
It reads the two box variables and nothing else of the bot's.

## What it never does

- **It runs nothing else.** It prints the line that runs CI; it never runs
  CI, installs a package, or moves, changes or removes a venv. Bringing a
  venv inside the bot is yours to do, as the bot's own plan says.
- **It writes nothing**, touches no box and no key, and reaches no network.
  It looks for the bot's venv inside the box; it never opens the box's
  record.

Exit codes, the kernel's: 0 some venv is ready (with only `--find`, some
venv was found); 42 none is (none was found); 2 refused (a bad command line,
no box for `--bot`, or a venv or folder that is not a folder).
