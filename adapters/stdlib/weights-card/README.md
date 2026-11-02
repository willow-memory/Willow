<!-- willow-addon
section: Assistants
line: A model card filled in from the weights file's own header, GGUF or safetensors (architecture, quantization, context length, licence), so the card says what the file says.
source: new
added: 2026-11-02
writes: to
network: none
tags: no-install, offline, writes-output, assistant
-->
# weights-card

A card for a model's weights file, filled in from the file's own header
rather than from its download page, so the card says what the file says.

```
python adapters/stdlib/weights-card/weights_card.py \
    --from gemma-3-4b-it-Q4_K_M.gguf --to gemma.md

wrote gemma.md: gemma-3-4b-it-Q4_K_M.gguf
```

```
<!-- willow-model
file: gemma-3-4b-it-Q4_K_M.gguf
format: GGUF v3
sha256: 9c1e…
bytes: 2489757856
architecture: gemma3
name: Gemma 3 4b It
quantization: Q4_K_M
context length: 131072
parameters: 3880263168
licence: gemma
-->
# Gemma 3 4b It
```

**GGUF** (llama.cpp, Ollama, LM Studio, Jan, llamafile), versions 2 and 3:
the architecture, name, licence and context length are the header's own
keys, the quantization is its `general.file_type` under llama.cpp's name
for it, and the parameters are counted from every tensor's shape. The
tokenizer's long lists are read past, not kept.

**safetensors** (Hugging Face): the header names each tensor's type and
shape, so the quantization is the types, most parameters first (`BF16,
I8`), and the parameters are counted. Architecture, name and licence come
from its `__metadata__` when that holds them; the context length never
does. One shard of a sharded model is a card for that shard.

A value the header doesn't hold is written as `not in the header`, never
guessed and never left out. The SHA-256 and size are the whole file's.
Only the file's name goes on the card, not the folder it sits in, so the
same file gives the same bytes on any machine.

It reads the header and hashes the file, nothing more: it never loads the
model or runs it. `--to` is a new file in a folder that exists; it never
writes over a card already there, and never makes a folder.

Exit codes, the kernel's: 0 a card written; 42 not a weights file it can
read (no GGUF or safetensors header, an older GGUF, or one cut short), and
nothing written; 2 refused (a bad command line, `--from` not a file,
`--to` already there or its folder missing).

**Uses:** the kernel's exit codes.

**Never:** loads or runs the model, goes online, writes anywhere but
`--to`, writes over a file, or reads your key.
