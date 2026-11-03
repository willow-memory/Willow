"""ed25519.py: Ed25519 signatures (RFC 8032), in the standard library only.

    public(seed)            the 32-byte public key of a 32-byte secret seed
    sign(seed, message)     a 64-byte signature
    check(public, message, signature)   True only for a good one

Written from RFC 8032's section 5.1 and held to its test vectors and to
random keys and messages against an audited library (test_share.py). It is
plain Python: correct, not constant-time. A signature made here can leak
timing to someone who can watch this machine sign many times; it is for
saying who sent a package, on your own machine, not for a server under load.
"""

from __future__ import annotations

import hashlib

P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)


def _add(a: tuple, b: tuple) -> tuple:
    """Two points added, in extended coordinates (X, Y, Z, T)."""
    x = (a[1] - a[0]) * (b[1] - b[0]) % P
    y = (a[1] + a[0]) * (b[1] + b[0]) % P
    c = 2 * a[3] * b[3] * D % P
    d = 2 * a[2] * b[2] % P
    e, f, g, h = y - x, d - c, d + c, y + x
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _times(s: int, p: tuple) -> tuple:
    q = (0, 1, 1, 0)  # the neutral point
    while s > 0:
        if s & 1:
            q = _add(q, p)
        p = _add(p, p)
        s >>= 1
    return q


def _same(a: tuple, b: tuple) -> bool:
    return (a[0] * b[2] - b[0] * a[2]) % P == 0 and (a[1] * b[2] - b[1] * a[2]) % P == 0


def _x_of(y: int, sign: int) -> int | None:
    if y >= P:
        return None
    x2 = (y * y - 1) * pow(D * y * y + 1, P - 2, P) % P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = x * SQRT_M1 % P
    if (x * x - x2) % P:
        return None
    return P - x if (x & 1) != sign else x


_GY = 4 * pow(5, P - 2, P) % P
_GX = _x_of(_GY, 0)
BASE = (_GX, _GY, 1, _GX * _GY % P)


def _packed(p: tuple) -> bytes:
    zi = pow(p[2], P - 2, P)
    x, y = p[0] * zi % P, p[1] * zi % P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _unpacked(s: bytes) -> tuple | None:
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    sign, y = y >> 255, y & ((1 << 255) - 1)
    x = _x_of(y, sign)
    return None if x is None else (x, y, 1, x * y % P)


def _h(data: bytes) -> int:
    return int.from_bytes(hashlib.sha512(data).digest(), "little")


def _expanded(seed: bytes) -> tuple[int, bytes]:
    if not isinstance(seed, bytes) or len(seed) != 32:
        raise ValueError("a seed is 32 bytes")
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def public(seed: bytes) -> bytes:
    a, _ = _expanded(seed)
    return _packed(_times(a, BASE))


def sign(seed: bytes, message: bytes) -> bytes:
    a, prefix = _expanded(seed)
    pub = _packed(_times(a, BASE))
    r = _h(prefix + message) % L
    big_r = _packed(_times(r, BASE))
    k = _h(big_r + pub + message) % L
    return big_r + ((r + k * a) % L).to_bytes(32, "little")


def check(pub: bytes, message: bytes, signature: bytes) -> bool:
    if not isinstance(pub, bytes) or not isinstance(signature, bytes):
        return False
    if len(pub) != 32 or len(signature) != 64:
        return False
    a = _unpacked(pub)
    r = _unpacked(signature[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= L:
        return False
    k = _h(signature[:32] + pub + message) % L
    return _same(_times(s, BASE), _add(r, _times(k, a)))
