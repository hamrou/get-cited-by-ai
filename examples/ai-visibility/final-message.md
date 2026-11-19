# The last message of a run (fictional example)

**The state.** The baseline audit, the brief, a 15-question prompt set and all
the code fixes are written and waiting. The "before" prompt panel, the deploy
and the account tasks wait for you. Nothing was deployed and nothing was billed.

**Next steps**

1. You: reply "run the panel" (30 calls on OpenAI, roughly $0.90; two runs per
   question is 60 calls, roughly $1.80, not a spending cap, and I recommend it).
   Me: run it before anything is deployed, and show how often the assistants
   name Maison Lys, who they name instead, and which sources they cite.
2. You: reply "deploy" (free).
   Me: deploy the 7 ready fixes, then re-run the audit with `--compare`.
3. You: reply "open Bing" and log in when the page opens.
   Me: read whether the site is listed and how many of the 8 pages Bing has
   indexed; if it is missing, show you the import from Search Console and the
   sitemap submission, and wait for your yes on each.
4. You: fill in `ai-visibility/facts-needed.md` (7 lines).
   Me: write the buying guides from those facts only.
5. You: reply "listings" (free; you press each submit button yourself).
   Me: fill in the Google Business Profile and Bing Places forms from the brief.
6. You: reply "schedule" for two free reminders: Bing's indexed count in two
   weeks, and the audit and panel re-run in six weeks.

**What the audit found** (6 pages: 0 fail, 4 warn, 18 pass)

- Passes: AI bots are allowed, every page has 380 to 449 words without
  JavaScript, the sitemap has 8 URLs.
- Warning: no Bing verification visible. This is a question, not a finding.
- Warnings: no canonical link, a thin pickup points page, one H2 on the
  history page. Fixes are written.

**The step table** is in [`plan.md`](plan.md).
