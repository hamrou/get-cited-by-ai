#!/usr/bin/env python3
"""AI-discovery audit: how a site looks to AI crawlers and answer engines.

Usage:
    python audit.py https://example.com [more page URLs on the same site] [--out report.md]

Stdlib only. Fetches each page as an AI crawler would (no JavaScript), plus
robots.txt, the sitemap and llms.txt, and prints a PASS / WARN / FAIL report.
It reads public pages only, one request at a time, like a polite crawler.
"""
import argparse
import gzip
import json
import os
import time
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA_BROWSER = "Mozilla/5.0 (compatible; get-cited-by-ai-audit/1.0)"
# One user agent per crawler family; the string is what the server sees.
UA_BOTS = {
    "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)",
    "OAI-SearchBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot",
    "ClaudeBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
}
# Tokens checked in robots.txt. Search/retrieval bots decide whether you can be
# cited; training bots only decide whether future models learn from you.
ROBOTS_TOKENS = {
    "OAI-SearchBot": "search", "ChatGPT-User": "user", "GPTBot": "training",
    "Claude-SearchBot": "search", "Claude-User": "user", "ClaudeBot": "training",
    "PerplexityBot": "search", "Perplexity-User": "user",
    "Googlebot": "search", "Google-Extended": "training", "Bingbot": "search",
    "Applebot": "search", "Applebot-Extended": "training", "CCBot": "training",
}

results = []  # (level, area, message)


def add(level, area, msg):
    results.append((level, area, msg))


