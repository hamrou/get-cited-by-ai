# Measuring AI discovery

All referrer-based numbers are a floor: assistant apps (ChatGPT mobile, Claude
desktop) often send no referrer and land in Direct.

## GA4: an "AI assistants" channel

Admin → Data display → Channel groups → copy the default group → add channel
"AI assistants", condition *Source matches regex*, and move it **above
Referral**:

```
^(.*\.)?(chatgpt\.com|chat\.openai\.com|openai\.com|perplexity\.ai|claude\.ai|gemini\.google\.com|bard\.google\.com|copilot\.microsoft\.com|edgeservices\.bing\.com|you\.com|phind\.com|meta\.ai|grok\.com|x\.ai|deepseek\.com|chat\.mistral\.ai|duckduckgo\.com/aichat)$
```

Don't restrict the medium: ChatGPT adds `utm_source=chatgpt.com` and those show
as `chatgpt.com / (not set)`. Newer GA4 properties may already have a built-in
AI channel; check before duplicating. Mark the key conversion (sign-up,
purchase) and compare its rate for AI traffic with organic search.

Without GA: the same regex over the server's Referer logs, plus
`utm_source=chatgpt.com` in the query string.

## Bing Webmaster Tools → AI Performance

Free for verified sites: citations in Copilot and Bing AI answers per page and
per query intent ("Citation share", "Topics"). Covers Microsoft surfaces only,
no clicks. Good early signal because ChatGPT search also leans on Bing.

## Google Search Console

AI Overviews / AI Mode impressions are counted inside normal Search
performance (Web). Watch impressions on the question-style queries in the
prompt set.

## The prompt panel (the real scoreboard)

Monthly, same 15–30 prompts from the brief, same engines (ChatGPT with search,
Perplexity, Gemini or AI Mode, Claude with web search, Copilot), logged out or a
clean profile, same language and country when possible. Record in
`ai-visibility/panel.md`:

| date | engine | prompt | mentioned | cited (link) | position | competitors named | sources cited |

Track: share of prompts where the brand is mentioned, share where it is linked,
and which third-party sources keep appearing (go get listed there). Answers vary
run to run; run each prompt 2–3 times before calling a change.

## Server logs

Count AI bot fetches per week (see crawlers.md) and which pages they fetch.
Pages never fetched by the search bots are not in their index yet: check
sitemap, internal links, IndexNow.
