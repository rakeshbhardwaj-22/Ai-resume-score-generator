import math
import re
from collections import Counter
from typing import List, Tuple

# Standard English stopwords to replicate sklearn behavior
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can\'t', 'cannot', 'could',
    'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t', 'doing', 'don\'t', 'down', 'during', 'each', 'few', 'for',
    'from', 'further', 'had', 'hadn\'t', 'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'he\'d', 'he\'ll',
    'he\'s', 'her', 'here', 'here\'s', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'how\'s', 'i', 'i\'d',
    'i\'ll', 'i\'m', 'i\'ve', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s', 'its', 'itself', 'let\'s', 'me', 'more',
    'most', 'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought',
    'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'shan\'t', 'she', 'she\'d', 'she\'ll', 'she\'s', 'should',
    'shouldn\'t', 'so', 'some', 'such', 'than', 'that', 'that\'s', 'the', 'their', 'theirs', 'them', 'themselves',
    'then', 'there', 'there\'s', 'these', 'they', 'they\'d', 'they\'ll', 'they\'re', 'they\'ve', 'this', 'those',
    'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasn\'t', 'we', 'we\'d', 'we\'ll', 'we\'re',
    'we\'ve', 'were', 'weren\'t', 'what', 'what\'s', 'when', 'when\'s', 'where', 'where\'s', 'which', 'while', 'who',
    'who\'s', 'whom', 'why', 'why\'s', 'with', 'won\'t', 'would', 'wouldn\'t', 'you', 'you\'d', 'you\'ll', 'you\'re',
    'you\'ve', 'your', 'yours', 'yourself', 'yourselves'
}

def tokenize(text: str) -> List[str]:
    """Helper to convert text to lowercase alphanumeric tokens, filtering out stop words."""
    # Find all words/symbols (retaining c++, c#, .net etc)
    words = re.findall(r'\b[a-zA-Z0-9\+\#\.]+\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]

class ResumeSimilarityModel:
    """
    Pure-Python NLP similarity model using TF-IDF and Cosine Similarity 
    to compare resume texts with job descriptions.
    Requires no external packages (scikit-learn, numpy, scipy).
    """

    def __init__(self):
        pass

    def calculate_similarity(self, resume_text: str, jd_text: str) -> float:
        """
        Calculate the cosine similarity between resume and JD texts in pure Python.
        
        Returns:
            float: Similarity score between 0.0 and 100.0.
        """
        if not resume_text.strip() or not jd_text.strip():
            return 0.0

        try:
            tokens_res = tokenize(resume_text)
            tokens_jd = tokenize(jd_text)

            if not tokens_res or not tokens_jd:
                return 0.0

            vocab = set(tokens_res).union(set(tokens_jd))
            
            tf_res = Counter(tokens_res)
            tf_jd = Counter(tokens_jd)

            # Document Frequency (DF) of words (N=2 documents)
            df = {}
            for word in vocab:
                count = 0
                if word in tf_res:
                    count += 1
                if word in tf_jd:
                    count += 1
                df[word] = count

            # IDF calculation with standard scikit-learn smooth formula: idf = ln((1+N)/(1+df)) + 1
            idf = {}
            for word in vocab:
                idf[word] = math.log(3.0 / (1.0 + df[word])) + 1.0

            # Calculate TF-IDF vectors
            vec_res = {word: tf_res[word] * idf[word] for word in vocab}
            vec_jd = {word: tf_jd[word] * idf[word] for word in vocab}

            # L2 normalisation
            sum_res = math.sqrt(sum(val ** 2 for val in vec_res.values()))
            sum_jd = math.sqrt(sum(val ** 2 for val in vec_jd.values()))

            if sum_res == 0 or sum_jd == 0:
                return 0.0

            norm_res = {word: vec_res[word] / sum_res for word in vocab}
            norm_jd = {word: vec_jd[word] / sum_jd for word in vocab}

            # Cosine similarity (dot product of normalized vectors)
            similarity = sum(norm_res[word] * norm_jd[word] for word in vocab)
            
            return round(similarity * 100, 2)
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0

    def extract_top_keywords(self, text: str, top_n: int = 15) -> List[Tuple[str, float]]:
        """
        Extract the most important keywords and their normalized weights from a text block.
        
        Returns:
            List[Tuple[str, float]]: List of (keyword, weight) tuples.
        """
        if not text.strip():
            return []

        try:
            tokens = tokenize(text)
            if not tokens:
                return []
                
            tf = Counter(tokens)
            vocab = list(tf.keys())
            
            # Normalise word frequencies (equivalent to fitting tf-idf on a single document)
            sum_squares = sum(tf[word] ** 2 for word in vocab)
            l2_norm = math.sqrt(sum_squares)
            
            if l2_norm == 0:
                return []

            keyword_scores = [(word, tf[word] / l2_norm) for word in vocab]
            # Sort by score descending
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return keyword_scores[:top_n]
        except Exception as e:
            print(f"Error extracting top keywords: {e}")
            return []
