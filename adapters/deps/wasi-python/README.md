<!-- willow-addon
section: Ways to use it
line: A job someone sent you as a Python script, run on wasi-python's CPython for WebAssembly over your folder read-only: one runtime, the same answer everywhere.
source: new
added: 2026-11-04
needs: wasi-python; Apache-2.0
floor: wasi-python 0.1.0a5; the rule names its first release, 0.1.0a3, which installs without wasmtime, so run() refuses until wasi-python[run] is asked for; 0.1.0a5 is the first that brings it
writes: record, to
network: none
uses: kart, share
-->
# wasi-python

A job someone sent you, as a Python script, run on
[wasi-python](https://pypi.org/project/wasi-python/)'s CPython for
WebAssembly over your own folder, read-only.

    pip install -r adapters/deps/wasi-python/requirements.txt
    python adapters/deps/kart/kart.py take --box DIR --package FILE --words "your words"
    python adapters/deps/wasi-python/wasi_py.py run --box DIR --job proposal:<sha256> --to FILE [--shape numbers] [--fuel N]

`run` takes `--now TS` as the kernel does.

**Why.** [wasm](../wasm/) runs a job that is WebAssembly, the same bytes on
every machine, but a job written as a module is compiled from Rust or C
first. Most people who'd write a job write Python. wasi-python is CPython
3.15 compiled to WebAssembly, with numpy, pandas, scipy and the rest built
in: the script is the job, and the runtime is one set of bytes, so two
people running the same script on the same release ran the same thing,
Linux, Mac or Windows, with no namespaces to be allowed.

**The doors are kart's.** A job comes in a share package and is taken to
your door with `kart.py take`, which puts it there as a proposal of yours,
waiting on your seal. `run` runs only a job you sealed, and refuses one
asking for the network. What it printed is proposed as an answer of yours,
waiting on your seal, under kart/results/ with the claim kart's results
carry, so `kart gather` adds them, and [dp](../dp/) and
[secure-sum](../secure-sum/) take them as they take kart's.

**What it sees.** The script runs as `python -c`, `{pile}` in it being
/pile. wasi-python's guest sees its own standard library, read-only, your
folder at /pile, read-only, and nothing else of this machine: no other path,
no network (WASI here has no way to ask for one), no environment variable of
yours, no box and no key. `--fuel` bounds the work (100,000,000,000 by
default); a script that runs out is stopped. `test_wasi_py.py` runs a probe
that writes to the folder, opens a file of this machine's and one above the
folder, opens a socket and lists its environment, and holds it to each
being refused.

**What it records.** A `ran` row: the job, how it ended, its exit code, its
output's SHA-256, wasi-python's and Wasmtime's versions, `tools` (the
SHA-256 of the runtime and of its library zip) and the fuel it used; never
the output. What it printed goes to FILE, new, outside the box and your
folder. A script that failed or ran out of fuel, or whose output broke
`--shape numbers`, proposes nothing.

**The first run of each is slow.** wasi-python keeps the runtime, compiled,
in a cache under your home folder; `run` turns that off, since it would be a
write its card doesn't name. So each `run` compiles the runtime first: most
of a minute here, then the script runs in a moment. wasi-python also
unpacks its library and keeps lock files in the temporary folder, under
names of its own; `run` points it at one scratch folder of its own, made by
`tempfile` and removed when it ends, so nothing is left in /tmp.

**What it can't do.** It can't tell you a script is harmless, only that it
reached nothing but your folder; read what it printed before you seal it.
wasi-python is young (its first release was in October 2026), and the
runtime is code its maintainer built: you trust that build as you'd trust a
Python you installed. Everyone asked should run the same release, or
`gather` says the tools differ.

**Exit codes:** 42 a result proposed, waiting on your seal, or a script
that failed, ran out of fuel or broke its shape; 2 refused (no wasi-python;
a job not sealed, not taken, or asking for the network; FILE already there
or inside the box or folder).

**Uses:** [kart](../kart/) for its door and its results' shape, and
[share](../../stdlib/share/) for FILE's rules; the kernel's `read`,
`append`, `sealed`, `standing`, `config`, `h256` and its command line for
the proposal.

**Never:** seals anything; reads your key; runs a job you didn't seal; gives
a job the network, your environment, the box or the key; writes but FILE and
the record, through the kernel.
