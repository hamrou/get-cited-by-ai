#!/usr/bin/env python3
"""AI prompt panel: ask buyer questions to answer engines through their official
APIs (web search on) and record mentions, links, competitors and cited sources.

Usage:
    python panel.py prompts.txt --brand "PetCred" --domain cred.pet \
        [--competitors "Rover,Wag"] [--engines openai,perplexity,anthropic,gemini,kimi,deepseek,qwen] \
        [--runs 1] [--out ai-visibility/panel] [--yes]
    python panel.py --keys [--env-file .env]     # which engines have a key (free)
    python panel.py --fetch-url https://example.com/page --engines kimi,deepseek,qwen [--yes]

prompts.txt: one prompt per line (blank lines and lines starting with # are skipped).
Keys come from the environment: OPENAI_API_KEY, PERPLEXITY_API_KEY,
ANTHROPIC_API_KEY, GEMINI_API_KEY (or GOOGLE_API_KEY), MOONSHOT_API_KEY,
DEEPSEEK_API_KEY and DASHSCOPE_API_KEY. Engines without a key are skipped.
Without --yes it only prints the plan and a rough cost estimate (nothing is
billed). Models are overridable: <ENGINE>_MODEL. Base URLs are overridable:
<ENGINE>_BASE_URL. QWEN_BASE_URL defaults to the China compatible-mode endpoint;
set the full compatible-mode base for another Model Studio region, including
any workspace ID, for example https://WORKSPACE.ap-southeast-1.maas.aliyuncs.com/compatible-mode.

API answers are a proxy for the consumer apps (different system prompts,
personalisation and search settings), so spot-check a few prompts by hand.
URL fetch checks use Kimi URL Fetch, DeepSeek URL reading and Qwen web extraction;
they are also billed only with --yes. Stdlib only.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from urllib.parse import urlparse

ENGINES = {
    # name: (key env vars, default model, rough USD per prompt incl. search)
    "openai": (("OPENAI_API_KEY",), "gpt-6.2-astra", 0.03),
    "perplexity": (("PERPLEXITY_API_KEY",), "sonar", 0.01),
    "anthropic": (("ANTHROPIC_API_KEY",), "claude-haiku-5-5", 0.04),
    "gemini": (("GEMINI_API_KEY", "GOOGLE_API_KEY"), "gemini-2.5-flash", 0.04),
    "kimi": (("MOONSHOT_API_KEY",), "kimi-k3.1-pro", 0.08),
    "deepseek": (("DEEPSEEK_API_KEY",), "deepseek-flash", 0.02),
    "qwen": (("DASHSCOPE_API_KEY",), "qwen4-max", 0.06),
}
FETCH_ENGINES = ("kimi", "deepseek", "qwen")
FETCH_COST = {"kimi": 0.002, "deepseek": 0.01, "qwen": 0.03}
KEY_PAGES = {
    "openai": "https://platform.openai.com/api-keys",
    "perplexity": "https://www.perplexity.ai/account/api",
    "anthropic": "https://console.anthropic.com/settings/keys",
    "gemini": "https://aistudio.google.com/apikey",
    "kimi": "https://platform.kimi.ai/console/api-keys",
    "deepseek": "https://platform.deepseek.com/api_keys",
    "qwen": "https://www.alibabacloud.com/help/model-studio/get-api-key",
}
BASE = {
    "openai": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com"),
    "perplexity": os.environ.get("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
    "anthropic": os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    "gemini": os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com"),
    "kimi": os.environ.get("KIMI_BASE_URL", os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.ai")),
    "deepseek": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    "qwen": os.environ.get("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode"),
}

STOPWORDS = {
    "en": "the for is what how best where to of and which are does can with near buy my in",
    "fr": "le les des pour est quel quelle quels quelles comment meilleur meilleure où du une et sur avec acheter au aux pas mon dans",
    "es": "el los las para es qué cómo mejor dónde del una y cuál con comprar mi cerca en",
    "de": "der die das für ist was wie beste wo und ein eine welche mit kaufen mein im",
    "pt": "o os as para é qual como melhor onde do da um uma e com comprar meu em",
    "it": "il gli per è quale come migliore dove del della un una e con comprare mio in",
    "zh": "",
}
STOPWORDS = {k: set(v.split()) for k, v in STOPWORDS.items()}


def prompt_lang(prompt):
    """Best-guess language of one prompt, or None when it isn't clear."""
    han = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", prompt))
    kana = len(re.findall(r"[\u3040-\u30ff]", prompt))
    latin_letters = len(re.findall(r"[A-Za-z]", prompt))
    if han >= 2 and not kana and han * 4 >= latin_letters:
        return "zh"
    words = re.findall(r"[^\W\d_]+", prompt.lower())
    hits = {lang: sum(w in sw for w in words) for lang, sw in STOPWORDS.items() if lang != "zh"}
    best = sorted(hits.items(), key=lambda kv: -kv[1])
    return best[0][0] if best[0][1] and best[0][1] > best[1][1] else None


