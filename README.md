# 🚀 Bulk Resume Ranking System (AI-Powered ATS)

An **AI-powered Bulk Resume Ranking System** built using **Streamlit + Groq LLM** that automatically analyzes, scores, and ranks multiple resumes against a job description.

This project helps HR teams and recruiters **quickly shortlist candidates** using AI — saving hours of manual screening.

---

## 📌 Features

✅ Upload multiple resumes (PDF / DOCX)
✅ Extract resume text automatically
✅ AI-based resume analysis using Groq LLM
✅ ATS-style candidate scoring
✅ Automatic ranking & shortlist generation
✅ Candidate score summary table
✅ Stylish Streamlit UI
✅ Fully FREE tech stack
✅ Deployable on Streamlit

---

## 🧠 Tech Stack

| Category       | Technology                  |
| -------------- | --------------------------- |
| Frontend       | Streamlit                   |
| LLM            | Groq API                    |
| Language       | Python                      |
| Resume Parsing | pdfplumber, python-docx     |
| Data Handling  | Pandas                      |
| Environment    | python-dotenv               |
| Deployment     | Streamlit |

---

## 📁 Project Structure

```
Bulk-Resume-Ranking-System/
│
├── app.py                # Main Streamlit App
├── groq_llm.py           # Groq LLM integration
├── utils.py              # Resume parsing + scoring logic
├── requirements.txt      # Dependencies
├── .env                  # API keys (not pushed to GitHub)
├── README.md             # Project documentation
│
└── resumes/              # Uploaded resumes (runtime)
```

---

## ⚙️ Installation (Local Setup)

### 1️⃣ Clone Repository

```bash
git clone https://github.com/mkador/bulk-resume-ranking.git
cd bulk-resume-ranking
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

---

### 3️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Create `.env` File

Create a file named:

```
.env
```

Add your Groq API key:

```
GROQ_API_KEY=your_api_key_here
```

Get API key from:
👉 https://console.groq.com

---

### 5️⃣ Run the App

```bash
streamlit run app.py
```

App will open at:

```
http://localhost:8501
```

---

## 📊 How It Works

1. Upload Job Description
2. Upload multiple resumes
3. System extracts resume text
4. Groq LLM analyzes candidate relevance
5. AI generates:

   * Score (0–100)
   * Strengths
   * Weaknesses
   * Recommendation
6. Candidates ranked automatically
7. HR can email shortlisted candidates directly

---

## 🤖 AI Model Used

Groq LLM (Ultra-fast inference)

Recommended Models:

* `llama-3.3-70b-versatile` ✅
* `mixtral-8x7b-32768`

---


## 🧾 requirements.txt

```
streamlit
groq
pdfplumber
python-docx
pandas
python-dotenv
```

---

## ☁️ Deployment

### ✅ Deploy on HuggingFace Spaces (Streamlit)
```
pip install -r requirements.txt
```

## 🎯 Use Cases

* HR Recruitment Automation
* ATS Resume Screening
* Internship Hiring
* Bulk Candidate Evaluation
* Startup Hiring Pipelines

---

## 🔐 Environment Variables

| Variable       | Description        |
| -------------- | ------------------ |
| GROQ_API_KEY   | Groq API access    |

---

## 🖼️ UI Preview

Features a clean modern interface with:

* Upload panels
* Score dashboard
* Ranking table
* AI analysis cards

---

## 🚧 Future Improvements

* Resume similarity clustering
* Skill gap visualization
* Multi-job comparison
* Recruiter dashboard
* Database storage
* Authentication system

---

## 👨‍💻 Author

**Mk Ador**
AI/ML Engineer & MERN Stack Developer

---

## ⭐ Support

If you like this project:

⭐ Star the repository
🍴 Fork the project
📢 Share with others

---

## 📜 License

This project is open-source and available under the **MIT License**.

---

## 💡 Final Note

This system demonstrates how **LLMs + automation** can transform recruitment workflows by reducing manual effort and improving candidate selection quality.

Happy Building 🚀
