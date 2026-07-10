# Indian Finance & Banking FAQ Assistant
## Fine-Tuned Qwen2.5-1.5B | 3-Stage Pipeline | July 2026

A domain-specific FAQ assistant for Indian Finance and Banking, built by fine-tuning Qwen2.5-1.5B through a 3-stage pipeline — Domain Adaptation → Instruction Fine-Tuning → DPO Preference Alignment.

---

## Problem Statement

Base LLMs fail on India-specific finance questions:
- Wrong income tax slabs (Budget 2025 changed exemption from Rs. 3L to Rs. 4L)
- No knowledge of Income Tax Act 2025 (effective April 1, 2026)
- No knowledge of Section 87A rebate revision (Rs. 25,000 → Rs. 60,000)
- No knowledge of Budget 2026 changes (STT hike on F&O)
- Sometimes references IRS, 401k instead of Indian equivalents

Our fine-tuned model correctly answers all of these with current July 2026 data.

---

## Pipeline Overview

```
Qwen2.5-1.5B Base
       ↓
Stage 1: Non-Instruction Fine-Tuning (Domain Adaptation)
       ↓ LR=2e-4 | packing=True | 232 paragraphs | Loss: 2.61 → 1.70
DesiLadkaa/indian-finance-stage1-merged-v2
       ↓
Stage 2: Instruction Fine-Tuning (SFT)
       ↓ LR=1e-4 | packing=False | 110 Q&A pairs | Loss: 2.22 → 1.44
DesiLadkaa/indian-finance-stage2-merged-v2
       ↓
Stage 3: DPO Preference Alignment
       ↓ LR=5e-5 | beta=0.1 | 50 preference pairs
DesiLadkaa/indian-finance-stage3-final-v2
```

---

## Repository Structure

```
indian-finance-banking-assistant-v2/
├── data/
│   ├── raw_pdfs/                          # Source government PDFs
│   │   ├── gst_gstr9_faqs.pdf
│   │   ├── gst_welcome_kit.pdf
│   │   ├── incometax_itr_filing_faqs.pdf
│   │   └── incometax_new_vs_old_regime_faqs.pdf
│   ├── non_instruction_data.txt           # 232 paragraphs — Stage 1
│   ├── instruction_dataset.jsonl          # 110 Q&A pairs — Stage 2
│   └── preference_dataset.jsonl           # 50 DPO pairs — Stage 3
│
├── notebooks/
│   ├── non_instruction_finetuning.ipynb   # Stage 1 training
│   ├── instruction_finetuning.ipynb       # Stage 2 training
│   └── dpo_alignment.ipynb                # Stage 3 training
│
├── reports/
│   ├── base_model_evaluation.md           # Base model vs Stage 1
│   ├── sft_model_comparison.md            # Stage 1 vs Stage 2
│   ├── final_evaluation.md                # All stages comparison
│   └── fine_tuning_explanation.md         # Technical decisions
│
├── src/
│   ├── data_preparation.py                # Non-instruction dataset builder
│   ├── create_instruction_dataset.py      # Instruction dataset builder
│   ├── create_preference_dataset.py       # Preference dataset builder
│   ├── push_to_huggingface.py             # Dataset push script
│   └── inference.py                       # Production inference script
│
├── README.md
└── requirements.txt
```

---

## Dataset

