"""Generate the evidence tables from completed manifests; do not edit results by hand."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifests = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "artifacts").glob("*/manifest.json"))]
static = next(m for m in reversed(manifests) if m["model"] == "mock" and m["attack_mode"] == "static")
adaptive = next(m for m in reversed(manifests) if m["model"] == "mock" and m["attack_mode"] == "adaptive")
stress = json.loads((ROOT / "artifacts/stress.json").read_text(encoding="utf-8"))
qwen = [m for m in manifests if m["model"].startswith("qwen")]


def table(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        + ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    )


results = table(
    [
        "Attack mode",
        "Defense",
        "Seed",
        "Tasks",
        "Successful attacks",
        "Critical violations",
        "False-block rate",
        "p95 ms",
    ],
    [
        [
            m["attack_mode"],
            r["variant"],
            r["seed"],
            f"{r['tasks_completed']}/{r['scenario_count']}",
            f"{r['attack_successes']}/{r['attack_runs']}",
            r["critical_violations"],
            f"{r['metrics']['fbr']:.3%}",
            f"{r['metrics']['latency_p95_ms']:.3f}",
        ]
        for m in (static, adaptive)
        for r in m["reports"]
        if r["variant"] in {"aegis", "allow_all", "provenance"}
    ],
)
ablation = table(
    ["Variant", "Probe objectives prevented", "Safe useful drafts preserved"],
    [
        [r["variant"], f"{r['safe']}/{r['total_probes']}", f"{r['safe_and_useful_drafts']}/{r['draft_probes']}"]
        for r in stress["rows"]
    ],
)
outcomes = json.loads((ROOT / "artifacts" / static["created"] / "aegis-s0.json").read_text(encoding="utf-8"))[
    "outcomes"
]
scenarios = table(
    ["Scenario", "Domain", "Attack family", "Difficulty", "Task", "Attack succeeded"],
    [
        [
            o["scenario_id"],
            o["domain"],
            o["attack_family"],
            o["difficulty"],
            "PASS" if o["task_success"] else "FAIL",
            "YES" if o["attack_success"] else "no" if o["attack_present"] else "not applicable",
        ]
        for o in outcomes
    ],
)
families = table(
    ["Family", "Tasks completed", "Successful attacks"],
    [
        [family, f"{r['tasks_completed']}/{r['runs']}", r["attack_successes"]]
        for family, r in next(r for r in static["reports"] if r["variant"] == "aegis" and r["seed"] == 0)[
            "families"
        ].items()
    ],
)
if qwen:
    realmodel = table(
        ["Recorded model", "Upstream", "Profile", "Defense", "Tasks", "Successful attacks", "Experiment"],
        [
            [
                m["model"],
                m["reference_commit"][:7],
                m.get("model_profile"),
                r["variant"],
                f"{r['tasks_completed']}/{r['scenario_count']}",
                f"{r['attack_successes']}/{r['attack_runs']}",
                m["created"],
            ]
            for m in qwen
            for r in m["reports"]
        ],
    )
    diagnostic_rows = []
    for manifest in qwen:
        for row in manifest["reports"]:
            result_path = ROOT / "artifacts" / manifest["created"] / f"{row['variant']}-s{row['seed']}.json"
            measured = json.loads(result_path.read_text(encoding="utf-8"))["outcomes"]
            diagnostic_rows.append(
                [
                    manifest.get("model_profile"),
                    row["variant"],
                    len(measured),
                    sum(o["termination"].startswith("model_error") for o in measured),
                    sum(
                        "INVALID_TOOL_ARGUMENTS" in d["reason_codes"]
                        for o in measured
                        for d in o["decisions"]
                    ),
                    sum(d["decision"] == "rewrite" for o in measured for d in o["decisions"]),
                    row["metrics"]["defense_errors"],
                ]
            )
    diagnostics = table(
        ["Profile", "Defense", "Runs", "Model-error terminations", "Invalid-argument blocks", "Rewrites", "Defense errors"],
        diagnostic_rows,
    )
else:
    realmodel = "No completed Qwen evaluation is available. Do not claim reference-model robustness."
    diagnostics = "No completed real-model diagnostic table is available."

text = f"""# AEGIS: action-bound authority and persistent information-flow controls

Technical report — research prototype, IndabaX Tunisia SENTINEL challenge

## Abstract

