import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clara_core import server


class FakeResponse:
    def __init__(self, body, content_type='image/png'):
        self.body = body
        self.headers = {'Content-Type': content_type}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size=-1): return self.body[:size]


class ImageProviderTests(unittest.TestCase):
    def test_key_is_stored_locally_but_never_returned_in_status(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / 'provider.json'
            with patch.object(server, 'IMAGE_PROVIDER_CONFIG', config):
                self.assertFalse(server.image_generation_status()['available'])
                self.assertTrue(server.save_image_provider_key('sk_test_key_123456789'))
                self.assertEqual(server.load_image_provider_key(), 'sk_test_key_123456789')
                status = server.image_generation_status()
                self.assertTrue(status['available'])
                self.assertNotIn('sk_test_key_123456789', json.dumps(status))
                self.assertEqual(config.stat().st_mode & 0o777, 0o600)
                self.assertFalse(server.save_image_provider_key(''))
                self.assertFalse(config.exists())

    def test_generate_image_saves_image_and_sends_key_only_in_header(self):
        png = bytes.fromhex('89504e470d0a1a0a') + b'fake-png-test-data'
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / 'provider.json'
            output = Path(folder) / 'images'
            with patch.object(server, 'IMAGE_PROVIDER_CONFIG', config), patch.object(server, 'IMAGE_OUTPUT_DIR', output):
                server.save_image_provider_key('sk_test_key_123456789')
                captured = {}
                def fake_urlopen(request, timeout):
                    captured['url'] = request.full_url
                    captured['auth'] = request.get_header('Authorization')
                    captured['timeout'] = timeout
                    return FakeResponse(png)
                with patch.object(server, 'urlopen', side_effect=fake_urlopen):
                    result = server.generate_image_local('a small test illustration', 'square')
                self.assertTrue(result['id'])
                self.assertTrue((output / result['filename']).is_file())
                self.assertTrue(captured['url'].startswith('https://gen.pollinations.ai/image/'))
                self.assertEqual(captured['auth'], 'Bearer sk_test_key_123456789')
                self.assertGreaterEqual(captured['timeout'], 60)
                self.assertEqual(result['provider'], 'Pollinations API')

    def test_natural_chat_image_prompt_is_normalized(self):
        prompt, composition = server.normalize_image_prompt("mi generi una foto a mare in formato orizzontale")
        self.assertIn("fotografia realistica", prompt)
        self.assertIn("mare", prompt.lower())
        self.assertIn("a mare", prompt.lower())
        self.assertEqual(composition, "landscape")

    def test_chat_image_generation_persists_generated_result_as_assistant_attachment(self):
        generated = {
            "id": "a" * 32, "url": "/api/generated/" + "a" * 32,
            "filename": "clara-test.png", "prompt": "mare", "composition": "square",
        }
        saved = []
        def fake_add(conversation_id, role, content, attachments=None):
            item = {"conversation_id": conversation_id, "role": role, "content": content,
                    "attachments": attachments or []}
            saved.append(item)
            return item
        with patch.object(server, "load_image_provider_key", return_value="sk_test_key_123456789"), \
             patch.object(server, "generate_image_local", return_value=generated), \
             patch.object(server.storage, "get_conversation", side_effect=[None, {"id": "b" * 32}]), \
             patch.object(server.storage, "create_conversation", return_value={"id": "b" * 32}), \
             patch.object(server.storage, "add_message", side_effect=fake_add):
            result = server.generate_image_chat_turn(
                "mi generi una foto a mare", "Fotografia realistica: mare", "square", None
            )
        self.assertEqual(result["mode"], "image-generation")
        self.assertEqual(saved[0]["role"], "user")
        self.assertEqual(saved[1]["role"], "assistant")
        self.assertTrue(saved[1]["attachments"][0]["generated"])
        self.assertEqual(saved[1]["attachments"][0]["url"], generated["url"])
        self.assertEqual([item["role"] for item in saved], ["user", "assistant"])

    def test_key_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / 'provider.json'
            with patch.object(server, 'IMAGE_PROVIDER_CONFIG', config):
                with self.assertRaises(ValueError):
                    server.save_image_provider_key('not-a-private-key')
                with self.assertRaises(ValueError):
                    server.save_image_provider_key('sk_ key with spaces')


if __name__ == '__main__':
    unittest.main()
