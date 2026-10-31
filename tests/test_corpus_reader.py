import json
import tempfile
import unittest
from pathlib import Path
from clara_core.corpus import iter_documents, normalize_text

class CorpusTests(unittest.TestCase):
    def test_normalize_text_preserves_accents_and_normalizes_newlines(self):
        self.assertEqual(normalize_text('Città\r\n  bella'), 'Città\n bella')

    def test_reads_text_and_jsonl_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'one.txt').write_text('Questo è un testo di prova sufficientemente lungo.', encoding='utf-8')
            with (root / 'two.jsonl').open('w', encoding='utf-8') as f:
                f.write(json.dumps({'text': 'Un altro testo sufficientemente lungo.'}, ensure_ascii=False) + '\n')
            docs = list(iter_documents(root))
            self.assertEqual(len(docs), 2)
            self.assertIn('Città', normalize_text('Città'))
            self.assertTrue(any('altro testo' in text for text, _ in docs))

if __name__ == '__main__': unittest.main()