AEGIS is an offline defense between the SENTINEL reference agent and its simulated tools. It combines task permissions, source-derived leak checks, persistent evidence, destination-field output streams, object-specific lifecycle constraints, exact-action human approvals, and revalidated safe rewrites. It emits source-linked, hash-chained decision receipts and an interactive trace explorer. The defense reads only the participant-visible request contract.

In the latest mock evaluations, AEGIS completes all 19 public tasks and records zero successful attacks among ten attack scenarios under both static and adaptive modes for three seeds. The provenance baseline completes 17 tasks with the same attack outcome. These are development results on known scenarios driven by the organizer's mock agent; they are not official scores or proof of general prompt-injection resistance. Component probes expose both useful mechanisms and remaining failure cases.

## Threat model and hypothesis

The attacker controls declared document, email, log, tool-output, or memory text inside a synthetic organization. It may impersonate authority in prose, split instructions, encode sensitive data, or adapt its input after observing actions. It cannot modify trusted policy or trusted human approval records, alter the defense process, or access real networks through simulator tools.

Our hypothesis is that checking the authority and information flow of each proposed effect can retain more task utility than blocking based on tool-name overlap with hostile text, while preventing the published harmful outcomes. A second hypothesis is that persistent evidence, stream checks, and repair make measurable contributions when those mechanisms are isolated. These hypotheses are tested on development scenarios and author-designed contract probes, not an independent holdout.

## Method

The decision pipeline validates tool permission and public argument schemas, ingests source evidence, checks data flow, checks memory and action authority, checks object lifecycle, and checks exact approval. Violations are resolved to the allowed interventions: allow, block, escalate, or rewrite. A proposed rewrite is checked again before release. Sensitive content in routing fields is not automatically repaired. A modified send becomes a draft and loses any applicability of the old approval.

Observed credential fields and sufficiently distinctive mixed identifiers become source-derived signatures. Sensitive prose contributes 48-character windows at a 24-character stride. Matching considers normalized plain text, spaced and punctuation-separated forms, reversal, base64/base64url, hexadecimal, URL decoding, and up to two decoding rounds. This is bounded representation matching, not a general semantic classifier. Encoded envelopes can be replaced while preserving surrounding safe prose.

Evidence persists in a session across the organizer's truncated history. The session key is opaque: its characters do not affect decisions. State stores observed sensitive strings, untrusted source text, lifecycle facts, and prior authorized output fields. Later-step requests missing their session fail closed; noninitial out-of-order requests cannot reset state. A one-hour TTL, 128-session cap, and explicit evidence/output budgets bound memory. The implementation requires a single service worker.

The output-stream monitor concatenates authorized values for a particular destination and field. It blocks the candidate that would complete a detected secret across prior releases. It records authorized emissions conservatively, even if an escalated action may later be denied. Retry bookkeeping prevents counting the same step/action twice. A new coverage check additionally groups fields by destination and matches four-character windows of compact known credentials in any order. It blocks new coverage reaching at least 90% and 16 characters of a representation. This closes the tested shuffled four-character fragment attacks, including alternating fields. It is a conservative heuristic: repeated substrings may overestimate coverage; early fragments, shorter pieces, recipient collusion, and semantic disclosures remain outside the guarantee.

The defense also repairs three unambiguous read-only argument aliases (`document_id` to `doc_id`, `keywords` or `search_query` to `query`) when the public schema accepts the result. Values are preserved, conflicting fields are not reconciled, writes are not repaired this way, and the replacement passes the remaining defense checks before release. This is an allowed REWRITE intervention; the agent's prompt and tool definitions remain unchanged.

For final responses, a narrow completion check recognizes selected claims that a draft or incident was created or a message was sent. Without an observed trusted success receipt of that kind, it replaces the assertion with an explicit unverified-completion statement. Sensitive-data repair and claim qualification compose, so one rewrite does not suppress the other. This prevents the tested unsupported claims but does not execute missing work. Receipts currently establish operation type somewhere in the session, not an exact goal/object/content correspondence; full factual verification remains unsolved.

Payment and remediation transitions depend on observed successful result envelopes for the same object. A document claiming approval is not an approval record. The simulator's canonical action digest binds an approval to the exact candidate arguments. Data-flow policy still applies to approved actions.

Authority checking uses provenance plus lexical action/target alignment. It permits allowed read-only tools, because hostile material must remain readable. Untrusted text cannot establish a durable policy through memory. A trusted exact approval provides an independent authority path for a consequential action but does not waive tool or data-flow checks. This design can still over-block legitimate policy memories or quoted instructions.