def site_lang(domain):
    """The home page's <html lang>, two letters, or '' (one request, no key needed)."""
    try:
        req = urllib.request.Request(f"https://{domain}/", headers={"User-Agent": "Mozilla/5.0 (compatible; get-cited-by-ai-panel/1.0)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            m = re.search(r"<html[^>]*\blang=[\"']?([a-zA-Z]{2})", r.read(20000).decode("utf-8", "replace"))
            return m.group(1).lower() if m else ""
    except Exception:
        return ""


def language_warning(prompts, lang):
    if lang not in STOPWORDS:
        return None
    langs = [prompt_lang(p) for p in prompts]
    known = [lang_code for lang_code in langs if lang_code]
    same = sum(lang_code == lang for lang_code in known)
    if len(known) >= 3 and same < len(known) / 2:
        top = Counter(known).most_common(1)[0][0]
        return (f"WARNING: the site is in '{lang}' but only {same} of {len(known)} prompts look like '{lang}' (most look like '{top}'). "
                f"Buyers ask in their own language: rewrite prompts.txt, or pass --lang {top} if the buyers really ask in '{top}'.")
    return None


def key_for(engine):
    for key_name in ENGINES[engine][0]:
        if os.environ.get(key_name):
            return os.environ[key_name]
    return None


def model_for(engine):
    return os.environ.get(f"{engine.upper()}_MODEL", ENGINES[engine][1])


def ensure_api_success(response):
    if not isinstance(response, dict):
        raise RuntimeError("API returned a non-object response")
    error = response.get("error")
    if error:
        if isinstance(error, dict):
            message = error.get("message") or error.get("code") or str(error)
        else:
            message = str(error)
        raise RuntimeError(f"API error: {message[:300]}")
    if response.get("status") == "failed":
        raise RuntimeError("API response failed without an error message")


def post(url, body, headers, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8", "replace"))
                ensure_api_success(data)
                return data
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 502, 503, 529) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {detail}")
    raise RuntimeError("unreachable")


def walk_sources(obj, out):
    """Collect (url, title) pairs from response keys url/uri + title."""
    if isinstance(obj, dict):
        url = obj.get("url") or obj.get("uri")
        if isinstance(url, str) and url.startswith("http"):
            out.append((url, obj.get("title") or ""))
        for value in obj.values():
            walk_sources(value, out)
    elif isinstance(obj, list):
        for value in obj:
            if isinstance(value, str) and value.startswith("http"):
                out.append((value, ""))
            else:
                walk_sources(value, out)
    return out


def responses_result(response):
    """Parse an OpenAI-compatible Responses API answer and its inline citations."""
    ensure_api_success(response)
    output = response.get("output", [])
    text = "".join(c.get("text", "") for o in output if o.get("type") == "message" for c in o.get("content", []))
    sources = walk_sources([c.get("annotations", []) for o in output if o.get("type") == "message" for c in o.get("content", [])], [])
    return text, sources


def deepseek_message(response):
    ensure_api_success(response)
    return (response.get("choices") or [{}])[0].get("message", {})


def ask(engine, prompt):
    key, model = key_for(engine), model_for(engine)
    if engine == "openai":
        response = post(f"{BASE[engine]}/v1/responses", {"model": model, "tools": [{"type": "web_search"}], "input": prompt},
                        {"Authorization": f"Bearer {key}"})
        text, sources = responses_result(response)
    elif engine == "kimi":
        response = post(f"{BASE[engine]}/v1/responses", {"model": model, "tools": [{"type": "web_search"}], "input": prompt},
                        {"Authorization": f"Bearer {key}"})
        text, sources = responses_result(response)
    elif engine == "qwen":
        response = post(f"{BASE[engine]}/v1/responses", {
            "model": model, "input": prompt,
            "tools": [{"type": "web_search"}, {"type": "web_extractor"}],
            "enable_thinking": True,
        }, {"Authorization": f"Bearer {key}"})
        text, sources = responses_result(response)
    elif engine == "perplexity":
        response = post(f"{BASE[engine]}/chat/completions", {"model": model, "messages": [{"role": "user", "content": prompt}]},
                        {"Authorization": f"Bearer {key}"})
        text = (response.get("choices") or [{}])[0].get("message", {}).get("content", "")
        sources = walk_sources(response.get("search_results") or response.get("citations") or [], [])
    elif engine == "deepseek":
        response = post(f"{BASE[engine]}/chat/completions", {
            "model": model, "messages": [{"role": "user", "content": prompt}],
            "tools": [{"type": "deepseek_web_search"}], "thinking": {"type": "disabled"}, "stream": False,
        }, {"Authorization": f"Bearer {key}"})
        message = deepseek_message(response)
        text = message.get("content", "")
        sources = []
        for annotation in message.get("annotations", []):
            citation = annotation.get("url_citation", {})
            if citation.get("url"):
                sources.append((citation["url"], citation.get("title") or ""))
    elif engine == "anthropic":
        response = post(f"{BASE[engine]}/v1/messages", {
            "model": model, "max_tokens": 2048, "messages": [{"role": "user", "content": prompt}],
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        }, {"x-api-key": key, "anthropic-version": "2023-06-01"})
        blocks = response.get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        sources = walk_sources([b.get("citations", []) for b in blocks if b.get("type") == "text"], [])
        if not sources:
            sources = walk_sources([b.get("content") for b in blocks if b.get("type") == "web_search_tool_result"], [])
    elif engine == "gemini":
        response = post(f"{BASE[engine]}/v1beta/models/{model}:generateContent",
                        {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}]},
                        {"x-goog-api-key": key})
        candidate = (response.get("candidates") or [{}])[0]
        text = "".join(p.get("text", "") for p in candidate.get("content", {}).get("parts", []))
        sources = [(c["web"].get("uri", ""), c["web"].get("title", "")) for c in candidate.get("groundingMetadata", {}).get("groundingChunks", []) if "web" in c]
    else:
        raise ValueError(engine)
    return text, sources


