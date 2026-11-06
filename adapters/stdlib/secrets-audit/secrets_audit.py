"""secrets_audit.py: passwords and keys sitting in plain files. Python 3.9+.

    python adapters/stdlib/secrets-audit/secrets_audit.py --box DIR [--json]
    python adapters/stdlib/secrets-audit/secrets_audit.py --from FOLDER [--json]

Every line of your files (the box's, or any folder's) that holds one of:

    password   a password you typed with its label: `password: hunter2`,
               `pw = widgets1998`, `pw Wendouree#14`; the second half of a
               login pair, `ana@example.org / Tide2024!`; and in a file
               whose name says it's a list of them (passwords.txt,
               logins.md), every value that looks like one. A label with
               no value, a comparison, a placeholder ("changeme",
               "example"), or prose ("password policy") is left alone
    key        a private key block, or an AWS, GitHub, Slack, Google,
               Stripe or model-provider API key, or a JWT
    card       a card number that passes the Luhn check, or 4x4 groups
    iban       an IBAN whose mod-97 check holds
    ssn        a US social security number

is listed by file and line, grouped by kind, never with the value:

    secrets-audit: populated, 2 places hold a secret in plain text; values are never shown
    ## a password typed with its label
      notes/wifi.txt:3   value not shown
    ## a key or token
      work/deploy.md:41  value not shown

It prints a report (ci/README.md, "The report contract"); `--json` prints the
same report as one JSON object.

The shapes are the privacy add-on's (willow-bot's scrub, rebuilt there),
passwords included, so what this lists is what privacy hides from an answer.
Without privacy, only willow-bot's own typed-password rule is used. A file is read the way the
kernel reads it, so what's listed is what an answer could have shown.
Email addresses and phone numbers aren't listed: they're in every file and
aren't secrets.

It only reads, and writes nothing. Exit codes, the kernel's: 0 nothing
found (empty); 42 something found, which waits on you (populated), or there
were no files to look in (unreachable); 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
import types
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

KINDS = ("password", "key", "card", "iban", "ssn")
#: each kind as its report group is headed
HEADS = {"password": "a password typed with its label", "key": "a key or token",
         "card": "a card number", "iban": "an IBAN", "ssn": "a US social security number"}  # fmt: skip
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


NAME = "secrets-audit"


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
    rows = [r for g in doc["groups"] for r in g["rows"]]
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    if not rows:
        return out[0]
    w = min(max(len(r["where"]) for r in rows), 60)
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


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


def kinds_in(line: str, pv, listed: bool = False) -> list[str]:
    """The kinds a line holds. `listed`: it is from a file of passwords."""
    found: dict = {}
    if pv is not None:
        pv.scrub(line, found, listed)
    got = [k for k in KINDS if k in found]
    if pv is None and typed_password(line):
        got = ["password", *got]
    return got


def audit(pile: Path, pv) -> list[tuple[str, int, str]]:
    """(path, line, kind) for every secret in the pile, in file order."""
    out = []
    for c in kernel.chunks(pile):
        listed = pv is not None and pv.password_list(c["path"])
        for i, line in enumerate(c["text"].splitlines()):
            for kind in kinds_in(line, pv, listed):
                out.append((c["path"], c["line"] + i, kind))
    return sorted(set(out))


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
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
    files = len({c["path"] for c in kernel.chunks(pile)})
    if not files:
        say(report(NAME, "unreachable", "nothing there to check", []), as_json)
        return kernel.ESCALATE
    found = audit(pile, pv)
    if not found:
        said = f"no password, key or card number in {files} file{'s' if files != 1 else ''}"
        say(report(NAME, "empty", said, []), as_json)
        return kernel.ALIVE
    places = len({(p, n) for p, n, _ in found})
    said = (f"{places} place{'s' if places != 1 else ''} hold{'' if places != 1 else 's'}"
            " a secret in plain text; values are never shown")  # fmt: skip
    groups = [(HEADS[k], [(f"{p}:{n}", "value not shown") for p, n, kd in found if kd == k])
              for k in KINDS]  # fmt: skip
    say(report(NAME, "populated", said, groups), as_json)
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
