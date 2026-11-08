<!-- willow-addon
section: Privacy and safety
line: Security advisories from a downloaded OSV or GitHub database, matched to your lockfiles: which dependency each names, and since when.
source: new
added: 2026-10-24
writes: nothing
network: none
role: page
output: report
-->
# advisories

Which of your locked dependencies a known security advisory names, and since
when -- read from a database you downloaded, with no network of its own.

```
python adapters/stdlib/advisories/advisories.py --box DIR  [--db OSV_DIR] [--json]
python adapters/stdlib/advisories/advisories.py --from ANY-FOLDER [--db OSV_DIR] [--json]

advisories: populated, 2 of 2 dependencies named by a known advisory
## named by a known advisory
  PyPI  requests 2.19.1  GHSA-x84v-xcm2-53pg  CVE-2018-18074  since 2018-10-09  Credentials leak
  npm   lodash 4.17.4  GHSA-jf85-cpcp-j695  CVE-2020-8203  since 2020-07-15  Prototype Pollution
```

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a line saying how many of your dependencies an
advisory names, then a row per dependency and advisory, its ecosystem and
then the package, its version and the advisory (its id, CVE, the day it was
published and its summary). `--json` gives the same report as one JSON
object.

Two things it reads:

- **Your lockfiles**, found in the folder (the box's pile, or any folder with
  `--from`): package-lock.json (npm), requirements.txt (the `name==version`
  pins, PyPI), poetry.lock (PyPI) and Cargo.lock (crates.io). A lockfile
  inside a `node_modules`, `vendor` or `.git` folder is skipped, so each
  dependency is counted once.
- **The advisory database** given with `--db`: a folder of OSV JSON files, the
  format both [osv.dev](https://osv.dev)'s per-ecosystem exports and the
  [GitHub advisory database](https://github.com/github/advisory-database) are
  published in. It reads every JSON file under the folder that looks like an
  OSV record, so either layout works. Download it yourself; this add-on never
  fetches.

| How a version is matched | |
|---|---|
| the advisory lists exact versions | the locked version is in that list |
| the advisory gives ranges | a plain numeric version (`1`, `2.4`, `3.1.6`) is compared to the range's `introduced` and `fixed`/`last_affected` bounds |
| a version or bound isn't plain numeric | not guessed at: listed apart, under "couldn't compare -- check by hand" |

The last row is the point: a prerelease, an epoch or a local tag is ordered
differently by each ecosystem, so rather than order it wrong -- in a tool
about security -- it names the pair and leaves the call to you. OSV's `GIT`
ranges are skipped for the same reason.

With no `--db` it lists the dependencies it found and stops: an inventory,
with nothing to match against, a row per dependency, and its first line says
no database was given:

```
advisories: populated, 2 locked dependencies; no advisory database given (--db), so none was matched
  PyPI  flask 2.0.1
  PyPI  requests 2.19.1
```

Exit codes, the kernel's: 0 no advisory names your dependencies, or there are
no locked dependencies to check (`empty`), or the inventory with no `--db`
(`populated`, nothing matched so nothing waits); 42 an advisory names one,
or one couldn't be compared, and waits on you (`populated`); 2 refused.

**Never:** fetches anything, or writes anything. It reads your lockfiles and
the database you point it at; the database is yours to keep current.
