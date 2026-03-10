import streamlit as st
import pandas as pd
import json
import re
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


# ---------- HELPER: Robust field extraction ----------
def extract_field(data, possible_keys, default=0.0):
    """Return the first existing value from possible_keys, converted to float."""
    for key in possible_keys:
        if key in data:
            try:
                return float(data[key])
            except (ValueError, TypeError):
                continue
    return default


def safe_json_parse(response_text):
    """Try to parse JSON; if fails, attempt to extract JSON from the text."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Look for a JSON object between curly braces
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None


# ---------- PROCESS ----------
def process_cv(file):
    try:
        text = extract_text(file)

        # empty CV check
        if not text.strip():
            return {
                "Candidate": file.name,
                "Score": 0,
                "Summary": "No readable text found"
            }

        response = score_resume(text, jd)
        data = safe_json_parse(response)

        if data is None:
            # If no JSON could be parsed, return raw response as summary
            return {
                "Candidate": file.name,
                "Score": 0,
                "Summary": f"Could not parse LLM response: {response[:200]}..."
            }

        # Flexible field extraction
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
            "Summary": summary
        }

    except Exception as e:
        return {
            "Candidate": file.name,
            "Score": 0,
            "Summary": f"Error: {str(e)}"
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
    if df['Score'].max() <= 1:
        df['Score'] = (df['Score'] * 100).round().astype(int)
    for col in ['Skills', 'Experience', 'Education']:
        if col in df.columns and df[col].max() <= 1:
            df[col] = (df[col] * 100).round().astype(int)

    ranked = df.sort_values("Score", ascending=False)

    st.subheader("🏆 Ranked Candidates")
    st.dataframe(
        ranked,
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

    st.subheader(f"✅ Top {top_n} Shortlisted")
    st.dataframe(
        ranked.head(top_n),
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

    csv = ranked.to_csv(index=False)
    st.download_button(
        "⬇ Download Result CSV",
        csv,
        "ranked_candidates.csv",
        "text/csv"
    )
