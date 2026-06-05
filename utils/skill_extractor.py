import os
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
from typing import Dict, List, Set, Any

class SkillExtractor:
    """
    NLP-based skill extraction engine using spaCy's PhraseMatcher.
    Reads a reference vocabulary of skills, matches them against text, 
    and categorizes the results.
    """

    def __init__(self, dataset_path: str = None):
        """
        Initialize the SkillExtractor by loading the skills taxonomy.
        
        Args:
            dataset_path: Path to the skills CSV dataset. If None, looks for it in data/skills_dataset.csv
        """
        # Load spaCy blank English model for fast tokenization and phrase matching
        try:
            self.nlp = spacy.blank("en")
        except Exception as e:
            # Fallback if blank model fails (should not fail as spacy is installed)
            self.nlp = spacy.load("en_core_web_sm")

        self.skills_dict = {}  # skill_name (lowercase) -> category
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Determine CSV dataset path
        if not dataset_path:
            # Assume relative path data/skills_dataset.csv from project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataset_path = os.path.join(base_dir, "data", "skills_dataset.csv")

        self._load_skills(dataset_path)

    def _load_skills(self, dataset_path: str):
        """Loads skills from CSV file and creates spaCy PhraseMatcher rules."""
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
                df = pd.read_csv(dataset_path)
                # Drop rows with NaN values
                df = df.dropna(subset=['skill', 'category'])
                for _, row in df.iterrows():
                    skill = str(row['skill']).strip().lower()
                    category = str(row['category']).strip()
                    self.skills_dict[skill] = category
            except Exception as e:
                print(f"Warning: Failed to load skills dataset from {dataset_path}: {e}. Using fallbacks.")
                self.skills_dict = fallback_skills
        else:
            print(f"Warning: Skills dataset path not found at {dataset_path}. Using fallbacks.")
            self.skills_dict = fallback_skills

        # Build spaCy doc objects for PhraseMatcher
        patterns = []
        for skill in self.skills_dict.keys():
            # Standard doc representation
            doc = self.nlp.make_doc(skill)
            patterns.append(doc)
            
        # Add patterns to matcher under "SKILL" ID
        self.matcher.add("SKILL", patterns)

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skills from a text block and group them by category.
        
        Args:
            text: Raw or cleaned text to analyze.
            
        Returns:
            Dict[str, List[str]]: Categorized lists of unique skills.
            e.g. {
                "Technical Skills": ["python", "machine learning"],
                "Soft Skills": ["communication"],
                "Tools & Technologies": ["git", "aws"]
            }
        """
        if not text:
            return {
                "Technical Skills": [],
                "Soft Skills": [],
                "Tools & Technologies": []
            }

        doc = self.nlp(text)
        matches = self.matcher(doc)

        # Set of extracted skills to avoid duplicates
        extracted = {
            "Technical Skills": set(),
            "Soft Skills": set(),
            "Tools & Technologies": set()
        }

        for match_id, start, end in matches:
            span = doc[start:end]
            matched_text = span.text.strip().lower()
            
            # Retrieve category
            category = self.skills_dict.get(matched_text)
            if category in extracted:
                extracted[category].add(matched_text)

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
