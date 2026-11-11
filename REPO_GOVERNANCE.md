# Repository Engineering and Agent Governance

**Status:** Proposed repository-wide mandatory rules. **Scope:** every repository and every agent/tool contributing code.  
**Authority:** repository owner and branch-protection rules prevail. This document does not grant permission to merge, deploy, publish releases, or rotate credentials.

## 1. Establish the correct base before editing
1. Query repository metadata and identify the configured default branch; do not assume it is `main`.
2. Identify the target component's maintained integration/base branch from repository docs, protection rules, CODEOWNERS, and recent history. If it differs from the default branch, use the component's documented base.
3. Fetch/re-read the selected base immediately before work; record its full commit SHA and cleanliness/freshness evidence. Create a dedicated agent branch from that exact base.
4. If the base moved during work, rebase/update the agent branch and repeat affected checks. Never push directly to the base or force-push without explicit owner approval.
5. Never infer that a branch exists or that CI passed. Verify via repository evidence.

## 2. Read before writing — literal review gate
Before distributing code, patches, commands, or config, inspect the complete relevant files and their call sites, tests, dependency manifests, workflow consumers, and policy docs. Review every line, identifier, token, delimiter, syntax element, punctuation mark, and relevant Unicode character in the proposed diff. Check exact paths and case sensitivity. Search for all references and callers. If the full content cannot be retrieved, mark the gate **BLOCKED**; do not claim a complete review.

## 3. Patch discipline and proof
1. State the issue and threat model; prefer the smallest coherent patch. Do not bundle unrelated refactors.
2. Show the exact diff and changed-file list. Explain behavior, compatibility, migration, rollback, and residual risk.
3. Run relevant unit tests, negative/security tests, static checks, and a smoke test against the candidate branch. Record exact commands, environment, exit codes, commit SHA, and logs/artifact links. Distinguish **PASS**, **FAIL**, **NOT RUN**, **BLOCKED**, **STALE**, and **UNPROVEN**.
4. Never say “tested”, “green”, “secure”, or “pass” without evidence tied to the exact candidate SHA. A badge or successful unrelated workflow is not proof.
5. Discuss risks/rewards and pros/cons before asking for merge approval. If a mandatory gate is not PASS, block merge/release recommendations.

## 4. Security and autonomy
- Fail closed for authentication, authorization, signature/attestation verification, policy checks, provenance, and required security scans. Missing evidence is not PASS.
- A client-supplied role, session identifier, hash, timestamp, or verdict is data, not authority. Verify identity and signatures independently.
- Least privilege: read-only by default; maintenance jobs must not merge, deploy, publish, delete, rotate keys, or modify protected branches.
- No shell interpolation for untrusted input; constrain subprocesses, network destinations, payload sizes, timeouts, and filesystem paths.
- Keep public repository visibility and normal public GitHub networking intact. Local/offline device requirements are separate and must not silently disable repository access.
- Never place credentials, tokens, private keys, personal secrets, or sensitive chat content in commits, SCAR records, issue comments, or public artifacts.

## 5. CI and scheduled maintenance
- Audit all workflow triggers, schedules, permissions, concurrency groups, jobs, duplicate coverage, external actions, and suppressed failures before adding automation.
- Prefer one minimal, read-only daily maintenance workflow at **00:00 UTC** unless the owner specifies a different timezone. Avoid overlapping schedules; use concurrency and timeouts. Schedules may be delayed by GitHub.
- Maintenance may inspect workflows, dependency/security alerts, stale branches/PRs, provenance, and tests, then publish a minimal 5W1H report. It must not self-approve or auto-merge code.
- Pin third-party actions to full commit SHAs. Use least-privilege workflow permissions and avoid `continue-on-error` for mandatory gates.
- An unavailable scanner or missing input is **BLOCKED/FAIL**, not a successful security result.

## 6. SCAR / provenance
Every meaningful change should record **Who, What, When, Where, Why, How**, repository, base branch/SHA, candidate branch/SHA, changed paths, test evidence, risks, decision, and model/tool attribution when known. Distinguish author, reviewer, executor, and approver. Record timestamps in UTC ISO 8601. Hashes establish integrity only when computed and verified; signatures establish signer identity only when cryptographically verified against a trusted key. Do not self-assert verification.

## 7. Chat handoff and recovery
Use `schemas/chat-handoff.schema.json` for portable chat/work recovery records. Include company/provider, model identifier, UTC timestamp, conversation scope, messages or a referenced protected archive, current task/state, decisions, changed files, branch/base SHA, tests, risks, and next action. Never include secrets. A company/model label or timestamp is attribution metadata, not a digital signature. Populate signature fields only when an actual signature was generated and independently verifiable.

## 8. Required review report
Each patch report must contain:
- Base branch and full base SHA; candidate branch and full candidate SHA.
- Complete changed-file list and diff.
- Read/coverage gate status.
- Tests and smoke-test evidence tied to candidate SHA.
- Security findings fixed, residual findings, and limitations.
- Risks/rewards and pros/cons.
- 5W1H provenance record.
- Explicit decision: **PASS**, **REJECT**, or **BLOCKED**. Never merge automatically.
