# AEGIS — SENTINEL defense

AEGIS checks an agent's proposed actions against tool permissions, source trust, sensitive-data flow, exact approvals and workflow state. It can allow, block, rewrite or request review. It includes a local dashboard and reproducible evidence. No learned defense model or added agent safety prompt is used.

**Team:** Mourad has lost a finger

**Members:** Mourad Kraiem, Mohamed Yassin ghaoui, Amine Fathallah

[Submission report (PDF)](docs/AEGIS-submission-report.pdf) | [Submission checklist](docs/submission-checklist.md) | [Video script](docs/video-storyboard.md)

## Current evidence — finalized 23 September 2026

| Check | Result | Scope |
|---|---|---|
| AEGIS pytest suite | 162 passed | No expected failures; two dependency warnings |
| Static mock, seeds 0/11/29 | 40/40 tasks; 0/31 validated attacks succeeded | Full public suite |
| Adaptive mock, seed 0 | 40/40 tasks; 0/30 validated attacks succeeded | One undefended attack fails, excluded |
| Adversarial contract audit | Two exposed cases; seven interventions; isolation check passes | Ten author-designed probes, not an LLM benchmark |
| Benign warning examples | 40/40 drafts allowed unchanged | Small targeted false-positive check |
| Earlier Qwen pilot, September 21 | Two validated attacks prevented, both tasks completed | Three-case pilot; finance unvalidated and task fails |

Two exposed diagnostic channels remain: labelled single-character fragments and multi-recipient collusion. Base32, ROT13 and the tested Unicode lookalikes now trigger intervention. The partial Unicode skeleton and bounded decoding do not guarantee protection against every representation. The 162 passing tests do not imply the remaining channels are protected. Semantic-paraphrase coverage is conservative external-email review, not semantic understanding. Human review is an additional dependency and can also interrupt harmless work.

Primary evidence: `artifacts/20260922T190222055363Z/manifest.json` (static), `artifacts/20260922T190233948131Z/manifest.json` (adaptive), and `artifacts/break-aegis-20260922.json`. Older evidence is historical. The later September 21 connection-failure run made no defense decisions and remains reported; it is not protection evidence.

Performance-only optimization reduced measured full-suite p95 from **134–196 ms to 18–44 ms**, with 845 identical recorded decision payloads and 1,440 differential text cases. [Performance review](docs/performance-review.md) explains scope and timing. The static action-level FBR remains **16/162 = 9.8765%**: [per-action analysis](docs/false-block-analysis.md). Eight clean-note blocks are genuine false positives despite full task completion.

## Install from a fresh clone

Use Python 3.12. The submodule contains the pinned official starter kit.

```powershell
git clone --recurse-submodules https://github.com/Soni-KR/indaba.git
cd indaba
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e ./starter-kit -e .
```

If already cloned, run `git submodule update --init --recursive`. These commands do not require activating a PowerShell script. No model download is required for mock evaluation. To regenerate the submission PDF, install `reportlab` in a document-tooling environment and run `python scripts/build_submission_pdf.py`; this is not a runtime defense dependency.

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

The organizer announcement sets the deadline to 23 September 2026, 23:59; its timezone was unspecified. Team identification and the report are complete locally. Final video recording, public repository access and manual submission remain; consult the submission checklist. No winning score or production readiness is claimed.
