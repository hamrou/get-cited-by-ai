# Evidence behind the priorities (checked 2026-11-18)

Re-check yearly: this field moves fast and most "GEO" posts are vendor marketing.

- **AI crawlers don't execute JavaScript**: Vercel + MERJ crawl analysis, "The
  rise of the AI crawler", https://vercel.com/blog/the-rise-of-the-ai-crawler
  (GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot fetch JS files but don't run
  them). Single large dataset, not independently replicated.
- **Citable writing**: Aggarwal et al., "GEO: Generative Engine Optimization",
  KDD 2024, https://arxiv.org/abs/2311.09735. Adding citations, quotations and
  statistics raised visibility up to ~40% in their benchmark, ~37% on live
  Perplexity; keyword stuffing did worse than baseline. Lab conditions.
- **Earned media bias**: Chen et al. 2025, https://arxiv.org/abs/2509.08919:
  AI search favours third-party (earned) sources over brand-owned pages.
- **Which sources get cited**: Peec AI, 30M citations (2026),
  https://peec.ai/blog/top-domains-cited-by-ai-search-analysis-based-on-30m-sources:
  Reddit, YouTube, LinkedIn, Wikipedia lead overall; ChatGPT leans on
  Wikipedia. Ahrefs (Dec 2025, 75k brands): YouTube mentions correlate most
  with AI visibility (correlation, not cause).
- **Schema**: Ahrefs controlled study (May 2026, 1,885 pages vs 4,000 controls):
  no measurable citation lift from adding JSON-LD. Summary:
  https://www.cmswire.com/digital-marketing/does-structured-data-actually-improve-answer-engine-citations/
  Google dropped FAQ rich results in May 2026.
- **llms.txt**: Ahrefs, May 2026: 97% of llms.txt files got zero requests;
  SE Ranking (~300k domains): no correlation with citations. Google: Search
  does not use it. https://ppc.land/llms-txt-adoption-rises-8-8x-but-97-of-files-get-zero-ai-requests/
  and https://www.optimizely.com/field-notes/articles/does-llms-txt-work/
- **Google's position**: no special requirements for AI Overviews / AI Mode;
  normal SEO applies; `nosnippet`/`max-snippet` limit AI use.
  https://developers.google.com/search/docs/appearance/ai-features
- **Bing AI Performance report** (public preview Feb 2026): Copilot / Bing AI
  citations per page and query, in Bing Webmaster Tools.
  https://www.searchinfluence.com/blog/bing-ai-performance-report-copilot-citations/
- **GA4 AI traffic**: ChatGPT desktop links carry `utm_source=chatgpt.com`;
  mobile apps often arrive as Direct.
  https://www.mo.agency/blog/how-to-track-ai-traffic-and-referrals-in-google-analytics-4
