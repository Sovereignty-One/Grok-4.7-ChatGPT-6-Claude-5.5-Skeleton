"""Evidence-gated reward proposals; never mutates quota or account balances."""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Callable, Iterable, Literal

Classification = Literal["HUMAN","SUSPICIOUS","BOT","INSUFFICIENT_DATA"]
FEATURE_MULTIPLIERS = {"text":1.0,"voice":1.2,"image":1.5,"video":1.5,"code":2.0,"build":2.0,"companion":1.8,"community":1.3}
ALLOWED_OUTCOMES = {"task_completion","artifact_creation","sustained_conversation","voice_session","image_generation","video_generation","code_run","build_completion","community_contribution"}

@dataclass(frozen=True, slots=True)
class VerifiedOutcome:
    feature: str
    outcome: str
    depth: float
    evidence_ref: str
    occurred_at: str

@dataclass(frozen=True, slots=True)
class RewardDecision:
    status: str
    classification: str
    earned_units: float
    cap_units: float
    verified_outcomes: int
    rejected_outcomes: int
    features: tuple[str,...]
    reason: str

EvidenceVerifier = Callable[[VerifiedOutcome], bool]

def _streak_multiplier(days: int) -> float:
    if isinstance(days,bool) or not isinstance(days,int) or days<0: raise ValueError("streak_days must be a non-negative integer")
    return 1.50 if days>=30 else 1.25 if days>=7 else 1.0

def qualify_rewards(classification: Classification, outcomes: Iterable[VerifiedOutcome], verifier: EvidenceVerifier, *, base_allowance: float=100.0, streak_days: int=0) -> RewardDecision:
    """Compute a proposal; bind verifier to trusted SCAR/evidence authority."""
    if classification not in {"HUMAN","SUSPICIOUS","BOT","INSUFFICIENT_DATA"}: raise ValueError("unsupported classification")
    if not callable(verifier): raise ValueError("trusted evidence verifier callback is required")
    if isinstance(base_allowance,bool) or not isinstance(base_allowance,(int,float)) or not math.isfinite(float(base_allowance)) or base_allowance<=0:
        raise ValueError("base_allowance must be finite and greater than zero")
    streak=_streak_multiplier(streak_days)
    cap=float(base_allowance)*streak*3.0
    if classification in {"BOT","SUSPICIOUS"}:
        return RewardDecision("DENIED",classification,0.0,cap,0,0,(),"bot-risk classification; no reward proposed")
    if classification=="INSUFFICIENT_DATA":
        return RewardDecision("PENDING_REVIEW",classification,0.0,cap,0,0,(),"insufficient session evidence; no reward proposed")
    earned=0.0; verified=0; rejected=0; seen=set(); features=set()
    for event in outcomes:
        if not isinstance(event,VerifiedOutcome):
            rejected+=1; continue
        if (not isinstance(event.evidence_ref,str) or not event.evidence_ref.strip() or event.evidence_ref in seen
            or not isinstance(event.occurred_at,str) or not event.occurred_at.strip()
            or not isinstance(event.outcome,str) or event.outcome not in ALLOWED_OUTCOMES
            or not isinstance(event.feature,str) or event.feature not in FEATURE_MULTIPLIERS
            or isinstance(event.depth,bool) or not isinstance(event.depth,(int,float))
            or not math.isfinite(float(event.depth)) or not 0.0<=float(event.depth)<=1.0):
            rejected+=1; continue
        seen.add(event.evidence_ref)
        try: accepted=verifier(event) is True
        except Exception: accepted=False
        if not accepted:
            rejected+=1; continue
        earned += 10.0*FEATURE_MULTIPLIERS[event.feature]*(0.5+float(event.depth))
        verified+=1; features.add(event.feature)
    earned=min(earned*streak,cap)
    return RewardDecision("QUALIFIED" if verified else "NO_VERIFIED_OUTCOMES",classification,round(earned,4),round(cap,4),verified,rejected,tuple(sorted(features)),"proposal only; quota/balance mutation requires a separate authorized gate")
