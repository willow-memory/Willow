# Design note: skill-picks, the best current skills, found and judged

**Status: an idea, 2026-11-18; nothing is built.** It is one entry on
`adapters/planned.json`. This note keeps the research behind it, so whoever
picks it up starts from what was found and what was not checked.

## The idea, in one line

Thousands of people have written skills (SKILL.md folders) for assistants.
`skill-picks` points at the best and most current of them, ranked on facts it
reads itself, and says what each one can touch. It only prints. It never
installs a skill and never approves one.

## What it should do

1. **Rank on what it reads, not on badges.** Last commit date, a deprecation
   notice, the licence, whether the source is the vendor's own, and a count
   of the skill folders it finds itself. Stars and install counts measure how
   well known a skill is, not whether it is kept up or safe, and README
   counts disagreed with the pages they sit on.
2. **Say what a skill can touch.** Shell, the network, spending money,
   changing accounts, and any gap between what its SKILL.md says and what
   its scripts do.
3. **Pin what it checked.** Record the commit it ranked, because a
   marketplace install can update after someone vetted it.
4. **Show its evidence and stop there.** It suggests. The person decides.

It goes online only to read public repositories (`api.github.com`).

## What the research found (2026-11-18)

Three short research passes, each by a small model, read only. "Opened"
means the page was fetched; "snippet" means a search result only. No page
showed a commit date, so none of this says what is current today, and star
counts differ between snippets and pages: treat every count as approximate.

### Official, opened

| Source | What it is |
|---|---|
| anthropics/claude-plugins-official | Anthropic's plugin marketplace, Apache-2.0. Says Anthropic cannot verify its third-party plugins. |
| anthropics/skills | Anthropic's reference skills (docx, pdf, pptx, xlsx). Its README calls them demonstration examples. |
| agentskills.io specification | The SKILL.md format. No date or licence visible. |
| Claude Code skills docs and the platform best-practices page | The loading rules and limits. Undated. |
| openai/skills | Marked deprecated in its own README. Rank last. |

### Official, snippet only (open these before trusting them)

google/skills (reported April 2026, counts disagree: 22 vs 28),
microsoft/skills (174 vs 338), MicrosoftDocs/agent-skills (193 reported),
google-gemini/gemini-skills (3 or 4 skills).

### Community, opened

| Source | Skills | Licence | Note |
|---|---|---|---|
| mattpocock/skills | 27 | MIT | Engineering workflow. |
| obra/superpowers | 15 | MIT | A whole development method. |
| addyosmani/agent-skills | 25 | MIT | Gate-based lifecycle. |
| heilcheng/awesome-agent-skills | about 400 listed | MIT | Has entry rules: 20+ stars, repo over 14 days old. The best-run list. |
| VoltAgent/awesome-agent-skills | 1,000+ links | MIT | Some entries can spend money. |
| sickn33/agentic-awesome-skills | about 3,000 | mixed | Broad, not curated. Includes offensive-security and spending skills. |
| ComposioHQ/awesome-claude-skills | about 164 | Apache-2.0 | Claims "1000+"; promotes Composio. |
| travisvn/awesome-claude-skills | about 28 | not stated | Badge says last updated Feb 2026. |

Skip skillcreatorai/Awesome-Agent-Skills, a copy of the Composio list.

### Directories and how they rank

skills.sh ranks by installs and shows no audit status per listing. ClawHub
mentions signed manifests and scanners, with no per-listing status. SkillsMP
(not opened, 403) scrapes public GitHub files. Every count a directory gives
for itself is self-reported.

### Safety

- Snyk "ToxicSkills" (Feb 2026, opened): of 3,984 skills scanned, 36.8% had
  some security issue, 13.4% a critical one, 76 were confirmed malicious.
- arXiv 2602.06547 (opened): of 98,380 skills, 157 malicious, all removed
  once the maintainers were told.
- MalSkillBench (arXiv 2606.07131) and SkillSieve (arXiv 2604.06550), both
  opened: scanners catch injected code well and catch malicious plain-language
  instructions badly. A person has to read the SKILL.md itself.
- Signing exists (NVIDIA's OMS signatures, SkillLedger's Sigstore). A
  signature shows a folder is unchanged since publishing, not that it is safe.
- Not checked: Unit 42 "Trust No Skill", Koi's "ClawHavoc" and SkillLedger's
  incident figures were seen only second-hand. Discount them.

## Open questions

- "Best" can mean newest, most used, or vetted. This note ranks on upkeep and
  source, because use alone rewards fame.
- Whether it ranks across assistants or only Claude's SKILL.md format.
- Where the evidence lives: it prints per run, or a record through the
  kernel. The entry says it writes nothing, so it prints.
