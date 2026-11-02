<!-- willow-addon
section: Finding things
line: A game's or a house's rules, approved one section at a time, so asking what a rule says gives back that exact section, word for word.
source: bot
added: 2026-11-01
writes: record
network: none
-->
# rules

A game's or a house's rules, sealed one section at a time, so asking for a
rule gives back the exact section, word for word, and nothing else.

    python adapters/stdlib/rules/rules.py propose --box DIR games/house.md
    skipped  House rules: the section is empty
    waiting  Hand limit: python kernel.py seal --box DIR proposal:7d9f82ef…
    waiting  Trading: python kernel.py seal --box DIR proposal:6f5fdb4c…

    python adapters/stdlib/rules/rules.py ask --box DIR hand limit
    You may hold seven cards.
    Discard down at the end of your turn.

FILE is a markdown file in your folder, named by its path under it. Each
heading starts a section, named by the heading and running to the next one.
`propose` asks the kernel `rule NAME` for each section and proposes the
section's text as the answer, citing the passages of that section the bite
served. Each waits for your seal, made with `kernel.py seal` and your key.

**Once sealed, the kernel itself answers:** `kernel.py bite --box DIR "rule
Hand limit"` gives the section back verbatim, as any sealed answer, and so
does `ask`, which is that bite. The question is matched word for word (any
case, any punctuation), never loosely: `ask` for a rule that isn't sealed
says so.

Two sections with the same name (any case), an empty one, or one over 20,000
characters are skipped and said. A name already sealed with other words is
said, `differs`, and not proposed again: the kernel answers with what you
sealed until you decline it.

**`list`** says each rules section proposed: `sealed`, `waiting` on your
seal, `changed` (sealed, but your folder's words for it now differ or are
gone; the kernel still answers with what you sealed), or `outdated`
(waiting, but no longer what your folder says). It writes nothing.

Exit codes, the kernel's: `propose` 0 when every section is sealed, 42 when
one waits or the file has no section; `ask` 0 with the sealed section, 42
when none of that name is sealed; `list` 0, or 42 when one waits or has
changed; 2 refused (a file outside your folder or not text, a record that
doesn't verify, a bad command line).

**Uses:** the kernel's `read`, `bite`, `propose`, `sealed`, `standing`,
`subject_of`, `bite_key`, `words`, `config` and its exit codes.

**Never:** reads your key, seals, or writes anything but the record's rows
and proposals, through the kernel. Reads only the file you name.

**Where it comes from:** [willow-bot's one script](https://github.com/willow-memory/willow-bot/blob/main/one-script/onescript/rules.py),
where a sealed `@markdownai` rules document becomes one row per `@phase`,
looked up by exact name. Here a section is a markdown heading, and the
kernel's own sealed answer is the lookup.