All datasets hosted on HuggingFace: [DesiLadkaa/indian-finance-banking-assistant](https://huggingface.co/datasets/DesiLadkaa/indian-finance-banking-assistant)

| Config | Size | Description |
|--------|------|-------------|
| non_instruction | 232 paragraphs | Raw text from Indian govt portals |
| instruction | 110 Q&A pairs | India-specific finance Q&A, July 2026 current |
| preference | 50 pairs | Chosen (correct) vs Rejected (wrong/outdated) |

**Data Sources (all public domain):**
- [incometax.gov.in](https://www.incometax.gov.in) — ITA 2025, tax slabs, deductions
- [gst.gov.in](https://www.gst.gov.in) — GST rates, registration, returns
- [rbi.org.in](https://www.rbi.org.in) — monetary policy, banking, UPI, KYC
- [sebi.gov.in](https://www.sebi.gov.in) — investor education, mutual funds

---

## Models

All models hosted on HuggingFace:

| Stage | Model | Description |
|-------|-------|-------------|
| Stage 1 Adapter | [indian-finance-stage1-adapter-v2](https://huggingface.co/DesiLadkaa/indian-finance-stage1-adapter-v2) | LoRA adapter after domain adaptation |
| Stage 1 Merged | [indian-finance-stage1-merged-v2](https://huggingface.co/DesiLadkaa/indian-finance-stage1-merged-v2) | Full merged model after Stage 1 |
| Stage 2 Adapter | [indian-finance-stage2-adapter-v2](https://huggingface.co/DesiLadkaa/indian-finance-stage2-adapter-v2) | LoRA adapter after SFT |
| Stage 2 Merged | [indian-finance-stage2-merged-v2](https://huggingface.co/DesiLadkaa/indian-finance-stage2-merged-v2) | Full merged model after Stage 2 |
| Stage 3 Adapter | [indian-finance-stage3-adapter-v2](https://huggingface.co/DesiLadkaa/indian-finance-stage3-adapter-v2) | LoRA adapter after DPO |
| **Stage 3 Final** | [**indian-finance-stage3-final-v2**](https://huggingface.co/DesiLadkaa/indian-finance-stage3-final-v2) | **Production model** |

---

## Training Details

| Parameter | Value | Reason |
|-----------|-------|--------|
| Base Model | Qwen2.5-1.5B | Best fit for T4 GPU (15GB VRAM) |
| Quantization | QLoRA 4-bit | 75% memory reduction, enables T4 training |
| LoRA rank (r) | 16 | Sweet spot — capacity vs memory |
| LoRA alpha | 16 | Scale = alpha/r = 1.0, stable training |
| Target modules | q,k,v,o,gate,up,down proj | All attention + FFN layers |
| Stage 1 LR | 2e-4 | Higher for domain adaptation |
| Stage 2 LR | 1e-4 | Lower, builds on Stage 1 |
| Stage 3 LR | 5e-5 | Fine alignment, not relearning |
| DPO beta | 0.1 | Gentle preference alignment |
| Batch size | 2 × 4 grad accum = 8 effective | T4 VRAM constraint |
| Max seq length | 512 | T4 safe limit |
| Framework | Unsloth + TRL | 2x faster, 60% less VRAM |

---

## Key Results

| Question | Base Model | Final Model |
|----------|------------|-------------|
| Income tax exemption FY 2025-26 | ❌ Rs. 2.5L or Rs. 3L | ✅ Rs. 4,00,000 (Budget 2025) |
| Section 87A rebate | ❌ Rs. 12,500 | ✅ Rs. 60,000 (Budget 2025) |
| Income Tax Act 2025 | ❌ No knowledge | ✅ Explains Tax Year concept |
| Budget 2026 changes | ❌ No knowledge | ✅ STT hike on F&O, ITA 2025 |
| Standard deduction | ❌ Rs. 50,000 | ✅ Rs. 75,000 (Budget 2024) |

---

## Inference

```python
# Install
pip install -r requirements.txt

# Run demo (10 preset questions)
python src/inference.py

# Interactive mode
python src/inference.py
# Type your question when prompted
```

**Model loads from:** `DesiLadkaa/indian-finance-stage3-final-v2`

---

## Domain Coverage

- **Income Tax:** New/Old regime slabs, Section 80C/80D/87A, HRA, TDS, advance tax, ITR forms
- **Income Tax Act 2025:** Tax Year concept, new section numbering, transition from 1961 Act
- **Budget 2025:** Rs. 4L exemption, Rs. 60K Section 87A rebate, Rs. 75K standard deduction
- **Budget 2026:** STT hike on F&O, ITA 2025 operationalisation
- **GST:** Registration thresholds, rates, ITC, composition scheme, e-invoicing, GSTR returns
- **Banking & RBI:** Repo rate, KYC, DICGC insurance, UPI/UPI Lite, home loan rules
- **Investments:** PPF, NPS, ELSS, SGB, SSY, SCSS, mutual fund taxation
- **SEBI & Markets:** IPO, Demat, T+1 settlement, insider trading, SCORES

---

## Technical Stack

- **Training:** Unsloth, TRL (SFTTrainer, DPOTrainer), PEFT, bitsandbytes
- **Models:** HuggingFace Hub
- **Data:** HuggingFace Datasets
- **Compute:** Google Colab T4 GPU (free tier)
- **Code:** GitHub

---

## Author

**Ravish** | [GitHub: DesiLadkaa](https://github.com/DesiLadkaa) | [HuggingFace: DesiLadkaa](https://huggingface.co/DesiLadkaa)

*Built as part of Full-Stack GenAI and Agentic AI Bootcamp — Krish Naik Academy*
