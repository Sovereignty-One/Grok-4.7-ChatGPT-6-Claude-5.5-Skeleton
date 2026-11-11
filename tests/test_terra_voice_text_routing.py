from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "Models" / "Chain_of_command.py"
SPEC = importlib.util.spec_from_file_location("chain_of_command", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TerraVoiceTextRoutingTests(unittest.TestCase):
    def setUp(self):
        self.router = MODULE.ChainOfCommandRouter()

    def test_openai_text_prefers_terra(self):
        decision = self.router.route(
            "Explain a general topic",
            modality="text",
            provider_preference="openai",
        )
        self.assertEqual(decision.primary_model, "GPT-6.1-Terra")
        self.assertEqual(decision.modality, "text")

    def test_openai_voice_prefers_terra(self):
        decision = self.router.route(
            "Explain a general topic",
            modality="voice",
            provider_preference="openai",
        )
        self.assertEqual(decision.primary_model, "GPT-6.1-Terra")
        self.assertEqual(decision.modality, "voice")

    def test_default_daily_route_uses_grok_48(self):
        decision = self.router.route("Explain a general topic")
        self.assertEqual(decision.primary_model, "SuperGrok-4.8")

    def test_unsupported_modality_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "modality"):
            self.router.route("Hello", modality="video", provider_preference="openai")

    def test_luna_aliases_are_not_routable(self):
        self.assertNotIn("GPT-6.1-Luna", MODULE.MODEL_REGISTRY)
        self.assertNotIn("GPT-6-Luna", str(MODULE.ROUTING_POLICY))
        self.assertNotIn("GPT-5.6-Luna", str(MODULE.ROUTING_POLICY))

    def test_terra_declares_text_and_voice_capability(self):
        terra = MODULE.MODEL_REGISTRY["GPT-6.1-Terra"]
        self.assertEqual(terra["modalities"], ["text", "voice"])
        self.assertEqual(terra["execution_status"], "adapter_unbound")


if __name__ == "__main__":
    unittest.main()
