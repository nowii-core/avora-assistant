import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clara_core import server


class ImageGalleryTests(unittest.TestCase):
    def test_library_merges_generated_direct_uploads_and_chat_attachments(self):
        generated = [{"id": "a" * 32, "created_at": "2026-10-28T20:00:00+01:00", "url": "/api/generated/" + "a" * 32}]
        direct = [{"id": "b" * 32, "created_at": "2026-10-28T19:00:00+01:00", "url": "/api/gallery/uploads/" + "b" * 32, "kind": "uploaded"}]
        chat = [{"id": "c" * 32, "created_at": "2026-10-28T18:00:00+01:00", "url": "/api/files/" + "c" * 32, "kind": "uploaded"}]
        with patch.object(server, "list_generated_images", return_value=generated), \
             patch.object(server, "list_gallery_uploads", return_value=direct), \
             patch.object(server, "list_chat_uploaded_images", return_value=chat):
            result = server.list_image_gallery()
        self.assertEqual({item["kind"] for item in result["gallery"]}, {"generated", "uploaded"})
        self.assertEqual(len(result["gallery"]), 3)
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(len(result["uploads"]), 2)
        self.assertEqual(result["gallery"][0]["id"], "a" * 32)

    def test_upload_saves_image_and_metadata_locally(self):
        # Signature-valid minimal fixture is sufficient for the storage boundary test.
        jpeg = b"\xff\xd8\xff" + b"test-image-bytes"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(server, "GALLERY_UPLOAD_DIR", root):
                item = server.save_gallery_upload(
                    "my photo.jpg", "image/jpeg", base64.b64encode(jpeg).decode("ascii")
                )
                self.assertEqual(item["kind"], "uploaded")
                self.assertEqual(item["origin"], "Caricata nella galleria")
                self.assertTrue((root / (item["id"] + ".jpg")).exists())
                metadata = json.loads((root / (item["id"] + ".json")).read_text(encoding="utf-8"))
                self.assertEqual(metadata["id"], item["id"])
                self.assertEqual(metadata["filename"], "my photo.jpg")

    def test_upload_normalizes_filename_extension_to_actual_mime(self):
        jpeg = b"\xff\xd8\xff" + b"test-image-bytes"
        with tempfile.TemporaryDirectory() as folder, patch.object(server, "GALLERY_UPLOAD_DIR", Path(folder)):
            item = server.save_gallery_upload("original.png", "image/jpeg", base64.b64encode(jpeg).decode())
            self.assertEqual(item["filename"], "original.jpg")

    def test_upload_rejects_mismatched_file_signature(self):
        fake_png = base64.b64encode(b"this is not a png file").decode("ascii")
        with tempfile.TemporaryDirectory() as folder, patch.object(server, "GALLERY_UPLOAD_DIR", Path(folder)):
            with self.assertRaisesRegex(ValueError, "non corrisponde"):
                server.save_gallery_upload("bad.png", "image/png", fake_png)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_svg_diagram_escapes_model_text(self):
        svg = server.render_diagram_svg({
            "title": 'A < B " onclick="alert(1)',
            "subtitle": "Schema > prova",
            "nodes": [
                {"id": "a", "label": "Input <script>alert(1)</script>"},
                {"id": "b", "label": "Passaggio"},
                {"id": "c", "label": "Risultato & controllo"},
            ],
            "edges": [{"from": "a", "to": "b", "label": "poi <"}, {"from": "b", "to": "c", "label": "e"}],
        }).decode("utf-8")
        self.assertTrue(svg.startswith('<svg'))
        self.assertIn("A &lt; B &quot; onclick=&quot;alert(1)", svg)
        self.assertIn("Input &lt;script&gt;", svg)
        self.assertNotIn("<script>", svg)
        self.assertIn("Risultato &amp; controllo", svg)

    def test_diagram_prompts_do_not_require_image_generation_model(self):
        self.assertTrue(server.is_diagram_prompt("Fammi uno schema del ciclo dell'acqua"))
        self.assertTrue(server.is_diagram_prompt("Crea un diagramma di flusso per una somma"))
        self.assertFalse(server.is_diagram_prompt("Genera una foto realistica del mare"))

    def test_local_image_model_is_preferred_when_installed(self):
        generated = {"id": "b" * 32, "url": "/api/generated/" + "b" * 32}
        with patch.object(server, "ollama_image_model_installed", return_value=True), \
             patch.object(server, "enhance_image_prompt", return_value="An ocean at sunrise, photorealistic"), \
             patch.object(server, "_generate_image_ollama", return_value=generated) as local, \
             patch.object(server, "urlopen", side_effect=AssertionError("should not call external service")):
            result = server.generate_image_local("A peaceful ocean at sunrise", "landscape")
        self.assertEqual(result["id"], generated["id"])
        local.assert_called_once_with("An ocean at sunrise, photorealistic", "landscape")

    def test_chat_image_generation_stores_one_user_message_and_one_assistant_image(self):
        generated = {
            "id": "c" * 32, "url": "/api/generated/" + "c" * 32,
            "filename": "test.svg", "prompt": "schema", "composition": "portrait",
        }
        saved = []
        def fake_add(conversation_id, role, content, attachments=None):
            item = {"conversation_id": conversation_id, "role": role, "content": content,
                     "attachments": attachments or []}
            saved.append(item)
            return item
        with patch.object(server, "generate_image_local", return_value=generated), \
             patch.object(server.storage, "get_conversation", return_value={"id": "d" * 32}), \
             patch.object(server.storage, "create_conversation", return_value={"id": "d" * 32}), \
             patch.object(server.storage, "add_message", side_effect=fake_add):
            result = server.generate_image_chat_turn("Crea uno schema matematico", "schema matematico", "portrait", None)
        self.assertEqual(result["mode"], "image-generation")
        self.assertEqual([message["role"] for message in saved], ["user", "assistant"])
        self.assertEqual(saved[0]["content"], "Crea uno schema matematico")
        self.assertEqual(saved[1]["attachments"][0]["mime"], "image/svg+xml")


if __name__ == "__main__":
    unittest.main()