def fetch_page(engine, url):
    """Fetch one public URL through the provider's official retrieval API."""
    key, model = key_for(engine), model_for(engine)
    if engine == "kimi":
        response = post(f"{BASE[engine]}/v1/tools/fetch", {"url": url}, {"Authorization": f"Bearer {key}"})
        markdown = response.get("markdown") or ""
        return {"engine": engine, "url": url, "retrieved": bool(markdown.strip()),
                "title": response.get("title") or "", "characters": len(markdown),
                "preview": markdown[:500], "answer": ""}
    if engine == "deepseek":
        response = post(f"{BASE[engine]}/chat/completions", {
            "model": model,
            "messages": [{"role": "user", "content": f"Read this exact public page and summarize its main answer. If it cannot be read, say so: {url}"}],
            "tools": [{"type": "deepseek_read_url"}], "thinking": {"type": "disabled"}, "stream": False,
        }, {"Authorization": f"Bearer {key}"})
        message = deepseek_message(response)
        calls = [call for step in message.get("server_tool_calls", []) for call in step.get("calls", [])
                 if call.get("type") == "deepseek_read_url"]
        completed = next((call for call in calls if call.get("status") == "completed" and call.get("page")), None)
        page = (completed or {}).get("page") or {}
        failed = next((call for call in calls if call.get("error")), {})
        answer = message.get("content", "")
        error = "" if completed else ("No URL-reading call was returned" if not calls else "URL reading did not complete")
        return {"engine": engine, "url": url, "retrieved": completed is not None,
                "title": page.get("title") or "", "characters": len(answer),
                "preview": answer[:500], "answer": answer,
                "error": error, "detail": (failed.get("error") or {}) if failed else {}}
    if engine == "qwen":
        response = post(f"{BASE[engine]}/v1/responses", {
            "model": model,
            "input": f"Visit this exact public URL and summarize its main answer. If it cannot be read, say so: {url}",
            "tools": [{"type": "web_search"}, {"type": "web_extractor"}],
            "enable_thinking": True,
        }, {"Authorization": f"Bearer {key}"})
        output = response.get("output", [])
        calls = [item for item in output if item.get("type") == "web_extractor_call"]
        completed = next((item for item in calls if item.get("status", "completed") == "completed" and (item.get("output") or item.get("content"))), None)
        extracted = (completed or {}).get("output") or (completed or {}).get("content") or ""
        if not isinstance(extracted, str):
            extracted = json.dumps(extracted, ensure_ascii=False)
        answer, _ = responses_result(response)
        error = "" if completed else ("No web-extractor call was returned" if not calls else "Web extraction did not complete")
        return {"engine": engine, "url": url, "retrieved": completed is not None,
                "title": "", "characters": len(extracted), "preview": extracted[:500], "answer": answer,
                "error": error, "detail": {}}
    raise ValueError(f"URL retrieval supports: {', '.join(FETCH_ENGINES)}")


