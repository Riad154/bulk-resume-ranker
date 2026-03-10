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
        # If the string contains a % sign and number > 1, assume it's a percentage on 0-100 scale
        if '%' in s and num > 1:
            num = num / 100.0
        return num
    return 0.0


def extract_field(data, possible_keys, default=0.0):
    """Return the first existing value from possible_keys, converted to float."""
    for key in possible_keys:
        if key in data:
            val = data[key]
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


def extract_scores_from_text(text):
    """
    Fallback: extract scores directly from raw text using regex patterns.
    Returns a dict with keys: match_score, skills, experience, education, summary.
    """
    result = {
        "match_score": 0.0,
        "skills": 0.0,
        "experience": 0.0,
        "education": 0.0,
        "summary": ""
    }

    # Patterns for common score indicators (case-insensitive)
    patterns = {
        "match_score": [
            r"(?:overall|total|match)\s*score\s*[:\-]?\s*(\d+\.?\d*%?)",
            r"score\s*[:\-]?\s*(\d+\.?\d*%?)",
        ],
        "skills": [
            r"skills?\s*(?:match|score)?\s*[:\-]?\s*(\d+\.?\d*%?)",
            r"skill\s*score\s*[:\-]?\s*(\d+\.?\d*%?)",
        ],
        "experience": [
            r"experience\s*(?:match|score)?\s*[:\-]?\s*(\d+\.?\d*%?)",
            r"exp\s*score\s*[:\-]?\s*(\d+\.?\d*%?)",
        ],
        "education": [
            r"education\s*(?:match|score)?\s*[:\-]?\s*(\d+\.?\d*%?)",
            r"edu\s*score\s*[:\-]?\s*(\d+\.?\d*%?)",
        ]
    }

    for key, pat_list in patterns.items():
        for pat in pat_list:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                num_str = m.group(1)
                num = extract_number_from_string(num_str)
                result[key] = num
                break

    # Try to extract summary (often after "summary:" or in a separate paragraph)
    summary_match = re.search(r"summary\s*[:\-]?\s*(.+?)(?:\n\n|\Z)", text, re.IGNORECASE | re.DOTALL)
    if summary_match:
        result["summary"] = summary_match.group(1).strip()
    else:
        # If no explicit summary, take the last sentence or something
        # For simplicity, we can take the last non-empty line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            result["summary"] = lines[-1]

    return result


# ---------- PROCESS CV ----------
def process_cv(file):
    raw_response = ""
    try:
        text = extract_text(file)

        if not text.strip():
            return {
                "Candidate": file.name,
                "Score": 0,
                "Summary": "No readable text found",
                "_raw": ""
            }

        raw_response = score_resume(text, jd)
        data = safe_json_parse(raw_response)

        # Initialize with defaults
        match_score = 0.0
        skills_match = 0.0
        experience_match = 0.0
        education_match = 0.0
        summary = ""

        if data is not None and isinstance(data, dict):
            # Extract from JSON
            match_score = extract_field(data, ["match_score", "overall_score", "score", "total_score"])
            skills_match = extract_field(data, ["skills_match", "skill_match", "skills_score", "skill_score"])
            experience_match = extract_field(data, ["experience_match", "exp_match", "experience_score", "exp_score"])
            education_match = extract_field(data, ["education_match", "edu_match", "education_score", "edu_score"])
            summary = data.get("summary", "")

        # If any score is zero but raw_response contains numbers, try fallback extraction
        # (This will also run if data is None)
        if match_score == 0.0 or skills_match == 0.0 or experience_match == 0.0 or education_match == 0.0:
            fallback = extract_scores_from_text(raw_response)
            # Only override if fallback extracted a non-zero value (or if we have no summary)
            if match_score == 0.0:
                match_score = fallback["match_score"]
            if skills_match == 0.0:
                skills_match = fallback["skills"]
            if experience_match == 0.0:
                experience_match = fallback["experience"]
            if education_match == 0.0:
                education_match = fallback["education"]
            if not summary and fallback["summary"]:
                summary = fallback["summary"]

        # If still no summary and data is None, use a preview
        if not summary and data is None:
            summary = f"Raw preview: {raw_response[:200]}..."

        return {
            "Candidate": file.name,
            "Score": match_score,
            "Skills": skills_match,
            "Experience": experience_match,
            "Education": education_match,
            "Summary": summary,
            "_raw": raw_response
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

    # Debug expander to show raw responses for entries with Score 0
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
