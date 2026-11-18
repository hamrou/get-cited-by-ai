# Doing the user's tasks in their browser

For when a browser tool is available (Claude in Chrome, a browser MCP, computer
use) and the user said yes. The rules are in SKILL.md: the user logs in,
reading is free, every change needs a yes, no posts or reviews in their name.

## How to work

- Open a new tab; leave the user's open tabs alone.
- Read the page before clicking. Menu names move, so find the control by what
  it does, not by the name given here.
- At a login, 2FA, captcha, payment or "verify it's you" page: stop, say what
  is on screen, and wait for the user to finish it.
- Before a change, show the exact values ("Submit sitemap
  https://example.com/sitemap.xml to Bing?") and wait for the yes.
- After two failed attempts at the same step, stop and give the manual steps.
- Write what you read or changed in `ai-visibility/plan.md`, with the date.

## Tasks

| task | where | read (no extra yes) | change (yes first) |
| --- | --- | --- | --- |
| Is the site indexed? | `bing.com/search?q=site:example.com`, same on Google; no login | result count against the sitemap count | |
| Bing Webmaster Tools | bing.com/webmasters | is the site listed, pages indexed, crawl errors, the AI Performance report | add the site by "Import from Google Search Console", submit the sitemap |
| Google Search Console | search.google.com/search-console | Pages report (indexed / not indexed and why), sitemap status | submit the sitemap, request indexing of the key pages |
| Google Business Profile | business.google.com | does a profile exist, its name, category, hours, reviews count | fill in name, category, address, phone, hours, description and site link from the brief; the user checks it and presses the final button. The verification code (post, phone, video) is theirs |
| Bing Places | bingplaces.com | does a listing exist | "Import from Google Business Profile" |
| Analytics (GA4, Plausible) | the user's property | AI-referred sessions and their landing pages (`references/measure.md`) | create the "AI assistants" channel group, create the site in Plausible, mark key events |
| CDN (Cloudflare) | the domain's dashboard | bot settings, AI Crawl Control, firewall events for AI user agents | allow the search and user bots |
| DNS | the registrar or DNS host | existing TXT / CNAME records | add the verification record, shown in full first |
| Directories | Product Hunt, AlternativeTo, the local ones in the plan | is the brand already listed | fill in the form from the brief; the user presses submit |

## Not by browser

- Reviews, ratings, upvotes: never.
- Reddit, forum, social and YouTube posts or comments: write the draft; the
  user posts it under their own name.
- Anything that costs money.
- ChatGPT, Perplexity, Gemini or Claude consumer apps for the prompt panel:
  the panel uses the APIs; manual spot checks are typed by the user.
