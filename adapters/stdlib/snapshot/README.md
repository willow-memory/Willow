<!-- willow-addon
section: Reading more kinds of files
line: A web page or data file fetched once into a folder, as it came, with its address, the time and its SHA-256, so later answers cite the copy.
source: bot
added: 2026-10-24
writes: to
network: the address you give, fetched once
tags: no-install, online, writes-output, file-reader, sources
-->
# snapshot

A web page or file fetched once into a folder, with where it came from,
when, and its SHA-256.

    python adapters/stdlib/snapshot/snapshot.py fetch --url URL --to FOLDER [--name NAME]
    python adapters/stdlib/snapshot/snapshot.py check --in FOLDER
    python kernel.py init --box BOX --pile FOLDER --key KEY

A page online changes. An answer that cites it should say what it said
then, and anyone should be able to tell whether the copy is still the one
that was fetched.

**fetch** saves the address's bytes exactly as they came, as FOLDER/NAME
(by default the address's last part), and adds a line to
`<FOLDER>/.snapshots.jsonl`:

    {"bytes": 692585, "fetched": "2026-10-24T08:53:10Z", "file": "old.pdf",
     "sha256": "…", "status": 200, "type": "application/pdf", "url": "https://…"}

The file is hidden, so the kernel never serves it as a passage. A redirect
is followed, and the address it ended at is kept as `final_url`.

- **Fetched once.** A name already in the folder is refused, never
  overwritten: fetch it again under another name and compare.
- **What couldn't be fetched is written down.** An address that can't be
  reached, or answers with an error, writes no file, but its line is kept,
  with `"status"` and `"why"`.

**check** goes nowhere. It hashes each file again and says `holds`,
`CHANGED` or `missing`, and `unlisted` for a file that no line names.

**What it was built for:** the sources of
[demo/google-privacy-2026-10-16](../../../demo/google-privacy-2026-10-16/):
two versions of a privacy policy and three news reports, saved on one
morning and asked offline afterwards.

**Changed from the idea:** the idea kept snapshots in the box, written to
the record, with a licence. A snapshot is a source to ask, so it goes in the
folder the box is pointed at, and a box can only be made once that folder
exists. A page's licence isn't something a fetch can learn reliably, so
it's left out rather than guessed.

**Exit codes:** fetch, 0 saved, 42 couldn't reach it; check, 0 every file
holds, 42 anything changed, missing or unlisted; 2 refused.

**Uses:** the kernel's exit codes.

**Never:** overwrites a file, goes anywhere but the address given, or
writes outside FOLDER.
