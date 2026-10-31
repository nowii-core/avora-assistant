import asyncio
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from clara_core.server import DEFAULT_NEURAL_VOICE, NEURAL_VOICES, normalize_tts_rate, normalize_tts_voice, synthesize_tts


class TTSRuntimeTests(unittest.TestCase):
    def test_known_italian_neural_voices_are_allowlisted(self):
        self.assertIn("it-IT-ElsaNeural", NEURAL_VOICES)
        self.assertEqual(normalize_tts_voice("it-IT-DiegoNeural"), "it-IT-DiegoNeural")

    def test_unknown_voice_falls_back_to_default(self):
        self.assertEqual(normalize_tts_voice("not-a-voice"), DEFAULT_NEURAL_VOICE)
        self.assertEqual(normalize_tts_voice(None), DEFAULT_NEURAL_VOICE)


    def test_neural_tts_saves_audio_bytes_with_an_optional_provider(self):
        class FakeCommunicate:
            def __init__(self, text, voice, rate):
                self.text, self.voice, self.rate = text, voice, rate
            async def save(self, path):
                Path(path).write_bytes(b"ID3" + b"x" * 1200)
        fake = types.SimpleNamespace(Communicate=FakeCommunicate)
        with patch.dict(sys.modules, {"edge_tts": fake}):
            audio, mime, provider = synthesize_tts("Ciao Clara", "it-IT-ElsaNeural", 0.95)
        self.assertTrue(audio.startswith(b"ID3"))
        self.assertEqual(mime, "audio/mpeg")
        self.assertEqual(provider, "edge-neural-online")

    def test_rate_is_clamped_and_normalized(self):
        text, value = normalize_tts_rate(2)
        self.assertEqual(text, "+15%")
        self.assertEqual(value, 1.15)
        text, value = normalize_tts_rate(0.85)
        self.assertEqual(text, "-15%")
        self.assertEqual(value, 0.85)


if __name__ == "__main__":
    unittest.main()
