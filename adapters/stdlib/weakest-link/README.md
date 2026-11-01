<!-- willow-addon
section: Trust and proof
line: Each answer's inputs marked measured, fitted or assumed, and the result worth its weakest input, never an average.
source: new
added: 2026-11-01
writes: nothing
network: none
tags: no-install, offline, read-only, trust
-->
# weakest-link

Each approved answer, worth the weakest input it cites.

    python adapters/stdlib/weakest-link/weakest_link.py --box DIR

    assumed  proposal:0a6fde95…  'Six hours.'
             assumed   garden.md:1   <- the weakest: fix this first
             measured  sun.md:3
    1 approved: 0 measured, 0 fitted, 1 assumed, 0 unmarked

A passage says what it rests on with a line in your file, such as
`provenance: measured`, `provenance: fitted` or `provenance: assumed`, in any
case and with `=` or `:`. These are **states, not a score**:

| state | means |
|---|---|
| measured | it traces to something a person can look up |
| fitted | a model calibrated against measured values |
| assumed | someone asserted it; nothing has checked it |

An approved answer is worth the **weakest** state among the passages it
cites, never an average. One assumed input and the whole answer is assumed,
however many measured ones sit beside it. Of all its inputs, the weakest ones
are the ones to fix first, and they are flagged.

**Absence is a value.** A cited passage that says nothing is `unmarked`, and
so is any answer that cites one, or that cites a passage no longer in your
folder. It is never quietly read as `assumed`. "No claim" and "a weak claim"
are different facts. A passage marked twice is worth its weaker mark. An
approval whose proposal file isn't the bytes that were sealed is `broken`,
shown with why and counted, as [stale](../stale/) shows it.

It reads the marks you wrote. It doesn't decide what is measured. A line that
says `provenance: measured` over a guess is a wrong mark in your file, and
this can't see that.

**From:** the SAFE App Store's field-acoustics (its provenance report) and
kitchen-pudding (its weakest-link rule), rebuilt over the kernel's approvals.

**Exit codes:** 0 every approval is measured, or there are none; 42 an
approval rests on something weaker, unmarked, gone or broken, and waits on
you; 2 refused (a record that doesn't verify).

**Uses:** the kernel's `read`, `sealed`, `standing`, `config` and `chunks`.

**Never:** writes anything, marks anything, or takes an approval back; that
stays yours.
