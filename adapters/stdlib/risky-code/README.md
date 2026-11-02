<!-- willow-addon
section: Privacy and safety
line: Lines of code matching a known-dangerous pattern (command injection, eval, sql concatenation, broken tls and more), by file and line, as leads to read.
source: new
added: 2026-10-25
writes: nothing
network: none
tags: security
-->
# risky-code

The lines in your code that match a known-dangerous pattern, grouped by
vulnerability class and cited by file and line -- a lead to read, never proof
of a bug.

    python adapters/stdlib/risky-code/risky_code.py --box DIR
    python adapters/stdlib/risky-code/risky_code.py --from ANY-FOLDER

    command injection
        app/views.py:4   subprocess.run("ping -c1 " + host, shell=True)
    broken tls
        app/client.js:6  fetch(url, {rejectUnauthorized: false})

    2 lines in 2 places match a risky-code pattern. Each is a lead to read,
    not proof; verify by hand.

| Class | What it points at |
|---|---|
| command injection | a shell run from built-up input (`shell=True`, `shell_exec`, `exec.Command("sh","-c",…)`) |
| code injection | `eval` / `exec` / `new Function` of a string |
| sql injection | a query built by formatting or concatenation |
| insecure deserialization | `pickle.loads`, `yaml.load`, `unserialize`, `ObjectInputStream`, … |
| broken tls | verification turned off (`verify=False`, `InsecureSkipVerify`, …) |
| ssrf | an http call to a host from the request |
| path traversal | a file opened at a path from the request |
| template injection | a template rendered from user input |
| xss sink | `innerHTML`, `document.write`, `mark_safe`, `echo $_GET`, … |
| weak crypto or randomness | MD5/SHA-1, ECB/DES, `Math.random` for a token |
| dangerous config | `DEBUG = True`, a wildcard CORS origin, `display_errors` on |
| xxe | an XML parser with entity resolution left on |

The patterns are idiomatic across Python, JavaScript, PHP, Java, Go and Ruby.
They catch the obvious sink, not an obfuscated or indirect one, and can match
a harmless line: **the class label is a hint, not a verdict** (a bare `exec(`
reads as code injection in any language). Read each hit.

**Secrets are a different job.** [secrets-audit](../secrets-audit/) finds
passwords, keys and card numbers, and never prints their value. This one reads
code and prints the matching line, so point it at code you own.

Exit codes, the kernel's: 0 nothing matched; 42 something matched, which waits
on you to read it; 2 refused.

**Never:** says a line is a bug (it surfaces leads, a person judges), or writes
anything.
