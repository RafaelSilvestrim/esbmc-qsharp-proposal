"""
ed25519.py — pure-Python Ed25519 (RFC 8032) signature primitives.

Adapted from the public-domain reference implementation in RFC 8032
Appendix A. Dependency-free on purpose: the governance evidence chain must
be reproducible on any machine with a Python interpreter, with no external
cryptographic packages to install or audit.

NOT constant-time — suitable for signing public verification evidence in a
laboratory setting, not for protecting high-value long-term keys. In
production the signing key must live in an HSM or equivalent.
"""

import hashlib


def _sha512(s: bytes) -> bytes:
    return hashlib.sha512(s).digest()


# Curve constants for edwards25519.
p = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493


def _modp_inv(x: int) -> int:
    return pow(x, p - 2, p)


d = -121665 * _modp_inv(121666) % p
_modp_sqrt_m1 = pow(2, (p - 1) // 4, p)


# Points are stored in extended homogeneous coordinates (X, Y, Z, T),
# with x = X/Z, y = Y/Z, x*y = T/Z.

def _point_add(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % p
    C = 2 * P[3] * Q[3] * d % p
    D = 2 * P[2] * Q[2] % p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % p, G * H % p, F * G % p, E * H % p)


def _point_mul(s, P):
    Q = (0, 1, 1, 0)  # neutral element
    while s > 0:
        if s & 1:
            Q = _point_add(Q, P)
        P = _point_add(P, P)
        s >>= 1
    return Q


def _point_equal(P, Q):
    # x1/z1 == x2/z2  <=>  x1*z2 == x2*z1 (and same for y)
    if (P[0] * Q[2] - Q[0] * P[2]) % p != 0:
        return False
    if (P[1] * Q[2] - Q[1] * P[2]) % p != 0:
        return False
    return True


def _recover_x(y, sign):
    if y >= p:
        return None
    x2 = (y * y - 1) * _modp_inv(d * y * y + 1)
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (p + 3) // 8, p)
    if (x * x - x2) % p != 0:
        x = x * _modp_sqrt_m1 % p
    if (x * x - x2) % p != 0:
        return None
    if (x & 1) != sign:
        x = p - x
    return x


_g_y = 4 * _modp_inv(5) % p
_g_x = _recover_x(_g_y, 0)
G = (_g_x, _g_y, 1, _g_x * _g_y % p)  # base point


def _point_compress(P) -> bytes:
    zinv = _modp_inv(P[2])
    x = P[0] * zinv % p
    y = P[1] * zinv % p
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _point_decompress(s: bytes):
    if len(s) != 32:
        raise ValueError("invalid point length")
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % p)


def _secret_expand(secret: bytes):
    if len(secret) != 32:
        raise ValueError("private key must be 32 bytes")
    h = _sha512(secret)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= (1 << 254)
    return a, h[32:]


def _sha512_modq(s: bytes) -> int:
    return int.from_bytes(_sha512(s), "little") % L


def secret_to_public(secret: bytes) -> bytes:
    """Derive the 32-byte public key from a 32-byte private key."""
    a, _ = _secret_expand(secret)
    return _point_compress(_point_mul(a, G))


def sign(secret: bytes, msg: bytes) -> bytes:
    """RFC 8032 Ed25519 signature (64 bytes) of msg under secret."""
    a, prefix = _secret_expand(secret)
    A = _point_compress(_point_mul(a, G))
    r = _sha512_modq(prefix + msg)
    R = _point_mul(r, G)
    Rs = _point_compress(R)
    h = _sha512_modq(Rs + A + msg)
    s = (r + h * a) % L
    return Rs + int.to_bytes(s, 32, "little")


def verify(public: bytes, msg: bytes, signature: bytes) -> bool:
    """Verify a 64-byte Ed25519 signature. Returns True iff valid."""
    if len(public) != 32 or len(signature) != 64:
        return False
    A = _point_decompress(public)
    if A is None:
        return False
    Rs = signature[:32]
    R = _point_decompress(Rs)
    if R is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= L:
        return False
    h = _sha512_modq(Rs + public + msg)
    sB = _point_mul(s, G)
    hA = _point_mul(h, A)
    return _point_equal(sB, _point_add(R, hA))
