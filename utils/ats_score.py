import re
from collections import Counter
from typing import Dict, Any, List, Set

class ATSScorer:
    """
    Evaluates resume formatting, structure, keyword density, and action verb strength.
    Provides actionable suggestions for resume optimization.
    """

    # Strong action verbs by category
    ACTION_VERBS = {
        "leadership": {"spearheaded", "led", "managed", "directed", "coordinated", "guided", "championed", "supervised", "orchestrated", "steered"},
        "technical": {"designed", "developed", "engineered", "architected", "implemented", "built", "created", "coded", "programmed", "authored", "deployed"},
        "optimization": {"optimized", "improved", "streamlined", "reduced", "enhanced", "accelerated", "maximized", "boosted", "revamped", "modernized"},
        "analysis": {"analyzed", "investigated", "evaluated", "audited", "researched", "assessed", "diagnosed", "tracked", "forecasted", "modeled"}
    }

    # Weak phrases to avoid or replace
    WEAK_PHRASES = [
        "responsible for",
        "helped with",
        "assisted in",
        "worked on",
        "duties included",
        "part of a team that"
    ]

    def __init__(self):
        # Flatten all action verbs into a single lookup set
        self.all_action_verbs = set().union(*self.ACTION_VERBS.values())

    def check_sections(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Check for the presence of standard sections and evaluate their richness.
        """
        results = {
            "score": 100.0,
            "missing_sections": [],
            "weak_sections": [],
            "tips": []
        }

        # Essential sections that should be present
        essential_sections = {
            "skills": "Skills / Technologies",
            "experience": "Work Experience / Professional Experience",
            "education": "Education / Academic Background"
        }

        # Nice-to-have sections
        optional_sections = {
            "projects": "Projects / Portfolio",
            "certifications": "Certifications"
        }

        # Evaluate essential sections (deduct 20 points per missing essential section)
        for key, name in essential_sections.items():
            content = sections.get(key, "").strip()
            if not content:
                results["missing_sections"].append(name)
                results["score"] -= 20.0
                results["tips"].append(f"Add a dedicated '{name}' section to make your resume easy to scan for ATS and recruiters.")
            elif len(content) < 50:
                results["weak_sections"].append(name)
                results["score"] -= 5.0
                results["tips"].append(f"Your '{name}' section is very brief. Expand it with more details, details of your achievements, or list more entries.")

        # Evaluate optional sections (deduct 5 points per missing optional section, up to 10 points)
        for key, name in optional_sections.items():
            content = sections.get(key, "").strip()
            if not content:
                results["score"] -= 5.0
                results["tips"].append(f"Consider adding a '{name}' section to showcase your additional qualifications and personal accomplishments.")

        # Clamp section score to minimum of 0
        results["score"] = max(0.0, results["score"])
        return results

    def check_action_verbs(self, text: str) -> Dict[str, Any]:
        """
        Analyze the presence of strong action verbs and detect weak/passive phrasing.
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        found_verbs = self.all_action_verbs.intersection(words)
        
        # Detect weak phrases
        found_weak_phrases = []
        lower_text = text.lower()
        for phrase in self.WEAK_PHRASES:
            if phrase in lower_text:
                found_weak_phrases.append(phrase)

        # Calculate score: we expect at least 8 strong action verbs in a good resume
        expected_count = 8
        verb_count = len(found_verbs)
        
        # Score calculation: base of 100, deduct 5 points for every verb missing below expected, 
        # and 5 points for every weak phrase found
        verb_score = 100.0 - (max(0, expected_count - verb_count) * 6.0)
        verb_score -= len(found_weak_phrases) * 8.0
        verb_score = max(0.0, round(verb_score, 2))

        # Build suggestions
        tips = []
        if verb_count < expected_count:
            tips.append(f"Only found {verb_count} strong action verbs. Use more action-oriented words (e.g., 'spearheaded', 'optimized', 'engineered') to describe your achievements.")
        
        if found_weak_phrases:
            tips.append(f"Avoid passive phrases like {', '.join([f'\"{p}\"' for p in found_weak_phrases])}. Replace them with strong active verbs (e.g. instead of 'responsible for building', use 'Engineered' or 'Developed').")

        return {
            "score": verb_score,
            "found_verbs": sorted(list(found_verbs)),
            "weak_phrases_found": found_weak_phrases,
            "tips": tips
        }

    def check_keyword_density(self, text: str) -> Dict[str, Any]:
        """
        Analyze keyword frequencies to flag potential keyword stuffing or low density.
        Focuses on single terms of length > 3 characters (excluding common stop words).
        """
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return {"score": 100.0, "stuffed_keywords": [], "tips": []}

        counts = Counter(words)
        stuffed = []
        underused = []
        
        tips = []
        score = 100.0

        for word, count in counts.items():
            density = (count / total_words) * 100
            
            # If a single word makes up more than 4% of the resume, flag as keyword stuffing
            if density > 4.0 and count > 6:
                stuffed.append((word, round(density, 2)))
                score -= 10.0
                
        if stuffed:
            stuffed_words = [f"'{w}' ({d}%)" for w, d in stuffed]
            tips.append(f"Potential keyword stuffing detected: {', '.join(stuffed_words)}. Keep your keyword density natural (between 1% and 3% per term) to avoid being flagged by automated ATS filters.")
            
        score = max(0.0, round(score, 2))

        return {
            "score": score,
            "stuffed_keywords": stuffed,
            "tips": tips
        }

    def generate_suggestions(self, resume_data: Dict[str, Any], jd_data: Dict[str, Any], 
                             gap_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a unified structural and phrasing improvement roadmap.
        """
        sections = resume_data.get("sections", {})
        cleaned_text = resume_data.get("cleaned_text", "")
        
        section_results = self.check_sections(sections)
        verb_results = self.check_action_verbs(cleaned_text)
        density_results = self.check_keyword_density(cleaned_text)
        
        # Compile missing skills suggestions
        missing_skills_tips = []
        missing_tech = gap_analysis.get("missing_skills", {}).get("Technical Skills", [])
        missing_tools = gap_analysis.get("missing_skills", {}).get("Tools & Technologies", [])
        
        if missing_tech:
            missing_skills_tips.append(f"Consider acquiring or highlighting these core technical skills mentioned in the JD: {', '.join(missing_tech[:5])}.")
        if missing_tools:
            missing_skills_tips.append(f"Add experience or list familiarity with these required tools/technologies: {', '.join(missing_tools[:5])}.")

        # Combine all tips into categories
        all_suggestions = {
            "structure_and_formatting": section_results["tips"],
            "phrasing_and_language": verb_results["tips"],
            "seo_and_keyword_stuffing": density_results["tips"],
            "skills_gap_remediation": missing_skills_tips,
            "metrics": {
                "structure_score": section_results["score"],
                "phrasing_score": verb_results["score"],
                "keyword_density_score": density_results["score"]
            }
        }
        
        return all_suggestions
