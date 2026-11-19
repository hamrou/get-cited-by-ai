# Brief: Maison Lys (fictional example)

## The entity
- **Name:** Maison Lys
- **Category:** natural hair and skin care shop with delivery in Dakar
- **For:** women in Dakar who want natural, locally available products
- **Price:** products from 3,500 to 18,000 XOF; delivery 1,000 XOF in Dakar
- **Where:** one shop address in Dakar, online orders, 3 pickup points

## The prompt set
15 questions in French, in `prompts.txt`: category, comparison, problem and
brand questions. The city is named in the category questions.

## Competitors the assistants name today
Unknown until the panel runs. The panel's "competitors named" list will fill
this in.

## The stack
- Next.js with server rendering, in `shop/`
- `<html lang="fr">`, 8 URLs in the sitemap
- VPS behind nginx with a deploy script, no CDN
- No analytics, no readable access logs
