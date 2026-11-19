# AI visibility audit: https://maisonlys.example

> Fictional example. The numbers are made up; the format is what `audit.py` writes.

**0 fail · 4 warn · 4 info · 18 pass** (6 pages checked)

## WARN
- **index**: no Bing Webmaster verification visible (meta msvalidate.01, /BingSiteAuth.xml or DNS). ChatGPT search and Copilot retrieve through Bing: verify the site at bing.com/webmasters (import from Google Search Console is quickest; a DNS CNAME verification is invisible to this check) and submit the sitemap
- **/points-de-retrait**: 212 words of text without JavaScript; a content page too thin for an answer engine to quote: expand it with facts the site already has
- **/notre-histoire**: fewer than 2 <h2> sections; answer engines lift passages section by section
- **/**: no canonical link

## INFO
- **llms.txt**: /llms.txt not found (HTTP 404). Optional: cheap to add, but few AI bots fetch it today
- **/conditions**: 140 words of text without JavaScript; a legal page, fine to leave short
- **index**: manual check: https://www.bing.com/search?q=site%3Amaisonlys.example and https://www.google.com/search?q=site%3Amaisonlys.example; compare the result count with the 8 sitemap URLs
- **/**: no JSON-LD (helps Google/Bing understand entities; no proven citation lift on its own)

## PASS
- **robots**: robots.txt allows the AI search, user and training bots checked
- **robots**: robots.txt advertises 1 sitemap(s)
- **sitemap**: 8 URLs in the sitemap(s)
- **/**: 449 words readable without JavaScript
- **/products/karite**: 380 words readable without JavaScript
