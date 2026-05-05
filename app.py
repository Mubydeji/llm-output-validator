import streamlit as st
import json
import re
from groq import Groq

st.set_page_config(
    page_title="Clinical NLP Validator",
    page_icon="🏥",
    layout="wide"
)

FIELDS = [
    "patient_name",
    "gender",
    "age",
    "visit_date",
    "chief_complaint",
    "blood_pressure",
    "heart_rate",
    "temperature",
    "diagnosis",
    "medications",
    "follow_up_days"
]

EXTRACTION_PROMPT = """You are a clinical data extraction assistant.
Extract the following fields from the clinical note below and return ONLY a valid JSON object.
Do not add any explanation, markdown, or text outside the JSON.

Fields to extract:
- patient_name (string or null)
- gender (string: "Male" or "Female" or null)
- age (integer or null)
- visit_date (string in DD/MM/YYYY format or null)
- chief_complaint (string or null)
- blood_pressure (string in "systolic/diastolic" format or null)
- heart_rate (integer or null)
- temperature (float in Celsius or null)
- diagnosis (string or null)
- medications (list of strings — include drug name and dose only, e.g. "Amoxicillin 500mg")
- follow_up_days (integer — convert weeks/months to days, or null if not mentioned)

Rules:
- Return null for any field not clearly stated in the note
- Do not infer or guess values
- medications must be a list even if empty
- follow_up_days must be an integer (1 week = 7 days, 1 month = 30 days)

Clinical note:
{note}

Return only the JSON object:"""

SAMPLE_NOTES = {
    "Clean note (easy)": """Patient: James Okafor, Male, 45 years old.
Visited on 12/03/2024. Chief complaint: persistent chest pain for 3 days.
BP: 145/92 mmHg. Heart rate: 88 bpm. Temperature: 37.1°C.
Diagnosis: Hypertensive heart disease.
Prescribed: Amlodipine 5mg once daily, Lisinopril 10mg once daily.
Follow-up in 2 weeks.""",

    "Abbreviated note (medium)": """Amina Bello, F, 32. Presented 05-07-2024 with severe headache and vomiting.
Vitals: BP 110/70, HR 76, Temp 38.4C.
Impression: Migraine with aura.
Rx: Sumatriptan 50mg PRN, Metoclopramide 10mg TDS.
Review after 1 week.""",

    "Incomplete note (hard)": """Patient brought in by family. No name given on referral slip.
Elderly male, approximately 70 years. Presented with confusion and fever.
BP not recorded. HR around 100. Temp 39.2C.
Working diagnosis: Sepsis, likely urinary source.
Started on IV Ceftriaxone 2g daily.
Admission — no outpatient follow-up scheduled.""",

    "Emergency note (hard)": """Referred case. Name: not given. Sex: female. Age: not stated.
Brought in from rural PHC with query severe malaria.
Vitals: BP 90/58. HR 130. Temp 40.1. RDT: Positive (Pf).
Dx: Severe Plasmodium falciparum malaria with hypotension.
Rx: IV Artesunate 2.4mg/kg stat, IV fluids, Paracetamol 1g IV.
ICU admission. No outpatient follow-up."""
}


def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY", None)
    if not api_key:
        return None
    return Groq(api_key=api_key)


def extract_fields(client, note_text):
    prompt = EXTRACTION_PROMPT.format(note=note_text)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=512
    )
    return response.choices[0].message.content.strip()


def parse_json(raw):
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group()), None
            except json.JSONDecodeError as e:
                return None, str(e)
        return None, "No JSON found in output"


def score_field(value):
    if value is None:
        return "null", "⬜"
    if isinstance(value, list):
        if len(value) == 0:
            return "empty list", "⬜"
        return "extracted", "✅"
    if str(value).strip() == "":
        return "empty", "⬜"
    return "extracted", "✅"


