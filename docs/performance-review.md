> Historical development note. For final September 23 metrics, public-access/CI status and submission readiness, see [the final technical report](technical-report.md). Results and timings below retain their original scope.

# Hardened versus optimized AEGIS

Finalized September 23 from September 22 measurements. Performance-only changes; the security boundary is unchanged.

| Run | Hardened p95 ms | Optimized p95 ms | Reduction |
|---|---|---|---|
| static seed 0 | 133.983 | 17.713 | 86.8% |
| static seed 11 | 196.041 | 29.247 | 85.1% |
| static seed 29 | 188.425 | 43.938 | 76.7% |
| adaptive seed 0 | 159.868 | 18.350 | 88.5% |

These are sequential local laptop comparisons; machine load affects timing. Audit serialization/redaction is included in the evaluator latency. No timeout increase or suppressed failures was used.

## What profiling showed

The initial three-scenario profile attributes 1.621 seconds cumulatively to redact(), 1.323 to matches(), 0.890 to compact(), and 0.311 to skeleton(). These calls nest, so their times must not be added. The initial profile also includes loading, the allow-all comparison and report work; the follow-up profile only wraps the protected evaluation. Their total durations are not directly comparable. Full-suite table timings are the performance comparison. Both profiles are retained under `artifacts/performance-baseline/`.

## Changes

- Cache normalized representations and compiled redaction patterns on each Secret object; no new global secret cache. Cache lifetime follows the secret/session.
- ASCII compact normalization uses an equivalent regular-expression path; ASCII skeleton normalization returns the same input immediately. Decoded non-ASCII content is still analyzed.
- Deduplicate intermediate decoding strings while preserving the two-round reachable view set.
- Preserve decoder acceptance rules and encoding priority. Avoid an unsafe early exit that would change reason codes or skip nested encodings.

## Behavioral verification

- Original 162 pytest checks pass; no expected failures. Two dependency warnings remain.
- 1,440 generated cases have identical matches, redacted text and decoded-view sets against the frozen hardened source.
- 845 complete defense-decision payloads are identical across static seeds 0/11/29 and adaptive seed 0. This includes actions, rewrites, risk values, reasons and explanations.
- 40/40 benign drafts remain unchanged. These are ten messages in four contexts, not independent samples.
- Stress remains 304/304 prevented objectives with 192 useful drafts.
- Static remains 40/40 tasks and 0/31 validated successful attacks. Adaptive remains 40/40 tasks and 0/30 validated successful attacks, one excluded.
- Two diagnostic channels remain exposed: arbitrary labelled one-character fragments and multi-recipient collusion.

Run `.venv/Scripts/python.exe scripts/verify_performance.py` to repeat the frozen-source and decision-payload comparison. The result is `artifacts/performance-comparison.json`. Equivalence on these cases is evidence, not a mathematical proof over all inputs.

## False blocks and scope

FBR is unchanged at 16/162 = 9.8765% in static seed 0. Eight blocks stop credential-bearing record copies; eight block clean follow-up notes conservatively. See [all sixteen actions](false-block-analysis.md). Task completion does not erase the clean-note false positives.

All current-build model demonstrations remain mock. Qwen results predate both encoding and performance changes and are historical. The deadline and remaining publication/video work have not changed.
