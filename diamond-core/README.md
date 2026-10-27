# Diamond Lattice 5D Core v0.1

Contract-first reference implementation for sovereign AI memory.

## Scope

v0.1 intentionally contains no Metal, ANE, unified-memory optimization, physical allocator, networking, model runtime, or cloud integration.

The model-facing boundary is `MemoryWindow`. Physical placement is absent from the API by design.

## Contract

Every access follows the fixed fail-closed sequence:

`identity -> temporal -> context -> provenance -> authority`

The canonical object identity is a BLAKE3 commitment over length-delimited:

`namespace + uuid + content_hash + version + provenance_root`

Capabilities are opaque, scoped to explicit operations, bound to the current policy hash and epoch, and expire at a fixed time.

The poisoning state machine permits only:

`MODEL_GENERATED -> UNVERIFIED -> REVIEWED -> POLICY_APPROVED -> AUTHORITATIVE`

Every authority-changing transition emits a minimal SCAR event containing evidence and authorization proof. There is no direct promotion from model-generated content to authoritative memory.

## Invariants

The test suite contains executable negative cases for I-001 through I-015. I-013 through I-015 specifically establish that policy is encapsulated, model capabilities cannot be expanded through the public API, and no physical-tier interface exists in v0.1 that can bypass authority.

## Test

```bash
cd diamond-core
cargo test --all-targets
```

A passing v0.1 means the contract tests pass. It does not claim hardware acceleration or production durability.
