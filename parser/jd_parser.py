import re
import io
import os
import pypdf
import docx
from typing import Dict, Any, Union

class JobDescriptionParser:
    """
    A class to parse Job Descriptions from text, PDF, or DOCX formats.
    Extracts requirements like experience and education.
    """

    def __init__(self):
        pass

    def extract_text(self, file_source: Union[str, io.BytesIO, bytes], file_name: str = "") -> str:
        """
        Extract raw text from PDF, DOCX, or text files.
        """
        # If it's already a string and not a file path, return it directly
        if isinstance(file_source, str) and not os.path.exists(file_source) and len(file_source.split()) > 10:
            return file_source

        ext = ""
        if isinstance(file_source, str):
            _, ext = os.path.splitext(file_source.lower())
        elif file_name:
            _, ext = os.path.splitext(file_name.lower())
        else:
            raise ValueError("Unable to determine file type. Provide a file path or specify file_name.")

        if isinstance(file_source, bytes):
            file_source = io.BytesIO(file_source)

        if ext == ".pdf":
            return self._extract_from_pdf(file_source)
        elif ext in [".docx", ".doc"]:
            return self._extract_from_docx(file_source)
        elif ext in [".txt", ""]:
            return self._extract_from_txt(file_source)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _extract_from_pdf(self, file_source: Union[str, io.BytesIO]) -> str:
        """Extract text from PDF using pypdf."""
        text = ""
        try:
            reader = pypdf.PdfReader(file_source)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            raise RuntimeError(f"Error reading PDF job description: {str(e)}")
        return text

    def _extract_from_docx(self, file_source: Union[str, io.BytesIO]) -> str:
        """Extract text from DOCX using python-docx."""
        text = ""
        try:
            doc = docx.Document(file_source)
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"
        except Exception as e:
            raise RuntimeError(f"Error reading DOCX job description: {str(e)}")
        return text

    def _extract_from_txt(self, file_source: Union[str, io.BytesIO]) -> str:
        """Extract text from a plain text file."""
        try:
            if isinstance(file_source, str):
                with open(file_source, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            else:
                return file_source.read().decode("utf-8", errors="ignore")
        except Exception as e:
            raise RuntimeError(f"Error reading TXT job description: {str(e)}")

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize job description text.
        """
        if not text:
            return ""
        cleaned = re.sub(r'[ \t]+', ' ', text)
        cleaned = re.sub(r'\n+', '\n', cleaned)
        cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in ['\n', '\r', '\t'])
        return cleaned.strip()

    def extract_experience_requirement(self, text: str) -> float:
        """
        Extract required years of experience from job description using regex.
        
        Returns:
            float: Minimum years of experience required. Defaults to 0.0 if not specified.
        """
        # Patterns like: "3+ years", "3-5 years", "minimum 5 years", "at least 2 years"
        patterns = [
            r'(\d+)\s*\+?\s*years?',
            r'(\d+)\s*to\s*(\d+)\s*years?',
            r'(\d+)\s*-\s*(\d+)\s*years?',
            r'minimum\s*of\s*(\d+)\s*years?',
            r'at\s*least\s*(\d+)\s*years?',
            r'experience\s*of\s*(\d+)\s*years?'
        ]
        
        lower_text = text.lower()
        years = []
        
        for pattern in patterns:
            matches = re.findall(pattern, lower_text)
            for match in matches:
                if isinstance(match, tuple):
                    # For ranges like 3 to 5 years, take the lower bound as the minimum
                    years.append(float(match[0]))
                else:
                    years.append(float(match))
                    
        # Filter realistic years of experience (e.g. less than 20 years)
        valid_years = [y for y in years if 0 < y < 20]
        
        return min(valid_years) if valid_years else 0.0

    def extract_education_requirement(self, text: str) -> str:
        """
        Extract minimum education requirements.
        """
        lower_text = text.lower()
        
        degrees = {
            "PhD / Doctorate": [r"\bphd\b", r"\bph\.d\b", r"\bdoctorate\b"],
            "Master's Degree": [r"\bmasters?\b", r"\bm\.s\b", r"\bm\.tech\b", r"\bmba\b", r"\bmsc\b"],
            "Bachelor's Degree": [r"\bbachelors?\b", r"\bb\.s\b", r"\bb\.tech\b", r"\bb\.a\b", r"\bbe\b", r"\bbs\b"]
        }
        
        # Check hierarchy starting from highest
        for degree_name, patterns in degrees.items():
            for pattern in patterns:
                if re.search(pattern, lower_text):
                    return degree_name
                    
        return "Not Specified"

    def parse(self, file_source: Union[str, io.BytesIO, bytes], file_name: str = "", title: str = "Unknown Job") -> Dict[str, Any]:
        """
        Complete parsing pipeline for a job description.
        """
        raw_text = self.extract_text(file_source, file_name)
        cleaned_text = self.clean_text(raw_text)
        min_experience = self.extract_experience_requirement(cleaned_text)
        education_req = self.extract_education_requirement(cleaned_text)
        
        return {
            "title": title,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "min_experience": min_experience,
            "education_requirement": education_req
        }
