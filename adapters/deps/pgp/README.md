<!-- willow-addon
section: Trust and proof
line: Signs exports and reports with your PGP key, verifiable anywhere.
source: new
added: 2026-10-30
needs: the gpg program, run not linked, and python-gnupg; GPL, BSD-3-Clause
floor: python-gnupg 0.4.6
writes: to
network: none
tags: needs-install, offline, writes-output, trust
-->
# pgp

An export or a report, signed with your own PGP key, so anyone with your
public key can check it came from you and hasn't changed.

    pip install -r adapters/deps/pgp/requirements.txt
    python adapters/stdlib/export/export.py --box DIR > answers.md
    python adapters/deps/pgp/pgp.py sign answers.md --to answers.md.asc [--key ID]
    python adapters/deps/pgp/pgp.py verify answers.md answers.md.asc

**Signing is yours.** Your own gpg makes the signature, with your default
key or the one `--key` names (by fingerprint, key id, name or address), and
asks you for its passphrase itself: this never sees your passphrase or your
secret key. A `--key` that names none of your keys, or more than one, is
refused; and since gpg falls back to your default key when it can't use the
one asked, a signature by any other key than the one named is refused and
not written.

**Verifiable anywhere.** The signature is detached and ASCII-armoured,
OpenPGP's standard form: `gpg --verify answers.md.asc answers.md` checks it
on any machine with your public key, no willow needed. `verify` checks it
the same way and says whose it is and when it was made; a changed file, or
a key your keyring doesn't have, is not good. On an export of a demo box,
signed and checked at the pins and at the floor, gpg itself said "Good
signature" both times.

**Not an approval.** A signed export is that file vouched for by you; it
seals nothing in willow, and willow's own key is never read.

**It writes only SIGNATURE**, which must not be there yet, in a folder that
is: nothing is overwritten and no folder is made. gpg keeps its own keyring
and agent, as it always does; looking a key up online is gpg's to do, and
only if your own gpg.conf tells it to.

**Without gpg or python-gnupg** it refuses and names the install: exit 2,
never a quiet skip.

**Uses:** the kernel's exit codes: 0 signed, or a good signature; 42 not a
good one; 2 refused.

**Never:** reads willow's key or your secret key, writes a seal, writes
anything but SIGNATURE, or goes online itself.
