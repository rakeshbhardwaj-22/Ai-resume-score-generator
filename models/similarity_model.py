import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict

class ResumeSimilarityModel:
    """
    NLP machine learning model using TF-IDF and Cosine Similarity 
    to compare resume texts with job descriptions.
    """

    def __init__(self):
        # Initialize TfidfVectorizer with English stop words and lowercase normalization
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)

    def calculate_similarity(self, resume_text: str, jd_text: str) -> float:
        """
        Calculate the cosine similarity between resume and JD texts.
        
        Returns:
            float: Similarity score between 0.0 and 100.0.
        """
        if not resume_text.strip() or not jd_text.strip():
            return 0.0

        try:
            # Fit vectorizer and transform both texts
            # We fit on both texts combined to get the shared vocabulary
            tfidf_matrix = self.vectorizer.fit_transform([resume_text, jd_text])
            
            # Compute cosine similarity between the first document (resume) and second (JD)
            sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            
            score = float(sim_matrix[0][0])
            # Convert to percentage and round
            return round(score * 100, 2)
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0

    def extract_top_keywords(self, text: str, top_n: int = 15) -> List[Tuple[str, float]]:
        """
        Extract the most important keywords and their TF-IDF weights from a text block (e.g., Job Description).
        
        Returns:
            List[Tuple[str, float]]: List of (keyword, weight) tuples.
        """
        if not text.strip():
            return []

        try:
            tfidf_matrix = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Pair feature names with scores
            keyword_scores = list(zip(feature_names, scores))
            
            # Sort by score descending
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return keyword_scores[:top_n]
        except Exception as e:
            print(f"Error extracting top keywords: {e}")
            return []
