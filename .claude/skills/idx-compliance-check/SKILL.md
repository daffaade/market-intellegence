---
name: idx-compliance-check
description: Use when writing, reviewing, or changing any user-facing text, API response field, LLM prompt, summary template, or UI copy in the market-intellegence repo, to enforce OJK non-advisory rules (no BUY/SELL/HOLD wording) and the mandatory Indonesian disclaimer
---

# IDX Compliance Check (OJK Non-Advisory)

## Overview
This platform analyses Indonesian equities (IDX) for a hackathon. It must never tell a user to buy, sell, or hold a stock. Output is limited to objective indicators: `Bullish` / `Bearish` / `Neutral`, `Opportunity Score` (0-100), `Risk Level` (`Low` / `Medium` / `High`), `Fundamental Divergence Detected`, `Anomaly Flag`, and `Anomaly Score`. Every user-facing intelligence summary must carry the mandatory disclaimer.

Source of truth: `AGENTS.md` section 3, Constraint 1.

## When to Use
- Editing any string that a user, the frontend, or an LLM will see.
- Changing an LLM prompt in `ai_engine/models/ai_summary/` (`summary_prompt.py`, `output_validator.py`) or the Go LLM adapter in `backend/internal/adapter/llm/client.go`.
- Adding or renaming a response field that carries a verdict or label.
- Reviewing a PR that touches intelligence, screener, or summary output.

## Forbidden vs. Allowed

| Forbidden (never output) | Use instead |
|---|---|
| `BUY`, `SELL`, `HOLD`, `STRONG BUY`, `ACCUMULATE` | `Bullish` / `Bearish` / `Neutral` plus a score |
| "Koleksi saham ini", "beli", "jual", "layak dibeli", "waktunya masuk" | Describe the indicator: "Opportunity Score 72 (tinggi)" |
| Price targets stated as advice ("target Rp 10.000") | Model output with its evidence and a clear "model estimate" label |

Note: `hold` is a common English code word (for example `hold` as a variable name or a comment). Do not rewrite code identifiers. Only user-facing strings matter.

## Mandatory Disclaimer
Every user-facing intelligence summary must include this exact text (Indonesian, keep it verbatim):

> *"Informasi dan analisis ini merupakan hasil pemrosesan data riset dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."*

## Procedure

1. **Scan for forbidden wording** in the files you touched, plus the whole layer if the change is broad:
   ```bash
   cd ~/market-intellegence
   grep -rniE "\b(buy|sell|hold|accumulate)\b|koleksi|layak dibeli|waktunya (masuk|keluar)" \
     ai_engine backend/internal data_processing \
     --include=*.py --include=*.go --include=*.ts --include=*.tsx --include=*.md
   ```
   Review every hit by hand. Ignore code identifiers and comments. Fix any hit that reaches a user or an LLM.

   Hits that are expected and fine as of the last scan:
   - The rule text itself in `ai_engine/models/ai_summary/summary_prompt.py` and `backend/internal/adapter/llm/client.go`, which forbids those words.
   - The banned-phrase list in `ai_engine/models/ai_summary/output_validator.py`.
   - `ACCUMULATE` as an institutional flow action label in `backend/internal/repository/memory/` seed data. This is a data label describing what an institution did, not advice to the user. Keep it, but don't reuse it as a verdict on the stock.

2. **Check the disclaimer** wherever a summary or report is built:
   ```bash
   grep -rn "bukan merupakan anjuran investasi" ai_engine backend/internal
   ```
   A summary generator or response builder that returns intelligence text without this string is a defect.

3. **Check LLM prompts.** The prompt must forbid buy/sell/hold advice and forbid invented numbers. Temperature must stay at or below `0.2` (Constraint 3). The output validator should reject or flag advisory wording.

4. **Report.** List each hit as `file:line`, with whether it was fixed or judged to be a code identifier.

## Common Mistakes
- Checking only the Python side. The Go backend builds fallback text too (`backend/internal/adapter/python_engine/client.go`).
- Accepting an LLM's "Rekomendasi: BUY" output unchanged. The validator must catch it, not the prompt alone.
- Dropping the disclaimer from a new endpoint's summary because the endpoint is "just data".
