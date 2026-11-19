"""Offline tests for audit.py: robots matching and the --compare logic.

No network: audit.fetch is replaced by a stub. Run with
    python -m unittest discover -s tests -p "test_*.py"
"""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit", ROOT / "skills" / "get-cited-by-ai" / "scripts" / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

GOOD_HTML = """<html lang="en"><head><title>A page</title>
<meta name="description" content="d"><link rel="canonical" href="https://example.com/x">
<meta property="og:title" content="t"><meta property="og:description" content="d"><meta property="og:image" content="i">
</head><body><h1>One</h1><h2>A?</h2><h2>B?</h2><p>""" + "word " * 400 + """ 2026</p>
<script type="application/ld+json">{"@type":"Organization"}</script></body></html>"""


def groups(txt):
    return audit.parse_robots(txt)


def old_report(level, area, msg):
    return f"# AI visibility audit: https://example.com\n\n## {level}\n- **{area}**: {msg}\n"


class RobotsTests(unittest.TestCase):
    def test_disallow_applies_per_path_not_only_to_root(self):
        g = groups("User-agent: *\nDisallow: /private/\n")
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/"))
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/blog/a"))
        self.assertFalse(audit.robots_allows(g, "GPTBot", "/private/a"))

    def test_wildcard_in_the_middle(self):
        g = groups("User-agent: *\nDisallow: /*/draft/\n")
        self.assertFalse(audit.robots_allows(g, "GPTBot", "/x/draft/y"))
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/x/final/y"))

    def test_dollar_anchors_the_end(self):
        g = groups("User-agent: *\nDisallow: /*.pdf$\n")
        self.assertFalse(audit.robots_allows(g, "GPTBot", "/a/b.pdf"))
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/a/b.pdf?download=1"))
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/a/b.pdfx"))

    def test_longest_match_wins(self):
        g = groups("User-agent: *\nDisallow: /docs\nAllow: /docs/public\n")
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/docs/public/a"))
        self.assertFalse(audit.robots_allows(g, "GPTBot", "/docs/secret"))

    def test_allow_wins_a_tie(self):
        g = groups("User-agent: *\nDisallow: /a\nAllow: /a\n")
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/a/b"))

    def test_specific_group_beats_star(self):
        g = groups("User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
        self.assertFalse(audit.robots_allows(g, "GPTBot", "/"))
        self.assertTrue(audit.robots_allows(g, "Googlebot", "/"))

    def test_empty_disallow_allows_everything(self):
        g = groups("User-agent: *\nDisallow:\n")
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/anything"))

    def test_query_string_is_matched(self):
        g = groups("User-agent: *\nDisallow: /*?variant=\n")
        self.assertFalse(audit.robots_allows(g, "GPTBot", "/p?variant=2"))
        self.assertTrue(audit.robots_allows(g, "GPTBot", "/p"))


class StubbedFetchTests(unittest.TestCase):
    def setUp(self):
        audit.results[:] = []
        audit.incomplete.clear()
        audit.bot_checked.clear()
        self._fetch = audit.fetch

    def tearDown(self):
        audit.fetch = self._fetch

    def stub(self, status=200, body=GOOD_HTML):
        audit.fetch = lambda url, ua=audit.UA_BROWSER, timeout=20: (status, {}, body if status == 200 else "", url)

    def test_audited_page_blocked_by_path_rule_is_reported(self):
        self.stub()
        g = groups("User-agent: OAI-SearchBot\nDisallow: /private/\n")
        audit.audit_page("https://example.com/private/a", bots=False, robots=g)
        msgs = [m for lvl, a, m in audit.results if lvl == "FAIL"]
        self.assertTrue(any("blocks OAI-SearchBot from this path" in m for m in msgs), msgs)

    def test_open_path_adds_no_robots_finding(self):
        self.stub()
        g = groups("User-agent: OAI-SearchBot\nDisallow: /private/\n")
        audit.audit_page("https://example.com/open", bots=False, robots=g)
        self.assertFalse(any("robots.txt blocks" in m for _, _, m in audit.results))

    def test_robots_network_error_is_incomplete(self):
        audit.fetch = lambda url, ua=audit.UA_BROWSER, timeout=20: (0, {}, "timeout", url)
        audit.audit_robots("https://example.com")
        self.assertIn("robots", audit.incomplete)


class CompareTests(unittest.TestCase):
    def setUp(self):
        audit.results[:] = []
        audit.incomplete.clear()
        audit.bot_checked.clear()
        self._fetch = audit.fetch

    def tearDown(self):
        audit.fetch = self._fetch

    def text(self, lines):
        return "\n".join(lines)

    def test_failed_page_fetch_is_not_reported_as_fixed(self):
        audit.fetch = lambda url, ua=audit.UA_BROWSER, timeout=20: (500, {}, "", url)
        audit.audit_page("https://example.com/x", bots=False)
        out = self.text(audit.compare(old_report("WARN", "/x", "12 words of text without JavaScript; a content page too thin"), ["https://example.com/x"]))
        self.assertIn("0 fixed", out)
        self.assertIn("1 not re-checked", out)

    def test_real_fix_is_reported_as_fixed(self):
        audit.fetch = lambda url, ua=audit.UA_BROWSER, timeout=20: (200, {}, GOOD_HTML, url)
        audit.audit_page("https://example.com/x", bots=False)
        out = self.text(audit.compare(old_report("WARN", "/x", "no canonical link"), ["https://example.com/x"]))
        self.assertIn("1 fixed", out)

    def test_thin_page_that_got_worse_is_remaining_not_fixed(self):
        audit.results.append(("FAIL", "/x", "only 5 words in the raw HTML (1 scripts): AI crawlers don't run JavaScript"))
        out = self.text(audit.compare(old_report("WARN", "/x", "12 words of text without JavaScript; a content page too thin"), ["https://example.com/x"]))
        self.assertIn("0 fixed", out)
        self.assertIn("1 remaining", out)
        self.assertIn("0 new", out)

    def test_skipped_bot_check_is_not_reported_as_fixed(self):
        audit.fetch = lambda url, ua=audit.UA_BROWSER, timeout=20: (200, {}, GOOD_HTML, url)
        audit.audit_page("https://example.com/x", bots=False)
        out = self.text(audit.compare(old_report("FAIL", "/x", "ClaudeBot user agent gets HTTP 403 (firewall, CDN bot protection or WAF?)"), ["https://example.com/x"]))
        self.assertIn("0 fixed", out)
        self.assertIn("1 not re-checked", out)

    def test_page_not_in_this_run_is_not_reported_as_fixed(self):
        out = self.text(audit.compare(old_report("WARN", "/other", "no canonical link"), ["https://example.com/x"]))
        self.assertIn("0 fixed", out)
        self.assertIn("1 not re-checked", out)

    def test_robots_fetch_error_does_not_fix_a_blocked_bot(self):
        audit.fetch = lambda url, ua=audit.UA_BROWSER, timeout=20: (0, {}, "timeout", url)
        audit.audit_robots("https://example.com")
        out = self.text(audit.compare(old_report("FAIL", "robots", "robots.txt blocks GPTBot (training bot): x"), []))
        self.assertIn("0 fixed", out)

    def test_changed_numbers_are_the_same_issue(self):
        audit.results.append(("WARN", "/x", "title is 80 chars (aim for under 60): A long title"))
        out = self.text(audit.compare(old_report("WARN", "/x", "title is 72 chars (aim for under 60): A long title"), ["https://example.com/x"]))
        self.assertIn("1 remaining", out)
        self.assertIn("0 new", out)


if __name__ == "__main__":
    unittest.main()
