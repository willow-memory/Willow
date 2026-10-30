"""privacy.py: what a question prints, with personal data and keys withheld.

    python adapters/stdlib/privacy/privacy.py bite --box DIR [--now TS] "your words"
    python adapters/stdlib/privacy/privacy.py scrub < FILE

`bite` runs the kernel's own bite (the record and the exit code are the
kernel's) and withholds, in every passage and approved answer it prints:

    email, phone            an address; a number with an area code, or +country,
                            or a national one from 0 in groups (0113 555 0122)
    account                 a bank number after its label: sort code, account
                            number, acct, a/c or routing; the label is kept
    card                    13 to 19 digits that pass the Luhn check, or 4x4 groups
    iban                    an IBAN whose mod-97 check holds
    ssn, itin               a US social security number, labelled or 3-2-4; an
                            ITIN, 9xx-7x-xxxx in its ranges
    ein                     a US employer number, 12-3456789
    birthdate, passport,    a number after its label (DOB, passport no., driver's
    licence, medical, case  licence, MRN, case or claim no.); the label is kept,
                            and the number holds a digit, so "passport renewal"
                            and "claim no longer open" are prose and left
    ip                      an address that names a machine (not 127.x or 0.0.0.0,
                            and an IPv6 one of three groups or more)
    mac, wallet, location   a MAC address; a Bitcoin or Ethereum address; a
                            latitude and longitude to four places
    discord                 a Discord mention, <@ and the person's id
    key                     a private key block; AWS, GitHub (fine-grained too),
                            Slack, Google, Stripe, Groq, Hugging Face, Cerebras,
                            xAI and model-provider API keys; a JWT; a Discord
                            bot token
    password                one typed after its label (`password: hunter2`,
                            `pw = widgets1998`, `pw Wendouree#14`), the second
                            half of a login pair (`ana@example.org / Tide2024!`,
                            `HomeNet / x7Kp9q2z`), and, in a file whose name
                            says it's a list of them (passwords.txt, logins.md),
                            every value that looks like one

Each is replaced by `[withheld: KIND]`, and the output says how many of each
it withheld (`"withheld": {"phone": 2}`). `scrub` does the same to any text,
except the password-list rule, since a pipe has no file name.

A password's label is kept, so the line still reads. A value only looks like
a password with six characters or more, a letter and a digit:
"password policy", "pw reset" and "and / or" are prose and left alone, and so
is a placeholder ("changeme", "example", "None") or a value that names where
the password comes from (`env:WIFI`, `$PASS`).

What it misses, said rather than hidden: a street address, and a person's name
on its own (a name is only a word; the kernel's demo found both getting
through). A home path's account name is transcript-redact's to take out, not
this. Checksums keep it from crying wolf on order numbers and serials; an EIN
has none, so an order number written 12-3456789 is withheld too.

The shapes are willow-bot's `onescript/scrub.py` (its `pii` and `credentials`
sets), rebuilt here for a person's own folder: the same patterns, Luhn and
mod-97 checks, and the rule that loopback and unspecified addresses name no
one. Two differences: a labelled number must hold a digit (the one script's
takes the word after "case number" or "passport"), and a GitHub fine-grained
token, which the one script misses, is a key.

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
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),  # a fine-grained GitHub token
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35,}"),
    re.compile(r"(?:sk|rk)_live_[0-9a-zA-Z]{16,}"),
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),  # Groq
    re.compile(r"hf_[A-Za-z0-9]{20,}"),  # Hugging Face
    re.compile(r"csk-[A-Za-z0-9]{20,}"),  # Cerebras
    re.compile(r"xai-[A-Za-z0-9]{20,}"),  # xAI
    re.compile(r"sk-(?:ant-)?[A-Za-z0-9_\-]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{6,}\.eyJ[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{6,}"),
    # a Discord bot token
    re.compile(r"[MN][A-Za-z0-9_-]{23,26}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}"),
]
_NO = r"(?:\s*(?:no\b\.?|number\b|#))?[\s#:.]*"
#: a number that holds a digit, so "passport renewal" is prose and left
_NUM = r"(?=[A-Za-z0-9-]*\d)[A-Za-z0-9-]"
#: a number after its label, the label kept so the line still reads
LABELLED = [
    (
        "birthdate",
        re.compile(
            r"(?i)(?P<label>\b(?:dob\b|d\.o\.b\.?|date of birth|birth\s?date|born(?:\s+on)?\b)"
            r"[\s:.]*)(?P<num>\d{1,4}[-/]\d{1,2}[-/]\d{1,4}|[A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})"
        ),
    ),
    (
        "passport",
        re.compile(rf"(?i)(?P<label>\bpassport{_NO})(?P<num>{_NUM}{{6,9}})\b"),
    ),
    (
        "licence",
        re.compile(
            rf"(?i)(?P<label>\b(?:driver'?s?\s+licen[cs]e|DL\b){_NO})(?P<num>{_NUM}{{5,15}})\b"
        ),
    ),
    (
        "medical",
        re.compile(
            rf"(?i)(?P<label>\b(?:MRN|medical record){_NO})(?P<num>{_NUM}{{5,12}})\b"
        ),
    ),
    (
        "case",
        re.compile(
            r"(?i)(?P<label>\b(?:case|claim)\s*(?:no\b\.?|number\b|#)[\s#:.]*)"
            rf"(?P<num>{_NUM}+)\b"
        ),
    ),
]
#: 9xx-7x-xxxx in the ITIN's ranges; read before the SSN, which it also looks like
ITIN = re.compile(r"\b9\d{2}[-\s](?:5\d|6[0-5]|7\d|8[0-8]|9[0-24-9])[-\s]\d{4}\b")
EIN = re.compile(r"\b\d{2}-\d{7}\b")
WALLET = re.compile(r"\b(?:bc1[a-z0-9]{25,59}|0x[0-9a-fA-F]{40})\b")
MAC = re.compile(r"(?<![\w:-])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![\w:-])")
#: a latitude and longitude to four places or more: where someone was
LOCATION = re.compile(r"(?<![\d.])-?\d{1,2}\.\d{4,},\s*-?\d{1,3}\.\d{4,}(?![\d.])")
DISCORD_USER = re.compile(r"<@!?\d{17,20}>")
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
# a national number from its trunk 0, in groups: 0113 555 0122, 07700 900123
PHONE_NATIONAL = re.compile(
    r"(?<![\d+])0\d{2,4}[-.\s]\d{3,4}(?:[-.\s]?\d{3,4})?(?![\d-])"
)
ACCOUNT = re.compile(
    r"(?P<label>\b(?:sort[\s-]?code|(?:bank\s+)?account(?:\s+(?:number|no\.?|#))?"
    r"|acct(?:\s+no\.?)?|a/c|routing(?:\s+number)?)[\s:#.]*)(?P<num>\d[\d-]{4,}\d)\b",
    re.IGNORECASE,
)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
IPV4 = re.compile(rf"(?<![\d.]){_OCTET}(?:\.{_OCTET}){{3}}(?![\d.])")
IPV6 = re.compile(
    r"(?<![\w:])(?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}(?![\w:])"
    r"|(?<![\w:])(?:[0-9A-Fa-f]{1,4}:){1,6}:(?:[0-9A-Fa-f]{1,4}:){0,5}[0-9A-Fa-f]{1,4}(?![\w:])"
)


def v6_host(value: str) -> bool:
    """An IPv6 address with three groups or more: `a::b` is C++, not a host."""
    return len([g for g in value.split(":") if g]) >= 3


NOT_A_HOST = re.compile(r"^(?:127\.|0\.0\.0\.0$|255\.255\.255\.255$)")
#: what a password looks like: six or more characters, a letter and a digit,
#: no space; so a word of prose, "lose!!" included, never is one
SECRET = r"(?=[^\s/,;()]*[A-Za-z])(?=[^\s/,;()]*\d)[^\s/,;()]{6,}"
_LABEL = r"(?:password|passwd|passphrase|passcode|pwd|pw)"
_SOURCE = r'(?:""|"?(?:None|null|NULL)"?(?![\w-])|"?env:|\$)'
#: willow-bot's onescript/scrub.py typed_password: a label, a : or =, a value;
#: never a comparison, a label alone, or a value that names a source
TYPED = re.compile(
    rf"(?i)(?P<label>(?<![\w$])\$?{_LABEL}\b['\"]?\s*(?<![=!<>])[:=](?!=)\s*)"
    rf"(?!{_SOURCE})(?P<pw>\"[^\"\n]+\"|'[^'\n]+'|[^\s\"',;)}}\]]+)"
)
#: the label, a space, the value: `pw Wendouree#14`
SPACED = re.compile(rf"(?i)(?P<label>(?<![\w$]){_LABEL}[ \t]+)(?P<pw>{SECRET})(?!\S)")
#: a login, a slash with a space each side, a password: `ana@example.org / Tide2024!`
PAIR = re.compile(rf"(?P<label>(?<![^\s:])[^\s/:]+[ \t]+/[ \t]+)(?P<pw>{SECRET})(?!\S)")
#: in a file of passwords, every value that looks like one, wherever it is on
#: the line: `ancestry: Considine1911`, `(changed -> Wendouree#15)`
LISTED = re.compile(rf"(?P<label>)(?<![^\s:(>])(?P<pw>{SECRET})(?![^\s,;)])")
PLACEHOLDER = re.compile(
    r"(?i)(your|example|xxxx+|placeholder|none|null|true|false|changeme|redacted|\*\*\*)"
)
#: a file named as a list of them: passwords.txt, my-logins.md, credentials-old;
#: the singular only on its own, so password-reset-steps.md is notes, not a list;
#: a word between separators holds none, so a name of many `_0`s is read once
LIST_NAME = re.compile(
    r"(?i)^(?:my[ _-]?)?(?:(?:passwords|logins|credentials)(?:[ _-][^\W_]+)*|password|passwd)$"
)


def password_list(path: str) -> bool:
    """Whether a file's name says it is a list of passwords."""
    return bool(LIST_NAME.search(Path(path).stem))


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


