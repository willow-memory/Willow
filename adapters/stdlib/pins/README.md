<!-- willow-addon
section: For maintainers
line: Version ranges in package.json, pyproject.toml or Cargo.toml that no lockfile holds.
source: new
added: 2026-10-24
writes: nothing
network: none
tags: no-install, offline, read-only, maintainers
-->
# pins

The dependencies your project declares as a version range that no lockfile
pins to one exact version, so the next install can resolve them to something
else. Offline and read-only.

    python adapters/stdlib/pins/pins.py --box DIR
    python adapters/stdlib/pins/pins.py --from ANY-FOLDER

    PyPI  requests  >=2.19   no lockfile pins it
    npm  jest  ~29.0.0   no lockfile pins it
    npm  lodash  ^4.17.0   no lockfile pins it

    3 of 3 declared ranges have no lockfile pin.

**What this first version reads.** Two manifests only: the package.json file
(its dependencies and devDependencies) and the requirements.txt file. The
pyproject.toml and Cargo.toml manifests are not read yet. Reading TOML with
the standard library on Python 3.9 is not safe enough to guess at, so they
wait for a version that does it properly.

A declared value is a range unless it is one exact version. A value like
`^1.2.0`, `~2`, `>=2.0`, `1.2`, `*`, `latest`, a hyphen range, a URL or a git
spec, or a requirement with no version at all, is a range. An exact `1.2.3`,
with an optional prerelease tag, or a requirement written `name==1.2.3`, is
already pinned and is not listed.

The lockfiles say what was resolved. They are read by the same reader the
[advisories](../advisories/) add-on uses: package-lock.json, requirements.txt,
poetry.lock and Cargo.lock. A range is pinned when a lockfile holds its package
at any version, and the PyPI names are matched with case and -_. folded. A
range no lockfile names is listed, with its ecosystem, name and range.

Manifests inside a node_modules, vendor or .git folder are skipped. A manifest
that can't be read is named apart as "couldn't read -- check by hand"; it is
never dropped quietly.

With nothing to check it says so and stops. It only reads, and writes nothing.
Exit codes, the kernel's: 0 every declared range is pinned, or there is no range
to check, or there is no manifest; 42 a range no lockfile pins, or a manifest
that can't be read, and waits on you; 2 refused.

**Never:** fetches anything, or writes anything. The lockfiles are yours to keep
current.
