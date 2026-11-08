# Put a stack together

A stack is the add-ons you chose, in the order you chose them, sealed by
you. It is kept outside this repository, in `~/willow-stack` unless you name
another folder with `--to`.

**On a page.** willow's own UI opens on this machine only:

```
$ python ui/canvas.py
```

Choose your folders, see what the kernel alone makes of them (as counts,
never your files' words or names), start from an example or pick add-ons,
look it over, then seal it. [ui/README.md](../../ui/README.md) has every step.

**From a terminal.** The same steps as commands. `plan` prints a stack file;
save it, and `look` and `propose` read it:

```
$ python ui/canvas.py pieces --role page
$ python ui/canvas.py plan NAME... > my-stack.md
$ python ui/canvas.py look my-stack.md
$ python ui/canvas.py propose my-stack.md
```

`propose` ends at 42: the stack waits for your seal, on the page or with
your key. A command never seals it.

**For someone else.** An agent putting a stack together for a person starts
from their words, with the forge add-on, and leaves the seal to them:
[docs/agents/stacks.md](../agents/stacks.md).

**Once it's sealed,** [stack](../../adapters/stdlib/stack/) runs it, and
[stack-share](../../adapters/stdlib/stack-share/) shares it without your
files.
