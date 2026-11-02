"""tiny_gguf.py: a llama-shaped GGUF model of a few kilobytes, for the tests.

One layer, an embedding of 16, two heads, and a vocabulary of the 256 bytes
with <unk>, <s> and </s>: enough for llama.cpp to load it, tokenize any text
and generate, from weights drawn by a seeded generator, so the same seed
writes the same bytes. What it says is noise; that it says it in this process,
the same way twice, is what the tests need.

    from tiny_gguf import write
    write(Path("tiny.gguf"))
"""

from __future__ import annotations

import random
import struct
from pathlib import Path

ALIGN = 32
EMBD, HEADS, FF, LAYERS, CTX = 16, 2, 32, 1, 256
STR, ARR, U32, F32, I32 = 8, 9, 4, 6, 5
#: llama.cpp's token types
NORMAL, UNKNOWN, CONTROL, BYTE = 1, 2, 3, 6


def _s(text: str) -> bytes:
    raw = text.encode()
    return struct.pack("<Q", len(raw)) + raw


def _kv(key: str, kind: int, value) -> bytes:
    out = _s(key) + struct.pack("<I", kind)
    if kind == STR:
        return out + _s(value)
    if kind == ARR:
        inner, items = value
        out += struct.pack("<IQ", inner, len(items))
        if inner == STR:
            return out + b"".join(_s(x) for x in items)
        fmt = {F32: "<f", I32: "<i"}[inner]
        return out + b"".join(struct.pack(fmt, x) for x in items)
    return out + struct.pack({U32: "<I", F32: "<f"}[kind], value)


def _pad(n: int) -> int:
    return (ALIGN - n % ALIGN) % ALIGN


def write(path: Path, seed: int = 0) -> Path:
    tokens = ["<unk>", "<s>", "</s>"] + [f"<0x{b:02X}>" for b in range(256)]
    types = [UNKNOWN, CONTROL, CONTROL] + [BYTE] * 256
    vocab = len(tokens)
    meta = [
        ("general.architecture", STR, "llama"),
        ("general.name", STR, "tiny"),
        ("general.alignment", U32, ALIGN),
        ("llama.context_length", U32, CTX),
        ("llama.embedding_length", U32, EMBD),
        ("llama.block_count", U32, LAYERS),
        ("llama.feed_forward_length", U32, FF),
        ("llama.attention.head_count", U32, HEADS),
        ("llama.attention.head_count_kv", U32, HEADS),
        ("llama.attention.layer_norm_rms_epsilon", F32, 1e-5),
        ("llama.rope.dimension_count", U32, EMBD // HEADS),
        ("tokenizer.ggml.model", STR, "llama"),
        ("tokenizer.ggml.tokens", ARR, (STR, tokens)),
        ("tokenizer.ggml.scores", ARR, (F32, [0.0] * vocab)),
        ("tokenizer.ggml.token_type", ARR, (I32, types)),
        ("tokenizer.ggml.unknown_token_id", U32, 0),
        ("tokenizer.ggml.bos_token_id", U32, 1),
        ("tokenizer.ggml.eos_token_id", U32, 2),
    ]
    # each tensor's dims in ggml's order, the fastest-changing first
    shapes = [("token_embd.weight", [EMBD, vocab]), ("output_norm.weight", [EMBD]),
              ("output.weight", [EMBD, vocab])]  # fmt: skip
    for i in range(LAYERS):
        shapes += [(f"blk.{i}.attn_norm.weight", [EMBD]),
                   (f"blk.{i}.attn_q.weight", [EMBD, EMBD]),
                   (f"blk.{i}.attn_k.weight", [EMBD, EMBD]),
                   (f"blk.{i}.attn_v.weight", [EMBD, EMBD]),
                   (f"blk.{i}.attn_output.weight", [EMBD, EMBD]),
                   (f"blk.{i}.ffn_norm.weight", [EMBD]),
                   (f"blk.{i}.ffn_gate.weight", [EMBD, FF]),
                   (f"blk.{i}.ffn_up.weight", [EMBD, FF]),
                   (f"blk.{i}.ffn_down.weight", [FF, EMBD])]  # fmt: skip
    rng = random.Random(seed)
    datas, infos, offset = [], b"", 0
    for name, dims in shapes:
        count = 1
        for d in dims:
            count *= d
        norm = name.endswith("norm.weight")
        values = [1.0] * count if norm else [rng.gauss(0, 0.02) for _ in range(count)]
        data = struct.pack(f"<{count}f", *values)
        infos += _s(name) + struct.pack("<I", len(dims))
        infos += b"".join(struct.pack("<Q", d) for d in dims)
        infos += struct.pack("<IQ", 0, offset)  # type F32, offset into the data
        datas.append(data + b"\0" * _pad(len(data)))
        offset += len(datas[-1])
    head = b"GGUF" + struct.pack("<IQQ", 3, len(shapes), len(meta))
    head += b"".join(_kv(*m) for m in meta) + infos
    path.write_bytes(head + b"\0" * _pad(len(head)) + b"".join(datas))
    return path