def fetch(url, ua=UA_BROWSER, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "gzip", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            if r.headers.get("Content-Encoding") == "gzip" or body[:2] == b"\x1f\x8b":
                body = gzip.decompress(body)
            return r.status, dict(r.headers), body.decode("utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), "", url
    except Exception as e:  # network error, TLS, timeout
        return 0, {}, str(e), url


class Page(HTMLParser):
    """Collects what a non-JS crawler can read from raw HTML."""
    SKIP = {"script", "style", "noscript", "template", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self.skip, self.cur = [], 0, None
        self.title = ""
        self.meta, self.links, self.jsonld, self.h1, self.h2 = {}, [], [], [], []
        self.html_lang, self.anchors, self.scripts = "", 0, 0
        self._buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_lang = a.get("lang", "")
        if tag == "script":
            self.scripts += 1
            if (a.get("type") or "").lower() == "application/ld+json":
                self.cur, self._buf = "jsonld", []
        if tag in self.SKIP:
            self.skip += 1
        if tag in ("title", "h1", "h2"):
            self.cur, self._buf = tag, []
        if tag == "meta":
            k = (a.get("name") or a.get("property") or "").lower()
            if k:
                self.meta[k] = a.get("content", "")
        if tag == "link":
            self.links.append(a)
        if tag == "a" and a.get("href"):
            self.anchors += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        if self.cur == "jsonld" and tag == "script":
            self.jsonld.append("".join(self._buf)); self.cur = None
        elif self.cur == tag:
            val = " ".join("".join(self._buf).split())
            if tag == "title": self.title = val
            elif tag == "h1": self.h1.append(val)
            elif tag == "h2": self.h2.append(val)
            self.cur = None

    def handle_data(self, data):
        if self.cur:
            self._buf.append(data)
        if not self.skip:
            self.text.append(data)

    def words(self):
        return len(" ".join(self.text).split())


def jsonld_types(blocks):
    types, bad = [], 0
    for b in blocks:
        try:
            data = json.loads(b)
        except Exception:
            bad += 1; continue
        stack = [data]
        while stack:
            o = stack.pop()
            if isinstance(o, list): stack.extend(o)
            elif isinstance(o, dict):
                t = o.get("@type")
                if t: types.extend(t if isinstance(t, list) else [t])
                stack.extend(v for v in o.values() if isinstance(v, (dict, list)))
    return types, bad


def parse_robots(txt):
    """Returns {agent_lower: [(allow:bool, path)]}."""
    groups, cur, last_was_agent = {}, [], False
    for line in txt.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line: continue
        k, v = (s.strip() for s in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if not last_was_agent: cur = []
            cur.append(v.lower()); groups.setdefault(v.lower(), []); last_was_agent = True
        elif k in ("allow", "disallow"):
            last_was_agent = False
            for agent in cur:
                groups[agent].append((k == "allow", v))
        else:
            last_was_agent = False
    return groups


def robots_allows(groups, agent, path="/"):
    rules = groups.get(agent.lower())
    if rules is None: rules = groups.get("*", [])
    best = (-1, True)
    for allow, p in rules:
        if p == "": continue  # "Disallow:" (empty) allows everything
        if path.startswith(p.rstrip("*").rstrip("$")) and len(p) > best[0]:
            best = (len(p), allow)
    return best[1]


def audit_robots(base):
    st, _, body, _ = fetch(urljoin(base, "/robots.txt"))
    if st != 200 or "<html" in body[:500].lower():
        add("WARN", "robots", f"/robots.txt missing or not plain text (HTTP {st}); every bot is allowed by default, but no Sitemap: line is advertised")
        return [], {}
    groups = parse_robots(body)
    blocked = [(t, kind) for t, kind in ROBOTS_TOKENS.items() if not robots_allows(groups, t)]
    for t, kind in blocked:
        level = "FAIL" if kind in ("search", "user") else "INFO"
        why = "it can't cite or link you" if kind != "training" else "future models won't learn about you from your own site (a business choice)"
        add(level, "robots", f"robots.txt blocks {t} ({kind} bot): {why}")
    if not blocked:
        add("PASS", "robots", "robots.txt allows the AI search, user and training bots checked")
    sitemaps = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", body)
    if sitemaps: add("PASS", "robots", f"robots.txt advertises {len(sitemaps)} sitemap(s)")
    else: add("WARN", "robots", "robots.txt has no Sitemap: line")
    return sitemaps, groups


def audit_sitemap(base, listed):
    urls, seen, queue = [], set(), list(listed) or [urljoin(base, "/sitemap.xml")]
    while queue and len(seen) < 20:
        u = queue.pop(0)
        if u in seen: continue
        seen.add(u)
        st, _, body, _ = fetch(u)
        if st != 200 or "<html" in body[:300].lower():
            add("FAIL" if not listed and u.endswith("/sitemap.xml") else "WARN", "sitemap", f"{u} → HTTP {st}{' (HTML, not XML)' if st == 200 else ''}")
            continue
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body)
        if "<sitemapindex" in body: queue.extend(locs)
        else: urls.extend(locs)
        lastmods = re.findall(r"<lastmod>([^<]+)</lastmod>", body)
        if "<urlset" in body and locs:
            if not lastmods: add("WARN", "sitemap", f"{u}: no <lastmod> (freshness is a ranking signal for answer engines)")
            elif len(set(lastmods)) == 1 and len(lastmods) > 5: add("WARN", "sitemap", f"{u}: every <lastmod> is identical ({lastmods[0]}); use the real change date per page")
            if "hreflang" in body: add("PASS", "sitemap", f"{u}: hreflang alternates present")
    if urls: add("PASS", "sitemap", f"{len(urls)} URLs in the sitemap(s)")
    return urls


def audit_index(base, n_sitemap=0):
    """Search-index readiness: ChatGPT search and Copilot retrieve through Bing,
    AI Overviews through Google. Looks for public evidence of webmaster
    verification; the index itself is only visible inside the webmaster tools."""
    host = urlparse(base).netloc
    st, _, html, _ = fetch(base)
    p = Page()
    try: p.feed(html)
    except Exception: pass
    bing = "msvalidate.01" in p.meta
    google = "google-site-verification" in p.meta
    st2, _, body2, _ = fetch(urljoin(base, "/BingSiteAuth.xml"))
    if st2 == 200 and "<users>" in body2.lower(): bing = True
    txt = []
    for name in {host, host[4:] if host.startswith("www.") else host}:
        try:
            dst, _, dbody, _ = fetch(f"https://dns.google/resolve?name={name}&type=TXT")
            txt += [a.get("data", "") for a in json.loads(dbody).get("Answer", [])] if dst == 200 else []
        except Exception: pass
    if any("google-site-verification" in t for t in txt): google = True
    if any("ms=" in t.lower() or "msvalidate" in t.lower() for t in txt): bing = True
    key = os.environ.get("BING_WEBMASTER_API_KEY")
    if key:
        try:
            from urllib.parse import quote
            ist, _, ibody, _ = fetch(f"https://ssl.bing.com/webmaster/api.svc/json/GetUrlInfo?apikey={key}&siteUrl={quote(base + '/')}&url={quote(base + '/')}")
            info = json.loads(ibody).get("d") if ist == 200 else None
            if info: add("PASS", "index", f"Bing Webmaster API: home page known to Bing (last crawled {info.get('LastCrawledDate', '?')})"); bing = True
            else: add("WARN", "index", f"Bing Webmaster API: no data for the home page (HTTP {ist}); is the site added and verified?")
        except Exception as e:
            add("INFO", "index", f"Bing Webmaster API check failed: {e}")
    if bing: add("PASS", "index", "Bing Webmaster verification found (meta tag, BingSiteAuth.xml or DNS)")
    else: add("WARN", "index", "no Bing Webmaster verification visible (meta msvalidate.01, /BingSiteAuth.xml or DNS). ChatGPT search and Copilot retrieve through Bing: verify the site at bing.com/webmasters (import from Google Search Console is quickest; a DNS CNAME verification is invisible to this check) and submit the sitemap")
    if google: add("PASS", "index", "Google Search Console verification found")
    else: add("INFO", "index", "no Google Search Console verification visible (it may be a DNS record on another name or a GA/GTM verification)")
    add("INFO", "index", f"manual check: https://www.bing.com/search?q=site%3A{host} and https://www.google.com/search?q=site%3A{host}; "
        + (f"compare the result count with the {n_sitemap} sitemap URLs: well under half means pages are missing from the index (verify, submit the sitemap, add IndexNow)" if n_sitemap else "0 results = not indexed"))


def audit_llms(base):
    st, h, body, _ = fetch(urljoin(base, "/llms.txt"))
    ct = (h.get("Content-Type") or h.get("content-type") or "").lower()
    if st != 200:
        add("INFO", "llms.txt", f"/llms.txt not found (HTTP {st}). Optional: cheap to add, but few AI bots fetch it today")
    elif "<html" in body[:500].lower() or "text/html" in ct:
        add("FAIL", "llms.txt", "/llms.txt returns an HTML page (an SPA fallback?), not Markdown text; serve a real file or a 404")
    else:
        ok = body.lstrip().startswith("# ")
        add("PASS" if ok else "WARN", "llms.txt", f"/llms.txt is text ({len(body)} chars){'' if ok else '; spec: start with an H1 \"# Name\" then a \"> summary\" line'}")


def audit_page(url, bots=True):
    st, h, html, final = fetch(url)
    area = urlparse(url).path or "/"
    if st != 200:
        add("FAIL", area, f"HTTP {st} for the browser fetch"); return
    p = Page()
    try: p.feed(html)
    except Exception: pass
    words = p.words()
    if words < 80:
        add("FAIL", area, f"only {words} words in the raw HTML ({p.scripts} scripts): AI crawlers don't run JavaScript, so this page looks empty to them. Server-render or pre-render it")
    elif words < 300:
        add("WARN", area, f"{words} words of text without JavaScript; thin for an answer engine to quote")
    else:
        add("PASS", area, f"{words} words readable without JavaScript")
    xrt = (h.get("X-Robots-Tag") or h.get("x-robots-tag") or "").lower()
    robots_meta = p.meta.get("robots", "").lower()
    for src, val in (("meta robots", robots_meta), ("X-Robots-Tag", xrt)):
        if "noindex" in val: add("FAIL", area, f"{src} says noindex")
        if "nosnippet" in val: add("WARN", area, f"{src} says nosnippet: Google won't use the text in AI Overviews/AI Mode")
    if not p.title: add("FAIL", area, "no <title>")
    elif len(p.title) > 65: add("WARN", area, f"title is {len(p.title)} chars (aim for under 60): {p.title[:70]}…")
    desc = p.meta.get("description", "")
    if not desc: add("WARN", area, "no meta description")
    if len(p.h1) != 1: add("WARN", area, f"{len(p.h1)} <h1> tags (want exactly one, saying what the page answers)")
    if len(p.h2) < 2 and words >= 300: add("WARN", area, "fewer than 2 <h2> sections; answer engines lift passages section by section")
    q = sum(1 for x in p.h2 if x.endswith("?"))
    if q: add("PASS", area, f"{q} question-style <h2> headings")
    canon = [l.get("href") for l in p.links if (l.get("rel") or "").lower() == "canonical"]
    if not canon: add("WARN", area, "no canonical link")
    elif urlparse(urljoin(url, canon[0])).netloc != urlparse(final).netloc:
        add("WARN", area, f"canonical points to another host: {canon[0]}")
    alts = [l for l in p.links if (l.get("rel") or "").lower() == "alternate" and l.get("hreflang")]
    if alts: add("PASS", area, f"{len(alts)} hreflang alternates")
    if not p.html_lang: add("WARN", area, "<html> has no lang attribute")
    og = [k for k in ("og:title", "og:description", "og:image") if k in p.meta]
    if len(og) < 3: add("WARN", area, f"Open Graph incomplete ({', '.join(og) or 'none'}); links shared in chats and AI apps preview badly")
    types, bad = jsonld_types(p.jsonld)
    if bad: add("FAIL", area, f"{bad} JSON-LD block(s) are invalid JSON")
    if types: add("PASS", area, f"JSON-LD: {', '.join(sorted(set(types)))}")
    else: add("INFO", area, "no JSON-LD (helps Google/Bing understand entities; no proven citation lift on its own)")
    if not re.search(r"\b(20\d\d)\b", " ".join(p.text)) and "article:modified_time" not in p.meta and "dateModified" not in html:
        add("INFO", area, "no visible date or dateModified; fresh, dated pages are favoured for time-sensitive questions")
    # Same page as each AI bot: blocked by a firewall / bot protection?
    for name, ua in (UA_BOTS.items() if bots else ()):
        bst, _, bhtml, _ = fetch(url, ua=ua)
        if bst != 200:
            add("FAIL", area, f"{name} user agent gets HTTP {bst} (firewall, CDN bot protection or WAF?)")
        elif abs(len(bhtml) - len(html)) > max(2000, 0.5 * len(html)):
            add("WARN", area, f"{name} gets a very different page ({len(bhtml)} vs {len(html)} bytes): challenge page or cloaking?")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--sample", type=int, default=5, help="sitemap pages to audit when only the home URL is given")
    ap.add_argument("--all", action="store_true", help="audit every sitemap URL (titles, headings, words); bot user-agent checks stay on the first 5 pages")
    a = ap.parse_args()
    base = "{0.scheme}://{0.netloc}".format(urlparse(a.urls[0]))
    sitemaps, _ = audit_robots(base)
    sm_urls = audit_sitemap(base, sitemaps)
    audit_llms(base)
    audit_index(base, len(sm_urls))
    norm = lambda u: u.rstrip("/") or u
    pages = list(dict.fromkeys(a.urls))
    if a.all and sm_urls:
        have = {norm(u) for u in pages}
        pages += [u for u in sm_urls if norm(u) not in have]
    elif len(pages) == 1 and sm_urls:
        step = max(1, len(sm_urls) // a.sample)
        have = {norm(u) for u in pages}
        pages += [u for u in sm_urls[::step] if norm(u) not in have][: a.sample]
    for i, u in enumerate(pages):
        audit_page(u, bots=i < 5)
        if a.all: time.sleep(0.3)  # polite crawl
    order = {"FAIL": 0, "WARN": 1, "INFO": 2, "PASS": 3}
    counts = {k: sum(1 for r in results if r[0] == k) for k in order}
    lines = [f"# AI visibility audit: {base}", "",
             f"**{counts['FAIL']} fail · {counts['WARN']} warn · {counts['INFO']} info · {counts['PASS']} pass** "
             f"({len(pages)} pages checked)", ""]
    for lvl in order:
        rows = [r for r in results if r[0] == lvl]
        if not rows: continue
        lines.append(f"## {lvl}")
        lines += [f"- **{area}**: {msg}" for _, area, msg in rows]
        lines.append("")
    report = "\n".join(lines)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f: f.write(report)
    sys.stdout.reconfigure(encoding="utf-8")
    print(report)
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
