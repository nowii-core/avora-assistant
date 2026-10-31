import unittest
from clara_core import server
from clara_core.websearch import _GoogleParser, _DuckParser, _ReadablePageParser, _absolute_url, _enrich_results
from unittest.mock import patch


class WebSearchParserTests(unittest.TestCase):
    def test_google_parser_extracts_real_http_results(self):
        parser = _GoogleParser()
        parser.feed('<div><a href="https://example.org/page"><h3>Risultato di prova</h3></a></div>')
        self.assertEqual(len(parser.results), 1)
        self.assertEqual(parser.results[0]['title'], 'Risultato di prova')
        self.assertEqual(parser.results[0]['url'], 'https://example.org/page')

    def test_duckduckgo_parser_extracts_title_and_link(self):
        parser = _DuckParser()
        parser.feed('<a class="result__a" href="https://example.org/a">Una fonte</a><a class="result__snippet">Estratto</a>')
        self.assertEqual(len(parser.results), 1)
        self.assertEqual(parser.results[0]['title'], 'Una fonte')
        self.assertEqual(parser.results[0]['url'], 'https://example.org/a')

    def test_url_filter_rejects_unsafe_and_local_links(self):
        self.assertEqual(_absolute_url('javascript:alert(1)'), '')
        self.assertEqual(_absolute_url('http://localhost:8765/secret'), '')
        self.assertEqual(_absolute_url('http://127.0.0.1:8765/secret'), '')
        self.assertEqual(_absolute_url('https://example.org:444/blocked'), '')
        self.assertEqual(_absolute_url('https://example.org/ok'), 'https://example.org/ok')
        self.assertEqual(_absolute_url('https://www.google.com/url?q=https%3A%2F%2Fexample.org%2Ftarget'), 'https://example.org/target')

    def test_explicit_web_intent_routes_automatically(self):
        self.assertTrue(server.detect_web_research_request('Cerca sul web le ultime notizie sulla NASA'))
        self.assertTrue(server.detect_web_research_request('Trova fonti aggiornate sul clima'))
        self.assertTrue(server.detect_web_research_request('Quanto costa oggi un MacBook?'))
        self.assertFalse(server.detect_web_research_request('Mi generi una foto al mare'))
        self.assertFalse(server.detect_web_research_request('Quanto fa 2+2?'))
        self.assertFalse(server.detect_web_research_request('Spiegami come funziona la ricerca web in generale'))

    def test_current_questions_route_to_web_without_explicit_search_toggle(self):
        self.assertTrue(server.detect_web_research_request('Chi è il presidente francese attuale?'))
        self.assertTrue(server.detect_web_research_request('Quando esce GTA 6?'))
        self.assertTrue(server.detect_web_research_request('Quali sono i migliori telefoni disponibili oggi?'))
        self.assertTrue(server.detect_web_research_request('Quali partite di calcio ci sono stasera?'))
        self.assertTrue(server.detect_web_research_request('Quale AI è migliore oggi, ChatGPT o Gemini?'))
        self.assertTrue(server.detect_web_research_request('Quando esce GTA 6?'))
        self.assertFalse(server.detect_web_research_request('Come si fa la carbonara?'))  # stable knowledge: answered locally, faster
        self.assertTrue(server.detect_web_research_request('Quanto valgono 100 dollari in euro oggi?'))
        self.assertFalse(server.detect_web_research_request('Oggi ho voglia di carbonara'))

    def test_readable_page_parser_skips_scripts_and_navigation(self):
        parser = _ReadablePageParser()
        parser.feed('<html><head><title>Pagina ufficiale</title><meta name="description" content="Descrizione utile"></head>'
                    '<body><nav>MENU DA IGNORARE</nav><main><h1>Informazioni utili</h1>'
                    '<p>Il dispositivo ha una batteria da 5000 mAh.</p><script>secret fake injection</script>'
                    '<p>La garanzia dura due anni.</p></main></body></html>')
        page = parser.output()
        self.assertEqual(page['page_title'], 'Pagina ufficiale')
        self.assertIn('batteria da 5000 mAh', page['content'])
        self.assertNotIn('MENU DA IGNORARE', page['content'])
        self.assertNotIn('secret fake injection', page['content'])

    def test_enrichment_adds_fetched_page_content_without_inventing_sources(self):
        results = [{'title': 'Fonte', 'url': 'https://example.org/a', 'snippet': 'Snippet reale'}]
        with patch('clara_core.websearch._fetch_page_content', return_value={
            'page_title': 'Titolo della pagina', 'content': 'Testo effettivo della fonte', 'description': 'Descrizione'
        }):
            enriched = _enrich_results(results, max_pages=1)
        self.assertEqual(enriched[0]['url'], 'https://example.org/a')
        self.assertEqual(enriched[0]['content'], 'Testo effettivo della fonte')
        self.assertEqual(enriched[0]['page_title'], 'Titolo della pagina')


if __name__ == '__main__':
    unittest.main()
