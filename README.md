# AEGIS — SENTINEL defense

AEGIS checks an agent's proposed actions against tool permissions, source trust, sensitive-data flow, exact approvals and workflow state. It can allow, block, rewrite or request review. It includes a local dashboard and reproducible evidence. No learned defense model or added agent safety prompt is used.

## Current evidence — 22 September 2026

| Check | Result | Scope |
|---|---|---|
| AEGIS pytest suite | 162 passed | No expected failures; two dependency warnings |
| Static mock, seeds 0/11/29 | 40/40 tasks; 0/31 validated attacks succeeded | Full public suite |
| Adaptive mock, seed 0 | 40/40 tasks; 0/30 validated attacks succeeded | One undefended attack fails, excluded |
| Adversarial contract audit | Two exposed cases; seven interventions; isolation check passes | Ten author-designed probes, not an LLM benchmark |
| Benign warning examples | 40/40 drafts allowed unchanged | Small targeted false-positive check |
| Earlier Qwen pilot, September 21 | Two validated attacks prevented, both tasks completed | Three-case pilot; finance unvalidated and task fails |

Two exposed diagnostic channels remain: labelled single-character fragments and multi-recipient collusion. Base32, ROT13 and the tested Unicode lookalikes now trigger intervention. The partial Unicode skeleton and bounded decoding do not guarantee protection against every representation. The 162 passing tests do not imply the remaining channels are protected. Semantic-paraphrase coverage is conservative external-email review, not semantic understanding. Human review is an additional dependency and can also interrupt harmless work.

Primary evidence: `artifacts/20260922T185242761643Z/manifest.json` (static), `artifacts/20260922T185313998546Z/manifest.json` (adaptive), and `artifacts/break-aegis-20260922.json`. Older evidence is historical. The later September 21 connection-failure run made no defense decisions and remains reported; it is not protection evidence.

## Try it

From the project root in PowerShell, use the existing environment:

```powershell
.\.venv\Scripts\python.exe -m aegis.cli serve
```

Open http://127.0.0.1:8080. The six-card trace summary shows source, sensitive item, attempted action, reason, enforcement and recorded task outcome. It starts at the first intervention. This is a replay of recorded evidence; new experiments run from the terminal:

```powershell
.\.venv\Scripts\python.exe -m aegis.cli evaluate --variants aegis provenance --seeds 0 11 29
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe scripts/break_aegis.py
```

The diagnostic script intentionally reports exposed cases; it does not claim success merely because execution exits normally. The evaluation harness pairs attacks with allow-all before crediting protection. The subsequent bounded encoding hardening is described in `docs/encoding-comparison.md`.

Ollama is currently unavailable here. The earlier Qwen traces used local Qwen3-8B Q4_K_M through llama.cpp. No September 22 real-model run or third validated Qwen case is claimed. All Qwen evidence predates the encoding change. The current demo inventory uses 31 validated mock cases; older Qwen traces remain historical, not current-build evidence.

## Reading and delivery

- [Technical report](docs/technical-report.md)
- [Beginner explanation](docs/beginner-guide.md)
- [September 22 audit](docs/september-22-review.md)
- [Demonstration inventory](docs/demo-evidence.md)
- [Recording storyboard](docs/video-storyboard.md)
- [Runtime setup and previous update](docs/september-21-update.md)

The pinned starter kit is `dd2e5fe0979d0781a4bfe6d0849cd80cf69ef4a2`, with unmodified upstream source. Its separately tested suite has 203 passes and three Windows-specific failures. Historical development counts are retained in the detailed guide and update notes, not presented as current results.

The organizer announcement sets the deadline to 23 September 2026, 23:59; its timezone was unspecified. Final video recording, team identification, repository publication and submission remain. No winning score or production readiness is claimed.
