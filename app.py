import streamlit as st
import os
import pandas as pd
import json
from typing import Dict, Any, List

# Import project modules
from parser.resume_parser import ResumeParser
from parser.jd_parser import JobDescriptionParser
from utils.skill_extractor import SkillExtractor
from database.db import DatabaseManager
from models.similarity_model import ResumeSimilarityModel
from models.ats_model import ATSModel
from utils.ats_score import ATSScorer
from dashboard.visualizations import (
    create_gauge_chart,
    create_radar_chart,
    create_skill_donut_chart,
    create_leaderboard_chart,
    create_keyword_bar_chart
)

# ----------------- PAGE CONFIG & THEME SETUP -----------------
st.set_page_config(
    page_title="AI Resume Screening & ATS Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for premium design (fonts, cards, clean borders, dynamic spacing)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #F8FAFC;
        color: #1E293B;
    }
    
    /* Premium Header styling */
    .header-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
    }
    
    .header-container h1 {
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
        color: white;
        letter-spacing: -0.025em;
    }
    
    .header-container p {
        font-size: 1.15rem;
        font-weight: 300;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Card Container */
    .premium-card {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 1.5rem;
    }
    
    .card-title {
        font-weight: 700;
        font-size: 1.35rem;
        color: #0F172A;
        margin-bottom: 1.25rem;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 0.5rem;
    }
    
    /* Pill styling */
    .skill-pill {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        margin: 0.25rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .pill-found {
        background-color: #DCFCE7;
        color: #15803D;
        border: 1px solid #BBF7D0;
    }
    
    .pill-missing {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FCA5A5;
    }
    
    /* Badge grading */
    .badge {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 700;
        text-align: center;
        display: inline-block;
        font-size: 1rem;
    }
    
    .badge-strong { background-color: #D1FAE5; color: #065F46; }
    .badge-good { background-color: #DBEAFE; color: #1E40AF; }
    .badge-average { background-color: #FEF3C7; color: #92400E; }
    .badge-needs { background-color: #FEE2E2; color: #991B1B; }

    /* Fix streamlit margins */
    div.block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- INITIALIZE SYSTEMS -----------------
@st.cache_resource
def init_systems():
    """Cache the system objects to prevent reloading databases and NLP components on rerun."""
    db = DatabaseManager("resume_screening.db")
    resume_parser = ResumeParser()
    jd_parser = JobDescriptionParser()
    skill_extractor = SkillExtractor()
    similarity_model = ResumeSimilarityModel()
    ats_model = ATSModel()
    ats_scorer = ATSScorer()
    return db, resume_parser, jd_parser, skill_extractor, similarity_model, ats_model, ats_scorer

db, r_parser, jd_parser, skill_extractor, sim_model, ats_model, ats_scorer = init_systems()

# ----------------- APP LAYOUT & BANNERS -----------------
st.markdown("""
<div class="header-container">
    <h1>AI-Based Resume Screening & ATS Analyzer</h1>
    <p>Optimize your resume for applicant tracking systems or rank multiple candidates instantly using NLP & ML</p>
</div>
""", unsafe_allow_html=True)

# Main Navigation
portal_option = st.sidebar.radio(
    "Choose Portal View",
    ["Job Seeker: Optimize Resume", "Recruiter: Candidate Leaderboard"]
)

# ----------------- PORTAL 1: JOB SEEKER -----------------
if portal_option == "Job Seeker: Optimize Resume":
    st.subheader("🔍 Resume Optimization Portal")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="premium-card"><div class="card-title">1. Upload Resume</div>', unsafe_allow_html=True)
        uploaded_resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="premium-card"><div class="card-title">2. Job Description</div>', unsafe_allow_html=True)
        jd_input_method = st.radio("Input Method", ["Paste Text", "Upload PDF/DOCX"], horizontal=True)
        
        jd_text = ""
        if jd_input_method == "Paste Text":
            jd_text = st.text_area("Paste Job Description here:", height=130, placeholder="We are looking for a Software Engineer with Python and SQL experience...")
        else:
            uploaded_jd_file = st.file_uploader("Upload Job Description File", type=["pdf", "docx", "txt"])
            if uploaded_jd_file:
                try:
                    jd_text = jd_parser.extract_text(uploaded_jd_file, uploaded_jd_file.name)
                except Exception as e:
                    st.error(f"Error reading Job Description: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Trigger Analysis
    if st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
        if not uploaded_resume:
            st.warning("Please upload a resume file first.")
        elif not jd_text.strip():
            st.warning("Please provide a Job Description.")
        else:
            with st.spinner("Analyzing resume content against job description using NLP..."):
                try:
                    # 1. Parse Resume
                    resume_bytes = uploaded_resume.read()
                    resume_data = r_parser.parse(resume_bytes, uploaded_resume.name)
                    
                    # 2. Parse JD
                    jd_data = jd_parser.parse(jd_text, title="Target Position")
                    
                    # 3. Extract Skills
                    resume_skills = skill_extractor.extract_skills(resume_data["cleaned_text"])
                    jd_skills = skill_extractor.extract_skills(jd_data["cleaned_text"])
                    
                    # 4. Perform Skill Gap Analysis
                    gap_analysis = skill_extractor.get_skill_gap(resume_skills, jd_skills)
                    
                    # 5. ML Similarity Model (TF-IDF Cosine Similarity)
                    similarity_score = sim_model.calculate_similarity(
                        resume_data["cleaned_text"], 
                        jd_data["cleaned_text"]
                    )
                    
                    # 6. Qualification Evaluations
                    candidate_exp = ats_model.extract_years_of_experience(resume_data["cleaned_text"])
                    education_score = ats_model.evaluate_education(
                        resume_data["cleaned_text"], 
                        jd_data["education_requirement"]
                    )
                    
                    # 7. Overall ATS Score Calculation
                    total_jd_skills = gap_analysis["summary"]["total_jd_skills"]
                    total_matched_skills = gap_analysis["summary"]["total_matched_skills"]
                    
                    score_details = ats_model.predict_score(
                        similarity_score=similarity_score,
                        skills_found_count=total_matched_skills,
                        total_jd_skills_count=total_jd_skills,
                        candidate_exp=candidate_exp,
                        required_exp=jd_data["min_experience"],
                        education_score=education_score
                    )
                    
                    # 8. Improvement Suggestions
                    suggestions = ats_scorer.generate_suggestions(resume_data, jd_data, gap_analysis)
                    
                    # Display Results
                    st.success("Analysis Completed Successfully!")
                    
                    # Layout Results Dashboard
                    st.markdown("### 📊 Matching Dashboard")
                    
                    row1_col1, row1_col2, row1_col3 = st.columns([1, 1, 1.2])
                    
                    with row1_col1:
                        # Gauge Chart
                        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                        fig_gauge = create_gauge_chart(score_details["ats_score"])
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                        # Display Badge Grade
                        grade = score_details["grade"]
                        if grade == "Strong Match":
                            badge_class = "badge-strong"
                        elif grade == "Good Match":
                            badge_class = "badge-good"
                        elif grade == "Average Match":
                            badge_class = "badge-average"
                        else:
                            badge_class = "badge-needs"
                            
                        st.markdown(f"<div style='text-align: center;'>Match Status: <span class='badge {badge_class}'>{grade}</span></div>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with row1_col2:
                        # Radar Chart
                        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                        fig_radar = create_radar_chart(score_details["breakdown"])
                        st.plotly_chart(fig_radar, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with row1_col3:
                        # Candidate Meta Card
                        st.markdown('<div class="premium-card"><div class="card-title">Candidate Details</div>', unsafe_allow_html=True)
                        st.markdown(f"**Name:** {resume_data['name']}")
                        st.markdown(f"**Email:** {resume_data['email'] or 'Not Found'}")
                        st.markdown(f"**Phone:** {resume_data['phone'] or 'Not Found'}")
                        st.markdown(f"**Extracted Experience:** {candidate_exp} years")
                        st.markdown(f"**Education Detected:** {jd_parser.extract_education_requirement(resume_data['cleaned_text'])}")
                        
                        st.markdown("<hr style='margin: 0.75rem 0;'>", unsafe_allow_html=True)
                        st.markdown(f"**JD Experience Requirement:** {jd_data['min_experience']} years")
                        st.markdown(f"**JD Education Requirement:** {jd_data['education_requirement']}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Row 2: Skills Gap and Suggestions tabs
                    tab1, tab2, tab3 = st.tabs(["🎯 Skill Gap Analysis", "💡 Actionable Recommendations", "📝 Extracted Sections"])
                    
                    with tab1:
                        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                        skill_cols = st.columns([1, 1])
                        
                        # Skills Donut Chart
                        with skill_cols[0]:
                            st.write("**Skills Matching Metrics**")
                            fig_donut = create_skill_donut_chart(total_matched_skills, total_jd_skills - total_matched_skills)
                            st.plotly_chart(fig_donut, use_container_width=True)
                            
                        with skill_cols[1]:
                            st.write("**Key Skill Coverage**")
                            categories = ["Technical Skills", "Soft Skills", "Tools & Technologies"]
                            for cat in categories:
                                found = gap_analysis["found_skills"].get(cat, [])
                                missing = gap_analysis["missing_skills"].get(cat, [])
                                
                                st.write(f"**{cat}**")
                                if not found and not missing:
                                    st.caption("No skills detected in this category.")
                                    continue
                                    
                                pills_html = ""
                                for f in found:
                                    pills_html += f"<span class='skill-pill pill-found'>{f}</span>"
                                for m in missing:
                                    pills_html += f"<span class='skill-pill pill-missing'>{m}</span>"
                                st.markdown(pills_html, unsafe_allow_html=True)
                                st.write("")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with tab2:
                        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                        
                        rec_cols = st.columns([1, 1])
                        with rec_cols[0]:
                            st.markdown("##### 🧱 Structure & Keyword Optimization")
                            
                            # Section structure suggestions
                            if suggestions["structure_and_formatting"]:
                                st.write("**Formatting & Sections:**")
                                for tip in suggestions["structure_and_formatting"]:
                                    st.write(f"- {tip}")
                            else:
                                st.success("Your resume structure looks perfect and contains all essential sections!")
                                
                            # Keyword density suggestions
                            if suggestions["seo_and_keyword_stuffing"]:
                                st.write("**SEO & Keyword Stuffing:**")
                                for tip in suggestions["seo_and_keyword_stuffing"]:
                                    st.write(f"- {tip}")
                            else:
                                st.success("Keyword density is natural. No stuffing detected.")
                                
                        with rec_cols[1]:
                            st.markdown("##### ✍️ Phrasing & Skill Improvements")
                            
                            # Action verbs suggestions
                            if suggestions["phrasing_and_language"]:
                                st.write("**Active Phrasing & Verbs:**")
                                for tip in suggestions["phrasing_and_language"]:
                                    st.write(f"- {tip}")
                            else:
                                st.success("Great job! Your resume uses strong action verbs to showcase achievements.")
                                
                            # Skills gaps suggestions
                            if suggestions["skills_gap_remediation"]:
                                st.write("**Skills Gaps suggestions:**")
                                for tip in suggestions["skills_gap_remediation"]:
                                    st.write(f"- {tip}")
                                    
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with tab3:
                        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                        for sec_name, sec_text in resume_data["sections"].items():
                            if sec_text.strip():
                                with st.expander(f"Section: {sec_name.upper()}"):
                                    st.text(sec_text)
                        st.markdown('</div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    st.exception(e)

# ----------------- PORTAL 2: RECRUITER PORTAL -----------------
else:
    st.subheader("💼 Recruiter Dashboard & Candidate Ranking")
    
    col1, col2 = st.columns([1, 1.2])
    
    # 1. Manage Job Descriptions
    with col1:
        st.markdown('<div class="premium-card"><div class="card-title">Manage Job Descriptions</div>', unsafe_allow_html=True)
        
        # Load existing Job Descriptions
        all_jds = db.get_all_job_descriptions()
        jd_options = {jd["id"]: f"{jd['title']} (ID: {jd['id']})" for jd in all_jds}
        
        jd_selection = st.selectbox(
            "Select Job Description Profile",
            options=list(jd_options.keys()),
            format_func=lambda x: jd_options[x],
            help="Select an existing JD to rank candidates against, or create a new one below."
        )
        
        st.write("---")
        st.write("**Create New Job Profile**")
        new_title = st.text_input("Job Title:", placeholder="Senior Python Engineer")
        new_jd_text = st.text_area("Job Description Details:", height=100, placeholder="Requirements and skills detail...")
        
        if st.button("➕ Create Job Profile", type="secondary"):
            if not new_title.strip() or not new_jd_text.strip():
                st.error("Please fill in Job Title and Description.")
            else:
                try:
                    # Parse JD to extract skills, experience, education
                    jd_parsed = jd_parser.parse(new_jd_text, title=new_title)
                    skills_extracted = skill_extractor.extract_skills(jd_parsed["cleaned_text"])
                    flat_skills = []
                    for s in skills_extracted.values():
                        flat_skills.extend(s)
                        
                    db.add_job_description(
                        title=new_title,
                        raw_text=new_jd_text,
                        required_skills=flat_skills,
                        min_experience=jd_parsed["min_experience"],
                        education_requirements=jd_parsed["education_requirement"]
                    )
                    st.success(f"Job Profile '{new_title}' created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create Job Profile: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Upload and Rank Resumes
    with col2:
        st.markdown('<div class="premium-card"><div class="card-title">Rank Candidates</div>', unsafe_allow_html=True)
        
        if not jd_selection:
            st.info("Please create a Job Description Profile first to enable resume uploading.")
        else:
            selected_jd_data = db.get_job_description(jd_selection)
            st.markdown(f"**Currently Evaluating For:** {selected_jd_data['title']}")
            st.markdown(f"**Required Experience:** {selected_jd_data['min_experience']} years | **Min Education:** {selected_jd_data['education_requirements']}")
            
            st.write("---")
            uploaded_resumes = st.file_uploader(
                "Upload Candidate Resumes (Multiple PDFs/DOCXs)", 
                type=["pdf", "docx"], 
                accept_multiple_files=True
            )
            
            if st.button("⚡ Rank Resumes", type="primary", use_container_width=True):
                if not uploaded_resumes:
                    st.warning("Please upload at least one candidate resume.")
                else:
                    progress_bar = st.progress(0)
                    total_files = len(uploaded_resumes)
                    success_count = 0
                    
                    for idx, file in enumerate(uploaded_resumes):
                        try:
                            # 1. Read & Parse Resume
                            file_bytes = file.read()
                            resume_data = r_parser.parse(file_bytes, file.name)
                            
                            # 2. Add Candidate
                            c_id = db.add_candidate(
                                name=resume_data["name"],
                                email=resume_data["email"],
                                phone=resume_data["phone"]
                            )
                            
                            # 3. Add Resume
                            resume_skills = skill_extractor.extract_skills(resume_data["cleaned_text"])
                            flat_res_skills = []
                            for s in resume_skills.values():
                                flat_res_skills.extend(s)
                                
                            r_id = db.add_resume(
                                candidate_id=c_id,
                                file_path=file.name,
                                raw_text=resume_data["raw_text"],
                                parsed_skills=flat_res_skills,
                                parsed_education=jd_parser.extract_education_requirement(resume_data["cleaned_text"]),
                                parsed_experience=str(ats_model.extract_years_of_experience(resume_data["cleaned_text"]))
                            )
                            
                            # 4. Perform scoring
                            similarity_score = sim_model.calculate_similarity(
                                resume_data["cleaned_text"], 
                                selected_jd_data["raw_text"]
                            )
                            
                            candidate_exp = ats_model.extract_years_of_experience(resume_data["cleaned_text"])
                            education_score = ats_model.evaluate_education(
                                resume_data["cleaned_text"],
                                selected_jd_data["education_requirements"]
                            )
                            
                            # Skills gap counts
                            # Convert selected JD list of skills to structured format
                            jd_skills_categorized = skill_extractor.extract_skills(selected_jd_data["raw_text"])
                            gap_analysis = skill_extractor.get_skill_gap(resume_skills, jd_skills_categorized)
                            
                            score_details = ats_model.predict_score(
                                similarity_score=similarity_score,
                                skills_found_count=gap_analysis["summary"]["total_matched_skills"],
                                total_jd_skills_count=gap_analysis["summary"]["total_jd_skills"],
                                candidate_exp=candidate_exp,
                                required_exp=selected_jd_data["min_experience"],
                                education_score=education_score
                            )
                            
                            suggestions = ats_scorer.generate_suggestions(resume_data, selected_jd_data, gap_analysis)
                            
                            # 5. Store match results
                            db.add_match_result(
                                resume_id=r_id,
                                jd_id=selected_jd_data["id"],
                                match_percentage=score_details["breakdown"]["skills_alignment"],  # Or average / ats_score
                                ats_score=score_details["ats_score"],
                                skills_found=gap_analysis["found_skills"]["Technical Skills"] + gap_analysis["found_skills"]["Tools & Technologies"],
                                skills_missing=gap_analysis["missing_skills"]["Technical Skills"] + gap_analysis["missing_skills"]["Tools & Technologies"],
                                feedback=suggestions
                            )
                            success_count += 1
                        except Exception as e:
                            st.error(f"Error parsing candidate '{file.name}': {e}")
                            
                        # Update progress
                        progress_bar.progress((idx + 1) / total_files)
                        
                    st.success(f"Successfully evaluated and ranked {success_count}/{total_files} candidates!")
                    st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. Ranking Leaderboard & Analysis
    st.write("---")
    st.markdown("### 🏆 Candidate Leaderboard")
    
    if jd_selection:
        leaderboard = db.get_leaderboard(jd_selection)
        selected_jd_data = db.get_job_description(jd_selection)
        
        if not leaderboard:
            st.info("No candidates evaluated yet for this Job Profile. Upload resumes above to compile a leaderboard.")
        else:
            lead_col1, lead_col2 = st.columns([1.5, 1])
            
            with lead_col1:
                st.markdown('<div class="premium-card"><div class="card-title">Ranking Table</div>', unsafe_allow_html=True)
                
                # Convert to clean dataframe for display
                leaderboard_df = pd.DataFrame(leaderboard)
                display_df = leaderboard_df[[
                    "candidate_name", "candidate_email", "file_path", 
                    "ats_score", "analyzed_at"
                ]].copy()
                
                display_df.columns = ["Candidate Name", "Email", "Resume File", "ATS Score", "Evaluation Date"]
                display_df = display_df.sort_values(by="ATS Score", ascending=False).reset_index(drop=True)
                
                st.dataframe(display_df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with lead_col2:
                st.markdown('<div class="premium-card"><div class="card-title">Score Comparison</div>', unsafe_allow_html=True)
                # Plotly leaderboard chart
                # Format leaderboard dictionary structure slightly for plotly chart
                formatted_list = [
                    {"candidate_name": entry["candidate_name"], "match_percentage": entry["ats_score"]} 
                    for entry in leaderboard
                ]
                fig_leaderboard = create_leaderboard_chart(formatted_list)
                st.plotly_chart(fig_leaderboard, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Interactive candidate drilldown
            st.markdown("#### 🔬 Detailed Candidate Drilldown")
            for idx, candidate in enumerate(leaderboard):
                with st.expander(f"Rank {idx+1}: {candidate['candidate_name']} — ATS Score: {candidate['ats_score']}/100"):
                    d_col1, d_col2 = st.columns([1, 1])
                    
                    with d_col1:
                        st.markdown("**Core Candidate Info**")
                        st.write(f"- **Email:** {candidate['candidate_email']}")
                        st.write(f"- **File Name:** {candidate['file_path']}")
                        
                        st.write("**Matched Skills:**")
                        if candidate["skills_found"]:
                            pills_html = "".join([f"<span class='skill-pill pill-found'>{s}</span>" for s in candidate["skills_found"]])
                            st.markdown(pills_html, unsafe_allow_html=True)
                        else:
                            st.caption("No matching skills detected.")
                            
                        st.write("**Missing Skills:**")
                        if candidate["skills_missing"]:
                            pills_html = "".join([f"<span class='skill-pill pill-missing'>{s}</span>" for s in candidate["skills_missing"]])
                            st.markdown(pills_html, unsafe_allow_html=True)
                        else:
                            st.caption("No missing skills detected.")
                            
                    with d_col2:
                        st.markdown("**Suggestions & Improvement Tips**")
                        # Deserialize feedback JSON
                        feedback_data = {}
                        if isinstance(candidate["feedback"], str):
                            try:
                                feedback_data = json.loads(candidate["feedback"])
                            except:
                                pass
                        elif isinstance(candidate["feedback"], dict):
                            feedback_data = candidate["feedback"]
                            
                        if feedback_data:
                            # Show tips
                            for cat_name, tips in feedback_data.items():
                                if cat_name == "metrics":
                                    continue
                                if tips:
                                    st.write(f"**{cat_name.replace('_', ' ').title()}:**")
                                    for t in tips[:3]:  # Top 3 tips
                                        st.write(f" - {t}")
                        else:
                            st.write("No feedback suggestions available.")
                            
            # Delete JD Profile option
            st.write("")
            if st.button("🗑️ Delete Current Job Profile and Results", type="secondary"):
                db.delete_job_description(jd_selection)
                st.success("Job profile and all associated candidate match results deleted.")
                st.rerun()
