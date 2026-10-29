<!-- willow-addon
section: Ways to use it
line: Record rows in the CloudEvents envelope, for any tool that already reads them.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, interface
-->
# cloudevents

Your record, in the envelope event tools already read.

CloudEvents is what event brokers, serverless platforms and a long list of
tools use to say that something happened. This writes each row of your record
as one, a JSON object a line, so anything that reads CloudEvents can take what
your box did.

    python adapters/stdlib/cloudevents/cloudevents.py --box DIR --to FILE [--from-row N] [--kinds a,b]
    wrote FILE: 4 events, rows 0 to 3

One line of FILE:

    {"specversion":"1.0","id":"<the row's hash>","source":"urn:willow:record:<the first row's hash>",
     "type":"org.willow.record.seal","time":"2026-10-24T00:00:00Z","sequence":"3",
     "standing":"sealed","subject":"proposal:...","datacontenttype":"application/json","data":{...}}

| Event field | From the row |
|---|---|
| id | the row's own hash, so a row is the same event wherever it is sent |
| source | the box, named by its first row, so two boxes don't mix |
| type | org.willow.record. and the row's kind: boot, bite, proposal, seal, decline, out |
| time | when the row was written |
| sequence | its place on the chain |
| standing | what the record says of it: sealed only for a row written by you with your approval |
| subject | the suggestion a proposal, seal or decline is about |
| data | the row as it is in the record, with its hash and the hash before it, so the chain still checks |

The record holds no question's words, and neither do the events: a question is
its fingerprint, a passage its id and where it was. `--from-row N` starts at
row N, for sending only what is new; `--kinds bite,seal` keeps only rows of
those kinds. A record that doesn't verify is refused: events read past a break
could say something that didn't happen.

FILE is written once, readable only by you, never over a file that exists, and
the same record gives the same bytes. It writes the file and sends nothing; a
tool that reads the lines does the rest.

Exit codes, the kernel's: 0 written; 42 nothing in range, nothing written; 2
refused.

**Uses:** the kernel's `read`.

**Never:** sends anything, reads the key, or writes anywhere but FILE.
