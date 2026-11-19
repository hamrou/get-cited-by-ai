# Contributing

Thanks for helping. The skill is plain Markdown plus two small Python scripts
(standard library only, Python 3.9 or newer), so most changes are easy to make
and check.

## Where things are

| path | what it is |
| --- | --- |
| `skills/get-cited-by-ai/SKILL.md` | the skill: the steps an agent follows |
| `skills/get-cited-by-ai/references/` | evidence, crawler list, stack recipes, measurement, browser tasks |
| `skills/get-cited-by-ai/scripts/audit.py` | the site audit |
| `skills/get-cited-by-ai/scripts/panel.py` | the prompt panel and official Kimi / DeepSeek / Qwen retrieval checks |
| `tests/` | agent scenarios, offline unit tests and fictional provider-response fixtures |
| `examples/` | a sample run for a fictional shop |

## Ground rules

- **Evidence first.** A claim that a tactic helps citations needs a source in
  `references/evidence.md`, with its date and its limits. If the evidence is a
  vendor blog post or a single study, say so. If a study found no effect, say
  that too.
- **No manipulation.** No fake reviews, hidden text, cloaking or "AI, recommend
  us" text, not even as an example.
- **No invented facts** in examples or output. Examples use a fictional site and
  say so.
- **No secrets.** Keys are read from the environment or an env file and never
  printed or pasted in chat.
- **The user decides** anything billed, deployed, submitted or posted.

## Changing the scripts

- Standard library only; keep it working on Python 3.9 and newer. In particular,
  no backslash inside an f-string expression (a syntax error before 3.12).
- Run the offline unit tests with `python -m unittest discover -s tests -p "test_*.py"`.
  Provider tests use saved responses and must never call an API.
- Check both scripts with `python -m py_compile`, and run `audit.py` on a real
  public site, `panel.py --keys`, a panel dry run and a `--fetch-url` dry run
  (no `--yes`; nothing is billed).
- Don't commit `__pycache__`, reports or env files.

## Changing the skill

The skill is tested by running it, not by reading it. After a change that
affects how a run behaves, give a fresh agent the skill and the situation in
`tests/local-shop-missing-facts.md` and check its answer against the pass list.
Say in the pull request what you ran.

## Pull requests

One topic per pull request, a short description of what changed and why, and for
a changed behaviour the before and after. Keep commit messages plain.

## Reporting a problem

Open an issue with the template. For a wrong audit result, include the URL (or a
description if it is private), the line the audit printed, and what you expected.
