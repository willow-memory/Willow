<!-- willow-addon
section: For maintainers
line: CI caches pip, npm, .NET and Maven downloads keyed on their lockfiles, so a run skips the installs.
source: new
added: 2026-10-26
writes: nothing
network: none
tags: no-install, offline, read-only, maintainers
-->
# ci-cache

CI reinstalls the same packages on every run. Those downloads can be cached and
**keyed on the files that pin them**, so a run whose pins haven't changed
restores the cache instead of fetching again. `ci-cache` reads a folder's
lockfiles and prints, per ecosystem, the directory to cache and the key a CI
cache step keys on.

    python adapters/stdlib/ci-cache/ci_cache.py --from FOLDER

It groups the lockfiles it finds by ecosystem and prints a line for each:

    pip    ~/.cache/pip        <key>  (3 files)
    npm    ~/.npm              <key>  (1 file)

The ecosystems and the lockfiles that key them:

    pip     requirements*.txt, Pipfile.lock, poetry.lock   ->  ~/.cache/pip
    npm     package-lock.json, yarn.lock, pnpm-lock.yaml   ->  ~/.npm
    .NET    packages.lock.json                             ->  ~/.nuget/packages
    Maven   pom.xml                                        ->  ~/.m2/repository

The key is the SHA-256 over each lockfile's path and the SHA-256 of its bytes,
sorted — so the **same pins give the same key** on any machine, and changing a
pin gives a new one (the cache falls through to a fresh install, then holds
again). A CI workflow uses it as the `key:` of its cache step for that
directory.

## what it reads and writes

It only reads FOLDER and prints. Hidden folders and `node_modules` are not
walked, so a dependency's own lockfiles never key the cache. It writes nothing,
touches no box or key, and reaches no network.

Exit codes, the kernel's: `0` some ecosystem's lockfiles were found; `42` none
were (nothing to cache); `2` refused (a bad command line, or a `--from` that is
not a folder).
