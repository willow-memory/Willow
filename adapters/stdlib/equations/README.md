<!-- willow-addon
section: Reading more kinds of files
line: Each displayed equation in LaTeX sources as a passage of its own, with the sentences around it and its label, cited by the .tex file's line.
source: new
added: 2026-11-05
writes: to
network: none
role: reads
reads: .tex
-->
# equations

The equations in your LaTeX papers and notes, each one a passage you can ask
for by the words around it.

    python adapters/stdlib/equations/equations.py mirror --from FOLDER --to MIRROR

The [latex](../latex/) add-on keeps a paper's prose and drops its math. This
keeps the math: one passage for each displayed equation, a blank line between
them, so the kernel serves an equation when a question holds the words its
paper says about it.

    paper/main.tex line 120, label eq:oz
    The Ornstein-Zernike relation reads
    h(r) = c(r) + \rho \int c(|\mathbf{r}-\mathbf{r}'|) h(r') d\mathbf{r}'
    where $c(r)$ is the direct correlation function.

| Line | What it holds |
|---|---|
| first | the .tex file, the line its equation opens on, and its labels |
| second | the end of the paragraph before it, cut at a sentence's start |
| third | the equation as its source writes it, on one line |
| last | the paragraph after it, up to its first sentence's end |

**The math is never rewritten.** Only `\label`, `\nonumber` and `\notag` are
taken out and the spaces collapsed, so a passage can be quoted back against
the paper. The words a question can hold are the prose's and the commands'
own: `\eta` holds "eta", `\frac{1+2\eta}` holds "frac", "1", "2" and "eta".

**A passage fits one of the kernel's chunks** (500 characters): the prose
around it is trimmed to make room, the prose after first. An equation longer
than that on its own is kept whole, and the kernel cuts it. Prose between two
equations goes with both: its first sentence with the first, and the end of
its paragraph with the second, since a lead-in such as "where the three
coefficients are:" belongs to what follows it.

**Displayed** means the equation, align, gather, multline, eqnarray,
displaymath, flalign and alignat environments, starred or not, `\[ ... \]`
and `$$ ... $$`, between `\begin{document}` and `\end{document}` when the
file has them. A macro the file defines without arguments as a display's
opening or closing, as physics papers often do (`\def\be{\begin{equation}}`),
is read as what it stands for. Inline math stays in the prose around an
equation; comments, verbatim, listings and `comment` environments are never
an equation.

Each file with an equation is written to MIRROR at the same relative path
with .txt added (`MIRROR/<same path>.tex.txt`). FOLDER is only read: hidden
folders and files are skipped, and nothing is written inside it. A file is
read as UTF-8, else as Windows-1252, else as Latin-1, so a paper holding one
stray byte of another encoding (an en dash pasted from a word processor, as
in some arXiv sources) is still read. A file with no displayed equation, or
that can't be read at all, is skipped and counted:

    found 212 equations
    wrote 9 files to MIRROR; skipped 3

Point the kernel at MIRROR, or at a folder holding it and latex's mirror, to
ask questions of both the prose and the math: `kernel.py init --pile MIRROR`,
or `scan index --from MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`) and its
chunk size (`MAX_CHUNK`); Python's standard library for the format.

**Never:** writes inside FOLDER, modifies an original, rewrites an equation,
writes anything outside MIRROR, or goes online.
