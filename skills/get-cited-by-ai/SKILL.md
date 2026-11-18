---
name: get-cited-by-ai
description: Use when a website, SaaS, app, game, store or local business should be found, recommended or cited by AI assistants and answer engines (ChatGPT, Claude, Perplexity, Gemini, Copilot, Google AI Overviews and AI Mode). Covers GEO (generative engine optimization), AEO (answer engine optimization), LLMO, AI SEO and AI search visibility; auditing a site for AI crawlers (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot), robots.txt, Cloudflare bot blocking, JavaScript/SPA pages that AI bots can't read, server-side rendering and pre-rendering, sitemaps, IndexNow and Bing indexing, llms.txt, schema/JSON-LD, citable content, brand mentions on Reddit and YouTube, and tracking AI referral traffic in GA4. Triggers: "get cited by ChatGPT", "why doesn't ChatGPT recommend us", "show up in AI answers", "AI visibility audit", "rank in Perplexity", "optimize for AI Overviews", "add llms.txt".
---

# get-cited-by-ai

Answer engines recommend what they can **reach**, **read**, **quote** and see
**confirmed elsewhere**. Work in that order: a page a bot can't fetch or that is
empty without JavaScript never gets cited, however good the copy is.

Audit tool in this folder (stdlib Python, public pages only):

```bash
python "<this skill's folder>/scripts/audit.py" https://example.com --out ai-audit.md
```

It checks robots.txt for each AI bot, whether AI user agents get blocked by a
firewall, how many words are readable **without JavaScript**, title, h1/h2,
canonical, hreflang, Open Graph, JSON-LD, sitemap and lastmod, and llms.txt. It
samples 5 sitemap pages (`--sample N`) or audits the URLs you pass. After the
fixes are live, re-run it with `--compare <the baseline report>`: it lists what
was fixed, what is new and what remains.

## What the evidence says (set expectations with the user)

| lever | evidence | priority |
| --- | --- | --- |
| Bots allowed + content in raw HTML | AI crawlers fetch but don't run JS (Vercel/MERJ crawl data) | **first** |
| Being in Bing's and Google's index | ChatGPT search, Copilot and part of Perplexity retrieve from Bing; AI Overviews from Google | first |
| Third-party mentions (reviews, Reddit, YouTube, press, Wikipedia) | most AI citations go to third-party sites; YouTube mentions correlate strongest with AI visibility (Ahrefs) | high |
| Citable writing: direct answers, statistics, quotes, cited sources | Princeton GEO paper: up to ~40% more visibility in lab tests; keyword stuffing hurt | high |
| Freshness (real dates, regular updates) | recency matters most on Perplexity and news-like questions | medium |
| JSON-LD / schema | no measurable citation lift in a controlled study (Ahrefs 2026); still helps search engines | low, cheap |
| llms.txt | ~97% of files get zero AI requests; no study shows a citation lift | lowest, optional |

Say this plainly when the user asks for "llms.txt and schema" first: they are
cheap extras, not the work. If they still want them first, do them (an hour of
work, no harm) in the same change as the Step 2 fixes, and keep the rest of the
order. Sources: `references/evidence.md`.

**Advice only?** If the user wants a plan, not changes, run Steps 0–1 and write
`ai-visibility/plan.md`; skip the code. If the audit can't run (no live site yet),
check the build output instead: `curl` the local server or open `dist/index.html`
and count the words outside `<script>`.

## Step 0: intake

Fill what you can from the repo and the live site; ask the user only for what is
missing, at most 4 questions in one message (usually: the prompt set, the
competitors, the price). One question is always asked, because the audit can't
see a DNS verification: "Is the site already added in Bing Webmaster Tools and
Google Search Console?"

**Ask for the AI keys first.** The panel can only measure the engines it has
a key for, and a baseline on one engine out of four is a weak baseline. Before
anything else, run (free, no call, values never printed; pass every env file
the project has):

```bash
python "<this skill's folder>/scripts/panel.py" --keys --env-file .env
```

If an engine is missing, the first message to the user asks for it, in the
same message as the intake questions, with the lines it printed:

