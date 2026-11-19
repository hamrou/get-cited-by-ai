import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "skills" / "get-cited-by-ai" / "scripts" / "panel.py"
FIXTURES = ROOT / "tests" / "fixtures"
spec = importlib.util.spec_from_file_location("panel", PANEL_PATH)
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Capture(io.StringIO):
    def reconfigure(self, encoding=None):
        pass


class LanguageTests(unittest.TestCase):
    def test_simplified_chinese_prompt(self):
        self.assertEqual(panel.prompt_lang("上海哪家天然洗发水店比较好？"), "zh")

    def test_chinese_prompt_with_latin_brand(self):
        self.assertEqual(panel.prompt_lang("Acme 的天然洗发水成分和价格靠谱吗？"), "zh")

    def test_english_prompt_containing_chinese_place_name(self):
        self.assertEqual(panel.prompt_lang("What are the best natural shops in 上海?"), "en")

    def test_japanese_prompt_is_not_mislabeled_as_chinese(self):
        self.assertIsNone(panel.prompt_lang("東京でおすすめの店はどこですか？"))

    def test_chinese_language_warning_detects_english_prompt_set(self):
        prompts = ["What is the best shampoo?", "How does delivery work?", "Where can I buy it?"]
        warning = panel.language_warning(prompts, "zh")
        self.assertIn("site is in 'zh'", warning)
        self.assertIn("most look like 'en'", warning)

    def test_chinese_prompt_set_has_no_language_warning(self):
        prompts = ["最好的天然洗发水是什么？", "配送如何收费？", "上海哪里可以买到？"]
        self.assertIsNone(panel.language_warning(prompts, "zh"))


