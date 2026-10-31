import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from clara_core import server, storage
from clara_core.image_intent import detect_image_request, image_composition, image_kind, image_subject
from clara_core.runtime import ClaraRuntime
from clara_core.svg_art import SVG_EXAMPLE, SvgRejected, sanitize_svg
from clara_core.textclean import clean_model_output, inside_code_fence, join_continuation, strip_emoji, trim_to_boundary


class TextCleanTests(unittest.TestCase):
    def test_emoji_are_removed_but_text_symbols_and_code_stay(self):
        text = "### 🧩 **Piano**\n- ✅ Fatto ⚠️ attenzione\n1️⃣ Primo\nCiao 👨‍👩‍👧 mondo ⌘ K © 2026\n```js\nconsole.log('🙂')\n```\n🚀\nOk"
        cleaned = strip_emoji(text)
        self.assertNotRegex(cleaned.split("```")[0] + cleaned.split("```")[2], "[\U0001F300-\U0001FAFF☀-➿️]")
        self.assertIn("### **Piano**", cleaned)
        self.assertIn("⌘ K © 2026", cleaned)
        self.assertIn("console.log('🙂')", cleaned)
        self.assertIn("Fatto attenzione", cleaned)

    def test_reasoning_blocks_are_removed(self):
        self.assertEqual(clean_model_output("<think>ragiono</think>\nRisposta"), "Risposta")
        self.assertEqual(clean_model_output("<think>solo pensiero"), "")

    def test_continuation_resumes_inside_code_without_reopening_the_fence(self):
        partial = "Ecco il codice:\n```html\n<html>\n<body>\n<div class=\"a\">ciao</di"
        trimmed = trim_to_boundary(partial)
        self.assertTrue(inside_code_fence(trimmed))
        joined = join_continuation(trimmed, "```html\n<div class=\"a\">ciao</div>\n</body>\n</html>\n```")
        self.assertEqual(joined.count("```"), 2)
        self.assertTrue(joined.endswith("</html>\n```"))
        self.assertNotIn("</di<", joined)

    def test_continuation_removes_repeated_text_and_fixes_spacing(self):
        previous = "La carbonara si prepara con guanciale, uova e pecorino. Il segreto è non"
        joined = join_continuation(trim_to_boundary(previous + "n"), "Il segreto è non cuocere le uova.")
        self.assertEqual(joined.count("Il segreto"), 1)
        self.assertTrue(joined.endswith("non cuocere le uova."))


class SvgSanitizerTests(unittest.TestCase):
    def test_example_is_accepted(self):
        output = sanitize_svg(SVG_EXAMPLE)
        self.assertTrue(output.startswith(b"<?xml"))
        self.assertIn(b"viewBox", output)

    def test_scripts_handlers_external_references_and_entities_are_rejected(self):
        hostile = SVG_EXAMPLE.replace("<circle", '<image href="http://x/y.png"/><script>x()</script><circle onclick="x()" stroke="javascript:1"', 1)
        output = sanitize_svg(hostile)
        for forbidden in (b"image", b"script", b"onclick", b"javascript", b"http://x"):
            self.assertNotIn(forbidden, output)
        with self.assertRaises(SvgRejected):
            sanitize_svg('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><svg xmlns="http://www.w3.org/2000/svg"/>')
        with self.assertRaises(SvgRejected):
            sanitize_svg('<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>')


