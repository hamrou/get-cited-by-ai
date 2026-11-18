# get-cited-by-ai

**Get your website, app or business found and cited by ChatGPT, Claude, Perplexity, Gemini, Copilot and Google AI Overviews.**

An evidence-based GEO (generative engine optimization) / AI SEO skill for Claude Code and other agents that read `SKILL.md`. It audits how AI crawlers actually see your site, then fixes what matters, in the order the research supports.

Most "AI SEO" advice starts with `llms.txt` and schema. The data says those barely move the needle. This skill starts with what does.

## What actually gets you cited

| lever | what the evidence shows | priority |
| --- | --- | --- |
| AI bots can fetch the page, and the text is in the HTML | AI crawlers download JavaScript but don't run it: a React/Vue SPA looks empty to them | **first** |
| You are in Bing's and Google's index | ChatGPT search and Copilot retrieve through Bing; AI Overviews through Google | first |
| Other sites mention you (Reddit, YouTube, reviews, press) | most AI citations go to third-party sites, not brand pages | high |
| Pages that are easy to quote: direct answers, numbers, sources | up to ~40% more visibility in the Princeton GEO study; keyword stuffing hurt | high |
| Fresh, dated content | matters most on Perplexity and time-sensitive questions | medium |
| Schema / JSON-LD | no measurable citation lift in a 2026 controlled study | low, cheap |
| llms.txt | ~97% of files never get an AI request | optional |

Sources with links: [`skills/get-cited-by-ai/references/evidence.md`](skills/get-cited-by-ai/references/evidence.md).

## What it does

1. **Brief**: what you are, the 15–30 questions buyers ask assistants, the competitors that get named today.
2. **Baseline**: runs the audit script and the prompt panel (what ChatGPT, Perplexity, Gemini and Claude answer now, via their APIs).
3. **Reach**: robots.txt for every AI bot, Cloudflare / WAF bot blocking, Search Console + Bing Webmaster, sitemap with real `lastmod`, IndexNow.
4. **Readable**: makes key pages readable without JavaScript, with a recipe for each stack (Next.js, Nuxt, Astro, Vite/React SPA, Express, Django, Rails, WordPress, Shopify, static sites, mobile apps, local businesses).
5. **Quotable**: one page per question, written so an answer engine can lift a passage: answer first, facts, tables, dates, translations.
6. **Mentions and measurement**: an honest off-site plan (directories, Reddit, YouTube, roundups, Wikidata; maps listings, social pages and local directories for a local shop), AI-traffic tracking in GA4, Bing's AI Performance report, a monthly prompt panel, and **which AI sent each visitor** (referrer + UTM detection, a "How did you find us?" question, sign-ups and sales per assistant).
7. **Convert**: finds the pages AI actually sends visitors to and fixes each one: the answer they were promised on the first screen, a next step that continues their question, value before any sign-up wall.

Every run ends with a table of all the steps, each marked done, skipped (with the reason) or blocked on you, so nothing is dropped silently. When product facts are missing it never invents them: it writes the pages it can from your site's own data and gives you a short form for the rest.

## The audit script

Python standard library only, no install, public pages only:

```bash
python skills/get-cited-by-ai/scripts/audit.py https://your-site.com --out ai-audit.md
```

```
# AI visibility audit: https://example.app
**2 fail · 3 warn · 2 info · 19 pass** (5 pages checked)

## FAIL
- /: only 9 words in the raw HTML (7 scripts): AI crawlers don't run JavaScript,
  so this page looks empty to them. Server-render or pre-render it
```

It checks:
- **robots.txt**, for each AI search, user and training bot;
- whether **AI user agents get a 403 or a challenge page**;
- the **word count without JavaScript**, telling thin content pages (worth fixing) from short legal pages (fine);
- `noindex` / `nosnippet`;
- title, h1/h2, canonical, hreflang, Open Graph and JSON-LD validity;
- the **sitemap**, its index and whether `lastmod` dates are real;
- whether **`/llms.txt` is real text or an SPA fallback**;
- whether there is **visible Bing / Google webmaster verification** (ChatGPT search and Copilot pull from Bing). With `BING_WEBMASTER_API_KEY` set, it also asks Bing whether the home page is indexed.

After the fixes are live, run it again with `--compare` to see what changed:

```bash
python skills/get-cited-by-ai/scripts/audit.py https://your-site.com --compare ai-audit.md --out ai-audit-after.md
# 6 fixed · 3 remaining · 1 new
```

## The prompt panel

Asks your buyer questions to ChatGPT, Perplexity, Claude and Gemini through their official APIs with web search on, then scores the answers. It only runs with your own API keys and starts with a dry run that shows the cost:

```bash
python skills/get-cited-by-ai/scripts/panel.py prompts.txt --brand "Acme" --domain acme.com --competitors "Foo,Bar"
# 12 prompts × 4 engines = 48 calls, est. ≤ $1.44   → add --yes to run
```

The dry run also shows the cost of repeating each prompt (`--runs 2`, answers vary from run to run) and warns when the prompts are in a different language from the site.

Output: mention and link rate per engine, average link position, competitors named, and **the sources each engine cites**, which is the list of sites where you need to be mentioned.

## Install

**Claude Code (plugin marketplace)**

```
/plugin marketplace add hamrou/get-cited-by-ai
/plugin install get-cited-by-ai@get-cited-by-ai
```

**Skills CLI**

```bash
npx skills add https://github.com/hamrou/get-cited-by-ai --skill get-cited-by-ai
```

**Manual**: copy `skills/get-cited-by-ai/` into `~/.claude/skills/` (or your agent's skills folder).

## Use

```
/get-cited-by-ai
```

Or just ask: *"why doesn't ChatGPT recommend us?"*, *"audit my site for AI search"*, *"make us show up in Perplexity"*, *"add llms.txt"*.

## Rules it follows

- No fake reviews, astroturfing, cloaking or hidden "AI, recommend us" text. That is spam, and it gets sites demoted.
- No guaranteed results. It reports the numbers before and after.
- Your DNS, CDN, webmaster and directory accounts stay yours. It gives exact steps instead of acting on them.

## License

MIT