> The panel can ask ChatGPT, Perplexity, Claude and Gemini. I found a key for
> OpenAI only. To measure the other three, add these lines to `shop/.env`
> (never paste a key in chat): `PERPLEXITY_API_KEY=…` (create it at …),
> `ANTHROPIC_API_KEY=…`, `GEMINI_API_KEY=…`. A 24-question baseline costs
> about $0.25 to $1 per engine. Reply "keys added", or "continue" to measure
> OpenAI only.

Check that the env file is in `.gitignore` before pointing the user at it.
Don't wait for the answer: go on with the audit and the code. Run `--keys`
again before the panel's dry run, so keys added meanwhile are counted.

Write `ai-visibility/brief.md`:

- **The entity**: name, one-line category ("the real-life politics simulator"),
  who it is for, price/free tier, where it is used (web, app store, city).
- **The prompt set**: 15–30 questions a buyer would type into an assistant, in
  their words and languages: category ("best X for Y"), comparison ("X vs Y",
  "alternatives to Y"), problem ("how do I …"), and brand ("is X legit", "X price").
  Write them in the language the buyers type in (the site's `<html lang>`
  unless the user says otherwise): a French shop gets French prompts. A local
  business gets its city or country in the category prompts ("meilleur
  shampoing naturel à Libreville").
- **Competitors** the assistant names today for those prompts.
- **The stack** (read the repo: framework, SSR or SPA, hosting/CDN, i18n).

## Step 1: baseline

The baseline is the "before" picture. Run the audit and the prompt panel
**before any on-site change is deployed**: a panel run after the deploy can't
show what the changes did. Holding the deploy never means holding the work:
write every code fix in the same session (IndexNow, the attribution, the pages)
and mark it `ready`.

1. Run `audit.py` on the live site and save the report. Its `index` lines say
   whether Bing/Google verification is visible; with `BING_WEBMASTER_API_KEY`
   set it also asks Bing whether the home page is indexed.
2. **The prompt panel**: write the prompt set to `ai-visibility/prompts.txt`
   (one per line) and run the panel through the engines' official APIs:

   ```bash
   python "<this skill's folder>/scripts/panel.py" ai-visibility/prompts.txt      --brand "Name" --domain example.com --competitors "A,B,C" --out ai-visibility/panel
   ```

   Run the dry run yourself, right away, without asking: without `--yes` it
   calls no API and costs nothing. It prints which
   engines have a key in the environment and the cost estimate (about
   $0.01–0.04 per prompt per engine). Ask the user with those concrete
   numbers ("22 calls on OpenAI + Perplexity, at most $0.88: run it?"), not
   "which keys do you have?". Never ask for key values in chat. If no key is
   set in the environment, look for the project's own env files (`.env`,
   `server/.env`) and pass them with `--env-file` (it reads only the four key
   names, never prints values); otherwise the user sets them in their shell.
   Answers vary from run to run, so the dry run also prints the cost of
   `--runs 2` and `--runs 3`: recommend `--runs 2` for the baseline when the
   total stays under about $5. If the dry run warns that the prompts are in
   another language than the site, fix `prompts.txt` before asking.
   The user approves the billed run, not you. Only add
   `--yes` after a yes: it bills the user's API keys
   (OPENAI_API_KEY, PERPLEXITY_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY;
   engines without a key are skipped). It writes `panel-<date>.md/.json`:
   mention and link rates per engine, competitors named, and the most cited
   sources, which is the off-site target list for Step 5.
   If the user has no API keys, ask them to run 10 prompts by hand in ChatGPT
   (search on), Perplexity, Gemini and Claude and paste the answers. Either
   way, never automate logged-in consumer sessions. API answers are a proxy
   for the apps; a few manual spot checks keep it honest.
3. Note current AI referral traffic and **the pages AI sends people to**, with
   their conversion rate (see `references/measure.md`). Few sessions is a hint,
   not a ranking: say so. GA only counts visitors who accepted the consent
   banner; if the server keeps access logs, count AI referrers there too.
4. "No Bing verification visible" in the audit is a question for the user, not
   a finding: a DNS CNAME verification is invisible to the audit. Use the
   Step 0 answer. Report it as a gap, or put "verify in Bing" on the user's
   task list, only after the user says the site isn't there. Either way, open
   the `site:` link the audit prints and compare Bing's result count with the
   sitemap count: "indexed" is not enough if Bing knows 50 of 212 pages.

## Step 2: reach (fix every FAIL first)

