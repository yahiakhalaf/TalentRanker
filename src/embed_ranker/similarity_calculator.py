from .embed_utils import normalize_text
from typing import List
from fuzzywuzzy import fuzz
from sentence_transformers import SentenceTransformer, util

sentence_model = SentenceTransformer('all-MiniLM-L6-v2')


def encode_data(text: str):
    """
    Encodes a given string into a sentence embedding.
    Returns None if the text is empty or None.
    """
    text = normalize_text(text)
    if not text:
        return None
    return sentence_model.encode(text, convert_to_tensor=True)


def calculate_similarity(embedding1, embedding2) -> float:
    """
    Calculates cosine similarity between two embeddings.
    Returns -1 if the first embedding is None, or 50.0 if the second is None.
    """
    if embedding1 is None:
        return -1.0
    if embedding2 is None:
        return 50.0
    return util.cos_sim(embedding1, embedding2).item() * 100


def compute_fuzzy_match(set1: set, set2: set) -> float:
    """Compute fuzzy match score between two sets of strings."""
    set1, set2 = set(normalize_text(s) for s in set1), set(normalize_text(s) for s in set2)
    if not set1:
        return -1  # Return -1 if first input is empty
    if not set2:
        return 50  # Return 50 if first input not empty but second is empty
    
    max_scores = []
    for s1 in set1:
        scores = [max(fuzz.ratio(s1, s2), fuzz.partial_ratio(s1, s2), fuzz.token_set_ratio(s1, s2)) for s2 in set2]
        max_scores.append(max(scores))
    
    return sum(max_scores) / len(max_scores) # Average of max scores


def compute_fuzzy_education_match(jd_edu: str, resume_edus: List[str]) -> float:
    """Compute fuzzy match score for education (single string vs. list of strings)."""
    jd_edu = normalize_text(jd_edu)
    resume_edus = [normalize_text(e) for e in resume_edus]
    if not jd_edu:
        return -1.0
    if not resume_edus:
        return 50.0
    
    max_score = 80
    for edu in resume_edus:
        score = max(fuzz.ratio(jd_edu, edu), fuzz.partial_ratio(jd_edu, edu), fuzz.token_set_ratio(jd_edu, edu))
        if score >= 90:
            return 95.0  # Exact or near-exact match
        max_score = max(max_score, min(score, 90))  # Cap partial matches at 60
    return max_score