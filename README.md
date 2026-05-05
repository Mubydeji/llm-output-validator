# LLM Output Validator: Medical Record Extraction
### Evaluating the Quality of AI-Extracted Clinical Data

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Groq](https://img.shields.io/badge/Groq-LLM%20API-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

---

## Overview

Healthcare organisations are increasingly using Large Language Models to extract
structured data from unstructured clinical notes. Before this data enters any
pipeline or dashboard, its quality must be validated systematically.

This project builds a complete validation framework that sends unstructured clinical
notes to a Groq-hosted LLM, captures structured JSON extractions, and validates
every field against ground truth using clinically appropriate rules.

---

## Research Question

> *Which fields does the LLM extract reliably, which does it miss or hallucinate,
> and what does that mean for the integrity of a clinical data pipeline?*

---

## Dataset

- 20 hand-crafted unstructured clinical notes covering a range of complexity levels
- Notes range from clean and well-structured to ambiguous, incomplete, and poorly formatted
- 9 of 20 notes contain intentional missing fields (no name, no date, no follow-up)
- Each note has a corresponding ground truth record for validation scoring
- Domain: Clinical medicine — Nigerian hospital and PHC setting

---

## Methodology

### 1. Prompt Engineering
A structured extraction prompt instructed the model to:
- Extract 11 specific fields per note
- Return only valid JSON with no additional text
- Return null for missing fields rather than guessing
- Convert follow-up duration to days consistently

### 2. LLM Extraction Pipeline
- Model: llama-3.3-70b-versatile via Groq API
- Temperature: 0.0 for deterministic outputs
- 20 notes processed sequentially with parse error handling
- 20/20 notes parsed successfully on first pass

### 3. Validation Framework
Four validation functions covering all field types:
- **String fields**: Case-insensitive partial match (≥50% keyword overlap)
- **Numeric fields**: Exact match with ±1 tolerance
- **Float fields**: Exact match with ±0.2 tolerance
- **List fields (medications)**: Drug name partial match per item

Each field scored as: `correct`, `wrong`, `missing`, or `hallucinated`

---

## Results

### Overall Performance

| Metric | Value |
|---|---|
| Notes evaluated | 20 |
| Fields evaluated | 220 |
| Mean score | 97.7% |
| Median score | 100.0% |
| Perfect scores | 15 / 20 |
| Hallucinations | 0 / 220 |

### Field-Level Accuracy

| Field | Accuracy | Failures |
|---|---|---|
| patient_name | 100% | 0 |
| gender | 100% | 0 |
| age | 100% | 0 |
| visit_date | 100% | 0 |
| blood_pressure | 100% | 0 |
| heart_rate | 100% | 0 |
| temperature | 100% | 0 |
| medications | 100% | 0 |
| diagnosis | 95% | 1 |
| follow_up_days | 95% | 1 |
| chief_complaint | 85% | 3 |

---

## Failure Analysis

All 5 failures were medium risk. Zero hallucinations detected.

**chief_complaint (3 failures)**
- CN006: Model returned null for a routine review visit with no acute complaint
- CN013: Model extracted "unconscious" but dropped "no history available"
- CN018: Model extracted cause of presentation but omitted specific injuries

**diagnosis (1 failure)**
- CN005: Model included clinical commentary — "Sepsis, likely urinary source" instead of "Sepsis"

**follow_up_days (1 failure)**
- CN017: Model returned 120 days instead of 28 — confused PCV repeat timing with follow-up schedule

---

## Pipeline Recommendations

**Deploy with confidence — 100% accuracy fields:**
patient_name, gender, age, visit_date, blood_pressure, heart_rate, temperature, medications

**Flag for human review:**
chief_complaint, diagnosis, follow_up_days

**Post-processing rules:**
1. Strip trailing commentary from diagnosis field
2. Default chief_complaint to "routine review" for notes with no acute complaint
3. Validate follow_up_days against note text to catch unit conversion errors

---

## Key Findings

- Zero hallucinations across 220 fields — the model did not fabricate any clinical values
- Structured prompt engineering with explicit null instructions prevented confabulation entirely
- The model struggles most with chief_complaint in ambiguous or incomplete notes
- follow_up_days errors stem from unit conversion confusion, fixable with post-processing
- 8 of 11 fields are pipeline-ready without human review

---

## Tools and Libraries

| Tool | Purpose |
|---|---|
| Python | Core language |
| Groq API | LLM inference (llama-3.3-70b-versatile) |
| Pandas | Data manipulation and scoring |
| Matplotlib | Visualisation |
| Seaborn | Statistical plots |

---

## Author

**Mubarak Adesola Adedeji**
Data Analyst | Python · SQL · R · Power BI
[LinkedIn](https://linkedin.com/in/mubarak-adedeji-776804273) · [GitHub](https://github.com/Mubydeji)

---

## License

MIT License — free to use, adapt, and build on with attribution.
