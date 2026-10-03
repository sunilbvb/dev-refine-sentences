"""Comprehensive unit tests for Sentence Refiner."""

import unittest
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


if __name__ == "__main__":
    unittest.main()
