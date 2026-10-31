import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clara_core.runtime import DEFAULT_OLLAMA_MODEL, ClaraRuntime


class OllamaRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ClaraRuntime()
        self.runtime.engine = "ollama"
        self.temp = tempfile.TemporaryDirectory()
        self.settings_path_patch = patch("clara_core.runtime.SETTINGS_PATH", Path(self.temp.name) / "settings.json")
        self.settings_path_patch.start()

    def tearDown(self):
        self.settings_path_patch.stop()
        self.temp.cleanup()

    def test_default_model_is_qwen3_one_point_seven_b(self):
        self.assertEqual(self.runtime._load_model_name(), DEFAULT_OLLAMA_MODEL)

    def test_invalid_model_name_is_rejected(self):
        with self.assertRaises(ValueError):
            self.runtime.set_model("qwen3:4b; rm -rf /")

    def test_model_setting_is_persisted(self):
        with patch.object(self.runtime, "status", return_value={"model_name": "qwen3:1.7b"}):
            result = self.runtime.set_model("qwen3:1.7b")
        self.assertEqual(result["model_name"], "qwen3:1.7b")
        saved = json.loads((Path(self.temp.name) / "settings.json").read_text())
        self.assertEqual(saved["ollama_model"], "qwen3:1.7b")

    def test_auto_mode_picks_fast_or_strong_model(self):
        runtime = self.runtime
        runtime.auto = True
        details = {"installed": ["qwen3:1.7b", "qwen3:8b"]}
        self.assertEqual(runtime._text_models(details), ("qwen3:1.7b", "qwen3:8b"))
        simple = [{"role": "user", "content": "Ciao, come va?"}]
        hard = [{"role": "user", "content": "Scrivi un programma Python che analizza un file CSV"}]
        self.assertEqual(runtime._pick_text_model("qwen3:1.7b", "qwen3:8b", {}, simple), "qwen3:1.7b")
        self.assertEqual(runtime._pick_text_model("qwen3:1.7b", "qwen3:8b", {}, hard), "qwen3:8b")
        self.assertEqual(runtime._pick_text_model("qwen3:1.7b", "qwen3:8b", {"voice_mode": True}, hard), "qwen3:1.7b")
        self.assertEqual(runtime._pick_text_model("qwen3:1.7b", "qwen3:8b", {"think": True}, simple), "qwen3:8b")

    def test_recommended_model_follows_memory(self):
        from clara_core.runtime import recommended_model
        self.assertIsNone(recommended_model(4))
        self.assertEqual(recommended_model(8), "qwen3:4b")
        self.assertEqual(recommended_model(16), "qwen3:8b")

    def test_reply_uses_local_ollama_messages(self):
        self.runtime.auto = False
        with patch.object(self.runtime, "_ollama_details", return_value={"running": True, "available": True, "installed": ["qwen3:4b"]}), \
             patch.object(self.runtime, "_request_chat_stream", return_value={"message": {"content": "Ciao, sono Clara."}, "prompt_eval_count": 5, "eval_count": 4, "done": True, "streamed_chunks": 3}) as request:
            reply, mode = self.runtime.reply([{"role": "user", "content": "Ciao"}])
        self.assertEqual(reply, "Ciao, sono Clara.")
        self.assertEqual(mode, "ollama")
        payload = request.call_args.args[0]
        self.assertEqual(payload["model"], "qwen3:1.7b")
        self.assertTrue(payload["stream"])
        self.assertEqual(payload["options"]["num_ctx"], 8192)
        self.assertFalse(payload["think"])
        self.assertIn("matematica", payload["messages"][0]["content"].lower())
        self.assertLessEqual(payload["options"]["num_predict"], 3072)
        self.assertEqual(request.call_args.kwargs["timeout"], 300)


    def test_qwen3_disables_thinking_for_normal_chat_and_uses_small_context(self):
        with patch.object(self.runtime, "_ollama_details", return_value={"running": True, "available": True, "installed": ["qwen3:1.7b"]}), \
             patch.object(self.runtime, "_request_chat_stream", return_value={"message": {"content": "Risposta breve."}, "prompt_eval_count": 8, "eval_count": 3, "done": True, "streamed_chunks": 1}) as request:
            self.runtime.reply_with_metadata([{"role": "user", "content": "Quanto fa 2+2?"}], max_tokens=320)
        payload = request.call_args.args[0]
        self.assertIs(payload["think"], False)
        self.assertEqual(payload["options"]["num_ctx"], 8192)
        self.assertEqual(payload["options"]["num_predict"], 320)

    def test_repeated_previous_answer_retries_with_current_question_only(self):
        previous = "La risposta precedente parlava di configurare un progetto con tre passaggi."
        results = [
            {"message": {"content": previous}, "prompt_eval_count": 20, "eval_count": 14, "done": True, "streamed_chunks": 4},
            {"message": {"content": "Nettuno è l'ottavo pianeta del Sistema solare."}, "prompt_eval_count": 12, "eval_count": 10, "done": True, "streamed_chunks": 3},
        ]
        with patch.object(self.runtime, "_ollama_details", return_value={"running": True, "available": True, "installed": ["qwen3:1.7b"]}), \
             patch.object(self.runtime, "_request_chat_stream", side_effect=results) as request:
            reply, mode, _ = self.runtime.reply_with_metadata([
                {"role": "user", "content": "Come organizzo un progetto software?"},
                {"role": "assistant", "content": previous},
                {"role": "user", "content": "Qual è l'ottavo pianeta?"},
            ], max_tokens=320)
        self.assertIn("Nettuno", reply)
        self.assertEqual(mode, "ollama")
        self.assertEqual(request.call_count, 2)
        retry_messages = request.call_args.args[0]["messages"]
        self.assertEqual(len(retry_messages), 2)
        self.assertEqual(retry_messages[-1]["content"], "Qual è l'ottavo pianeta?")


    def test_web_grounded_answer_receives_real_page_content_and_returns_citations(self):
        source = {
            "title": "Pagina ufficiale", "page_title": "Pagina ufficiale",
            "url": "https://example.org/specs", "snippet": "Lo snippet afferma una batteria più grande.",
            "content": "Il testo effettivo della pagina dice che il prodotto ha una batteria da 5000 mAh.",
            "source": "Test provider",
        }
        response = {"message": {"content": "La batteria è da 5000 mAh."}, "prompt_eval_count": 50,
                    "eval_count": 12, "done": True, "streamed_chunks": 3}
        with patch.object(self.runtime, "_ollama_details", return_value={"running": True, "available": True, "installed": ["qwen3:1.7b"]}), \
             patch("clara_core.websearch.search_web", return_value=[source]), \
             patch.object(self.runtime, "_request_chat_stream", return_value=response) as request:
            reply, mode, metrics = self.runtime.reply_with_metadata(
                [{"role": "user", "content": "Qual è la capacità della batteria?"}],
                {"deep_research": True, "intent": "web", "search_query": "capacità batteria prodotto"},
                max_tokens=560)
        messages = request.call_args.args[0]["messages"]
        source_messages = [item["content"] for item in messages if item["role"] == "system" and "FONTI WEB REALI" in item["content"]]
        self.assertTrue(source_messages)
        self.assertIn("5000 mAh", source_messages[0])
        self.assertIn("https://example.org/specs", reply)
        self.assertEqual(mode, "ollama-research")
        self.assertEqual(metrics["sources_count"], 1)

    def test_streaming_helper_reports_real_partial_output(self):
        class FakeResponse:
            def __init__(self, lines): self.lines = iter(lines)
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def __iter__(self): return self
            def __next__(self): return next(self.lines)
        chunks = [
            b'{"message":{"role":"assistant","content":"Ciao"},"done":false}\n',
            b'{"message":{"role":"assistant","content":"!"},"done":false}\n',
            b'{"message":{"role":"assistant","content":""},"done":true,"prompt_eval_count":7,"eval_count":2}\n',
        ]
        updates = []
        with patch("clara_core.runtime._urlrequest.urlopen", return_value=FakeResponse(chunks)):
            result = self.runtime._request_chat_stream({"model": "qwen3:4b", "stream": True},
                progress_callback=lambda phase, detail, **extra: updates.append((phase, detail, extra)))
        self.assertEqual(result["message"]["content"], "Ciao!")
        self.assertEqual(result["eval_count"], 2)
        self.assertGreaterEqual(result["streamed_chunks"], 2)
        self.assertEqual(updates[-1][0], "generating")
        self.assertEqual(updates[-1][2]["partial_text"], "Ciao!")

    def test_reply_does_not_fake_model_when_service_is_offline(self):
        with patch.object(self.runtime, "_ollama_details", return_value={"running": False, "available": False, "installed": []}):
            reply, mode = self.runtime.reply([{"role": "user", "content": "Ciao"}])
        self.assertEqual(mode, "ollama-unavailable")
        self.assertIn("non è in esecuzione", reply)

    def test_runtime_defaults_to_local_engine(self):
        with patch.dict("os.environ", {}, clear=True):
            runtime = ClaraRuntime()
        self.assertEqual(runtime.engine, "ollama")
        self.assertTrue(runtime.model_name)

    def test_avora_engine_setting_takes_priority_and_keeps_legacy_compatibility(self):
        with patch.dict("os.environ", {"AVORA_ENGINE": "transformer", "CLARA_ENGINE": "ollama", "NAUTILUS_ENGINE": "ollama"}, clear=True):
            runtime = ClaraRuntime()
        self.assertEqual(runtime.engine, "transformer")


if __name__ == "__main__":
    unittest.main()


class DemoModeTests(unittest.TestCase):
    def test_demo_runtime_replies_without_ollama(self):
        runtime = ClaraRuntime()
        runtime.demo = True
        chunks = []
        reply, mode, metrics = runtime.reply_with_metadata(
            [{"role": "user", "content": "Fammi un sito"}], {"delta_callback": chunks.append})
        self.assertEqual(mode, "demo")
        self.assertIn("Modalità demo", reply)
        self.assertEqual("".join(chunks), reply)
        from unittest.mock import patch
        with patch("clara_core.storage.database_stats", return_value={}), patch("clara_core.storage.usage_snapshot", return_value={}):
            status = runtime.status()
        self.assertTrue(status["demo"])
        self.assertTrue(status["model_loaded"])
