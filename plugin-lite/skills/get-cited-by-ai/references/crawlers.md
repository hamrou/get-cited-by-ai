# AI crawlers and robots.txt

User agents change: confirm against each operator's own page before relying on
the list (OpenAI: platform.openai.com/docs/bots, Anthropic: support.anthropic.com
crawler article, Perplexity: docs.perplexity.ai bots, Google: "Google crawlers"
docs). The community list github.com/ai-robots-txt/ai.robots.txt tracks 150+.

| operator | search / index (citations) | user-triggered fetch | training |
| --- | --- | --- | --- |
| OpenAI | OAI-SearchBot | ChatGPT-User | GPTBot |
| Anthropic | Claude-SearchBot | Claude-User | ClaudeBot |
| Perplexity | PerplexityBot | Perplexity-User | – |
| Google | Googlebot (AI Overviews / AI Mode use the Search index) | – | Google-Extended (a robots token, not a crawler) |
| Microsoft | Bingbot (Copilot, and ChatGPT search via Bing) | – | – |
| Apple | Applebot | – | Applebot-Extended |
| Common Crawl | – | – | CCBot (feeds many models) |

User-triggered fetchers may ignore robots.txt (OpenAI says so for ChatGPT-User).
Blocking Google-Extended does not remove a site from AI Overviews; only
`nosnippet` / `max-snippet` / `noindex` limit that, and they also cut normal
snippets.

## Default robots.txt (allow discovery, keep private paths out)

```
User-agent: *
Disallow: /api/
Disallow: /admin
Disallow: /account

# Explicit for clarity; same rules as *
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
User-agent: Perplexity-User
Disallow: /api/
Disallow: /admin
Disallow: /account

Sitemap: https://example.com/sitemap.xml
```

To opt out of training only, add a group per training bot with `Disallow: /`
(GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, CCBot). This does not
affect citations by the search bots above.

## Checking real bot traffic

Server or CDN logs, grep the user agents above. Bots don't run analytics JS, so
GA never shows them. A healthy site sees OAI-SearchBot / Claude-SearchBot /
PerplexityBot fetch new pages within days of IndexNow or sitemap updates.

## Kimi, DeepSeek and Qwen: test retrieval, don't invent bots

Do not add unverified "KimiBot", "DeepSeekBot" or "QwenBot" tokens to
robots.txt. Use the providers' official page-retrieval APIs to test the exact
public URLs that matter, and inspect real server logs for observed user agents:

Ask each assistant by hand to read the page and note what it extracts.

Kimi URL Fetch returns the extracted Markdown; DeepSeek URL reading returns a
read-URL tool result; Qwen web extraction returns an extractor result. A failed
or empty extraction is a retrieval finding, not proof that the consumer app can
never cite the page. A successful fetch does not prove indexing or citation.
Official capability references are in `references/evidence.md`.
