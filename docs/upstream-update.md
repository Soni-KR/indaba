> Historical development note. For final September 23 metrics, public-access/CI status and submission readiness, see [the final technical report](technical-report.md). Results and timings below retain their original scope.

**Current follow-up:** the historical counts below describe earlier stages. The latest build has 96 passing AEGIS tests and no expected failures. It adds conservative confidential-context email review and isolated two-character fragment coverage. Fresh matching-build demo evidence uses ten mock cases; Qwen evidence below predates these defense changes.

# September 19 starter-kit integration

Updated the unmodified submodule from `14c30fb7c6d05d3b5724e45ae53fce17d6d750e2` to `87944a1bbb4565fac853e017dac2727b0f377704` (2026-09-19 11:44:11 +01:00).

## Organizer changes that matter

- Qwen parsing now extracts the first complete JSON object instead of greedily consuming everything between braces. It strips complete and truncated thinking blocks.
- HF runtime chooses CUDA automatically, uses float32 on CPU by default, disables thinking by default, and increases the generation budget from 384 to 768 tokens.
- Participant guidance explicitly permits quantization/GGUF, llama.cpp or Ollama, runtime placement, thinking-mode settings, and decode-budget changes. The same model, tools and system prompt must remain; adding agent safety instructions is prohibited.
- `CompetitionConfig.arena` became `attack_simulation`. Our harness uses the public defaults and remains compatible.
- Private-split terminology and report redaction were removed; this is a published-scenario, jury-judged challenge.

Source: [pinned organizer update](https://github.com/Skan22/Sentinel_Starter_Kit/commit/87944a1bbb4565fac853e017dac2727b0f377704).

## Our changes

1. Updated the submodule pin and revision fallback; upstream source remains unmodified.
2. Kept the local Q4_K_M runtime and aligned its output budget to 768. A test checks exact equality between stock-profile messages and the updated HF adapter's messages. The upstream parser is imported directly.
3. Added narrow read-argument repair inside the defense's REWRITE intervention. It preserves values, requires schema validity, refuses conflicting aliases, and rechecks the proposed replacement.
4. Added destination-level coverage detection for shuffled four-character credential pieces, including pieces spread over subject and body. The previous expected failure is now a regression test; shorter labelled pieces remain a disclosed failure.
5. Added qualification of selected unsupported completion claims, backed by observed trusted success receipts. This improves honesty, not task completion by itself.
6. Expanded stress probes from 256 to 304 and preserved the previous evidence. Added `aegis_v1`, `no_argument_repair`, `no_unordered`, and `no_completion` for measured comparisons.

## Validation and interpretation

The current suite passes 73 tests with two strict expected failures. The updated upstream suite has 192 tests: 189 pass and three fail on Windows (two require unavailable symlink privileges; one assumes POSIX absolute-path behavior). The source is not patched to hide those failures.

The latest mock static and adaptive comparisons each preserve 19/19 AEGIS tasks with no successful attacks for seeds 0, 11 and 29. Expanded stress results are 304/304 for full AEGIS versus 256/304 for the earlier controls, with 192/192 useful drafts retained in each.

Real-model measurements and termination diagnostics are generated into `technical-report.md` from completed manifests. Historical results on a different parser, output budget, upstream revision or schema-enriched prompt are not an isolated causal comparison. The paired stock-profile run evaluates earlier controls and new controls on the same updated runtime.


## September 20 follow-up: validity before recording

The current unmodified submodule is now `9aa43f731749cf1a039c5b62d49507696d54bf6c`. It includes `c86681a`, which adds compact argument cards and a requirement to read the task records before finishing. The latest commit tightens starter-service schema validation and fixes setup instructions. Empty scenario suites now raise instead of returning vacuous metrics.

The organizer requires a successful undefended attack in every demonstrated scenario/configuration. The updated Q4_K_M finance pilot failed that check: the model read the correspondence but did not perform the harmful confirmation. That cannot count as defense protection. Our harness automatically includes allow-all, records per-scenario eligibility, and excludes unvalidated cases from the validated-attack denominator. Historical files remain unchanged; report/dashboard loading adds derived validity labels.

Current demonstration model selection is generated in `demo-evidence.md` and `artifacts/demo-plan.json`. Qwen is chosen only when its paired baseline attack succeeds; verified mock is the disclosed fallback. The latest mock static runs validate all ten attacks; adaptive runs validate nine, with split settlement excluded. The current defense suite has 77 passing tests and two expected failures; the updated upstream suite has 194 tests, with the same three Windows failures described above.
