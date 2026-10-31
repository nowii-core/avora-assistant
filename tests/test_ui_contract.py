import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UIContractTests(unittest.TestCase):
    def test_settings_and_history_controls_exist(self):
        html = (ROOT / 'assets' / 'index.html').read_text(encoding='utf-8')
        for marker in (
            'id="historyList"', 'id="historySearch"', 'id="settingsPanel"',
            'data-tab="account"', 'data-tab="general"', 'data-tab="personalization"',
            'data-tab="data"', 'data-tab="model"', 'data-tab="usage"', 'data-tab="voice"', 'data-tab="about"',
            'id="avatarInput"', 'id="thinkToggle"', 'id="researchToggle"',
            'id="projectsAction"', 'id="exportAll"', 'id="deleteAll"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)

    def test_brand_and_assets_are_local(self):
        html = (ROOT / 'assets' / 'index.html').read_text(encoding='utf-8')
        self.assertNotRegex(html, r'<script[^>]+src=["\']https?://')
        self.assertIn('/assets/app.js?v=1.4.0', html)
        self.assertIn('/assets/styles.css?v=1.4.0', html)
        for ident in ('setupCard','autoModel','scrollDown','welcomeHello'):
            self.assertIn(f'id="{ident}"', html)
        self.assertIn('<title>Avora</title>', html)
        self.assertIn('/assets/avora.svg', html)
        self.assertIn('id="imageInput"', html)
        self.assertIn('id="saveVisionModel"', html)
        self.assertNotIn('id="billingSetup"', html)
        self.assertNotRegex(html, r'\d+,\d\d\s*€')
        self.assertIn('data-plan="max"', html)
        self.assertIn('id="quotaSummary"', html)
        self.assertIn('finestra di 3 ore', html)
        self.assertNotIn('<title>Clara</title>', html)
        self.assertNotIn('Nautilus AI', html)
        self.assertNotIn('id="modelNotice"', html)
        self.assertNotIn('id="modelPill"', html)
        self.assertNotIn('id="statusLabel"', html)

    def test_explore_images_math_and_clean_status_ui(self):
        html = (ROOT / 'assets' / 'index.html').read_text(encoding='utf-8')
        js = (ROOT / 'assets' / 'app.js').read_text(encoding='utf-8')
        css = (ROOT / 'assets' / 'styles.css').read_text(encoding='utf-8')
        for marker in (
            'id="exploreLayer"', 'id="exploreForm"', 'id="exploreResults"',
            'id="imageGenLayer"', 'id="imageGenForm"', 'id="imageGallery"',
            'id="generateImageButton"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertIn("api('/api/search'", js)
        self.assertIn("api('/api/images/generate'", js)
        self.assertIn("api('/api/images/generate-chat'", js)
        self.assertIn('function detectMathRequest(text)', js)
        self.assertIn('function detectImageRequest(text)', js)
        self.assertIn('function detectWebRequest(text)', js)
        self.assertIn('deep_research: research', js)
        self.assertIn('target="_blank" rel="noopener noreferrer"', js)
        self.assertIn('generated-result', js)
        self.assertIn("api('/api/images'", js)
        self.assertNotIn('Nessun modello linguistico addestrato è disponibile', js)
        self.assertNotIn('Server non disponibile', js)
        self.assertIn('@media(max-width:680px){.feature-layer', css)
        self.assertIn('.processing-steps{display:flex', css)


    def test_all_direct_event_selectors_exist_in_html(self):
        import re
        html = (ROOT / 'assets' / 'index.html').read_text(encoding='utf-8')
        js = (ROOT / 'assets' / 'app.js').read_text(encoding='utf-8')
        ids = set(re.findall(r"""\bid=["\']([^"\']+)""", html))
        # Covers direct registrations such as $('#someId').addEventListener(...).
        selectors = set(re.findall(r"""\$\(["\']#([^"\']+)["\']\)\.addEventListener""", js))
        missing_handlers = sorted(selectors - ids)
        self.assertEqual(missing_handlers, [], f'Event handlers reference missing HTML IDs: {missing_handlers}')
        # Also catch broken lookups even when they are used for something other than events.
        queried = re.findall(r"""\$\(["\'](#[^"\']+)["\']""", js)
        queried_ids = {selector[1:].split()[0].split('.')[0].split(':')[0] for selector in queried}
        missing_queries = sorted(queried_ids - ids)
        self.assertEqual(missing_queries, [], f'DOM queries reference missing HTML IDs: {missing_queries}')
        self.assertIn('id="refreshImages"', html)

    def test_voice_features_are_present_and_transparent(self):
        html = (ROOT / 'assets' / 'index.html').read_text(encoding='utf-8')
        js = (ROOT / 'assets' / 'app.js').read_text(encoding='utf-8')
        css = (ROOT / 'assets' / 'styles.css').read_text(encoding='utf-8')
        for marker in ('id="voiceModeButton"', 'id="voiceModeLayer"', 'id="voiceOrbButton"', 'id="voiceSelect"', 'id="autoReadResponses"', 'data-tab="voice"'):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        self.assertIn('/api/tts', js)
        self.assertIn('SpeechSynthesisUtterance', js)
        self.assertIn('SpeechRecognition', js)
        self.assertIn('message-listen', js)
        self.assertIn('voiceRecognitionStarting', js)
        self.assertNotIn('setTimeout(startVoiceListening', js)
        self.assertIn('/api/chat/stream', js)
        self.assertIn('voice_mode', js)
        self.assertIn('createSpeechStream', js)
        self.assertIn('voice-ripple', css)
        self.assertIn('Microsoft Edge Neural TTS', html)

    def test_streaming_theme_and_model_ui_present(self):
        html = (ROOT / 'assets' / 'index.html').read_text(encoding='utf-8')
        js = (ROOT / 'assets' / 'app.js').read_text(encoding='utf-8')
        for marker in ('data-theme-choice="dark"', 'data-size-choice="large"', 'id="voiceEngine"', 'data-preset="qwen3:4b"', 'id="pullProgress"', 'id="hordeToggle"'):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for marker in ('readChatStream', 'stopGeneration', 'applyAppearance', "api('/api/models/pull'", 'addFiles', 'AbortController', 'stripEmojiClient'):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)
        self.assertNotRegex(html, r'<script>[^<]')  # the CSP forbids inline scripts
        self.assertTrue((ROOT / 'assets' / 'theme-init.js').exists())

    def test_toolbar_menu_and_message_actions(self):
        html = (ROOT / 'assets' / 'index.html').read_text(encoding='utf-8')
        js = (ROOT / 'assets' / 'app.js').read_text(encoding='utf-8')
        for marker in ('id="modelMenuButton"', 'id="collapseSidebar"', 'id="expandSidebar"', 'id="promptMenu"', 'id="filePreviewLayer"'):
            self.assertIn(marker, html)
        for removed in ('id="agentToggle"', 'id="personaQuick"', 'id="modelQuick"'):
            self.assertNotIn(removed, html)
        for marker in ('Risposta utile', 'Rigenera la risposta', 'Modifica messaggio', 'Ascolta la risposta'):
            self.assertIn(marker, js)

    def test_agent_persona_preview_and_context_ui_present(self):
        html = (ROOT / 'assets' / 'index.html').read_text(encoding='utf-8')
        js = (ROOT / 'assets' / 'app.js').read_text(encoding='utf-8')
        for marker in ('id="personaSelect"', 'id="personaCustom"', 'id="previewPanel"', 'sandbox="allow-scripts"', 'id="contextMeter"', 'id="compactChat"'):
            with self.subTest(marker=marker):
                self.assertIn(marker, html)
        for marker in ('showToolEvent', 'buildToolTrace', 'openPreview', 'updateContextMeter', 'compactCurrentChat', 'persona_prompt', "'/api/personas'", 'vision_model_missing'):
            with self.subTest(marker=marker):
                self.assertIn(marker, js)
        frame = (ROOT / 'assets' / 'artifact-frame.js').read_text(encoding='utf-8')
        self.assertIn('event.source !== window.parent', frame)
        self.assertNotIn('allow-same-origin', html)


if __name__ == '__main__':
    unittest.main()
