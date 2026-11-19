"""Build plugin-lite/: the skill without scripts, for the Anthropic directory.

The directory accepts only text, JSON, YAML and images from unverified
organizations, so audit.py and panel.py cannot ship there. This copies the
skill's Markdown, swaps the steps that call the scripts for manual ones, and
fails loudly if the full skill changed in a way a swap no longer matches.

    python tools/build_lite.py
"""
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "skills" / "get-cited-by-ai"
OUT = ROOT / "plugin-lite"


def read(p):
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def between(s, start, end, new):
    a, b = s.index(start), s.index(end)
    assert a < b, (start, end)
    return s[:a] + new + s[b:]


def sub(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:60])
    return s.replace(old, new)


AUDIT = """This edition has no scripts, so the audit is done by hand on the public pages
(`curl`, or your fetch tool):

- `/robots.txt`: which AI bots are allowed (list in `references/crawlers.md`).
  Apply the rules per page path, with `*` and `$` patterns, the longest match
  winning and Allow winning a tie.
- `curl -A "OAI-SearchBot" URL` (and ClaudeBot, PerplexityBot, GPTBot): a 403 or
  a challenge page means a firewall blocks the bot.
- The words readable **without JavaScript**: fetch the raw HTML and count the
  words outside `<script>`. Under about 80 on a content page is a FAIL.
- Title, one h1, h2s, canonical, hreflang, Open Graph, JSON-LD, the sitemap and
  its `lastmod`, and `/llms.txt`.

Check the home page and 4 to 5 sitemap pages, or the URLs the user names. After
the fixes are live, check the same pages again and list what was fixed, what is
new and what remains; a page that failed to load is "not re-checked", never
"fixed".

"""

KEYS = """**The prompt check is manual in this edition.** There is no script to call the
assistants' APIs. Ask the user to run the prompt set in the consumer apps their
buyers use (search on), including Kimi, DeepSeek and Qwen for a Chinese-speaking
audience, and paste the answers. Never automate logged-in consumer sessions, and
never ask for an API key in chat.

"""

BASELINE = """1. Audit the live site by hand (see the top of this file) and save the report.
   Whether Bing/Google verification is visible is a question for the user, not a
   finding.
2. **The prompt check**: write the prompt set to `ai-visibility/prompts.txt`
   (one per line). Ask the user to run 10 to 15 of them in the consumer apps
   their buyers use, twice each (answers vary), and paste the answers. Count how
   often the brand is named and linked, which competitors are named, and which
   sources are cited. Save it as `ai-visibility/panel-<date>.md`. API answers
   and consumer apps differ, and a hand count is a rough signal: say so.
3. **Chinese AI assistants**: when Kimi, DeepSeek or Qwen matters, run the
   important pages through each app by hand ("summarize this page") and note
   whether the page is read and what is extracted. Do not invent crawler user
   agents or assume Bing/Google/Baidu supplies these engines. Success does not
   prove indexing or citation. See `references/crawlers.md`.
"""


def lite_skill():
    s = read(SRC / "SKILL.md")
    s = sub(s, "official Kimi/DeepSeek/Qwen retrieval checks, ", "")
    s = between(s, "Audit tool in this folder", "## What the evidence says", AUDIT)
    s = between(s, "**Ask for the AI keys first.**", "Write `ai-visibility/brief.md`:", KEYS)
    s = between(s, "1. Run `audit.py` on the live site", "4. Note current AI referral traffic", BASELINE)
    s = sub(s, "the missing AI keys, Bing, the competitors", "Bing, the competitors")
    s = sub(s, 'reply "run the panel" (48 calls on OpenAI, roughly $1.44, not a cap).\n      Me: run it and show who the assistants name instead of you.',
            'reply "prompts done" after pasting the assistants\' answers to 10 prompts.\n      Me: count who they name instead of you and which sources they cite.')
    s = sub(s, "re-run the audit with --compare.", "check the same pages again.")
    s = sub(s, "| 1 prompt panel (before deploy) | | |", "| 1 prompt check by hand (before deploy) | | |")
    s = sub(s, "| 1 official retrieval baseline (when Kimi / DeepSeek / Qwen is relevant) | | |\n", "")
    s = sub(s, "and run the billed panel locally in a\nsession when the reminder comes. Never put an API key in a scheduled prompt.",
            "and do the manual prompt check\nwhen the reminder comes. Never put an API key in a scheduled prompt.")
    s = re.sub(r"\n`ai-visibility/retrieval-<date>\.md` when official Kimi/DeepSeek/Qwen retrieval\nchecks are relevant, ", "\n", s)
    assert not re.search(r"audit\.py|panel\.py|--keys|--yes|--fetch-url|KIMI_SKILL_DIR|<this skill's folder>", s)
    return s


def lite_refs():
    c = read(SRC / "references" / "crawlers.md")
    c = between(c, "```bash\npython \"<this skill's folder>/scripts/panel.py\"", "Kimi URL Fetch returns",
                "Ask each assistant by hand to read the page and note what it extracts.\n\n")
    m = read(SRC / "references" / "measure.md")
    m = between(m, "For Kimi, DeepSeek and Qwen, also run the official URL-retrieval check", "Save `retrieval-<date>.md/.json`",
                "For Kimi, DeepSeek and Qwen, also ask each app by hand to read the\nimportant pages. ")
    m = sub(m, "Save `retrieval-<date>.md/.json` beside the panel.", "Save the notes beside the prompt check.")
    st = read(SRC / "references" / "stacks.md")
    st = sub(st, "Check with `audit.py` or `curl", "Check with `curl")
    return {"crawlers.md": c, "measure.md": m, "stacks.md": st}


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    skill_out = OUT / "skills" / "get-cited-by-ai"
    (skill_out / "references").mkdir(parents=True)
    (skill_out / "SKILL.md").write_text(lite_skill(), encoding="utf-8", newline="\n")
    patched = lite_refs()
    for f in (SRC / "references").glob("*.md"):
        text = patched.get(f.name, read(f))
        (skill_out / "references" / f.name).write_text(text, encoding="utf-8", newline="\n")
    meta = json.loads(read(ROOT / ".claude-plugin" / "plugin.json"))
    meta["description"] = meta["description"].replace("AI-crawler audit, official retrieval checks, and fixes", "AI-crawler audit, prompt checks and fixes")
    (OUT / ".claude-plugin").mkdir()
    (OUT / ".claude-plugin" / "plugin.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for name in ("LICENSE",):
        if (ROOT / name).exists():
            shutil.copyfile(ROOT / name, OUT / name)
    print("built", OUT)


if __name__ == "__main__":
    main()
