#!/usr/bin/env python3
"""AI prompt panel: ask the same buyer questions to several answer engines
through their official APIs (web search on) and record whether your brand is
mentioned, linked, which competitors are named and which sources are cited.

Usage:
    python panel.py prompts.txt --brand "PetCred" --domain cred.pet \
        [--competitors "Rover,Wag"] [--engines openai,perplexity,anthropic,gemini] \
        [--runs 1] [--out ai-visibility/panel] [--yes]

prompts.txt: one prompt per line (blank lines and lines starting with # are skipped).
Keys come from the environment: OPENAI_API_KEY, PERPLEXITY_API_KEY,
ANTHROPIC_API_KEY, GEMINI_API_KEY (or GOOGLE_API_KEY). Engines without a key are
skipped. Without --yes it only prints the plan and a cost estimate (nothing is
billed). Models are overridable: OPENAI_MODEL, PERPLEXITY_MODEL,
ANTHROPIC_MODEL, GEMINI_MODEL.

API answers are a proxy for the consumer apps (different system prompts,
personalisation and search settings), so spot-check a few prompts by hand.
Stdlib only.
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
    # name: (key env vars, default model, est. USD per prompt incl. search)
    "openai": (("OPENAI_API_KEY",), "gpt-6.2-astra", 0.03),
    "perplexity": (("PERPLEXITY_API_KEY",), "sonar", 0.01),
    "anthropic": (("ANTHROPIC_API_KEY",), "claude-haiku-5-5", 0.04),
    "gemini": (("GEMINI_API_KEY", "GOOGLE_API_KEY"), "gemini-2.5-flash", 0.04),
}
BASE = {  # overridable for testing / proxies
    "openai": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com"),
    "perplexity": os.environ.get("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
    "anthropic": os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    "gemini": os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com"),
}


# Common short words per language: enough to tell which language a buyer
# question is written in, not a real language detector.
STOPWORDS = {
    "en": "the for is what how best where to of and which are does can with near buy my in",
    "fr": "le les des pour est quel quelle quels quelles comment meilleur meilleure où du une et sur avec acheter au aux pas mon dans",
    "es": "el los las para es qué cómo mejor dónde del una y cuál con comprar mi cerca en",
    "de": "der die das für ist was wie beste wo und ein eine welche mit kaufen mein im",
    "pt": "o os as para é qual como melhor onde do da um uma e com comprar meu em",
    "it": "il gli per è quale come migliore dove del della un una e con comprare mio in",
}
STOPWORDS = {k: set(v.split()) for k, v in STOPWORDS.items()}


def prompt_lang(prompt):
    """Best-guess language of one prompt, or None when it isn't clear."""
    words = re.findall(r"[^\W\d_]+", prompt.lower())
    hits = {lang: sum(w in sw for w in words) for lang, sw in STOPWORDS.items()}
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
    known = [l for l in langs if l]
    same = sum(l == lang for l in known)
    if len(known) >= 3 and same < len(known) / 2:
        top = Counter(known).most_common(1)[0][0]
        return (f"WARNING: the site is in '{lang}' but only {same} of {len(known)} prompts look like '{lang}' (most look like '{top}'). "
                f"Buyers ask in their own language: rewrite prompts.txt, or pass --lang {top} if the buyers really ask in '{top}'.")
    return None


def key_for(engine):
    for k in ENGINES[engine][0]:
        if os.environ.get(k):
            return os.environ[k]
    return None


def model_for(engine):
    return os.environ.get(f"{engine.upper()}_MODEL", ENGINES[engine][1])


def post(url, body, headers, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 502, 503, 529) and attempt < 2:
                time.sleep(5 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {detail}")
    raise RuntimeError("unreachable")


def walk_sources(obj, out):
    """Collect (url, title) pairs from any response shape: keys url/uri + title."""
    if isinstance(obj, dict):
        u = obj.get("url") or obj.get("uri")
        if isinstance(u, str) and u.startswith("http"):
            out.append((u, obj.get("title") or ""))
        for v in obj.values():
            walk_sources(v, out)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, str) and v.startswith("http"):
                out.append((v, ""))  # Perplexity's flat citations list
            else:
                walk_sources(v, out)
    return out


