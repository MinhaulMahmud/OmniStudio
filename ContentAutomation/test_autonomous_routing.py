"""
Unit tests for Autonomous Voice & Language Routing
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import unittest
from autonomous_voice_router import AutonomousVoiceRouter


class TestAutonomousVoiceRouter(unittest.TestCase):

    def test_short_english_routing(self):
        """English script <= 2 minutes should route to OmniVoice base model (onyx)."""
        text = "Ever wondered why running an AI model like Llama 70B makes your GPU scream? It comes down to weights."
        decision = AutonomousVoiceRouter.route_voice(text)
        self.assertEqual(decision.model, "omnivoice")
        self.assertEqual(decision.voice, "onyx")
        self.assertEqual(decision.language_code, "en")
        self.assertFalse(decision.is_long_form)
        self.assertLessEqual(decision.estimated_duration_seconds, 120.0)

    def test_long_english_routing(self):
        """English script > 2 minutes should autonomously switch to KittenTTS."""
        # 300 words paragraph
        text = "This is an in-depth video lecture on machine learning architectures, memory bandwidth, and quantization. " * 30
        decision = AutonomousVoiceRouter.route_voice(text)
        self.assertEqual(decision.model, "kittentts")
        self.assertEqual(decision.voice, "expr-voice-2-m")
        self.assertEqual(decision.language_code, "en")
        self.assertTrue(decision.is_long_form)
        self.assertGreater(decision.estimated_duration_seconds, 120.0)

    def test_spanish_detection_and_routing(self):
        """Spanish text should route to OmniVoice multilingual."""
        text = "En este video explicaremos cómo el tamaño del modelo de inteligencia artificial determina el cómputo necesario."
        decision = AutonomousVoiceRouter.route_voice(text)
        self.assertEqual(decision.model, "omnivoice")
        self.assertEqual(decision.language_code, "es")
        self.assertEqual(decision.language_name, "Spanish")

    def test_french_detection_and_routing(self):
        """French text should route to OmniVoice multilingual."""
        text = "Dans cette vidéo, nous allons expliquer pourquoi les modèles demandent autant de mémoire VRAM."
        decision = AutonomousVoiceRouter.route_voice(text)
        self.assertEqual(decision.model, "omnivoice")
        self.assertEqual(decision.language_code, "fr")
        self.assertEqual(decision.language_name, "French")

    def test_bengali_detection_and_routing(self):
        """Bengali text (Unicode script) should route to OmniVoice multilingual."""
        text = "এই ভিডিওতে আমরা জানব কীভাবে একটি এআই মডেল চালাতে কত মেমোরি ও কম্পিউট পাওয়ার লাগে।"
        decision = AutonomousVoiceRouter.route_voice(text)
        self.assertEqual(decision.model, "omnivoice")
        self.assertEqual(decision.language_code, "bn")
        self.assertEqual(decision.language_name, "Bengali")

    def test_german_detection_and_routing(self):
        """German text should route to OmniVoice multilingual."""
        text = "In diesem Video erklären wir, wie neuronale Netze funktionieren und warum VRAM entscheidend ist."
        decision = AutonomousVoiceRouter.route_voice(text)
        self.assertEqual(decision.model, "omnivoice")
        self.assertEqual(decision.language_code, "de")
        self.assertEqual(decision.language_name, "German")

    def test_explicit_override_honored(self):
        """User explicit choice must be respected over automatic routing."""
        text = "Short text"
        decision = AutonomousVoiceRouter.route_voice(text, requested_voice="alloy", requested_model="omnivoice")
        self.assertEqual(decision.model, "omnivoice")
        self.assertEqual(decision.voice, "alloy")

    def test_explicit_language_override(self):
        """Explicit language code override should take precedence."""
        text = "Hello world"
        decision = AutonomousVoiceRouter.route_voice(text, requested_language="es")
        self.assertEqual(decision.language_code, "es")
        self.assertEqual(decision.model, "omnivoice")


if __name__ == "__main__":
    unittest.main()
