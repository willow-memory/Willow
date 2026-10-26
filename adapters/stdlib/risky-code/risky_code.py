"""risky_code.py: lines in your code that match a known-dangerous pattern,
by file and line -- a lead to read, never proof of a bug. Python 3.9+.

    python adapters/stdlib/risky-code/risky_code.py --box DIR
    python adapters/stdlib/risky-code/risky_code.py --from ANY-FOLDER

Every line of your files (the box's, or any folder's) that matches a curated
pattern for a common vulnerability class, grouped by class, each cited by
file and line:

    command injection
        app/views.py:4   subprocess.run("ping -c1 " + host, shell=True)
    broken tls
        app/client.js:6  fetch(url, {rejectUnauthorized: false})

The classes: command injection, code injection (eval/exec), sql injection,
insecure deserialization, broken tls, ssrf, path traversal, template
injection, xss sink, weak crypto or randomness, dangerous config, and xxe.
The patterns are idiomatic across Python, JavaScript, PHP, Java, Go and
Ruby; they catch the obvious sink, not an obfuscated or indirect one, and
can match a harmless line. The class label is a hint, not a verdict: a bare
`exec(` reads as code injection whichever language it's in.

Secrets are a different job: [secrets-audit](../secrets-audit/) finds those,
and never prints their value. This reads code and prints the line, so point
it at code you own, not at a folder of secrets.

It only reads, and writes nothing. Exit codes, the kernel's: 0 nothing
matched; 42 something matched, which waits on you to read it; 2 refused.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: vulnerability class -> line patterns that point at it, idiomatic across
#: Python, JS/TS, PHP, Java, Go and Ruby. A match is a lead, not a verdict.
PATTERNS = {
    "command injection": [
        r"shell\s*=\s*True",
        r"\bos\.(system|popen)\s*\(",
        r"child_process\.(exec|execSync)\s*\(",
        r"Runtime\.getRuntime\(\)\.exec\s*\(",
        r"\b(shell_exec|passthru|proc_open)\s*\(",
        r"exec\.Command\([^)]*(\"sh\"|\"bash\"|-c)",
    ],
    "code injection": [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bnew\s+Function\s*\(",
        r"\binstance_eval\b",
    ],
    "sql injection": [
        r"\.execute\([^)]*(%|\+)",
        r"\.execute\(\s*[fF][\"']",
        r"(SELECT\b[^;\"'`]*\bFROM|INSERT\b[^;\"'`]*\bINTO|UPDATE\b[^;\"'`]*\bSET|DELETE\b[^;\"'`]*\bFROM)"
        r"\b[^;\"'`]*(%s|%d|\.format\(|\$_|\$\{|\"\s*\+|\+\s*\")",
        r"(mysqli_query|->query)\s*\([^)]*\$",
        r"executeQuery\s*\([^)]*\+",
        r"fmt\.Sprintf\([^)]*(SELECT|INSERT|UPDATE|DELETE)",
    ],
    "insecure deserialization": [
        r"pickle\.loads?\s*\(",
        r"\bcPickle\b",
        r"yaml\.load\s*\((?![^)]*Safe)",
        r"\bmarshal\.loads?\b",
        r"\bunserialize\s*\(",
        r"ObjectInputStream",
        r"Marshal\.load\b",
    ],
    "broken tls": [
        r"verify\s*=\s*False",
        r"CERT_NONE",
        r"check_hostname\s*=\s*False",
        r"rejectUnauthorized\s*[:=]\s*false",
        r"InsecureSkipVerify\s*[:=]\s*true",
        r"CURLOPT_SSL_VERIFY(PEER|HOST)\s*,\s*(0|false)",
        r"NODE_TLS_REJECT_UNAUTHORIZED",
    ],
    "ssrf": [
        r"(requests|httpx|urllib|axios|fetch)\.?(get|post|request|urlopen)?\s*\([^)]*\b(request|req|param|input|argv|\$_)",
        r"urlopen\s*\([^)]*\b(request|input|\$_)",
    ],
    "path traversal": [
        r"open\s*\([^)]*\b(request|argv|params|input)\b",
        r"(send_file|sendFile)\s*\([^)]*request",
        r"(fopen|file_get_contents|readfile|include|require)\s*\([^)]*\$_",
        r"os\.path\.join\([^)]*\b(request|input|argv)",
    ],
    "template injection": [
        r"render_template_string\s*\(",
        r"Template\s*\([^)]*(\+|%|\.format|\$\{|request)",
        r"\{\{[^}]*\b(request|param|input)\b",
    ],
    "xss sink": [
        r"\.innerHTML\s*=",
        r"document\.write\s*\(",
        r"dangerouslySetInnerHTML",
        r"mark_safe\s*\(",
        r"\|\s*safe\b",
        r"\bv-html\b",
        r"echo\s+\$_(GET|POST|REQUEST)",
    ],
    "weak crypto or randomness": [
        r"hashlib\.(md5|sha1)\s*\(",
        r"\b(md5|sha1)\s*\(",
        r"MessageDigest\.getInstance\(\s*[\"'](MD5|SHA-?1)",
        r"(MODE_ECB|AES/ECB|DES/)",
        r"(Math\.random|random\.random\s*\(|mt_rand\s*\(|\brand\s*\(\s*\))",
    ],
    "dangerous config": [
        r"DEBUG\s*=\s*True",
        r"\.run\([^)]*debug\s*=\s*True",
        r"app\.debug\s*=\s*True",
        r"display_errors\s*=\s*(On|1)",
        r"Access-Control-Allow-Origin[\"']?\s*[:,]\s*[\"']?\*",
        r"cors\(\s*\{[^}]*origin\s*:\s*[\"']\*",
    ],
    "xxe": [
        r"resolve_entities\s*=\s*True",
        r"\bnoent\s*=\s*True",
        r"DocumentBuilderFactory",
        r"libxml_disable_entity_loader\s*\(\s*false",
    ],
}
RULES = {cls: [re.compile(p, re.I) for p in pats] for cls, pats in PATTERNS.items()}


def scan(pile: Path) -> dict:
    """{class: [(path, line, text)]} for every matching line, in file order."""
    out: dict = {cls: [] for cls in RULES}
    for c in kernel.chunks(pile):
        for i, line in enumerate(c["text"].splitlines()):
            for cls, regs in RULES.items():
                if any(r.search(line) for r in regs):
                    out[cls].append((c["path"], c["line"] + i, line.strip()))
    return {cls: rows for cls, rows in out.items() if rows}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("--box", "--from"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if argv[0] == "--box":
        box = Path(argv[1])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        pile = Path(kernel.config(box)["pile"])
    else:
        pile = Path(argv[1])
        if not pile.is_dir():
            print(f"refused: {pile} isn't a folder", file=sys.stderr)
            return kernel.REFUSED

    found = scan(pile)
    if not found:
        print("No lines matched a risky-code pattern.")
        return kernel.ALIVE
    total = 0
    for cls, rows in found.items():
        print(cls)
        width = max(len(f"{p}:{n}") for p, n, _ in rows)
        for path, n, text in rows:
            print(f"    {f'{path}:{n}':<{width}}  {text[:90]}")
            total += 1
    where = len({(p, n) for rows in found.values() for p, n, _ in rows})
    print(f"\n{total} line{'s' if total != 1 else ''} in {where} place"
          f"{'s' if where != 1 else ''} match a risky-code pattern. Each is a lead to "
          "read, not proof; verify by hand.")  # fmt: skip
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