class ImageIntentTests(unittest.TestCase):
    REQUESTS = [
        "mi generi una foto al mare", "disegna un gatto", "disegnami un drago che vola", "vorrei un logo per la mia azienda",
        "crea un logo per il mio sito web", "fammi un'immagine di un tramonto", "genera un'illustrazione di una foresta",
        "Crea uno schema del ciclo dell'acqua", "please generate an image of a red car", "mi serve una locandina per una festa",
        "foto di un gatto sul divano",
    ]
    OTHER = [
        "come si crea un'immagine docker", "scrivi uno script python che genera un'immagine", "che differenza c'è tra foto e immagine",
        "dammi la ricetta della carbonara", "crea un sito web con html", "ciao come stai", "analizza questa foto",
    ]

    def test_requests_are_detected_and_other_text_is_not(self):
        for text in self.REQUESTS:
            with self.subTest(text=text):
                self.assertTrue(detect_image_request(text))
        for text in self.OTHER:
            with self.subTest(text=text):
                self.assertFalse(detect_image_request(text))

    def test_subject_kind_and_format(self):
        self.assertEqual(image_subject("mi generi una foto al mare in formato orizzontale"), "al mare")
        self.assertEqual(image_subject("disegna un lago di montagna"), "lago di montagna")
        self.assertEqual(image_kind("fammi un logo"), "logo professionale")
        self.assertEqual(image_composition("poster verticale"), "portrait")

    def test_javascript_detector_matches_python_on_the_same_sentences(self):
        import shutil
        import subprocess
        node = shutil.which("node")
        if not node:
            self.skipTest("node non disponibile")
        source = (Path(__file__).resolve().parents[1] / "assets" / "image-intent.js").read_text(encoding="utf-8")
        script = source + "\nconst cases = JSON.parse(process.argv[1]);\nconsole.log(JSON.stringify(cases.map(t => Boolean(AvoraImageIntent.detect(t)))));"
        cases = self.REQUESTS + self.OTHER
        result = subprocess.run([node, "-e", script, json.dumps(cases)], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [detect_image_request(t) for t in cases])


class RuntimeQualityTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ClaraRuntime()
        self.runtime.engine = "ollama"
        self.details = {"running": True, "available": True, "installed": ["qwen3:1.7b"]}

    def test_cut_answers_are_continued_until_complete(self):
        first = {"message": {"content": "Passo uno. Passo due. Passo tr"}, "done_reason": "length", "eval_count": 3000, "prompt_eval_count": 50, "done": True, "streamed_chunks": 5}
        second = {"message": {"content": "Passo tre. Fine."}, "done_reason": "stop", "eval_count": 8, "prompt_eval_count": 60, "done": True, "streamed_chunks": 2}
        with patch.object(self.runtime, "_ollama_details", return_value=self.details), \
             patch.object(self.runtime, "_request_chat_stream", side_effect=[first, second]) as request:
            reply, mode, metrics = self.runtime.reply_with_metadata([{"role": "user", "content": "Elenca i passi"}], max_tokens=9000)
        self.assertEqual(request.call_count, 2)
        self.assertIn("Passo tre. Fine.", reply)
        self.assertNotIn("Passo tr ", reply)
        self.assertEqual(metrics["continuations"], 1)
        self.assertNotIn("molto lunga", reply)

    def test_answers_never_contain_emoji_even_if_the_model_writes_them(self):
        result = {"message": {"content": "Ecco il piano \U0001F680\n- ✅ Primo"}, "done_reason": "stop", "eval_count": 9, "prompt_eval_count": 9, "done": True}
        with patch.object(self.runtime, "_ollama_details", return_value=self.details), \
             patch.object(self.runtime, "_request_chat_stream", return_value=result):
            reply, _, _ = self.runtime.reply_with_metadata([{"role": "user", "content": "Dammi un piano"}])
        self.assertNotRegex(reply, "[\U0001F300-\U0001FAFF☀-➿]")

    def test_web_failure_still_produces_an_answer_with_a_clear_notice(self):
        result = {"message": {"content": "Risposta dalla conoscenza del modello."}, "done_reason": "stop", "eval_count": 6, "prompt_eval_count": 9, "done": True}
        with patch.object(self.runtime, "_ollama_details", return_value=self.details), \
             patch("clara_core.websearch.search_web", side_effect=RuntimeError("offline")), \
             patch.object(self.runtime, "_request_chat_stream", return_value=result):
            reply, mode, _ = self.runtime.reply_with_metadata([{"role": "user", "content": "Che tempo fa a Roma?"}], {"deep_research": True, "intent": "weather"})
        self.assertEqual(mode, "ollama-research")
        self.assertIn("Risposta dalla conoscenza", reply)
        self.assertIn("non sono riuscito a consultare il web", reply.lower())

    def test_system_prompt_is_professional_and_date_only_for_cache_stability(self):
        prompt = self.runtime._build_system_prompt({}, "general")
        self.assertIn("Nessuna emoji", prompt)
        self.assertIn("Non lasciare mai una risposta a metà", prompt)
        self.assertNotRegex(prompt, r"\d{2}:\d{2}")
        voice = self.runtime._build_system_prompt({"voice_mode": True}, "general")
        self.assertIn("CONVERSAZIONE VOCALE", voice)

    def test_voice_mode_uses_short_budget_and_no_thinking(self):
        result = {"message": {"content": "Certo."}, "done_reason": "stop", "eval_count": 2, "prompt_eval_count": 9, "done": True}
        with patch.object(self.runtime, "_ollama_details", return_value=self.details), \
             patch.object(self.runtime, "_request_chat_stream", return_value=result) as request:
            self.runtime.reply_with_metadata([{"role": "user", "content": "Ciao"}], {"voice_mode": True, "think": True}, max_tokens=9000)
        payload = request.call_args.args[0]
        self.assertLessEqual(payload["options"]["num_predict"], 420)
        self.assertIs(payload["think"], False)

    def test_history_keeps_recent_turns_within_budget(self):
        messages = []
        for index in range(30):
            messages.append({"role": "user", "content": f"domanda {index} " + "x" * 800})
            messages.append({"role": "assistant", "content": f"risposta {index} " + "y" * 800})
        messages.append({"role": "user", "content": "ultima domanda"})
        selected = ClaraRuntime._select_history(messages, False)
        self.assertEqual(selected[-1]["content"], "ultima domanda")
        self.assertEqual(selected[0]["role"], "user")
        self.assertLessEqual(sum(len(m["content"]) for m in selected), 14000 + 12000)
        self.assertGreater(len(selected), 6)


