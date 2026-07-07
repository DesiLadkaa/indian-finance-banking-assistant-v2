"""
push_to_huggingface.py
=======================
Indian Finance & Banking FAQ Assistant
Push all 3 datasets to HuggingFace Hub

Run in Colab:
    %run /content/push_to_huggingface.py
"""

from huggingface_hub import login
from google.colab import userdata
from datasets import load_dataset, Dataset

# ── Config ─────────────────────────────────────────────────────────────────
HF_USERNAME = "DesiLadkaa"
REPO_NAME   = "indian-finance-banking-assistant"
HF_REPO     = f"{HF_USERNAME}/{REPO_NAME}"
DATA_DIR    = f"/content/{REPO_NAME}/data"

# ── Auth ───────────────────────────────────────────────────────────────────
login(token=userdata.get("HF_TOKEN_WRITE"))
print(f"[AUTH] Logged in to HuggingFace ✓")
print(f"[REPO] Pushing to: {HF_REPO}\n")

# ── 1. Instruction Dataset ─────────────────────────────────────────────────
print("="*55)
print("STEP 1: Pushing instruction_dataset.jsonl")
print("="*55)
instruction_ds = load_dataset(
    "json",
    data_files={"train": f"{DATA_DIR}/instruction_dataset.jsonl"},
    split="train"
)
print(f"  Loaded: {len(instruction_ds)} rows")
instruction_ds.push_to_hub(
    HF_REPO,
    config_name="instruction",
    split="train",
    commit_message="Add instruction dataset 110 QA pairs July 2026 ITA2025 Budget2025 Budget2026"
)
print(f"  [OK] Instruction dataset pushed ✓")

# ── 2. Preference Dataset ──────────────────────────────────────────────────
print("\n" + "="*55)
print("STEP 2: Pushing preference_dataset.jsonl")
print("="*55)
preference_ds = load_dataset(
    "json",
    data_files={"train": f"{DATA_DIR}/preference_dataset.jsonl"},
    split="train"
)
print(f"  Loaded: {len(preference_ds)} rows")
preference_ds.push_to_hub(
    HF_REPO,
    config_name="preference",
    split="train",
    commit_message="Add preference dataset 50 DPO pairs July 2026"
)
print(f"  [OK] Preference dataset pushed ✓")

# ── 3. Non-Instruction Dataset ─────────────────────────────────────────────
print("\n" + "="*55)
print("STEP 3: Pushing non_instruction_data.txt")
print("="*55)
with open(f"{DATA_DIR}/non_instruction_data.txt", "r") as f:
    content = f.read()

paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 100]
print(f"  Loaded: {len(paragraphs)} paragraphs")
non_instruction_ds = Dataset.from_dict({"text": paragraphs})
non_instruction_ds.push_to_hub(
    HF_REPO,
    config_name="non_instruction",
    split="train",
    commit_message="Add non-instruction dataset July 2026 current data"
)
print(f"  [OK] Non-instruction dataset pushed ✓")

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("ALL DATASETS PUSHED TO HUGGINGFACE")
print("="*55)
print(f"\n  URL: https://huggingface.co/datasets/{HF_REPO}")
print(f"\n  Configs:")
print(f"    instruction     — 110 QA pairs")
print(f"    preference      — 50 DPO pairs")
print(f"    non_instruction — paragraphs from govt sources")
print(f"\n  Data current as of: July 2026\n")
