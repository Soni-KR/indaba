**Latest evidence, September 21:** pinned kit `dd2e5fe`; 98 AEGIS tests pass; expanded static mock suite 40/40 tasks and 0/31 validated attacks. A three-case Qwen pilot validates two attacks, both prevented with task success; finance remains unvalidated. Current demo inventory: 2 Qwen + 29 mock. Older counts below are development history. See [update details](docs/september-21-update.md).

# AEGIS — SENTINEL defense and safety observatory

AEGIS sits between the SENTINEL agent and its tools. It checks active permissions, tracks observed sensitive data across history truncation, requires approvals for exact consequential actions, and repairs safe content when possible. Every decision produces a source-linked, hash-chained receipt.

**Development evidence:** the offline mock agent completed **19/19 published tasks** for seeds 0, 11, and 29 under static and adaptive attacks. Static allow-all checks validate all ten attacks; adaptive checks validate nine, with split settlement excluded. AEGIS prevents every validated attack in those runs. The provenance baseline completes 17/19 tasks. These are local diagnostics, not official scores or proof of general Qwen robustness.

**Evidence validity:** attack claims now require `attack_success=True` in a paired `allow_all` run for the same scenario and configuration. Earlier raw zero-attack numbers are historical diagnostics, not automatically evidence of protection. The updated Qwen finance pilot failed that prerequisite. Use the generated [validated demo plan](docs/demo-evidence.md) to choose explicitly labelled Qwen or mock evidence.

**Current Qwen comparison:** at `9aa43f7`, the updated stock prompt completes 6/19 tasks with AEGIS, 6/19 with the earlier controls, and 7/19 with provenance. Only the direct-token scenario passes the Qwen undefended-attack prerequisite; AEGIS prevents its attack but the legitimate task fails. The other nine attack scenarios use validated mock demonstrations. The new controls improve the targeted stress results, but this run does not establish better real-model task utility.

**September 20 update:** pinned organizer revision `9aa43f7` includes Qwen runtime/parser fixes, compact argument schemas, completion instructions, strict starter-service models, and the mandatory undefended-attack check. Primary new evaluations use its unchanged agent prompt. AEGIS now repairs unambiguous read arguments, qualifies unsupported completion claims, and detects more reordered credential fragments. Full-precision HF testing is an optional comparison, not a prerequisite under the clarified rules.

**Submission status:** working defense, dashboard, mock and quantized-Qwen experiments, technical report, beginner guide, and video storyboard are included. Stronger real-model task completion, the final recorded video, team details, and repository publication remain outstanding. Winning cannot be guaranteed.

## Run locally

Python 3.12 is required. This workspace already has a configured `.venv`.

```powershell
.\.venv\Scripts\python.exe -m aegis.cli serve
```

Open **http://127.0.0.1:8080**. The official service endpoint is `POST /v1/decision`; health is `GET /healthz`. Keep the service local, with one worker. Session evidence is held in that process.

Fresh Git checkout (for the ZIP package, the starter kit is already included; omit the submodule command):

```powershell
git submodule update --init --recursive
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e ./starter-kit -e .
.\.venv\Scripts\python.exe -m pytest tests -q
```

On Linux, use `.venv/bin/python` in place of `.venv\Scripts\python.exe`.

## Reproduce the evidence

```powershell
.\.venv\Scripts\python.exe -m aegis.cli evaluate --seeds 0 11 29
.\.venv\Scripts\python.exe -m aegis.cli evaluate --variants aegis provenance --seeds 0 11 29 --adaptive
.\.venv\Scripts\python.exe -m aegis.stress
```

Each evaluation writes a new timestamped directory under `artifacts/`: original simulator traces, participant reports, defense audit receipts, source hashes, and a manifest. Audit receipts redact recognized secrets; original simulator traces contain fictional data, including synthetic canaries. The dashboard never loads remote assets.