class StreamingEndpointTests(unittest.TestCase):
    def test_chat_stream_sends_deltas_then_a_final_event_and_saves_the_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(storage, "DATA_DIR", Path(folder)), patch.object(storage, "DB_PATH", Path(folder) / "t.sqlite3"), \
                 patch.object(storage, "UPLOAD_DIR", Path(folder) / "uploads"):
                storage.init_db()

                def fake_reply(messages, options, max_tokens=0):
                    for piece in ("Ciao ", "dal ", "server \U0001F600."):
                        options["delta_callback"](piece)
                    return "Ciao dal server.", "ollama", {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9, "model": "test"}

                with patch.object(server.RUNTIME, "status", return_value={"model_loaded": True, "engine": "ollama"}), \
                     patch.object(server.RUNTIME, "reply_with_metadata", side_effect=fake_reply):
                    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
                    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                    thread.start()
                    try:
                        request = urllib.request.Request(
                            f"http://127.0.0.1:{httpd.server_address[1]}/api/chat/stream",
                            data=json.dumps({"message": "Salutami"}).encode(), headers={"Content-Type": "application/json"})
                        with urllib.request.urlopen(request, timeout=20) as response:
                            self.assertIn("ndjson", response.headers["Content-Type"])
                            events = [json.loads(line) for line in response.read().decode().splitlines() if line.strip()]
                    finally:
                        httpd.shutdown()
                        httpd.server_close()
                deltas = "".join(e["text"] for e in events if e["type"] == "delta")
                self.assertEqual(deltas, "Ciao dal server.")
                self.assertEqual(events[-1]["type"], "done")
                self.assertEqual(events[-1]["assistant_message"]["content"], "Ciao dal server.")


if __name__ == "__main__":
    unittest.main()
