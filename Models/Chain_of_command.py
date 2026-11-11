#!/usr/bin/env python3

"""
Chain of Command AI
===================

On-device Shortcut controller for:

    USER
      |
      v
    Heavy Controller
      |
      v
    Model Router
      |
      +------ Grok
      +------ GPT / Codex
      +------ Claude
      +------ Copilot
      +------ DuckAI
      +------ DevAssist420 / Sovereignty AI Hybrid
      |
      v
    Council
      |
      v
    Heavy Judge
      |
      +------ PASS
      +------ REWRITE
      +------ YANK
      +------ COUNCIL_OVERRIDE
      |
      v
    Final Output
      |
      +------ SHA3-512
      +------ optional Ed25519 signature
      +------ SCAR / REPMHL
      |
      v
    Shortcut
      |
      +------ Speak
      +------ Show
      +------ Save

IMPORTANT:
The MODEL_REGISTRY is routing metadata.
It does not itself execute or prove availability of a
remote/provider model.

Actual model execution belongs behind the adapter boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ============================================================================
# MODEL REGISTRY
# ============================================================================

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {

    # ------------------------------------------------------------------------
    # xAI
    # ------------------------------------------------------------------------

    "SuperGrok-4.8": {
        "provider": "xai",
        "policy": "strict daily use",
        "role": "main_daily",
        "enabled": True,
        "modalities": ["text"],
        "execution_status": "adapter_unbound",
    },

    "Grok-4.8": {
        "provider": "xai",
        "policy": "strict fallback",
        "role": "fallback_candidate",
        "enabled": True,
        "modalities": ["text"],
        "execution_status": "adapter_unbound",
    },

    "Grok-4.7": {
        "provider": "xai",
        "policy": "strict fallback",
        "role": "fallback",
        "enabled": True,
    },

    # ------------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------------

    "GPT-6.1-Terra": {
        "provider": "openai",
        "policy": "strict daily use",
        "role": "preferred_openai_text_and_voice",
        "enabled": True,
        "modalities": ["text", "voice"],
        "execution_status": "adapter_unbound",
    },

    # Compatibility alias only; new routing selects GPT-6.1-Terra.
    "GPT-6-Terra": {
        "provider": "openai",
        "policy": "compatibility alias",
        "role": "deprecated_alias",
        "enabled": False,
        "alias_for": "GPT-6.1-Terra",
    },

    "GPT-6.1-Sol": {
        "provider": "openai",
        "policy": "strict daily use",
        "role": "difficult_tasks",
        "enabled": True,
    },

    "gpt-6.1-Astra": {
        "provider": "openai",
        "policy": "strict daily use",
        "role": "highest_reasoning_escalation",
        "enabled": True,
    },

    "GPT-DayBreak-Red-latest": {
        "provider": "openai",
        "policy": "strict security",
        "role": "continuous_security",
        "enabled": True,
    },

    "GPT-5.7-Codex-Cyber": {
        "provider": "openai",
        "policy": "strict code syntax diff linting",
        "role": "security_code_backup",
        "enabled": True,
    },

    # ------------------------------------------------------------------------
    # GitHub
    # ------------------------------------------------------------------------

    "GitHub Copilot": {
        "provider": "github",
        "policy": "strict limited per session",
        "role": "limited_code_helper",
        "enabled": True,
    },

    # ------------------------------------------------------------------------
    # DuckDuckGo
    # ------------------------------------------------------------------------

    "DuckAI": {
        "provider": "duckduckgo",
        "policy": "strict privacy",
        "role": "privacy_lane",
        "enabled": True,
    },

    # ------------------------------------------------------------------------
    # Anthropic
    # ------------------------------------------------------------------------

    "Claude-Sonnet-5.5": {
        "provider": "anthropic",
        "policy": "review and building dashboards",
        "role": "main_review",
        "enabled": True,
    },

    "Claude-Opus-5.5": {
        "provider": "anthropic",
        "policy": "strict review medical escalation",
        "role": "review_medical_escalation",
        "enabled": True,
    },

    "Claude-Fable-5.1": {
        "provider": "anthropic",
        "policy": "strict medical",
        "role": "medical",
        "enabled": True,
    },

    "Claude-Mythos-5.1": {
        "provider": "anthropic",
        "policy": "strict production live tasks",
        "role": "medical_production",
        "enabled": True,
    },

    # ------------------------------------------------------------------------
    # Hybrid / sovereign routing
    # ------------------------------------------------------------------------

    "DevAssist420 + Sovereignty AI Hybrid": {
        "provider": "local_hybrid",
        "policy": "daily council router",
        "role": "daily_council_router",
        "enabled": True,
    },
}


# ============================================================================
# ROUTING POLICY
# ============================================================================

ROUTING_POLICY: Dict[str, Any] = {
    "version": "2.0",

    "description": (
        "SuperGrok Heavy Judge routing with defined trigger "
        "strategy, council arbitration, yank behavior, "
        "and structured verdicts."
    ),

    "defaults": {
        "primary_model": "SuperGrok-4.8",
        "fallback_model": "Grok-4.7",
        "openai_model": "GPT-6.1-Terra",
        "heavy_judge": "SuperGrok-5.7-hybrid",
        "use_judge": True,
    },

    "heavy_judge": {
        "enabled": True,
        "role": "final_quality_gate",

        # Your original specification says the Judge is not normally
        # the primary responder, but must be able to act as final gate.
        "never_use_as_primary": False,

        "trigger_strategy": {
            "always_for": [
                "medical",
                "education",
                "legal",
                "financial",
                "safety_critical",
                "security",
            ],

            "always_when": "use_judge == true",

            "general_queries": {
                "sampling_rate": 0.08,
                "description": (
                    "Sample approximately eight percent of general "
                    "queries for quality control."
                ),
            },
        },

        "activation_thresholds": {
            "medical_education": 0.0,
            "general_default": 0.75,
            "dynamic_escalation": True,
        },

        "yank_behavior": {
            "low_risk": "rewrite_safer",
            "medium_risk": "replace_with_safe_generic",
            "high_critical_risk": "polite_refusal_with_explanation",
        },

        "verdict_format": {
            "timestamp": "ISO8601_UTC",
            "risk_score": "float_0_to_1",
            "action": [
                "pass",
                "rewrite",
                "yank",
                "council_override",
            ],
            "hash": "SHA3-512_of_final_output",
            "signature": "optional_ed25519",
            "context": "string_description_of_input_scenario",
        },

        "integration": {
            "location": "ChainOfCommandRouter.consume_with_routing",
            "condition": "when use_judge=True",
            "position": "final_gatekeeper_before_user_response",
        },
    },

    "risk_scoring": {
        "enabled": True,
        "max_score": 100,

        "weights": {
            "context": 45,
            "user_role": 20,
            "request_type": 35,
        },

        "context_keywords": {
            "medical": 50,
            "legal": 45,
            "safety_critical": 50,
            "education": 30,
            "financial": 25,
            "security": 50,
            "privacy": 25,
            "general": 10,
        },
    },

    "model_selection": {
        "low_risk": {
            "prefer": "fastest",
            "models": [
                "SuperGrok-4.8",
            ],
        },

        "medium_risk": {
            "prefer": "balanced",
            "models": [
                "SuperGrok-4.7",
                "GPT-6.1-Terra",
                "GPT-5.7-Codex-Cyber",
                "Claude-Sonnet-5.5",
                "Claude-Opus-5.5",
            ],
        },

        "high_risk": {
            "prefer": "highest_quality",
            "models": [
                "Claude-Fable-5.1",
                "Claude-Mythos-5.1",
                "Claude-Opus-5.5",
                "gpt-6.1-Astra",
                "GPT-DayBreak-Red-latest",
                "GPT-5.7-Codex-Cyber",
            ],
            "force_heavy_judge": True,
        },
    },

    "fallback": {
        "when_bridge_offline": "local_fallback",
        "local_models": [
            "Grok-4.7",
            "DevAssist420 + Sovereignty AI Hybrid",
            "GPT-6.1-Terra",
        ],
    },
}


# ============================================================================
# RISK KEYWORDS
# ============================================================================

RISK_KEYWORDS: Dict[str, List[str]] = {

    "medical": [
        r"\bmedical\b",
        r"\bmedicine\b",
        r"\bdiagnos(?:e|is|ing)\b",
        r"\bsymptom(?:s)?\b",
        r"\bmedication(?:s)?\b",
        r"\bdrug(?:s)?\b",
        r"\bdos(?:e|age)\b",
        r"\btreatment\b",
        r"\btherapy\b",
        r"\bclinical\b",
        r"\bdoctor\b",
        r"\bhospital\b",
    ],

    "legal": [
        r"\blegal\b",
        r"\blaw\b",
        r"\blawyer\b",
        r"\battorney\b",
        r"\blawsuit\b",
        r"\bcourt\b",
        r"\bcontract\b",
        r"\bliability\b",
    ],

    "safety_critical": [
        r"\bemergency\b",
        r"\bdanger\b",
        r"\bunsafe\b",
        r"\bsafety\b",
        r"\bcritical\b",
        r"\bexplosive\b",
        r"\bweapon\b",
    ],

    "security": [
        r"\bsecurity\b",
        r"\bcyber\b",
        r"\bvulnerability\b",
        r"\bexploit\b",
        r"\bmalware\b",
        r"\bransomware\b",
        r"\bcredential\b",
        r"\bsecret\b",
        r"\btoken\b",
        r"\bprivate key\b",
        r"\bcertificate\b",
        r"\bcryptograph(?:y|ic)\b",
        r"\bauthorization\b",
        r"\bauthentication\b",
    ],

    "financial": [
        r"\bfinancial\b",
        r"\bfinance\b",
        r"\bbank\b",
        r"\binvest(?:ment|ing)\b",
        r"\bstock(?:s)?\b",
        r"\bloan\b",
        r"\bmortgage\b",
        r"\btax(?:es)?\b",
        r"\bpayment\b",
    ],

    "education": [
        r"\beducation\b",
        r"\bschool\b",
        r"\bstudent\b",
        r"\bteacher\b",
        r"\bhomework\b",
        r"\bexam\b",
        r"\bcurriculum\b",
    ],

    "privacy": [
        r"\bprivacy\b",
        r"\bpersonal data\b",
        r"\bpii\b",
        r"\bprivate\b",
        r"\bsurveillance\b",
        r"\btracking\b",
    ],
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class RoutingDecision:
    primary_model: str
    council_models: List[str]
    context: str
    risk_score: float
    risk_categories: List[str]
    use_judge: bool
    reason: str
    modality: str = "text"
    provider_preference: str = "default"


# ============================================================================
# CRYPTOGRAPHIC HELPERS
# ============================================================================

def sha3_512(value: str) -> str:
    """
    SHA3-512 over UTF-8 bytes.
    """
    return hashlib.sha3_512(
        value.encode("utf-8")
    ).hexdigest()


def utc_timestamp() -> str:
    """
    ISO8601 UTC timestamp.
    """
    return time.strftime(
        "%Y-%m-%dT%H:%M:%SZ",
        time.gmtime(),
    )


# ============================================================================
# HEAVY JUDGE
# ============================================================================

class HeavyJudge:

    def __init__(
        self,
        model_name: str = "SuperGrok-5.7-hybrid",
        repmhl: Optional[Any] = None,
    ):
        self.model = model_name
        self.repmhl = repmhl

        self.strictness = {
            "medical": 0.95,
            "education": 0.90,
            "legal": 0.95,
            "financial": 0.90,
            "security": 0.95,
            "safety_critical": 0.99,
            "privacy": 0.85,
            "general": 0.75,
        }

    # ------------------------------------------------------------------------
    # MAIN REVIEW
    # ------------------------------------------------------------------------

    def review(
        self,
        original_output: str,
        context: str,
        risk_score: float = 0.0,
        risk_categories: Optional[List[str]] = None,
        council_disagreement: bool = False,
    ) -> Dict[str, Any]:

        if not isinstance(original_output, str):
            raise TypeError("original_output must be a string")

        if not isinstance(context, str):
            raise TypeError("context must be a string")

        risk_categories = risk_categories or []

        verdict = self._generate_verdict(
            original_output,
            context,
            risk_score,
            risk_categories,
            council_disagreement,
        )

        action = verdict["action"]

        if action == "yank":
            final_output = self._safe_replacement(
                original_output,
                context,
            )

        elif action == "rewrite":
            final_output = self._safe_rewrite(
                original_output,
                context,
            )

        else:
            final_output = original_output

        # IMPORTANT:
        # The digest belongs to the ACTUAL FINAL OUTPUT,
        # not the rejected/intermediate output.
        verdict["hash"] = sha3_512(final_output)

        verdict["final_output_length"] = len(final_output)

        self._log_to_repmhl(
            verdict=verdict,
            final_output=final_output,
        )

        return {
            "final_output": final_output,
            "verdict": verdict,
            "judge_model": self.model,
        }

    # ------------------------------------------------------------------------
    # VERDICT
    # ------------------------------------------------------------------------

    def _generate_verdict(
        self,
        text: str,
        context: str,
        risk_score: float,
        risk_categories: List[str],
        council_disagreement: bool,
    ) -> Dict[str, Any]:

        detected_categories = self._detect_categories(text)

        merged_categories = sorted(
            set(risk_categories).union(detected_categories)
        )

        text_risk = self._calculate_text_risk(
            merged_categories
        )

        context_key = context.strip().lower()

        context_prior = self.strictness.get(
            context_key,
            self.strictness["general"],
        )

        normalized_external_risk = max(
            0.0,
            min(1.0, float(risk_score)),
        )

        calculated_risk = max(
            normalized_external_risk,
            text_risk,
            context_prior if context_key in self.strictness
            and context_key != "general"
            else 0.0,
        )

        if council_disagreement:
            calculated_risk = min(
                1.0,
                calculated_risk + 0.15,
            )

        # ------------------------------------------------------------
        # Determine action
        # ------------------------------------------------------------

        if calculated_risk >= 0.90:
            action = "yank"

        elif calculated_risk >= 0.65:
            action = "rewrite"

        elif council_disagreement and calculated_risk >= 0.50:
            action = "council_override"

        else:
            action = "pass"

        return {
            "timestamp": utc_timestamp(),
            "risk_score": round(calculated_risk, 6),
            "action": action,
            "hash": None,
            "signature": None,
            "context": context,
            "risk_categories": merged_categories,
            "council_disagreement": council_disagreement,
            "judge_model": self.model,
        }

    # ------------------------------------------------------------------------
    # CATEGORY DETECTION
    # ------------------------------------------------------------------------

    def _detect_categories(
        self,
        text: str,
    ) -> List[str]:

        categories: List[str] = []

        for category, patterns in RISK_KEYWORDS.items():

            for pattern in patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    categories.append(category)
                    break

        return categories

    # ------------------------------------------------------------------------
    # TEXT RISK
    # ------------------------------------------------------------------------

    def _calculate_text_risk(
        self,
        categories: List[str],
    ) -> float:

        weights = {
            "medical": 0.95,
            "legal": 0.90,
            "safety_critical": 1.00,
            "security": 0.95,
            "financial": 0.75,
            "education": 0.60,
            "privacy": 0.70,
        }

        if not categories:
            return 0.0

        return min(
            1.0,
            max(
                weights.get(category, 0.50)
                for category in categories
            ),
        )

    # ------------------------------------------------------------------------
    # SAFE REWRITE
    # ------------------------------------------------------------------------

    def _safe_rewrite(
        self,
        original_output: str,
        context: str,
    ) -> str:

        notice = (
            "\n\n"
            "[Heavy Judge review: "
            "the response was retained with a safety/context "
            "qualification.]"
        )

        return original_output.rstrip() + notice

    # ------------------------------------------------------------------------
    # YANK
    # ------------------------------------------------------------------------

    def _safe_replacement(
        self,
        original_output: str,
        context: str,
    ) -> str:

        return (
            "The requested response was withheld by the Heavy Judge "
            "because the detected risk level requires additional "
            "review before the content can be released."
        )

    # ------------------------------------------------------------------------
    # REPMHL / SCAR
    # ------------------------------------------------------------------------

    def _log_to_repmhl(
        self,
        verdict: Dict[str, Any],
        final_output: str,
    ) -> None:

        evidence = {
            "event": "heavy_judge_verdict",
            "timestamp": verdict["timestamp"],
            "judge_model": verdict["judge_model"],
            "context": verdict["context"],
            "risk_score": verdict["risk_score"],
            "risk_categories": verdict["risk_categories"],
            "action": verdict["action"],
            "final_output_hash": sha3_512(final_output),
            "final_output_length": len(final_output),
            "signature": verdict.get("signature"),
        }

        if self.repmhl is None:
            # Local stdout is deliberately used as the fallback evidence
            # channel rather than pretending a persistent ledger exists.
            print(
                json.dumps(
                    evidence,
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return

        if hasattr(self.repmhl, "append"):
            self.repmhl.append(evidence)

        elif callable(self.repmhl):
            self.repmhl(evidence)

        else:
            raise TypeError(
                "repmhl must provide append(), be callable, or be None"
            )


# ============================================================================
# MODEL ROUTER
# ============================================================================

class ChainOfCommandRouter:

    def __init__(
        self,
        registry: Optional[Dict[str, Dict[str, Any]]] = None,
        policy: Optional[Dict[str, Any]] = None,
        judge: Optional[HeavyJudge] = None,
    ):

        self.registry = registry or MODEL_REGISTRY
        self.policy = policy or ROUTING_POLICY
        self.judge = judge or HeavyJudge()

    # ------------------------------------------------------------------------
    # CONTEXT CLASSIFICATION
    # ------------------------------------------------------------------------

    def classify_context(
        self,
        request: str,
        supplied_context: str = "",
    ) -> str:

        combined = (
            f"{supplied_context} {request}"
        ).strip()

        detected = self._detect_categories(combined)

        if "safety_critical" in detected:
            return "safety_critical"

        if "security" in detected:
            return "security"

        if "medical" in detected:
            return "medical"

        if "legal" in detected:
            return "legal"

        if "financial" in detected:
            return "financial"

        if "education" in detected:
            return "education"

        if "privacy" in detected:
            return "privacy"

        return (
            supplied_context.strip().lower()
            if supplied_context.strip()
            else "general"
        )

    # ------------------------------------------------------------------------
    # CATEGORY DETECTION
    # ------------------------------------------------------------------------

    def _detect_categories(
        self,
        text: str,
    ) -> List[str]:

        categories: List[str] = []

        for category, patterns in RISK_KEYWORDS.items():

            for pattern in patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    categories.append(category)
                    break

        return categories

    # ------------------------------------------------------------------------
    # RISK CALCULATION
    # ------------------------------------------------------------------------

    def calculate_risk(
        self,
        request: str,
        context: str,
    ) -> float:

        categories = self._detect_categories(
            f"{context} {request}"
        )

        weights = {
            "medical": 0.95,
            "legal": 0.90,
            "safety_critical": 1.00,
            "security": 0.95,
            "financial": 0.75,
            "education": 0.60,
            "privacy": 0.70,
        }

        if not categories:
            return 0.10

        return min(
            1.0,
            max(
                weights.get(
                    category,
                    0.50,
                )
                for category in categories
            ),
        )

    # ------------------------------------------------------------------------
    # MODEL SELECTION
    # ------------------------------------------------------------------------

    def select_model(
        self,
        request: str,
        context: str,
        risk_score: float,
        modality: str = "text",
        provider_preference: str = "default",
    ) -> str:

        if modality not in {"text", "voice"}:
            raise ValueError("modality must be 'text' or 'voice'")
        if provider_preference not in {"default", "openai", "xai"}:
            raise ValueError("provider_preference must be 'default', 'openai', or 'xai'")

        request_lower = request.lower()

        # Security has explicit priority.
        if (
            context == "security"
            or any(
                word in request_lower
                for word in (
                    "security",
                    "cyber",
                    "vulnerability",
                    "exploit",
                    "cryptographic",
                    "authentication",
                    "authorization",
                )
            )
        ):
            return "GPT-DayBreak-Red-latest"

        # Code / implementation lane.
        if (
            "code" in request_lower
            or "function" in request_lower
            or "debug" in request_lower
            or "syntax" in request_lower
            or "diff" in request_lower
            or "lint" in request_lower
            or "repository" in request_lower
            or "github" in request_lower
        ):
            return "GPT-5.7-Codex-Cyber"

        # Medical lane.
        if context == "medical":
            return "Claude-Fable-5.1"

        # Legal / financial high-sensitivity lane.
        if context in {
            "legal",
            "financial",
        }:
            return "gpt-6.1-Astra"

        # High-risk escalation.
        if risk_score >= 0.90:
            return "gpt-6.1-Astra"

        # Medium-risk reasoning.
        if risk_score >= 0.60:
            return "GPT-6.1-Terra"

        # Explicit OpenAI lane: Terra is selected for both text and voice.
        # This is routing metadata; a real authorized provider adapter is
        # still required before execution can be reported as successful.
        if provider_preference == "openai":
            return "GPT-6.1-Terra"

        if provider_preference == "xai":
            return "SuperGrok-4.8"

        # Main daily model.
        return "SuperGrok-4.8"

    # ------------------------------------------------------------------------
    # COUNCIL SELECTION
    # ------------------------------------------------------------------------

    def build_council(
        self,
        primary_model: str,
        context: str,
        risk_score: float,
    ) -> List[str]:

        council: List[str] = []

        def add(name: str) -> None:
            if name not in council:
                council.append(name)

        add(primary_model)

        # Grok adversarial lane.
        add("SuperGrok-4.8")

        # GPT reasoning/code lane.
        if context == "security":
            add("GPT-DayBreak-Red-latest")
            add("GPT-5.7-Codex-Cyber")
        else:
            add("GPT-6.1-Terra")

        # Claude lane.
        if context == "medical":
            add("Claude-Fable-5.1")
            add("Claude-Mythos-5.1")
            add("Claude-Opus-5.5")
        else:
            add("Claude-Sonnet-5.5")

        # Hybrid council router.
        add("DevAssist420 + Sovereignty AI Hybrid")

        return council

    # ------------------------------------------------------------------------
    # JUDGE TRIGGER
    # ------------------------------------------------------------------------

    def should_use_judge(
        self,
        context: str,
        risk_score: float,
    ) -> bool:

        if not self.policy["heavy_judge"]["enabled"]:
            return False

        if self.policy["defaults"]["use_judge"]:
            return True

        if context in self.policy[
            "heavy_judge"
        ]["trigger_strategy"]["always_for"]:
            return True

        threshold = self.policy[
            "heavy_judge"
        ]["activation_thresholds"]["general_default"]

        return risk_score >= threshold

    # ------------------------------------------------------------------------
    # FULL ROUTING
    # ------------------------------------------------------------------------

    def route(
        self,
        request: str,
        supplied_context: str = "",
        modality: str = "text",
        provider_preference: str = "default",
    ) -> RoutingDecision:

        context = self.classify_context(
            request,
            supplied_context,
        )

        risk_score = self.calculate_risk(
            request,
            context,
        )

        primary_model = self.select_model(
            request,
            context,
            risk_score,
            modality=modality,
            provider_preference=provider_preference,
        )

        council_models = self.build_council(
            primary_model,
            context,
            risk_score,
        )

        use_judge = self.should_use_judge(
            context,
            risk_score,
        )

        reason = self._routing_reason(
            context,
            risk_score,
            primary_model,
        )

        return RoutingDecision(
            primary_model=primary_model,
            council_models=council_models,
            context=context,
            risk_score=risk_score,
            risk_categories=self._detect_categories(
                f"{supplied_context} {request}"
            ),
            use_judge=use_judge,
            reason=reason,
            modality=modality,
            provider_preference=provider_preference,
        )

    # ------------------------------------------------------------------------
    # ROUTING REASON
    # ------------------------------------------------------------------------

    def _routing_reason(
        self,
        context: str,
        risk_score: float,
        primary_model: str,
    ) -> str:

        if context == "security":
            return (
                "Security context routed to the "
                "DayBreak-Red security lane."
            )

        if context == "medical":
            return (
                "Medical context routed to the "
                "Claude medical lane with Heavy Judge."
            )

        if primary_model == "GPT-6.1-Codex-Cyber":
            return (
                "Code, syntax, diff, lint, or repository "
                "signals selected the Codex-Cyber lane."
            )

        if risk_score >= 0.90:
            return (
                "High-risk request escalated to highest-quality "
                "reasoning and Heavy Judge."
            )

        if risk_score >= 0.60:
            return (
                "Medium-risk request selected the difficult-task "
                "reasoning lane."
            )

        return (
            "General request selected the main daily "
            "SuperGrok lane."
        )


# ============================================================================
# PROVIDER ADAPTER BOUNDARY
# ============================================================================

class ProviderAdapter:

    """
    This is intentionally an execution boundary.

    Do not fabricate a provider response here.

    A real implementation should attach authorized adapters for the
    actual execution mechanisms available to the device:

        local model
        Shortcut action
        local HTTP/WSS bridge
        SSH
        provider connector
        approved hybrid gateway

    The router itself must never pretend that a registry entry means
    the model executed successfully.
    """

    def execute(
        self,
        model_name: str,
        request: str,
        context: str,
    ) -> str:

        raise RuntimeError(
            f"No execution adapter is bound for {model_name!r}. "
            "Routing succeeded, but model execution is not configured."
        )


# ============================================================================
# SCAR / REPMHL LOCAL EVIDENCE
# ============================================================================

class LocalEvidenceLog:

    def __init__(
        self,
        path: Optional[str] = None,
    ):

        self.path = path

    def append(
        self,
        evidence: Dict[str, Any],
    ) -> None:

        serialized = json.dumps(
            evidence,
            sort_keys=True,
            separators=(",", ":"),
        )

        if self.path is None:
            print(
                serialized,
                file=sys.stderr,
            )
            return

        with open(
            self.path,
            "a",
            encoding="utf-8",
        ) as handle:

            handle.write(
                serialized + "\n"
            )


# ============================================================================
# INPUT
# ============================================================================

def get_argument(
    index: int,
    default: str = "",
) -> str:

    if len(sys.argv) <= index:
        return default

    return sys.argv[index]


# ============================================================================
# JSON OUTPUT
# ============================================================================

def emit_json(
    payload: Dict[str, Any],
) -> None:

    print(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
    )


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:

    request = get_argument(
        1,
        "",
    ).strip()

    supplied_context = get_argument(
        2,
        "",
    ).strip()

    if not request:
        emit_json({
            "ok": False,
            "error": "No UserRequest was supplied.",
        })

        return 2

    evidence_path = get_argument(
        3,
        "",
    ).strip()

    modality = get_argument(4, "text").strip().lower() or "text"
    provider_preference = get_argument(5, "default").strip().lower() or "default"

    evidence = LocalEvidenceLog(
        evidence_path or None
    )

    judge = HeavyJudge(
        model_name="SuperGrok-5.7-hybrid",
        repmhl=evidence,
    )

    router = ChainOfCommandRouter(
        judge=judge,
    )

    try:

        routing = router.route(
            request=request,
            supplied_context=supplied_context,
            modality=modality,
            provider_preference=provider_preference,
        )

        # ------------------------------------------------------------
        # Provider execution
        # ------------------------------------------------------------
        #
        # Do NOT fabricate output.
        #
        # If no actual adapter exists, the Shortcut receives a
        # deterministic routing result instead of a fake model answer.
        # ------------------------------------------------------------

        provider_adapter = ProviderAdapter()

        try:

            primary_output = provider_adapter.execute(
                model_name=routing.primary_model,
                request=request,
                context=routing.context,
            )

        except RuntimeError as execution_error:

            primary_output = (
                "MODEL_EXECUTION_NOT_BOUND\n\n"
                f"Primary model: {routing.primary_model}\n"
                f"Context: {routing.context}\n"
                f"Risk score: {routing.risk_score:.6f}\n"
                f"Reason: {routing.reason}\n\n"
                "The Chain of Command router completed successfully, "
                "but no authorized execution adapter is currently "
                "bound to the selected model."
            )

            execution_status = {
                "executed": False,
                "error": str(execution_error),
            }

        else:

            execution_status = {
                "executed": True,
                "error": None,
            }

        # ------------------------------------------------------------
        # Heavy Judge
        # ------------------------------------------------------------

        if routing.use_judge:

            judge_result = judge.review(
                original_output=primary_output,
                context=routing.context,
                risk_score=routing.risk_score,
                risk_categories=routing.risk_categories,
                council_disagreement=False,
            )

        else:

            final_output = primary_output

            judge_result = {
                "final_output": final_output,
                "verdict": {
                    "timestamp": utc_timestamp(),
                    "risk_score": routing.risk_score,
                    "action": "pass",
                    "hash": sha3_512(final_output),
                    "signature": None,
                    "context": routing.context,
                    "risk_categories": routing.risk_categories,
                    "council_disagreement": False,
                    "judge_model": None,
                },
                "judge_model": None,
            }

        # ------------------------------------------------------------
        # Final response
        # ------------------------------------------------------------

        final_output = judge_result["final_output"]

        final_hash = sha3_512(
            final_output
        )

        response = {
            # A successful routing decision is not successful provider execution.
            "ok": bool(execution_status["executed"]),
            "status": "EXECUTED" if execution_status["executed"] else "EXECUTION_BLOCKED",

            "request": request,

            "routing": {
                "context": routing.context,
                "risk_score": routing.risk_score,
                "risk_categories": routing.risk_categories,
                "primary_model": routing.primary_model,
                "council_models": routing.council_models,
                "use_judge": routing.use_judge,
                "reason": routing.reason,
                "modality": routing.modality,
                "provider_preference": routing.provider_preference,
            },

            "execution": execution_status,

            "heavy_judge": {
                "model": judge_result["judge_model"],
                "verdict": judge_result["verdict"],
            },

            "final_output": final_output,

            "integrity": {
                "algorithm": "SHA3-512",
                "hash": final_hash,
            },

            "timestamp": utc_timestamp(),
        }

        emit_json(response)

        return 0

    except Exception as error:

        # Fail closed.
        emit_json({
            "ok": False,
            "error": str(error),
            "timestamp": utc_timestamp(),
        })

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
