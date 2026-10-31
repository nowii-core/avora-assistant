import base64
import unittest
from unittest.mock import patch

from clara_core import server
from clara_core.agent import AgentUnsupported, run_agent
from clara_core.personas import PERSONAS, persona_list, persona_prompt
from clara_core.sandbox import run_python


class SandboxTests(unittest.TestCase):
    def test_runs_code_and_captures_output(self):
        result = run_python("print(sum(range(5)))")
        self.assertTrue(result["ok"])
        self.assertEqual(result["stdout"].strip(), "10")

    def test_network_and_processes_are_blocked(self):
        result = run_python("import socket\nsocket.socket()")
        self.assertFalse(result["ok"])
        self.assertIn("non consentita", result["stderr"])
        result = run_python("import os\nos.system('echo hi')")
        self.assertFalse(result["ok"])

    def test_timeout_is_enforced(self):
        result = run_python("while True:\n    pass", timeout=1)
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["ok"])

    def test_created_text_files_are_returned(self):
        result = run_python("open('dati.csv','w').write('a,b\\n1,2')")
        self.assertEqual([f["name"] for f in result["files"]], ["dati.csv"])

    def test_empty_code_is_rejected(self):
        with self.assertRaises(ValueError):
            run_python("   ")


class PersonaTests(unittest.TestCase):
    def test_personas_and_prompts(self):
        ids = [p["id"] for p in persona_list()]
        self.assertIn("general", ids)
        self.assertIn("code", ids)
        self.assertEqual(persona_prompt("general"), "")
        self.assertIn("ingegnere software", persona_prompt("code"))
        self.assertIn("RUOLO DEFINITO", persona_prompt("general", "Sei un sommelier."))
        self.assertEqual(persona_prompt("sconosciuta"), "")
        self.assertEqual(len(PERSONAS), len(ids))


class AgentLoopTests(unittest.TestCase):
    def _payload(self):
        return {"model": "qwen3:4b", "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "somma"}], "options": {}}

    def test_tool_call_then_final_answer(self):
        calls = []

        def chat(request):
            calls.append(request)
            if not any(m.get("role") == "tool" for m in request["messages"]):
                return {"message": {"content": "", "tool_calls": [{"function": {"name": "run_python", "arguments": {"code": "print(6*7)"}}}]}, "eval_count": 5}
            return {"message": {"content": "Il risultato è 42."}, "eval_count": 7}

        events = []
        deltas = []
        result = run_agent(chat, self._payload(), tool_callback=events.append, delta_callback=deltas.append)
        self.assertEqual(result["text"], "Il risultato è 42.")
        self.assertEqual("".join(deltas), "Il risultato è 42.")
        self.assertEqual(result["tools"][0]["name"], "run_python")
        self.assertIn("42", result["tools"][0]["output"])
        self.assertEqual([e["status"] for e in events], ["start", "done"])
        self.assertIn("tools", calls[0])
        self.assertTrue(all(call["stream"] is False for call in calls))

    def test_unknown_tool_is_reported_not_executed(self):
        def chat(request):
            if not any(m.get("role") == "tool" for m in request["messages"]):
                return {"message": {"content": "", "tool_calls": [{"function": {"name": "rm_rf", "arguments": {}}}]}}
            return {"message": {"content": "Fatto."}}
        result = run_agent(chat, self._payload())
        self.assertFalse(result["tools"][0]["ok"])
        self.assertIn("sconosciuto", result["tools"][0]["output"])

    def test_step_limit_forces_a_final_answer(self):
        def chat(request):
            if "tools" in request:
                return {"message": {"content": "", "tool_calls": [{"function": {"name": "run_python", "arguments": {"code": "print(1)"}}}]}}
            return {"message": {"content": "Risposta finale."}}
        result = run_agent(chat, self._payload(), max_steps=2)
        self.assertEqual(result["text"], "Risposta finale.")
        self.assertEqual(len(result["tools"]), 2)

    def test_model_without_tool_support_raises(self):
        from urllib.error import HTTPError

        def chat(request):
            raise HTTPError("http://x", 400, "bad", {}, None)
        with self.assertRaises(AgentUnsupported):
            run_agent(chat, self._payload())


class ServerFeatureTests(unittest.TestCase):
    def test_tool_images_become_generated_attachments(self):
        png = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 32).decode()
        record = {"id": "a" * 32, "url": "/api/generated/" + "a" * 32, "filename": "a.png", "prompt": "Grafico: g.png"}
        metrics = {"tools": [{"name": "run_python", "ok": True, "input": "x", "output": "y"}],
                   "tool_images": [{"name": "g.png", "mime": "image/png", "data": png}]}
        with patch.object(server, "_persist_generated_image", return_value=record):
            items = server._tool_attachments(metrics)
        self.assertTrue(items[0]["tool"])
        self.assertTrue(items[1]["generated"])
        self.assertEqual(items[1]["url"], record["url"])

    def test_compact_conversation_builds_new_chat_with_summary(self):
        from clara_core import storage
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp, patch.object(storage, "DB_PATH", Path(tmp) / "t.sqlite3"):
            storage.init_db()
            conv = storage.create_conversation("Prova")
            storage.add_message(conv["id"], "user", "Ciao, voglio un piano di studio")
            storage.add_message(conv["id"], "assistant", "Certo, ecco un piano.")
            with patch.object(server, "_ollama_text", return_value="- Obiettivo: piano di studio"):
                new = server.compact_conversation(conv["id"])
            messages = storage.get_messages(new["id"])
            self.assertTrue(new["title"].startswith("Continua:"))
            self.assertEqual(messages[0]["role"], "user")
            self.assertIn("piano di studio", messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
