# Fine-Tuning Technical Explanation
## Indian Finance & Banking FAQ Assistant

## Pipeline Overview

| Stage | Trainer | Dataset | Goal | Key Config |
|-------|---------|---------|------|------------|
| Stage 1 Non-instruction | SFTTrainer | Raw text paragraphs | Domain adaptation | packing=True, LR=2e-4 |
| Stage 2 Instruction SFT | SFTTrainer | Q&A pairs (Alpaca format) | Instruction following | packing=False, LR=1e-4 |
| Stage 3 DPO | DPOTrainer | Chosen/Rejected pairs | Preference alignment | beta=0.1, LR=5e-5 |

## Model: Qwen2.5-1.5B with QLoRA 4-bit

- LoRA rank (r) = 16 — controls adapter capacity
- LoRA alpha = 16 — scale = alpha/r = 1.0
- Target modules: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- Max sequence length = 512 (T4 safe limit)
- Batch size = 2, Gradient accumulation = 4 (effective batch = 8)

## Why packing=True in Stage 1 but False in Stage 2
Stage 1 uses raw paragraphs — packing combines multiple short texts into one sequence, maximizing GPU utilization.
Stage 2 uses instruction-response pairs — packing would mix response from one pair with instruction from next, corrupting training signal.

## Why DPO beta=0.1
Beta controls preference strength. Low beta (0.1) = gentle alignment staying close to SFT behavior.
High beta risks forgetting SFT knowledge. 0.1 is the standard starting value in DPO literature.