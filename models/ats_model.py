import re
import datetime
from typing import Dict, Any, List

class ATSModel:
    """
    Predicts ATS scores and evaluates qualification relevance (experience, education, skills).
    Calculates a weighted compatibility rating out of 100.
    """

    def __init__(self, similarity_weight: float = 0.30, skills_weight: float = 0.40,
                 experience_weight: float = 0.20, education_weight: float = 0.10):
        """
        Initialize the ATS Scoring model with customized weights.
        All weights must sum to 1.0.
        """
        self.w_sim = similarity_weight
        self.w_skills = skills_weight
        self.w_exp = experience_weight
        self.w_edu = education_weight

    def extract_years_of_experience(self, text: str) -> float:
        """
        Extract years of experience from resume text using heuristics:
        1. Date range intervals (e.g. 2018 - 2022, 2020 to Present)
        2. Direct statements (e.g. "8+ years of experience in...")
        """
        current_year = datetime.datetime.now().year  # Fallback to current system year (e.g. 2026)
        
        # Heuristic 1: Find date ranges (like 2018 - 2022, 2020 - Present)
        # Match years between 1990 and current_year+1
        year_range_pattern = r'\b(19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*(present|current|19\d{2}|20\d{2})\b'
        matches = re.findall(year_range_pattern, text.lower())
        
        calculated_years = 0.0
        ranges_found = False
        
        for start, end in matches:
            start_year = int(start)
            if start_year < 1980 or start_year > current_year:
                continue
                
            if end in ['present', 'current']:
                end_year = current_year
            else:
                end_year = int(end)
                if end_year < start_year or end_year > current_year + 1:
                    continue
            
            calculated_years += max(0.5, float(end_year - start_year))
            ranges_found = True

        # Heuristic 2: Find direct experience statements like "5+ years", "10 years experience"
        exp_phrase_pattern = r'\b(\d{1,2})\+?\s*(?:years?)\s*(?:of\s*)?(?:work\s*)?experience\b'
        phrases = re.findall(exp_phrase_pattern, text.lower())
        phrase_years = 0.0
        if phrases:
            phrase_years = max([float(x) for x in phrases])

        # Combine results: If date ranges were found, use them as primary; 
        # otherwise use phrase matching or return max of both.
        final_years = 0.0
        if ranges_found:
            # Date ranges can sum up experiences, cap at 30 years to prevent anomalies
            final_years = min(calculated_years, 30.0)
        else:
            final_years = min(phrase_years, 30.0)

        # In case both are present, we can take the maximum as a fallback
        final_years = max(final_years, phrase_years)

        return round(final_years, 1)

    def evaluate_education(self, resume_text: str, required_degree: str) -> float:
        """
        Compare the candidate's degree level against required education.
        
        Hierarchy: PhD (3) > Master's (2) > Bachelor's (1) > Not Specified (0)
        
        Returns:
            float: score out of 100.
        """
        if required_degree == "Not Specified":
            return 100.0

        # Heuristics for candidate degree level detection
        lower_text = resume_text.lower()
        phd_patterns = [r"\bphd\b", r"\bph\.d\b", r"\bdoctorate\b"]
        masters_patterns = [r"\bmasters?\b", r"\bm\.s\b", r"\bm\.tech\b", r"\bmba\b", r"\bmsc\b"]
        bachelors_patterns = [r"\bbachelors?\b", r"\bb\.s\b", r"\bb\.tech\b", r"\bb\.a\b", r"\bbe\b", r"\bbs\b"]

        cand_level = 0
        if any(re.search(pat, lower_text) for pat in phd_patterns):
            cand_level = 3
        elif any(re.search(pat, lower_text) for pat in masters_patterns):
            cand_level = 2
        elif any(re.search(pat, lower_text) for pat in bachelors_patterns):
            cand_level = 1

        req_level = 0
        if required_degree == "PhD / Doctorate":
            req_level = 3
        elif required_degree == "Master's Degree":
            req_level = 2
        elif required_degree == "Bachelor's Degree":
            req_level = 1

        if cand_level >= req_level:
            return 100.0
        elif cand_level > 0:
            # Partial match (e.g. required Master's, candidate has Bachelor's)
            return 50.0
        else:
            return 0.0

    def predict_score(self, similarity_score: float, skills_found_count: int, 
                      total_jd_skills_count: int, candidate_exp: float, 
                      required_exp: float, education_score: float) -> Dict[str, Any]:
        """
        Calculate the predicted ATS score using a weighted average.
        
        Returns:
            Dict[str, Any]: Detailed breakdown of the score.
        """
        # 1. Similarity Component (already 0-100)
        sim_component = similarity_score

        # 2. Skill Component (0-100)
        if total_jd_skills_count > 0:
            skills_component = (skills_found_count / total_jd_skills_count) * 100
        else:
            skills_component = 100.0  # If no skills are defined in JD, give full score

        # 3. Experience Component (0-100)
        if required_exp <= 0.0:
            exp_component = 100.0
        else:
            # Ratio of candidate exp to required exp, capped at 100%
            # If candidate has some experience but less than required, they get partial score
            exp_ratio = candidate_exp / required_exp
            exp_component = min(exp_ratio * 100, 100.0)

        # 4. Education Component (already 0-100)
        edu_component = education_score

        # Calculate final weighted score
        final_score = (
            (sim_component * self.w_sim) +
            (skills_component * self.w_skills) +
            (exp_component * self.w_exp) +
            (edu_component * self.w_edu)
        )
        final_score = round(final_score, 2)

        # Determine grade/match status
        if final_score >= 80:
            grade = "Strong Match"
        elif final_score >= 60:
            grade = "Good Match"
        elif final_score >= 40:
            grade = "Average Match"
        else:
            grade = "Needs Improvement"

        return {
            "ats_score": final_score,
            "grade": grade,
            "breakdown": {
                "semantic_similarity": round(sim_component, 2),
                "skills_alignment": round(skills_component, 2),
                "experience_suitability": round(exp_component, 2),
                "education_suitability": round(edu_component, 2)
            },
            "weights": {
                "semantic_similarity": self.w_sim,
                "skills_alignment": self.w_skills,
                "experience_suitability": self.w_exp,
                "education_suitability": self.w_edu
            }
        }
