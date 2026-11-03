<!-- willow-addon
section: Ways to use it
line: Sealed answers sent to someone, checkable by them and by whoever they pass them on to, without giving anyone the folder.
source: new
added: 2026-11-03
writes: record, to
network: none
-->
# share

Answers you sealed, packed for one person, signed so they (and anyone they
pass it on to) can check who sent what, and passed on in layers that nobody
along the way can change. Each hop is a row on both people's chains.

    python adapters/stdlib/share/share.py id      --to IDFILE
    python adapters/stdlib/share/share.py send    --box DIR --id IDFILE --answer proposal:<sha256>[,...] --for KEY --to FILE [--note TEXT] [--replaces PACKAGE]
    python adapters/stdlib/share/share.py receive --box DIR --id IDFILE --package FILE
    python adapters/stdlib/share/share.py forward --box DIR --id IDFILE --package FILE --for KEY --to FILE [--note TEXT] [--replaces PACKAGE]
    python adapters/stdlib/share/share.py check   --package FILE
    python adapters/stdlib/share/share.py log     --box DIR
    python adapters/stdlib/share/share.py witness --box DIR --package FILE[,...]
    python adapters/stdlib/share/share.py rotate  --box DIR --id IDFILE --to NEWIDFILE

`send`, `forward`, `receive` and `rotate` take `--now TS` as the kernel does.

**Why a key of its own.** A seal is an HMAC under your key: only that key
can check it, so a seal can't travel without giving the key away, and with
it the power to seal. `id` makes an identity instead, an Ed25519 key pair:
the secret half stays in IDFILE, the public half (KEY, 64 hex) is printed
for you to give people. An IDFILE that is your seal key is refused by name,
before it is opened.

**What a package holds.** For each answer: its text, its reason, the
passages it cites by fingerprint and place (`notes.md:12`), never their
text, and the record's proposal and seal rows for it; then where your
record stood (its first hash, its length, its last hash), who it is for,
your note, and your signature over all of it. A row in a package is checked
against its own hash, so it is the row your chain linked; that it is in your
chain only your record can show, to someone you let check it (`tip-pin`
says where it ended).

**Receiving.** `receive` checks every layer, and prints each sender's key and
whether a package that held came from it before. It writes a `received` row
whatever it found, `good`, `not-for-you` (it holds, but is addressed to
someone else) or `broken`, so what came in and what didn't hold are both on
your chain; the same package twice writes one row. A received answer is
never your approval: only you seal, through the kernel, and the kernel
seals only answers made from your own files.

**Forwarding.** `forward` passes on a package you received and that held,
inside a layer of your own: your note, your `received` row for it, your
signature. A forward by anyone else than the one the inner package was for
is broken, and so is any change to an inner layer.

**Corrections.** `--replaces` names a package you sent before. When one
arrives, `receive` says which package it replaces and, if you passed that
one on, to whom, and the package to name in your own `--replaces`: a
correction follows the same path the first one took, a hop at a time, and
everyone's first seal and first receipt stay on their chains.

**willow-gate's rules.** Three come from
[willow-gate](https://github.com/willow-memory/willow-gate), the agents'
check-in gate:

- *The label is inside the signature.* Every layer says what it proves,
  "who signed each layer, the answers and rows it shows, and where the
  sender's record stood; never that the record holds nothing else", and a
  layer that says anything else is broken, so the label can be neither
  stripped nor raised.
- *A key is rotated, never swapped.* `rotate` writes a new identity to
  NEWIDFILE and a `rotated` row naming both keys, signed by the old key and
  by the new. Every package after it carries the record's rotations, so
  whoever had the old key sees the new one as the same person. A record
  speaks with one key at a time: `send`, `forward` and `receive` refuse any
  other, the rotated-away one included. A package for a key you rotated from
  is still yours, and so is forwarding it.
- *Trust is earned, not claimed.* `receive` names each key's rung on your
  own chain, willow-gate's names counted from that key's packages that held
  (through its rotations): `rookie` until one has, `steady` from one,
  `veteran` from five. A broken package counts for nothing either way: its
  sender is only a claim. A chain you know arriving with a key it never
  rotated to is said loudly.

**The people as witnesses.** Every layer is signed over where its sender's
record stood, and its `sent` row, with the key that signed, is the next row
on that record. So everyone who keeps a package holds a signed pin of the
sender's record that the sender can't reach: what `tip-pin` asks for, in
the hands of the people you sent to. `witness` holds a box's record to the
packages others kept, every layer signed for that chain, inner ones too:

    holds        package:395adab752a3… at row 13: sent to 8f81cbe42a8d…, 2026-03-12T14:48:00Z
    rewritten    package:395adab752a3… at row 13: row 12 is not the row it was signed after
    cut short    package:9a04ad57e06f… at row 17: signed at 17 rows; the record has 12

A record rewritten from some row on and re-hashed, which `verify` can't
see, is `rewritten` for anyone holding a package sent after that row; one
cut short is `cut short`. A layer signed by a key the record never sent
with is said as such, beside its verdict: either the record lost those rows,
or someone else signed for this chain, and it accuses no one by itself. A
package that doesn't hold proves nothing. It covers only what was sent: rows
after the last package anyone kept have no witness yet.

**What it can't tell you.** That KEY is the person you think it is: a key is
first met somewhere (in person, on a card, from someone you trust), and
`receive` only says whether you have had it before. And it can't stop a
copy: a package's text pasted somewhere else is just text, without its
proof.

**The signatures** are Ed25519 (RFC 8032), in `ed25519.py`, standard
library only. It is held to RFC 8032's test vectors and to vectors made
with an audited library, and checked against that library on random keys
and messages while it was written. It is not constant-time: fine on your
own machine, not for a server signing for strangers.

**Exit codes:** 0 done (a rotation written), a package that holds, or a record every witness
holds to; 42 a package that doesn't hold or isn't for you, or a record a
witness doesn't hold to, and waits on you; 2 refused.

**Uses:** the kernel's `read`, `append`, `sealed`, `standing`,
`subject_of`, `canon`, `h256`, `config` and its exit codes.

**Never:** reads your seal key; writes a seal; goes online (how a package
travels is yours: mail, a stick, a shared folder); writes anything but
FILE or IDFILE, new, in a folder that exists, outside the box and your
folder, and the record through the kernel. IDFILE is readable only by you.

**Try it** on the Johnson case: five people, one report, a forged copy and a
correction, in [demo/johnson](../../../demo/johnson/).