def domain_of(url, title=""):
    host = urlparse(url).netloc.lower()
    if "vertexaisearch" in host or "grounding-api-redirect" in url:
        host = title.lower()
    return host[4:] if host.startswith("www.") else host


def score(text, sources, brand, domain, competitors):
    low = text.lower()
    names = [brand.lower()] + ([domain.lower()] if domain else [])
    mentioned = any(re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", low) for name in names)
    domains = [domain_of(url, title) for url, title in sources]
    unique = list(dict.fromkeys(domain for domain in domains if domain))
    position = next((i + 1 for i, source_domain in enumerate(unique) if domain and (source_domain == domain or source_domain.endswith("." + domain))), None)
    comps = [c for c in competitors if re.search(r"(?<![a-z0-9])" + re.escape(c.lower()) + r"(?![a-z0-9])", low)]
    return {"mentioned": mentioned, "linked": position is not None, "position": position, "competitors": comps, "sources": unique}


def md_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def save_rows(base, md, rows):
    os.makedirs(os.path.dirname(base) or ".", exist_ok=True)
    with open(base + ".md", "w", encoding="utf-8") as handle:
        handle.write(md)
    with open(base + ".json", "w", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=1)
    print("\n" + md)
    print(f"Saved {base}.md and {base}.json")


def retrieval_report(rows, base):
    today = dt.date.today().isoformat()
    lines = [f"# Official AI URL-retrieval check ({today})", "",
             "Kimi URL Fetch, DeepSeek URL reading and Qwen web extraction. These API checks are proxies for the consumer apps.", "",
             "| URL | engine | retrieved | characters | title / error |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        status = "yes" if row.get("retrieved") else "no"
        detail = row.get("error") or row.get("title") or (row.get("detail", {}).get("message") if row.get("detail") else "") or ""
        lines.append(f"| {md_cell(row['url'])} | {row['engine']} | {status} | {row.get('characters', 0)} | {md_cell(detail)} |")
    lines += ["", "Retrieval does not imply indexing or citation. Inspect the JSON previews and repeat after fixing access or rendering problems."]
    save_rows(base, "\n".join(lines) + "\n", rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompts", nargs="?")
    parser.add_argument("--brand", default="")
    parser.add_argument("--keys", action="store_true", help="only list which engines have an API key and where to get the missing ones (no call, no cost, values never printed)")
    parser.add_argument("--domain", default="")
    parser.add_argument("--competitors", default="")
    parser.add_argument("--engines", default="", help="comma-separated engines; default: all panel engines, or kimi,deepseek,qwen with --fetch-url")
    parser.add_argument("--runs", type=int, default=1, help="repeat each prompt (answers vary run to run)")
    parser.add_argument("--out", help="output prefix; default: panel, or retrieval with --fetch-url")
    parser.add_argument("--yes", action="store_true", help="actually call the APIs (billed)")
    parser.add_argument("--env-file", action="append", default=[], help="read API keys from KEY=VALUE files (only recognized key and model names are read; values are never printed)")
    parser.add_argument("--lang", default="", help="language the buyers ask in (zh, fr, en, es…); default: the <html lang> of --domain's home page")
    parser.add_argument("--fetch-url", action="append", default=[], help="test a public URL through Kimi, DeepSeek and Qwen retrieval APIs; repeatable; billed only with --yes")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    allowed = {key for engine in ENGINES.values() for key in engine[0]} | {f"{name.upper()}_MODEL" for name in ENGINES}
    for path in args.env_file:
        try:
            with open(path, encoding="utf-8") as handle:
                for line in handle:
                    key, sep, value = line.strip().removeprefix("export ").partition("=")
                    key = key.strip()
                    if sep and key in allowed and not os.environ.get(key):
                        os.environ[key] = value.strip().strip('"').strip("'")
        except OSError as e:
            print(f"--env-file {path}: {e}")

    if args.keys:
        have = [engine for engine in ENGINES if key_for(engine)]
        print(f"Keys found: {', '.join(have) or 'none'}")
        for engine in ENGINES:
            if engine not in have:
                print(f"Missing: {engine}. Add {ENGINES[engine][0][0]}=<key> to the project's env file (create the key at {KEY_PAGES[engine]}); roughly ${ENGINES[engine][2]:.3f} per question")
        if len(have) < len(ENGINES):
            print("Never paste a key in chat, and keep the env file out of git.")
        return 0
    if not args.fetch_url and (not args.prompts or not args.brand):
        parser.error("prompts and --brand are required (or use --keys or --fetch-url)")
    if args.runs < 1:
        parser.error("--runs must be at least 1")

    prompts = []
    if args.prompts:
        with open(args.prompts, encoding="utf-8") as handle:
            prompts = [line.strip() for line in handle if line.strip() and not line.lstrip().startswith("#")]
    default_engines = FETCH_ENGINES if args.fetch_url else list(ENGINES)
    wanted = [engine.strip() for engine in args.engines.split(",") if engine.strip()] or default_engines
    unknown = [engine for engine in wanted if engine not in ENGINES]
    if unknown:
        sys.exit(f"unknown engine(s): {', '.join(unknown)}; choose from {', '.join(ENGINES)}")
    if args.fetch_url:
        unsupported = [engine for engine in wanted if engine not in FETCH_ENGINES]
        if unsupported:
            sys.exit(f"--fetch-url supports {', '.join(FETCH_ENGINES)} only; unsupported: {', '.join(unsupported)}")
    engines = [engine for engine in wanted if key_for(engine)]
    skipped = [engine for engine in wanted if engine not in engines]
    if skipped:
        print(f"skipped (no API key in env): {', '.join(skipped)}")

    if args.fetch_url:
        calls = len(args.fetch_url) * len(engines)
        cost = sum(FETCH_COST[engine] for engine in engines) * len(args.fetch_url)
        print(f"{len(args.fetch_url)} URL(s) × {len(engines)} engines ({', '.join(f'{engine}:{model_for(engine)}' for engine in engines) or 'none'}) = {calls} retrieval request(s), rough est. ${cost:.2f} (not a spending cap)")
        if not args.yes or not engines:
            print("Dry run: nothing was called. Re-run with --yes to query the retrieval APIs (billed to your keys).")
            return 0
        rows = []
        for url in args.fetch_url:
            for engine in engines:
                try:
                    row = fetch_page(engine, url)
                    rows.append(row)
                    print(f"[{engine}] {'RETRIEVED' if row['retrieved'] else 'NOT READ':9} {url}")
                except Exception as ex:
                    rows.append({"engine": engine, "url": url, "retrieved": False, "characters": 0, "error": str(ex)})
                    print(f"[{engine}] ERROR     {url}: {str(ex)[:120]}")
        retrieval_report(rows, f"{args.out or 'retrieval'}-{dt.date.today().isoformat()}")
        return 0

    competitors = [competitor.strip() for competitor in args.competitors.split(",") if competitor.strip()]
    calls = len(prompts) * len(engines) * args.runs
    cost = sum(ENGINES[engine][2] for engine in engines) * len(prompts) * args.runs
    print(f"{len(prompts)} prompts × {len(engines)} engines ({', '.join(f'{engine}:{model_for(engine)}' for engine in engines) or 'none'}) × {args.runs} run(s) = {calls} model call(s), rough est. ${cost:.2f} (not a spending cap; search and token use vary)")
    if args.runs == 1 and engines:
        print(f"Answers vary from run to run: --runs 2 would be {calls * 2} calls, rough est. ${cost * 2:.2f}; --runs 3, {calls * 3} calls, rough est. ${cost * 3:.2f}.")
    warning = language_warning(prompts, (args.lang or (site_lang(args.domain) if args.domain else ""))[:2].lower())
    if warning:
        print(warning)
    if not args.yes or not engines:
        print("Dry run: nothing was called. Re-run with --yes to query the engines (billed to your keys).")
        return 0

    rows = []
    for prompt in prompts:
        for engine in engines:
            for run in range(1, args.runs + 1):
                try:
                    text, sources = ask(engine, prompt)
                    scored = score(text, sources, args.brand, args.domain.lower(), competitors)
                    rows.append({"engine": engine, "model": model_for(engine), "prompt": prompt, "run": run, **scored, "answer": text})
                    flag = "LINKED" if scored["linked"] else "mentioned" if scored["mentioned"] else "-"
                    print(f"[{engine}] {flag:9} {prompt[:70]}")
                except Exception as ex:
                    rows.append({"engine": engine, "model": model_for(engine), "prompt": prompt, "run": run, "error": str(ex)})
                    print(f"[{engine}] ERROR     {prompt[:50]}: {str(ex)[:120]}")

    today = dt.date.today().isoformat()
    ok = [row for row in rows if "error" not in row]
    lines = [f"# AI prompt panel: {args.brand} ({today})", "",
             "API answers with web search on; a proxy for the consumer apps.", "",
             "| engine | answers | mentioned | linked | avg position when linked |", "| --- | --- | --- | --- | --- |"]
    for engine in engines + ["all"]:
        selected = [row for row in ok if engine == "all" or row["engine"] == engine]
        if not selected:
            continue
        positions = [row["position"] for row in selected if row["position"]]
        mentioned = sum(row["mentioned"] for row in selected)
        linked = sum(row["linked"] for row in selected)
        average = f"{sum(positions)/len(positions):.1f}" if positions else "–"
        lines.append(f"| {engine} | {len(selected)} | {mentioned} ({100*mentioned//len(selected)}%) | {linked} ({100*linked//len(selected)}%) | {average} |")
    competitor_counts = Counter(competitor for row in ok for competitor in row["competitors"])
    if competitors:
        lines += ["", "## Competitors named", ""] + [f"- {competitor}: {competitor_counts.get(competitor, 0)} answers" for competitor in competitors]
    source_counts = Counter(domain for row in ok for domain in set(row["sources"]))
    lines += ["", "## Most cited sources (your off-site target list)", ""] + [f"- {domain}: {count}" for domain, count in source_counts.most_common(25)]
    lines += ["", "## Per prompt", "", "| prompt | engine | mentioned | linked | competitors |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        if "error" in row:
            lines.append(f"| {md_cell(row['prompt'])} | {row['engine']} | error | | {md_cell(row['error'][:60])} |")
        else:
            lines.append(f"| {md_cell(row['prompt'])} | {row['engine']} | {'yes' if row['mentioned'] else 'no'} | {row['position'] or 'no'} | {md_cell(', '.join(row['competitors']))} |")
    if len(ok) < len(rows):
        lines += ["", f"{len(rows) - len(ok)} call(s) failed; check the model name (`<ENGINE>_MODEL`), region endpoint and the key."]
    save_rows(f"{args.out or 'panel'}-{today}", "\n".join(lines) + "\n", rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