- **robots.txt**: allow the search and user bots (OAI-SearchBot, ChatGPT-User,
  Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User, Bingbot,
  Googlebot). Training bots (GPTBot, ClaudeBot, Google-Extended, CCBot) are a
  business decision: blocking them doesn't stop citations, allowing them helps
  future models know the brand. Template: `references/crawlers.md`.
- **CDN / firewall**: Cloudflare and other WAFs can block AI bots by default.
  If the audit shows a bot user agent getting 403/challenge pages, the user must
  change it in the dashboard (their account, their decision). Cloudflare: the
  domain's **AI Crawl Control** page (allow the search/user bots per crawler),
  **Security → Bots** (Bot Fight Mode challenges bots; Super Bot Fight Mode can
  allow "verified bots"), and the "Block AI bots" / managed robots.txt toggles.
  Menu names move; confirm on Cloudflare's docs before giving steps. The audit
  sends bot user agents from a normal IP, so a CDN that verifies bot IPs may
  pass it and still block, or block it and still pass the real bot: confirm in
  the CDN's bot/firewall logs.
- **Index (user task)**: verify the site in Google Search Console and Bing
  Webmaster Tools (DNS TXT) and submit the sitemap. With a browser tool, do it
  with them (see "Doing the user's tasks in their browser").
- **IndexNow (code task, yours)**: add the key file at the root and a ping to
  api.indexnow.org on deploy or publish, in the same change as the other
  fixes. Ping only the URLs that changed in that deploy (all of them on the
  first one only). Recipe: `references/stacks.md`.
- **Sitemap**: every public page, real per-page `<lastmod>`, hreflang for
  translations, an index if there are several. Advertise it in robots.txt.

## Step 3: readable (the page must exist without JavaScript)

If the audit says a key page has <80 words in raw HTML, that page is invisible to
AI crawlers. Pick the cheapest fix for the stack (`references/stacks.md`):
static generation or SSR for the marketing pages, pre-rendering at build, or
server-rendered landing pages beside the SPA. The app itself can stay a SPA; the
pages that answer questions cannot. Same content for bots and people: never
serve bots different text (cloaking).

## Step 4: quotable (pages that answer the prompt set)

This step is the high-priority on-site work. The canonical, JSON-LD and
llms.txt extras at the end of it don't replace it.

Map every prompt in the brief to one page that answers it. The page set, by
project type, is in `references/stacks.md`; most projects need: home (what it is,
in one sentence), how it works, pricing, FAQ, "X vs Y" / "alternatives to Y"
(honest, dated), one page per use case/audience/place, about/press (facts,
founder, dates, contact), changelog or blog for freshness.

Write each page so a passage can be lifted on its own:

- **First sentence answers the question**, in a full declarative sentence that
  names the entity ("BlindSpot is a free browser politics simulator where…").
  Same category phrase on every page: assistants match categories.
- **One H1; H2s phrased as the questions people ask**; short sections, each
  starting with its answer.
- **Specific facts**: numbers, prices, dates, counts, limits, with sources
  linked for any outside claim (the GEO paper's strongest levers: statistics,
  quotations, citations). Keep live facts (prices, counts) rendered from the
  same source as the product so they never go stale.
