<!-- willow-addon
section: Privacy and safety
line: Finds passwords, keys and card numbers sitting in plain files, by file and line, never showing the value.
source: bot
added: 2026-10-24
writes: nothing
network: none
tags: everyday
uses: privacy
-->
# secrets-audit

The passwords and keys sitting in plain files in your folder, so you can
move them somewhere safer.

    python adapters/stdlib/secrets-audit/secrets_audit.py --box DIR
    python adapters/stdlib/secrets-audit/secrets_audit.py --from ANY-FOLDER

    wifi.txt:2          password
    work/deploy.md:3    key

    2 places hold a secret in plain text. A password manager is a safer home
    for them; the value was not shown here.

| Kind | What counts |
|---|---|
| password | a password typed with its label: `password: hunter2`, `pw = widgets1998` |
| key | a private key block; AWS, GitHub, Slack, Google, Stripe or model-provider API keys; a JWT |
| card | a card number that passes the Luhn check, or four groups of four |
| iban | an IBAN whose mod-97 check holds |
| ssn | a US social security number |

These are left alone: a label with no value, a comparison (`$p == $password`),
a value that names somewhere else (`env:WIFI`, `None`), a placeholder
(`changeme`, `example`), and e-mail addresses and phone numbers, which are
in every file and aren't secrets.

**Where the shapes come from:** the [privacy](../privacy/) add-on's checks
([willow-bot's scrub](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/scrub.py), rebuilt there), and willow-bot's own typed-password
rule. A file is read the way the kernel reads it, so what's listed is what
an answer could have shown. If the privacy add-on was deleted, it says so
and looks for typed passwords alone.

Exit codes, the kernel's: 0 nothing found; 42 something found; 2 refused.

**Never:** prints a value it found, or writes anything.
