<!-- willow-addon
section: Reading more kinds of files
line: Each displayed LaTeX equation with the words its paper gives its symbols ("where η is the packing fraction"), so words find the equation.
source: new
added: 2026-11-06
version: 0.1.0
writes: to
network: none
role: reads
output: mirror
reads: .tex
uses: equations
-->
# notation

Your LaTeX papers' equations, each with the words its paper gives for its
symbols, so a question in words finds the equation.

    python adapters/stdlib/notation/notation.py mirror --from FOLDER --to MIRROR

The [equations](../equations/) add-on makes each displayed equation a passage
of its own, with the prose around it. But an equation is mostly symbols, and a
question is asked in words: "what is the structure factor in terms of the
direct correlation function?" shares no word with
`S(q) = 1/(1 - \rho \hat{c}(q))`, so the kernel, which serves a passage only
when it holds half a question's words, never serves it. A paper says what its
symbols mean, once, somewhere. This reads those sentences into a glossary, one
for each folder of .tex files, and writes each equation as the equations
add-on does, with one more line:

    paper/main.tex line 120, label eq:oz
    so the Ornstein-Zernike equation also gives
    S(q) = \frac{1}{1 - \rho \hat{c}(q)}
    where $c(r)$ is the direct correlation function.
    symbols: S structure factor; \rho number density; c direct correlation function

**A definition** is read in two shapes, from the prose and never from inside
math:

| Shape | Example |
|---|---|
| a name of up to four words, after an article, right before the symbol | "the packing fraction $\eta$" |
| the symbol, then is, denotes, stands for, represents or being, an article and a name | "where $\eta$ is the packing fraction" |

A name starts after the last article or small word inside it ("a fluid at
packing fraction $\eta$" names packing fraction), and right before a symbol
it must end on its name ("the density and $x$" names nothing). A lone generic
word ("the coefficient $a$") and a phrase holding a verb or a judgement are
not names. A symbol keeps its first two names.

**A symbol** is one letter or one Greek letter, read through any accent,
subscript, superscript or argument: `\hat{c}(k)` is c, `S(q)` is S,
`g_{ij}(r)` is g. Inline math holding more than one (`\rho\sigma^3`,
`x = 1`) defines nothing. One letter means one thing within a paper, which is
mostly so and sometimes not: a paper using S for both entropy and the
structure factor gives S both names.

**The symbols line** comes last in its passage and names each symbol the equation uses once, in the order it
first uses them, and leaves out a symbol the paper never defines. An equation
using none it defines gets no line. The line holds at most 200 characters,
and takes its room from the prose before the equation, so a passage still
fits in one of the kernel's chunks (500 characters). When the equation
itself leaves less room than that, the line is shortened to fit, or left
out: a passage is never pushed past a chunk by its symbols. The math is never
rewritten.

**One paper, one glossary:** the .tex files in one folder share it, since a
paper split into files defines a symbol in one and uses it in another. Files
in another folder don't.

Each file with an equation is written to MIRROR at the same relative path
with .txt added (`MIRROR/<same path>.tex.txt`). FOLDER is only read: hidden
folders and files are skipped, and nothing is written inside it. A file is
read as the equations add-on reads it (UTF-8, else Windows-1252, else
Latin-1). A file with no displayed equation, or that can't be read, is
skipped and counted:

    found 440 equations; 425 given the words for their symbols
    wrote 1 files to MIRROR; skipped 1

Use it in place of the equations add-on's mirror, not beside it: the two
would hold each equation twice.

**What it can't tell.** A glossary is read by pattern, not understood. On
Santos's 2013 lecture notes on hard spheres it finds the radial distribution
function, the direct correlation function, the packing fraction, the cavity
function and the compressibility factor, and also names some symbols by a
nearby phrase that isn't their meaning ("total", "first"). A wrong name adds
words a question might hold; it never takes the equation out.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the [equations](../equations/) add-on's reading of a .tex file
(its displays, macros, encodings and context); the kernel's exit codes and
its chunk size; Python's standard library.

**Where each passage came from** is in a hidden map beside its mirror,
`MIRROR/.places/<same path>.txt.json`, which the kernel never reads, as
[the mirror contract](../ci/README.md#the-mirror-contract) says: the .tex
file's lines from the paragraph before the equation to the end of the one
after it, as the [equations](../equations/) add-on places the same
equation. The symbols line is placed nowhere of its own: its words are the
glossary's, from wherever the paper defines its symbols. That is why it
comes last, after the paper's own words.

**Never:** writes inside FOLDER, modifies an original, rewrites an equation,
writes anything outside MIRROR, or goes online.