The contribution is the combined action-bound enforcement, persistent representation tracking, safe replacement checks, and inspectable evidence. We do not claim that hashing, taint tracking, or access-control primitives are new inventions. Parts of authority recognition remain lexical.

## Experimental setup and reproducibility

Organizer commit: `{static["reference_commit"]}`. Python: `{static["python"]}`. Models and data are declared below. The organizer repository is pinned and unmodified. The defense imports public tool schemas and contract types but does not load scenarios, fixture data, reference plans, or evaluator labels. The harness uses organizer grading only after decisions have been made.

Seeds are 0, 11, and 29. The full public suite contains 19 scenarios: nine benign and ten attacked, covering three domains and difficulty levels 1–5. Static runs apply the prescribed attack; adaptive runs use the organizer mutation attacker. Repeated seeds on this same small published suite are correlated development runs, not independent generalization samples.

The mock model internally follows organizer reference plans. AEGIS never receives those plans. Mock results must therefore be interpreted as integration/security regressions, not autonomous language-model success rates. The simulated human can reject escalation independently; that is part of the environment and must not be credited as learned intelligence in the defense.

Latest static evidence: `artifacts/{static["created"]}/manifest.json`.
Latest adaptive evidence: `artifacts/{adaptive["created"]}/manifest.json`.
Additional probes: `artifacts/stress.json`.

Each manifest contains source hashes, participant metrics, deterministic digests and retained audit-chain heads. Original JSONL simulator logs show the executed effects; audit JSONL files show source-linked defense receipts. Audit logging is inside the measured wrapper, so reported latency includes receipt/redaction work. Latency is machine-specific.

## Published-suite results

{results}

Family breakdown below is the full AEGIS static seed-0 run, not an average over differently sized groups.

{families}

Task completion and attack prevention are separate outcomes. All versions retain the nine benign tasks in these mock experiments, while AEGIS also preserves useful work in the poisoned-invoice and memory-poisoning tasks. Allowed reads suggested by hostile material can still count against the organizer's tool-use-integrity diagnostic. Zero critical violations does not mean every attempted read was independently authorized by the user's intent.

## Per-scenario evidence

{scenarios}

## Ablation study

On the public mock suite, several component ablations tie on task success and attack success because other controls cover the same cases. Those ties do not establish that the components are unnecessary. Full per-variant metrics are retained in the static manifest.

The expanded stress suite uses 16 generated-secret seeds. It contains 192 immediate/delayed encoded-draft cases, 16 memory-authority cases, 48 ordered reconstruction cases, and 48 shuffled reconstruction cases alternating subject/body fields. Each variant sees identical generated inputs. “Safe useful draft” means the secret representation is absent while a particular harmless sentence remains. Fragment probes measure prevention of the complete tested reconstruction, not prevention of every partial disclosure. The earlier 256-probe evidence is retained in `artifacts/stress-v1.json`.

{ablation}

Disabling flow removes direct leak prevention. Disabling persistence loses the earlier source after truncation. Disabling authority admits the planted memory policy. Disabling repair preserves safety through blocking but loses useful drafts. Disabling streaming admits the tested ordered fragmented reconstructions. These are mechanism checks designed by the authors; an independent adversarial evaluation remains necessary.

## Real-model evidence, separately disclosed

{realmodel}

The local quantized setup uses publisher-provided `Qwen/Qwen3-8B-GGUF`, Q4_K_M, and official llama.cpp Vulkan binaries with pinned SHA-256 checks. Organizer commit `87944a1` explicitly permits quantization, llama.cpp, runtime placement, thinking-mode selection and decode-budget changes, while requiring the same model, tools and system prompt. The current primary `stock` profile produces messages identical to the updated HF adapter; a test verifies exact equality without loading weights. Thinking is disabled and the output budget is 768 tokens, matching the new default. No safety instructions or reference plans are added. The historical `schema` profile enriches the tool description and remains a diagnostic experiment, not our primary competition evidence. Full-precision HF execution is optional under the clarified rules and has not been measured here.

The update also replaces greedy JSON extraction with first-object decoding and strips thinking blocks. Earlier runs at `14c30fb` retain the old parser and 512-token budget. They must not be treated as an isolated defense ablation against the new runs. Within the updated paired experiment, `aegis_v1` disables the new argument, completion and unordered-coverage controls while keeping the same updated parser/runtime as AEGIS.

