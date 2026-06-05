# AI-Based Resume Screening and ATS Analyzer

A production-quality web application built using **Python** and **Streamlit** designed to help recruiters and job seekers parse, analyze, and rank resumes against job descriptions using Natural Language Processing (NLP) and Machine Learning (ML).

---

## Key Features

1. **Robust Resume Parser**: Extracts, cleans, and structures text from PDF and DOCX files.
2. **Metadata & Contact Extraction**: Automatically identifies names, emails, and phone numbers using regex and heuristics.
3. **Skill Gap Analysis**: Compares candidate profiles against job requirements and categorizes skills into *Technical Skills*, *Soft Skills*, and *Tools & Technologies*.
4. **Weighted ATS Score Prediction**: Predicts candidate compatibility based on four pillars:
   - **Semantic Similarity** (30% weight) - Cosine similarity of TF-IDF vectors.
   - **Skill Alignment** (40% weight) - Rate of matched skills.
   - **Experience Suitability** (20% weight) - Compares candidate's years of experience to job requirements.
   - **Education Suitability** (10% weight) - Compares candidate's highest degree to job specs.
5. **Actionable Improvement Suggestions**: Identifies missing sections, passive vocabulary (audits action verbs), and keyword stuffing.
6. **Recruiter Portal & Leaderboard**: Persists evaluations in a SQLite database, ranks multiple candidate files automatically, and plots a comparative leaderboard.
7. **Interactive Dashboard**: Displays gauge, radar, bar, and donut charts built using **Plotly**.

---

## Project Structure

```
resume-screening-system/
│
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python package dependencies
├── README.md                   # Installation & deployment guide
│
├── database/
│   ├── __init__.py
│   └── db.py                   # SQLite tables, connection, and CRUD manager
│
├── models/
│   ├── __init__.py
│   ├── ats_model.py            # Experience extraction and ATS scoring algorithm
│   └── similarity_model.py     # TF-IDF Vectorizer and Cosine Similarity models
│
├── parser/
│   ├── __init__.py
│   ├── resume_parser.py        # PDF/DOCX text reader and section divider
│   └── jd_parser.py            # Job Description reader and target specs parser
│
├── utils/
│   ├── __init__.py
│   ├── skill_extractor.py      # spaCy PhraseMatcher skill-tagging utility
│   └── ats_score.py            # Verb check, keyword stuffing, and suggestion compiler
│
├── dashboard/
│   ├── __init__.py
│   └── visualizations.py       # Plotly gauge, radar, donut, and leaderboard charts
│
└── data/
    └── skills_dataset.csv      # Vocabulary of technical, soft, and tool keywords
```

---

## Machine Learning & NLP Details

- **NLP Tokenization & Matcher**: The application uses `spaCy`'s `PhraseMatcher` configured with `attr="LOWER"` for fast, case-insensitive multi-word phrase matching. It matches skills against a curated vocabulary stored in `data/skills_dataset.csv`.
- **TF-IDF Vectorization**: Text blocks are converted into numeric vectors using Scikit-Learn's `TfidfVectorizer` (removing standard English stopwords) to represent term importance.
- **Cosine Similarity**: Measures the angle of TF-IDF vectors to compute the semantic correlation between the resume and the Job Description.
- **Date Range Heuristics**: Automatically extracts start and end years (e.g. `2018-2022`, `2020-Present`) using regex to estimate years of work experience.

---

## Getting Started (Local Development)

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your computer.

### 2. Clone the Repository
Clone or download the project files directly to your workspace.

### 3. Install Dependencies
Install all the required python packages using `pip`:
```bash
pip install -r requirements.txt
```

### 4. Download spaCy NLP Model
Download the English language model used for NLP tasks:
```bash
python -m spacy download en_core_web_sm
```

### 5. Run the Streamlit Application
Launch the web interface locally:
```bash
streamlit run app.py
```
This will start a local server and open the web application automatically in your web browser (typically at `http://localhost:8501`).

---

## Deployment to Streamlit Cloud

You can deploy this application to Streamlit Cloud for free in just a few steps:

### Step 1: Upload to GitHub
Create a new public repository on GitHub and commit all project files:
- Make sure `.gitignore` excludes temporary test DB files like `*.db` (the database will automatically initialize fresh on the server).
- Ensure `requirements.txt` is in the root directory.

### Step 2: Configure spaCy in requirements.txt (Optional but recommended)
Streamlit Cloud installs packages listed in `requirements.txt` automatically. To make sure the spaCy English model downloads during deployment, add this line at the bottom of your `requirements.txt`:
```text
https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```
This forces Streamlit Cloud to fetch and register the model without requiring separate terminal execution.

### Step 3: Launch Streamlit Cloud Dashboard
1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2. Click **New app**.
3. Select your repository, branch, and specify the main file path as `app.py`.
4. Click **Deploy!**

Your web application will be built and deployed online with a shareable public URL.
