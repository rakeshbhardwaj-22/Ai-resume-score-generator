import os
import csv
import re
from typing import Dict, List, Set, Any

class SkillExtractor:
    """
    Pure-Python skill extraction engine using boundary-aware regular expressions.
    Reads a reference vocabulary of skills, matches them against text, 
    and categorizes the results.
    """

    def __init__(self, dataset_path: str = None):
        """
        Initialize the SkillExtractor by loading the skills taxonomy.
        """
        self.skills_dict = {}  # skill_name (lowercase) -> category
        self.patterns = {}     # skill_name -> compiled regex pattern
        
        # Determine CSV dataset path
        if not dataset_path:
            # Assume relative path data/skills_dataset.csv from project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataset_path = os.path.join(base_dir, "data", "skills_dataset.csv")

        self._load_skills(dataset_path)

    def _load_skills(self, dataset_path: str):
        """Loads skills from CSV file and creates compiled regex pattern rules."""
        # Baseline fallback skills if file is not found
        fallback_skills = {
            "python": "Technical Skills",
            "java": "Technical Skills",
            "c++": "Technical Skills",
            "javascript": "Technical Skills",
            "sql": "Technical Skills",
            "machine learning": "Technical Skills",
            "deep learning": "Technical Skills",
            "data science": "Technical Skills",
            "nlp": "Technical Skills",
            "communication": "Soft Skills",
            "leadership": "Soft Skills",
            "teamwork": "Soft Skills",
            "git": "Tools & Technologies",
            "docker": "Tools & Technologies",
            "aws": "Tools & Technologies",
            "kubernetes": "Tools & Technologies",
            "tableau": "Tools & Technologies"
        }

        if os.path.exists(dataset_path):
            try:
                with open(dataset_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        skill = row.get('skill')
                        category = row.get('category')
                        if skill and category:
                            skill_clean = str(skill).strip().lower()
                            category_clean = str(category).strip()
                            self.skills_dict[skill_clean] = category_clean
            except Exception as e:
                print(f"Warning: Failed to load skills dataset from {dataset_path}: {e}. Using fallbacks.")
                self.skills_dict = fallback_skills
        else:
            print(f"Warning: Skills dataset path not found at {dataset_path}. Using fallbacks.")
            self.skills_dict = fallback_skills

        # Precompile boundary-aware regex patterns for each skill
        for skill in self.skills_dict.keys():
            escaped = re.escape(skill)
            # Custom boundary checks:
            # - (?<![a-zA-Z0-9_]) checks that the matched skill starts at a word boundary
            # - (?![a-zA-Z0-9_]) checks that the matched skill ends at a word boundary
            # This matches c++, c#, .net etc. correctly without false matching internal strings.
            pattern_str = r'(?<![a-zA-Z0-9_])' + escaped + r'(?![a-zA-Z0-9_])'
            self.patterns[skill] = re.compile(pattern_str, re.IGNORECASE)

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skills from a text block and group them by category.
        
        Args:
            text: Raw or cleaned text to analyze.
            
        Returns:
            Dict[str, List[str]]: Categorized lists of unique skills.
        """
        if not text:
            return {
                "Technical Skills": [],
                "Soft Skills": [],
                "Tools & Technologies": []
            }

        lower_text = text.lower()
        extracted = {
            "Technical Skills": set(),
            "Soft Skills": set(),
            "Tools & Technologies": set()
        }

        for skill, category in self.skills_dict.items():
            # Quick substring search before running regex to maximize execution speed
            if skill in lower_text:
                if self.patterns[skill].search(lower_text):
                    if category in extracted:
                        extracted[category].add(skill)

        # Convert sets to sorted lists for deterministic output
        return {cat: sorted(list(skills)) for cat, skills in extracted.items()}

    def get_skill_gap(self, resume_skills: Dict[str, List[str]], jd_skills: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Performs gap analysis between resume skills and job description skills.
        
        Returns:
            Dict[str, Any]: Lists of overlapping (found) and missing skills by category.
        """
        gap_analysis = {
            "found_skills": {},
            "missing_skills": {},
            "summary": {
                "total_jd_skills": 0,
                "total_matched_skills": 0,
                "overall_gap_percentage": 0.0
            }
        }

        total_jd = 0
        total_matched = 0

        categories = ["Technical Skills", "Soft Skills", "Tools & Technologies"]
        for cat in categories:
            res_set = set(resume_skills.get(cat, []))
            jd_set = set(jd_skills.get(cat, []))

            found = jd_set.intersection(res_set)
            missing = jd_set.difference(res_set)

            gap_analysis["found_skills"][cat] = sorted(list(found))
            gap_analysis["missing_skills"][cat] = sorted(list(missing))

            total_jd += len(jd_set)
            total_matched += len(found)

        gap_analysis["summary"]["total_jd_skills"] = total_jd
        gap_analysis["summary"]["total_matched_skills"] = total_matched
        
        if total_jd > 0:
            match_rate = total_matched / total_jd
            gap_analysis["summary"]["overall_gap_percentage"] = round((1 - match_rate) * 100, 2)
        else:
            gap_analysis["summary"]["overall_gap_percentage"] = 0.0

        return gap_analysis
