# Making pages readable without JavaScript, by stack

Goal: every page in the prompt map returns its full text in the first HTML
response. Check with `audit.py` or `curl -A "OAI-SearchBot" URL | grep "a phrase"`.

| stack | fix |
| --- | --- |
| Next.js / Nuxt / SvelteKit / Astro / Remix | already SSR/SSG: make sure marketing pages are server components or statically generated, not `"use client"` + fetch-in-effect. Use the framework's metadata API, `sitemap.ts` / `robots.ts` (Next) or the equivalent module. |
| Vite / CRA SPA (React, Vue) | keep the app a SPA; add pre-rendering for public routes at build (vite-ssg, vite-plugin-prerender, Astro for the marketing site), **or** serve server-rendered landing pages from the backend beside the SPA and route them at the proxy (nginx `location` per path). Put the real headline + paragraph in `index.html` itself so the home page is never empty. |
| Express / Fastify / Django / Rails / Laravel | render HTML templates from JSON copy files per language (one template, many pages); generate sitemap and llms.txt from the same data so prices and counts stay live. |
| WordPress / Webflow / Shopify / Wix | already HTML; use the SEO plugin (Yoast, Rank Math) or platform settings for sitemap, schema and canonical; check the security plugin or CDN is not blocking AI bots. |
| Static site (Hugo, Jekyll, 11ty) | already fine; add sitemap lastmod from git dates and an IndexNow ping in the deploy step. |
| Mobile app only | the store listing is the page: title/subtitle with the category phrase, first lines answer "what is it", screenshots with captions. Add a one-page website with the facts, a FAQ and store links, because assistants cite web pages. |
| Local business | Google Business Profile, Bing Places, Apple Business Connect with identical name/address/phone/hours; a site with one page per service and per area, prices, and LocalBusiness JSON-LD. Reviews on the platforms assistants cite. |

## nginx: server-rendered pages beside a SPA

The SPA fallback (`try_files $uri /index.html`) answers every unknown path with
the empty shell, including `/llms.txt` and `/sitemap.xml` if they aren't
routed. Send the public pages to the server first:

```nginx
# exact pages and generated files → the app server
location ~ ^/(llms\.txt|sitemap[a-z-]*\.xml|robots\.txt|[0-9a-f]{32}\.txt)$ { proxy_pass http://app; }
location ~ "^/(fr|es|de)?/?(pricing|faq|features|alternatives|vs)(/.*)?$" { proxy_pass http://app; }
# everything else → the SPA
location / { try_files $uri /index.html; }
```

Regexes containing `{}` must be quoted. Run `nginx -t`, then add a test that
every sitemap URL returns server HTML (not the SPA shell), so a new page can't
silently fall through.

## Page set by project type

| type | pages that answer most prompts |
| --- | --- |
| SaaS / tool | home, features per job-to-be-done, pricing, "X vs <competitor>", "<competitor> alternatives", integrations, use cases per role/industry, docs/help, changelog, security/privacy |
| Game / app | home, how to play, is it free (pricing), FAQ, "games like <known title>", per mode/country/level guides, press kit, updates |
| E-commerce | category pages with buying guides, product pages with specs tables, comparison guides, shipping/returns FAQ |
| Local service | service × area pages, prices, FAQ, about/credentials, booking |
| Content / media / course | topic hubs, glossary, "how to" guides with steps, author pages with credentials |

## Local shop or small store

A shop with a street address, or a small online store selling in one city or
country. Assistants answer "where can I buy X in <city>" from maps listings,
social pages and local sites far more than from the shop's own pages.

**Off-site, in this order** (the user creates the accounts; you write the
exact name, category, description, hours and links to paste):

1. Google Business Profile, Bing Places, Apple Business Connect: identical
   name, address, phone and hours on all three and on the site. Bing Places
   feeds ChatGPT search and Copilot.
2. The social pages buyers in that market actually use (Facebook, Instagram,
   TikTok, a WhatsApp Business catalog): same name and one-liner, the site
   link, and every one of them in `sameAs`.
3. Local directories, marketplaces and classifieds for the country and the
   category. The panel's "most cited sources" list says which ones assistants
   read for these prompts.
4. Local press, bloggers and creators: one pitch with the facts (what, where,
   price, who is behind it). Paid coverage is disclosed.
5. Reviews on the platforms above, asked from real customers after a purchase.
   Never written by the shop.

**On-site**:

- Name, address, phone, hours, delivery areas and payment methods as text on
  the home page and a contact page, not only in an image or a map embed.
- `LocalBusiness` (or `Store`) JSON-LD with address, geo, phone, opening hours
  and `sameAs`; `Product` JSON-LD with price, currency and availability
  rendered from the live catalog.
- One page per pickup point or delivery area when there are several, each with
  its address, hours and how pickup works.
- Buying guides that answer the category prompts ("which X for Y"), each
  linking to the products, with prices in the local currency.
- Prompts and pages in the buyers' language, with the city and country named:
  "meilleur shampoing naturel à Libreville", "où acheter X au Gabon",
  "livraison X Libreville".

## IndexNow (Bing, Yandex, Seznam, Naver; Bing feeds ChatGPT search)

1. Generate a key (32 hex chars), serve it as `/<key>.txt` containing the key.
2. On deploy or publish, POST JSON to `https://api.indexnow.org/indexnow`:
   `{"host": "example.com", "key": "<key>", "keyLocation": "https://example.com/<key>.txt", "urlList": [...]}`
   (up to 10,000 URLs; send changed URLs, or all on a full deploy).
3. 200/202 = accepted. Don't ping unchanged URLs repeatedly.

## llms.txt (optional, cheap)

Plain Markdown at `/llms.txt` (never the SPA's HTML fallback): `# Name`, a
`> one-paragraph summary` with the category phrase and key facts (price, free
tier, platforms), then `## Sections` with links to the key pages and one line
each. Generate it from the same data as the pages.
