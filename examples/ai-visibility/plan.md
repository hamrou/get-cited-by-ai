# Plan: Maison Lys (fictional example)

Fixes ranked reach → readable → quotable → off-site. Owner: code (the agent),
user, or third party.

| # | fix | step | owner | status |
| --- | --- | --- | --- | --- |
| 1 | Run the baseline prompt panel before deploying | 1 | user approves, agent runs | blocked |
| 2 | Verify the site in Bing Webmaster Tools, submit the sitemap | 2 | user (or agent in the user's browser) | blocked |
| 3 | IndexNow key file and a ping of the changed URLs on deploy | 2 | code | ready |
| 4 | Canonical link on every page | 4 | code | ready |
| 5 | Expand `/points-de-retrait` from the 3 pickup points in the database | 4 | code | ready |
| 6 | Two H2 sections on `/notre-histoire` | 4 | code | ready |
| 7 | Pages that need no new facts: how to order, delivery, prices, contact | 4 | code | ready |
| 8 | Buying guides (which product for which hair type) | 4 | user supplies facts | blocked |
| 9 | Google Business Profile, Bing Places, Apple Business Connect | 5 | user | blocked |
| 10 | Facebook, Instagram and WhatsApp Business pages linked in `sameAs` | 5 | user | blocked |
| 11 | Ask real customers for reviews on those listings | 5 | user | blocked |
| 12 | AI source classifier and "How did you find us?" at checkout | 6 | code | ready |
| 13 | `llms.txt` and `Store` / `Product` JSON-LD from the live catalog | 4 | code | ready |

## Step table

| step | status | what was done, or why not |
| --- | --- | --- |
| 0 brief and prompt set | done | `brief.md`; 15 French prompts naming Dakar |
| 1 audit baseline | done | `audit.md`: 0 fail, 4 warn |
| 1 prompt panel (before deploy) | blocked | dry run done: 30 calls on OpenAI, at most $0.90 |
| 1 AI traffic and landing pages baseline | blocked | no analytics, access logs not readable |
| 2 robots.txt and CDN bot access | not needed | audit: all bots allowed, no CDN |
| 2 Bing / Google verification (user) | blocked | the audit can't see a DNS verification: asked |
| 2 IndexNow ping (code) | ready | key file and a ping of changed URLs |
| 2 sitemap | ready | per-page `lastmod` |
| 3 readable without JavaScript | not needed | audit: 380 to 449 words per page |
| 4 pages that answer the prompts | blocked | pages that need no new facts are ready; guides need `facts-needed.md` |
| 4 cheap extras (canonical, JSON-LD, llms.txt) | ready | written, not deployed |
| 5 off-site plan | blocked | listed above; the accounts are the user's |
| 6 measurement and AI attribution | ready | classifier and checkout question written |
| 6 re-check scheduled | blocked | waiting for the user's yes to reminder-only schedules |
| 7 AI landing pages convert | blocked | no AI visits recorded yet |
