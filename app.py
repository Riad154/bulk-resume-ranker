import streamlit as st
import pandas as pd
import json
import re
import ast
from concurrent.futures import ThreadPoolExecutor

from utils import extract_text
from groq_llm import score_resume
from ui import apply_style

st.set_page_config(page_title="AI Bulk CV Ranker for Olympic Industries PLC.", layout="wide")

st.markdown(apply_style(), unsafe_allow_html=True)

st.title("🤖 Bulk Resume Ranker for Olympic Industries PLC.")
st.caption("Powered by Groq Llama3")

files = st.file_uploader(
    "📂 Upload Multiple CVs or Resumes",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

jd = st.text_area(
    "🧾 Paste Job Description",
    height=200
)

top_n = st.slider("🎯 Shortlist Top Candidates", 1, 10, 5)


# ---------- HELPER FUNCTIONS ----------
def extract_number_from_string(s):
    """Extract first float/int from a string, handling percentages and decimals."""
    if isinstance(s, (int, float)):
        return float(s)
    if not isinstance(s, str):
        return 0.0
    # Look for a number (including decimal) possibly followed by %
    match = re.search(r"(\d+\.?\d*)", s.replace(',', ''))
    if match:
        num = float(match.group(1))
        # If the string contains a % sign, assume it's a percentage and convert to 0-1 scale if >1
        if '%' in s and num > 1:
            num = num / 100.0
        return num
    return 0.0


def extract_field(data, possible_keys, default=0.0):
    """Return the first existing value from possible_keys, converted to float."""
    for key in possible_keys:
        if key in data:
            val = data[key]
            # If it's a string, try to extract a number
            if isinstance(val, str):
                num = extract_number_from_string(val)
                return num
            try:
                return float(val)
            except (ValueError, TypeError):
                continue
    return default


def safe_json_parse(response_text):
    """Try to parse JSON; if fails, attempt to extract JSON object or Python dict."""
    # First, try direct JSON parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Look for a JSON object between curly braces
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if match:
        candidate = match.group()
        try:
            return json.loads(candidate)
        except:
            pass

    # Try to evaluate as Python dict (e.g., using single quotes)
    try:
        # Replace single quotes with double quotes for JSON compatibility
        candidate = re.sub(r"(?<!\\)'", '"', response_text)
        return json.loads(candidate)
    except:
        pass

    # Last resort: use ast.literal_eval for Python-style dicts (safe)
    try:
        return ast.literal_eval(response_text)
    except:
        return None


# ---------- PROCESS CV ----------
def process_cv(file):
    raw_response = ""  # for debugging
    try:
        text = extract_text(file)

        if not text.strip():
            return {
                "Candidate": file.name,
                "Score": 0,
                "Summary": "No readable text found",
                "_raw": ""
            }

        raw_response = score_resume(text, jd)  # store raw for debugging
        data = safe_json_parse(raw_response)

        if data is None:
            # No structured data found – return raw as summary, scores 0
            return {
                "Candidate": file.name,
                "Score": 0,
                "Summary": f"⚠️ Could not parse LLM response. Raw preview: {raw_response[:300]}...",
                "_raw": raw_response
            }

        # Flexible field extraction with number extraction
        match_score = extract_field(data, ["match_score", "overall_score", "score", "total_score"])
        skills_match = extract_field(data, ["skills_match", "skill_match", "skills_score", "skill_score"])
        experience_match = extract_field(data, ["experience_match", "exp_match", "experience_score", "exp_score"])
        education_match = extract_field(data, ["education_match", "edu_match", "education_score", "edu_score"])
        summary = data.get("summary", "")

        return {
            "Candidate": file.name,
            "Score": match_score,
            "Skills": skills_match,
            "Experience": experience_match,
            "Education": education_match,
            "Summary": summary,
            "_raw": raw_response  # store for debugging
        }

    except Exception as e:
        return {
            "Candidate": file.name,
            "Score": 0,
            "Summary": f"Error: {str(e)}",
            "_raw": raw_response
        }


# ---------- ANALYZE ----------
if st.button("🚀 Analyze Candidates"):
    if not files or not jd.strip():
        st.warning("Upload CVs and Job Description first")
        st.stop()

    results = []
    progress = st.progress(0)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_cv, f) for f in files]

        for i, future in enumerate(futures):
            results.append(future.result())
            progress.progress((i + 1) / len(files))

    df = pd.DataFrame(results)

    # Normalize scores to 0-100 if they are decimals (<= 1)
    # But first, ensure they are floats
    for col in ['Score', 'Skills', 'Experience', 'Education']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    if df['Score'].max() <= 1:
        df['Score'] = (df['Score'] * 100).round().astype(int)
    for col in ['Skills', 'Experience', 'Education']:
        if col in df.columns and df[col].max() <= 1:
            df[col] = (df[col] * 100).round().astype(int)

    ranked = df.sort_values("Score", ascending=False)

    st.subheader("🏆 Ranked Candidates")

    # Display main table without raw column
    display_cols = ['Candidate', 'Score', 'Skills', 'Experience', 'Education', 'Summary']
    ranked_display = ranked[display_cols].copy()

    st.dataframe(
        ranked_display,
        column_config={
            "Candidate": "Candidate",
            "Score": st.column_config.NumberColumn("Score", format="%d"),
            "Skills": st.column_config.NumberColumn("Skills", format="%d"),
            "Experience": st.column_config.NumberColumn("Experience", format="%d"),
            "Education": st.column_config.NumberColumn("Education", format="%d"),
            "Summary": st.column_config.TextColumn("Summary", width="large"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # Debug expander to show raw responses for entries with Score 0 and non-empty Summary
    with st.expander("🔍 Debug: Raw LLM Responses (for entries with Score 0)"):
        zero_score_df = ranked[ranked['Score'] == 0]
        if not zero_score_df.empty:
            for idx, row in zero_score_df.iterrows():
                st.markdown(f"**{row['Candidate']}**")
                st.text(row.get('_raw', 'No raw response stored'))
                st.markdown("---")
        else:
            st.info("No zero-score entries found.")

    st.subheader(f"✅ Top {top_n} Shortlisted")
    st.dataframe(
        ranked_display.head(top_n),
        column_config={
            "Candidate": "Candidate",
            "Score": st.column_config.NumberColumn("Score", format="%d"),
            "Skills": st.column_config.NumberColumn("Skills", format="%d"),
            "Experience": st.column_config.NumberColumn("Experience", format="%d"),
            "Education": st.column_config.NumberColumn("Education", format="%d"),
            "Summary": st.column_config.TextColumn("Summary", width="large"),
        },
        use_container_width=True,
        hide_index=True,
    )

    csv = ranked[display_cols].to_csv(index=False)
    st.download_button(
        "⬇ Download Result CSV",
        csv,
        "ranked_candidates.csv",
        "text/csv"
    )
