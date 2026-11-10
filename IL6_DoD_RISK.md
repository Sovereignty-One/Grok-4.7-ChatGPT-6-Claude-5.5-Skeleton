# IL6 (DoD Impact Level 6) — Risk Statement: Single Cloud Dependency

**Scope:** Sovereignty / SuperGrok dashboard operating on bare-metal, air-gapped
iOS hardware. This statement records the IL6 posture and the residual risk of any
**single cloud dependency**.

## Posture

The dashboard is built to run with **zero external callouts** (see
`GATE_ONE_MLDSA87_MERKLE.md` and the `SovereignGuard` block in
`SGHv119_Newest.html` / `SGHv119-local.html`):

- No external AI API (Anthropic / OpenAI / xAI) — hard-blocked by guard + CSP.
- No Google, no Meta, no CDN, no remote fonts/frames/images.
- WebSocket is inert; `fetch`/`XHR` permit **self + loopback only**.
- All keys derived on-device; PQ gate via ML-DSA-87 + Merkle.

IL6 handles classified information up to **SECRET**. It requires a dedicated,
isolated infrastructure with no shared tenancy and no commodity internet path.

## Single Cloud Dependency — Risk

A **single cloud dependency** (one provider, one region, one control plane) is a
**HIGH** risk for IL6 because it creates:

| Risk | Impact (IL6) | Mitigation in this build |
|---|---|---|
| Availability — provider/region outage | Mission loss; no failover | App runs fully **air-gapped on-device**; cloud is optional, never required |
| Confidentiality — shared control plane / lawful-access | Spillage of SECRET | No data leaves device; all crypto on-device; CSP `connect-src 'self'` + loopback |
| Integrity — supply-chain of remote code (CDN/API) | Tampered runtime | No remote code; Three.js/CDN removed; Merkle + ML-DSA-87 attest the runtime |
| Sovereignty — vendor key custody | Loss of key control | **No external keys** — operator-derived only (PBKDF2/HKDF, Secure Enclave) |
| Concentration — one provider = one failure domain | Systemic IL6 outage | Architecture is provider-agnostic and offline-first; bridge is loopback-only |

## Residual Risk & Decision

With the air-gap guard active, the dashboard carries **no runtime cloud
dependency**. Any optional local bridge is loopback (`127.0.0.1:9897-9899`) and
fails closed when absent. The **single-cloud risk is therefore reduced from HIGH
to LOW** for the dashboard itself; any IL6 deployment that *adds* a cloud component
MUST provide a second, independent failure domain (multi-region or
multi-provider) before that component is relied upon for availability.

**Accept** for the on-device dashboard. **Do not accept** a single cloud
dependency for any IL6 service path.
