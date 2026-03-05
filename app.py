import streamlit as st
import pandas as pd
import json
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

        data = json.loads(response)

        return {
            "Candidate": file.name,
            "Score": data.get("match_score", 0),
            "Skills": data.get("skills_match", 0),
            "Experience": data.get("experience_match", 0),
            "Education": data.get("education_match", 0),
            "Summary": data.get("summary", "")
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
    ranked = df.sort_values("Score", ascending=False)

    st.subheader("🏆 Ranked Candidates")
    st.dataframe(ranked, use_container_width=True)

    st.subheader(f"✅ Top {top_n} Shortlisted")
    st.dataframe(ranked.head(top_n), use_container_width=True)

    csv = ranked.to_csv(index=False)

    st.download_button(
        "⬇ Download Result CSV",
        csv,
        "ranked_candidates.csv",
        "text/csv"
    )