- **Tables and lists** for comparisons, specs and steps.
- **Visible "updated" date**; update key pages at least quarterly.
- **Translations** as real pages per language with hreflang, if the audience is
  multilingual (assistants answer in the asker's language).
- Then add the cheap extras (skippable; do them because they are cheap and help
  normal search, not for citations): JSON-LD matching the page (Organization, WebSite,
  Product/SoftwareApplication/VideoGame/LocalBusiness, FAQPage, BreadcrumbList,
  Article with dateModified), Open Graph, canonical, and an llms.txt generated from
  the same live facts (H1 name, `>` summary, links to the key pages).

**When product facts are missing** (ingredients, specs, reviews), never invent
them, and don't stop at the extras either. In the same session:

1. Write the pages that need no new facts, from the repo and the live catalog:
   how ordering works, delivery and pickup, prices, payment, returns, contact,
   opening hours, the about page.
2. Expand the content pages the audit marks thin from data the site already
   has (the pickup points list, the catalog, the shipping rules). Legal pages
   (terms, privacy) can stay short: the audit marks those INFO.
3. Write `ai-visibility/facts-needed.md`: a short form the user fills in, one
   line per fact, grouped by the page it unblocks ("Guide: which shampoo for
   which hair type → needs: hair types per product, ingredients, scent").
   Ask for reviews with their source (name or platform, date).

## Step 5: confirmed elsewhere (off-site)

From the Step 1 source list, list where assistants already look for this
category, and plan presence there, honestly:

- **Directories and stores** for the category (Product Hunt, AlternativeTo,
  G2/Capterra, itch.io, app stores, Google Business Profile / Bing Places /
  Apple Business Connect for local).
- **Reddit and forums**: the founder answers questions as themselves, with
  disclosure. No sock puppets, no bought upvotes.
- **YouTube**: a demo, a how-to, creator coverage (disclosed if paid).
- **Press and roundups**: pitch the "best X" list articles that assistants cite.
- **Wikipedia/Wikidata** only if the entity meets notability; never write your
  own article (conflict of interest). A Wikidata item with official site and
  socials is fine when the entity is real and notable.
- Consistent name, one-liner and links everywhere (sameAs in Organization JSON-LD).

**A local shop or small store** doesn't belong on Product Hunt or G2. Its
off-site list (maps listings, social pages, local directories and press) is in
`references/stacks.md`, "Local shop or small store".

**A new, unknown brand** has no third-party footprint, and that is the real
bottleneck: on-site work makes it citable, mentions make it recommended. Plan
for months, not weeks. Start where a small brand can earn a mention: 5–10
directory listings, answering existing Reddit/forum threads, one YouTube demo,
one comparison or "best X" roundup pitch a week, and a launch (Product Hunt,
Hacker News Show HN, the niche's subreddit) when there is something to show.
Long-tail pages (one per use case, place, audience) get cited before the broad
category ever is.

## Step 6: measure and repeat

Set up what `references/measure.md` describes (GA4 AI channel, Bing AI
Performance report, server-log bot hits, the monthly prompt panel), plus
**which AI sent each visitor**: classify the referrer/UTM on landing, ask
"How did you find us?" (with ChatGPT, Claude, Perplexity, Gemini, Copilot as
options) at sign-up or checkout, and carry the source into the conversion event. Re-run the
audit and the prompt panel after 4–6 weeks; retrieval engines move in days to
weeks, model knowledge only with new training cycles.

**Re-check dates**: don't leave them in a file for the user to remember. If the
harness can schedule work (Claude Code: `/schedule` creates a scheduled agent;
other agents: cron or the CI scheduler), offer to schedule the Bing indexed-count
check (1–2 weeks after verification) and the audit + panel re-run (4–6 weeks).
Cloud routines run on a fresh checkout: they can't read local `.env` files or
untracked files, and a spending cap in the prompt is only an instruction. So
by default schedule **reminder-only** routines (they say what to run and the
last baseline; no API keys, no spend), and run the billed panel locally in a
session when the reminder comes. Never put an API key in a scheduled prompt.

## Step 7: convert the visitors AI sends

A cited page that loses the visitor wastes the citation. For each page the
AI channel lands on (Step 1, item 3), check it against the question that sent
the visitor there (the prompt set says what they asked):

- **The first screen confirms the answer** they were promised: same words as
  the question, what it costs, who it's for. No generic hero.
- **One next step that continues that question**, not the site's default CTA.
  A reader of "how to start a mobile grooming business" gets the grooming course
  and its price, or the free practice test; not a newsletter box.
- **Value before a wall**: a free tool, sample, calculator, demo or practice
  test reachable without sign-up. AI visitors arrive mid-research and leave
  when asked to commit first.
- **Proof near the step**: real numbers, real reviews with sources, refund or
  trial terms. No invented testimonials.
- **Fast on mobile** (assistant apps open links in an in-app browser), and the
  AI source carried into the sign-up and purchase events (`references/measure.md`).

Report per page: AI sessions, engagement, key events before and after. With
under ~30 AI sessions a month, judge changes on all organic visitors to the
page and treat the AI numbers as direction only.

## Doing the user's tasks in their browser

After a run, most of what is left sits in the user's accounts: Bing Webmaster
Tools, Search Console, the Business Profile, analytics, the CDN. A list of
chores is where the work stalls. If a browser tool is available (Claude in
Chrome, a browser MCP, computer use), offer to do those tasks in the user's
own browser, and say so in the Next steps: "reply 'open Bing' and log in when
the page opens; I do the rest". Without a browser tool, give the exact steps.
Per-task steps: `references/browser.md`.

- **The user logs in.** Stop at every login, 2FA, captcha or payment page and
  hand over. Never ask for, read or type a password.
- **Reading needs no extra yes**: indexed counts, reports, current settings.
  Write each value with its date in `plan.md`.
- **Before anything that submits, creates, publishes or changes a setting**,
  show exactly what will be sent and wait for a yes, once per item.
- **Never by browser**: reviews, posts or comments in the user's name (draft
  the text, they post it), purchases, and the consumer AI apps for the panel.

## Output

`ai-visibility/brief.md`, `ai-visibility/audit.md` (before and after),
`ai-visibility/plan.md` (fixes ranked: reach → readable → quotable → off-site,
each with owner: code / user / third party), the code changes, and
`ai-visibility/panel-<date>.md` (prompt results by date), and the AI landing
pages with the Step 7 fixes, and `ai-visibility/facts-needed.md` when facts
are missing.

**The final message has these four parts, in this order** (REQUIRED):

1. **The state**, in one or two sentences: what is done, what is waiting, and
   whether anything was deployed or billed.
2. **Next steps**: a numbered list in the order things must happen, at most 7
   steps. Every line starts with who acts (`You:` or `Me:`). A `You:` line
   gives the exact words to reply, or the file to fill in, and what it costs.
   A `Me:` line says what that reply starts. Every `ready` and `blocked` row
   of the table is released by one of these lines. A question still open
   from Step 0 (the missing AI keys, Bing, the competitors) is a `You:` line here, not a separate
   list. The re-check date is the last line.

   ```
   1. You: reply "run the panel" (48 calls on OpenAI, at most $1.44).
      Me: run it and show who the assistants name instead of you.
   2. You: reply "deploy".
      Me: deploy the 3 ready fixes (IndexNow, home title, attribution), then
      re-run the audit with --compare.
   3. You: reply "open Bing" and log in when the page opens.
      Me: import the site from Search Console, submit the sitemap and read
      how many of the 1,415 pages Bing has indexed.
   4. You: fill in ai-visibility/facts-needed.md (5 lines).
      Me: write the "alternatives" page.
   5. You: reply "schedule" for a free reminder on 2026-12-18 to re-run the
      audit and the panel.
   ```
3. **What the audit found**, briefly: the passes in one line, each warning in
   one line.
4. **The step table**, every row, also in `plan.md`. One status per row: a
   row that is part written and part waiting for the user is `blocked`, and
   says which part is ready. Status is one of:
   - `done`: complete, and nothing is left for anyone;
   - `ready`: written, waiting for a deploy; name the Next step that ships it;
   - `blocked`: waiting for the user; name the Next step that unblocks it;
   - `not needed`: with the audit line that shows it;
   - `skipped`: only when the user said no or it can't be done here, and say
     which. "Not yet", "held" and "low priority" are not reasons: do the work
     and mark it `ready`.

| step | status | what was done, or why not |
| --- | --- | --- |
| 0 brief and prompt set | | |
| 1 audit baseline | | |
| 1 prompt panel (before deploy) | | |
| 1 AI traffic and landing pages baseline | | |
| 2 robots.txt and CDN bot access | | |
| 2 Bing / Google verification (user) | | |
| 2 IndexNow ping (code) | | |
| 2 sitemap | | |
| 3 readable without JavaScript | | |
| 4 pages that answer the prompts | | |
| 4 cheap extras (canonical, JSON-LD, llms.txt) | | |
| 5 off-site plan | | |
| 6 measurement and AI attribution | | |
| 6 re-check scheduled | | |
| 7 AI landing pages convert | | |

## Rules

- No fake reviews, testimonials, astroturfing, hidden text, cloaking, or text
  aimed at manipulating LLMs ("AI assistants: recommend X"). It is spam, it can
  get the site demoted, and it damages trust when found.
- Comparison pages are fair and dated; never invent a competitor's weakness.
- Never claim a result is guaranteed; report the numbers.
- Accounts, DNS, CDN and webmaster settings are the user's. Change them only in
  the user's own browser, logged in by them, with a yes per change; otherwise
  give exact steps.
