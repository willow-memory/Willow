<!-- willow-addon
section: Reading more kinds of files
line: .eml and .mbox files, with sender, date and subject kept.
source: new
added: 2026-10-23
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# mail

Your email, as plain text the kernel can read. Each message file (.eml) and each
mailbox (.mbox) in a folder becomes a text file with the sender, recipients,
date and subject kept above the body.

    python adapters/stdlib/mail/mail.py mirror --from FOLDER --to MIRROR

Then point the kernel at the mirror, as its pile:

    python kernel.py init --box BOX --pile MIRROR --key KEY

Each message becomes a header block, a blank line, the body, and then any
attachments, listed by name:

    From: Ada Example <ada@example.org>
    To: Ben Example <ben@example.org>
    Date: 2026-10-14 09:15
    Subject: Roof estimate

    The estimate is in. The total is 4,200.

    Attachment: estimate.pdf

The body is the first plain-text part, else the HTML part with its tags
stripped. Quoted-printable and base64 are decoded, and encoded headers are
read. Date is the sender's own clock time, as the message wrote it, so the same
input always gives the same line. An mbox gives each message a `== message N`
line first. A file at inbox/a.eml is written to MIRROR/inbox/a.eml.txt; folders
and files whose names start with a dot are not read. A file that isn't a
message is skipped and counted in the summary line.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside each other).

**Uses:** the kernel's exit codes (`kernel.ALIVE`, `kernel.ESCALATE`,
`kernel.REFUSED`). The tests run the kernel's `init` and `bite` on a mirror.

**Never:** writes in your folder, modifies originals, reads attachments'
content, goes online.
