"""privacy.py: what a question prints, with personal data and keys withheld.

    python adapters/stdlib/privacy/privacy.py bite --box DIR [--now TS] "your words"
    python adapters/stdlib/privacy/privacy.py scrub < FILE

`bite` runs the kernel's own bite (the record and the exit code are the
kernel's) and withholds, in every passage and approved answer it prints:

    email, phone            an address; a number with an area code, or +country
    card                    13 to 19 digits that pass the Luhn check, or 4x4 groups
    iban                    an IBAN whose mod-97 check holds
    ssn                     a US social security number, labelled or 3-2-4
    ip                      an address that names a machine (not 127.x or 0.0.0.0)
    key                     a private key block, and AWS, GitHub, Slack, Google,
                            Stripe and model-provider API keys, and a JWT

Each is replaced by `[withheld: KIND]`, and the output says how many of each
it withheld (`"withheld": {"phone": 2}`). `scrub` does the same to any text.

What it misses, said rather than hidden: a street address, and a person's name
on its own (a name is only a word; the kernel's demo found both getting
through). Checksums keep it from crying wolf on order numbers and serials.

The shapes are willow-bot's `onescript/scrub.py` (its `pii` and `credentials`
sets), rebuilt here for a person's own folder: the same patterns, Luhn and
mod-97 checks, and the rule that loopback and unspecified addresses name no
one.

It never writes to the record (the kernel's bite row holds no words anyway),
and it never changes which passages are served, only what they show.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

MARK = "[withheld: {kind}]"

_PEM = r"(?:RSA |EC |OPENSSH |DSA |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?"
KEYS = [
    re.compile(rf"-----BEGIN {_PEM}-----.*?(?:-----END {_PEM}-----|\Z)", re.DOTALL),
    re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16,}"),
    re.compile(r"gh[posur]_[A-Za-z0-9]{36,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35,}"),
    re.compile(r"(?:sk|rk)_live_[0-9a-zA-Z]{16,}"),
    re.compile(r"sk-(?:ant-)?[A-Za-z0-9_\-]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{6,}\.eyJ[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{6,}"),
]
EMAIL = re.compile(r"[^\s@\"'<>()\[\],;:]+@[^\s@\"'<>()\[\],;:]+\.[A-Za-z]{2,}\b")
SSN = re.compile(
    r"\b(?:ssn|social security(?: number| no\.?)?)\b[\s#:.]*\d{3}-?\d{2}-?\d{4}\b"
    r"|\b\d{3}[-\s]\d{2}[-\s]\d{4}\b",
    re.IGNORECASE,
)
CARD_GROUPS = re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b")
CARD_BARE = re.compile(r"\b\d{13,19}\b")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b")
PHONE = re.compile(
    r"(?<![\d+])(?:\+?1[-.\s]?)?(?:\(\d{3}\)\s?|\d{3}[-.\s])\d{3}[-.\s]\d{4}(?!\d)"
    r"|\+[1-9]\d{6,14}(?![A-Za-z0-9])"
)
_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
IPV4 = re.compile(rf"(?<![\d.]){_OCTET}(?:\.{_OCTET}){{3}}(?![\d.])")
NOT_A_HOST = re.compile(r"^(?:127\.|0\.0\.0\.0$|255\.255\.255\.255$)")


def luhn(digits: str) -> bool:
    total = 0
    for i, d in enumerate(int(c) for c in reversed(digits)):
        total += (d * 2 - 9 if d * 2 > 9 else d * 2) if i % 2 else d
    return total % 10 == 0


def iban_ok(value: str) -> bool:
    s = value.replace(" ", "")
    if not 15 <= len(s) <= 34:
        return False
    return int("".join(str(int(c, 36)) for c in s[4:] + s[:4])) % 97 == 1


def scrub(text: str, found: dict) -> str:
    """`text` with every kind withheld; `found` counts each kind."""

    def hide(kind: str, keep=lambda v: False):
        def sub(m: re.Match) -> str:
            if keep(m.group(0)):
                return m.group(0)
            found[kind] = found.get(kind, 0) + 1
            return MARK.format(kind=kind)

        return sub

    for rx in KEYS:  # first: a key can hold digits that look like a phone
        text = rx.sub(hide("key"), text)
    text = EMAIL.sub(hide("email"), text)
    text = IBAN.sub(hide("iban", lambda v: not iban_ok(v)), text)
    text = SSN.sub(hide("ssn"), text)
    text = CARD_GROUPS.sub(hide("card"), text)
    text = CARD_BARE.sub(hide("card", lambda v: not luhn(v)), text)
    text = PHONE.sub(hide("phone"), text)
    text = IPV4.sub(hide("ip", lambda v: bool(NOT_A_HOST.match(v))), text)
    return text


def bite(argv: list[str]) -> int:
    got = io.StringIO()
    with contextlib.redirect_stdout(got):
        code = kernel.main(["bite", *argv])
    out = got.getvalue()
    try:
        doc = json.loads(out)
    except ValueError:  # a refusal: the kernel's words, untouched
        print(out, end="")
        return code
    found: dict = {}
    for s in doc.get("served", []):
        s["text"] = scrub(s["text"], found)
    if "answer" in doc:
        doc["answer"] = scrub(doc["answer"], found)
    doc["withheld"] = dict(sorted(found.items()))
    print(json.dumps(doc, ensure_ascii=False))
    return code


def main(argv: list[str]) -> int:
    if argv[:1] == ["bite"]:
        return bite(argv[1:])
    if argv == ["scrub"]:
        found: dict = {}
        sys.stdout.write(scrub(sys.stdin.read(), found))
        print(json.dumps({"withheld": dict(sorted(found.items()))}), file=sys.stderr)
        return kernel.ALIVE
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