class ProviderResponseTests(unittest.TestCase):
    def setUp(self):
        self.key_patch = mock.patch.object(panel, "key_for", return_value="test-key")
        self.model_patch = mock.patch.object(panel, "model_for", side_effect=lambda engine: panel.ENGINES[engine][1])
        self.key_patch.start()
        self.model_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.addCleanup(self.model_patch.stop)

    def test_registry_contains_all_three_providers(self):
        self.assertEqual(panel.ENGINES["kimi"][0], ("MOONSHOT_API_KEY",))
        self.assertEqual(panel.ENGINES["deepseek"][0], ("DEEPSEEK_API_KEY",))
        self.assertEqual(panel.ENGINES["qwen"][0], ("DASHSCOPE_API_KEY",))

    @mock.patch.object(panel, "post")
    def test_kimi_web_search_answer_and_citations(self, post):
        post.return_value = fixture("kimi-response.json")
        text, sources = panel.ask("kimi", "上海哪家天然洗发水店比较好？")
        url, body, headers = post.call_args.args
        self.assertEqual(url, "https://api.moonshot.ai/v1/responses")
        self.assertEqual(body["tools"], [{"type": "web_search"}])
        self.assertEqual(body["model"], "kimi-k3.1-pro")
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertIn("Acme", text)
        self.assertEqual(sources, [("https://acme.com/zh/guide", "Acme 指南")])
        scored = panel.score(text, sources, "Acme", "acme.com", [])
        self.assertTrue(scored["mentioned"])
        self.assertTrue(scored["linked"])
        self.assertEqual(scored["position"], 1)

    @mock.patch.object(panel, "post")
    def test_deepseek_web_search_uses_answer_citations_only(self, post):
        post.return_value = fixture("deepseek-response.json")
        text, sources = panel.ask("deepseek", "Acme 成分靠谱吗？")
        url, body, _ = post.call_args.args
        self.assertEqual(url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(body["tools"], [{"type": "deepseek_web_search"}])
        self.assertEqual(body["thinking"], {"type": "disabled"})
        self.assertIn("Acme", text)
        self.assertEqual(sources, [("https://acme.com/zh/ingredients", "Acme 成分表")])
        self.assertNotIn("retrieved-but-not-cited.example", str(sources))

    @mock.patch.object(panel, "post")
    def test_qwen_web_search_answer_and_citations(self, post):
        post.return_value = fixture("qwen-response.json")
        text, sources = panel.ask("qwen", "Acme 价格是多少？")
        url, body, _ = post.call_args.args
        self.assertEqual(url, "https://dashscope.aliyuncs.com/compatible-mode/v1/responses")
        self.assertEqual(body["tools"], [{"type": "web_search"}, {"type": "web_extractor"}])
        self.assertTrue(body["enable_thinking"])
        self.assertIn("Acme", text)
        self.assertEqual(sources, [("https://acme.com/zh/pricing", "Acme 价格")])

    def test_http_200_api_error_is_not_treated_as_an_answer(self):
        with self.assertRaisesRegex(RuntimeError, "temporarily unavailable"):
            panel.ensure_api_success({"error": {"message": "temporarily unavailable"}})


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.key_patch = mock.patch.object(panel, "key_for", return_value="test-key")
        self.model_patch = mock.patch.object(panel, "model_for", side_effect=lambda engine: panel.ENGINES[engine][1])
        self.key_patch.start()
        self.model_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.addCleanup(self.model_patch.stop)

    @mock.patch.object(panel, "post")
    def test_kimi_url_fetch(self, post):
        post.return_value = fixture("kimi-fetch.json")
        result = panel.fetch_page("kimi", "https://acme.com/zh/guide")
        _, body, _ = post.call_args.args
        self.assertEqual(body, {"url": "https://acme.com/zh/guide"})
        self.assertTrue(result["retrieved"])
        self.assertEqual(result["title"], "Acme 天然洗发水指南")
        self.assertGreater(result["characters"], 20)

    @mock.patch.object(panel, "post")
    def test_deepseek_url_reading(self, post):
        post.return_value = fixture("deepseek-fetch.json")
        result = panel.fetch_page("deepseek", "https://acme.com/zh/guide")
        _, body, _ = post.call_args.args
        self.assertEqual(body["tools"], [{"type": "deepseek_read_url"}])
        self.assertTrue(result["retrieved"])
        self.assertEqual(result["title"], "Acme 天然洗发水指南")
        self.assertIn("成分", result["preview"])

    @mock.patch.object(panel, "post")
    def test_qwen_web_extraction(self, post):
        post.return_value = fixture("qwen-fetch.json")
        result = panel.fetch_page("qwen", "https://acme.com/zh/guide")
        _, body, _ = post.call_args.args
        self.assertEqual(body["tools"], [{"type": "web_search"}, {"type": "web_extractor"}])
        self.assertTrue(result["retrieved"])
        self.assertIn("使用方法", result["preview"])

    @mock.patch.object(panel, "post")
    def test_qwen_without_extractor_call_is_not_retrieved(self, post):
        response = fixture("qwen-fetch.json")
        response["output"] = response["output"][1:]
        post.return_value = response
        result = panel.fetch_page("qwen", "https://acme.com/zh/guide")
        self.assertFalse(result["retrieved"])
        self.assertEqual(result["error"], "No web-extractor call was returned")


class CliSafetyTests(unittest.TestCase):
    def setUp(self):
        self.keys = {
            "MOONSHOT_API_KEY": "kimi-secret",
            "DEEPSEEK_API_KEY": "deepseek-secret",
            "DASHSCOPE_API_KEY": "qwen-secret",
        }
        self.env_patch = mock.patch.dict(os.environ, self.keys, clear=False)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def run_cli(self, arguments):
        stdout = Capture()
        with mock.patch.object(sys, "argv", ["panel.py"] + arguments), contextlib.redirect_stdout(stdout):
            code = panel.main()
        return code, stdout.getvalue()

    def test_keys_never_print_secret_values(self):
        code, output = self.run_cli(["--keys", "--engines", "kimi,deepseek,qwen"])
        self.assertEqual(code, 0)
        for secret in self.keys.values():
            self.assertNotIn(secret, output)
        self.assertIn("kimi", output)
        self.assertIn("deepseek", output)
        self.assertIn("qwen", output)

    @mock.patch.object(panel, "ask")
    def test_three_provider_panel_dry_run_makes_no_calls(self, ask):
        with tempfile.TemporaryDirectory() as directory:
            prompts = Path(directory) / "prompts.txt"
            prompts.write_text("上海哪家天然洗发水店比较好？\nAcme 靠谱吗？\n", encoding="utf-8")
            code, output = self.run_cli([str(prompts), "--brand", "Acme", "--engines", "kimi,deepseek,qwen"])
        self.assertEqual(code, 0)
        ask.assert_not_called()
        self.assertIn("6 model call(s)", output)
        self.assertIn("not a spending cap", output)
        self.assertIn("Dry run", output)

    @mock.patch.object(panel, "fetch_page")
    def test_retrieval_dry_run_makes_no_calls(self, fetch_page):
        code, output = self.run_cli(["--fetch-url", "https://acme.com/zh/guide"])
        self.assertEqual(code, 0)
        fetch_page.assert_not_called()
        self.assertIn("3 retrieval request(s)", output)
        self.assertIn("Dry run", output)

    @mock.patch.object(panel, "fetch_page")
    def test_approved_retrieval_writes_markdown_and_json(self, fetch_page):
        fetch_page.side_effect = lambda engine, url: {
            "engine": engine, "url": url, "retrieved": True, "title": "Acme 指南",
            "characters": 42, "preview": "成分和价格", "answer": "", "error": "", "detail": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            prefix = str(Path(directory) / "retrieval")
            code, _ = self.run_cli(["--fetch-url", "https://acme.com/zh/guide", "--out", prefix, "--yes"])
            date = panel.dt.date.today().isoformat()
            markdown = Path(prefix + "-" + date + ".md").read_text(encoding="utf-8")
            rows = json.loads(Path(prefix + "-" + date + ".json").read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(fetch_page.call_count, 3)
        self.assertEqual([row["engine"] for row in rows], ["kimi", "deepseek", "qwen"])
        self.assertIn("Acme 指南", markdown)


if __name__ == "__main__":
    unittest.main()
