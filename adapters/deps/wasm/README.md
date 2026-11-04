<!-- willow-addon
section: Ways to use it
line: A job someone sent you as WebAssembly, run by Wasmtime over your folder read-only: the same bytes, so the same answer, on every machine.
source: new
added: 2026-11-04
needs: wasmtime; Apache-2.0 WITH LLVM-exception
floor: wasmtime 48.0.0; the rule names 0.21.0 from 2020, and before 48.0.0 a folder is opened read-only only through permission objects this code doesn't use, and output can't be caught without a file
writes: record, to
network: none
uses: kart, share
-->
# wasm

A job someone sent you, as WebAssembly, run by
[Wasmtime](https://wasmtime.dev) over your own folder, read-only.

    pip install -r adapters/deps/wasm/requirements.txt
    python adapters/deps/kart/kart.py take --box DIR --package FILE --words "your words"
    python adapters/deps/wasm/wasm.py run  --box DIR --job proposal:<sha256> --to FILE [--runtime FILE] [--shape numbers] [--fuel N]

`run` takes `--now TS` as the kernel does.

**Why.** [kart](../kart/) runs a shell job on your machine's own grep and
sort, and two machines' tools can read one job apart: busybox's grep and
GNU's count `grep -lic` differently. A WebAssembly job carries its program.
Two machines that ran the same bytes ran the same job, and Wasmtime runs
them the same on Linux, a Mac or Windows, with no namespaces to be allowed,
so in a container where bubblewrap can't make a sandbox it still runs.

**The doors are kart's.** A job comes in a share package and is taken to
your door with `kart.py take`, which puts it there as a proposal of yours,
waiting on your seal. `run` runs only a job you sealed, and refuses one
asking for the network. What it found is proposed as an answer of yours,
waiting on your seal, under kart/results/ with the claim kart's results
carry, so `kart gather` adds them; the tools' hash in that claim is the
module's, alike wherever it ran.

**What a job is.** Its text is a WebAssembly module: `(module ...` in the
text format, or `wasm:` and the module's bytes in base64. Or, with
`--runtime FILE`, a script for an interpreter compiled to WebAssembly that
you keep, CPython's WASI build say: FILE runs with the script as its one
argument, `{pile}` in the script being /pile. Then the runtime's SHA-256
is the tools', so everyone asked should run the same runtime file.

**What it sees**, in Wasmtime's WASI: your folder at /pile, read-only;
the script at /job, read-only, with `--runtime`; nothing else. No path
above the folder, no network (WASI here has no way to ask for one), no
environment variable, no box and no key. `--fuel` bounds the work
(10,000,000,000 by default); a job that runs out is stopped and proposes
nothing. `test_wasm.py` runs modules that try to create a file in the
folder, write one there, open ../key and /etc/passwd, and holds them to
each being refused.

**What it records.** A `ran` row: the job, how it ended, its exit code, its
output's SHA-256, the engine and its version, `tools` (the module's or the
runtime's SHA-256) and the fuel it used; never the output. What it printed
goes to FILE, new, outside the box and your folder. A job that failed or ran
out of fuel, or whose output broke `--shape numbers`, proposes nothing.

**What it can't do.** It can't tell you a job is harmless, only that it
reached nothing but your folder; read what it printed before you seal it.
Writing a job as WebAssembly by hand is for small ones; a real one is
compiled, or a script for a runtime, and a runtime you didn't build is code
you trust. Wasmtime's version is on the `ran` row but not in the tools'
hash: a module that asks for the clock or random numbers can still answer
differently.

**Exit codes:** 42 a result proposed, waiting on your seal, or a job that
failed, ran out of fuel or broke its shape; 2 refused (no Wasmtime; a job
not sealed, not taken, asking for the network, or not a module; a runtime
that isn't a module; FILE already there or inside the box or folder).

**Uses:** [kart](../kart/) for its door and its results' shape, and
[share](../../stdlib/share/) for FILE's rules; the kernel's `read`,
`append`, `sealed`, `standing`, `config`, `h256` and its command line for
the proposal.

**Never:** seals anything; reads your key; runs a job you didn't seal; gives
a job the network, your environment, the box or the key; writes but FILE and
the record, through the kernel.
