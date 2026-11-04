<!-- willow-addon
section: Assistants
line: An answer translated by a local model, the original kept beside it, the translation held until you seal it.
source: new
added: 2026-11-02
writes: record
network: loopback
role: suggests
uses: local-model, openai-compatible
-->
# translate

An answer you sealed, translated by a model on this machine, with the
original kept beside it, and the translation held until you seal it too.

```
python adapters/stdlib/translate/translate.py --box DIR --into Spanish "what goes in biscochitos"

Manteca, no mantequilla, y una cucharada de anís [1].
pass  proposal:5e0c…  waiting on your seal
```

**What is translated** is the answer you sealed for the question's words
(the kernel's `sealed` and `standing`); with none, nothing is asked. The
model is the first local server answering among those `--url` names, or
on the usual ports, as [local-model](../local-model/) finds one, and its
first model unless `--model` names another. It is told to translate into
the language and keep each citation, `[1]`, beside the words it belongs to,
at temperature 0 with a fixed seed.

**Its own question.** The translation is proposed through `kernel.py
propose` as the answer to "your question in Spanish", never to the
original question: sealed, it answers that question, and the original
still answers yours. The proposal holds the translation, then `Original:`
and the answer you sealed; it cites the original's passages that the new
question's bite serves; its claim names the model, the server and the
original's proposal. A translation sealed already is said, and the model
isn't asked again.

**Its citations must be the original's.** A translation that drops a `[1]`
or makes up a `[3]` is printed and proposed to no one, and nothing goes on
the record.

**Built in stdlib**, like [local-model](../local-model/): the idea was
filed as needing a local model server, which is a program you run, reached
over HTTP, not a package this imports.

Exit codes, the kernel's: 0 a translation waits on your seal, or one is
sealed already; 42 no answer you sealed for the question, no local server
running, or a translation whose citations differ; 2 refused (a bad command
line, a URL off this machine, not a box, a record that doesn't verify).

**Uses:** the kernel's `read`, `sealed`, `standing`, `bite_key`, `bite` and
`propose`; [local-model](../local-model/)'s finding of a server;
[openai-compatible](../openai-compatible/)'s asking.

**Never:** sends anything off this machine, changes the answer you sealed,
seals, or reads your key (the kernel checks your seals).
