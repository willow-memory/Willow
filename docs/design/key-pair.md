# Design note: the seal by a key pair

**Status: a design, drafted 2026-11-26, not built.** Drafted by an AI session
from what the maintainer decided in one conversation; their rulings are
marked as theirs. Everything else is the session's reading, theirs to cut.

## Why

A seal is proved today by HMAC-SHA-256 under the person's key
(`kernel.proof`). An HMAC is checked with the same secret that made it, so
`sealed()` reads the key on every question, every `verify` and every `out`.
That ties the key to the account that asks questions: wherever the record is
read, the key must be readable too. An assistant runs as the person, so code
it writes can read the key, and every guard that stands in the way judges
words, which code gets past.

The one guarantee words can't give is the system's: the key in a file the
person's account can't read, owned by an account of its own (the keyholder).
With an HMAC that breaks every question, since nothing running as the person
could check a seal any more. With a key pair it doesn't: the private half
signs, and stays with the keyholder; the public half checks, and sits in the
box for anyone. **The maintainer's ruling, 2026-11-26: the key pair is the
way.**

## The law

CONST-0-4 asks for "a human cryptographic authorization" and names no
algorithm, so its words stand. The body that names HMAC changes with this.

## The design

1. **Ed25519 (RFC 8032).** A seal or a decline is signed over the bytes its
   HMAC covers now: the act, a unit separator, the subject, and for a seal
   that names its question, another separator and that question's bite key.
   The row keeps `proof` for an HMAC and carries `sig` for a signature; a
   row has one or the other.
2. **Two halves.** `kernel.json` holds `pub` (the public half, hex), which
   checks every seal for anyone, with no secret. `key` names the private
   half's file, readable by its owner alone (`read_key`'s rule, unchanged),
   which may be the keyholder's. Signing needs the private half; checking
   never does.
3. **The crossing (the maintainer's ruling, 2026-11-26: old seals sit as
   sealed).** A record with HMAC seals moves to a key pair by one row,
   `rekey`: whoever holds both keys at that moment checks every seal and
   decline before it under the old secret, and signs, with the new private
   half, the hash of the chain up to that row and the subjects it vouches
   for. After it, a row before the `rekey` stands on the `rekey` row's
   signature, checked with `pub`; the old secret can be retired, and nothing
   is re-sealed. `share` already keeps a chain of rotations, each signed by
   both its keys: the same shape.
4. **One rule for checking, in every port.** Ed25519 libraries differ on
   edge cases ("Taming the many EdDSAs", 2020), and a port that accepts what
   another refuses is a forged seal on one of them. So the rule is written
   once and every port holds to it:
   - refuse S ≥ L, and an A or R whose y is ≥ p;
   - refuse the eight small-order encodings for A and R;
   - check `[S]B = R + [k]A` without the cofactor;
   - check `pub` once, when it is installed: it decodes and is of prime order.
   Held by RFC 8032's vectors, Wycheproof's EdDSA vectors and C2SP's CCTV
   edge cases, each port's expected answer made by the Python rule.
5. **Speed.** A signature check in pure Python is about 2.5 ms (measured
   2026-11-21, in the Provider's docs/OPEN.md), where an HMAC is 0.003 ms,
   and today every question checks every seal. So:
   - `bite` checks only the seal rows that could answer its question
     (`asked == k`), one or none at any size of record;
   - a checked row is remembered by its hash within one process, never on
     disk (the kernel keeps no index on purpose, LIMITS.md, and a file of
     "checked" rows would be one a forged seal could be written into).

## The ports

| Port | Ed25519 in its standard library | What it takes |
|---|---|---|
| Python (`kernel.py`) | no | `adapters/stdlib/share/ed25519.py`'s code, in the kernel, with the rule above |
| Go | `crypto/ed25519` | a check of the bytes in front, for the rule |
| TypeScript (Node) | `crypto.verify` with `ed25519` | the same |
| Java | from JDK 15 | its floor from JDK 11 to 15, or code of its own |
| Rust | none (no crates) | its own, from Go's, as the port already is; and SHA-512 |
| C# (.NET 8) | none | its own |

Checking is every port's; signing need be only the Python kernel's at first,
since a seal is made once, at the person's click.

## The stages

1. The Python kernel: `pub`, signing and checking with the rule, `sig` rows,
   `verify`, `seal` and `decline`, the `rekey` crossing, and the speed above.
   New vectors for each.
2. The ports, one at a time, each passing every vector and verifying boxes
   the others wrote (`vectors/compare.py`).
3. The Provider: account A, the seal page and the kernel's `seal` running as
   the keyholder, the record's folder shared by a group (**the maintainer's
   ruling, 2026-11-26**: shared by a group, not the keyholder's alone).
4. Later: the private half in a password manager or an SSH agent that asks
   the person on every signature, the signed bytes holding the row's hash and
   a nonce the seal page shows (design D in the Provider's docs/OPEN.md); and
   a passkey (design C), which signs with ECDSA P-256, a second algorithm.

## Ruled

- **A record with a key pair and HMAC seals not yet crossed: `seal` signs
  beside them (the maintainer, 2026-11-26).** New seals and declines carry
  `sig`; the old ones keep `proof` until the `rekey` row. Until then,
  checking the old ones still needs the old secret, so the key leaves the
  person's account only once they have crossed.

## Open

- What the keyholder's private-half file is called and where it lives by
  default.
- Whether a port that can't yet check signatures refuses a box with `pub`, or
  reads its HMAC rows only.
