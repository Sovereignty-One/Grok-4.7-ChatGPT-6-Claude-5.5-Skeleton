# Security review status — SCAR maintenance PR

## Scope
This patch adds a SHA3-512 hash-chain integrity verifier and tests. It does not implement or validate PQC signatures, TPM/Secure Enclave attestation, signer identity, or authorization.

## Known workflow risks
- Third-party GitHub Actions are currently referenced by mutable version tags rather than full commit SHAs; pin them to reviewed immutable SHAs before treating supply-chain hardening as complete.
- The workflow only triggers for listed branch patterns and pull requests targeting `Collaboration` or `main`. Confirm the repository's actual default/integration branches and adjust triggers to the documented policy.
- Genesis JSON under `scar/0001-genesis.json` is descriptive metadata; `SCAR.jsonl` is the canonical hash-checked record. Do not treat the JSON metadata file as signed evidence.
- Hash chaining is not tamper-proof against an actor who can rewrite the entire file and recompute all hashes. Protect history with signed commits, access controls, and external trusted checkpoints if that threat is in scope.
- Full test execution and GitHub Actions results must be checked against the latest candidate commit before merge.

## Required final gates
1. Run Python compilation and all SCAR tests.
2. Run verifier against committed `SCAR.jsonl`.
3. Confirm negative tests fail for tampered payloads and broken links.
4. Validate `schemas/chat-handoff.schema.json` with a Draft 2020-12 validator and format checking.
5. Review complete diff and verify branch base freshness.
6. Confirm required checks pass on the latest candidate SHA.
7. Keep PR unmerged until the owner approves.
