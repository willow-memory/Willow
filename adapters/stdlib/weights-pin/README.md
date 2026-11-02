<!-- willow-addon
section: Trust and proof
line: A local model's weights file hashed before each run and refused when it differs from the hash on its model card.
source: new
added: 2026-11-02
writes: nothing
network: none
uses: weights-card
-->
# weights-pin

A weights file held to the hash on its model card, checked before the model
runs, so the model that answers is the one the card describes.

```
python adapters/stdlib/weights-pin/weights_pin.py --card gemma.md --from gemma.gguf

same     gemma.gguf  sha256=9c1e… (as on its card)
```

The card is one with a `willow-model` header, as
[weights-card](../weights-card/) writes: its `sha256` and `bytes` lines are
the pin. The size is compared first, so a file of another size is told
apart without reading it; then the whole file is hashed. A file that
differs says both hashes and both sizes, and the name its card gives when
that isn't the file's: the hash decides, never the name.

```
differs  gemma.gguf: its card says sha256=9c1e… (2489757856 bytes);
         the file is sha256=04ab… (2489757856 bytes)
```

Put it in front of whatever runs the model, so a file that differs never
runs:

```
weights_pin.py --card gemma.md --from gemma.gguf && llama-server -m gemma.gguf
```

Exit codes, the kernel's: 0 the file is the one on its card; 42 it differs;
2 refused (a bad command line, `--from` not a file, `--card` not a model
card with a sha256 and a size).

**Uses:** the kernel's exit codes; [weights-card](../weights-card/)'s card
format, and weights-card itself in its tests.

**Never:** changes the card or the file, runs the model, goes online, or
reads your key.