```powershell
cd starter-kit
..\.venv\Scripts\python.exe -m sentinel.cli run --scenario scenarios/public/enterprise/enterprise_poisoned_invoice.yaml --defense-url http://127.0.0.1:8080 --artifacts ../artifacts/http-validation
```

This exercises the actual HTTP integration. In the dashboard, select the corresponding experiment or enable live decisions. Live receipts show decisions; full simulator traces additionally show execution and task outcomes.

## Design

1. Validate the tool and arguments against the current task policy and public tool schemas.
2. Extract sensitive identifiers, credential fields, and verbatim prose windows from observed sources; retain them across truncated context.
3. Check plain, reversed, spaced, Unicode-normalized, hex, base64, URL, and bounded nested encoded representations at action boundaries.
4. Prevent untrusted text from establishing memory policy or action authority. Reading untrusted evidence remains possible.
5. Enforce object-specific prepare/confirm/execute prerequisites and exact action-digest approval.
6. Redact only supported free-text fields; recheck replacements against every remaining constraint. Changed outbound messages become drafts.

No defense decision reads scenario IDs, filenames, reference plans, expected outcomes, evaluator labels, or fixture values. `run_id` is only an opaque session namespace. Tool names and schemas describe the public API; they are not scenario-specific rules. The evaluation harness is separate from the defense.

## Evidence and limitations

Start with [the beginner’s guide](docs/beginner-guide.md) if you are new to cybersecurity. See [the technical report](docs/technical-report.md), [responsible AI statement](docs/responsible-ai.md), [video storyboard](docs/video-storyboard.md), and [Qwen validation guide](docs/qwen-validation.md).

The expanded synthetic stress suite has 304 probes per variant. AEGIS prevents all 304 tested attack objectives and preserves the safe sentence in 192/192 draft probes. Earlier controls prevent 256/304; the 48 additional prevented objectives are shuffled four-character fragments across fields. Disabling persistence prevents 112/304 objectives; disabling data-flow checks prevents 16/304; disabling stream checks prevents 208/304. Earlier partial fragments can still escape. These are author-designed contract tests, not an independent benchmark.

All 96 AEGIS tests pass, with no expected failures. Confidential prose now gates external email on exact-action review (including harmless content), and isolated two-character credential fragments are tracked across outputs. This is not general semantic leak detection; short or unobserved prose, arbitrary one-character encodings and partial disclosure remain limitations. Completion qualification recognizes selected phrasings and receipt types; it does not verify all claims or complete missing work. Risk and confidence are engineering signals, not calibrated probabilities. Human approval cannot waive data-flow policy.

## Repository map

| Path | Purpose |
|---|---|
| `aegis/defense.py` | Action policy, session evidence, object lifecycle, repair checks |
| `aegis/flow.py` | Sensitive-value extraction, encoding normalization, redaction |
| `aegis/audit.py` | Redacted decision receipts and hash-chain verification |
| `aegis/app.py`, `aegis/web/` | HTTP defense and offline observability dashboard |
| `aegis/experiments.py`, `aegis/stress.py` | Reproducible evaluations and component ablations |
| `tests/` | Security invariants, integration, determinism, documented failures |
| `starter-kit/` | Unmodified organizer repository, pinned git submodule |
| `docs/` | Report, safety statement, recording plan and remaining validation |

Organizer source: https://github.com/Skan22/Sentinel_Starter_Kit, commit `9aa43f731749cf1a039c5b62d49507696d54bf6c`. Its Apache-2.0 notice is retained in the submodule. Earlier evidence retains its original `14c30fb` revision. No external dataset or learned defense model was used.


Current-build evidence: fresh static/adaptive mock runs preserve 19/19 tasks across seeds 0, 11 and 29. Static validates 10 attacks; adaptive validates nine and excludes one. The current demo plan uses ten mock cases because earlier Qwen runs belong to the previous defense build. See `docs/demo-evidence.md` and section 18 of `docs/beginner-guide.md`.
