# Engagement Signal and Reward Qualification

This package provides deterministic session-pattern scoring and evidence-gated
reward proposals. It performs no network requests, persistence, identity
verification, quota mutation, or billing operation.

Flow: turns -> score_session -> classification -> qualify_rewards -> proposal.

BOT and SUSPICIOUS sessions are denied. INSUFFICIENT_DATA is pending review.
HUMAN classification is necessary but insufficient: every outcome requires a
trusted evidence-verifier callback. Duplicate evidence references are counted
once; verifier exceptions fail closed. Raw message count and unverified
activity earn nothing.

Feature multipliers preserve the repository design: text 1.0x, voice 1.2x,
image/video 1.5x, code/build 2.0x, companion 1.8x, community 1.3x.
Each verified outcome earns 10 * multiplier * (0.5 + depth), with depth
constrained to [0,1]. Streak bonus is 1.25x at seven days and 1.50x at
thirty days. Proposed headroom is capped at three times adjusted base.

The caller must bind classification to the detector and verifier to a trusted
SCAR/evidence authority. This module only returns a proposal. Separate
authorization, audit, persistence, and quota controls are required to apply it.

Run: python -m unittest discover -s engagement/tests -p 'test_*.py' -v
