"""pgp.py: sign an export or a report with your own PGP key, and check one.

    python adapters/deps/pgp/pgp.py sign FILE --to SIGNATURE [--key ID]
    python adapters/deps/pgp/pgp.py verify FILE SIGNATURE

Needs python-gnupg (BSD-3-Clause), pinned in requirements.txt beside this
file, and the gpg program (GPL, run, never linked) with your key in it:

    pip install -r adapters/deps/pgp/requirements.txt

`sign` makes a detached, ASCII-armoured signature of FILE and writes it to
SIGNATURE, which must not exist yet, in a folder that does. Your own gpg
makes it, with your default key or the one --key names, and asks you for
the passphrase itself: this never sees your passphrase or your secret key.
It is gpg's standard form, so anyone with your public key can check it,
with gpg or anything else that reads OpenPGP:

    gpg --verify SIGNATURE FILE

`verify` checks one the same way, through your gpg's keyring, and says
whose signature it is and when it was made, or that it is not good.

A signature is yours to make: an export of approved answers signed is that
file vouched for by you, not a willow approval. Nothing here writes a seal,
and willow's own key is never read.

It writes only SIGNATURE, and goes nowhere: gpg keeps its own keyring, and
looks up no key online unless your own gpg.conf tells it to. Without
python-gnupg or gpg it refuses and names the install; it never skips
quietly. Exit codes, the kernel's: 0 signed, or a good signature; 42 not a
good one (a changed file, an unknown key); 2 refused.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/pgp/requirements.txt"
PROGRAM = "the gpg program: apt install gnupg, or brew install gnupg"


def gpg():
    """python-gnupg's handle on your own gpg, or a refusal's reason."""
    try:
        import gnupg
    except ImportError:
        return None, f"pgp needs python-gnupg: {INSTALL}"
    try:
        return gnupg.GPG(), None
    except (OSError, ValueError, RuntimeError):  # no gpg program to run
        return None, f"pgp needs {PROGRAM}"


def mine(g, want: str) -> list[dict]:
    """Your secret keys that `want` names: by fingerprint, by the key id it
    ends with, or by a part of a user id (a name, an address)."""
    w = want.strip().lower().removeprefix("0x")
    out = []
    for k in g.list_keys(True):
        fpr = k["fingerprint"].lower()
        if (len(w) >= 8 and fpr.endswith(w)) or any(w in u.lower() for u in k["uids"]):
            out.append(k)
    return out


def sign(path: Path, out: Path, key: str | None) -> int:
    if not path.is_file():
        print(f"refused: {path} is not a file", file=sys.stderr)
        return kernel.REFUSED
    if out.exists():
        print(
            f"refused: {out} is there already; a signature never overwrites",
            file=sys.stderr,
        )
        return kernel.REFUSED
    if not out.parent.is_dir():
        print(f"refused: no folder {out.parent}", file=sys.stderr)
        return kernel.REFUSED
    g, why = gpg()
    if g is None:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    allowed = None
    if key:
        found = mine(g, key)
        if len(found) != 1:
            print(f"refused: {len(found) or 'no'} secret key{'s' * (len(found) != 1)} "
                  f"match {key!r}; name one by its fingerprint", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        key = found[0]["fingerprint"]
        allowed = {key} | {
            sub[2] for sub in found[0].get("subkeys", []) if len(sub) > 2
        }
    with open(path, "rb") as f:
        got = (
            g.sign_file(f, keyid=key, detach=True)
            if key
            else g.sign_file(f, detach=True)
        )
    if not got.fingerprint:
        said = (got.status or "gpg made no signature").strip()
        print(
            f"refused: {said} (no secret key, or no passphrase given)", file=sys.stderr
        )
        return kernel.REFUSED
    if allowed is not None and got.fingerprint not in allowed:
        # gpg falls back to the default key when it can't use the one asked
        print(f"refused: gpg signed with {got.fingerprint}, not the key asked for; "
              "nothing written", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    with open(out, "x", encoding="ascii", newline="\n") as f:
        f.write(str(got))
    print(f"signed {path.name} with key {got.fingerprint} to {out}")
    print(f"check: gpg --verify {out} {path}")
    return kernel.ALIVE


def verify(path: Path, sig: Path) -> int:
    for p in (path, sig):
        if not p.is_file():
            print(f"refused: {p} is not a file", file=sys.stderr)
            return kernel.REFUSED
    g, why = gpg()
    if g is None:
        print(f"refused: {why}", file=sys.stderr)
        return kernel.REFUSED
    with open(sig, "rb") as f:
        got = g.verify_file(f, data_filename=str(path))
    if not got.valid:
        said = (got.status or "not a signature").strip()
        print(f"not good: {said}")
        return kernel.ESCALATE
    when = datetime.fromtimestamp(int(got.timestamp), timezone.utc)
    print(f"good signature by {got.username}, key {got.fingerprint}")
    print(f"made {when.strftime('%Y-%m-%dT%H:%M:%SZ')}; your trust in the key: "
          f"{(got.trust_text or 'none').removeprefix('TRUST_').lower()}")  # fmt: skip
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    if len(argv) in (4, 6) and argv[0] == "sign" and argv[2] == "--to":
        key = None
        if len(argv) == 6:
            if argv[4] != "--key" or not argv[5]:
                print(__doc__.split("\n\n")[1], file=sys.stderr)
                return kernel.REFUSED
            key = argv[5]
        return sign(Path(argv[1]), Path(argv[3]), key)
    if len(argv) == 3 and argv[0] == "verify":
        return verify(Path(argv[1]), Path(argv[2]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
