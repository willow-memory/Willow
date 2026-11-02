<!-- willow-addon
section: Reading more kinds of files
line: An Almanac's catalog.json (climate, health, civic and the rest): each public dataset's description and source as passages, with when its link was last checked.
source: new
added: 2026-10-31
writes: to
network: none
-->
# almanac

An [Almanac](https://github.com/almanac-data)'s catalog of public datasets, as
plain text the kernel can ask questions of.

    python adapters/stdlib/almanac/almanac.py mirror --from FOLDER --to MIRROR

An Almanac is a catalog, not a host: each vertical (climate, health, civic,
education and the rest) is a repository of reviewed entries pointing at
public datasets where their publishers keep them, and publishes a generated
catalog.json. Clone the verticals you want into one folder and point this
at it; every file named catalog.json under FOLDER is read.

Each entry becomes one paragraph, sorted by id:

    Tide Gauge Records (tide-gauge-records)
    Hourly sea level at the harbour gauge.
    publisher: Made-Up Statistics Office
    source: https://stats.example.org/tide-gauge-records
    status: live since 2026-07-01 (curator); licence: CC-BY-4.0
    link last checked: 2026-10-30, reachable, HTTP 200
    coverage: Example Island; 1990-present; annual
    topics: sea-level, tides

The file's first line names the catalog and how many entries it holds. `link
last checked` is what the almanac's own link checker last wrote: reachable
with its HTTP status, `no response`, or `not yet probed`. `status` is the
curator's word, kept as written; this never decides whether a dataset is
alive. A field an entry lacks leaves its line out.

Where the entry has them, three more kinds of line follow `link last
checked`. `fingerprint` says which baselines the almanac took while the
source was live (`full`, the whole file's hash; `lead`, its title and opening
text) and when. Each `archived copy` is one of the entry's recovery copies,
in the almanac's own order: how verifiable it is, where it is, when it was
captured, and its address. A copy marked `excluded` is never shown. An entry
that isn't a dataset says its `kind` (a `document`, say), and one in a
`collection` names it. To fetch one of those copies into your folder, use
[almanac-keep](../almanac-keep/).

Each catalog is written to MIRROR at the same relative path with .txt added:
`FOLDER/<vertical>/catalog.json` becomes `MIRROR/<vertical>/catalog.json.txt`.
A file that isn't a catalog (not JSON, or no `entries` list) is skipped and
counted.
Point the kernel at MIRROR to ask questions of it:
`kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) in
`almanac.py`; the tests run the kernel's `init` and `bite` on the mirror
(`kernel.py`). No kernel function is called by the mirror itself.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, fetches a catalog or a dataset, or changes an entry's status.
