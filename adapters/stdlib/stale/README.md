<!-- willow-addon
section: Trust and proof
line: Approved answers whose cited passage has changed or gone. Citations are content hashes, so it's exact.
source: box
added: 2026-10-23
writes: nothing
network: none
-->
# stale

Approved answers whose cited passage has changed or gone.

    python adapters/stdlib/stale/stale.py --box DIR

    stale   proposal:eb63d0addbe2…  'Six hours.'
            cited 63d9b600aca4, was at garden.md:1: no longer in your folder
    1 approved; 1 stale

A passage's id is the SHA-256 of its text, so when the cited words change or
their file goes, the id is nowhere in your folder, and this says so exactly.
The kernel keeps giving an approved answer whatever its sources do; this is
how you find out the ground moved under one.

**Exit codes:** 0 every approval holds; 42 one has gone stale and waits on
you; 2 refused (a record that doesn't verify).

**Uses:** the kernel's `read`, `sealed`, `config` and `chunks`.

**Never:** writes anything, or takes an approval back; that stays yours.
