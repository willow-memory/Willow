# Report 2: a local model examined on the five repos, 2026-11-03

**The exam is set, not sat.** model-exam marks a model only against
answers a person sealed, and nothing in the box is sealed (report 1 says
why: sealing is the person's act, and the session refuses to do it). So
the exam ran and said so, twelve times. The six suggestions waiting in
`proof-box` are the answer key the moment someone seals them. What could
run without a seal did, and it found things.

## What was set up

- llama-cpp-python 0.3.36 built from source (no binary wheel reaches this
  machine; the build took about eight minutes), with its server extras.
- Qwen2.5-0.5B-Instruct at Q4_K_M, 193 MB, fetched in seconds into its
  own folder; SHA-256 `74a4da8c…` as in-process's claim names it.
- The model served on 127.0.0.1:8080 for the loopback add-ons;
  `local-model servers` found it there and nowhere else. Stopped after.

## in-process: three questions, three suggestions, no answers

| question | the model's reply | proposed? |
|---|---|---|
| source code never leaves the machine | `[1] (credential-cli/README.md:159)` | yes, 15.7 s |
| who may approve | `[2]` | yes, 10.3 s |
| append-only log with cryptographic chaining | `[1]` then the cited passage's own text, a demo question file | yes, 18.0 s |

The card says that on its test machine the 0.5B and 1.5B models wrote no
`[1]` and nothing was proposed. Here the 0.5B cited every time, so three
suggestions wait on a seal. But each is a citation with no answer: a
bracket, a misspelled path, or the passage repeated. in-process proposes
any reply whose brackets name a served passage, and that rule is met by a
reply that says nothing. That is a lead for in-process: hold a reply to
some content words beyond its citation before proposing it.

## same-way: consistent, including consistently empty

12 questions, each asked three times at temperature 0 with a fixed seed,
36 asks in 2 min 29 s:

- 11 answered the same way every time.
- 1 flipped, "dataset manifest provenance checksums", two ways in three.
- "what is the key for" cited nothing, all three times, the same way.

same-way's one line says the model is one you can build on. in-process
shows what it builds: a bare citation. Consistency and correctness are
two different add-ons, and only the second needs a seal.

## model-exam and quantized

Twelve unmarked, "no answer you sealed"; quantized, "nothing to mark".
Both exit 42, which is their card: an exam with no key is not a pass.

## What sealing would change

Seal the six waiting suggestions and rerun the same three commands. Then
model-exam scores each question by two things the sealed answer did: cite
a passage the answer cites, and hold half of its content words. On this
model's showing, the citations would pass and the words would fail, and
the score would say so in one line.

## Files

`exam.txt` (the twelve questions), `exam/run.log` (the three runs),
`exam/server.log`, `model-dl/` (the model), `proof-box/proposals/` (the
nine waiting suggestions, three of them the model's).
