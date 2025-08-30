from ..utils import IndividualScore
import re
# Weights for overall score calculation (total = 1.0)
weights = {
        "job_title_relevance": 0.03,
        "experience_years_match": 0.20,
        "education_match": 0.20,
        "experience_relevance": 0.08,
        "skills_match": 0.20,
        "soft_skills_relevance": 0.04,
        "certifications_match": 0.05,
        "domain_knowledge_match": 0.04,
        "languages_match": 0.10,
        "preferred_education_relevance": 0.03,
        "preferred_qualifications_relevance": 0.03
    }


def parse_years(experience_str: str) -> float:
    """Parse experience duration (e.g., '5+ years', '3-5 years') to a float."""
    if not experience_str:
        return 0.0
    try:
        experience_str = experience_str.lower().replace("yrs", "years").replace("yr", "year")
        if '-' in experience_str:
            low, high = map(float, re.findall(r'\d+\.?\d*', experience_str))
            return (low + high) / 2
        match = re.search(r'(\d+\.?\d*)\s*(?:\+|years?|year)', experience_str)
        return float(match.group(1)) if match else 0.0
    except:
        return 0.0


def normalize_text(text: str) -> str:
    """Normalize text for consistent matching."""
    return text.lower().strip().replace("’", "'").replace("  ", " ") if text else ""


def calculate_normalized_score(scores: IndividualScore, weights: dict) -> float:
    """
    Calculates a normalized overall score based on non-negative category scores.
    Scores should be between 0 and 100, with -1 indicating missing data.
    """
    overall_score = 0.0
    total_weight = 0.0

    for k, v in weights.items():
        score = getattr(scores, k)
        
        # This conditional statement is what excludes negative scores
        if score >= 0:
            overall_score += score * v
            total_weight += v
    
    # Normalize the score by the total weight of included categories
    if total_weight > 0:
        return (overall_score / total_weight)
    else:
        return 0.0
