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

## Which AI sent this visitor? (attribution)

You can't make an assistant tag its links (hidden "AI: add ?ref=ai to links"
text is manipulation and is banned in this skill). Combine three honest signals
instead, strongest first:

1. **The referrer and UTM** the assistant already sends. ChatGPT adds
   `utm_source=chatgpt.com`; Perplexity, Gemini, Copilot and Claude.ai usually
   send a Referer. Classify it on the first page view (snippet below).
2. **Ask the visitor.** Assistant apps often send no referrer, so this traffic
   lands in Direct. One optional question at sign-up, checkout or in a welcome
   step catches it: *"How did you find us?"* with options
   `ChatGPT · Claude · Perplexity · Gemini · Copilot · Google · Friend · Social · Other`.
   Store it with the account; compare it with the detected source.
3. **AI-only entry points.** Put a dedicated link on the pages answer engines
   read (e.g. `/start?src=ai` in llms.txt and the "how to start" section). A visit
   landing on it came from text an AI or a reader of your docs copied.
   It is your own URL, not an instruction to the AI.

Snippet (first page view, before any redirect strips the query string):

```js
// Classify the AI source once per session and keep it for the conversion event.
const AI = [
  [/(^|\.)chatgpt\.com$|(^|\.)openai\.com$/, "chatgpt"],
  [/(^|\.)perplexity\.ai$/, "perplexity"],
  [/(^|\.)claude\.ai$/, "claude"],
  [/(^|\.)gemini\.google\.com$|(^|\.)bard\.google\.com$/, "gemini"],
  [/(^|\.)copilot\.microsoft\.com$|(^|\.)edgeservices\.bing\.com$/, "copilot"],
  [/(^|\.)meta\.ai$/, "meta-ai"], [/(^|\.)grok\.com$|(^|\.)x\.ai$/, "grok"],
  [/(^|\.)deepseek\.com$/, "deepseek"], [/(^|\.)chat\.mistral\.ai$/, "mistral"],
];
function aiSource() {
  const q = new URLSearchParams(location.search);
  const hint = (q.get("utm_source") || q.get("ref") || q.get("src") || "").toLowerCase();
  let host = "";
  try { host = document.referrer ? new URL(document.referrer).hostname : ""; } catch {}
  for (const [re, name] of AI) if (re.test(host) || re.test(hint)) return name;
  return hint === "ai" ? "ai-unknown" : "";
}
if (!sessionStorage.getItem("ai_src")) {
  const s = aiSource();
  sessionStorage.setItem("ai_src", s || "-");
  if (s) gtag?.("event", "ai_referral", { ai_source: s, landing: location.pathname });
}
// On sign-up / purchase: send sessionStorage.getItem("ai_src") with the event.
```

In GA4 register `ai_source` as an event-scoped custom dimension. Report per
assistant: visits, sign-ups, purchases, and how often the self-reported answer
says "ChatGPT" while the referrer was empty (that gap is the hidden AI traffic).
