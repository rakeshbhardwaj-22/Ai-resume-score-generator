import os
import json
import datetime
from flask import Flask, request, jsonify, render_template_string
from parser.resume_parser import ResumeParser
from parser.jd_parser import JobDescriptionParser
from utils.skill_extractor import SkillExtractor
from database.db import DatabaseManager
from models.similarity_model import ResumeSimilarityModel
from models.ats_model import ATSModel
from utils.ats_score import ATSScorer

app = Flask(__name__)

# Route SQLite to /tmp on Vercel as Vercel runs on a read-only filesystem (except /tmp)
db_path = "/tmp/resume_screening.db" if os.environ.get("VERCEL") or os.environ.get("NOW_REGION") else "resume_screening.db"
db = DatabaseManager(db_path)

r_parser = ResumeParser()
jd_parser = JobDescriptionParser()
skill_extractor = SkillExtractor()
sim_model = ResumeSimilarityModel()
ats_model = ATSModel()
ats_scorer = ATSScorer()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Resume Screening & ATS Analyzer</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <style>
        :root {
            --bg-primary: #0b0f19;
            --bg-secondary: #111827;
            --bg-tertiary: #1f2937;
            --border-color: #374151;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-primary: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.15);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --card-gradient: linear-gradient(135deg, #111827 0%, #1e293b 100%);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        header {
            background-color: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 1.25rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(12px);
            background-color: rgba(17, 24, 39, 0.85);
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            font-size: 1.75rem;
            animation: pulse 2s infinite;
        }

        .logo-text {
            font-weight: 800;
            font-size: 1.35rem;
            letter-spacing: -0.025em;
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .tagline {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            background-color: var(--bg-tertiary);
            border: 1px solid var(--border-color);
        }

        .main-container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 1.5rem;
            width: 100%;
            display: grid;
            grid-template-columns: 450px 1fr;
            gap: 2rem;
            flex-grow: 1;
        }

        @media (max-width: 1024px) {
            .main-container {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--card-gradient);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            position: relative;
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: #4b5563;
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }

        .input-control {
            width: 100%;
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.95rem;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .input-control:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }

        textarea.input-control {
            resize: vertical;
            min-height: 120px;
        }

        .upload-zone {
            border: 2px dashed var(--border-color);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background-color: rgba(17, 24, 39, 0.4);
            position: relative;
        }

        .upload-zone:hover, .upload-zone.dragover {
            border-color: var(--accent-primary);
            background-color: var(--accent-glow);
        }

        .upload-icon {
            font-size: 2rem;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
        }

        .upload-text {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .upload-text strong {
            color: var(--accent-primary);
        }

        .file-info {
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background-color: var(--bg-tertiary);
            border-radius: 6px;
            display: none;
            align-items: center;
            justify-content: space-between;
            font-size: 0.85rem;
        }

        .remove-file {
            color: var(--danger);
            cursor: pointer;
            font-weight: bold;
            font-size: 1rem;
        }

        input[type="file"] {
            display: none;
        }

        .btn-primary {
            width: 100%;
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            border: none;
            border-radius: 10px;
            padding: 1rem;
            color: white;
            font-family: inherit;
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.5);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .results-container {
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        .placeholder-results {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 400px;
            text-align: center;
            color: var(--text-secondary);
        }

        .placeholder-icon {
            font-size: 4rem;
            margin-bottom: 1.5rem;
            opacity: 0.5;
        }

        .placeholder-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .placeholder-desc {
            max-width: 400px;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .loading-screen {
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(11, 15, 25, 0.85);
            border-radius: 16px;
            z-index: 10;
            backdrop-filter: blur(8px);
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(59, 130, 246, 0.2);
            border-top-color: var(--accent-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 1.5rem;
        }

        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .candidate-title {
            font-size: 1.5rem;
            font-weight: 800;
        }

        .match-badge {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.9rem;
            display: inline-block;
        }

        .match-strong { background-color: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid var(--success); }
        .match-good { background-color: rgba(59, 130, 246, 0.15); color: var(--accent-primary); border: 1px solid var(--accent-primary); }
        .match-average { background-color: rgba(245, 158, 11, 0.15); color: var(--warning); border: 1px solid var(--warning); }
        .match-needs { background-color: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid var(--danger); }

        .candidate-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            padding: 1.25rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }

        .meta-item {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .meta-item strong {
            display: block;
            font-size: 0.95rem;
            color: var(--text-primary);
            margin-top: 0.25rem;
        }

        .charts-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        @media (max-width: 768px) {
            .charts-row {
                grid-template-columns: 1fr;
            }
        }

        .chart-box {
            background-color: rgba(17, 24, 39, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .chart-box-title {
            align-self: flex-start;
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }

        .skills-section {
            background-color: rgba(17, 24, 39, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .skill-group-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .skill-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }

        .skill-pill {
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            border: 1px solid transparent;
            transition: all 0.2s;
        }

        .skill-pill.found {
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--success);
            border-color: rgba(16, 185, 129, 0.3);
        }

        .skill-pill.missing {
            background-color: rgba(239, 68, 68, 0.08);
            color: #fca5a5;
            border-color: rgba(239, 68, 68, 0.2);
            text-decoration: line-through;
            opacity: 0.75;
        }

        .recommendations-section {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .rec-box {
            border-left: 4px solid var(--accent-primary);
            background-color: rgba(31, 41, 55, 0.4);
            border-radius: 0 12px 12px 0;
            padding: 1rem 1.25rem;
        }

        .rec-box.success { border-left-color: var(--success); }
        .rec-box.warning { border-left-color: var(--warning); }
        .rec-box.danger { border-left-color: var(--danger); }

        .rec-title {
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .rec-list {
            padding-left: 1.25rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        .rec-list li {
            margin-bottom: 0.25rem;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.08); }
            100% { transform: scale(1); }
        }

        footer {
            margin-top: auto;
            text-align: center;
            padding: 2rem;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.85rem;
        }

        /* Responsive tabs */
        .tabs-header {
            display: flex;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 1.5rem;
            gap: 1.5rem;
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 600;
            padding: 0.75rem 0.5rem;
            cursor: pointer;
            position: relative;
            transition: color 0.2s;
        }

        .tab-btn:hover {
            color: var(--text-primary);
        }

        .tab-btn.active {
            color: var(--accent-primary);
        }

        .tab-btn.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 100%;
            height: 2px;
            background-color: var(--accent-primary);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-container">
            <span class="logo-icon">🎯</span>
            <span class="logo-text">AI Resume Screener</span>
        </div>
        <span class="tagline">NLP & ML-powered ATS Optimizer</span>
    </header>

    <div class="main-container">
        <!-- Input Panel -->
        <div class="card" style="height: fit-content;">
            <div class="card-title">
                <span>⚡</span> Analyze Profile
            </div>
            
            <form id="analyzeForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label>1. Upload Candidate Resume</label>
                    <div class="upload-zone" id="uploadZone">
                        <div class="upload-icon">📁</div>
                        <div class="upload-text">Drag & drop or <strong>browse file</strong></div>
                        <p style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">Supports PDF & DOCX</p>
                    </div>
                    <input type="file" id="resumeFile" name="resume" accept=".pdf,.docx">
                    <div class="file-info" id="fileInfo">
                        <span id="fileName" style="font-weight: 600;">resume.pdf</span>
                        <span class="remove-file" id="removeFile">&times;</span>
                    </div>
                </div>

                <div class="form-group">
                    <label for="jdText">2. Paste Job Description</label>
                    <textarea class="input-control" id="jdText" name="jd_text" placeholder="We are seeking a Senior Backend Engineer... Experience with Python, SQL, AWS, and docker is required."></textarea>
                </div>

                <div class="form-group">
                    <label for="minExperience">3. Minimum Experience (Years)</label>
                    <input type="number" class="input-control" id="minExperience" name="min_experience" min="0" max="30" value="0">
                </div>

                <div class="form-group">
                    <label for="educationRequirement">4. Education Requirement</label>
                    <select class="input-control" id="educationRequirement" name="education_requirement">
                        <option value="Not Specified">Not Specified</option>
                        <option value="Bachelor's Degree">Bachelor's Degree</option>
                        <option value="Master's Degree">Master's Degree</option>
                        <option value="PhD / Doctorate">PhD / Doctorate</option>
                    </select>
                </div>

                <button type="submit" class="btn-primary" id="submitBtn">🚀 Run Analytics</button>
            </form>
        </div>

        <!-- Output / Dashboard Panel -->
        <div class="card" id="resultsCard" style="min-height: 500px;">
            <div class="loading-screen" id="loadingScreen">
                <div class="spinner"></div>
                <h3 style="font-weight: 700; margin-bottom: 0.5rem;">Running NLP Analysis</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">Extracting details & predicting ATS scores...</p>
            </div>

            <!-- Placeholder state -->
            <div class="placeholder-results" id="placeholderState">
                <span class="placeholder-icon">📊</span>
                <h3 class="placeholder-title">Interactive Match Dashboard</h3>
                <p class="placeholder-desc">Upload a resume and input job requirements on the left, then click 'Run Analytics' to view semantic fit, skill alignment, and recommendations.</p>
            </div>

            <!-- Analysis results content (hidden initially) -->
            <div id="resultsContent" style="display: none;">
                <div class="dashboard-header">
                    <div>
                        <h2 class="candidate-title" id="resCandidateName">John Doe</h2>
                        <p id="resFileName" style="font-size: 0.85rem; color: var(--text-secondary);">resume.pdf</p>
                    </div>
                    <span class="match-badge" id="resGradeBadge">Strong Match</span>
                </div>

                <!-- Meta Row -->
                <div class="candidate-meta">
                    <div class="meta-item">
                        Email
                        <strong id="resEmail">johndoe@example.com</strong>
                    </div>
                    <div class="meta-item">
                        Phone
                        <strong id="resPhone">+1-234-567-8900</strong>
                    </div>
                    <div class="meta-item">
                        Experience Detected
                        <strong id="resExperience">5.5 Years</strong>
                    </div>
                    <div class="meta-item">
                        Education Detected
                        <strong id="resEducation">Bachelor's</strong>
                    </div>
                </div>

                <!-- Charts Area -->
                <div class="charts-row">
                    <div class="chart-box">
                        <div class="chart-box-title">Predicted ATS Match Score</div>
                        <div id="gaugeChart" style="width: 100%; min-height: 220px;"></div>
                    </div>
                    <div class="chart-box">
                        <div class="chart-box-title">Score Components Breakdown</div>
                        <div id="radarChart" style="width: 100%; min-height: 220px;"></div>
                    </div>
                </div>

                <!-- Navigation Tabs -->
                <div class="tabs-header">
                    <button class="tab-btn active" onclick="switchTab('tabSkills')">🎯 Skill Gap Analysis</button>
                    <button class="tab-btn" onclick="switchTab('tabRecommendations')">💡 Actionable Recommendations</button>
                </div>

                <!-- Tab 1: Skills -->
                <div class="tab-content active" id="tabSkills">
                    <div class="skills-section">
                        <h3 class="skill-group-title">🛠️ Technical Skills</h3>
                        <div class="skill-pills" id="techSkillsContainer"></div>

                        <h3 class="skill-group-title">⚙️ Tools & Technologies</h3>
                        <div class="skill-pills" id="toolSkillsContainer"></div>

                        <h3 class="skill-group-title">💬 Soft Skills</h3>
                        <div class="skill-pills" id="softSkillsContainer"></div>
                    </div>
                </div>

                <!-- Tab 2: Recommendations -->
                <div class="tab-content" id="tabRecommendations">
                    <div class="recommendations-section">
                        <div class="rec-box warning" id="recStructureBox">
                            <h4 class="rec-title">🧱 Formatting & Section Structure</h4>
                            <ul class="rec-list" id="recStructureList"></ul>
                        </div>
                        <div class="rec-box danger" id="recSeoBox">
                            <h4 class="rec-title">🔍 ATS SEO & Keyword Stuffing</h4>
                            <ul class="rec-list" id="recSeoList"></ul>
                        </div>
                        <div class="rec-box" id="recPhrasingBox">
                            <h4 class="rec-title">✍️ Phrasing & Language Improvement</h4>
                            <ul class="rec-list" id="recPhrasingList"></ul>
                        </div>
                        <div class="rec-box success" id="recRemediationBox">
                            <h4 class="rec-title">📚 Skills Gap Remediation</h4>
                            <ul class="rec-list" id="recRemediationList"></ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer>
        <p>AI-Based Resume Screening and ATS Analyzer &copy; 2026. Made with Python, Flask, spaCy and ApexCharts.</p>
    </footer>

    <script>
        const uploadZone = document.getElementById('uploadZone');
        const resumeFileInput = document.getElementById('resumeFile');
        const fileInfo = document.getElementById('fileInfo');
        const fileNameSpan = document.getElementById('fileName');
        const removeFile = document.getElementById('removeFile');
        const analyzeForm = document.getElementById('analyzeForm');
        const loadingScreen = document.getElementById('loadingScreen');
        const placeholderState = document.getElementById('placeholderState');
        const resultsContent = document.getElementById('resultsContent');

        let gaugeChartInstance = null;
        let radarChartInstance = null;

        // File Selection Event Listeners
        uploadZone.addEventListener('click', () => resumeFileInput.click());

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                resumeFileInput.files = e.dataTransfer.files;
                updateFileInfo();
            }
        });

        resumeFileInput.addEventListener('change', updateFileInfo);

        removeFile.addEventListener('click', (e) => {
            e.stopPropagation();
            resumeFileInput.value = '';
            fileInfo.style.display = 'none';
            uploadZone.style.display = 'block';
        });

        function updateFileInfo() {
            if (resumeFileInput.files.length > 0) {
                fileNameSpan.textContent = resumeFileInput.files[0].name;
                uploadZone.style.display = 'none';
                fileInfo.style.display = 'flex';
            }
        }

        // Form Submit
        analyzeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!resumeFileInput.files || resumeFileInput.files.length === 0) {
                alert('Please upload a resume file first.');
                return;
            }
            if (!document.getElementById('jdText').value.trim()) {
                alert('Please provide a Job Description.');
                return;
            }

            // Show loading
            loadingScreen.style.display = 'flex';

            const formData = new FormData(analyzeForm);

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.error || 'Server error during analysis');
                }

                const data = await response.json();
                renderResults(data);
            } catch (error) {
                alert('Analysis failed: ' + error.message);
                console.error(error);
            } finally {
                loadingScreen.style.display = 'none';
            }
        });

        // Tab Switching
        window.switchTab = function(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Find clicked button
            const clickedBtn = Array.from(document.querySelectorAll('.tab-btn')).find(
                btn => btn.getAttribute('onclick').includes(tabId)
            );
            if (clickedBtn) clickedBtn.classList.add('active');

            const targetContent = document.getElementById(tabId);
            if (targetContent) targetContent.classList.add('active');
        };

        // Render Results Data
        function renderResults(data) {
            placeholderState.style.display = 'none';
            resultsContent.style.display = 'block';

            // Candidate Info
            document.getElementById('resCandidateName').textContent = data.candidate_details.name;
            document.getElementById('resFileName').textContent = resumeFileInput.files[0].name;
            document.getElementById('resEmail').textContent = data.candidate_details.email;
            document.getElementById('resPhone').textContent = data.candidate_details.phone;
            document.getElementById('resExperience').textContent = data.candidate_details.extracted_experience + ' Years';
            document.getElementById('resEducation').textContent = data.candidate_details.education_detected;

            // Grade Badge
            const badge = document.getElementById('resGradeBadge');
            badge.textContent = data.score_details.grade;
            badge.className = 'match-badge';
            
            const grade = data.score_details.grade;
            if (grade === "Strong Match") badge.classList.add('match-strong');
            else if (grade === "Good Match") badge.classList.add('match-good');
            else if (grade === "Average Match") badge.classList.add('match-average');
            else badge.classList.add('match-needs');

            // Render Charts
            renderGaugeChart(data.score_details.ats_score);
            renderRadarChart(data.score_details.breakdown);

            // Render Skills
            renderSkills('techSkillsContainer', data.gap_analysis.found_skills["Technical Skills"], data.gap_analysis.missing_skills["Technical Skills"]);
            renderSkills('toolSkillsContainer', data.gap_analysis.found_skills["Tools & Technologies"], data.gap_analysis.missing_skills["Tools & Technologies"]);
            renderSkills('softSkillsContainer', data.gap_analysis.found_skills["Soft Skills"], data.gap_analysis.missing_skills["Soft Skills"]);

            // Render Recommendations
            renderList('recStructureList', data.suggestions.structure_and_formatting, 'recStructureBox', 'Your resume structure contains all essential sections.');
            renderList('recSeoList', data.suggestions.seo_and_keyword_stuffing, 'recSeoBox', 'Keyword density looks natural and optimized.');
            renderList('recPhrasingList', data.suggestions.phrasing_and_language, 'recPhrasingBox', 'Phrasing is clear and contains strong action verbs.');
            renderList('recRemediationList', data.suggestions.skills_gap_remediation, 'recRemediationBox', 'No critical skills gaps detected against the Job Description.');

            // Reset tab
            switchTab('tabSkills');
        }

        function renderSkills(containerId, found, missing) {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            
            if ((!found || found.length === 0) && (!missing || missing.length === 0)) {
                container.innerHTML = '<span style="font-size: 0.85rem; color: var(--text-secondary); font-style: italic;">No skills matching this category detected.</span>';
                return;
            }

            if (found) {
                found.forEach(s => {
                    const span = document.createElement('span');
                    span.className = 'skill-pill found';
                    span.textContent = s;
                    container.appendChild(span);
                });
            }

            if (missing) {
                missing.forEach(s => {
                    const span = document.createElement('span');
                    span.className = 'skill-pill missing';
                    span.textContent = s;
                    container.appendChild(span);
                });
            }
        }

        function renderList(listId, items, boxId, emptyMsg) {
            const list = document.getElementById(listId);
            const box = document.getElementById(boxId);
            list.innerHTML = '';

            if (!items || items.length === 0) {
                list.innerHTML = `<li>✨ ${emptyMsg}</li>`;
                box.style.opacity = '0.8';
                return;
            }

            box.style.opacity = '1';
            items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                list.appendChild(li);
            });
        }

        // Charts Rendering Functions
        function renderGaugeChart(score) {
            if (gaugeChartInstance) {
                gaugeChartInstance.destroy();
            }

            let color = '#3b82f6';
            if (score >= 80) color = '#10b981';
            else if (score >= 60) color = '#3b82f6';
            else if (score >= 40) color = '#f59e0b';
            else color = '#ef4444';

            const options = {
                chart: {
                    height: 220,
                    type: 'radialBar',
                },
                series: [score],
                colors: [color],
                plotOptions: {
                    radialBar: {
                        startAngle: -135,
                        endAngle: 135,
                        hollow: {
                            size: '70%',
                        },
                        track: {
                            background: '#374151',
                            strokeWidth: '100%',
                        },
                        dataLabels: {
                            name: {
                                show: true,
                                color: '#9ca3af',
                                fontSize: '12px',
                                offsetY: 80
                            },
                            value: {
                                show: true,
                                color: '#f3f4f6',
                                fontSize: '32px',
                                fontWeight: 800,
                                offsetY: -10,
                                formatter: function (val) {
                                    return val + '%';
                                }
                            }
                        }
                    }
                },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shade: 'dark',
                        type: 'horizontal',
                        gradientToColors: [color],
                        stops: [0, 100]
                    }
                },
                stroke: {
                    lineCap: 'round'
                },
                labels: ['ATS Compatibility Score']
            };

            gaugeChartInstance = new ApexCharts(document.querySelector("#gaugeChart"), options);
            gaugeChartInstance.render();
        }

        function renderRadarChart(breakdown) {
            if (radarChartInstance) {
                radarChartInstance.destroy();
            }

            const categories = [
                'Semantic Similarity',
                'Skills Alignment',
                'Experience Suitability',
                'Education Suitability'
            ];

            const seriesData = [
                breakdown.semantic_similarity,
                breakdown.skills_alignment,
                breakdown.experience_suitability,
                breakdown.education_suitability
            ];

            const options = {
                chart: {
                    height: 220,
                    type: 'radar',
                    toolbar: {
                        show: false
                    }
                },
                series: [{
                    name: 'Relevance',
                    data: seriesData,
                }],
                colors: ['#3b82f6'],
                stroke: {
                    width: 2
                },
                fill: {
                    opacity: 0.2
                },
                markers: {
                    size: 4,
                    colors: ['#3b82f6'],
                    strokeColor: '#0b0f19',
                    strokeWidth: 2,
                },
                xaxis: {
                    categories: categories,
                    labels: {
                        style: {
                            colors: ['#9ca3af', '#9ca3af', '#9ca3af', '#9ca3af'],
                            fontSize: '11px',
                            fontFamily: 'inherit',
                            fontWeight: 600,
                        }
                    }
                },
                yaxis: {
                    show: false,
                    min: 0,
                    max: 100
                },
                grid: {
                    borderColor: '#374151',
                }
            };

            radarChartInstance = new ApexCharts(document.querySelector("#radarChart"), options);
            radarChartInstance.render();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Check if file is provided
        if 'resume' not in request.files:
            return jsonify({"error": "No resume file provided"}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        jd_text = request.form.get('jd_text', '').strip()
        min_experience = float(request.form.get('min_experience', 0.0))
        education_requirement = request.form.get('education_requirement', 'Not Specified')
        
        if not jd_text:
            return jsonify({"error": "No job description text provided"}), 400
            
        file_bytes = file.read()
        file_name = file.filename
        
        # 1. Parse Resume
        resume_data = r_parser.parse(file_bytes, file_name)
        
        # 2. Parse JD
        jd_data = jd_parser.parse(jd_text, title="Target Position")
        # Override JD values with manual user inputs if provided, otherwise use parsed ones
        if min_experience > 0:
            jd_data["min_experience"] = min_experience
        if education_requirement != 'Not Specified':
            jd_data["education_requirement"] = education_requirement
            
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
        
        # Optional: Save to SQLite database (wrapped in try-except in case of serverless read-only errors)
        try:
            c_id = db.add_candidate(
                name=resume_data["name"],
                email=resume_data["email"],
                phone=resume_data["phone"]
            )
            flat_res_skills = []
            for s in resume_skills.values():
                flat_res_skills.extend(s)
            
            r_id = db.add_resume(
                candidate_id=c_id,
                file_path=file_name,
                raw_text=resume_data["raw_text"],
                parsed_skills=flat_res_skills,
                parsed_education=jd_parser.extract_education_requirement(resume_data["cleaned_text"]),
                parsed_experience=str(candidate_exp)
            )
            
            jd_flat_skills = []
            for s in jd_skills.values():
                jd_flat_skills.extend(s)
            
            # Add JD
            jd_id = db.add_job_description(
                title=jd_data.get("title", "Target Position"),
                raw_text=jd_text,
                required_skills=jd_flat_skills,
                min_experience=jd_data["min_experience"],
                education_requirements=jd_data["education_requirement"]
            )
            
            db.add_match_result(
                resume_id=r_id,
                jd_id=jd_id,
                match_percentage=score_details["breakdown"]["skills_alignment"],
                ats_score=score_details["ats_score"],
                skills_found=gap_analysis["found_skills"].get("Technical Skills", []) + gap_analysis["found_skills"].get("Tools & Technologies", []),
                skills_missing=gap_analysis["missing_skills"].get("Technical Skills", []) + gap_analysis["missing_skills"].get("Tools & Technologies", []),
                feedback=suggestions
            )
        except Exception as db_err:
            print(f"Database write ignored in serverless: {db_err}")

        # Construct final JSON response
        response_data = {
            "candidate_details": {
                "name": resume_data["name"],
                "email": resume_data["email"] or "Not Found",
                "phone": resume_data["phone"] or "Not Found",
                "extracted_experience": candidate_exp,
                "education_detected": jd_parser.extract_education_requirement(resume_data["cleaned_text"])
            },
            "jd_requirements": {
                "min_experience": jd_data["min_experience"],
                "education_requirement": jd_data["education_requirement"]
            },
            "score_details": score_details,
            "gap_analysis": gap_analysis,
            "suggestions": suggestions
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