def ask(engine, prompt):
    k, m = key_for(engine), model_for(engine)
    if engine == "openai":
        r = post(f"{BASE[engine]}/v1/responses", {"model": m, "tools": [{"type": "web_search"}], "input": prompt},
                 {"Authorization": f"Bearer {k}"})
        text = "".join(c.get("text", "") for o in r.get("output", []) if o.get("type") == "message" for c in o.get("content", []))
        src = walk_sources([c.get("annotations", []) for o in r.get("output", []) if o.get("type") == "message" for c in o.get("content", [])], [])
    elif engine == "perplexity":
        r = post(f"{BASE[engine]}/chat/completions", {"model": m, "messages": [{"role": "user", "content": prompt}]},
                 {"Authorization": f"Bearer {k}"})
        text = (r.get("choices") or [{}])[0].get("message", {}).get("content", "")
        src = walk_sources(r.get("search_results") or r.get("citations") or [], [])
    elif engine == "anthropic":
        r = post(f"{BASE[engine]}/v1/messages", {
            "model": m, "max_tokens": 2048, "messages": [{"role": "user", "content": prompt}],
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}]},
            {"x-api-key": k, "anthropic-version": "2023-06-01"})
        blocks = r.get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        src = walk_sources([b.get("citations", []) for b in blocks if b.get("type") == "text"], [])
        if not src:  # answered from search results without inline citations
            src = walk_sources([b.get("content") for b in blocks if b.get("type") == "web_search_tool_result"], [])
    elif engine == "gemini":
        r = post(f"{BASE[engine]}/v1beta/models/{m}:generateContent",
                 {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}]},
                 {"x-goog-api-key": k})
        cand = (r.get("candidates") or [{}])[0]
        text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
        # groundingChunks carry a redirect URI; the title is the real domain.
        src = [(c["web"].get("uri", ""), c["web"].get("title", "")) for c in cand.get("groundingMetadata", {}).get("groundingChunks", []) if "web" in c]
    else:
        raise ValueError(engine)
    return text, src


def domain_of(url, title=""):
    host = urlparse(url).netloc.lower()
    if "vertexaisearch" in host or "grounding-api-redirect" in url:
        host = title.lower()  # Gemini: title holds the source domain
    return host[4:] if host.startswith("www.") else host


