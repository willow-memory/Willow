# Background: AI rebuilding large programs

Written 2026-10-24, before the study, as the reason for it. In 2026, AI agents went from writing functions to rebuilding whole programs: a C compiler, a browser engine, an 800K-line runtime, and in October a free clone of most of Adobe Creative Cloud. A rough first version now takes days to weeks. A production-grade one still takes months, and what makes either possible is a precise, checkable target: a spec, a test suite, real files to round-trip. Whoever holds the tests can rebuild the program, which is pressuring both closed-source moats and copyleft licenses, and no court has ruled yet.

Note: this environment could not open the article pages, so the facts below come from search-engine summaries of the pages named. Check a page before quoting a number from it.

## Desktop apps: the Adobe clones (Oct 2026)

In early October 2026 one engineer, Brandon Thomas of the ArtCraft project, released free, open-source Rust clones of most of Adobe Creative Cloud, written mostly by AI. The Photoshop clone, PhotoCraft, went from first commit (30 Sep) to four releases by 7 Oct (cloudmagazin, PetaPixel).

| Clone | Stands in for | Reported state |
| --- | --- | --- |
| PhotoCraft | Photoshop | Layers, masks, layer styles, smart objects, brush engine; 34 tools, 27 blend modes; 134 of 135 real test files saved back byte for byte |
| LightCraft | Lightroom (not Classic) | Alpha |
| FilmCraft | Premiere Pro | Alpha; built by prompting Claude Opus, in Rust |
| Others | Illustrator, After Effects, InDesign, Acrobat | Alpha; names differ between reports |
| Later | Word, Excel, PowerPoint, AutoCAD, Pro Tools | Secondhand report only |

**How it was built.** The project says it is clean-room: Photoshop was studied only for behavior and appearance, from public specs. Its AGENTS.md forbids copying code, shaders, color profiles or assets. Thomas reportedly used Claude Opus 5.5 with Rust, and roughly 60–75% of commits list Claude as co-author; the sources conflict on the share and the model attribution is unverified.

**How good it is.** Alpha. A reviewer called it "glitchy, but real, Photoshop" (AppleInsider, Gizmodo). The project itself claims a quarter to a third of professional work. File compatibility, color management and print standards are the hard part, with about a hundred open issues there.

**Pushback.** Critics on Hacker News and Reddit question the quality, and some say the free apps advertise an AI-credits business. No Adobe statement has been reported. Copyright, trade dress and the PSD format are the open legal questions (Plagiarism Today).

## Other large agent-built systems

Three projects set the pattern before the Adobe clones: many agents, a shared repo, a test suite as the boss, and a long run.

| Project | When | Scale | Cost and time | Caveats |
| --- | --- | --- | --- | --- |
| GitHub Copilot runtime port | Sep 2026 | TypeScript rewritten as 800K+ lines of production Rust, 128 PRs | About $120K in tokens plus about 3 weeks of a developer's time, over 14.5 weeks | A few dozen regressions shipped |
| Anthropic C compiler | Feb 2026 | 16 parallel Claude Opus 4.6 agents wrote a Rust C compiler that builds Linux 6.9 for x86, ARM and RISC-V | About $20K, about 2,000 sessions | "Almost" autonomous (InfoQ); may echo existing compilers (shape-of-code) |
| Cursor FastRender browser | Jan 2026 | 1.3M–3M lines of Rust from thousands of agents | A few weeks; longest run about a week | "Kind of" works; 88% CI failure rate reported; may lean on Servo parsers and QuickJS |

Smaller ports show the same split between fast first output and slow finishing: a C-to-Rust library port reached 25K lines in two days (Rubin/LSST), while an agent's Rust port of ScanCode ran faster but returned wrong results (AboutCode).

## Measuring it: MirrorCode

MirrorCode, from Epoch AI and METR, found that agents can rebuild real programs without their source when given a detailed, checkable spec.

- **Setup:** the agent may run the original program but not read it, and must rebuild it whole. About 25 targets: Unix tools, serializers and query tools, bioinformatics, interpreters, static analysis, crypto, compression.
- **Grading:** end-to-end tests from the original's test suite, real data and LLM-generated cases.
- **Best result:** Claude Opus 4.6 rebuilt gotree, a Go bioinformatics toolkit of about 16K lines with 40+ commands. Epoch puts the human effort at 2–17 weeks.
- **Limits:** bigger targets such as Pkl stayed unsolved. Each attempt gets up to 10B tokens and 7 days; more compute kept helping.

## The licensing fight

An AI clean-room rewrite can move code from one license to another, and no court has said whether that holds.

| Case | When | What happened |
| --- | --- | --- |
| PhotoCraft and the Adobe clones | Oct 2026 | Clean-room from behavior and public specs; copyright, trade dress and the PSD format are untested |
| claw-code | After 31 Mar 2026 | After Claude Code's source leaked, a self-described clean-room Python rewrite, with a Rust port under way; widely forked |
| chardet 7.0 | Mar 2026 | The LGPL library was rewritten with Claude Code from a design document and released as MIT. Original author Mark Pilgrim filed "No right to relicense this project" |
| Malus.sh | Feb 2026 (FOSDEM) | Satirical but working "clean room as a service": one set of agents reads the docs, another writes the code |

The US Supreme Court declined *Thaler* in March 2026, leaving purely AI-made works without copyright. So a fully AI-written clone may itself belong to no one.

## What it means

- **The test suite is the moat.** Every success above had a precise target: GCC's torture tests, a program to probe, 135 real PSD files. Hard-to-specify parts (color management, print, file quirks) are where the clones fall short.
- **First pass in days, finish in months.** The last 25–75% of professional features is where the cost and the regressions are.
- **Provenance is the open question.** Clean-room claims rest on AGENTS.md rules and commit logs, not on anything a court has tested.
- **For Willow:** this matches the freeze-first rule in AGENTS.md. A FROZEN.json of questions and pass rules is the same kind of checkable target MirrorCode grades against, and kernel rows with SHA-256 are the kind of provenance record the clean-room disputes lack.
