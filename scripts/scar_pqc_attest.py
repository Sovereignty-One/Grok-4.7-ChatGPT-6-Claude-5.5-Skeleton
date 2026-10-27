#!/usr/bin/env python3
"""Fail-closed SCAR JSONL hash-chain verifier.

Integrity verification only. This module does not claim to verify PQC signatures,
identity, authorization, TPM, Secure Enclave, or hardware attestation.
"""
import argparse, hashlib, hmac, json, sys
from pathlib import Path

def canonical(record):
    payload = dict(record)
    payload.pop("hash", None)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def digest(record):
    return hashlib.sha3_512(canonical(record)).hexdigest()

def verify(path):
    if not path.is_file():
        return False, f"FAIL: records file missing: {path}"
    previous = None
    count = 0
    try:
        with path.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    return False, f"FAIL: blank record at line {number}"
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    return False, f"FAIL: invalid JSON at line {number}: {exc}"
                if not isinstance(record, dict):
                    return False, f"FAIL: record at line {number} must be an object"
                supplied = record.get("hash")
                if not isinstance(supplied, str) or len(supplied) != 128:
                    return False, f"FAIL: missing/invalid SHA3-512 hash at line {number}"
                if previous is None:
                    if record.get("hash_prev") not in (None, "0" * 128):
                        return False, f"FAIL: unexpected genesis hash_prev at line {number}"
                elif record.get("hash_prev") != previous:
                    return False, f"FAIL: missing/broken hash_prev at line {number}"
                if not hmac.compare_digest(supplied, digest(record)):
                    return False, f"FAIL: record hash mismatch at line {number}"
                previous = supplied
                count += 1
    except OSError as exc:
        return False, f"FAIL: cannot read records: {exc}"
    if count == 0:
        return False, "FAIL: no SCAR records"
    return True, f"PASS: {count} record(s); hash integrity only, signatures NOT verified"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", default="SCAR.jsonl")
    args = parser.parse_args()
    ok, message = verify(Path(args.records))
    print(message)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
