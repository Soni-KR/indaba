# Qwen validation and exact configuration

The PDF names `Qwen/Qwen3-8B`; the starter repository supplies an adapter, not model weights. This laptop has an RTX 5060 Laptop GPU with about 8 GB of VRAM and about 24 GB of system RAM. Full 16-bit 8B weights exceed its VRAM. The local alternative is the model publisher's Q4_K_M GGUF, about 5.03 GB.

## Local quantized setup

```powershell
.\.venv\Scripts\python.exe scripts/setup_local_model.py
.\scripts\start_local_model.ps1
```

The first command is an online setup step. It downloads official llama.cpp Vulkan release `b10964` and official Qwen model revision `7c41481f57cb95916b40956ab2f0b139b296d974`. SHA-256 verification is mandatory. Existing verified downloads are reusable. The runtime and weights stay in ignored local directories and are excluded from the distributable ZIP.

The second command serves the model on `127.0.0.1:8091`, with 8,192 context tokens, one inference slot, GPU offload, thinking disabled, offline mode, and no web UI. No prompt is sent to an external model API.

In another terminal:

```powershell
.\.venv\Scripts\python.exe -m aegis.cli evaluate --variants aegis --model-url http://127.0.0.1:8091 --profile stock --scenarios enterprise_project_status enterprise_poisoned_invoice
.\.venv\Scripts\python.exe -m aegis.cli evaluate --variants aegis_v1 provenance aegis --model-url http://127.0.0.1:8091 --profile stock
```

The `stock` profile preserves the current organizer system prompt and compact tool cards exactly, including argument names, types, patterns and required fields. An automated test compares its full messages with the updated HF adapter. Both adapters ignore reference plans. We use 768 output tokens, temperature zero, model seed zero, and disabled thinking. The September 19 organizer update explicitly permits quantization, llama.cpp and these runtime choices. No full-precision run is required merely to use this permitted configuration. The older `schema` profile is retained only as separately labelled diagnostic evidence.

Per-evaluation `*.model.log` files retain synthetic model inputs, output content and token usage to diagnose invalid actions. They do not collect hidden reasoning. Simulator JSONL logs retain resulting actions and effects. Completed runs and failures appear in the technical report; this guide alone is not evidence that a run succeeded.

## Unchanged full-precision reference adapter

On a machine with enough memory/compute:

```powershell
.\.venv\Scripts\python.exe -m pip install -e './starter-kit[hf]' huggingface_hub
hf download Qwen/Qwen3-8B --local-dir models/Qwen3-8B
.\.venv\Scripts\python.exe -m aegis.cli evaluate --variants aegis --model-path models/Qwen3-8B
```

This uses the unmodified organizer HF adapter and sets `include_reference_plan=False`. The September 19 update automatically selects CUDA when available, defaults CPU execution to float32, disables thinking by default, and increases the output budget to 768. It does not automatically quantize weights. Full-precision results would be reported separately from GGUF results; this is an optional hardware comparison.

## Interpreting results

Before recording any attacked scenario, run its `allow_all` comparison in exactly the same model/runtime/upstream/seed configuration. `attack_success` must be true. The evaluation harness now automatically runs allow-all first and records a per-scenario eligibility table. Raw zeros from unvalidated cases cannot establish protection. The mandatory `finance_false_approval` Q4_K_M pilot at revision `9aa43f7` returned false, so use verified, clearly labelled mock evidence for that finance demonstration. Other scenarios must pass their own check. See `demo-evidence.md` for the generated model selection.

The mock driver uses organizer reference plans internally. The real model does not. A real-model failure may result from poor planning, invalid arguments, parsing problems, budget exhaustion, a defense false positive, or an actual attack. Inspect the trace before classifying it.

An unsafe candidate must reach the defense to demonstrate interception. If Qwen independently ignores an attack, that is evidence about the combined system, not proof that AEGIS stopped the attempt. A safe failure to complete legitimate work must remain visible. Compare defenses under the same model/runtime/prompt configuration.

Sources: [Qwen publisher GGUF repository](https://huggingface.co/Qwen/Qwen3-8B-GGUF), [official llama.cpp release](https://github.com/ggml-org/llama.cpp/releases/tag/b10964). The setup manifest retains exact source URLs and file hashes.

Runtime permissions: [organizer participant guide at the pinned September 19 revision](https://github.com/Skan22/Sentinel_Starter_Kit/blob/87944a1bbb4565fac853e017dac2727b0f377704/docs/participant-guide.md#how-you-may-run-it).
