<!-- willow-addon
section: Assistants
line: Suggestions from a GGUF model loaded inside the add-on itself through llama-cpp-python: no server, no port, nothing listening.
source: new
added: 2026-11-02
version: 0.1.0
needs: llama-cpp-python; MIT; licence of the model varies
floor: llama-cpp-python 0.2.29; the rule names 0.1.1, its first release, which reads no GGUF; a seed per chat arrived in 0.2.15, and before 0.2.29 every quiet load opens /dev/null to write, which the guard holds as a write its card doesn't allow
writes: record
network: none
role: suggests
uses: openai-compatible
output: suggestions
-->
# in-process

A model on this machine suggests an answer from your folder, loaded inside
this add-on's own process: no server to start, no port, nothing listening.
The suggestion waits for your seal.

```
python adapters/deps/in-process/in_process.py ask --box DIR \
    --model qwen2.5-1.5b-instruct-q4_k_m.gguf "what goes in biscochitos"

Lard, not butter, and a spoonful of anise seed [1].
pass  proposal:cdd2…  waiting on your seal
```

**What it is.** [openai-compatible](../../stdlib/openai-compatible/)'s ask
with the model in place of the endpoint: the kernel bites first; when it
serves nothing, the model is never loaded. Otherwise the GGUF file is
loaded here through llama-cpp-python, with a context of 4096, and given
only the passages served, numbered, under the rule to answer only from
them and cite each used as [1], at temperature 0 with a fixed seed, for a
reply of at most 512 tokens. A reply whose brackets name a served passage
is proposed through `kernel.py propose`; one that cites nothing is printed
and proposed to no one, and so is one that cites and says nothing else: a
bare `[1]`, or a file and line in brackets, points at a passage and answers
nothing, and a suggestion with no words in it would wait on nobody. `--system FILE` puts a voice before the rule.

**Its claim** names the model file by its name and SHA-256, never by
where it lives, in the suggestions contract's one form: `qwen.gguf in this
process (weights sha256 9c1e…, temperature 0, seed 0) answered from 1 of
the 2 passages served`, a `--system` voice by its SHA-256 too. [weights-pin](../../stdlib/weights-pin/) in
front of it holds the file to its card before it loads.

**Small models and the rule.** On this repository's test machine (4 CPU
threads, no GPU), Qwen2.5 0.5B and 1.5B Instruct at Q4_K_M answered from
the passage in under 8 seconds, and neither wrote the `[1]` the rule asks
for, so nothing was proposed. That is the kernel's promise holding: an
answer with no passage under it isn't one. A larger model, or one tuned to
cite, is what turns these into suggestions.

**Its tests** load a model of a few kilobytes that
[conftest.py](conftest.py) writes from seeded weights (one llama layer,
a byte vocabulary), so llama.cpp itself runs, in this process, the same
way twice, with nothing downloaded. Its words are noise, so the step from
a reply to a proposal is tested with a stand-in where the loaded model
would be.

Exit codes, the kernel's: 0 a suggestion waits on your seal; 42 nothing
served, the model wouldn't load or answer, or a reply citing nothing; 2
refused (a bad command line, `--model` not a file, a `--system` file that
can't be read, llama-cpp-python not installed).

**Uses:** the kernel's `bite` and `propose`, as its own commands;
[openai-compatible](../../stdlib/openai-compatible/)'s chat, its reading
of cites and its seed.

**Never:** opens a port or goes online, sends a passage the bite didn't
serve, loads a model when the folder holds nothing, seals, or reads your
key.
