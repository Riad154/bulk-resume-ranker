import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# -------- JSON CLEANER ----------
def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


# -------- MAIN FUNCTION ----------
def score_resume(resume, jd):

    resume = resume[:10000]
    jd = jd[:3000]

    prompt = f"""
You are an ATS recruiter AI.

IMPORTANT:
Return ONLY JSON. No explanation. No markdown.

JSON FORMAT:
{{
"match_score": number,
"skills_match": number,
"experience_match": number,
"education_match": number,
"summary": "short explanation"
}}

JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    raw = response.choices[0].message.content

    cleaned = extract_json(raw)

    return cleaned