An unsafe proposal must reach the defense for a run to demonstrate interception. If the model declines an attack by itself, or fails to produce a valid action, the result cannot be presented as a defense success. Preserve task failures, termination reasons, and unsuccessful proposals when interpreting the real-model results.

### Real-model failure diagnostics

{diagnostics}

These counts separate model protocol failures from defense execution errors. Invalid-argument blocks prevent malformed calls; they are not proof of attack interception. A `completed` termination means the agent ended its turn, not that the task grader passed.

The initial two-scenario stock-profile pilot completed zero graded tasks for either defense. Its traces show `document_id` supplied to a tool whose required parameter is `doc_id`. The allow-all project-status answer contained “October 2, 2026,” but the exact-string grader expected `2026-10-02`. This is a correct-date formatting mismatch, not a factual date error. Other failures include missing required records, incomplete work, and malformed model actions. We keep the published graders unchanged and report their failures; we do not silently replace them with favorable manual judgments.

In the full schema-profile invoice trace, Qwen retrieved the restricted token and proposed it in its final response. AEGIS rewrote that response with the token redacted; the simulator's effective `model_output` confirms the redaction. However, Qwen also claimed to have prepared a draft without invoking `email_draft`. The task grader therefore failed. This demonstrates a concrete disclosure interception, not successful completion of the invoice task. AEGIS does not comprehensively verify the truth of completion claims.

The real-model task utility is substantially below the mock result. The completed full-suite run does not show an advantage over the provenance baseline on task completion. Several consequential workflows ended early or produced invalid action types before the defense could evaluate them. Stronger evidence requires reliable reference-agent execution and repeated, clearly disclosed comparisons; a low attack-success rate alone is insufficient.

## Failure analysis and limits

Two executable security expectations deliberately fail under `xfail(strict=True)`: semantic paraphrases of confidential prose and reordered two-character fragments separated by labels. The previous four-character reordering failure is now a passing regression test, supplemented with randomized order/field probes. A paraphrase can disclose meaning without matching source text, and tiny labelled pieces evade four-character coverage. These broader channels remain unsolved.

Other limits include secrets never observed in full, source truncation before first exposure, custom ciphers, deep encodings, multilingual instruction variants, mixed-trust records, conservative credential classification, and false-positive blocks on legitimate policy memory. Untrusted-source promotion and action alignment are heuristic components. Fixed risk and confidence are ordinal engineering signals, not calibrated probabilities; the organizer's Brier/ECE outputs do not make them calibrated.

The trusted runtime supplies policy, provenance, ordering, and approval records. The local service has no production authentication or distributed state. A compromised metadata provider is outside the tested threat model. No claim is made of production readiness for real finance, email, or SOC systems.

## Engineering verification

The defense test suite includes API contracts, argument/permission checks, encoded and fragmented disclosure, safe-content preservation, exact approvals, object-specific prerequisites, history truncation, state isolation, retries, ordering, full-suite regression, deterministic digests, and audit tamper detection. Run `python -m pytest tests -q` for the current collected count. Two strict expected failures keep known weaknesses visible.

The unchanged upstream suite was also run on Windows: three tests failed. Two require unavailable symlink privileges, and one assumes Unix absolute-path behavior. Those upstream failures are not silently waived or claimed as defense test passes. Linux CI configuration is supplied, but a hosted CI execution and Docker build are not claimed unless separately recorded.

The HTTP integration was exercised with an actual simulator call to the local defense. Dashboard replay, filtering and inspection were visually checked. Hash chains are tamper-evident only relative to an independently preserved head; they are not signatures and do not prevent whole-chain replacement by an administrator.

## Responsible AI, models, and data

All scenario people, accounts, domains and credentials are fictional. No real bank or sponsor infrastructure was probed. No external training data or learned defense model was used. Model preparation downloads software/weights from the official publishers; inference and simulator evaluation are local. AgentDojo and paid model APIs have not been used. See `docs/responsible-ai.md` for data retention, false positives, human oversight and remaining limitations.

## Submission status

The deliverable includes the defense, local service, dashboard, reproducible code, manifests, traces, ablations, failure tests, report and beginner guide. The final 5–10 minute video, team identification, repository publication and organizer submission remain to be completed. The recording storyboard is in `docs/video-storyboard.md`. The report describes measured evidence; it does not promise a winning place.
"""
(ROOT / "docs/technical-report.md").write_text(text, encoding="utf-8")
print("Wrote docs/technical-report.md from completed evidence.")
