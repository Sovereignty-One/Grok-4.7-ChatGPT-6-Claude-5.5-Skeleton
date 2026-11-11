"""Engagement scoring and evidence-gated reward proposals."""
from .engagement_bot_finder import Turn, coerce_turns, score_session
from .reward_qualification import VerifiedOutcome, RewardDecision, qualify_rewards
__all__ = ["Turn","coerce_turns","score_session","VerifiedOutcome","RewardDecision","qualify_rewards"]
