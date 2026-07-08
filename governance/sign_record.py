#!/usr/bin/env python3
"""
sign_record.py — Ed25519 signing and verification of VBE evidence records.

Stage E4 of the pipeline: every verification verdict is materialized as a
JSON-LD record and digitally signed, so that the accountability registry can
prove, after the fact, that a given circuit was verified (or blocked) before
any operational use.

Signature scheme: the record is canonicalized as JSON with sorted keys and
no insignificant whitespace (a lightweight JCS-style canonicalization); the
Ed25519 signature of those bytes is attached under "proof". Verification
removes "proof", re-canonicalizes and checks the signature.

Key management: a laboratory keypair is kept under governance/keys/ (hex
files, generated on first use). This demonstrates the mechanism; production
deployments must hold the private key in an HSM.

Usage:
  python3 governance/sign_record.py sign   <record.json> [<output.jsonld>]
  python3 governance/sign_record.py verify <record.jsonld>
"""

import json
import os
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ed25519  # noqa: E402

KEY_DIR = pathlib.Path(__file__).resolve().parent / "keys"
PRIV_PATH = KEY_DIR / "vbe_signing_key.hex"
PUB_PATH = KEY_DIR / "vbe_signing_key.pub.hex"


def canonical_bytes(record: dict) -> bytes:
    """Canonical JSON serialization used as the signing input."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def load_or_create_keypair():
    """Load the laboratory keypair, generating it on first use."""
    if PRIV_PATH.exists():
        secret = bytes.fromhex(PRIV_PATH.read_text().strip())
    else:
        KEY_DIR.mkdir(parents=True, exist_ok=True)
        secret = os.urandom(32)
        PRIV_PATH.write_text(secret.hex() + "\n")
        os.chmod(PRIV_PATH, 0o600)
    public = ed25519.secret_to_public(secret)
    PUB_PATH.write_text(public.hex() + "\n")
    return secret, public


def sign_record(record: dict) -> dict:
    """Attach an Ed25519 proof to a record (returns a new dict)."""
    secret, public = load_or_create_keypair()
    unsigned = {k: v for k, v in record.items() if k != "proof"}
    signature = ed25519.sign(secret, canonical_bytes(unsigned))
    signed = dict(unsigned)
    signed["proof"] = {
        "type": "Ed25519Signature2020",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verificationMethod": f"did:key:z-lab-esbmc-qsharp#{public.hex()[:16]}",
        "publicKeyHex": public.hex(),
        "signatureHex": signature.hex(),
    }
    return signed


def verify_record(record: dict) -> bool:
    """Check the Ed25519 proof of a signed record."""
    proof = record.get("proof")
    if not proof:
        return False
    unsigned = {k: v for k, v in record.items() if k != "proof"}
    try:
        public = bytes.fromhex(proof["publicKeyHex"])
        signature = bytes.fromhex(proof["signatureHex"])
    except (KeyError, ValueError):
        return False
    return ed25519.verify(public, canonical_bytes(unsigned), signature)


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("sign", "verify"):
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)

    cmd, path = sys.argv[1], sys.argv[2]
    with open(path, encoding="utf-8") as f:
        record = json.load(f)

    if cmd == "sign":
        signed = sign_record(record)
        out = sys.argv[3] if len(sys.argv) > 3 else path
        with open(out, "w", encoding="utf-8") as f:
            json.dump(signed, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"[ok] signed record written to {out}")
    else:
        if verify_record(record):
            print(f"[ok] signature VALID: {path}")
        else:
            print(f"[FAIL] signature INVALID: {path}")
            sys.exit(1)


if __name__ == "__main__":
    main()
