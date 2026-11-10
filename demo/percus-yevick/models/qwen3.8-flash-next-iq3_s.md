<!-- willow-model
name: Qwen3.8 Flash Next IQ3_S (Strata GSQ-RCO pack)
sha256: 4c1eb2ceb4915e1192f4f386021897bde56a97f40a0bb78bb86465e0f7d2aca3
runs: the ML specialist's machine, Strata 0.1.56, in an opencode session
licence: not known here
limits: not run here; its settings are as the ML specialist reported them
-->
# Qwen3.8 Flash Next, IQ3_S

The model behind the ML specialist's interim report and transcript, as they
reported it on 2026-11-05. It was not run here: it needs about 70 GB, and this
card is written from what they sent, not read from the weights file.

- **Weights**, two GGUF files, SHA-256 as they sent them:
  - `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf`:
    `4c1eb2ceb4915e1192f4f386021897bde56a97f40a0bb78bb86465e0f7d2aca3`
    (the `sha256` above)
  - `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf`:
    `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113`
- **Runtime**: Strata 0.1.56, speculative decoding with DFlash2 drafts and
  MTP, int8 KV cache, a 262,144-token context.
- **Session**: opencode, with code execution and web fetches; a 157.5k
  reasoning budget; compaction keeping 30k.
- **Sampling**: opencode's default temperature, taken to be 0.8 and not
  confirmed; no seed.
