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
| phone | a number with an area code, or +country, or a national number from its 0 in groups (`0113 555 0122`, `07700 900123`), 10 or 11 digits |
| account | a bank number after its label: sort code, account (number, no.), acct, a/c or routing; six digits or more, never a date. The label stays, so `sort code [withheld: account]` still reads |
| email | an address |
| card | 4x4 groups, or 13 to 19 digits that pass the Luhn check |
| iban | an IBAN whose mod-97 check holds |
| ssn | a US social security number, labelled or 3-2-4 |
| itin | a US taxpayer number, 9xx-7x-xxxx in its ranges |
| ein | a US employer number, 12-3456789 |
| birthdate, passport, licence, medical, case | a number after its label: DOB, passport no., driver's licence, MRN, case or claim no. The label stays, and the number holds a digit, so `passport renewal` and `claim no longer open` are left |
| ip | an address that names a machine (not 127.x or 0.0.0.0, and an IPv6 one of three groups or more) |
| mac | a network card's address |
| wallet | a Bitcoin or Ethereum address |
| location | a latitude and longitude to four places |
| discord | a Discord mention, `<@` and the person's id |
| key | a private key block; AWS, GitHub (fine-grained too), Slack, Google, Stripe, Groq, Hugging Face, Cerebras, xAI and model-provider API keys; a JWT; a Discord bot token |

Each becomes `[withheld: KIND]`, and the output counts them
(`"withheld": {"phone": 2}`). The checksums keep it from crying wolf on order
numbers and serials.

**Misses, said rather than hidden:** a street address, and a name on its own.
A home path's account name is [transcript-redact](../transcript-redact/)'s.
An EIN has no checksum, so an order number written 12-3456789 is withheld too.

**Source:** the shapes and checks of [willow-bot's one-script scrub module](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/scrub.py) (its
personal-data and credential sets), rebuilt for a person's own folder. Two
differences: a labelled number must hold a digit, where the one script's takes
the word after `case number` or `passport`; and a GitHub fine-grained token,
which the one script misses, is a key.

**Uses:** the kernel's `main` (its own bite).

**Never:** changes which passages are served, only what they show; writes to
the record (the kernel's bite row holds no words anyway).