def score(text, sources, brand, domain, competitors):
    low = text.lower()
    names = [brand.lower()] + ([domain.lower()] if domain else [])
    mentioned = any(re.search(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", low) for n in names)
    doms = [domain_of(u, t) for u, t in sources]
    uniq = list(dict.fromkeys(d for d in doms if d))
    pos = next((i + 1 for i, d in enumerate(uniq) if domain and (d == domain or d.endswith("." + domain))), None)
    comps = [c for c in competitors if re.search(r"(?<![a-z0-9])" + re.escape(c.lower()) + r"(?![a-z0-9])", low)]
    return {"mentioned": mentioned, "linked": pos is not None, "position": pos, "competitors": comps, "sources": uniq}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompts")
    ap.add_argument("--brand", required=True)
    ap.add_argument("--domain", default="")
    ap.add_argument("--competitors", default="")
    ap.add_argument("--engines", default=",".join(ENGINES))
    ap.add_argument("--runs", type=int, default=1, help="repeat each prompt (answers vary run to run)")
    ap.add_argument("--out", default="panel")
    ap.add_argument("--yes", action="store_true", help="actually call the APIs (billed)")
    ap.add_argument("--env-file", action="append", default=[], help="read the API keys from a KEY=VALUE file such as the project's .env (only the 4 key names and model overrides are read; values are never printed)")
    ap.add_argument("--lang", default="", help="language the buyers ask in (fr, en, es…); default: the <html lang> of --domain's home page. Used only to warn when the prompts are in another language")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    allowed = {k for e in ENGINES.values() for k in e[0]} | {f"{n.upper()}_MODEL" for n in ENGINES}
    for path in a.env_file:
        try:
            for line in open(path, encoding="utf-8"):
                k, sep, v = line.strip().removeprefix("export ").partition("=")
                k = k.strip()
                if sep and k in allowed and not os.environ.get(k):
                    os.environ[k] = v.strip().strip('"').strip("'")
        except OSError as e:
            print(f"--env-file {path}: {e}")

    prompts = [l.strip() for l in open(a.prompts, encoding="utf-8") if l.strip() and not l.lstrip().startswith("#")]
    wanted = [e.strip() for e in a.engines.split(",") if e.strip()]
    unknown = [e for e in wanted if e not in ENGINES]
    if unknown:
        sys.exit(f"unknown engine(s): {', '.join(unknown)}; choose from {', '.join(ENGINES)}")
    engines = [e for e in wanted if key_for(e)]
    skipped = [e for e in wanted if e not in engines]
    competitors = [c.strip() for c in a.competitors.split(",") if c.strip()]
    calls = len(prompts) * len(engines) * a.runs
    cost = sum(ENGINES[e][2] for e in engines) * len(prompts) * a.runs
    print(f"{len(prompts)} prompts × {len(engines)} engines ({', '.join(f'{e}:{model_for(e)}' for e in engines) or 'none'}) × {a.runs} run(s) = {calls} calls, est. ≤ ${cost:.2f}")
    if skipped:
        print(f"skipped (no API key in env): {', '.join(skipped)}")
    if a.runs == 1 and engines:
        print(f"Answers vary from run to run: --runs 2 would be {calls * 2} calls, est. ≤ ${cost * 2:.2f}; --runs 3, {calls * 3} calls, est. ≤ ${cost * 3:.2f}.")
    warning = language_warning(prompts, (a.lang or (site_lang(a.domain) if a.domain else ""))[:2].lower())
    if warning:
        print(warning)
    if not a.yes or not engines:
        print("Dry run: nothing was called. Re-run with --yes to query the engines (billed to your keys).")
        return 0

    rows = []
    for p in prompts:
        for e in engines:
            for run in range(1, a.runs + 1):
                try:
                    text, src = ask(e, p)
                    s = score(text, src, a.brand, a.domain.lower(), competitors)
                    rows.append({"engine": e, "model": model_for(e), "prompt": p, "run": run, **s, "answer": text})
                    flag = "LINKED" if s["linked"] else "mentioned" if s["mentioned"] else "-"
                    print(f"[{e}] {flag:9} {p[:70]}")
                except Exception as ex:
                    rows.append({"engine": e, "model": model_for(e), "prompt": p, "run": run, "error": str(ex)})
                    print(f"[{e}] ERROR     {p[:50]}: {str(ex)[:120]}")

    today = dt.date.today().isoformat()
    ok = [r for r in rows if "error" not in r]
    lines = [f"# AI prompt panel: {a.brand} ({today})", "",
             "API answers with web search on; a proxy for the consumer apps.", "",
             "| engine | answers | mentioned | linked | avg position when linked |", "| --- | --- | --- | --- | --- |"]
    for e in engines + ["all"]:
        rs = [r for r in ok if e == "all" or r["engine"] == e]
        if not rs: continue
        pos = [r["position"] for r in rs if r["position"]]
        lines.append(f"| {e} | {len(rs)} | {sum(r['mentioned'] for r in rs)} ({100*sum(r['mentioned'] for r in rs)//len(rs)}%) | "
                     f"{sum(r['linked'] for r in rs)} ({100*sum(r['linked'] for r in rs)//len(rs)}%) | {sum(pos)/len(pos):.1f} |" if pos else
                     f"| {e} | {len(rs)} | {sum(r['mentioned'] for r in rs)} ({100*sum(r['mentioned'] for r in rs)//len(rs)}%) | 0 (0%) | – |")
    comp = Counter(c for r in ok for c in r["competitors"])
    if competitors:
        lines += ["", "## Competitors named", ""] + [f"- {c}: {comp.get(c, 0)} answers" for c in competitors]
    srcs = Counter(d for r in ok for d in set(r["sources"]))
    lines += ["", "## Most cited sources (your off-site target list)", ""] + [f"- {d}: {n}" for d, n in srcs.most_common(25)]
    lines += ["", "## Per prompt", "", "| prompt | engine | mentioned | linked | competitors |", "| --- | --- | --- | --- | --- |"]
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['prompt']} | {r['engine']} | error | | {r['error'][:60]} |")
        else:
            lines.append(f"| {r['prompt']} | {r['engine']} | {'yes' if r['mentioned'] else 'no'} | {r['position'] or 'no'} | {', '.join(r['competitors'])} |")
    if len(ok) < len(rows):
        lines += ["", f"{len(rows) - len(ok)} call(s) failed; check the model name (`<ENGINE>_MODEL`) and the key."]
    md = "\n".join(lines) + "\n"
    base = f"{a.out}-{today}"
    os.makedirs(os.path.dirname(base) or ".", exist_ok=True)
    open(base + ".md", "w", encoding="utf-8").write(md)
    json.dump(rows, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n" + md)
    print(f"Saved {base}.md and {base}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
