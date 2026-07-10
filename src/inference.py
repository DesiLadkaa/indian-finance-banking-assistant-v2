"""
inference.py
=============
Indian Finance & Banking FAQ Assistant
Final Model Inference Script

How to run:
    python inference.py
"""
import warnings
warnings.filterwarnings("ignore")

import torch
from unsloth import FastLanguageModel

# ── Configuration ──────────────────────────────────────────────────────────
MODEL_NAME     = "DesiLadkaa/indian-finance-stage3-final-v2"
MAX_SEQ_LENGTH = 512
LOAD_IN_4BIT   = True

# ── Prompt Template ────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """Below is an instruction that describes a task about Indian Finance and Banking. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:


### Response:
"""

# ── Load Model ─────────────────────────────────────────────────────────────
print("Loading Indian Finance & Banking FAQ Assistant...")
print(f"Model: {MODEL_NAME}")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name     = MODEL_NAME,
    max_seq_length = MAX_SEQ_LENGTH,
    dtype          = None,
    load_in_4bit   = LOAD_IN_4BIT,
)
FastLanguageModel.for_inference(model)
print("Model loaded successfully ✓\n")

# ── Generate Answer Function ───────────────────────────────────────────────
def get_answer(question: str) -> str:
    """Generate answer for a given question."""
    prompt = PROMPT_TEMPLATE.format(question)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens = 300,
            temperature    = 0.1,
            do_sample      = True,
            pad_token_id   = tokenizer.eos_token_id,
        )

    answer = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens = True
    ).strip()

    return answer

# ── Demo Questions ─────────────────────────────────────────────────────────
DEMO_QUESTIONS = [
    "What is the income tax exemption limit under new tax regime for FY 2025-26?",
    "What is Section 87A rebate for FY 2025-26?",
    "What is the Income Tax Act 2025 and when did it come into effect?",
    "What changed in Budget 2026 for income tax?",
    "What is the GST registration threshold for service providers in India?",
    "What is the TDS rate on FD interest for senior citizens?",
    "What is the PPF interest rate for FY 2025-26?",
    "What is LTCG tax rate on equity mutual funds in FY 2025-26?",
    "What is the standard deduction for salaried employees in FY 2025-26?",
    "What is UPI Lite and what is the per transaction limit?",
]

print("=" * 60)
print("DEMO — Indian Finance & Banking FAQ Assistant")
print("Model: Stage 3 DPO Final (Qwen2.5-1.5B)")
print("=" * 60)

for i, question in enumerate(DEMO_QUESTIONS, 1):
    print(f"\nQ{i}: {question}")
    answer = get_answer(question)
    print(f"A  : {answer}")
    print("-" * 60)

# ── Interactive Mode ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Interactive Mode — Ask your own questions")
print("Type 'exit' to quit")
print("=" * 60)

while True:
    print()
    question = input("Your Question: ").strip()

    if question.lower() in ["exit", "quit", "q"]:
        print("Thank you for using Indian Finance & Banking FAQ Assistant!")
        break

    if not question:
        continue

    answer = get_answer(question)
    print(f"\nAnswer: {answer}")
    print("-" * 60)
