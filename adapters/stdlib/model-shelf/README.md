<!-- willow-addon
section: Assistants
line: Every model already on this machine, read from Ollama's, LM Studio's, Jan's and GPT4All's folders and the Hugging Face cache: its runtime, size, quantization and hash, before you download another.
source: new
added: 2026-11-02
writes: nothing
network: none
role: suggests
uses: weights-card
-->
# model-shelf

Every model already on this machine, from the folders each runtime keeps
them in, so you know what you have before you download another.

```
python adapters/stdlib/model-shelf/model_shelf.py list [--home DIR] [--hash]

ollama        gemma3:4b  3338801804 bytes  Q4_K_M  sha256=aeda… (Ollama's name for it)
lm-studio     lmstudio-community/gemma-3-4b-it-GGUF/gemma-3-4b-it-Q4_K_M.gguf  2489757856 bytes  Q4_K_M  not hashed
hugging-face  google/gemma-3-4b-it/model-00001-of-00002.safetensors  4961251752 bytes  BF16  sha256=… (the cache's name for it)
jan           not on this machine (looked in ~/jan/models, …)
3 models in 3 files, 10789811412 bytes
```

Where it looks, under your home folder (or `--home DIR`), on Linux, macOS
and Windows:

| Runtime | Folders |
|---|---|
| Ollama | `~/.ollama/models`, or `OLLAMA_MODELS` when set; and, with no `--home`, the Linux service's /usr/share/ollama/.ollama/models |
| LM Studio | `~/.lmstudio/models`, `~/.cache/lm-studio/models` |
| Jan | `~/jan/models`, `~/.local/share/Jan/data`, `~/Library/Application Support/Jan/data`, `~/AppData/Roaming/Jan/data` |
| GPT4All | `~/.local/share/nomic.ai/GPT4All`, `~/Library/Application Support/nomic.ai/GPT4All`, `~/AppData/Local/nomic.ai/GPT4All` |
| Hugging Face | `~/.cache/huggingface/hub`, or `HF_HUB_CACHE`, or `HF_HOME` and `hub` under it |

Ollama's models are read from its manifests, one line per tag, named as
`ollama list` names them (`gemma3:4b`, `hf.co/org/repo:Q6_K`). The Hugging
Face cache is read by snapshot, each file once however many revisions
point to it. Elsewhere every GGUF and safetensors file is a model.

Each line's quantization is read from the file's own header by
[weights-card](../weights-card/). The hash: Ollama and the Hugging Face
cache store each file under its SHA-256, so that name is the hash and
nothing is read for it. Other files are hashed only with `--hash`, since a
model is gigabytes; until then the line says `not hashed`. The same weights
under two names (two Ollama tags, a copy in LM Studio of a file in the
cache) are said once both hashes are known, and the total counts each file
once.

A runtime with no folder here says where it looked; a folder with no model
says `nothing there`; a tag whose file is gone says so. Paths are shown
from `~` under the home folder.

Exit codes, the kernel's: 0 at least one model found; 42 none; 2 refused (a
bad command line, `--home` not a folder).

**Uses:** the kernel's exit codes; [weights-card](../weights-card/)'s header
reader.

**Never:** downloads, deletes or moves a model, runs one, goes online, or
reads your key.
