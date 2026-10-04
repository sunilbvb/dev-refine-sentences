"""Comprehensive unit tests for Sentence Refiner."""

import unittest
import sys
from pathlib import Path

# Ensure repo root and src/ are in python path for direct test execution
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from refiner.rules import RuleBasedRefiner
from refiner.gemini import GeminiRefiner
from refiner.openai import OpenAIRefiner
from refiner.claude import ClaudeRefiner
from refiner.manager import RefinerManager
from clipboard.manager import ClipboardManager
from config.settings import ConfigManager
from history.history_manager import HistoryManager
from ui.diff_highlighter import compute_word_diff
from metrics.readability import analyze_readability, count_syllables


class TestSentenceRefiner(unittest.TestCase):
    def setUp(self):
        self.config_mgr = ConfigManager()
        self.refiner = RuleBasedRefiner(config_manager=self.config_mgr)
        self.history_mgr = HistoryManager()

    def test_standard_grammar_and_typos(self):
        res = self.refiner.refine("he go to store and buyed apples", tone="standard")
        self.assertEqual(res, "He goes to store and bought apples.")

    def test_pronoun_and_double_verb(self):
        res = self.refiner.refine("I students are is great", tone="standard")
        self.assertEqual(res, "My students are great.")

    def test_shorthand_expansions(self):
        res = self.refiner.refine("pls send msg btw", tone="standard")
        self.assertEqual(res, "Please send message by the way.")


    def test_concise_tone(self):
        res = self.refiner.refine("basically in order to test this we need time", tone="concise")
        self.assertEqual(res, "To test this we need time.")

    def test_professional_tone(self):
        res = self.refiner.refine("gonna fix this asap plz give me a shout", tone="professional")
        self.assertEqual(res, "Going to fix this as soon as possible please contact me.")

    def test_bullet_points_tone(self):
        res = self.refiner.refine("step one is done. step two is ready.", tone="bullet_points")
        self.assertIn("- Step one is done.", res)
        self.assertIn("- Step two is ready.", res)

    def test_email_formal_tone(self):
        res = self.refiner.refine("the project is completed", tone="email_formal")
        self.assertTrue(res.startswith("Hi team,"))
        self.assertTrue(res.endswith("Best regards,"))

    def test_snippet_expansion(self):
        res = self.refiner.refine("lgtm and omw", tone="standard")
        self.assertIn("Looks good to me!", res)
        self.assertIn("on my way", res)

    def test_dynamic_snippet_variables(self):
        self.config_mgr.add_snippet("dt_test", "Year is {{year}}")
        res = self.refiner.refine("check dt_test now", tone="standard")
        self.assertIn("Year is 20", res)

    def test_teach_explanations(self):
        self.refiner.refine("he go to store and buyed apples", tone="standard")
        explanations = self.refiner.get_last_explanations()
        self.assertTrue(len(explanations) > 0)
        expl_text = " ".join(explanations)
        self.assertIn("Subject-verb agreement", expl_text)
        self.assertIn("Irregular verb", expl_text)

    def test_whitelist_protection(self):
        res = self.refiner.refine("i use antigravity and kubernetes", tone="standard")
        self.assertIn("Antigravity", res)
        self.assertIn("Kubernetes", res)

    def test_word_diff_computation(self):
        diff = compute_word_diff("he buyed apples", "He bought apples.")
        tags = [t[0] for t in diff]
        self.assertIn("del", tags)
        self.assertIn("add", tags)
        self.assertIn("equal", tags)

    def test_history_recording(self):
        self.history_mgr.record("orig text", "refined text", "standard", "TestEngine")
        last = self.history_mgr.get_last()
        self.assertIsNotNone(last)
        self.assertEqual(last["original"], "orig text")
        self.assertEqual(last["refined"], "refined text")

    def test_readability_metrics(self):
        metrics = analyze_readability("The quick brown fox jumps over the lazy dog.")
        self.assertEqual(metrics["words"], 9)
        self.assertGreater(metrics["reading_ease"], 70)
        self.assertIn(metrics["label"], ["Very Easy", "Fairly Easy", "Standard"])
        self.assertEqual(count_syllables("apples"), 2)

    def test_gemini_refiner_availability(self):
        gr_none = GeminiRefiner(api_key=None, config_manager=self.config_mgr)
        if not self.config_mgr.get_api_key("gemini"):
            self.assertFalse(gr_none.is_available())
        gr_with_key = GeminiRefiner(api_key="AIzaSyDummyKeyForTest")
        self.assertTrue(gr_with_key.is_available())

    def test_openai_refiner_availability(self):
        oa_none = OpenAIRefiner(api_key=None, config_manager=self.config_mgr)
        if not self.config_mgr.get_api_key("openai"):
            self.assertFalse(oa_none.is_available())
        oa_with_key = OpenAIRefiner(api_key="sk-proj-dummy123")
        self.assertTrue(oa_with_key.is_available())

    def test_claude_refiner_availability(self):
        cl_none = ClaudeRefiner(api_key=None, config_manager=self.config_mgr)
        if not self.config_mgr.get_api_key("anthropic"):
            self.assertFalse(cl_none.is_available())
        cl_with_key = ClaudeRefiner(api_key="sk-ant-dummy123")
        self.assertTrue(cl_with_key.is_available())

    def test_refiner_manager_fallback(self):
        rm = RefinerManager(preferred_engine="auto", config_manager=self.config_mgr)
        active = rm.get_active_engine()
        self.assertIsNotNone(active)
        self.assertTrue(active.is_available())

    def test_daemon_client_inactive(self):
        from daemon import send_daemon_request
        # When daemon socket is not running, gracefully returns False
        handled = send_daemon_request("flash")
        self.assertIsInstance(handled, bool)

    def test_precompiled_lru_cache(self):
        res1 = self.refiner.refine("dont worry i is ready", tone="standard")
        res2 = self.refiner.refine("dont worry i is ready", tone="standard")
        self.assertEqual(res1, res2)
        self.assertEqual(res1, "Don't worry I am ready.")

    def test_web_server_endpoints(self):
        import threading
        import urllib.request
        import json
        from http.server import HTTPServer
        from web_server.server import DocsRequestHandler

        server = HTTPServer(("127.0.0.1", 0), DocsRequestHandler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        try:
            # 1. Test static index.html GET
            req = urllib.request.urlopen(f"http://127.0.0.1:{port}/")
            self.assertEqual(req.status, 200)
            content = req.read().decode("utf-8")
            self.assertIn("Universal Sentence Refiner", content)

            # 2. Test /api/status GET
            req_status = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status")
            status_data = json.loads(req_status.read().decode("utf-8"))
            self.assertEqual(status_data["status"], "online")

            # 3. Test /api/refine POST
            body = json.dumps({"text": "he go to store and buyed fruit", "tone": "standard"}).encode("utf-8")
            post_req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/refine",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(post_req)
            ref_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(ref_data["refined"], "He goes to store and bought fruit.")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()

