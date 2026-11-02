<!-- willow-addon
section: Privacy and safety
line: How old each locked dependency is, and which are yanked, deprecated or two years without a release, from a registry index you downloaded.
source: new
added: 2026-10-24
writes: nothing
network: none
uses: advisories
-->
# outdated

How old each locked dependency is, and which have gone bad -- yanked,
deprecated, or a project that hasn't shipped in two years -- read from a
registry index you downloaded, with no network of its own.

    python adapters/stdlib/outdated/outdated.py --box DIR  [--index DIR] [--now YYYY-MM-DD]
    python adapters/stdlib/outdated/outdated.py --from ANY-FOLDER [--index DIR] [--now YYYY-MM-DD]

    npm       lodash 4.17.4
        released 2017-02-20 (9.7y ago); latest 4.17.21, 2021-02-20
    PyPI      left-pad 1.0.0
        released 2018-01-01 (8.8y ago); latest 1.0.0, 2018-01-01
        yanked; no release in 8.8y

    1 of 2 dependencies need attention (yanked, deprecated, or two years
    without a release).

It reads the lockfiles [advisories](../advisories/) reads (it uses that
add-on's reader), so the dependencies are the same set: npm, PyPI and
crates.io. It pairs with advisories -- that one asks whether a dependency is
*named by an advisory*; this one asks whether it is *old or abandoned*.

The index given with `--index` is a folder of each registry's own metadata,
one JSON file per package, at `<index>/<ecosystem>/<name>.json`:

| Ecosystem | The document, and what it reads from it |
|---|---|
| npm | registry.npmjs.org/&lt;name&gt;: its `time`, `dist-tags.latest`, and a version's `deprecated` note |
| PyPI | pypi.org/pypi/&lt;name&gt;/json: its `releases` with upload times and the per-file `yanked` flag |
| crates.io | crates.io/api/v1/crates/&lt;name&gt;: its `versions` with `created_at` and `yanked` |

Each flag is only looked for where a registry has it: npm has no yank, and
PyPI and crates.io have no deprecation. A version missing from the index is
reported as unknown, never judged. `--now` fixes today so a run repeats; it
defaults to the real date. With no `--index` it just lists the dependencies.

Exit codes, the kernel's: 0 nothing to act on (or no lockfiles); 42 one is
yanked, deprecated or two years without a release, and waits on you; 2
refused.

**Never:** fetches anything, or writes anything. The index is yours to keep
current.
