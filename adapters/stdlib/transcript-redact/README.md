<!-- willow-addon
section: Privacy and safety
line: An agent transcript with keys, home paths and emails taken out before you share it, each removal listed by line.
source: new
added: 2026-10-27
writes: to
network: none
uses: privacy
-->
# transcript-redact

An agent transcript is full of your machine: API keys in tool output, your
home path in every file name, your email in a config dump. This writes a
copy fit to share and lists each removal by line, so you can read what left
before the transcript does.

```
python adapters/stdlib/transcript-redact/transcript_redact.py --from FILE --to FILE

line 12   a key        [redacted:key]        …w8Qa
line 40   a home path  /home/[redacted]      …drew
line 57   an email     [redacted:email]      …d@example.org
wrote FILE: 3 removals on 3 lines
```

**What is taken out, exactly.** Keys, by the shapes keys wear: sk- and its
siblings, GitHub's ghp_ and github_pat_ families, AWS's AKIA ids, Slack's
xox tokens, Google's AIza, a JWT's three dotted blocks, and every key shape
the [privacy](../privacy/) add-on knows (Groq, Hugging Face, xAI, Stripe,
Discord and the rest). A private key block goes whole: on one line with its
breaks written `\n`, as a JSON transcript holds one, or over many, every
line from BEGIN to END. Home paths: the
account name in /home/NAME, /Users/NAME and C:\\Users\\NAME becomes
[redacted], the rest kept, so the transcript still reads. Emails, whole.
Each removal is listed with its line and a stub — a key's last characters,
an email's first letter — enough to recognise, nothing worth keeping, and
the listing never prints what it removed.

**The copy is always written**, "0 removals" said when nothing left, so the
file you share is always the one this wrote; running it twice gives the
same bytes. A transcript that is JSON stays JSON: nothing replaced holds a
quote or a backslash, and a key block's `\n` goes only with the block. What it cannot see is said: a password in prose, a
name, a secret with no shape slip through, and
[secrets-audit](../secrets-audit/) hunting the whole folder, and
[pii-audit](../pii-audit/) the numbers that identify a person, are the
wider nets.

FILE is written once, readable only by you, never over a file that exists.
Exit codes, the kernel's: 0 written; 2 refused.

**Uses:** the kernel's exit codes; nothing else of it, so a transcript from
any tool cleans the same. The privacy add-on's key shapes, read from its
source; if it was deleted, this file's own shapes still work.

**Never:** changes the transcript it reads; writes anywhere but FILE;
prints what it removed; calls its silence a clean bill.
