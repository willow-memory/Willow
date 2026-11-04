<!-- willow-addon
section: Trust and proof
line: Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact.
source: box
added: 2026-10-23
writes: nothing
network: none
role: page
output: report
-->
# stale

Approved answers whose cited passage has changed or gone.

    python adapters/stdlib/stale/stale.py --box DIR [--json]

    stale: populated, 1 approved; 1 stale
    ## proposal:eb63d0addbe2…  'Six hours.'
      garden.md:1  cited 63d9b600aca4: no longer in your folder

It prints [a report](../ci/README.md#the-report-contract), the shape every
report add-on shares: a line counting the approvals and the stale ones, then
a group per approval that doesn't hold, each row where a cited passage was
and then its id. `--json` gives the same report as one JSON object. When
every approval holds, or there are none, it is empty: `stale: empty, 2
approved; 0 stale`.

A passage's id is the SHA-256 of its text, so when the cited words change or
their file goes, the id is nowhere in your folder, and this says so exactly.
The kernel keeps giving an approved answer whatever its sources do; this is
how you find out the ground moved under one.

An approval's cited passages are read from its proposal file, so the file has
to be what you approved. When it isn't (missing, or no longer the bytes the
key signed) the approval is a row of its own, first, marked `broken` with
why, never read for its cites, and counted:

    stale: populated, 1 approved; 0 stale; 1 broken
      proposal:0a6fde95fa41…  broken: its proposal file is not the bytes that were sealed

**Exit codes:** 0 every approval holds, or there are none (empty); 42 one has
gone stale or broken and waits on you (populated); 2 refused (a record that
doesn't verify).

**Uses:** the kernel's `read`, `sealed`, `standing`, `config` and `chunks`.

**Never:** writes anything, or takes an approval back; that stays yours.