def scrub(text: str, found: dict, listed: bool = False) -> str:
    """`text` with every kind withheld; `found` counts each kind. `listed`:
    the text is from a file of passwords (`password_list`)."""

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

    def password(m: re.Match) -> str:
        if PLACEHOLDER.search(m.group("pw")):
            return m.group(0)
        found["password"] = found.get("password", 0) + 1
        return m.group("label") + MARK.format(kind="password")

    for rx in (TYPED, SPACED, PAIR, *((LISTED,) if listed else ())):
        text = rx.sub(password, text)
    text = IBAN.sub(hide("iban", lambda v: not iban_ok(v)), text)

    def account(m: re.Match) -> str:
        num = m.group("num")
        if sum(c.isdigit() for c in num) < 6 or DATE.fullmatch(num):
            return m.group(0)  # too short to be a bank number, or a date
        found["account"] = found.get("account", 0) + 1
        return m.group("label") + MARK.format(kind="account")

    text = ACCOUNT.sub(account, text)

    def labelled(kind: str):
        def sub(m: re.Match) -> str:
            found[kind] = found.get(kind, 0) + 1
            return m.group("label") + MARK.format(kind=kind)

        return sub

    for kind, rx in LABELLED:
        text = rx.sub(labelled(kind), text)
    text = DISCORD_USER.sub(hide("discord"), text)  # its digits before a card
    text = ITIN.sub(hide("itin"), text)
    text = SSN.sub(hide("ssn"), text)
    text = CARD_GROUPS.sub(hide("card"), text)
    text = CARD_BARE.sub(hide("card", lambda v: not luhn(v)), text)
    text = EIN.sub(hide("ein"), text)
    text = WALLET.sub(hide("wallet"), text)
    text = MAC.sub(hide("mac"), text)
    text = LOCATION.sub(hide("location"), text)
    text = PHONE.sub(hide("phone"), text)
    digits = lambda v: sum(c.isdigit() for c in v)  # noqa: E731
    text = PHONE_NATIONAL.sub(hide("phone", lambda v: digits(v) not in (10, 11)), text)
    text = IPV4.sub(hide("ip", lambda v: bool(NOT_A_HOST.match(v))), text)
    text = IPV6.sub(hide("ip", lambda v: not v6_host(v)), text)
    return text


def well_formed(argv: list[str]) -> bool:
    """`--box DIR [--now TS] "your words"`, nothing more: a command line the
    kernel would refuse is refused here, with this add-on's own usage."""
    opts, words, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now"):
            opts[a] = next(it, "")
        else:
            words.append(a)
    return bool(opts.get("--box")) and len(words) == 1 and not words[0].startswith("--")


def bite(argv: list[str]) -> int:
    if not well_formed(argv):
        print(__doc__.split("\n\n")[1].splitlines()[0], file=sys.stderr)
        return kernel.REFUSED
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
        listed = password_list(s["where"].rsplit(":", 1)[0])
        s["text"] = scrub(s["text"], found, listed)
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
