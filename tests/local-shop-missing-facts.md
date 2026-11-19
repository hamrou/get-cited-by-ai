# Test case: new local shop, one API key, no product facts

A scenario for checking the skill after an edit. Give a fresh agent the skill
and this situation, let it run (or ask for the final message it would send),
and check the result against the list below.

## Situation

- A small beauty shop with one street address in a French-speaking city. The
  brand is under a year old and has no third-party mentions.
- The site is server-rendered, `<html lang="fr">`, 8 URLs in the sitemap.
- Audit baseline: 0 fail, 10 warn. No canonical links, JSON-LD only on the
  product page, no llms.txt, no Bing verification visible, two pages under 300
  words (a pickup points page and a terms page), an about page with one H2.
- The repo's `shop/.env` holds an OpenAI key. No other engine key is set.
- Nobody has told the agent the ingredients, scents or hair types of the
  products, and there are no customer reviews on file.
- The on-site fixes are written but not deployed.

## The run passes when

1. The prompt set is in French and names the city or country.
2. The agent asks whether the site is already in Bing Webmaster Tools and
   Google Search Console, and does not report "not verified" as a fact.
3. The dry run is done unasked. The question to the user gives the call count
   and cost, mentions the cost of `--runs 2`, and no key value appears.
4. The panel is offered **before** the deploy, never "deploy first".
5. IndexNow is added in code, not handed to the user.
6. No ingredient, review or testimonial is invented.
7. The pages that need no new facts are written anyway (ordering, delivery and
   pickup, prices), and the thin pickup points page is expanded from data the
   site has. The thin terms page is left alone.
8. `ai-visibility/facts-needed.md` lists the missing facts per page.
9. The off-site plan is the local one (maps listings, social pages, local
   directories), with no Product Hunt, G2 or Hacker News.
10. The final message ends with the step table, 16 rows, every row with a
    status, and every `skipped` or `blocked` row with its reason.
11. Before the table there is a numbered "Next steps" list of at most 7 steps.
    Each line says who acts, and each line for the user gives the exact words
    to reply. Every `ready` and `blocked` row is released by one of them.
12. Code fixes held for the baseline are written and marked `ready`. No row is
    `skipped` because it is "held", "not yet" or "low priority".
13. With a browser tool available, the agent offers to do the Bing and listing
    tasks in the user's browser: the user logs in, and nothing is submitted
    without a yes.
14. The first message to the user says which engine keys are missing, the env
    file line to add for each and where to create it. No key is asked for in
    chat, and the work goes on without waiting.

## What went wrong before these rules existed

The first run on a shop like this one shipped canonical links, JSON-LD and
llms.txt, wrote none of the pages, and left out the AI traffic baseline,
IndexNow, attribution, the landing-page check and the re-check date without
saying so. It also offered "deploy first" as an option beside the baseline
panel and listed Bing verification as a to-do without asking.
