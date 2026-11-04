<!-- willow-addon
section: Reading more kinds of files
line: Apple Mail's .emlx messages, read as the mail add-on reads an .eml.
source: new
added: 2026-11-02
writes: to
network: none
role: reads
uses: mail
-->
# apple-mail

Your Apple Mail, as plain text the kernel can read. Apple Mail keeps each
message as its own file, `<number>.emlx` (or `<number>.partial.emlx` once its
attachments have been moved out), in the Messages folders under
`~/Library/Mail/<version>/`. Each one becomes a text file with the sender,
recipients, date and subject kept above the body.

    python adapters/stdlib/apple-mail/apple_mail.py mirror --from FOLDER --to MIRROR

Then point the kernel at the mirror, as its pile:

    python kernel.py init --box BOX --pile MIRROR --key KEY

An .emlx is the size of the message in bytes on its first line, then the
message exactly as it came in, then a short list of Apple Mail's own flags and
dates. The message is read the way the [mail](../mail/) add-on reads an .eml,
with mail's own code, so the two mirrors read the same:

    From: Ada Example <ada@example.org>
    To: Ben Example <ben@example.org>
    Date: 2026-10-14 09:15
    Subject: Roof estimate

    The estimate is in. The total is 4,200.

    Attachment: estimate.pdf

The body is the first plain-text part, else the HTML part with its tags
stripped; attachments are listed by name, and a .partial.emlx still names the
ones moved out. Date is the message's own Date header, the sender's clock time.
Only a message with no Date header takes Apple Mail's date received instead,
in UTC. The text adds no word to say so, since a word written on every such
message would answer questions your folder can't; the line before the summary
says how many:

    2 had no Date header; their Date is Apple Mail's date received, in UTC

With neither, the line is `Date: none`. A file at Messages/12.emlx is written to
`MIRROR/Messages/<number>.emlx.txt`; folders and files whose names start with a
dot are not read, nor the `.emlxpart` files attachments are kept in. A file
whose first line isn't a byte count, one shorter than its count, or one that
isn't a message is skipped and counted in the summary line.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside each other).

**Uses:** [mail](../mail/), for how a message reads (`mail.render` and
`mail.is_message`), so an .emlx and an .eml of the same message give the same
text; the kernel's exit codes (`kernel.ALIVE`, `kernel.ESCALATE`,
`kernel.REFUSED`). The tests run mail on the same message, and the kernel's
`init` and `bite` on a mirror.

**Never:** writes in your folder, modifies originals, reads attachments'
content, changes Apple Mail's flags, goes online.
