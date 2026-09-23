**Latest encoding follow-up:** Base32, ROT13 and the tested Unicode lookalikes now trigger intervention. Current tests: 162 passing; benign checks: 40/40. Two fragment channels remain exposed. See [before/after comparison](encoding-comparison.md). Earlier counts below are historical. No current-build Qwen result is claimed.

**Current evidence, September 22:** see [final review](september-22-review.md). AEGIS has 98 passing pytest checks, but the separate ten-case adversarial audit exposes five channels. Three benign warning drafts pass. Fresh full-suite evidence is mock; Qwen pairs retain their September 21 date. Earlier counts below describe development history.

# Responsible AI and safety statement

AEGIS is a research prototype for the fully synthetic SENTINEL simulator. It does not connect to real email, accounts, banking systems, or SOC infrastructure. It is not approved for production use or autonomous financial decisions.

## Scope and information observed

The defense sees the authenticated task goal, proposed action, participant-visible policy, conversation, provenance metadata, and trusted history digest. It stores observed source-derived sensitive strings, evidence references, observed lifecycle states, and recent authorized output fields in process memory. Raw source strings are needed to derive encoded variants; this is not a hash-only secret store.

Audit files contain redacted action fields and recent observations, reason codes, ordinal risk, confidence, provenance references, latency, and integrity hashes. Redaction is best effort within the documented detector scope. Original organizer traces retain fictional source data. Neither trace format should be used to publish real sensitive information.

The only interventions are allow, block, escalate, and rewrite. No action is secretly executed outside the simulator. No reference plans or evaluator labels enter the defense.

## Intended protection

Active tool permissions and schemas constrain the action space. Source-derived information-flow checks stop the tested literal and encoded disclosure paths, including final answers and memory. Persistent session evidence survives truncated conversation windows. Approvals are bound to the candidate's canonical digest and cannot override data-flow checks. Payment and remediation prerequisites are tied to the same observed object. Durable memory cannot promote untrusted context into policy authority.

## False positives and uncertainty

Mixed identifiers in sensitive documents can be treated too conservatively. Quoted tool instructions that exactly resemble a proposed write can trigger a block without a trusted approval. A legitimate policy summary in memory can be blocked after unrelated untrusted content. Missing object-state evidence blocks lifecycle transitions. The defense intentionally allows policy-permitted reads even when an attacker suggested them; downstream controls carry the burden of preventing harmful effects.

Risk values and confidence are manually assigned engineering signals, not learned or calibrated probabilities. A low risk means the implemented constraints found no violation. It does not prove the action is safe. Grader-provided calibration diagnostics in evaluation output do not change this interpretation.

## Known failures

- Semantic paraphrases can disclose confidential meaning without matching source strings.
- Ordered fragments and coverage by four-character credential pieces across fields at the same destination are monitored. Early partial fragments, shorter pieces, recipient collusion, and transformations outside known representations can still disclose information. Coverage can be overestimated for repetitive values.
- Unknown secrets or source bytes truncated before the defense first observes them cannot reliably be recognized.
- Custom ciphers, steganography, images, Unicode confusables outside normalization, and deep encoding chains are not comprehensively handled.
- Instruction recognition is partly lexical and is weaker for paraphrases and languages other than English.
- Completion qualification recognizes selected English assertions and observed receipt types, not all meanings. A previous receipt of the same operation type can mask an unsupported claim about a different object or goal. Qualifying a claim does not perform the missing work.
- Argument repair renames only three known-equivalent read fields, preserves values and rechecks policy. It never repairs write arguments or invents missing identifiers; many model planning/protocol failures remain.
- A compromised trusted metadata/policy provider or forged trusted approval digest is outside the threat model.
- The local service assumes trusted transport and one worker. It has no production authentication or distributed state. Restart or expiry loses prior evidence; a later-step request without its session fails closed and requires a fresh task.
- The one-hour session TTL, 128-session cap, and evidence budgets may stop lengthy legitimate work. Capacity failures block; they do not silently evict active state.
- Hash chains detect edits relative to an independently retained final hash. They do not prevent a local administrator from rewriting the entire chain, and are not signatures or remote attestations.

## Human involvement

The human must approve exact consequential actions when no matching approval exists. An unapproved send can become a draft. Rewritten content needs fresh approval before sending. In the mock simulator, approval is provided by the organizer's simulated human, which is an additional safety layer; it must not be presented as defense intelligence. No operator should approve a request solely because a lower-trust document claims approval already exists.

## Models, data, and claims

Executed evidence uses the organizer's deterministic mock agent and synthetic public scenarios, plus author-generated synthetic contract probes. Model-specific executed evidence is listed in the technical report. A separate local adapter supports publisher-provided quantized Qwen3-8B weights; its runtime and prompt profile are disclosed. The unchanged full-precision HF reference configuration has not been run. No fine-tuning, external dataset, real personal data, or third-party model API was used. AgentDojo was not run. Repeated seeds on known scenarios are not an independent statistical sample or a generalization guarantee.

The September 19 participant guide expressly allows quantization, llama.cpp, thinking-mode and decode-budget changes while retaining the model, tools and system prompt. Current primary runs preserve the updated reference messages exactly; historical schema-enriched runs are labelled diagnostic. Before/after defense comparisons use the same upstream version and runtime within each paired experiment.

The September 20 validity rule requires a successful undefended attack for each scenario/configuration before crediting protection. Our harness, historical report loader and dashboard enforce that distinction. When Qwen fails this prerequisite, the demonstration plan selects a verified mock comparison and labels the model. No unvalidated zero-attack result is presented as resistance to an exercised attack.



Latest boundary changes: confidential prose observed by the defense now triggers exact-action review for external emails, including harmless ones. This is a conservative workflow restriction, not a semantic classifier. Human approval may release a paraphrase; incorrect approval remains a risk. Existing exact credential restrictions still apply even with approval. Isolated two-character fragments are now monitored, but this does not protect every partial or single-character disclosure. The current build has 96 passing tests; earlier Qwen results are historical and the current demo plan uses matching-build mock runs.
