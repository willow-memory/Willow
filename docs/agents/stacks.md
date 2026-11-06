# A stack, for agents

Putting add-ons together for someone, and sharing what they settle. Part of
[AGENTS.md](../../AGENTS.md); the rule is CONTRIBUTING.md's "A chain of
add-ons starts at the Forge".

A stack is a runbook for a pile: the add-ons a person runs, in order, and
why each is there. The forge add-on builds it from their words and keeps
their reasons on their record; you propose, they seal.

1. **Ask with their words.**
   `python adapters/deps/forge/suggest.py suggest --box DIR "their sentence"`
   names the add-ons the words reach, and a fork for each word that reaches
   several. Don't pick between them for the person.
2. **When a word misses**, the add-on they meant isn't reached because no
   line of `ui/search-words.txt` points their word at its card. Add the
   line (their word, then the card's words), and ask again. That fixes it
   for everyone, where working around it fixes it once.
3. **Settle each fork with a reason.**
   `propose --choose WORD=NAME --why WORD=...` puts each choice, what it
   beat and why, and the stack, on their record as proposals. A reason is
   what the next person needs: what each add-on misreads on this kind of
   folder, as much as what it finds.
4. **Leave the seal to them.** Nothing runs and nothing is shared until they
   seal it with their key (`python kernel.py seal`). An agent never seals,
   and never reads the key (AGENTS.md, Never).
5. **Run it:** `suggest.py build` runs only the stack they sealed.
6. **Share it:** `python adapters/stdlib/stack-share/stack_share.py --box DIR`
   prints the page Show your stack (#87) asks for: their sentence, each step
   with its card's line, promises and reason, and the stack file. Only what
   they sealed is on it, and nothing of their folder; they read it and post
   it.

Where the Forge can't run (it needs forge-play and Python 3.11 or newer),
say so, and write the stack file by hand, each step with its reason beside
it, so what's shared still says why.
