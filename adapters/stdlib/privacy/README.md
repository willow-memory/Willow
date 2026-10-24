<!-- willow-addon
section: Privacy and safety
line: Hides phone numbers, emails, card, bank and ID numbers, and API keys in what a question prints, and says what it hid.
source: bot
added: 2026-10-23
writes: record
network: none
tags: no-install, offline, records, privacy
-->
# privacy

What a question prints, with personal data and keys withheld.

    python adapters/stdlib/privacy/privacy.py bite --box DIR [--now TS] "your words"
    python adapters/stdlib/privacy/privacy.py scrub < FILE

| Withheld | How it's told apart |
|---|---|
| phone | a number with an area code, or +country |
| email | an address |
| card | 4x4 groups, or 13 to 19 digits that pass the Luhn check |
| iban | an IBAN whose mod-97 check holds |
| ssn | a US social security number, labelled or 3-2-4 |
| ip | an address that names a machine (not 127.x or 0.0.0.0) |
| key | a private key block; AWS, GitHub, Slack, Google, Stripe and model-provider API keys; a JWT |

Each becomes `[withheld: KIND]`, and the output counts them
(`"withheld": {"phone": 2}`). The checksums keep it from crying wolf on order
numbers and serials.

**Misses, said rather than hidden:** a street address, and a name on its own.

**Source:** the shapes and checks of [willow-bot's one-script scrub module](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/scrub.py) (its
personal-data and credential sets), rebuilt for a person's own folder.

**Uses:** the kernel's `main` (its own bite).

**Never:** changes which passages are served, only what they show; writes to
the record (the kernel's bite row holds no words anyway).
