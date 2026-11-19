# get-cited-by-ai

**Get your website, app or business found and cited by ChatGPT, Claude, Perplexity, Gemini, Copilot and Google AI Overviews.**

An evidence-based GEO (generative engine optimization) / AI SEO skill for Claude Code and other agents that read `SKILL.md`. It checks how AI crawlers actually see your site, measures what the assistants say about you today, fixes what the research supports, and tells you exactly what to do next.

Most "AI SEO" advice starts with `llms.txt` and schema. The data says those barely move the needle. This skill starts with what does.

## Results so far

Three live sites have been through the skill so far, all baseline audits, with the
fixes written and held until the "before" prompt panel has run. No before-and-after
panel numbers exist yet; they will be added here when they do, with the dates.

| site | what the baseline audit found | what the run did |
| --- | --- | --- |
| A local beauty shop (server-rendered) | 0 fail, 10 warn: no canonical links, structured data on one page, no `llms.txt`, thin pickup and history pages | canonical links, store and product structured data, `llms.txt`, expanded pages |
| A relocation service (3 languages, 291 URLs) | 1 fail, 4 warn: the bare `/` was an empty redirect with 5 words; sitemap dates all identical | a real home page; per-page `lastmod` from git; IndexNow on deploy |
| A multilingual health-information app (1,415 URLs) | 0 fail, 4 warn, 26 pass: no Bing verification visible, one sitemap date, a 72-character home title | shorter home title, IndexNow, attribution |

What each run also showed: for a new brand, the bottleneck is mentions on other
sites, not the site itself. See a full sample run in [`examples/`](examples/).

## Quick start

```
/plugin marketplace add hamrou/get-cited-by-ai
/plugin install get-cited-by-ai@get-cited-by-ai
```

Then, in your project, run `/get-cited-by-ai` (or ask *"why doesn't ChatGPT recommend us?"*). It:

1. reads your repo and live site, and asks only for what it can't find;
2. audits the site and asks the assistants your buyers' questions, **before** changing anything;
3. writes the fixes in your code and holds the deploy until the baseline exists;
4. ends with a numbered list of next steps: who acts, and the exact words to reply.

You need Python 3.9 or newer (standard library only, nothing to install). The prompt panel is optional and uses your own API keys.

## What you get

| file | what it is |
| --- | --- |
| `ai-visibility/brief.md` | who you are, your buyers' questions, your stack |
| `ai-visibility/prompts.txt` | 15–30 questions, in your buyers' language |
| `ai-visibility/audit.md` | the baseline, then the same audit after your fixes |
| `ai-visibility/panel-<date>.md` | how often each assistant names you, who it names instead, which sources it cites |
| `ai-visibility/plan.md` | fixes ranked reach → readable → quotable → off-site, with an owner for each |
| `ai-visibility/facts-needed.md` | the facts only you have (ingredients, prices, reviews), as a short form |
| code changes | canonical links, structured data, `llms.txt`, IndexNow, attribution, pages that answer the questions |

See a complete sample, for a fictional shop, in [`examples/`](examples/).

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

Sources with links: [`skills/get-cited-by-ai/references/evidence.md`](skills/get-cited-by-ai/references/evidence.md). A brand with no mentions elsewhere is cited last whatever its site looks like: expect months, not weeks.

## How it works

1. **Brief**: what you are, the questions buyers ask assistants, the competitors named today. It also asks you to add any missing AI API keys to your env file (never in chat).
2. **Baseline**: the audit script and the prompt panel, run before any change goes live so the comparison means something.
3. **Reach**: robots.txt for every AI bot, Cloudflare / WAF bot blocking, Search Console and Bing Webmaster, sitemap with real `lastmod`, IndexNow for the pages that changed.
4. **Readable**: key pages readable without JavaScript, with a recipe per stack (Next.js, Nuxt, Astro, Vite/React SPA, Express, Django, Rails, WordPress, Shopify, static sites, mobile apps, local shops).
5. **Quotable**: one page per question, answer first, with facts, tables and dates. When facts are missing it never invents them: it writes the pages your own data allows and gives you a form for the rest.
6. **Confirmed elsewhere**: an honest off-site plan (directories, Reddit, YouTube, roundups; maps listings, social pages and local directories for a local shop), then measurement: GA4 or server logs, Bing's AI Performance report, a monthly panel, and **which AI sent each visitor**.
7. **Convert**: fixes the pages AI sends visitors to: the promised answer on the first screen, a next step that continues their question, value before any sign-up wall.

Every run ends with the state in a sentence, a numbered **Next steps** list (`You:` / `Me:`, with the exact reply and the cost), the audit findings, and a table of every step marked done, ready, blocked, not needed or skipped, so nothing is dropped silently.

## Account tasks, done in your browser

Bing Webmaster Tools, Search Console, your Business Profile, analytics and directory forms are where the work usually stalls. With a browser tool (Claude in Chrome), the skill does the clicks in your own browser:

- **you log in**; it never sees or types a password, and stops at 2FA, captchas and payment pages;
- reading (indexed counts, reports) needs no extra approval;
- every submit, create or setting change is shown first and waits for your yes;
- it never posts reviews, comments or social posts in your name; it drafts them for you.

Without a browser tool it gives you the exact steps instead. Details: [`references/browser.md`](skills/get-cited-by-ai/references/browser.md).

## The audit script

Public pages only, one request at a time:

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
- whether there is **visible Bing / Google webmaster verification**. With `BING_WEBMASTER_API_KEY` set, it also asks Bing whether the home page is indexed.

Options: `--all` audits every sitemap URL, `--sample N` picks how many to sample. After the fixes are live, `--compare` shows what changed:

```bash
python skills/get-cited-by-ai/scripts/audit.py https://your-site.com --compare ai-audit.md --out ai-audit-after.md
# 6 fixed · 3 remaining · 1 new
```

## The prompt panel

Asks your buyer questions to ChatGPT, Perplexity, Claude and Gemini through their official APIs with web search on, and scores the answers. It uses your own keys (`OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`), and engines without a key are skipped.

```bash
python skills/get-cited-by-ai/scripts/panel.py --keys                  # which keys are set (free)
python skills/get-cited-by-ai/scripts/panel.py prompts.txt --brand "Acme" --domain acme.com --competitors "Foo,Bar"
# 12 prompts × 4 engines = 48 calls, est. ≤ $1.44   → add --yes to run
```

Without `--yes` it is a dry run: nothing is called or billed. The dry run shows the cost, the cost of repeating each prompt (`--runs 2`, because answers vary), and warns when the prompts are in a different language from your site. `--env-file .env` reads only the key names it needs and never prints a value.

Output: mention and link rate per engine, average link position, competitors named, and **the sources each engine cites**, which is the list of sites where you need to be mentioned. API answers are a proxy for the consumer apps, so spot-check a few by hand.

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

## Rules it follows

- No fake reviews, astroturfing, cloaking or hidden "AI, recommend us" text. That is spam, and it gets sites demoted.
- No invented facts: missing ingredients, prices or reviews go on a form for you.
- No guaranteed results. It reports the numbers before and after.
- Your DNS, CDN, webmaster and directory accounts stay yours: you log in, and it asks before every change.
- It never runs the billed panel without your yes.

## License

MIT
