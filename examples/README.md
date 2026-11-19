# Example output

What a run leaves in your project's `ai-visibility/` folder, for a **fictional**
shop ("Maison Lys", a natural beauty shop in Dakar). The shop, its site and all
numbers here are made up to show the shape of the files. Real runs write the
same files from your own site.

| file | step |
| --- | --- |
| [`brief.md`](ai-visibility/brief.md) | 0: who you are, the stack, the competitors |
| [`prompts.txt`](ai-visibility/prompts.txt) | 0: the buyers' questions, in their language |
| [`audit.md`](ai-visibility/audit.md) | 1: the baseline, from `audit.py` |
| [`plan.md`](ai-visibility/plan.md) | the ranked fixes and the step table |
| [`facts-needed.md`](ai-visibility/facts-needed.md) | 4: the facts only the owner has |
| [`final-message.md`](ai-visibility/final-message.md) | the last message of the run: state, next steps, findings |

Not shown: `panel-<date>.md`, which a real run writes after you approve the
billed prompt panel.
