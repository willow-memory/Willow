"""secrets_audit.py: passwords and keys sitting in plain files. Python 3.9+.

    python adapters/stdlib/secrets-audit/secrets_audit.py --box DIR
    python adapters/stdlib/secrets-audit/secrets_audit.py --from FOLDER

Every line of your files (the box's, or any folder's) that holds one of:

    password   a password you typed with its label: `password: hunter2`,
               `pw = widgets1998`; a label with no value, a comparison,
               or a placeholder ("changeme", "example") is left alone
    key        a private key block, or an AWS, GitHub, Slack, Google,
               Stripe or model-provider API key, or a JWT
    card       a card number that passes the Luhn check, or 4x4 groups
    iban       an IBAN whose mod-97 check holds
    ssn        a US social security number

is listed by file, line and kind, never with the value:

    notes/wifi.txt:3        password
    work/deploy.md:41       key

The shapes are the privacy add-on's (willow-bot's scrub, rebuilt there),
and the typed-password rule is willow-bot's own. A file is read the way the
kernel reads it, so what's listed is what an answer could have shown.
Email addresses and phone numbers aren't listed: they're in every file and
aren't secrets.

It only reads, and writes nothing. Exit codes, the kernel's: 0 nothing
found; 42 something found, which waits on you; 2 refused.
"""

from __future__ import annotations

import re
import sys
import types
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

KINDS = ("password", "key", "card", "iban", "ssn")
#: willow-bot's onescript/scrub.py typed_password: a label, a : or =, a value;
#: never a comparison, a label alone, or a value that names a source
_SKIP = r'(?:""|"?(?:None|null|NULL)"?(?![\w-])|"?env:|\$)'
TYPED_PASSWORD = re.compile(
    r"(?i)(?<![\w$])\$?(?:password|passwd|passphrase|pwd|pw)\b['\"]?\s*"
    r"(?<![=!<>])[:=](?!=)\s*"
    r"(?!" + _SKIP + r")"
    r"(\"[^\"\n]+\"|'[^'\n]+'|[^\s\"',;)}\]]+)"
)
PLACEHOLDER = re.compile(
    r"(?i)(your|example|xxxx+|placeholder|none|null|true|false|changeme|redacted|\*\*\*)"
)


def privacy():
    """The privacy add-on's module, from its source; None if it was deleted."""
    path = STDLIB / "privacy" / "privacy.py"
    if not path.is_file():
        return None
    mod = types.ModuleType("audit_privacy")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def typed_password(line: str) -> bool:
    return any(
        not PLACEHOLDER.search(m.group(1)) for m in TYPED_PASSWORD.finditer(line)
    )


def kinds_in(line: str, pv) -> list[str]:
    found: dict = {}
    if pv is not None:
        pv.scrub(line, found)
    got = [k for k in KINDS if k in found]
    if typed_password(line):
        got.insert(0, "password")
    return got


def audit(pile: Path, pv) -> list[tuple[str, int, str]]:
    """(path, line, kind) for every secret in the pile, in file order."""
    out = []
    for c in kernel.chunks(pile):
        for i, line in enumerate(c["text"].splitlines()):
            for kind in kinds_in(line, pv):
                out.append((c["path"], c["line"] + i, kind))
    return sorted(set(out))


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if args or len([v for v in opts.values() if v]) != 1 or len(opts) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if "--box" in opts:
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        pile = Path(kernel.config(box)["pile"])
    else:
        pile = Path(opts["--from"])
        if not pile.is_dir():
            print(f"refused: {pile} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    pv = privacy()
    if pv is None:
        print("note: the privacy add-on isn't here, so only typed passwords are looked for",
              file=sys.stderr)  # fmt: skip
    found = audit(pile, pv)
    if not found:
        print("No passwords, keys or card numbers found sitting in your files.")
        return kernel.ALIVE
    width = max(len(f"{p}:{n}") for p, n, _ in found)
    for path, n, kind in found:
        print(f"{f'{path}:{n}':<{width}}  {kind}")
    places = len({(p, n) for p, n, _ in found})
    print(f"\n{places} place{'s' if places != 1 else ''} hold a secret in plain text. "
          "A password manager is a safer home for them; the value was not shown here.")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
