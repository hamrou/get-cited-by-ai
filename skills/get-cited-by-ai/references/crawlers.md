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
