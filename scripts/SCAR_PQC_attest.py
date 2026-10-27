#!/usr/bin/env python3
"""Create a fail-closed, BLAKE3 + ML-DSA-87 signed SCAR pipeline attestation.

The signing key is runner-local. It is never written to the repository or emitted
in logs. Verification uses the public key saved beside the private key.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import sys
import time
from pathlib import Path
from typing import Any

from blake3 import blake3

try:
    import oqs
except ImportError as exc:  # pragma: no cover - exercised by the fail-closed path
    raise SystemExit("SCAR PQC gate requires liboqs-python; refusing unsigned evidence") from exc

ALGORITHM = "ML-DSA-87"
DEFAULT_KEY_DIR = Path(os.environ.get("SCAR_PQC_KEY_DIR", ".scar/pqc"))
DEFAULT_OUTPUT = Path(os.environ.get("SCAR_PQC_OUTPUT", ".scar/scar-attestation.json"))


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load_or_create_signer(key_dir: Path):
    key_dir.mkdir(parents=True, exist_ok=True)
    private_path = key_dir / f"{ALGORITHM}.priv"
    public_path = key_dir / f"{ALGORITHM}.pub"
    signer = oqs.Signature(ALGORITHM)
    if private_path.exists() and public_path.exists():
        private_key = private_path.read_bytes()
        public_key = public_path.read_bytes()
        signer.import_secret_key(private_key)
    else:
        public_key = signer.generate_keypair()
        private_key = signer.export_secret_key()
        private_path.write_bytes(private_key)
        public_path.write_bytes(public_key)
        private_path.chmod(0o600)
    return signer, public_key


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", choices=("PASS", "FAIL"), required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--key-dir", type=Path, default=DEFAULT_KEY_DIR)
    args = parser.parse_args()

    signer, public_key = load_or_create_signer(args.key_dir)
    payload = {
        "schema": "SCAR-PQC-ATTESTATION-v1",
        "timestamp": int(time.time()),
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
        "commit": args.commit,
        "status": args.status,
        "algorithm": ALGORITHM,
    }
    digest = blake3(canonical_bytes(payload)).hexdigest()
    signed_payload = {**payload, "blake3": digest}
    message = canonical_bytes(signed_payload)
    signature = signer.sign(message)
    verified = signer.verify(message, signature, public_key)
    if not verified:
        print("SCAR_PQC_VERIFY=FAIL", file=sys.stderr)
        return 1

    attestation = {
        "payload": signed_payload,
        "signature": signature.hex(),
        "public_key": public_key.hex(),
        "verification": {"algorithm": ALGORITHM, "verified": True},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(attestation, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("SCAR_PQC_ALGORITHM=ML-DSA-87")
    print(f"SCAR_BLAKE3={digest}")
    print("SCAR_PQC_VERIFY=PASS")
    print(f"SCAR_ATTESTATION={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