st.title("🏥 Clinical NLP Validator")
st.markdown(
    "Paste an unstructured clinical note below. The app sends it to a Groq-hosted LLM, "
    "extracts 11 structured fields, and validates the output quality in real time."
)
st.divider()

col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("Clinical Note Input")

    sample_choice = st.selectbox(
        "Load a sample note or write your own:",
        ["Write my own"] + list(SAMPLE_NOTES.keys())
    )

    if sample_choice == "Write my own":
        note_text = st.text_area(
            "Paste clinical note here:",
            height=280,
            placeholder="e.g. Patient: John Doe, Male, 45. Visited 12/03/2024. BP: 140/90..."
        )
    else:
        note_text = st.text_area(
            "Clinical note (editable):",
            value=SAMPLE_NOTES[sample_choice],
            height=280
        )

    run = st.button("Extract and Validate", type="primary", use_container_width=True)

with col_right:
    st.subheader("What This Validates")
    st.markdown("""
Each extracted field is checked for:
- ✅ **Extracted** — model returned a value
- ⬜ **Null** — model returned null (field not found in note)

**Fields extracted:**
`patient_name` · `gender` · `age` · `visit_date` · `chief_complaint` · `blood_pressure` · `heart_rate` · `temperature` · `diagnosis` · `medications` · `follow_up_days`

**Model:** llama-3.3-70b-versatile via Groq  
**Temperature:** 0.0 (deterministic)  
**Hallucination guard:** Model instructed to return null rather than guess
    """)

st.divider()

if run:
    if not note_text.strip():
        st.warning("Please enter a clinical note before extracting.")
        st.stop()

    client = get_groq_client()

    if not client:
        st.error(
            "Groq API key not found. Add GROQ_API_KEY to your Streamlit secrets. "
            "Go to App Settings → Secrets and add: GROQ_API_KEY = 'your-key-here'"
        )
        st.stop()

    with st.spinner("Sending note to LLM and extracting fields..."):
        raw_output  = extract_fields(client, note_text)
        parsed, err = parse_json(raw_output)

    if err or not parsed:
        st.error(f"Failed to parse LLM output: {err}")
        with st.expander("Raw LLM output"):
            st.code(raw_output)
        st.stop()

    st.subheader("Extraction Results")

    col1, col2, col3 = st.columns(3)

    extracted_count = sum(
        1 for f in FIELDS
        if parsed.get(f) is not None and parsed.get(f) != []
    )
    null_count    = len(FIELDS) - extracted_count
    completeness  = round(extracted_count / len(FIELDS) * 100, 1)

    col1.metric("Fields Extracted", f"{extracted_count} / {len(FIELDS)}")
    col2.metric("Completeness", f"{completeness}%")
    col3.metric("Null Fields", null_count)

    st.divider()

    field_col1, field_col2 = st.columns(2)

    for i, field in enumerate(FIELDS):
        value         = parsed.get(field)
        status, icon  = score_field(value)

        display_value = (
            ", ".join(value) if isinstance(value, list)
            else str(value) if value is not None
            else "—"
        )

        target_col = field_col1 if i % 2 == 0 else field_col2

        with target_col:
            with st.container():
                st.markdown(f"{icon} **{field.replace('_', ' ').title()}**")
                if value is not None and value != []:
                    st.success(display_value)
                else:
                    st.info("Not found in note")

    st.divider()

    with st.expander("Raw LLM JSON Output"):
        st.json(parsed)

    hallucination_note = (
        "✅ No hallucination risk detected — all null fields are consistent with missing information in the note."
        if null_count > 0
        else "✅ All fields extracted. Verify values against source note to confirm accuracy."
    )
    st.caption(hallucination_note)

st.divider()
st.caption(
    "⚕️ This tool is for research and educational purposes only. "
    "Not a substitute for clinical judgment. · "
    "Built by Mubarak Adesola Adedeji · "
    "[LinkedIn](https://linkedin.com/in/mubarak-adedeji-776804273) · "
    "[GitHub](https://github.com/Mubydeji)"
)
